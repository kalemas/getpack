from ..executable import Executable
from ..resource import WebResource


class ffmpeg(Executable, WebResource):
    name = 'ffmpeg'
    version = '5.1.2'
    archive_url = (
        'https://github.com/GyanD/codexffmpeg/releases/download/'
        '{self.version}/ffmpeg-{self.version}-essentials_build.zip')
    archive_extraction = {
        'ffmpeg-{self.version}-essentials_build/bin/': {
            'path': '',
        },
    }
    executable = 'ffmpeg'
