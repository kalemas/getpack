from io import BytesIO
import os
from pathlib import Path
import sys
import urllib.request
import zipfile


class Resource:
    name = None
    local_base = Path(os.getenv('APPDATA')) / 'redeploy'
    initialized = False
    activated = False

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_available_versions(self):
        path = self.local_base / self.name
        if path.is_dir():
            return os.listdir(path)
        return []

    def ensure_avaialble(self):
        if self.initialized:
            return
        assert self.version, 'Resource should be versioned'
        if self.version in self.get_available_versions():
            return
        self.initialized = True
        self.make_available()

    def make_available(self):
        raise NotImplemented

    def activate(self):
        raise NotImplemented


class WebResource(Resource):
    archive_extraction = {'': {'path': ''}}

    def make_available(self):
        request = urllib.request.urlopen(self.archive_url)
        with zipfile.ZipFile(BytesIO(request.read())) as archive:
            for entity in archive.filelist:
                destpath = ''
                for k ,v in self.archive_extraction.items():
                    if entity.filename.startswith(k):
                        destpath = v['path']
                        break
                else:
                    continue
                destpath = (self.local_base / self.name / self.version /
                            destpath / entity.filename)
                if not destpath.parent.is_dir():
                    destpath.parent.mkdir(parents=True)
                if destpath.is_file():
                    destpath.unlink()
                destpath.write_bytes(archive.read(entity.filename))


class WebPackage(WebResource):
    local_base = WebResource.local_base / 'python'

    def activate(self):
        if self.activated:
            return
        self.ensure_avaialble()
        self.activated = True
        sys.path.insert(0, str(self.local_base / self.name / self.version))
        __import__(self.name)

    def __getattr__(self, key):
        self.activate()
        return getattr(sys.modules[self.name], key)


if __name__ == '__main__':
    cefpython3 = WebPackage(
        name='cefpython3',
        archive_url=(
            'https://files.pythonhosted.org/packages/3b/d4/f313221a999e4d295'
            'cc8fcb15fc4ac9c98f6759e50735d6f6ce84fd3e98a/'
            'cefpython3-66.1-py2.py3-none-win_amd64.whl'),
        version='66.1',
        )
    print(cefpython3.__version__)
