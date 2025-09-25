import shutil
import tempfile
import pytest


@pytest.fixture
def db_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def pytest_addoption(parser):
    # boolean flag: present -> True
    parser.addoption(
        "--no-rpc",
        action="store_false",
        default=True,
        help="Flag for turning rpc off"
    )

import pytest

@pytest.fixture
def rpc(request):
    return request.config.getoption("--no-rpc")
