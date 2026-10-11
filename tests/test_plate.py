import pytest
from shapely.geometry import Point

from memorial import spec


def test_outline_is_16_by_9_5(final):
    minx, miny, maxx, maxy = final.outline.bounds
    assert (maxx - minx, maxy - miny) == (pytest.approx(16.0, abs=1e-6), pytest.approx(9.5, abs=1e-6))


def test_border_is_three_eighths_inside_the_edge(final):
    (border,) = final.border
    for x, y in list(border.coords)[::97]:
        assert final.outline.exterior.distance(Point(x, y)) == pytest.approx(0.375, abs=0.001)


def test_eight_pin_holes_evenly_spaced_first_at_top(final):
    (border,) = final.border
    assert len(final.holes) == 8
    assert final.holes[0] == (pytest.approx(0.0, abs=0.01), pytest.approx(4.375, abs=0.001))
    positions = sorted(border.project(Point(h)) for h in final.holes)
    steps = [b - a for a, b in zip(positions, positions[1:])]
    assert max(steps) == pytest.approx(border.length / 8, abs=0.01)
    assert min(steps) == pytest.approx(border.length / 8, abs=0.01)


def test_names_and_dates_flank_the_centred_knot(final):
    def centre_x(key):
        minx, _, maxx, _ = final.lines[key].glyphs[0].union(final.lines[key].glyphs[-1]).bounds
        return (minx + maxx) / 2

    knot_minx = min(p.bounds[0] for p in final.knot)
    knot_maxx = max(p.bounds[2] for p in final.knot)
    assert (knot_minx + knot_maxx) / 2 == pytest.approx(0.0, abs=1e-6)
    assert centre_x("name_left") == pytest.approx(-centre_x("name_right"), abs=1e-6)
    assert centre_x("name_left") < -3.5
    for key in ("name_left", "name_right", "date_left", "date_right"):
        nearest = min(min(g.distance(p) for p in final.knot) for g in final.lines[key].glyphs)
        assert nearest >= spec.KNOT_SIDE_GAP - 1e-6, key


def test_every_line_sits_on_its_baseline(final):
    for key, line_spec in spec.LINES.items():
        maxy = max(g.bounds[3] for g in final.lines[key].glyphs)
        # cap height 0.70 em; serifs and apexes overshoot to 0.72 em; mitred thickening adds at most 5 x 0.012"
        assert line_spec.baseline + 0.69 * line_spec.em < maxy < line_spec.baseline + 0.72 * line_spec.em + 0.06, key


def test_knot_is_1_2_tall_at_its_centre(final):
    miny = min(p.bounds[1] for p in final.knot)
    maxy = max(p.bounds[3] for p in final.knot)
    assert (miny + maxy) / 2 == pytest.approx(spec.KNOT_CENTER[1], abs=0.03)  # mitred tips are not symmetric
    assert len(final.knot) == 3


def test_lettering_and_knot_clear_the_border(final):
    (border,) = final.border
    assert min(region.distance(border) for _, region in final.cutouts) >= 0.30


def test_final_plate_is_centred_on_its_sheet(final):
    assert final.sheet == (18.0, 10.0)
    assert final.offset == (9.0, 5.0)


def test_cutouts_are_labelled_for_error_messages(final):
    labels = [label for label, _ in final.cutouts]
    assert labels[0] == "'F' in 'FITZGERALD'"
    assert labels[-1] == "knot piece 3"
    assert len(labels) == 68
