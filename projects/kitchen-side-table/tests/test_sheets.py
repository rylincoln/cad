import pytest

from table.legs import make_leg
from table import spec
from table.sheets import lvl_clamp_room, lvl_depths


def test_there_are_four_jobs(sheets):
    assert list(sheets) == ["aprons", "fit_test", "legs", "top"]


def test_the_legs_nest_head_to_toe_in_two_pairs_of_one_handedness(sheets):
    parts = sheets["legs"].parts
    assert [p.name for p in parts] == ["front-left", "back-right", "front-right", "back-left"]
    for lower, upper in ((parts[0], parts[1]), (parts[2], parts[3])):
        assert lower.outline.distance(upper.outline) == pytest.approx(0.4, abs=1e-6)
        lower_top = dict(lower.pockets)["POCKET_HOUSING"].centroid.x
        upper_top = dict(upper.pockets)["POCKET_HOUSING"].centroid.x
        assert (lower_top > 16) != (upper_top > 16)  # one leg's top at each end
    assert parts[1].outline.distance(parts[2].outline) == pytest.approx(0.4, abs=1e-6)


def test_the_legs_go_on_by_rotation_only_never_mirrored(sheets):
    for part in sheets["legs"].parts:
        leg = make_leg(part.name)
        assert part.outline.area == pytest.approx(leg.outline.area)
        assert part.outline.exterior.is_ccw == leg.outline.exterior.is_ccw


def test_the_legs_sit_centred_across_the_lvl_leaving_the_clamps_wood_along_both_long_edges(sheets):
    parts = sheets["legs"].parts
    below = min(p.outline.bounds[1] for p in parts)
    above = spec.LVL_WIDTH - max(p.outline.bounds[3] for p in parts)
    assert below == pytest.approx(above) == pytest.approx(0.523, abs=0.005)
    assert lvl_clamp_room(sheets["legs"]) == pytest.approx(0.148, abs=0.005)


def test_the_aprons_go_in_three_strips_with_the_coupon_above(sheets):
    bounds = {p.name: p.outline.bounds for p in sheets["aprons"].parts}
    assert bounds["back apron"] == pytest.approx((2.625, 0.125, 29.375, 3.096))
    assert bounds["front apron"] == pytest.approx((2.625, 3.346, 29.375, 6.317))
    assert bounds["left apron"][1] == pytest.approx(6.567) and bounds["right apron"][1] == pytest.approx(6.567)
    assert bounds["right apron"][0] - bounds["left apron"][2] == pytest.approx(0.25)
    assert bounds["coupon"] == pytest.approx((14.5, 9.788, 17.5, 11.538))


def test_the_grooves_go_on_with_their_aprons(sheets):
    back = next(p for p in sheets["aprons"].parts if p.name == "back apron")
    starts = [g.coords[0] for g in back.grooves]
    assert starts == [pytest.approx((2.625 + 2.375, 0.125 + 2.471)), pytest.approx((2.625 + 15.15625, 0.125 + 2.471))]


def test_the_top_sits_show_face_up_with_its_front_edge_toward_the_operator(sheets):
    outline = sheets["top"].parts[0].outline
    assert outline.bounds == pytest.approx((0.125, 0.125, 31.875, 23.875))
    left_front = min(y for x, y in outline.exterior.coords if x < 3.3)
    right_front = min(y for x, y in outline.exterior.coords if x > 28.8)
    assert left_front > right_front + 1.5


def test_the_fit_test_pockets_sit_side_by_side_on_the_scrap(sheets):
    pockets = dict(sheets["fit_test"].parts[0].pockets)
    housing, lap = pockets["POCKET_HOUSING"].bounds, pockets["POCKET_LAP"].bounds
    assert housing[2] < lap[0]
    assert 0 < housing[0] and lap[2] < 6.0 and 0 < housing[1] and housing[3] < 4.0


def test_the_lvl_cut_depths_follow_the_flute(sheets):
    assert lvl_depths() == pytest.approx({"full": 1.64, "clearance": 0.34, "first_stage": 1.3})
