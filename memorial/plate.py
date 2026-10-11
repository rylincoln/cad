"""Assemble the final plate, its practice window, and the outline-only plate from the spec."""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge

from memorial import spec
from memorial.font import Font
from memorial.knot import knot_cutouts
from memorial.text import SetLine, set_line


@dataclass(frozen=True)
class Plate:
    name: str
    sheet: tuple[float, float]
    offset: tuple[float, float]               # add to plate coordinates to get sheet coordinates
    outline: Polygon                          # CUT_OUTSIDE
    border: tuple[LineString, ...]            # ENGRAVE_BORDER
    lines: dict[str, SetLine]                 # placed lettering, CUT_INSIDE
    knot: tuple[Polygon, ...]                 # CUT_INSIDE
    holes: tuple[tuple[float, float], ...]    # pin-hole centres, CUT_INSIDE circles

    @property
    def cutouts(self) -> list[tuple[str, Polygon]]:
        """Every cut-through region except the pin holes, labelled for error messages."""
        regions = [(f"{char!r} in {line.text!r}", glyph)
                   for line in self.lines.values() for char, glyph in zip(line.chars, line.glyphs)]
        regions += [(f"knot piece {i + 1}", piece) for i, piece in enumerate(self.knot)]
        return regions


def ellipse(half_width: float, half_height: float, samples: int = spec.OUTLINE_SAMPLES) -> Polygon:
    return Polygon([(half_width * math.cos(2 * math.pi * i / samples), half_height * math.sin(2 * math.pi * i / samples))
                    for i in range(samples)])


def move_line(line: SetLine, dx: float, dy: float) -> SetLine:
    return replace(line, glyphs=tuple(affinity.translate(g, dx, dy) for g in line.glyphs))


def pin_holes(border: LineString, count: int) -> tuple[tuple[float, float], ...]:
    """`count` points at equal arc length along the border, the first at top centre."""
    top_y = max(y for _, y in border.coords)
    start = border.project(Point(0.0, top_y))
    length = border.length
    points = (border.interpolate((start + k * length / count) % length) for k in range(count))
    return tuple((p.x, p.y) for p in points)


def build_final(font: Font) -> Plate:
    lines = {key: set_line(font, s.text, s.em, s.tracking_em, s.thicken, spec.MIN_LETTER_GAP)
             for key, s in spec.LINES.items()}
    knot = tuple(knot_cutouts(spec.KNOT_HEIGHT, spec.KNOT_CENTER, spec.KNOT_BAND, spec.KNOT_BRIDGE, spec.KNOT_TIP_DEG))
    knot_width = max(p.bounds[2] for p in knot) - min(p.bounds[0] for p in knot)
    column_width = max(lines[key].width for key, s in spec.LINES.items() if s.column)
    column_x = column_width / 2 + knot_width / 2 + spec.KNOT_SIDE_GAP
    placed = {key: move_line(lines[key], s.column * column_x, s.baseline) for key, s in spec.LINES.items()}
    outline = ellipse(spec.PLATE_HALF_WIDTH, spec.PLATE_HALF_HEIGHT)
    border = LineString(outline.buffer(-spec.BORDER_INSET).exterior.coords)
    w, h = spec.FINAL_SHEET
    return Plate("final", spec.FINAL_SHEET, (w / 2, h / 2), outline, (border,), placed, knot,
                 pin_holes(border, spec.HOLE_COUNT))


def _line_parts(geom) -> list[LineString]:
    if geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    lines = [g for g in getattr(geom, "geoms", []) if g.geom_type == "LineString"]
    if not lines:
        return []
    merged = linemerge(lines)
    return list(getattr(merged, "geoms", [merged]))


def build_practice(final: Plate) -> Plate:
    """A 12.5 x 7.5 window of the final plate: same coordinates, whole glyphs only."""
    x0, y0, x1, y1 = spec.PRACTICE_WINDOW
    m = spec.PRACTICE_MARGIN
    window = box(x0, y0, x1, y1)
    keep = box(x0 + m, y0 + m, x1 - m, y1 - m)
    lines = {}
    for key, line in final.lines.items():
        kept = [(c, g) for c, g in zip(line.chars, line.glyphs) if keep.contains(g)]
        if kept:
            chars, glyphs = zip(*kept)
            lines[key] = replace(line, chars=tuple(chars), glyphs=tuple(glyphs))
    knot = final.knot if all(keep.contains(p) for p in final.knot) else ()
    holes = tuple(h for h in final.holes if keep.contains(Point(h).buffer(spec.HOLE_DIAMETER / 2)))
    border = tuple(part for b in final.border for part in _line_parts(b.intersection(keep)))
    return Plate("practice", spec.PRACTICE_SHEET, (m - x0, m - y0), final.outline.intersection(window),
                 border, lines, knot, holes)


def outline_only(final: Plate) -> Plate:
    """Just the oval's edge, for whoever does the inlay and tile work around the plate."""
    return replace(final, name="plate_outline", border=(), lines={}, knot=(), holes=())
