import getpack.library


def test_ffmpeg():
    ffmpeg = getpack.library.Ffmpeg()
    assert ffmpeg.version in ffmpeg('-version').decode()


def test_executable_override():
    python = getpack.library.Python()
    assert b'python.exe' in python('-c', 'import sys; print(sys.executable)')
    python = getpack.library.Python(executable_name='pythonw')
    assert b'pythonw.exe' in python('-c', 'import sys; print(sys.executable)')
