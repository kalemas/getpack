import getpack.library.ffmpeg
import getpack.library


def test_ffmpeg():
    ffmpeg = getpack.library.ffmpeg.ffmpeg()
    assert ffmpeg.version in ffmpeg('-version').decode()


def test_executable_override():
    python = getpack.library.Python()
    assert python.executable.name == 'python.exe'
    python = getpack.library.Python(executable_name='pythonw')
    assert python.executable.name == 'pythonw.exe'
