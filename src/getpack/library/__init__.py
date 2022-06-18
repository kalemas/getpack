"""
This module contain the library of available *getpack* resources.
"""
from .. import PyPiPackage


class cefpython3(PyPiPackage):
    name = 'cefpython3'
    version = '66.1'


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
