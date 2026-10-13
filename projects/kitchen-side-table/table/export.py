"""Write a sheet as DXF and SVG (inches, sheet coordinates), and a labelled PNG preview."""
from __future__ import annotations

from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from table import spec  # noqa: E402
from table.sheets import Sheet  # noqa: E402

LAYERS = {  # name: (DXF colour index, SVG stroke colour), in drawing order
    "REFERENCE_STOCK": (8, "#999999"),
    "POCKET_HOUSING": (30, "#ff8000"),
    "POCKET_LAP": (2, "#d4b000"),
    "GROOVE_CENTERLINE": (1, "#e00000"),
    "CLEARANCE": (4, "#00a8a8"),
    "ROUGH": (6, "#c000c0"),
    "CUT_OUTSIDE": (5, "#0050ff"),
}
FILL = {"aprons": "#eadcb8", "legs": "#d6b07a", "top": "#c98b6b", "fit_test": "#e8e0d0"}


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


def sheet_items(sheet: Sheet) -> list[tuple[str, list[tuple[float, float]], bool]]:
    """(layer, points, closed) for everything on the sheet, in drawing order."""
    w, h = sheet.stock
    items = [("REFERENCE_STOCK", [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)], True)]
    for part in sheet.parts:
        for layer, pocket in part.pockets:
            items.append((layer, _clean(pocket.exterior.coords, True), True))
        for groove in part.grooves:
            items.append(("GROOVE_CENTERLINE", _clean(groove.coords, False), False))
        if part.outline is None:
            continue
        if sheet.lvl:
            for layer, offset in (("CLEARANCE", spec.CLEARANCE_OFFSET), ("ROUGH", spec.ROUGH_OFFSET)):
                items.append((layer, _clean(part.outline.buffer(offset, quad_segs=16).exterior.coords, True), True))
        items.append(("CUT_OUTSIDE", _clean(part.outline.exterior.coords, True), True))
    order = list(LAYERS)
    return sorted(items, key=lambda item: order.index(item[0]))


def write_dxf(sheet: Sheet, path: Path) -> None:
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 1     # inches
    doc.header["$MEASUREMENT"] = 0  # imperial
    items = sheet_items(sheet)
    for name, (aci, _) in LAYERS.items():
        if any(layer == name for layer, _, _ in items):
            doc.layers.add(name, color=aci)
    msp = doc.modelspace()
    for layer, points, closed in items:
        msp.add_lwpolyline(points, close=closed, dxfattribs={"layer": layer})
    doc.saveas(path)


def write_svg(sheet: Sheet, path: Path) -> None:
    w, h = sheet.stock
    groups: dict[str, list[str]] = {name: [] for name in LAYERS}
    for layer, points, closed in sheet_items(sheet):
        d = "M" + " L".join(f"{x:.4f},{h - y:.4f}" for x, y in points) + (" Z" if closed else "")
        groups[layer].append(f'<path d="{d}"/>')
    body = "\n".join(
        f'  <g id="{name}" fill="none" stroke="{LAYERS[name][1]}" stroke-width="0.02">\n    '
        + "\n    ".join(elements) + "\n  </g>"
        for name, elements in groups.items() if elements)
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}in" height="{h:g}in" viewBox="0 0 {w:g} {h:g}">\n'
                    f"{body}\n</svg>\n")


def write_preview(sheet: Sheet, path: Path) -> None:
    """The sheet seen from above, parts filled and named, every layer in its colour."""
    w, h = sheet.stock
    scale = 10.0 / max(w, h)
    fig, ax = plt.subplots(figsize=(w * scale + 0.4, h * scale + 0.8))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.5, w + 0.5)
    ax.set_ylim(-0.5, h + 0.5)
    ax.set_title(sheet.title, fontsize=10)
    for part in sheet.parts:
        if part.outline is not None:
            xs, ys = part.outline.exterior.xy
            ax.fill(xs, ys, color=FILL[sheet.name], zorder=1)
    for layer, points, closed in sheet_items(sheet):
        xs, ys = zip(*(points + points[:1] if closed else points))
        if layer.startswith("POCKET"):
            ax.fill(xs, ys, color=LAYERS[layer][1], alpha=0.5, zorder=2)
        style = "--" if layer in ("REFERENCE_STOCK", "CLEARANCE", "ROUGH") else "-"
        ax.plot(xs, ys, style, color=LAYERS[layer][1], linewidth=0.6 if layer != "GROOVE_CENTERLINE" else 2.0, zorder=3)
    for part in sheet.parts:
        labels = ([(part.outline, part.name)] if part.outline is not None
                  else [(pocket, layer.removeprefix("POCKET_").lower()) for layer, pocket in part.pockets])
        for shape, label in labels:
            c = shape.centroid
            ax.text(c.x, c.y, label, ha="center", va="center", fontsize=7, zorder=4)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
