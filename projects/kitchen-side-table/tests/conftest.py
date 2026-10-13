import pytest


@pytest.fixture(scope="session")
def table():
    from table.frame import build_table

    return build_table()


@pytest.fixture(scope="session")
def sheets(table):
    from table.sheets import make_sheets

    return {sheet.name: sheet for sheet in make_sheets(table)}
