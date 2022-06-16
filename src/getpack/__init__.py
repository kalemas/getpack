"""
Setup external resources that already available.


Copyright (c) 2022 Konstantin Maslyuk. All rights reserved.

This work is licensed under the terms of the MIT license.
For a copy, see <https://opensource.org/licenses/MIT>.
"""

from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile


class Resource:
    """Base resource."""
    name = None
    activated = False
    initialized = False

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
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

    def ensure_available(self):
        if self.initialized:
            return
        assert self.version, 'Resource should be versioned'
        if self.version in self.get_available_versions():
            return
        self.initialized = True
        self.make_available()

    def cleanup(self):
        path = self.get_path(self.name, self.version)
        if path.is_dir():
            shutil.rmtree(path)


class WebResource(LocalResource):
    """Resource acquired from the web."""
    archive_extraction = {'': {'path': ''}}

    def make_available(self):
        self.cleanup()

        request = urllib.request.urlopen(self.archive_url)
        # TODO raise for status
        # TODO extract to temporary folder then rename
        with zipfile.ZipFile(BytesIO(request.read())) as archive:
            for entity in archive.filelist:
                dest_path = ''
                for k, v in self.archive_extraction.items():
                    if entity.filename.startswith(k):
                        dest_path = v['path']
                        break
                else:
                    continue
                dest_path = self.get_path(self.name, self.version, dest_path,
                                          entity.filename)
                if not dest_path.parent.is_dir():
                    dest_path.parent.mkdir(parents=True)
                if dest_path.is_file():
                    dest_path.unlink()
                dest_path.write_bytes(archive.read(entity.filename))


class PythonPackage(LocalResource):
    """Python package."""
    local_prefix = 'python'

    def __call__(self, *_, **__):
        if self.activated:
            return
        self.ensure_available()
        self.activated = True
        sys.path.insert(0, str(self.get_path(self.name, self.version)))
        __import__(self.name)

    def __getattr__(self, key):
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
            for release in releases[:]:
                # TODO improve release selection
                if 'py3' not in release['python_version']:
                    releases.remove(release)
                elif 'win_amd64' not in release['filename']:
                    releases.remove(release)
                assert len(releases) == 1, 'Failed to choose release'
            # TODO save and check digest
            self._archive_url = releases[0]['url']
        return self._archive_url
