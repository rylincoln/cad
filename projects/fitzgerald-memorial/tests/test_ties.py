import pytest
from shapely.ops import unary_union

from memorial import spec
from memorial.rules import check_plate
from memorial.ties import tie_region, with_ties


@pytest.fixture(scope="module")
def tied(untied):
    return with_ties(untied, "tied")


def _glyphs(plate, key):
    line = plate.lines[key]
    return list(zip(line.chars, line.glyphs))


def test_no_letter_centre_is_left_to_drop_out(tied):
    assert all(not part.interiors for _, part in tied.cutouts)


def test_the_tied_plate_passes_every_rule_with_no_drop_outs(tied):
    assert check_plate(tied, full_text=True, drop_outs=False) == []


def test_bowl_letters_get_two_ties_and_the_rest_one(untied, tied):
    # two ties split a D or 0 into two pieces; one tie, or a widened neck, leaves a letter in one piece
    for key in untied.lines:
        if key == "surname":
            continue
        for (char, before), (_, after) in zip(_glyphs(untied, key), _glyphs(tied, key)):
            pieces = len(getattr(after, "geoms", [after]))
            assert pieces == (2 if before.interiors and char in spec.TWO_TIE_CHARS else 1), char


def test_each_tie_is_one_tie_width_of_plate(tied):
    d = dict(_glyphs(tied, "shared"))["D"]
    a, b = d.geoms
    assert a.distance(b) == pytest.approx(spec.TIE_WIDTH, abs=0.002)


def test_ties_take_only_a_narrow_strip_of_each_letter(untied, tied):
    # each tie, and each neck widened into one (at most two per letter, in an E), costs a strip of stroke
    for key in untied.lines:
        for (char, before), (_, after) in zip(_glyphs(untied, key), _glyphs(tied, key)):
            ties = 2 if char in spec.TWO_TIE_CHARS else 1
            centres = sum(len(p.interiors) for p in getattr(before, "geoms", [before]))
            removed = before.area - unary_union(after).area
            assert removed <= spec.TIE_WIDTH * 0.2 * (ties * centres + 2), char


def test_ties_change_only_the_lettering(untied, tied):
    # 25 centres: 21 in the Roman names and dates, 4 loops in the script surname
    assert sum(len(p.interiors) for _, p in untied.cutouts) == 25
    assert tied.outline.equals(untied.outline) and tied.holes == untied.holes and tied.knot == untied.knot


@pytest.mark.parametrize("width", [0.08])
def test_wider_ties_still_fit_the_small_letters(untied, width):
    # a wide tie's square ends must clear the tight curves inside the small 9, p and 6
    tied = with_ties(untied, "wide", width=width)
    assert check_plate(tied, full_text=True, drop_outs=False) == []
    d = dict(_glyphs(tied, "shared"))["D"]
    assert d.geoms[0].distance(d.geoms[1]) == pytest.approx(width, abs=0.002)


def test_a_script_word_in_several_pieces_has_every_loop_tied(untied, script_font):
    from dataclasses import replace

    from memorial.plate import move_line
    from memorial.text import set_word

    word = move_line(set_word(script_font, "Fitzgerald", em=2.4, min_stroke=0.065), 0, 1.4)
    assert sum(len(p.interiors) for p in word.glyphs[0].geoms) == 4  # loops of the z, g, e and d
    tied = with_ties(replace(untied, lines={"surname": word}), "script", width=0.08)
    assert all(not part.interiors for _, part in tied.cutouts)
    assert check_plate(tied, full_text=True, drop_outs=False) == []


def test_a_narrow_opening_into_a_centre_becomes_a_full_tie():
    # a C whose opening is only 0.02": the copper inside hangs by a hairline until the opening is
    # widened to a full tie (in Cinzel's E, the gap between an arm's serif and the next arm)
    from shapely.geometry import box

    ring = box(0, 0, 0.5, 0.5).difference(box(0.15, 0.15, 0.35, 0.35))
    letter = ring.difference(box(0.3, 0.24, 0.6, 0.26))
    tied = tie_region(letter, 1, 0.08)
    assert tied.geom_type == "Polygon" and not tied.interiors
    copper = box(-1, -1, 2, 2).difference(tied)
    assert copper.buffer(-0.0399).geom_type == "Polygon"  # the inside stays joined through 0.08"
    assert letter.area - tied.area < 0.08 * 0.2  # only the lips of the opening are trimmed
