import pytest

from memorial import spec
from memorial.font import Font


@pytest.fixture(scope="session")
def font():
    return Font(spec.FONT_PATH)


@pytest.fixture(scope="session")
def final(font):
    from memorial.plate import build_final

    return build_final(font)
