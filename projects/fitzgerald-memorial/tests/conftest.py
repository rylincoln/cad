import pytest

from memorial import spec
from memorial.font import Font


@pytest.fixture(scope="session")
def font():
    return Font(spec.FONT_PATH)


@pytest.fixture(scope="session")
def script_font():
    return Font(spec.SCRIPT_FONT_PATH)


@pytest.fixture(scope="session")
def untied(font, script_font):
    from memorial.plate import layout_final

    return layout_final(font, script_font)


@pytest.fixture(scope="session")
def final(font, script_font):
    from memorial.plate import build_final

    return build_final(font, script_font)


@pytest.fixture(scope="session")
def practice(final):
    from memorial.plate import build_practice

    return build_practice(final)
