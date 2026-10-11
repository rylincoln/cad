import itertools

import pytest
from shapely.ops import unary_union

from memorial.text import set_line, set_word


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


@pytest.mark.parametrize("text, em", [("Mary Theresa", 0.771), ("Feb 6, 1935", 0.679), ("Apr 19, 1939", 0.679),
                                      ("December 30, 2025", 0.700)])
def test_thickening_closes_loops_with_a_cuttable_wall(font, text, em):
    # thickening closes the small r, p, 6, 9 and B loops; the joint must be wide enough to cut,
    # so every letter centre still drops out instead of staying tacked to the plate
    line = set_line(font, text, em=em, thicken=0.012, min_slot=0.05)
    for char, glyph in zip(line.chars, line.glyphs):
        core = glyph.buffer(-0.025)
        assert core.geom_type == "Polygon" and len(core.interiors) == len(glyph.interiors), char


def test_widening_takes_only_what_each_wall_needs_and_keeps_the_outline(font):
    from shapely.geometry import Polygon

    for text, em in [("Feb 6, 1935", 0.679), ("Apr 19, 1939", 0.679), ("Mary Theresa", 0.771)]:
        plain = set_line(font, text, em=em, thicken=0.012)
        fixed = set_line(font, text, em=em, thicken=0.012, min_slot=0.05)
        for char, a, b in zip(plain.chars, plain.glyphs, fixed.glyphs):
            dx = b.bounds[0] - a.bounds[0]
            a_outline = Polygon(a.exterior.coords)
            b_outline = Polygon([(x - dx, y) for x, y in b.exterior.coords])
            assert a_outline.symmetric_difference(b_outline).area < 1e-5, char
            before = sum(Polygon(r).area for r in a.interiors)
            after = sum(Polygon(r).area for r in b.interiors)
            if before:
                assert after / before >= 0.78, (char, after / before)


def _parts(glyph):
    return list(getattr(glyph, "geoms", [glyph]))


@pytest.fixture(scope="module")
def script_word(script_font):
    return set_word(script_font, "Fitzgerald", em=2.58, min_stroke=0.065)


def test_a_script_word_is_one_joined_cut_beside_its_capital_and_i_dot(script_word):
    assert script_word.chars == ("Fitzgerald",) and len(script_word.glyphs) == 1
    parts = sorted(_parts(script_word.glyphs[0]), key=lambda p: p.area)
    assert len(parts) == 3 and parts[0].area < 0.05  # the i's dot, the F, and "itzgerald" joined


def test_every_script_stroke_is_at_least_the_minimum_width(script_word):
    for part in _parts(script_word.glyphs[0]):
        core = part.buffer(-0.065 / 2)
        assert core.geom_type == "Polygon" and len(core.interiors) == len(part.interiors)


def test_a_stroke_that_nearly_touches_another_is_trimmed_back(script_font, script_word):
    # Great Vibes' F crossbar swash tapers to a point 0.036" short of the t: too little copper to keep,
    # so the tip is trimmed back to leave 0.06"
    untrimmed = set_word(script_font, "Fitzgerald", em=2.58, min_stroke=0.065, min_copper=0.0)
    before = _parts(untrimmed.glyphs[0])
    assert min(a.distance(b) for a, b in itertools.combinations(before, 2)) < 0.04
    after = _parts(script_word.glyphs[0])
    assert min(a.distance(b) for a, b in itertools.combinations(after, 2)) >= 0.06 - 1e-9
    assert sum(p.area for p in before) - sum(p.area for p in after) < 0.002  # only the tip


def test_a_script_word_is_centred_on_its_ink(script_word):
    minx, _, maxx, _ = script_word.glyphs[0].bounds
    assert minx == pytest.approx(-maxx, abs=1e-9) and script_word.width == pytest.approx(maxx - minx)
