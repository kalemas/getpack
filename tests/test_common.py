import subprocess

from getpack import  library, WebPackage


def test_cefpython3():
    cefpython3 = WebPackage(
        name='cefpython3',
        archive_url=(
            'https://files.pythonhosted.org/packages/3b/d4/f313221a999e4d295'
            'cc8fcb15fc4ac9c98f6759e50735d6f6ce84fd3e98a/'
            'cefpython3-66.1-py2.py3-none-win_amd64.whl'),
        version='66.1',
    )
    assert cefpython3.__version__ == cefpython3.version


def test_pyside2():
    PySide2 = library.PySide2()
    PySide2.cleanup()
    assert PySide2.__version__ == PySide2.version


def test_cefpython3_pypi():
    cefpython3 = library.cefpython3()
    cefpython3.cleanup()
    assert cefpython3.__version__ == cefpython3.version


def test_blender():
    version = '3.2.2'
    blender = library.Blender(version=version)
    blender.cleanup()
    blender.__call__()
    executable = blender.path / ('blender' + blender.bin_ext)
    output = subprocess.check_output([executable, '--version'])
    assert version.encode() in output
