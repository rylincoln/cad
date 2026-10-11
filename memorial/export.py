"""Write a Plate as DXF and SVG (inches, sheet coordinates), a cut-only DXF for a laser shop, and a 1:1 PDF."""
from __future__ import annotations

from pathlib import Path

import ezdxf
import matplotlib
from ezdxf import bbox

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402

from memorial import spec  # noqa: E402
from memorial.plate import Plate  # noqa: E402

LAYERS = {  # name: (DXF colour index, SVG stroke colour), in drawing order
    "REFERENCE_SHEET": (8, "#999999"),
    "REFERENCE_PLATE": (8, "#999999"),
    "ENGRAVE_BORDER": (3, "#00a000"),
    "CUT_INSIDE": (1, "#e00000"),
    "CUT_OUTSIDE": (5, "#0050ff"),
}
PAGE = (17.0, 11.0)
COPPER, REDWOOD = "#c98257", "#5e2817"


def _clean(points, closed: bool) -> list[tuple[float, float]]:
    """Drop consecutive duplicate points (and the repeated closing point of a ring)."""
    pts = list(points)
    if closed and len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    return out


def layer_items(plate: Plate, reference_cuts: bool = False) -> list[tuple[str, str, object, bool]]:
    """(layer, "poly" | "circle", points or centre, closed) for everything on the sheet, in sheet coordinates.

    With `reference_cuts`, the outline and holes are already cut and go on REFERENCE_PLATE, to line up by.
    """
    items = _items(plate)
    if reference_cuts:
        items = [("REFERENCE_PLATE" if layer.startswith("CUT_") else layer, kind, data, closed)
                 for layer, kind, data, closed in items]
    return items


def _items(plate: Plate) -> list[tuple[str, str, object, bool]]:
    dx, dy = plate.offset
    w, h = plate.sheet

    def moved(coords):
        return [(x + dx, y + dy) for x, y in coords]

    items: list[tuple[str, str, object, bool]] = [("REFERENCE_SHEET", "poly", [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)], True)]
    for line in plate.border:
        items.append(("ENGRAVE_BORDER", "poly", _clean(moved(line.coords), line.is_ring), line.is_ring))
    for _, region in plate.cutouts:
        for ring in (region.exterior, *region.interiors):
            items.append(("CUT_INSIDE", "poly", _clean(moved(ring.coords), True), True))
    for x, y in plate.holes:
        items.append(("CUT_INSIDE", "circle", (x + dx, y + dy), True))
    items.append(("CUT_OUTSIDE", "poly", _clean(moved(plate.outline.exterior.coords), True), True))
    return items


def write_dxf(plate: Plate, path: Path, reference_cuts: bool = False) -> None:
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 1     # inches
    doc.header["$MEASUREMENT"] = 0  # imperial
    items = layer_items(plate, reference_cuts)
    for name, (aci, _) in LAYERS.items():
        if any(layer == name for layer, *_ in items):
            doc.layers.add(name, color=aci)
    msp = doc.modelspace()
    for layer, kind, data, closed in items:
        if kind == "circle":
            msp.add_circle(data, spec.HOLE_DIAMETER / 2, dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(data, close=closed, dxfattribs={"layer": layer})
    doc.saveas(path)


def write_cut_dxf(plate: Plate, path: Path) -> None:
    """Only the through-cuts, for a laser shop: no sheet rectangle, no engraving, plate's lower-left at the origin."""
    minx, miny, _, _ = plate.outline.bounds
    x0, y0 = minx + plate.offset[0], miny + plate.offset[1]
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 1     # inches
    doc.header["$MEASUREMENT"] = 0  # imperial
    doc.layers.add("CUT", color=7)
    msp = doc.modelspace()
    for layer, kind, data, closed in layer_items(plate):
        if not layer.startswith("CUT_"):
            continue
        if kind == "circle":
            msp.add_circle((data[0] - x0, data[1] - y0), spec.HOLE_DIAMETER / 2, dxfattribs={"layer": "CUT"})
        else:
            msp.add_lwpolyline([(x - x0, y - y0) for x, y in data], close=closed, dxfattribs={"layer": "CUT"})
    extents = bbox.extents(msp)
    # ezdxf copies the layout's extents into the header on save, but skips a corner at exactly (0, 0, 0)
    msp.reset_extents(extents.extmin, extents.extmax)
    doc.header["$EXTMIN"] = extents.extmin
    doc.header["$EXTMAX"] = extents.extmax
    doc.saveas(path)


def write_svg(plate: Plate, path: Path, reference_cuts: bool = False) -> None:
    w, h = plate.sheet
    groups: dict[str, list[str]] = {name: [] for name in LAYERS}
    for layer, kind, data, closed in layer_items(plate, reference_cuts):
        if kind == "circle":
            x, y = data
            groups[layer].append(f'<circle cx="{x:.4f}" cy="{h - y:.4f}" r="{spec.HOLE_DIAMETER / 2:.4f}"/>')
        else:
            d = "M" + " L".join(f"{x:.4f},{h - y:.4f}" for x, y in data) + (" Z" if closed else "")
            groups[layer].append(f'<path d="{d}"/>')
    body = "\n".join(
        f'  <g id="{name}" fill="none" stroke="{LAYERS[name][1]}" stroke-width="0.005">\n    '
        + "\n    ".join(elements) + "\n  </g>"
        for name, elements in groups.items() if elements)
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}in" height="{h:g}in" viewBox="0 0 {w:g} {h:g}">\n'
                    f"{body}\n</svg>\n")


def _patch(polygon, dx: float, dy: float, **style) -> PathPatch:
    poly = orient(polygon, sign=1.0)  # exterior CCW, holes CW: matplotlib's nonzero fill leaves the holes empty
    vertices, codes = [], []
    for ring in (poly.exterior, *poly.interiors):
        pts = [(x + dx, y + dy) for x, y in ring.coords]
        vertices += pts
        codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(pts) - 2) + [MplPath.CLOSEPOLY]
    return PathPatch(MplPath(vertices, codes), **style)


def write_pdf(plate: Plate, path: Path) -> None:
    """The plate at 1:1, centred on an 11 x 17 landscape page, with a 1-inch scale bar."""
    pw, ph = PAGE
    dx, dy = pw / 2, ph / 2
    fig = plt.figure(figsize=PAGE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, pw)
    ax.set_ylim(0, ph)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(_patch(plate.outline, dx, dy, facecolor=COPPER, edgecolor="black", linewidth=0.5))
    for line in plate.border:
        xs, ys = zip(*line.coords)
        ax.plot([x + dx for x in xs], [y + dy for y in ys], color="#7a3d20", linewidth=0.6)
    for _, region in plate.cutouts:
        ax.add_patch(_patch(region, dx, dy, facecolor=REDWOOD, edgecolor="none"))
    for x, y in plate.holes:
        ax.add_patch(Circle((x + dx, y + dy), spec.HOLE_DIAMETER / 2, facecolor=REDWOOD, edgecolor="none"))
    ax.plot([0.5, 1.5], [0.35, 0.35], color="black", linewidth=1.5)
    for x in (0.5, 1.5):
        ax.plot([x, x], [0.28, 0.42], color="black", linewidth=1.0)
    ax.text(1.65, 0.35, "1 inch. Measure it: the print must be actual size (print at 100%).", va="center", fontsize=9)
    minx, miny, maxx, maxy = plate.outline.bounds
    ax.text(pw / 2, ph - 0.35, f"Fitzgerald memorial plate, {maxx - minx:.3f} x {maxy - miny:.3f} in, actual size",
            ha="center", va="center", fontsize=10)
    fig.savefig(path, format="pdf")
    plt.close(fig)
