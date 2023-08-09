"""
Declarative external resources with implicit deployment.

This file is suitable to bundle with projects so they would bootstrap *getpack*
and install it from pypi, then use full set of functions.


Copyright (c) 2022 Konstantin Maslyuk. All rights reserved.

This work is licensed under the terms of the MIT license.
For a copy, see <https://opensource.org/licenses/MIT>.
"""

import json
import os
from pathlib import Path
import random
import re
import shutil
import sys
import threading
import typing  # noqa: F401

import fasteners
from six.moves import urllib

from .extraction import TarExtractor, ZipExtractor


class HybridLock:
    def __init__(self, key):
        self.key = key.as_posix() + '.lock'
        self.folder = os.path.dirname(self.key)
        self.file_lock = fasteners.InterProcessLock(self.key)
        self.lock = threading.RLock()
        self.counter = 0

    def __enter__(self):
        self.lock.acquire()

        # no more single thread now can access here
        self.counter += 1
        if self.counter == 1:
            if not os.path.isdir(self.folder):
                try:
                    os.makedirs(self.folder)
                except OSError:
                    pass  # may fail because of race
            try:
                self.file_lock.acquire()
            except Exception:
                # attempt to fix rare PermissionError in multi process races,
                # maybe timeout? Have no info on effectiveness of following
                # code
                self.file_lock.acquire()

    def __exit__(self, *_):
        self.counter -= 1
        if not self.counter:
            self.file_lock.release()
            try:
                os.unlink(self.key)
            except Exception:
                pass
        self.lock.release()


def lock(key, _locks={None: threading.Lock()}):
    with _locks[None]:
        if key not in _locks:
            _locks[key] = HybridLock(key)
    return _locks[key]


def _logging(*args):
    print(args[0] % args[1:])


def _logging_off(*args):
    pass


info = _logging_off
debug = info


class Resource(object):
    """Base resource."""
    _available = False
    name = ''
    path = None  # type: Path
    version = None  # type: str

    def __init__(self, **kwargs):
        """
        Initialization is not heavy operation, feel free to construct a
        Resource and query available versions.
        """
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    @property
    def lock(self):
        return lock(self.path)

    def get_available_versions(self):  # type: () -> typing.List[str]
        """Get list of available versions."""
        raise NotImplementedError()

    def deploy(self):
        """
        This will produce all the hard work to make resource available, but
        not necessary to make an effect from resource in current environment.
        This method also will cleanup currently deployed data before the
        deployment.
        """
        raise NotImplementedError

    def provide(self):
        """Make resource available so it would be immediately used."""
        if self._available:
            return
        assert self.name, 'Resource should be named'
        assert self.version, 'Resource should be versioned'
        with self.lock:
            if self.version in self.get_available_versions():
                self._available = True
                return
            self.deploy()
            self._available = True

    def __call__(self):
        self.provide()
        return self

    def cleanup(self):
        raise NotImplementedError


class LocalResource(Resource):
    """Locally cached resource."""
    if sys.platform == 'win32':
        local_base = Path(os.getenv('APPDATA')) / 'getpack'
    elif sys.platform == 'linux':
        local_base = Path(os.environ['HOME']) / '.config' / 'getpack'
    local_prefix = ''
    _path = None

    @property
    def path(self):  # type: () -> Path
        if self._path is None:
            self._path = (
                self.local_base / self.local_prefix / self.name / self.version)
        return self._path

    def get_available_versions(self):
        if not self.path.parent.is_dir():
            return []
        return [
            i.name for i in self.path.parent.iterdir()
            if not i.name.endswith('.temp')
        ]

    def _deploy_to(self, path):
        """Obtain resrouce and store in `path`"""
        raise NotImplementedError

    def deploy(self):
        self.cleanup()
        # extract to temporary folder then rename
        temp_path = None
        try:
            for _ in range(100):
                temp_path = self.path.parent / '{:020x}.temp'.format(
                    random.randrange(16**20))
                if not temp_path.is_dir():
                    temp_path.mkdir(parents=True)
                    break
            else:
                raise Exception(
                    'Failed to find empty temp dir (last: {})'.format(
                        temp_path))
            self._deploy_to(temp_path)
            if not self.path.parent.is_dir():
                self.path.parent.mkdir(parents=True)
            temp_path.rename(self.path)
        except Exception:
            if temp_path and temp_path.is_dir():
                shutil.rmtree(str(temp_path))
            raise

    def cleanup(self):
        with self.lock:
            if self.path.is_dir():
                info('Cleanup %s', self.path)
                shutil.rmtree(str(self.path))
            self._available = False


class ArchivedResource(LocalResource):
    archive_name = ''
    archive_extraction = {'': {'path': ''}}
    extractor_plugins = {
        r'.+\.(whl|zip)$': ZipExtractor,
        r'.+\.tar(.gz|.xz|.bz)?$': TarExtractor,
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
                    k = k.format(self=self)
                    # TODO add regex
                    if filename.startswith(k):
                        dest_path = v['path'] + filename[len(k):]
                        break
                else:
                    continue
                assert dest_path and dest_path[0] != '/'
                dest_path = path / dest_path
                if not dest_path.parent.is_dir():
                    dest_path.parent.mkdir(parents=True)

                # py2 pathlib.Path does not have write_bytes()
                with open(str(dest_path), 'wb') as f:
                    f.write(extractor.get_bytes(filename))


class WebResource(ArchivedResource):
    """Resource from the web."""

    def get_archive_stream(self):
        archive_url = self.archive_url.format(self=self)
        info('Downloading %s', archive_url)
        request = urllib.request.urlopen(archive_url)
        assert request.getcode() in {200}, (
            'Unexpected status {} for {}'.format(
                request.getcode(), archive_url))
        return request

    @property
    def archive_name(self):
        return urllib.parse.urlparse(self.archive_url).path.rsplit('/', 1)[1]


class PythonPackage(LocalResource):
    """Python package."""
    local_prefix = 'python'
    _activated = False
    requirements = []  # type: typing.Iterable[Resource]

    def __init__(self, name=None, version=None, **kwargs):
        if name:
            kwargs['name'] = name
        if version:
            kwargs['version'] = version
        super(PythonPackage, self).__init__(**kwargs)

    def provide(self):
        for r in self.requirements:
            r.provide()
        super(PythonPackage, self).provide()
        if str(self.path) not in sys.path:
            sys.path.insert(0, str(self.path))

    def activate(self):
        if self._activated:
            return
        self.provide()
        [r.activate() for r in self.requirements]
        __import__(self.name)
        self._activated = True

    def get(self, name=None):
        name = name or self.name
        self.activate()
        __import__(name)
        return sys.modules[name]

    def __call__(self, name=None):
        return self.get(name=name)


class WebPythonPackage(PythonPackage, WebResource):
    """Python package from the web."""


WebPackage = WebPythonPackage  # TODO deprecated


class PyPiPackage(WebPythonPackage):
    _archive_url = ''
    _release_info = None

    @property
    def release_info(self):
        if self._release_info is None:
            request = urllib.request.urlopen(
                'https://pypi.org/pypi/{}/json'.format(self.name))
            data = json.loads(request.read())
            releases = data['releases'][self.version]
            debug('Available releases:\n\t%s', '\n\t'.join(
                r['filename'] for r in data['releases'][self.version]))
            platform = 'win_amd64'
            if (len(releases) == 1
                    and releases[0]['python_version'] == 'source'):
                pass
            else:
                releases = [
                    r for r in releases
                    if platform in r['filename']
                    or re.search(r'\Wany\W', r['filename'])
                ]
            # TODO improve release selection
            assert len(
                releases) >= 1, 'No unique release available from {}'.format(
                    ', '.join(r['filename'] +
                              (' (selected)' if r in releases else '')
                              for r in data['releases'][self.version]))
            self._release_info = releases[0]
        return self._release_info

    @property
    def archive_url(self):
        if not self._archive_url:
            # TODO save and check digest
            self._archive_url = self.release_info['url']
        return self._archive_url
