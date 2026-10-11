import itertools

import numpy as np
import pytest

from memorial.knot import assign_alternation, knot_cutouts, self_crossings, triquetra_centerline


def test_centerline_has_the_requested_height_and_centre():
    curve = triquetra_centerline(1.2, center=(0.0, -0.32))
    lo, hi = curve.min(axis=0), curve.max(axis=0)
    assert hi[1] - lo[1] == pytest.approx(1.2)
    assert (lo + hi)[1] / 2 == pytest.approx(-0.32)
    assert (lo + hi)[0] / 2 == pytest.approx(0.0, abs=1e-9)


def test_one_leaf_points_straight_up():
    curve = triquetra_centerline(1.2)
    top = curve[np.argmax(curve[:, 1])]
    assert top[0] == pytest.approx(0.0, abs=1e-6)


def test_triquetra_crosses_itself_exactly_three_times():
    assert len(self_crossings(triquetra_centerline(1.2))) == 3


def test_crossings_alternate_over_and_under():
    pairs = assign_alternation(self_crossings(triquetra_centerline(1.2)))
    assert len(pairs) == 3
    assert all(over != under for over, under in pairs)


def test_band_becomes_three_equal_cutouts():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    assert len(pieces) == 3
    areas = [p.area for p in pieces]
    assert max(areas) == pytest.approx(min(areas), rel=1e-3)


def test_bridges_leave_the_design_width_of_copper():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    assert min(a.distance(b) for a, b in itertools.combinations(pieces, 2)) >= 0.079


def test_band_pieces_are_wide_enough_to_cut_and_drop_nothing():
    for piece in knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08):
        assert piece.buffer(-0.025).geom_type == "Polygon"
        assert len(piece.interiors) == 0


def test_knot_fits_its_height():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    miny = min(p.bounds[1] for p in pieces)
    maxy = max(p.bounds[3] for p in pieces)
    assert maxy - miny == pytest.approx(1.2 + 0.10, abs=0.08)  # centerline height plus the band (mitred tips)
