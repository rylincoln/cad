import itertools

import pytest
from shapely.ops import unary_union

from memorial.text import set_line


def test_thickened_names_never_have_a_neck_under_the_slot_rule(font):
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.012, min_gap=0.06)
    for glyph in line.glyphs:
        core = glyph.buffer(-0.025)
        assert core.geom_type == "Polygon" and not core.is_empty


def test_unthickened_names_would_break_the_slot_rule(font):
    # documents why the small text is thickened
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.0, min_gap=0.0)
    assert any(g.buffer(-0.025).geom_type != "Polygon" for g in line.glyphs)


def test_every_visible_character_becomes_one_region(font):
    line = set_line(font, "Feb 6, 1935", em=0.679, thicken=0.012)
    assert "".join(line.chars) == "Feb6,1935"
    assert len(line.glyphs) == 9
    assert all(g.geom_type == "Polygon" for g in line.glyphs)


def test_letters_keep_the_minimum_copper_between_them(font):
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.012, min_gap=0.06)
    assert min(a.distance(b) for a, b in itertools.combinations(line.glyphs, 2)) >= 0.06 - 1e-9


def test_only_the_tight_pair_in_the_surname_is_opened(font):
    line = set_line(font, "FITZGERALD", em=1.664, tracking_em=0.045, thicken=0.0, min_gap=0.06)
    assert [char for char, _ in line.pushes] == ["A"]  # R and A are kerned into contact


def test_line_is_centred_on_its_ink(font):
    line = set_line(font, "December 30, 2025", em=0.7, thicken=0.012)
    minx, _, maxx, _ = unary_union(line.glyphs).bounds
    assert minx == pytest.approx(-maxx, abs=1e-9)
    assert line.width == pytest.approx(maxx - minx)


def test_capitals_sit_on_the_baseline(font):
    line = set_line(font, "FITZGERALD", em=1.664, tracking_em=0.045)
    _, miny, _, maxy = unary_union(line.glyphs).bounds
    assert 0.69 * 1.664 < maxy < 0.73 * 1.664
    assert -0.03 < miny < 0.0


def test_widths_match_the_approved_cuttable_preview(font):
    widths = {
        "FITZGERALD": set_line(font, "FITZGERALD", 1.664, 0.045, 0.0).width,
        "Mary Theresa": set_line(font, "Mary Theresa", 0.771, 0.0, 0.012).width,
        "James Guinn": set_line(font, "James Guinn", 0.771, 0.0, 0.012).width,
        "Feb 6, 1935": set_line(font, "Feb 6, 1935", 0.679, 0.0, 0.012).width,
        "Apr 19, 1939": set_line(font, "Apr 19, 1939", 0.679, 0.0, 0.012).width,
        "December 30, 2025": set_line(font, "December 30, 2025", 0.700, 0.0, 0.012).width,
    }
    expected = {"FITZGERALD": 11.700, "Mary Theresa": 6.285, "James Guinn": 5.468,
                "Feb 6, 1935": 3.581, "Apr 19, 1939": 4.094, "December 30, 2025": 6.968}
    for text, width in widths.items():
        assert width == pytest.approx(expected[text], abs=0.05), text
