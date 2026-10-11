from shapely.geometry import LineString, Polygon, box

from memorial.plate import Plate
from memorial.rules import check_plate
from memorial.text import SetLine


def _plate(letters=(), chars=None, text=None, holes=(), knot=()):
    outline = box(-8, -4.75, 8, 4.75)
    border = LineString(outline.buffer(-0.375, join_style="mitre").exterior.coords)
    chars = tuple(chars if chars is not None else "X" * len(letters))
    line = SetLine(text if text is not None else "".join(chars), chars, tuple(letters), 1.0)
    return Plate("test", (18.0, 10.0), (9.0, 5.0), outline, (border,), {"line": line}, tuple(knot), tuple(holes))


def _square(x, y, size=0.2):
    return box(x, y, x + size, y + size)


def test_a_clean_plate_passes():
    assert check_plate(_plate([_square(0, 0), _square(0.3, 0)]), full_text=True) == []


def test_too_little_copper_between_cutouts_is_reported():
    problems = check_plate(_plate([_square(0, 0), _square(0.25, 0)]), full_text=True)
    assert len(problems) == 1 and "copper between" in problems[0]


def test_a_neck_narrower_than_the_slot_rule_is_reported():
    dumbbell = _square(0, 0).union(box(0.2, 0.08, 0.6, 0.12)).union(_square(0.6, 0))
    problems = check_plate(_plate([dumbbell]), full_text=True)
    assert any("slot narrower" in p for p in problems)


def test_sharp_corners_are_not_slot_problems():
    sliver_tip = Polygon([(0, 0), (1.0, 0.1), (0, 0.3)])  # wide body, needle-sharp tip
    assert check_plate(_plate([sliver_tip]), full_text=True) == []


def test_a_tiny_letter_centre_is_reported():
    letter = Polygon(box(0, 0, 0.5, 0.5).exterior.coords, [box(0.23, 0.23, 0.27, 0.27).exterior.coords])
    problems = check_plate(_plate([letter]), full_text=True)
    assert any("letter centre" in p for p in problems)


def test_a_cutout_too_close_to_the_border_is_reported():
    problems = check_plate(_plate([_square(7.3, 0)]), full_text=True)
    assert any("from the border" in p for p in problems)


def test_a_pin_hole_off_the_border_is_reported():
    problems = check_plate(_plate([_square(0, 0)], holes=[(2.0, 2.0)]), full_text=True)
    assert any("off the border line" in p for p in problems)


def test_a_missing_character_is_reported_when_the_full_text_is_required():
    plate = _plate([_square(0, 0)], chars="A", text="AB")
    assert any("missing characters" in p for p in check_plate(plate, full_text=True))
    assert check_plate(plate, full_text=False) == []


def test_letters_that_run_together_are_reported():
    problems = check_plate(_plate([_square(0, 0), _square(0.1, 0)]), full_text=True)
    assert any("run together" in p for p in problems)


def test_the_real_final_plate_passes_every_rule(final):
    assert check_plate(final, full_text=True) == []


def test_a_thin_wall_around_a_letter_centre_is_reported():
    # the counter's wall to the outside is only 0.02" on one side: the bit cannot cut it,
    # so the centre would stay tacked to the plate instead of dropping out
    letter = Polygon(box(0, 0, 0.5, 0.5).exterior.coords, [box(0.1, 0.1, 0.48, 0.4).exterior.coords])
    problems = check_plate(_plate([letter]), full_text=True)
    assert any("slot narrower" in p for p in problems)
