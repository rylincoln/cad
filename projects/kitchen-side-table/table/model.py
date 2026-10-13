"""The assembled table as a 3D model (STEP and GLB), for looking at in the CAD Viewer."""
from __future__ import annotations

from pathlib import Path

from build123d import (Align, Color, Compound, Cylinder, Face, Plane, Pos, Vector, Wire, export_gltf, export_step,
                       extrude)
from shapely.geometry import Polygon

from table import spec
from table.aprons import dowel_depths
from table.frame import Placed, Table, dowel_spots

SIMPLIFY = 0.002  # the preview's outlines may stray this far from the cut files', to keep the files small
COLORS = {"cherry": (0.62, 0.32, 0.2), "lvl": (0.84, 0.69, 0.48), "plywood": (0.92, 0.86, 0.72)}


def _face(polygon: Polygon) -> Face:
    ring = polygon.simplify(SIMPLIFY).exterior.coords[:-1]
    return Face(Wire.make_polygon([Vector(x, y, 0) for x, y in ring], close=True))


def part_solid(part: Placed):
    """The part with its pockets cut, moved into table coordinates."""
    solid = extrude(_face(part.outline), amount=part.thickness, dir=(0, 0, -1))
    for shape, depth in part.pockets:
        solid = solid - extrude(_face(shape), amount=depth, dir=(0, 0, -1))
    placed = Plane(origin=part.origin, x_dir=part.a_axis, z_dir=part.normal).location * solid
    placed.label = part.name
    placed.color = Color(*COLORS[part.material])
    return placed


def table_model(table: Table) -> Compound:
    parts = [part_solid(p) for p in table.placed]
    r = spec.DOWEL_DIAMETER / 2
    for i, (x, y, z) in enumerate(dowel_spots(table), start=1):
        dowel = Pos(x, y, z + dowel_depths()[0] - spec.DOWEL_LENGTH) * Cylinder(
            r, spec.DOWEL_LENGTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
        dowel.label = f"dowel {i}"
        dowel.color = Color(0.95, 0.9, 0.75)
        parts.append(dowel)
    return Compound(children=parts, label="kitchen side table")


def write_model(table: Table, step: Path, glb: Path) -> None:
    model = table_model(table)
    export_step(model, step)
    export_gltf(model, str(glb), binary=True)
