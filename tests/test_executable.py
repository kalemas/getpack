import getpack.library.ffmpeg


def test_ffmpeg():
    ffmpeg = getpack.library.ffmpeg.ffmpeg()
    assert ffmpeg.version in ffmpeg('-version').decode()
