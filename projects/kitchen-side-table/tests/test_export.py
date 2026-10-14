import re
import xml.etree.ElementTree as ET

import ezdxf
import pytest
from cadgen.drawing_checks import validate_dxf_file
from shapely.geometry import Polygon

from table.export import write_dxf, write_preview, write_svg

SVG = "{http://www.w3.org/2000/svg}"
EXPECTED_LAYERS = {
    "aprons": {"REFERENCE_STOCK", "GROOVE_CENTERLINE", "CUT_OUTSIDE"},
    "fit_test": {"REFERENCE_STOCK", "POCKET_HOUSING", "POCKET_LAP"},
    "legs": {"REFERENCE_STOCK", "POCKET_HOUSING", "POCKET_LAP", "CLEARANCE", "ROUGH", "CUT_OUTSIDE"},
    "top": {"REFERENCE_STOCK", "CUT_OUTSIDE"},
}


@pytest.fixture(scope="module")
def dxfs(tmp_path_factory, sheets):
    folder = tmp_path_factory.mktemp("dxf")
    for name, sheet in sheets.items():
        write_dxf(sheet, folder / f"{name}.dxf")
    return folder


def test_each_dxf_is_in_inches_with_the_layers_its_job_needs(dxfs):
    for name, layers in EXPECTED_LAYERS.items():
        doc = ezdxf.readfile(dxfs / f"{name}.dxf")
        assert doc.header["$INSUNITS"] == 1
        assert {layer.dxf.name for layer in doc.layers} - {"0", "Defpoints"} == layers


def test_each_dxf_passes_cadgens_drawing_checks(dxfs):
    for name in EXPECTED_LAYERS:
        assert [f.render() for f in validate_dxf_file(dxfs / f"{name}.dxf") if f.severity == "error"] == []


def test_grooves_are_open_lines_and_everything_else_closed(dxfs):
    for name in EXPECTED_LAYERS:
        for line in ezdxf.readfile(dxfs / f"{name}.dxf").modelspace().query("LWPOLYLINE"):
            assert line.closed == (line.dxf.layer != "GROOVE_CENTERLINE")


def test_the_legs_clearance_and_rough_lines_sit_outside_each_leg_by_their_offsets(dxfs):
    msp = ezdxf.readfile(dxfs / "legs.dxf").modelspace()
    shapes = lambda layer: [Polygon(list(p.get_points("xy"))) for p in msp.query(f'LWPOLYLINE[layer=="{layer}"]')]  # noqa: E731
    legs, clearance, rough = shapes("CUT_OUTSIDE"), shapes("CLEARANCE"), shapes("ROUGH")
    assert len(legs) == len(clearance) == len(rough) == 4
    for leg, wide, near in zip(legs, clearance, rough):
        assert wide.contains(leg) and near.contains(leg)
        assert leg.hausdorff_distance(wide) == pytest.approx(0.125, abs=0.002)
        assert leg.hausdorff_distance(near) == pytest.approx(0.02, abs=0.002)


def test_the_top_dxf_has_the_shallow_end_on_the_left(dxfs):
    msp = ezdxf.readfile(dxfs / "top.dxf").modelspace()
    points = list(next(iter(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]'))).get_points("xy"))
    assert min(y for x, y in points if x < 3.3) > min(y for x, y in points if x > 28.8) + 1.5


def test_the_svg_is_sized_in_inches_with_a_group_per_layer(tmp_path, sheets):
    path = tmp_path / "legs.svg"
    write_svg(sheets["legs"], path)
    root = ET.parse(path).getroot()
    assert (root.get("width"), root.get("height"), root.get("viewBox")) == ("32.5in", "11.75in", "0 0 32.5 11.75")
    assert {g.get("id") for g in root.findall(f"{SVG}g")} == EXPECTED_LAYERS["legs"]


def test_the_top_svg_has_the_shallow_end_on_the_left(tmp_path, sheets):
    path = tmp_path / "top.svg"
    write_svg(sheets["top"], path)
    root = ET.parse(path).getroot()
    height = float(root.get("viewBox").split()[3])
    group = next(g for g in root.findall(f"{SVG}g") if g.get("id") == "CUT_OUTSIDE")
    numbers = re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", group.find(f"{SVG}path").get("d"))
    points = [(float(x), height - float(y)) for x, y in numbers]
    assert min(y for x, y in points if x < 3.3) > min(y for x, y in points if x > 28.8) + 1.5


def test_the_preview_is_a_png(tmp_path, sheets):
    path = tmp_path / "aprons.png"
    write_preview(sheets["aprons"], path)
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
