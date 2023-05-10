from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from getpack.library import Python


def test_threads(temp_folder):
    pool = ThreadPoolExecutor(6)
    resources = [
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
        Python(local_base=temp_folder),
    ]
    list(pool.map(lambda r: r.cleanup(), resources))
    list(pool.map(lambda r: r.provide(), resources))


def _cleanup_stub(id, folder):
    resource = Python(local_base=folder)
    resource.cleanup()


def _provide_stub(id, folder):
    resource = Python(local_base=folder)
    resource.provide()


def test_processes(temp_folder):
    num = 30
    pool = ProcessPoolExecutor(num)
    list(pool.map(_cleanup_stub, range(num), [temp_folder] * num))
    list(pool.map(_provide_stub, range(num), [temp_folder] * num))
