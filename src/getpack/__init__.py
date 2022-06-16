"""
Setup external resources any deploy them on the fly.

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


__version__ = '0.0.1'


class Resource:
    """Base resource."""
    name = ''
    activated = False
    initialized = False

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            # TODO prevent usage of undefined properties
            setattr(self, k, v)

    def make_available(self):
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

    def get_available_versions(self):
        path = self.get_path(self.name)
        if path.is_dir():
            return os.listdir(path)
        return []

    def get_path(self, *args):
        path = self.local_base
        for a in (self.local_prefix,) + args:
            if a:
                path /= a
        return path

    def _ensure_available(self):
        if self.initialized:
            return
        assert self.name, 'Resource should be named'
        assert self.version, 'Resource should be versioned'
        if self.version in self.get_available_versions():
            return
        self.initialized = True
        self.make_available()

    def cleanup(self):
        path = self.get_path(self.name, self.version)
        if path.is_dir():
            shutil.rmtree(path)


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
    archive_extraction = {'': {'path': ''}}
    extractor_plugins = {
        r'.+\.(whl|zip)$': ZipExtractor,
    }

    def get_extractor(self, filename, stream):
        for k, v in self.extractor_plugins.items():
            if re.match(k, filename):
                return v(stream)


class WebResource(ArchivedResource):
    """Resource from the web."""

    def make_available(self):
        self.cleanup()

        request = urllib.request.urlopen(self.archive_url)
        assert request.status in {200}, 'Unexpected status {} for {}'.format(
            request.status, self.archive_url)

        # extract to temporary folder then rename
        temp_path = Path(tempfile.mkdtemp())

        with self.get_extractor(self.archive_url, request) as extractor:
            for filename in extractor.get_file_list():
                dest_path = ''
                for k, v in self.archive_extraction.items():
                    if filename.startswith(k):
                        dest_path = v['path']
                        break
                else:
                    continue
                dest_path = temp_path / dest_path / filename
                if not dest_path.parent.is_dir():
                    dest_path.parent.mkdir(parents=True)
                dest_path.write_bytes(extractor.get_stream(filename))

        temp_path.rename(self.get_path(self.name, self.version))


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
        self.activated = True
        sys.path.insert(0, str(self.get_path(self.name, self.version)))
        __import__(self.name)
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

    def cleanup(self):
        # TODO consider recursive cleanup, it cause dll locking in PySide test
        # for resource in self.requirements:
        #     resource.cleanup()
        return super(PythonPackage, self).cleanup()


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
