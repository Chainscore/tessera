import shutil
import tempfile
import pytest


@pytest.fixture
def db_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
