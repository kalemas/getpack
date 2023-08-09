from pathlib import Path
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_folder():
    folder = Path(tempfile.mkdtemp())
    yield folder
    try:
        shutil.rmtree(folder.as_posix())
    except Exception:
        print('Failed to cleanup {}'.format(folder))
