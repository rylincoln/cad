import pytest
from shapely.ops import unary_union

from memorial import spec
from memorial.rules import check_plate
from memorial.ties import with_ties


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
    # two ties split a D or 0 into two pieces; one tie leaves a letter in one piece
    for key in untied.lines:
        if key == "surname":
            continue
        for (char, before), (_, after) in zip(_glyphs(untied, key), _glyphs(tied, key)):
            pieces = len(getattr(after, "geoms", [after]))
            if not before.interiors:
                assert after.equals(before), char
            elif char in spec.TWO_TIE_CHARS:
                assert pieces == 2, char
            else:
                assert pieces == 1, char


def test_each_tie_is_one_tie_width_of_plate(tied):
    d = dict(_glyphs(tied, "shared"))["D"]
    a, b = d.geoms
    assert a.distance(b) == pytest.approx(spec.TIE_WIDTH, abs=0.002)


def test_ties_take_only_a_narrow_strip_of_each_letter(untied, tied):
    for key in untied.lines:
        for (char, before), (_, after) in zip(_glyphs(untied, key), _glyphs(tied, key)):
            ties = 2 if char in spec.TWO_TIE_CHARS else 1
            centres = sum(len(p.interiors) for p in getattr(before, "geoms", [before]))
            removed = before.area - unary_union(after).area
            assert removed <= ties * spec.TIE_WIDTH * 0.2 * centres, char


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
