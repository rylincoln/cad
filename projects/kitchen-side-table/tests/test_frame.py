import pytest

from table.frame import back_inside_y, dowel_spots, extent, front_inside_y, tip_load, weight_and_center_y


def _placed(table):
    return {p.name: p for p in table.placed}


def test_the_legs_stand_an_inch_in_from_each_end_with_the_flare_toward_the_middle(table):
    for name, part in _placed(table).items():
        if part.material != "lvl":
            continue
        lo, hi = extent(part)
        outer = 1.0 if name.endswith("left") else 30.75
        assert (lo[0], hi[0]) == pytest.approx((1.0, 4.25) if name.endswith("left") else (27.5, 30.75))
        foot = [part.to_table(a, b)[0] for a, b in part.outline.exterior.coords if b == 0.0]
        assert min(abs(x - outer) for x in foot) == pytest.approx(0.0)
        assert max(abs(x - outer) for x in foot) == pytest.approx(1.5)


def test_the_front_legs_stand_3_5_behind_the_front_edge_and_the_back_legs_3_332_from_the_wall(table):
    placed = _placed(table)
    for name in ("front-left", "front-right"):
        lo, hi = extent(placed[name])
        assert (lo[1], hi[1]) == pytest.approx((3.5, 5.12))
    for name in ("back-left", "back-right"):
        lo, hi = extent(placed[name])
        assert (lo[1], hi[1]) == pytest.approx((18.798, 20.418))


def test_every_inside_face_faces_the_middle_of_the_table(table):
    middle = (31.75 / 2, 23.75 / 2)
    for part in (p for p in table.placed if p.name != "top"):
        to_middle = (middle[0] - part.origin[0], middle[1] - part.origin[1])
        assert part.normal[0] * to_middle[0] + part.normal[1] * to_middle[1] > 0, part.name


def test_the_long_aprons_are_flush_with_the_legs_inside_faces(table):
    placed = _placed(table)
    assert extent(placed["front apron"])[1][1] == pytest.approx(front_inside_y())
    assert extent(placed["back apron"])[0][1] == pytest.approx(back_inside_y())


def test_the_aprons_are_flush_with_the_leg_tops_under_the_top(table):
    placed = _placed(table)
    for name in ("front apron", "back apron", "left apron", "right apron"):
        lo, hi = extent(placed[name])
        assert (lo[2], hi[2]) == pytest.approx((28.279, 31.25))
    lo, hi = extent(placed["top"])
    assert (lo[2], hi[2]) == pytest.approx((31.25, 32.0))


def test_the_side_aprons_outer_faces_are_1_375_in_from_each_end(table):
    placed = _placed(table)
    assert extent(placed["left apron"])[0][0] == pytest.approx(1.375)
    assert extent(placed["right apron"])[1][0] == pytest.approx(31.75 - 1.375)


def test_to_face_undoes_to_table(table):
    for part in table.placed:
        assert part.to_face(part.to_table(1.25, 2.5, 0.375)) == pytest.approx((1.25, 2.5, 0.375))


def test_the_dowels_sit_at_the_middle_of_the_long_aprons_where_they_meet_the_top(table):
    spots = sorted(dowel_spots(table))
    assert [x for x, _, _ in spots] == pytest.approx([14.875, 14.875, 16.875, 16.875])
    assert sorted({round(y, 4) for _, y, _ in spots}) == pytest.approx([front_inside_y() - 0.353, back_inside_y() + 0.353])
    assert all(z == pytest.approx(31.25) for _, _, z in spots)


def test_the_empty_table_weighs_about_24_lb_centered_about_12_in_back(table):
    weight, center_y = weight_and_center_y(table)
    assert weight == pytest.approx(24.1, abs=0.5)
    assert center_y == pytest.approx(12.08, abs=0.1)


def test_it_takes_about_59_lb_on_the_front_edge_to_tip_it(table):
    assert tip_load(table) == pytest.approx(59.0, abs=1.0)
