from getpack import  library, resource


def test_cefpython3():
    cefpython3 = resource.WebPackage(
        name='cefpython3',
        archive_url=(
            'https://files.pythonhosted.org/packages/3b/d4/f313221a999e4d295'
            'cc8fcb15fc4ac9c98f6759e50735d6f6ce84fd3e98a/'
            'cefpython3-66.1-py2.py3-none-win_amd64.whl'),
        version='66.1',
    )
    assert cefpython3().__version__ == cefpython3.version
    assert '66.1' in cefpython3.get_available_versions()


def test_pyside2():
    PySide2 = library.PySide2()
    PySide2.cleanup()
    assert PySide2().__version__ == PySide2.version


def test_cefpython3_pypi():
    cefpython3 = library.cefpython3()
    assert not cefpython3._activated
    cefpython3.cleanup()
    assert not cefpython3._activated
    assert cefpython3().__version__ == cefpython3.version
    assert cefpython3._activated


def test_blender():
    version = '3.2.2'
    blender = library.Blender(version=version)
    assert not blender._available, (
        'Blender resource is not initialized and could not have _available '
        'flag set')
    blender.cleanup()
    blender.provide()
    output = blender('--version')
    assert version in output.decode()
