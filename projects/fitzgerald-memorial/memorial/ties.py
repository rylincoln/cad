"""Stencil ties: strips of plate left across a letter's stroke so its centre stays attached to the plate."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import nearest_points, polylabel, unary_union

from typing import TYPE_CHECKING

from memorial import spec

if TYPE_CHECKING:  # plate.py ties its lettering with this module
    from memorial.plate import Plate

SAMPLE_STEP = 0.004  # in, between candidate tie positions along a centre's edge
OVERSHOOTS = (0.02, 0.035, 0.05)  # in, how far a tie may run past the stroke's edges to clear a tight curve
SLIVER_AREA = 1e-4   # sq in; scraps of stroke this small left beside a tie become plate
SLIVER_WIDTH = 0.01  # in; slivers of stroke thinner than this beside a widened neck become plate
EVEN = 0.003         # in; crossings within this of each other count as the same stroke width
NECK_REACH = 0.3     # in; plate this far around a letter is searched for necks


def _band(segment: LineString, width: float, overshoot: float) -> Polygon:
    (x0, y0), (x1, y1) = segment.coords
    ux, uy = (x1 - x0) / segment.length, (y1 - y0) / segment.length
    run = LineString([(x0 - ux * overshoot, y0 - uy * overshoot), (x1 + ux * overshoot, y1 + uy * overshoot)])
    return run.buffer(width / 2, cap_style="flat")


def _clean_tie(region: Polygon, centre: Polygon, outline: Polygon, segment: LineString, width: float):
    """The shortest tie along `segment` whose square ends land inside the centre and outside the letter,
    crossing only this one stroke; None if there is none."""
    p, q = (Point(c) for c in segment.coords)
    for overshoot in OVERSHOOTS:
        tie = _band(segment, width, overshoot)
        corners = [Point(c) for c in tie.exterior.coords[:4]]
        near = [c for c in corners if c.distance(p) < c.distance(q)]
        far = [c for c in corners if c.distance(p) >= c.distance(q)]
        if (all(centre.contains(c) for c in near) and not any(outline.contains(c) for c in far)
                and region.intersection(tie).geom_type == "Polygon"):
            return tie
    return None


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
        tie = _clean_tie(region, centre, outline, segment, width)
        if tie is not None:
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


def _strip(run: LineString, width: float) -> Polygon:
    """Plate `width` wide along `run`, square-ended a hair past each end."""
    pts = [np.array(c) for c in run.coords]
    head, tail = pts[0] - pts[1], pts[-1] - pts[-2]
    pts[0] = pts[0] + head / np.linalg.norm(head) * 0.01
    pts[-1] = pts[-1] + tail / np.linalg.norm(tail) * 0.01
    return LineString(pts).buffer(width / 2, cap_style="flat", join_style="round")


def _joins(piece: Polygon, cores: list[Polygon], inner: Polygon, shrink: float, width: float):
    """(strip of plate to cut, its run) joining the split-off core `inner` back to another core, best
    first: straight across the neck; straight along the thin plate between them; bent once through the
    middle of a curved channel (the curl at the top of a script a)."""
    others = sorted((c for c in cores if c is not inner), key=lambda c: c.distance(inner))
    for other in others:
        run = LineString(nearest_points(inner, other))
        yield _strip(run, width), run
    thin = piece.difference(unary_union(cores).buffer(shrink))
    necks = [n for n in getattr(thin, "geoms", [thin])
             if n.distance(inner) <= shrink + 1e-3 and any(n.distance(o) <= shrink + 1e-3 for o in others)]
    for neck in necks:
        reach = neck.buffer(shrink + 1e-3)
        middle = polylabel(neck, tolerance=1e-4)
        for other in others:
            if neck.distance(other) <= shrink + 1e-3:
                run = LineString(nearest_points(inner.intersection(reach), other.intersection(reach)))
                yield _strip(run, width), run
                bent = LineString([nearest_points(inner, middle)[0], middle, nearest_points(other, middle)[0]])
                yield _strip(bent, width), bent


def _open_necks(region: Polygon, width: float) -> Polygon:
    """Widen every neck of plate thinner than the copper rule into a full tie `width` wide.

    Where a stroke comes back close to itself (an arm's end and the next arm's serif in an E, the
    curl at the top of a script g) the plate between them can be the only thing holding a letter's
    inside. Shrinking the plate around the letter by half the copper rule splits such an inside off,
    even a pocket too small for a tie (the crotch of a small r behind its serifs); a strip `width`
    wide is then cut through the plate joining it back, trimming the stroke on either side. Sharp
    corners never split off, so they are left alone.
    """
    return _join_split_plate(region, width, (spec.MIN_COPPER - 1e-4) / 2)


def _join_split_plate(region: Polygon, width: float, shrink: float) -> Polygon:
    for _ in range(40):
        inside = region.buffer(-1e-6)
        plate = box(*region.bounds).buffer(NECK_REACH).difference(region)
        joined = None
        for piece in getattr(plate, "geoms", [plate]):
            core = piece.buffer(-shrink)
            cores = [c for c in getattr(core, "geoms", [core]) if c.area > 1e-8]
            for inner in sorted(cores, key=lambda c: c.area)[:-1]:
                for strip, run in _joins(piece, cores, inner, shrink, width):
                    if inside.intersection(run).length > 0.02:
                        continue  # across a stroke, not through the neck
                    cut = region.difference(strip)
                    # overlapping strips can leave hairline slivers of stroke beside the cut
                    slivers = cut.difference(cut.buffer(-SLIVER_WIDTH / 2).buffer(SLIVER_WIDTH / 2))
                    cut = cut.difference(slivers.intersection(strip.buffer(SLIVER_WIDTH * 2)))
                    opened = [p for p in getattr(cut, "geoms", [cut]) if p.area >= SLIVER_AREA]
                    if len(opened) == 1 and _cuttable(opened[0]):
                        joined = opened[0]
                        break
                if joined is not None:
                    break
            if joined is not None:
                break
        if joined is None:
            return region
        region = joined
    return region


def tie_region(region: Polygon | MultiPolygon, ties_per_centre: int, width: float = spec.TIE_WIDTH) -> Polygon | MultiPolygon:
    """Leave a tie across the stroke's thinnest square crossing around each centre, in every piece of the
    region (a second, if asked for, at least a third of the way round from the first), skipping any
    spot that would leave a scrap of stroke too narrow to cut."""
    if region.geom_type == "MultiPolygon":
        return unary_union([tie_region(part, ties_per_centre, width) for part in region.geoms])
    region = _open_necks(region, width)
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


def with_ties(plate: "Plate", name: str, width: float = spec.TIE_WIDTH) -> "Plate":
    """The same plate with every letter centre tied in place, for a shop that can't return drop-outs."""
    lines = {key: replace(line, glyphs=tuple(tie_region(glyph, 2 if char in spec.TWO_TIE_CHARS else 1, width)
                                             for char, glyph in zip(line.chars, line.glyphs)))
             for key, line in plate.lines.items()}
    return replace(plate, name=name, lines=lines)
