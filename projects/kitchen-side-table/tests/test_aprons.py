import pytest

from table import spec
from table.aprons import dowel_depths, long_apron_length, make_aprons, make_coupon, side_apron_length


def _aprons():
    return {a.name: a for a in make_aprons()}


def test_the_long_aprons_are_26_75_and_the_side_aprons_15_178():
    assert long_apron_length() == pytest.approx(26.75)
    assert side_apron_length() == pytest.approx(15.178)
    assert _aprons()["front apron"].outline.bounds == pytest.approx((0, 0, 26.75, 2.971))
    assert _aprons()["left apron"].outline.bounds == pytest.approx((0, 0, 15.178, 2.971))


def test_the_dowel_holes_sit_an_inch_either_side_of_each_long_aprons_middle():
    aprons = _aprons()
    assert aprons["front apron"].dowels == pytest.approx((12.375, 14.375))
    assert aprons["back apron"].dowels == pytest.approx((12.375, 14.375))
    assert aprons["left apron"].dowels == () and aprons["right apron"].dowels == ()


def test_the_long_aprons_grooves_split_around_the_dowels():
    grooves = [[c for point in g.coords for c in point] for g in _aprons()["front apron"].grooves]
    assert grooves == [pytest.approx([2.375, 2.471, 11.59375, 2.471]), pytest.approx([15.15625, 2.471, 24.375, 2.471])]


def test_the_side_aprons_groove_stops_half_an_inch_short_of_the_housings():
    grooves = [[c for point in g.coords for c in point] for g in _aprons()["left apron"].grooves]
    assert grooves == [pytest.approx([1.375, 2.471, 13.803, 2.471])]


def test_each_joint_is_the_end_that_goes_into_a_leg():
    aprons = _aprons()
    assert [j.bounds for j in aprons["front apron"].joints] == [pytest.approx((0, 0, 1.75, 2.971)), pytest.approx((25.0, 0, 26.75, 2.971))]
    assert [j.bounds for j in aprons["left apron"].joints] == [pytest.approx((0, 0, 0.75, 2.971)), pytest.approx((14.428, 0, 15.178, 2.971))]


def test_the_coupon_is_3_by_1_75():
    assert make_coupon().outline.bounds == pytest.approx((0, 0, 3.0, 1.75))


def test_the_dowel_holes_leave_a_quarter_inch_of_cherry_and_room_for_glue():
    assert dowel_depths() == pytest.approx((0.5, 1.0625))


def test_the_dowel_holes_follow_a_top_sanded_thinner(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.72)
    assert dowel_depths() == pytest.approx((0.47, 1.0925))
