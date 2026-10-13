import pytest


@pytest.fixture(scope="session")
def table():
    from table.frame import build_table

    return build_table()
