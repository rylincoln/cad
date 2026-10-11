import pytest

from memorial import spec
from memorial.font import Font


@pytest.fixture(scope="session")
def font():
    return Font(spec.FONT_PATH)
