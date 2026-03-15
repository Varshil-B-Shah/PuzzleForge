import pytest
from db import database


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Reset DB path to a fresh temp database before every test."""
    database.init_db(str(tmp_path / "test.db"))
    yield
