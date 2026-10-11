import pytest
from shapely.geometry import Point, box

from memorial import spec
from memorial.rules import check_plate

KEEP = box(-8.0 + 0.25, -3.75 + 0.25, 4.5 - 0.25, 3.75 - 0.25)


def test_practice_outline_is_the_12_5_by_7_5_window(practice):
    assert practice.outline.bounds == pytest.approx((-8.0, -3.75, 4.5, 3.75), abs=1e-6)


def test_practice_keeps_only_whole_glyphs_inside_the_margin(practice):
    for label, region in practice.cutouts:
        assert KEEP.contains(region), label
    for h in practice.holes:
        assert KEEP.contains(Point(h).buffer(spec.HOLE_DIAMETER / 2))


def test_practice_contains_the_hardest_details(practice):
    assert len(practice.knot) == 3
    assert "".join(practice.lines["date_left"].chars) == "Feb6,1935"
    assert "".join(practice.lines["name_left"].chars) == "MaryTheresa"
    assert "".join(practice.lines["shared"].chars) == "December30,2025"
    assert "".join(practice.lines["surname"].chars).startswith("FITZG")
    assert len(practice.holes) == 3


def test_practice_border_is_an_open_arc_inside_the_margin(practice):
    assert practice.border
    for line in practice.border:
        assert not line.is_ring
        assert KEEP.buffer(1e-9).contains(line)
    assert sum(line.length for line in practice.border) > 9.0  # the left arc is about 9.85" long


def test_practice_sits_on_its_sheet_with_quarter_inch_margins(practice):
    assert practice.sheet == (13.0, 8.0)
    assert practice.offset == (8.25, 4.0)


def test_practice_passes_every_rule(practice):
    assert check_plate(practice, full_text=False) == []


def test_outline_only_has_nothing_but_the_oval(final):
    from memorial.plate import outline_only

    plate = outline_only(final)
    assert plate.name == "plate_outline"
    assert plate.cutouts == [] and plate.holes == () and plate.border == ()
    assert plate.outline.equals(final.outline)
