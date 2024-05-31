from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from getpack.library import Python


def test_threads(temp_folder, background_scanner):
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
    futures = []
    with ThreadPoolExecutor(6) as pool:
        for r in resources:
            futures.append(pool.submit(r.cleanup))
        for r in resources:
            futures.append(pool.submit(r.provide))
        for r in resources:
            futures.append(pool.submit(r.cleanup))
        for r in resources:
            futures.append(pool.submit(r.provide))
        for f in futures:
            f.result()



def _cleanup_stub(id, folder):
    resource = Python(local_base=folder)
    resource.cleanup()


def _provide_stub(id, folder):
    resource = Python(local_base=folder)
    resource.provide()


def test_processes(temp_folder, background_scanner):
    num = 16
    futures = []
    with ProcessPoolExecutor(num) as pool:
        for i in range(num):
            futures.append(pool.submit(_cleanup_stub, i, temp_folder))
        for i in range(num):
            futures.append(pool.submit(_provide_stub, i, temp_folder))
        for i in range(num):
            futures.append(pool.submit(_cleanup_stub, i, temp_folder))
        for i in range(num):
            futures.append(pool.submit(_provide_stub, i, temp_folder))
        for f in futures:
            f.result()
