"""
This module will demonstrate *getpack*
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

    def __init__(self, **kwargs):
        super(PySide2, self).__init__(**kwargs)
        if not self.requirements:
            self.requirements = [PyPiPackage('shiboken2', self.version)]


class ffmpeg:
    pass


class blender:
    pass
