import pytest
from shapely.ops import unary_union

from memorial import spec
from memorial.rules import check_plate
from memorial.ties import with_ties


@pytest.fixture(scope="module")
def tied(final):
    return with_ties(final, "final_sendcutsend")


def _glyphs(plate, key):
    line = plate.lines[key]
    return list(zip(line.chars, line.glyphs))


def test_no_letter_centre_is_left_to_drop_out(tied):
    assert all(not part.interiors for _, part in tied.cutouts)


def test_the_tied_plate_passes_every_rule_with_no_drop_outs(tied):
    assert check_plate(tied, full_text=True, drop_outs=False) == []


def test_bowl_letters_get_two_ties_and_the_rest_one(final, tied):
    # two ties split a D or 0 into two pieces; one tie leaves a letter in one piece
    for key in final.lines:
        for (char, before), (_, after) in zip(_glyphs(final, key), _glyphs(tied, key)):
            pieces = len(getattr(after, "geoms", [after]))
            if not before.interiors:
                assert after.equals(before), char
            elif char in spec.TWO_TIE_CHARS:
                assert pieces == 2, char
            else:
                assert pieces == 1, char


def test_each_tie_is_one_tie_width_of_plate(tied):
    d = dict(_glyphs(tied, "surname"))["D"]
    a, b = d.geoms
    assert a.distance(b) == pytest.approx(spec.TIE_WIDTH, abs=0.002)


def test_ties_take_only_a_narrow_strip_of_each_letter(final, tied):
    for key in final.lines:
        for (char, before), (_, after) in zip(_glyphs(final, key), _glyphs(tied, key)):
            ties = 2 if char in spec.TWO_TIE_CHARS else 1
            removed = before.area - unary_union(after).area
            assert removed <= ties * spec.TIE_WIDTH * 0.2 * len(before.interiors), char


def test_the_glue_back_plate_is_unchanged(final, tied):
    assert sum(len(p.interiors) for _, p in final.cutouts) == 23
    assert tied.outline.equals(final.outline) and tied.holes == final.holes and tied.knot == final.knot


@pytest.mark.parametrize("width", [0.08])
def test_wider_ties_still_fit_the_small_letters(final, width):
    # a wide tie's square ends must clear the tight curves inside the small 9, p and 6
    tied = with_ties(final, "wide", width=width)
    assert check_plate(tied, full_text=True, drop_outs=False) == []
    d = dict(_glyphs(tied, "surname"))["D"]
    assert d.geoms[0].distance(d.geoms[1]) == pytest.approx(width, abs=0.002)


def test_a_script_word_in_several_pieces_has_every_loop_tied(final, script_font):
    from dataclasses import replace

    from memorial.plate import move_line
    from memorial.text import set_word

    word = move_line(set_word(script_font, "Fitzgerald", em=2.4, min_stroke=0.065), 0, 1.4)
    assert sum(len(p.interiors) for p in word.glyphs[0].geoms) == 4  # loops of the z, g, e and d
    tied = with_ties(replace(final, lines={"surname": word}), "script", width=0.08)
    assert all(not part.interiors for _, part in tied.cutouts)
    assert check_plate(tied, full_text=True, drop_outs=False) == []
