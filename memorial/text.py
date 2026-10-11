"""Set one line of lettering: kerned glyphs, optional thickening, and per-pair spacing for copper."""
from __future__ import annotations

from dataclasses import dataclass

from shapely import affinity
from shapely.geometry import Polygon

from memorial.font import Font


@dataclass(frozen=True)
class SetLine:
    text: str
    chars: tuple[str, ...]                      # visible characters, in order
    glyphs: tuple[Polygon, ...]                 # one cut region per visible character, inches
    width: float                                # ink width, inches
    pushes: tuple[tuple[str, float], ...] = ()  # (character, extra space opened before it)


def set_line(font: Font, text: str, em: float, tracking_em: float = 0.0, thicken: float = 0.0,
             min_gap: float = 0.06, push_step: float = 0.002) -> SetLine:
    """Lay out `text` left to right, then centre it on its ink (x = 0) with the baseline at y = 0.

    Every glyph is grown outward by `thicken` (mitred corners). A glyph that would come
    within `min_gap` of any glyph already set is pushed right in `push_step` increments
    until it clears; only those pairs move.
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
