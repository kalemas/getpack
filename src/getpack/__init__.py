"""
Declarative external resources any with implicit deployment.

This file is suitable to bundle with projects so they would bootstrap *getpack*
and install it from pypi, then use full set of functions.


Copyright (c) 2022 Konstantin Maslyuk. All rights reserved.

This work is licensed under the terms of the MIT license.
For a copy, see <https://opensource.org/licenses/MIT>.
"""

from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import typing
import urllib.request
import zipfile


__version__ = '0.0.5'


def _logging(*args):
    return print(args[0] % args[1:])


def _logging_off(*args):
    pass


info = _logging_off
debug = info


class Resource:
    """Base resource."""
    name = ''
    activated = False
    initialized = False

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            # TODO prevent usage of undefined properties
            setattr(self, k, v)

    def deploy(self):
        """
        This will produce all the hard work to make resource available, but
        not necessary to make an effect from resource in current environment.
        This method also will cleanup currently deployed data before the
        deployment.
        """
        raise NotImplementedError

    def __call__(self, *_, **__):
        """Actually produce an effect from the resource."""
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError


class LocalResource(Resource):
    """Locally cached resource."""
    local_base = Path(os.getenv('APPDATA')) / 'getpack'
    local_prefix = ''
    _path = None

    @property
    def path(self):
        if self._path is None:
            self._path = (
                self.local_base / self.local_prefix / self.name / self.version)
        return self._path

    def _deploy_to(self, path):
        """Obtain resrouce and store in `path`"""
        raise NotImplementedError

    def _ensure_available(self):
        if self.initialized:
            return
        assert self.name, 'Resource should be named'
        assert self.version, 'Resource should be versioned'
        if self.path.is_dir():
            return
        self.initialized = True
        self.deploy()

    def deploy(self):
        self.cleanup()
        # extract to temporary folder then rename
        temp_path = Path(tempfile.mkdtemp())
        self._deploy_to(temp_path)
        if not self.path.parent.is_dir():
            self.path.parent.mkdir(parents=True)
        temp_path.rename(self.path)

    def cleanup(self):
        if self.path.is_dir():
            info('Cleanup %s', self.path)
            shutil.rmtree(self.path)


class ArchiveExtractor:
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, exc_traceback):
        raise NotImplementedError


class ZipExtractor(ArchiveExtractor):

    def __enter__(self):
        # TODO here we process archive in memory, not the best approach
        # especially for large archives, consider local caching, retransferring
        # broken parts
        self.zipfile = zipfile.ZipFile(BytesIO(self.stream.read()))
        self.context = self.zipfile.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.zipfile.__exit__(exc_type, exc_value, exc_traceback)

    def get_file_list(self):
        return [f.filename for f in self.zipfile.filelist]

    def get_stream(self, filename):
        return self.zipfile.read(filename)


class ArchivedResource(LocalResource):
    archive_name = ''
    archive_extraction = {'': {'path': ''}}
    extractor_plugins = {
        r'.+\.(whl|zip)$': ZipExtractor,
    }

    def get_archive_stream(self):
        raise NotImplementedError

    def _deploy_to(self, path):
        assert self.archive_name, (
            'Property *archive_name* should be defined for {}'.format(self))
        for k, extractor_cls in self.extractor_plugins.items():
            if re.match(k, self.archive_name):
                break
        else:
            raise Exception('No extractor for {}'.format(self.archive_name))

        with extractor_cls(self.get_archive_stream()) as extractor:
            for filename in extractor.get_file_list():
                dest_path = ''
                for k, v in self.archive_extraction.items():
                    if filename.startswith(k):
                        dest_path = v['path']
                        break
                else:
                    continue
                dest_path = path / dest_path / filename
                if not dest_path.parent.is_dir():
                    dest_path.parent.mkdir(parents=True)
                dest_path.write_bytes(extractor.get_stream(filename))


class WebResource(ArchivedResource):
    """Resource from the web."""

    def get_archive_stream(self):
        info('Downloading %s', self.archive_url)
        request = urllib.request.urlopen(self.archive_url)
        assert request.status in {200}, 'Unexpected status {} for {}'.format(
            request.status, self.archive_url)
        return request

    @property
    def archive_name(self):
        return self.archive_url.rsplit('/', 1)[1]


class PythonPackage(LocalResource):
    """Python package."""
    local_prefix = 'python'
    requirements = []  # type: typing.Iterable[Resource]

    def __init__(self, name=None, version=None, **kwargs):
        if name:
            kwargs['name'] = name
        if version:
            kwargs['version'] = version
        super(PythonPackage, self).__init__(**kwargs)

    def __call__(self, *_, **__):
        if self.activated:
            return

        # activate requirements
        [r() for r in self.requirements]

        self._ensure_available()
        sys.path.insert(0, str(self.path))
        try:
            __import__(self.name)
        except Exception:
            sys.path.remove(str(self.path))
            raise
        self.activated = True
        # TODO validate imported package by path

    def __getattr__(self, key):
        """
        The biggest problem in such approach is that static analysis does not
        work. I think it is still necessary to use something like:
        ```python
        try:
            import PySide2
        except ImportError:
            PySide2 = getpack.PyPiPackage('PySide2', '5.15.2')
        ```
        or
        ```python
        getpack.PyPiPackage('PySide2', '5.15.2')()
        import PySide2
        ```
        """
        self()
        return getattr(sys.modules[self.name], key)


class WebPackage(PythonPackage, WebResource):
    """Python package from the web."""


class PyPiPackage(WebPackage):
    _archive_url = ''

    @property
    def archive_url(self):
        if not self._archive_url:
            request = urllib.request.urlopen(
                'https://pypi.org/pypi/{}/json'.format(self.name))
            data = json.loads(request.read())
            releases = data['releases'][self.version]
            debug('Available releases:\n\t%s', '\n\t'.join(
                r['filename'] for r in data['releases'][self.version]))
            platform = 'win_amd64'
            releases = [
                r for r in releases
                if platform in r['filename']
            ]
            # TODO improve release selection
            assert len(
                releases) >= 1, 'No unique release available from {}'.format(
                    ', '.join(r['filename'] +
                              (' (selected)' if r in releases else '')
                              for r in data['releases'][self.version]))
            # TODO save and check digest
            self._archive_url = releases[0]['url']
        return self._archive_url
