import pytest
from shapely.geometry import Point, box

from table import spec
from table.legs import (dogbone, fit_test_pockets, housing_width, inside_faces_apart, leg_length, leg_width,
                        make_leg, make_legs)


def test_the_legs_are_31_25_long_so_the_table_is_32_tall():
    assert leg_length() == pytest.approx(31.25)


def test_a_leg_is_1_75_wide_at_the_foot_and_flares_to_3_25_at_the_aprons():
    assert leg_width(0.0) == pytest.approx(1.75)
    assert leg_width(28.25) == pytest.approx(3.25)
    assert leg_width(31.25) == pytest.approx(3.25)
    widths = [leg_width(28.25 * i / 50) for i in range(51)]
    assert widths == sorted(widths)


def test_the_front_left_and_back_right_legs_flare_to_the_left_seen_from_the_inside_face():
    assert make_leg("front-left").outline.bounds == pytest.approx((-3.25, 0.0, 0.0, 31.25))
    assert make_leg("back-right").outline.bounds == pytest.approx((-3.25, 0.0, 0.0, 31.25))
    assert make_leg("front-right").outline.bounds == pytest.approx((0.0, 0.0, 3.25, 31.25))
    assert make_leg("back-left").outline.bounds == pytest.approx((0.0, 0.0, 3.25, 31.25))


def test_the_housing_is_the_plywood_plus_clearance_wide_and_open_at_the_top():
    leg = make_leg("front-right")
    assert housing_width() == pytest.approx(0.728)
    assert leg.housing.contains(box(0.375, 28.25, 1.103, 31.25))
    assert leg.housing.bounds[3] == pytest.approx(31.25 + spec.OPEN_END)


def test_the_lap_is_open_at_the_inner_edge_and_the_top():
    leg = make_leg("front-right")
    assert leg.lap.contains(box(1.5, 28.25, 3.25, 31.25))
    assert leg.lap.bounds[2] == pytest.approx(3.25 + spec.OPEN_END)
    assert leg.lap.bounds[3] == pytest.approx(31.25 + spec.OPEN_END)


def test_a_dogbone_lets_the_bit_reach_right_into_a_square_corner():
    r = spec.BIT_DIAMETER / 2
    with_dogbone = box(0, 0, 1, 1).union(dogbone((0, 0), (1, 1)))
    without = box(0, 0, 1, 1)
    corner = Point(0.002, 0.002)
    assert with_dogbone.buffer(-r, quad_segs=32).buffer(r, quad_segs=32).contains(corner)
    assert not without.buffer(-r, quad_segs=32).buffer(r, quad_segs=32).contains(corner)


def test_there_are_four_legs_named_for_their_corners():
    assert [leg.name for leg in make_legs()] == ["front-left", "front-right", "back-left", "back-right"]


def test_the_legs_inside_faces_are_13_678_apart_front_to_back():
    assert inside_faces_apart() == pytest.approx(13.678)


def test_the_fit_test_pockets_take_the_coupon():
    housing, lap = fit_test_pockets()
    assert housing.contains(box(0, 0, 0.723, 1.75))
    assert lap.contains(box(0, 0, 3.0, 1.75))
