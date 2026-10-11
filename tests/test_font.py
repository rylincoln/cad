import hashlib

import pytest

from memorial import spec

ALL_CHARS = sorted(set("".join(line.text for line in spec.LINES.values())) - {" "})


def test_text_is_exactly_what_the_family_approved():
    assert [line.text for line in spec.LINES.values()] == [
        "FITZGERALD", "Mary Theresa", "James Guinn", "Feb 6, 1935", "Apr 19, 1939", "December 30, 2025"]


def test_font_file_is_the_pinned_cinzel_bold():
    assert hashlib.sha256(spec.FONT_PATH.read_bytes()).hexdigest() == spec.FONT_SHA256


def test_cap_height_is_seven_tenths_of_an_em(font):
    assert font.cap_height == pytest.approx(0.700)
    assert font.outline(font.glyph_name("H")).bounds[3] == pytest.approx(0.700, abs=0.002)


@pytest.mark.parametrize("char", ALL_CHARS)
def test_every_character_is_one_solid_region(font, char):
    shape = font.outline(font.glyph_name(char))
    assert shape.geom_type == "Polygon"
    assert shape.area > 0.02


def test_reverse_wound_digit_one_is_still_filled(font):
    # Cinzel draws "1" with its single contour wound the other way; a naive fill drops it.
    assert font.outline(font.glyph_name("1")).area == pytest.approx(0.1067, abs=0.002)


def test_counters_are_holes_and_open_bowls_are_not(font):
    def holes(char):
        return len(font.outline(font.glyph_name(char)).interiors)

    assert [holes(c) for c in "ADab0"] == [1, 1, 1, 1, 1]
    assert [holes(c) for c in "R69p"] == [0, 0, 0, 0]


def test_pair_kerning_comes_from_gpos(font):
    assert font.kerning("R", "A") == pytest.approx(-0.012)
    assert font.kerning("H", "H") == 0.0


def test_advance_is_in_em(font):
    assert 0.5 < font.advance(font.glyph_name("H")) < 1.0


def test_unknown_character_is_a_clear_error(font):
    with pytest.raises(ValueError, match="no glyph"):
        font.glyph_name("☃")


def test_the_script_font_is_the_pinned_great_vibes():
    assert hashlib.sha256(spec.SCRIPT_FONT_PATH.read_bytes()).hexdigest() == spec.SCRIPT_FONT_SHA256
