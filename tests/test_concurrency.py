from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from getpack.library.ffmpeg import ffmpeg


def test_threads_ffmpeg_deployment():
    pool = ThreadPoolExecutor(6)
    resources = [
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
        ffmpeg(version='5.1.1'),
    ]
    list(pool.map(lambda r: r.cleanup(), resources))
    list(pool.map(lambda r: r.provide(), resources))


def _cleanup_stub(id):
    resoruce = ffmpeg(version='5.1.1')
    resoruce.cleanup()


def _provide_stub(id):
    resoruce = ffmpeg(version='5.1.1')
    resoruce.provide()


def test_processes_ffmpeg_deployment():
    pool = ProcessPoolExecutor(5)
    list(pool.map(_cleanup_stub, range(5)))
    list(pool.map(_provide_stub, range(5)))
