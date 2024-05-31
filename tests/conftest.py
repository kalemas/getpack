import os
import shutil
import tempfile
import threading
from pathlib import Path

import pytest


@pytest.fixture
def temp_folder():
    folder = Path(tempfile.mkdtemp())
    yield folder
    try:
        shutil.rmtree(folder.as_posix())
    except Exception:
        print('Failed to cleanup {}'.format(folder))


@pytest.fixture
def background_scanner(temp_folder):
    """
    This fixture emulates antivirus scanning for downloaded files, that would
    cause issues on renaming or removing temporary folders.
    """
    stop = False
    read_bytes = 0

    def reader():
        nonlocal read_bytes

        while not stop:
            try:
                for path, _, files in os.walk(temp_folder):
                    for file in files:
                        try:
                            with open(os.path.join(path, file), 'rb') as f:
                                while True:
                                    b = f.read(8 * 1024)
                                    read_bytes += len(b)
                                    if stop:
                                        return
                                    if not b:
                                        break
                        except Exception:
                            pass
            except Exception:
                pass

    thread = threading.Thread(target=reader)
    thread.start()

    yield

    stop = True
    thread.join()
    assert read_bytes > 0
