"""Cinzel glyph outlines as shapely polygons (exact nonzero fill), with advances and GPOS pair kerning."""
from __future__ import annotations

import math
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union

from memorial import spec

Point2 = tuple[float, float]


class _FlatteningPen(BasePen):
    """Collects every contour as a point list, flattening curves to within `tolerance` font units."""

    def __init__(self, glyphset, tolerance: float):
        super().__init__(glyphset)
        self.tolerance = tolerance
        self.contours: list[list[Point2]] = []
        self._current: list[Point2] = []

    def _moveTo(self, pt):
        self._current = [pt]

    def _lineTo(self, pt):
        self._current.append(pt)

    def _qCurveToOne(self, p1, p2):
        p0 = self._current[-1]
        bend = math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1])
        steps = max(2, math.ceil(math.sqrt(bend / (4 * self.tolerance))))
        for i in range(1, steps + 1):
            t = i / steps
            mt = 1 - t
            self._current.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                                  mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._current[-1]
        bend = max(math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
                   math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]))
        steps = max(2, math.ceil(math.sqrt(3 * bend / (4 * self.tolerance))))
        for i in range(1, steps + 1):
            t = i / steps
            mt = 1 - t
            self._current.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                                  mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))

    def _closePath(self):
        if len(self._current) > 2:
            self.contours.append(self._current)
        self._current = []

    def _endPath(self):
        self._closePath()


def _winding(ring: list[Point2], pt: Point2) -> int:
    """Signed number of times the closed ring winds around pt."""
    x, y = pt
    w = 0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        side = (x2 - x1) * (y - y1) - (x - x1) * (y2 - y1)
        if y1 <= y < y2 and side > 0:
            w += 1
        elif y2 <= y < y1 and side < 0:
            w -= 1
    return w


def _fill_nonzero(contours: list[list[Point2]]) -> Polygon | MultiPolygon:
    """Exact nonzero-winding fill: node all contours, keep arrangement faces whose winding is nonzero."""
    rings = [c + [c[0]] for c in contours]
    faces = polygonize(unary_union([LineString(r) for r in rings]))
    keep = [f for f in faces if sum(_winding(r, f.representative_point().coords[0]) for r in rings) != 0]
    return unary_union(keep)


def _x_advance(value_record) -> int:
    if value_record is None:
        return 0
    return getattr(value_record, "XAdvance", 0) or 0


class Font:
    def __init__(self, path: Path, tolerance_units: float = spec.FONT_TOLERANCE_UNITS):
        self._tt = TTFont(str(path))
        self.units_per_em: int = self._tt["head"].unitsPerEm
        self.cap_height: float = self._tt["OS/2"].sCapHeight / self.units_per_em
        self._cmap = self._tt.getBestCmap()
        self._glyphset = self._tt.getGlyphSet()
        self._hmtx = self._tt["hmtx"]
        self._tolerance = tolerance_units
        self._kern_subtables = self._load_kern_subtables()
        self._outlines: dict[str, Polygon | MultiPolygon] = {}

    def glyph_name(self, char: str) -> str:
        try:
            return self._cmap[ord(char)]
        except KeyError:
            raise ValueError(f"font has no glyph for {char!r}") from None

    def advance(self, glyph: str) -> float:
        return self._hmtx[glyph][0] / self.units_per_em

    def outline(self, glyph: str) -> Polygon | MultiPolygon:
        if glyph not in self._outlines:
            pen = _FlatteningPen(self._glyphset, self._tolerance)
            self._glyphset[glyph].draw(pen)
            shape = _fill_nonzero(pen.contours) if pen.contours else Polygon()
            k = 1 / self.units_per_em
            self._outlines[glyph] = affinity.scale(shape, k, k, origin=(0, 0))
        return self._outlines[glyph]

    def kerning(self, left: str, right: str) -> float:
        """GPOS `kern` pair adjustment in em, following OpenType's first-matching-subtable rule."""
        for st in self._kern_subtables:
            covered = st.Coverage.glyphs
            if left not in covered:
                continue
            if st.Format == 1:
                for rec in st.PairSet[covered.index(left)].PairValueRecord:
                    if rec.SecondGlyph == right:
                        return _x_advance(rec.Value1) / self.units_per_em
                continue  # covered, but this subtable has no such pair
            if st.Format == 2:
                c1 = st.ClassDef1.classDefs.get(left, 0)
                c2 = st.ClassDef2.classDefs.get(right, 0)
                return _x_advance(st.Class1Record[c1].Class2Record[c2].Value1) / self.units_per_em
        return 0.0

    def _load_kern_subtables(self) -> list:
        if "GPOS" not in self._tt:
            return []
        gpos = self._tt["GPOS"].table
        indices = sorted({i for rec in gpos.FeatureList.FeatureRecord if rec.FeatureTag == "kern"
                          for i in rec.Feature.LookupListIndex})
        subtables = []
        for i in indices:
            lookup = gpos.LookupList.Lookup[i]
            for st in lookup.SubTable:
                if lookup.LookupType == 9:
                    if st.ExtensionLookupType != 2:
                        continue
                    st = st.ExtSubTable
                elif lookup.LookupType != 2:
                    continue
                subtables.append(st)
        return subtables
