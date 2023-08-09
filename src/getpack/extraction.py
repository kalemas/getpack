from io import BytesIO
import tarfile
import zipfile


class ArchiveExtractor:
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, exc_traceback):
        raise NotImplementedError

    def get_file_list(self):
        raise NotImplementedError

    def get_bytes(self, filename):
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
        return [
            f.filename
            for f in self.zipfile.filelist
            # skip folders
            if f.filename[-1] != '/'
        ]

    def get_bytes(self, filename):
        return self.zipfile.read(filename)


class TarExtractor(ArchiveExtractor):
    def __enter__(self):
        self.obj = tarfile.open(fileobj=BytesIO(self.stream.read()))
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.obj.close()

    def get_file_list(self):
        files = [f.name for f in self.obj.getmembers()]
        for i in reversed(range(len(files))):
            for ii in files[i:]:
                if ii.startswith(files[i] + '/'):
                    break
            else:
                continue
            del files[i]
        return files

    def get_bytes(self, filename):
        return self.obj.extractfile(filename).read()
