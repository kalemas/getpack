from pathlib import Path
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_folder():
    folder = Path(tempfile.mkdtemp())
    yield folder
    shutil.rmtree(folder.as_posix())
