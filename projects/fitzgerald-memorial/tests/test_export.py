import re
import xml.etree.ElementTree as ET

import ezdxf
import pytest
from cadgen.drawing_checks import validate_dxf_file
from shapely.geometry import Polygon

from memorial.export import write_cut_dxf, write_dxf, write_pdf, write_svg
from memorial.plate import border_only

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture(scope="module")
def final_dxf(tmp_path_factory, final):
    path = tmp_path_factory.mktemp("dxf") / "final.dxf"
    write_dxf(final, path)
    return path


def _bounds(entities):
    xs, ys = [], []
    for e in entities:
        if e.dxftype() == "LWPOLYLINE":
            for x, y in e.get_points("xy"):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def test_dxf_is_in_inches_with_the_four_layers(final_dxf):
    doc = ezdxf.readfile(final_dxf)
    assert doc.header["$INSUNITS"] == 1
    assert {"REFERENCE_SHEET", "ENGRAVE_BORDER", "CUT_INSIDE", "CUT_OUTSIDE"} <= {layer.dxf.name for layer in doc.layers}


def test_dxf_outline_measures_16_by_9_5_centred_on_the_sheet(final_dxf):
    msp = ezdxf.readfile(final_dxf).modelspace()
    assert _bounds(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]')) == pytest.approx((1.0, 0.25, 17.0, 9.75), abs=1e-4)
    assert _bounds(msp.query('LWPOLYLINE[layer=="REFERENCE_SHEET"]')) == pytest.approx((0.0, 0.0, 18.0, 10.0))


def test_dxf_pin_holes_are_eight_circles_of_0_070(final_dxf):
    circles = list(ezdxf.readfile(final_dxf).modelspace().query('CIRCLE[layer=="CUT_INSIDE"]'))
    assert len(circles) == 8
    assert all(c.dxf.radius == pytest.approx(0.035) for c in circles)


def test_dxf_writes_every_cut_as_one_closed_polyline_with_nothing_inside_another(final_dxf, final):
    polys = list(ezdxf.readfile(final_dxf).modelspace().query('LWPOLYLINE[layer=="CUT_INSIDE"]'))
    assert len(polys) == len(final.cutouts)
    assert all(p.closed for p in polys)
    for p in polys:
        pts = list(p.get_points("xy"))
        assert all(a != b for a, b in zip(pts, pts[1:] + pts[:1]))  # no zero-length segments
    # every letter centre is tied in, so no ring sits inside another and nothing drops out
    rings = [Polygon(list(p.get_points("xy"))) for p in polys]
    assert not any(a.contains(b) for a in rings for b in rings if a is not b)


def test_dxf_passes_cadgens_drawing_checks(final_dxf):
    assert [f.render() for f in validate_dxf_file(final_dxf) if f.severity == "error"] == []


def test_svg_is_sized_in_inches_with_a_sheet_viewbox(tmp_path, final):
    path = tmp_path / "final.svg"
    write_svg(final, path)
    root = ET.parse(path).getroot()
    assert (root.get("width"), root.get("height"), root.get("viewBox")) == ("18in", "10in", "0 0 18 10")
    groups = {g.get("id"): g for g in root.findall(f"{SVG}g")}
    assert set(groups) == {"REFERENCE_SHEET", "ENGRAVE_BORDER", "CUT_INSIDE", "CUT_OUTSIDE"}
    assert len(groups["CUT_INSIDE"].findall(f"{SVG}path")) == sum(1 + len(r.interiors) for _, r in final.cutouts)
    assert len(groups["CUT_INSIDE"].findall(f"{SVG}circle")) == 8
    outline_d = groups["CUT_OUTSIDE"].find(f"{SVG}path").get("d")
    ys = [float(v) for v in re.findall(r"[ML]\s*[-\d.]+,([-\d.]+)", outline_d)]
    assert min(ys) == pytest.approx(0.25, abs=1e-4) and max(ys) == pytest.approx(9.75, abs=1e-4)  # y flipped for SVG


def test_practice_border_is_written_as_open_polylines(tmp_path, practice):
    path = tmp_path / "practice.dxf"
    write_dxf(practice, path)
    msp = ezdxf.readfile(path).modelspace()
    border = list(msp.query('LWPOLYLINE[layer=="ENGRAVE_BORDER"]'))
    assert border and not any(p.closed for p in border)
    assert [f.render() for f in validate_dxf_file(path) if f.severity == "error"] == []
    assert _bounds(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]')) == pytest.approx((0.25, 0.25, 12.75, 7.75), abs=1e-4)


def test_pdf_is_a_tabloid_landscape_page(tmp_path, final):
    path = tmp_path / "final_fullsize.pdf"
    write_pdf(final, path)
    box = re.search(rb"/MediaBox\s*\[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", path.read_bytes())
    assert box and (float(box.group(1)), float(box.group(2))) == (1224.0, 792.0)


@pytest.fixture(scope="module")
def cut_dxf(tmp_path_factory, final):
    path = tmp_path_factory.mktemp("cut") / "final_sendcutsend.dxf"
    write_cut_dxf(final, path)
    return path


def test_cut_dxf_holds_only_through_cuts(cut_dxf, final):
    # a laser shop cuts every line it is sent: no sheet rectangle, no engraved border
    msp = ezdxf.readfile(cut_dxf).modelspace()
    assert {e.dxf.layer for e in msp} == {"CUT"}
    assert len(msp.query("LWPOLYLINE")) == 1 + len(final.cutouts)
    assert len(msp.query("CIRCLE")) == 8
    assert all(p.closed for p in msp.query("LWPOLYLINE"))


def test_cut_dxf_is_the_plate_alone_at_the_origin_in_inches(cut_dxf):
    doc = ezdxf.readfile(cut_dxf)
    assert doc.header["$INSUNITS"] == 1
    msp = doc.modelspace()
    assert _bounds(msp.query("LWPOLYLINE")) == pytest.approx((0.0, 0.0, 16.0, 9.5), abs=1e-4)
    assert doc.header["$EXTMIN"][:2] == pytest.approx((0.0, 0.0), abs=1e-4)
    assert doc.header["$EXTMAX"][:2] == pytest.approx((16.0, 9.5), abs=1e-4)


def test_cut_dxf_is_one_part_with_nothing_to_drop_out(cut_dxf):
    # every contour sits directly inside the oval: none inside another, so nothing falls free
    rings = [Polygon(list(p.get_points("xy"))) for p in ezdxf.readfile(cut_dxf).modelspace().query("LWPOLYLINE")]
    outline = max(rings, key=lambda r: r.area)
    inner = [r for r in rings if r is not outline]
    assert all(outline.contains(r) for r in inner)
    assert not any(a.contains(b) for a in inner for b in inner if a is not b)


def test_border_engrave_file_has_the_border_and_only_reference_lines(tmp_path, final):
    path = tmp_path / "border_engrave.dxf"
    write_dxf(border_only(final), path, reference_cuts=True)
    msp = ezdxf.readfile(path).modelspace()
    assert not msp.query('*[layer=="CUT_INSIDE" | layer=="CUT_OUTSIDE"]')
    border = list(msp.query('LWPOLYLINE[layer=="ENGRAVE_BORDER"]'))
    assert len(border) == 1 and border[0].closed
    assert _bounds(border) == pytest.approx((0.375, 0.375, 15.625, 9.125), abs=1e-3)
    assert _bounds(msp.query('LWPOLYLINE[layer=="REFERENCE_PLATE"]')) == pytest.approx((0.0, 0.0, 16.0, 9.5), abs=1e-4)
    assert len(msp.query('CIRCLE[layer=="REFERENCE_PLATE"]')) == 8
    assert _bounds(msp.query('LWPOLYLINE[layer=="REFERENCE_SHEET"]')) == pytest.approx((0.0, 0.0, 16.0, 9.5))
    assert [f.render() for f in validate_dxf_file(path) if f.severity == "error"] == []


def test_cut_dxf_passes_cadgens_drawing_checks(cut_dxf):
    assert [f.render() for f in validate_dxf_file(cut_dxf) if f.severity == "error"] == []
