"""The spec's cutting rules. check_plate returns plain-English problems; an empty list means cuttable."""
from __future__ import annotations

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from memorial import spec
from memorial.plate import Plate

TOLERANCE = 1e-4


def _where(geom) -> str:
    p = geom.representative_point()
    return f"({p.x:.2f}, {p.y:.2f})"


def _count(geom) -> int:
    return 0 if geom.is_empty else len(getattr(geom, "geoms", [geom]))


def check_plate(plate: Plate, *, full_text: bool) -> list[str]:
    problems: list[str] = []
    cutouts = plate.cutouts

    # 1. narrowest slot: shrinking a cutout by half the rule must leave exactly one piece that
    #    still surrounds every letter centre (a thin wall around a centre vanishes without splitting)
    for label, region in cutouts:
        core = region.buffer(-spec.MIN_SLOT / 2)
        if _count(core) != 1 or len(core.interiors) != len(region.interiors):
            problems.append(f"slot narrower than {spec.MIN_SLOT}\" in {label} at {_where(region)}")

    # 2. narrowest copper between any two separate cutouts (pin holes included)
    shapes = cutouts + [(f"pin hole {i + 1}", Point(h).buffer(spec.HOLE_DIAMETER / 2, quad_segs=32))
                        for i, h in enumerate(plate.holes)]
    tree = STRtree([s for _, s in shapes])
    for i, (label, region) in enumerate(shapes):
        for j in tree.query(region.buffer(spec.MIN_COPPER)):
            if j <= i:
                continue
            other_label, other = shapes[j]
            gap = region.distance(other)
            if gap < spec.MIN_COPPER - TOLERANCE:
                problems.append(f"only {gap:.3f}\" of copper between {label} and {other_label}")

    # 3. letter centres that drop out must be big enough to handle and glue back
    for label, region in cutouts:
        for ring in region.interiors:
            if Polygon(ring).buffer(-spec.MIN_ISLAND / 2).is_empty:
                problems.append(f"letter centre in {label} is under {spec.MIN_ISLAND}\" across")

    # 4. every character present, none empty, none merged with a neighbour
    for line in plate.lines.values():
        if any(g.is_empty for g in line.glyphs):
            problems.append(f"an empty glyph in {line.text!r}")
        if _count(unary_union(line.glyphs)) != sum(_count(g) for g in line.glyphs):
            problems.append(f"letters run together in {line.text!r}")
        if full_text and "".join(line.chars) != line.text.replace(" ", ""):
            problems.append(f"missing characters in {line.text!r}: have {''.join(line.chars)!r}")

    # 5. inside the outline, clear of the border, pin holes on the border line
    for label, region in cutouts:
        if not plate.outline.contains(region):
            problems.append(f"{label} is not inside the plate outline")
        if plate.border:
            clearance = min(region.distance(b) for b in plate.border)
            if clearance < spec.BORDER_CLEARANCE - TOLERANCE:
                problems.append(f"{label} is only {clearance:.3f}\" from the border")
    for i, h in enumerate(plate.holes):
        off = min(Point(h).distance(b) for b in plate.border) if plate.border else float("inf")
        if off > 1e-3:
            problems.append(f"pin hole {i + 1} is {off:.3f}\" off the border line")
    return problems
