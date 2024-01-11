"""
This module contain the library of available *getpack* resources.
"""
import sys
import platform

from ..resource import PyPiPackage, WebResource
from ..executable import Executable


class CefPython3(PyPiPackage):
    name = 'cefpython3'
    version = '66.1'

    if sys.version_info.major == 3 and sys.version_info.minor == 10:
        version = '88.0'
        archive_url = (
            'https://github.com/HonorarPlus/cefpython/releases/'
            'download/v88.2_py310/cefpython3-88.0-cp310-none-win_amd64'
            '.whl')


class PySide2(PyPiPackage):
    """
    Qt.

    Minimal working snippet:
    ```python
    import getpack.library
    getpack.library.PySide2(version='5.12.1')()  # call resource to make effect
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication()
    widget = QtWidgets.QWidget()
    widget.show()
    app.exec_()
    ```
    """
    name = 'PySide2'
    version = '5.15.2'

    def _deploy_to(self, path):
        # this should be installed into the same dir as PySide itself
        PyPiPackage('shiboken2', self.version)._deploy_to(path)
        return super(PySide2, self)._deploy_to(path)

    def get_available_versions(self):
        # fix installations with regular PyPiPackage('PySide2')
        versions = []
        for i in super(PySide2, self).get_available_versions():
            if ((self.path.with_name(i) / 'PySide2').is_dir()
                    and (self.path.with_name(i) / 'shiboken2').is_dir()):
                versions.append(i)
        return versions


class Blender(Executable, WebResource):
    name = 'blender'
    architecture = 'x64'
    version = '3.6.7'
    archive_url = ('https://download.blender.org/release/'
                   'Blender{self.version_minor}/'
                   'blender-{self.version}-{self.platform}-'
                   '{self.architecture}.zip')
    archive_extraction = {
        'blender-{self.version}-{self.platform}-{self.architecture}/': {
            'path': ''
        },
    }

    @property
    def version_minor(self):
        return '.'.join(self.version.split('.')[:2])

    @property
    def platform(self):
        if platform.system() == 'Darwin':
            return 'macos'
        return platform.system().lower()


class Rclone:
    version = '1.62.2'
    platform = 'windows-amd64'
    archive_url = (
        'https://downloads.rclone.org/v{self.version}/'
        'rclone-v{self.version}-{self.platform}.zip')


class Python(Executable, WebResource):
    name = 'python'
    version = '3.7.9'
    archive_url = (
        'https://www.python.org/ftp/python/{self.version}/'
        'python-{self.version}-embed-amd64.zip')


class Ffmpeg(Executable, WebResource):
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
