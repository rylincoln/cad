"""Stencil ties: strips of plate left across a letter's stroke so its centre stays attached to the plate."""
from __future__ import annotations

from dataclasses import replace

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from memorial import spec
from memorial.plate import Plate

SAMPLE_STEP = 0.004  # in, between candidate tie positions along a centre's edge
OVERSHOOT = 0.02     # in, a tie runs this far past both edges of the stroke so it cuts clean through
SLIVER_AREA = 1e-4   # sq in; scraps of stroke this small left beside a tie become plate
EVEN = 0.003         # in; crossings within this of each other count as the same stroke width


def _band(segment: LineString, width: float) -> Polygon:
    (x0, y0), (x1, y1) = segment.coords
    ux, uy = (x1 - x0) / segment.length, (y1 - y0) / segment.length
    run = LineString([(x0 - ux * OVERSHOOT, y0 - uy * OVERSHOOT), (x1 + ux * OVERSHOOT, y1 + uy * OVERSHOOT)])
    return run.buffer(width / 2, cap_style="flat")


def _crossings(region: Polygon, ring, width: float) -> list[tuple[float, float, LineString, Polygon]]:
    """(length, position along the centre's edge, segment, tie) for every square crossing from the centre
    to the outside that stays within the stroke: never to another centre (the middle of a B), and never
    slanted across a corner, where the tie's ends would stop short of the edges."""
    inside = region.buffer(1e-6)
    centre, outline = Polygon(ring), Polygon(region.exterior)
    out = []
    count = max(64, int(ring.length / SAMPLE_STEP))
    for k in range(count):
        s = ring.length * k / count
        p = ring.interpolate(s)
        q = region.exterior.interpolate(region.exterior.project(p))
        segment = LineString([p, q])
        if segment.length == 0 or not inside.covers(segment):
            continue
        tie = _band(segment, width)
        corners = [Point(c) for c in tie.exterior.coords[:4]]
        near = [c for c in corners if c.distance(p) < c.distance(q)]
        far = [c for c in corners if c.distance(p) >= c.distance(q)]
        if all(centre.contains(c) for c in near) and not any(outline.contains(c) for c in far):
            out.append((segment.length, s, segment, tie))
    return out


def _ranked(options, perimeter: float):
    """Thinnest crossing first; along a stroke of even width, the middle of that stretch first."""
    def stretch(option):
        length, s, _, _ = option
        rivals = [abs(o[1] - s) for o in options if o[0] > length + EVEN]
        return min([min(d, perimeter - d) for d in rivals], default=perimeter)
    return sorted(options, key=lambda o: (round(o[0] / EVEN), -stretch(o)))


def _cuttable(piece: Polygon) -> bool:
    core = piece.buffer(-spec.MIN_SLOT / 2)
    return not core.is_empty and core.geom_type == "Polygon" and len(core.interiors) == len(piece.interiors)


def _apply(region: Polygon, ties: list[Polygon]) -> list[Polygon]:
    cut = region.difference(unary_union(ties))
    return [p for p in getattr(cut, "geoms", [cut]) if p.area >= SLIVER_AREA]


def tie_region(region: Polygon, ties_per_centre: int, width: float = spec.TIE_WIDTH) -> Polygon | MultiPolygon:
    """Leave a tie across the stroke's thinnest square crossing around each centre (a second, if asked for,
    at least a third of the way round from the first), skipping any spot that would leave a scrap of
    stroke too narrow to cut."""
    if not region.interiors:
        return region
    ties: list[Polygon] = []
    for interior in region.interiors:
        perimeter = interior.length
        options = _crossings(region, interior, width)
        chosen: list[tuple] = []
        for _ in range(ties_per_centre):
            pool = [o for o in options
                    if all(min(abs(o[1] - c[1]), perimeter - abs(o[1] - c[1])) >= perimeter / 3 for c in chosen)]
            pick = next((o for o in _ranked(pool, perimeter)
                         if all(_cuttable(p) for p in _apply(region, ties + [c[3] for c in chosen] + [o[3]]))), None)
            if pick is None:
                raise ValueError(f"no place to tie a letter centre at {interior.representative_point()}")
            chosen.append(pick)
        ties += [c[3] for c in chosen]
    parts = _apply(region, ties)
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def with_ties(plate: Plate, name: str, width: float = spec.TIE_WIDTH) -> Plate:
    """The same plate with every letter centre tied in place, for a shop that can't return drop-outs."""
    lines = {key: replace(line, glyphs=tuple(tie_region(glyph, 2 if char in spec.TWO_TIE_CHARS else 1, width)
                                             for char, glyph in zip(line.chars, line.glyphs)))
             for key, line in plate.lines.items()}
    return replace(plate, name=name, lines=lines)
