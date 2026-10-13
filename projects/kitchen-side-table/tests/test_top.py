import pytest
from shapely.geometry import Point

from table.top import front_edge_y, top_outline, top_size


def test_the_finished_top_is_the_glue_up_less_the_trim():
    assert top_size() == pytest.approx((31.75, 23.75))


def test_the_front_edge_starts_2_25_back_at_the_left_and_reaches_the_front_at_82_percent():
    w, _ = top_size()
    assert front_edge_y(0.0) == pytest.approx(2.25)
    assert front_edge_y(0.82 * w) == pytest.approx(0.0)
    assert front_edge_y(w) == pytest.approx(0.0)
    assert all(front_edge_y(w * i / 20) >= front_edge_y(w * (i + 1) / 20) for i in range(20))


def test_the_top_is_21_5_deep_at_the_left_end_and_23_75_at_the_right():
    w, d = top_size()
    assert d - front_edge_y(0.0) == pytest.approx(21.5)
    assert d - front_edge_y(w) == pytest.approx(23.75)


def test_the_outline_fills_the_finished_size():
    assert top_outline().is_valid
    assert top_outline().bounds == pytest.approx((0.0, 0.0, 31.75, 23.75))


def test_the_back_corners_are_square_and_the_front_corners_rounded():
    outline = top_outline()
    w, d = top_size()
    assert outline.boundary.distance(Point(0, d)) < 1e-9
    assert outline.boundary.distance(Point(w, d)) < 1e-9
    assert outline.distance(Point(w, 0)) == pytest.approx(1.25 * (2 ** 0.5 - 1), abs=0.005)
    assert outline.distance(Point(0, front_edge_y(0.0))) > 0.5


def test_the_shallow_end_is_on_the_left():
    outline = top_outline()
    lowest = lambda x0, x1: min(y for x, y in outline.exterior.coords if x0 <= x <= x1)  # noqa: E731
    assert lowest(0, 3) > lowest(28.75, 31.75) + 1.5
