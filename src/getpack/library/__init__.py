"""
This module contain the library of available *getpack* resources.
"""
import sys

from .. import PyPiPackage


class cefpython3(PyPiPackage):
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
        return super()._deploy_to(path)


class ffmpeg:
    pass


class blender:
    pass


class rclone:
    pass
