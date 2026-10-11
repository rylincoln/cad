"""Set one line of lettering: kerned glyphs, optional thickening, and per-pair spacing for copper."""
from __future__ import annotations

from dataclasses import dataclass

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from memorial.font import Font

WALL_MARGIN = 0.005  # in, extra width given to a widened wall beyond the slot rule


@dataclass(frozen=True)
class SetLine:
    text: str
    chars: tuple[str, ...]                      # visible characters, in order
    glyphs: tuple[Polygon, ...]                 # one cut region per visible character, inches (several once tied)
    width: float                                # ink width, inches
    pushes: tuple[tuple[str, float], ...] = ()  # (character, extra space opened before it)


def _widen_thin_walls(shape: Polygon | MultiPolygon, min_slot: float) -> Polygon | MultiPolygon:
    """Widen every cut wall narrower than `min_slot` that separates a letter centre from the plate or another centre.

    Thickening closes some loops (small r, p, 6, 9 and B) with only a sliver of overlap. The bit
    could not cut that sliver, so the centre would stay tacked to the plate. Growing the wall
    into the centre (never outward) until it meets the slot rule lets the centre drop out cleanly
    while the letter's outline stays as designed.
    """
    parts = list(getattr(shape, "geoms", [shape]))
    widened = []
    for part in parts:
        for _ in range(3):
            if not part.interiors:
                break
            r = min_slot / 2
            thin = part.difference(part.buffer(-r).buffer(r))
            rings = [part.exterior, *part.interiors]
            grown = []
            for piece in getattr(thin, "geoms", [thin]):
                touched = [i for i, ring in enumerate(rings) if piece.distance(ring) < 1e-6]
                if piece.is_empty or len(touched) < 2:
                    continue
                wall = rings[touched[0]].distance(rings[touched[1]])
                # a wall between two centres grows both ways; a wall to the outside grows only inward
                between_centres = 0 not in touched
                reach = (min_slot - wall) / 2 + WALL_MARGIN if between_centres else min_slot - wall + WALL_MARGIN
                grown.append(piece.buffer(reach))
            if not grown:
                break
            # never past the letter's outline, so its silhouette stays as designed
            part = part.union(unary_union(grown).intersection(Polygon(part.exterior)))
        widened.append(part)
    return widened[0] if len(widened) == 1 else unary_union(widened)


def set_line(font: Font, text: str, em: float, tracking_em: float = 0.0, thicken: float = 0.0,
             min_gap: float = 0.06, push_step: float = 0.002, min_slot: float = 0.0) -> SetLine:
    """Lay out `text` left to right, then centre it on its ink (x = 0) with the baseline at y = 0.

    Every glyph is grown outward by `thicken` (mitred corners). A glyph that would come
    within `min_gap` of any glyph already set is pushed right in `push_step` increments
    until it clears; only those pairs move. With `min_slot`, any wall around a letter centre
    thinner than the slot rule is widened first.
    """
    names = [font.glyph_name(c) for c in text]
    x = 0.0
    chars: list[str] = []
    placed: list[Polygon] = []
    pushes: list[tuple[str, float]] = []
    for i, (char, name) in enumerate(zip(text, names)):
        outline = font.outline(name)
        if not outline.is_empty:
            shape = affinity.scale(outline, em, em, origin=(0, 0))
            if thicken:
                shape = shape.buffer(thicken, join_style="mitre")
            if min_slot:
                shape = _widen_thin_walls(shape, min_slot)
            moved = affinity.translate(shape, x, 0)
            push = 0.0
            while placed and min(moved.distance(p) for p in placed) < min_gap:
                push += push_step
                moved = affinity.translate(shape, x + push, 0)
            if push:
                pushes.append((char, round(push, 4)))
            x += push
            chars.append(char)
            placed.append(moved)
        kern = font.kerning(name, names[i + 1]) if i + 1 < len(names) else 0.0
        x += (font.advance(name) + kern) * em + tracking_em * em
    minx = min(p.bounds[0] for p in placed)
    maxx = max(p.bounds[2] for p in placed)
    shift = -(minx + maxx) / 2
    glyphs = tuple(affinity.translate(p, shift, 0) for p in placed)
    return SetLine(text, tuple(chars), glyphs, maxx - minx, tuple(pushes))
