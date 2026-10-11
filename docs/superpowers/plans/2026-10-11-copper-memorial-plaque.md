# Copper Memorial Plaque Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate validated, Carbide Create-ready cut files (DXF + SVG, inches) for the pierced
copper memorial plate (16 × 9.5" oval) and its 12.5 × 7.5" practice window, plus an
outline-only file and a 1:1 PDF print.

**Architecture:** A small Python package, `memorial/`. Its modules:
- `spec.py` holds every approved dimension.
- `font.py` turns Cinzel glyphs into shapely polygons, with nonzero fill and GPOS kerning.
- `text.py` sets lines, with thickening and per-pair spacing.
- `knot.py` builds the interlaced triquetra.
- `plate.py` assembles the final and practice plates.
- `rules.py` enforces the cutting rules.
- `export.py` writes the DXF, SVG and PDF.

`build.py` runs everything and refuses to write anything if any rule fails. All code runs in
the cadgen environment that text-to-cad installed, through `uvx`. cadgen's own tools validate
and render the DXF.

**Tech Stack:** Python 3.13 (uv-managed), shapely 2.2, fontTools 4.66, ezdxf 1.4, matplotlib
3.11, numpy, pytest 8.4.2, cadgen 0.7.20 (`cadgen.drawing_checks`, `cadgen dxf snapshot`,
`cadgen viewer`).

**Spec:** `docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md`

## Global Constraints

**Text and font**
- Exact text: `FITZGERALD`, `Mary Theresa`, `James Guinn`, `Feb 6, 1935`, `Apr 19, 1939`, `December 30, 2025`.
- Font: `fonts/Cinzel-Bold.ttf`, sha256 `2c6b1ff0d368efb73636700b69dbef707fa5602a06d085a4e91e5125082651f0`, shipped with its `fonts/OFL.txt`.

**Plate**
- Units are inches everywhere. Plate coordinates have the origin at the plate center, +y up.
- Plate: an ellipse with semi-axes 8.000 × 4.750.
- Border: the outline inset by 0.375".
- Pin holes: 8 holes of Ø0.070", evenly spaced along the border by arc length, the first at top center.

**Lettering**

| Line | Em size | Tracking | Thicken | Baseline y |
|---|---|---|---|---|
| FITZGERALD | 1.664" | +0.045 em | 0 | +0.966 |
| Names | 0.771" | 0 | 0.012" | −0.098 |
| Dates | 0.679" | 0 | 0.012" | −1.001 |
| Shared date | 0.700" | 0 | 0.012" | −2.082 |

- Letters are spaced so at least 0.06" of copper separates them.
- Each line is centered on its ink.

**Knot**
- 1.20" tall, centered at (0, −0.32), one leaf pointing up, tips enclosing 90°.
- Band 0.10" wide, with 0.08" bridges at the crossings.
- 0.24" between the knot's cut edge and the nearest name or date (`KNOT_SIDE_GAP`; see the Task 4 ruling in the ledger).

**Cutting rules**
- No neck narrower than 0.05".
- At least 0.06" of copper between any two separate cutouts.
- Letter centers that drop out at least 0.06" across.
- Every cutout at least 0.30" from the border line.

**Sheets**
- Final: 18 × 10", plate centered (offset (9, 5)).
- Practice: 13 × 8", window x ∈ [−8, 4.5], y ∈ [−3.75, 3.75], with 0.25" margins (offset (8.25, 4.0)).

**Output files**
- Layers: `REFERENCE_SHEET`, `ENGRAVE_BORDER`, `CUT_INSIDE`, `CUT_OUTSIDE`.
- DXF: `$INSUNITS` = 1 (inches); only closed `LWPOLYLINE`s and `CIRCLE`s, except the practice border, which is open polylines.
- SVG: `width`/`height` in `in`, with `viewBox="0 0 W H"`.
- PDF: 17 × 11" (MediaBox 1224 × 792).

**Environment and git**
- Run every Python command through `tools/py`, which wraps uvx with cadgen 0.7.20 and pytest 8.4.2.
- Never add AI attribution to commits or files.
- Work on branch `memorial-plaque`.

## Review Focus

1. **Carbide Create imports at the wrong scale.** Expected: the oval measures exactly
   16.000 × 9.500" after import. Task 7 tests that the DXF declares inches, that the SVG
   carries inch width/height with a matching viewBox, and that the outline's sheet
   extents are exactly (1, 0.25)–(17, 9.75).
2. **Letter centers lost in CAM.** Each counter must be its own closed ring nested
   inside its letter's ring, so Carbide Create keeps the island. Task 7 tests that the
   `CUT_INSIDE` polyline count equals outer rings plus counters, and that every counter
   ring lies inside a letter ring.
3. **A glyph silently vanishing or mis-filling,** like Cinzel's reverse-wound "1".
   Expected: every character is cut. Tested by Task 1 (per-character region test),
   Task 5 (full-text rule) and Task 8 (68 cutouts, 23 loose pieces).
4. **The practice window slicing through a letter.** Expected: only whole glyphs.
   Task 6 tests that every kept cutout and hole lies inside the window shrunk by 0.25".
5. **A rule failure must stop the build before any file is written.** Task 8 tests that
   a forced failure raises `BuildError` and leaves the output folder empty.

---

### Task 1: Toolchain, vendored font, spec constants, and glyph outlines

**Files:**
- Create: `tools/py`, `pytest.ini`, `fonts/Cinzel-Bold.ttf`, `fonts/OFL.txt`
- Create: `memorial/__init__.py`, `memorial/spec.py`, `memorial/font.py`
- Test: `tests/conftest.py`, `tests/test_font.py`

**Interfaces:**
- Produces:
  - `memorial.spec`: every constant named in Global Constraints, `LineSpec(text, em, tracking_em, thicken, baseline, column)`, and `LINES: dict[str, LineSpec]` with keys `surname, name_left, name_right, date_left, date_right, shared`.
  - `memorial.font.Font(path)`, with:
    - `.units_per_em: int` and `.cap_height: float` (em);
    - `.glyph_name(char) -> str`;
    - `.advance(glyph) -> float` (em);
    - `.kerning(left, right) -> float` (em);
    - `.outline(glyph) -> Polygon | MultiPolygon` (em units, pen origin at (0, 0) on the baseline).
  - Test fixture `font` (session scope).

- [ ] **Step 1: Branch and scaffold the toolchain**

```bash
cd /Users/ry/repos/cad
git checkout -b memorial-plaque
git add .gitignore docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md docs/superpowers/plans/2026-10-11-copper-memorial-plaque.md
git commit -m "Add memorial plaque design spec and implementation plan"
mkdir -p tools memorial tests fonts
```

Create `tools/py`:

```sh
#!/bin/sh
# Run Python inside the cadgen environment that text-to-cad installed, with pytest added.
exec uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.20 --with pytest==8.4.2 python "$@"
```

```bash
chmod +x tools/py
```

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 2: Vendor the font and license, and verify the hashes**

```bash
curl -sL -o fonts/Cinzel-Bold.ttf "https://fonts.gstatic.com/s/cinzel/v26/8vIU7ww63mVu7gtR-kwKxNvkNOjw-jHgTYo.ttf"
curl -sL -o fonts/OFL.txt "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/OFL.txt"
shasum -a 256 fonts/Cinzel-Bold.ttf fonts/OFL.txt
```

Expected:
```
2c6b1ff0d368efb73636700b69dbef707fa5602a06d085a4e91e5125082651f0  fonts/Cinzel-Bold.ttf
f2b3029aba64c378bf0963b62945eee15e564fe4330b934c8f2eb058282b5e83  fonts/OFL.txt
```

If the TTF hash differs (Google re-versioned the URL), get the current URL from
`curl -s "https://fonts.googleapis.com/css2?family=Cinzel:wght@700"`, then stop and report:
the hash is pinned in the spec.

- [ ] **Step 3: Write the spec constants**

Create `memorial/__init__.py`:

```python
"""Copper memorial plaque geometry. Design: docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md"""
```

Create `memorial/spec.py`:

```python
"""Every dimension the approved design fixes, in inches.

Plate coordinates: origin at the plate centre, +y up.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FONT_PATH = Path(__file__).resolve().parent.parent / "fonts" / "Cinzel-Bold.ttf"
FONT_SHA256 = "2c6b1ff0d368efb73636700b69dbef707fa5602a06d085a4e91e5125082651f0"
FONT_TOLERANCE_UNITS = 0.25  # curve flattening in font units: 0.0004" at the surname's size

# plate
PLATE_HALF_WIDTH = 8.0
PLATE_HALF_HEIGHT = 4.75
OUTLINE_SAMPLES = 2000
BORDER_INSET = 0.375
HOLE_DIAMETER = 0.070
HOLE_COUNT = 8

# cutting rules
MIN_SLOT = 0.05
MIN_COPPER = 0.06
MIN_ISLAND = 0.06
BORDER_CLEARANCE = 0.30

# lettering
SMALL_TEXT_THICKEN = 0.012
MIN_LETTER_GAP = 0.06


@dataclass(frozen=True)
class LineSpec:
    text: str
    em: float           # em size, in
    tracking_em: float  # extra space after every character, em
    thicken: float      # grown outward on every edge, in
    baseline: float     # y, in
    column: int         # -1 left column, 0 centred, +1 right column


LINES: dict[str, LineSpec] = {
    "surname": LineSpec("FITZGERALD", 1.664, 0.045, 0.0, 0.966, 0),
    "name_left": LineSpec("Mary Theresa", 0.771, 0.0, SMALL_TEXT_THICKEN, -0.098, -1),
    "name_right": LineSpec("James Guinn", 0.771, 0.0, SMALL_TEXT_THICKEN, -0.098, +1),
    "date_left": LineSpec("Feb 6, 1935", 0.679, 0.0, SMALL_TEXT_THICKEN, -1.001, -1),
    "date_right": LineSpec("Apr 19, 1939", 0.679, 0.0, SMALL_TEXT_THICKEN, -1.001, +1),
    "shared": LineSpec("December 30, 2025", 0.700, 0.0, SMALL_TEXT_THICKEN, -2.082, 0),
}

# trinity knot
KNOT_HEIGHT = 1.20
KNOT_CENTER = (0.0, -0.32)
KNOT_BAND = 0.10
KNOT_BRIDGE = 0.08
KNOT_TIP_DEG = 90.0
KNOT_SIDE_GAP = 0.30

# sheets
FINAL_SHEET = (18.0, 10.0)
PRACTICE_SHEET = (13.0, 8.0)
PRACTICE_WINDOW = (-8.0, -3.75, 4.5, 3.75)  # minx, miny, maxx, maxy in plate coordinates
PRACTICE_MARGIN = 0.25
```

- [ ] **Step 4: Write the failing font tests**

Create `tests/conftest.py`:

```python
import pytest

from memorial import spec
from memorial.font import Font


@pytest.fixture(scope="session")
def font():
    return Font(spec.FONT_PATH)
```

Create `tests/test_font.py`:

```python
import hashlib

import pytest

from memorial import spec

ALL_CHARS = sorted(set("".join(line.text for line in spec.LINES.values())) - {" "})


def test_text_is_exactly_what_the_family_approved():
    assert [line.text for line in spec.LINES.values()] == [
        "FITZGERALD", "Mary Theresa", "James Guinn", "Feb 6, 1935", "Apr 19, 1939", "December 30, 2025"]


def test_font_file_is_the_pinned_cinzel_bold():
    assert hashlib.sha256(spec.FONT_PATH.read_bytes()).hexdigest() == spec.FONT_SHA256


def test_cap_height_is_seven_tenths_of_an_em(font):
    assert font.cap_height == pytest.approx(0.700)
    assert font.outline(font.glyph_name("H")).bounds[3] == pytest.approx(0.700, abs=0.002)


@pytest.mark.parametrize("char", ALL_CHARS)
def test_every_character_is_one_solid_region(font, char):
    shape = font.outline(font.glyph_name(char))
    assert shape.geom_type == "Polygon"
    assert shape.area > 0.02


def test_reverse_wound_digit_one_is_still_filled(font):
    # Cinzel draws "1" with its single contour wound the other way; a naive fill drops it.
    assert font.outline(font.glyph_name("1")).area == pytest.approx(0.1067, abs=0.002)


def test_counters_are_holes_and_open_bowls_are_not(font):
    def holes(char):
        return len(font.outline(font.glyph_name(char)).interiors)

    assert [holes(c) for c in "ADab0"] == [1, 1, 1, 1, 1]
    assert [holes(c) for c in "R69p"] == [0, 0, 0, 0]


def test_pair_kerning_comes_from_gpos(font):
    assert font.kerning("R", "A") == pytest.approx(-0.012)
    assert font.kerning("H", "H") == 0.0


def test_advance_is_in_em(font):
    assert 0.5 < font.advance(font.glyph_name("H")) < 1.0


def test_unknown_character_is_a_clear_error(font):
    with pytest.raises(ValueError, match="no glyph"):
        font.glyph_name("☃")
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_font.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'memorial.font'`.

- [ ] **Step 6: Implement `memorial/font.py`**

```python
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
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_font.py -q`
Expected: 41 passed (8 named tests + 33 parametrized characters).

- [ ] **Step 8: Commit**

```bash
git add tools/py pytest.ini fonts memorial/__init__.py memorial/spec.py memorial/font.py tests/conftest.py tests/test_font.py
git commit -m "Add memorial spec constants and Cinzel glyph outlines"
```

---

### Task 2: Line setting (thicken, per-pair spacing, ink centering)

**Files:**
- Create: `memorial/text.py`
- Test: `tests/test_text.py`

**Interfaces:**
- Consumes: `Font.glyph_name`, `Font.outline`, `Font.advance`, `Font.kerning` (Task 1).
- Produces:
  - `memorial.text.SetLine`, a frozen dataclass:
    - `text: str`
    - `chars: tuple[str, ...]` (visible characters only)
    - `glyphs: tuple[Polygon, ...]` (one region per visible character, inches)
    - `width: float` (ink width)
    - `pushes: tuple[tuple[str, float], ...] = ()`
  - `set_line(font, text, em, tracking_em=0.0, thicken=0.0, min_gap=0.06, push_step=0.002) -> SetLine`. The line is centered on its ink at x = 0, with the baseline at y = 0.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_text.py`:

```python
import itertools

import pytest
from shapely.ops import unary_union

from memorial.text import set_line


def test_thickened_names_never_have_a_neck_under_the_slot_rule(font):
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.012, min_gap=0.06)
    for glyph in line.glyphs:
        core = glyph.buffer(-0.025)
        assert core.geom_type == "Polygon" and not core.is_empty


def test_unthickened_names_would_break_the_slot_rule(font):
    # documents why the small text is thickened
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.0, min_gap=0.0)
    assert any(g.buffer(-0.025).geom_type != "Polygon" for g in line.glyphs)


def test_every_visible_character_becomes_one_region(font):
    line = set_line(font, "Feb 6, 1935", em=0.679, thicken=0.012)
    assert "".join(line.chars) == "Feb6,1935"
    assert len(line.glyphs) == 9
    assert all(g.geom_type == "Polygon" for g in line.glyphs)


def test_letters_keep_the_minimum_copper_between_them(font):
    line = set_line(font, "Mary Theresa", em=0.771, thicken=0.012, min_gap=0.06)
    assert min(a.distance(b) for a, b in itertools.combinations(line.glyphs, 2)) >= 0.06 - 1e-9


def test_only_the_tight_pair_in_the_surname_is_opened(font):
    line = set_line(font, "FITZGERALD", em=1.664, tracking_em=0.045, thicken=0.0, min_gap=0.06)
    assert [char for char, _ in line.pushes] == ["A"]  # R and A are kerned into contact


def test_line_is_centred_on_its_ink(font):
    line = set_line(font, "December 30, 2025", em=0.7, thicken=0.012)
    minx, _, maxx, _ = unary_union(line.glyphs).bounds
    assert minx == pytest.approx(-maxx, abs=1e-9)
    assert line.width == pytest.approx(maxx - minx)


def test_capitals_sit_on_the_baseline(font):
    line = set_line(font, "FITZGERALD", em=1.664, tracking_em=0.045)
    _, miny, _, maxy = unary_union(line.glyphs).bounds
    assert 0.69 * 1.664 < maxy < 0.73 * 1.664
    assert -0.03 < miny < 0.0


def test_widths_match_the_approved_cuttable_preview(font):
    widths = {
        "FITZGERALD": set_line(font, "FITZGERALD", 1.664, 0.045, 0.0).width,
        "Mary Theresa": set_line(font, "Mary Theresa", 0.771, 0.0, 0.012).width,
        "James Guinn": set_line(font, "James Guinn", 0.771, 0.0, 0.012).width,
        "Feb 6, 1935": set_line(font, "Feb 6, 1935", 0.679, 0.0, 0.012).width,
        "Apr 19, 1939": set_line(font, "Apr 19, 1939", 0.679, 0.0, 0.012).width,
        "December 30, 2025": set_line(font, "December 30, 2025", 0.700, 0.0, 0.012).width,
    }
    expected = {"FITZGERALD": 11.700, "Mary Theresa": 6.285, "James Guinn": 5.468,
                "Feb 6, 1935": 3.581, "Apr 19, 1939": 4.094, "December 30, 2025": 6.968}
    for text, width in widths.items():
        assert width == pytest.approx(expected[text], abs=0.05), text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_text.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'memorial.text'`.

- [ ] **Step 3: Implement `memorial/text.py`**

```python
"""Set one line of lettering: kerned glyphs, optional thickening, and per-pair spacing for copper."""
from __future__ import annotations

from dataclasses import dataclass

from shapely import affinity
from shapely.geometry import Polygon

from memorial.font import Font


@dataclass(frozen=True)
class SetLine:
    text: str
    chars: tuple[str, ...]                     # visible characters, in order
    glyphs: tuple[Polygon, ...]                # one cut region per visible character, inches
    width: float                               # ink width, inches
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_text.py -q`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/text.py tests/test_text.py
git commit -m "Set memorial lettering with thickening and per-pair spacing"
```

---

### Task 3: Trinity knot with interlaced crossings

**Files:**
- Create: `memorial/knot.py`
- Test: `tests/test_knot.py`

**Interfaces:**
- Produces:
  - `triquetra_centerline(height, center=(0, 0), tip_deg=90.0, samples_per_arc=240) -> np.ndarray`: shape (N, 2), closed curve without a repeated end point, one leaf up.
  - `self_crossings(curve) -> list[tuple[float, float, tuple[float, float]]]`: (arclength a, arclength b, point).
  - `assign_alternation(crossings) -> list[tuple[float, float]]`: (over arclength, under arclength).
  - `local_segment(curve, s, half_length, samples=48) -> np.ndarray`.
  - `knot_cutouts(height, center, band, bridge, tip_deg=90.0) -> list[Polygon]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_knot.py`:

```python
import itertools

import numpy as np
import pytest

from memorial.knot import assign_alternation, knot_cutouts, self_crossings, triquetra_centerline


def test_centerline_has_the_requested_height_and_centre():
    curve = triquetra_centerline(1.2, center=(0.0, -0.32))
    lo, hi = curve.min(axis=0), curve.max(axis=0)
    assert hi[1] - lo[1] == pytest.approx(1.2)
    assert (lo + hi)[1] / 2 == pytest.approx(-0.32)
    assert (lo + hi)[0] / 2 == pytest.approx(0.0, abs=1e-9)


def test_one_leaf_points_straight_up():
    curve = triquetra_centerline(1.2)
    top = curve[np.argmax(curve[:, 1])]
    assert top[0] == pytest.approx(0.0, abs=1e-6)


def test_triquetra_crosses_itself_exactly_three_times():
    assert len(self_crossings(triquetra_centerline(1.2))) == 3


def test_crossings_alternate_over_and_under():
    pairs = assign_alternation(self_crossings(triquetra_centerline(1.2)))
    assert len(pairs) == 3
    assert all(over != under for over, under in pairs)


def test_band_becomes_three_equal_cutouts():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    assert len(pieces) == 3
    areas = [p.area for p in pieces]
    assert max(areas) == pytest.approx(min(areas), rel=1e-3)


def test_bridges_leave_the_design_width_of_copper():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    assert min(a.distance(b) for a, b in itertools.combinations(pieces, 2)) >= 0.079


def test_band_pieces_are_wide_enough_to_cut_and_drop_nothing():
    for piece in knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08):
        assert piece.buffer(-0.025).geom_type == "Polygon"
        assert len(piece.interiors) == 0


def test_knot_fits_its_height():
    pieces = knot_cutouts(1.2, (0.0, -0.32), band=0.10, bridge=0.08)
    miny = min(p.bounds[1] for p in pieces)
    maxy = max(p.bounds[3] for p in pieces)
    assert maxy - miny == pytest.approx(1.2 + 0.10, abs=0.08)  # centerline height plus the band (mitred tips)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_knot.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'memorial.knot'`.

- [ ] **Step 3: Implement `memorial/knot.py`**

```python
"""Trinity knot (triquetra): an interlaced band cut through the plate, as shapely polygons."""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

GAP_REACH = 0.3      # in, how far along each strand a crossing's gap is computed
SLIVER_GUARD = 0.01  # in, widens the under-strand cutter so no hairline of band survives


def triquetra_centerline(height: float, center=(0.0, 0.0), tip_deg: float = 90.0,
                         samples_per_arc: int = 240) -> np.ndarray:
    """Closed centreline (no repeated end point) with one leaf pointing up (+y).

    Three circular arcs, each swinging through the middle between two leaf tips. Tips sit
    at radius 2 (before scaling); each arc's circle is centred opposite the third tip at
    distance mu, solved so the two arcs meeting at a tip enclose `tip_deg`.
    """
    c2 = math.cos(math.radians(90 - tip_deg / 2)) ** 2
    qa, qb, qc = 1 - 4 * c2, -8 + 8 * c2, 16 - 16 * c2
    if abs(qa) < 1e-12:
        mu = -qc / qb
    else:
        roots = [(-qb + sign * math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa) for sign in (1, -1)]
        mu = min(r for r in roots if 0 < r < 4)
    radius = math.sqrt(4 + mu * mu - 2 * mu)
    units = [np.array([math.cos(t), math.sin(t)]) for t in (math.radians(-90 + 120 * k) for k in range(3))]
    centres = [mu * u for u in units]
    tips = [-2 * u for u in units]  # tip 0 points up

    def arc(i: int, start: np.ndarray, end: np.ndarray) -> np.ndarray:
        c = centres[i]
        a0 = math.atan2(start[1] - c[1], start[0] - c[0])
        a1 = math.atan2(end[1] - c[1], end[0] - c[0])
        am = math.atan2(-c[1], -c[0])  # the arc must swing through the middle
        for ccw in (True, False):
            sweep = (a1 - a0) % (2 * math.pi) if ccw else -((a0 - a1) % (2 * math.pi))
            to_mid = (am - a0) % (2 * math.pi) if ccw else -((a0 - am) % (2 * math.pi))
            if abs(to_mid) < abs(sweep):
                t = np.linspace(a0, a0 + sweep, samples_per_arc)
                return np.column_stack([c[0] + radius * np.cos(t), c[1] + radius * np.sin(t)])
        raise RuntimeError("triquetra arc construction failed")

    pts = np.vstack([arc(0, tips[1], tips[2]), arc(1, tips[2], tips[0])[1:], arc(2, tips[0], tips[1])[1:-1]])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    scale = height / (hi - lo)[1]
    return (pts - (lo + hi) / 2) * scale + np.asarray(center, dtype=float)


def _segments(curve: np.ndarray):
    start = curve
    vec = np.roll(curve, -1, axis=0) - curve
    lengths = np.linalg.norm(vec, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(lengths)[:-1]])
    return start, vec, lengths, cum


def self_crossings(curve: np.ndarray) -> list[tuple[float, float, tuple[float, float]]]:
    """Every self-crossing of a closed polyline as (arclength a, arclength b, point)."""
    start, vec, lengths, cum = _segments(curve)
    n = len(curve)
    found = []
    for i in range(n):
        p, r = start[i], vec[i]
        q, s = start[i + 1:], vec[i + 1:]
        denom = r[0] * s[:, 1] - r[1] * s[:, 0]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((q[:, 0] - p[0]) * s[:, 1] - (q[:, 1] - p[1]) * s[:, 0]) / denom
            u = ((q[:, 0] - p[0]) * r[1] - (q[:, 1] - p[1]) * r[0]) / denom
        for h in np.nonzero((denom != 0) & (t >= 0) & (t < 1) & (u >= 0) & (u < 1))[0]:
            j = i + 1 + h
            if min(j - i, n - (j - i)) <= 3:  # neighbouring segments, including at the tips
                continue
            found.append((cum[i] + t[h] * lengths[i], cum[j] + u[h] * lengths[j], tuple(p + t[h] * r)))
    return found


def assign_alternation(crossings) -> list[tuple[float, float]]:
    """Walk the curve and alternate over/under at each passage. Returns (over s, under s) per crossing."""
    passages = sorted((s, k, side) for k, (sa, sb, _) in enumerate(crossings) for side, s in ((0, sa), (1, sb)))
    over = {(k, side): n % 2 == 0 for n, (_, k, side) in enumerate(passages)}
    pairs = []
    for k, (sa, sb, _) in enumerate(crossings):
        if over[(k, 0)] == over[(k, 1)]:
            raise ValueError("these crossings cannot alternate over and under")
        pairs.append((sa, sb) if over[(k, 0)] else (sb, sa))
    return pairs


def local_segment(curve: np.ndarray, s: float, half_length: float, samples: int = 48) -> np.ndarray:
    """Points of the closed curve within +-half_length of arclength s."""
    ring = np.vstack([curve, curve[:1]])
    cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))])
    positions = np.linspace(s - half_length, s + half_length, samples) % cum[-1]
    return np.column_stack([np.interp(positions, cum, ring[:, 0]), np.interp(positions, cum, ring[:, 1])])


def knot_cutouts(height: float, center, band: float, bridge: float, tip_deg: float = 90.0) -> list[Polygon]:
    """The knot's cut-through regions: the band, with each under-strand stopped `bridge` short of the over-strand.

    Each gap is cut only from the under strand's own band, so neighbouring crossings never
    disturb each other.
    """
    curve = triquetra_centerline(height, center, tip_deg)
    band_shape = LineString(np.vstack([curve, curve[:1]])).buffer(band / 2, join_style="mitre", mitre_limit=5.0)
    gaps = []
    for over_s, under_s in assign_alternation(self_crossings(curve)):
        over_line = LineString(local_segment(curve, over_s, GAP_REACH))
        under_line = LineString(local_segment(curve, under_s, GAP_REACH))
        gaps.append(under_line.buffer(band / 2 + SLIVER_GUARD, cap_style="flat")
                    .intersection(over_line.buffer(band / 2 + bridge, cap_style="flat"))
                    .difference(over_line.buffer(band / 2, cap_style="flat")))
    pieces = band_shape.difference(unary_union(gaps))
    return [p for p in getattr(pieces, "geoms", [pieces]) if not p.is_empty]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_knot.py -q`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/knot.py tests/test_knot.py
git commit -m "Add interlaced trinity knot geometry"
```

---

### Task 4: Final plate assembly

**Files:**
- Create: `memorial/plate.py`
- Modify: `tests/conftest.py` (add the `final` fixture)
- Test: `tests/test_plate.py`

**Interfaces:**
- Consumes: `spec.*`, `set_line`, `SetLine`, `knot_cutouts`.
- Produces:
  - `memorial.plate.Plate`, a frozen dataclass:
    - `name: str`
    - `sheet: (w, h)`
    - `offset: (dx, dy)`, added to plate coordinates to get sheet coordinates
    - `outline: Polygon`
    - `border: tuple[LineString, ...]`
    - `lines: dict[str, SetLine]` (placed)
    - `knot: tuple[Polygon, ...]`
    - `holes: tuple[(x, y), ...]`
    - property `cutouts -> list[(label, Polygon)]`
  - `ellipse(half_w, half_h, samples) -> Polygon`
  - `move_line(line, dx, dy) -> SetLine`
  - `pin_holes(border, count) -> tuple`
  - `build_final(font) -> Plate`
  - Test fixture `final`.

- [ ] **Step 1: Add the fixture and write the failing tests**

Append to `tests/conftest.py`:

```python


@pytest.fixture(scope="session")
def final(font):
    from memorial.plate import build_final

    return build_final(font)
```

Create `tests/test_plate.py`:

```python
import pytest
from shapely.geometry import Point

from memorial import spec


def test_outline_is_16_by_9_5(final):
    minx, miny, maxx, maxy = final.outline.bounds
    assert (maxx - minx, maxy - miny) == (pytest.approx(16.0, abs=1e-6), pytest.approx(9.5, abs=1e-6))


def test_border_is_three_eighths_inside_the_edge(final):
    (border,) = final.border
    for x, y in list(border.coords)[::97]:
        assert final.outline.exterior.distance(Point(x, y)) == pytest.approx(0.375, abs=0.001)


def test_eight_pin_holes_evenly_spaced_first_at_top(final):
    (border,) = final.border
    assert len(final.holes) == 8
    assert final.holes[0] == (pytest.approx(0.0, abs=0.01), pytest.approx(4.375, abs=0.001))
    positions = sorted(border.project(Point(h)) for h in final.holes)
    steps = [b - a for a, b in zip(positions, positions[1:])]
    assert max(steps) == pytest.approx(border.length / 8, abs=0.01)
    assert min(steps) == pytest.approx(border.length / 8, abs=0.01)


def test_names_and_dates_flank_the_centred_knot(final):
    def centre_x(key):
        minx, _, maxx, _ = final.lines[key].glyphs[0].union(final.lines[key].glyphs[-1]).bounds
        return (minx + maxx) / 2

    knot_minx = min(p.bounds[0] for p in final.knot)
    knot_maxx = max(p.bounds[2] for p in final.knot)
    assert (knot_minx + knot_maxx) / 2 == pytest.approx(0.0, abs=1e-6)
    assert centre_x("name_left") == pytest.approx(-centre_x("name_right"), abs=1e-6)
    assert centre_x("name_left") < -3.5
    for key in ("name_left", "name_right", "date_left", "date_right"):
        nearest = min(min(g.distance(p) for p in final.knot) for g in final.lines[key].glyphs)
        assert nearest >= spec.KNOT_SIDE_GAP - 1e-6, key


def test_every_line_sits_on_its_baseline(final):
    for key, line_spec in spec.LINES.items():
        maxy = max(g.bounds[3] for g in final.lines[key].glyphs)
        # cap height 0.70 em; serifs and apexes overshoot to 0.72 em; mitred thickening adds at most 5 x 0.012"
        assert line_spec.baseline + 0.69 * line_spec.em < maxy < line_spec.baseline + 0.72 * line_spec.em + 0.06, key


def test_knot_is_1_2_tall_at_its_centre(final):
    miny = min(p.bounds[1] for p in final.knot)
    maxy = max(p.bounds[3] for p in final.knot)
    assert (miny + maxy) / 2 == pytest.approx(spec.KNOT_CENTER[1], abs=0.03)  # mitred tips are not symmetric
    assert len(final.knot) == 3


def test_lettering_and_knot_clear_the_border(final):
    (border,) = final.border
    assert min(region.distance(border) for _, region in final.cutouts) >= 0.30


def test_final_plate_is_centred_on_its_sheet(final):
    assert final.sheet == (18.0, 10.0)
    assert final.offset == (9.0, 5.0)


def test_cutouts_are_labelled_for_error_messages(final):
    labels = [label for label, _ in final.cutouts]
    assert labels[0] == "'F' in 'FITZGERALD'"
    assert labels[-1] == "knot piece 3"
    assert len(labels) == 68
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_plate.py -q`
Expected: errors with `ModuleNotFoundError: No module named 'memorial.plate'`.

- [ ] **Step 3: Implement `memorial/plate.py`**

```python
"""Assemble the final plate (and, in Task 6, the practice window) from the spec."""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon

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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_plate.py -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/plate.py tests/conftest.py tests/test_plate.py
git commit -m "Assemble the final memorial plate"
```

---

### Task 5: Cutting rules

**Files:**
- Create: `memorial/rules.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `Plate`, `SetLine`, `spec` (rule constants read at call time, so tests can monkeypatch them).
- Produces: `memorial.rules.check_plate(plate, *, full_text: bool) -> list[str]` (plain-English problems; empty means cuttable).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_rules.py`:

```python
from shapely.geometry import LineString, Polygon, box

from memorial.plate import Plate
from memorial.rules import check_plate
from memorial.text import SetLine


def _plate(letters=(), chars=None, text=None, holes=(), knot=()):
    outline = box(-8, -4.75, 8, 4.75)
    border = LineString(outline.buffer(-0.375, join_style="mitre").exterior.coords)
    chars = tuple(chars if chars is not None else "X" * len(letters))
    line = SetLine(text if text is not None else "".join(chars), chars, tuple(letters), 1.0)
    return Plate("test", (18.0, 10.0), (9.0, 5.0), outline, (border,), {"line": line}, tuple(knot), tuple(holes))


def _square(x, y, size=0.2):
    return box(x, y, x + size, y + size)


def test_a_clean_plate_passes():
    assert check_plate(_plate([_square(0, 0), _square(0.3, 0)]), full_text=True) == []


def test_too_little_copper_between_cutouts_is_reported():
    problems = check_plate(_plate([_square(0, 0), _square(0.25, 0)]), full_text=True)
    assert len(problems) == 1 and "copper between" in problems[0]


def test_a_neck_narrower_than_the_slot_rule_is_reported():
    dumbbell = _square(0, 0).union(box(0.2, 0.08, 0.6, 0.12)).union(_square(0.6, 0))
    problems = check_plate(_plate([dumbbell]), full_text=True)
    assert any("slot narrower" in p for p in problems)


def test_sharp_corners_are_not_slot_problems():
    sliver_tip = Polygon([(0, 0), (1.0, 0.1), (0, 0.3)])  # wide body, needle-sharp tip
    assert check_plate(_plate([sliver_tip]), full_text=True) == []


def test_a_tiny_letter_centre_is_reported():
    letter = Polygon(box(0, 0, 0.5, 0.5).exterior.coords, [box(0.23, 0.23, 0.27, 0.27).exterior.coords])
    problems = check_plate(_plate([letter]), full_text=True)
    assert any("letter centre" in p for p in problems)


def test_a_cutout_too_close_to_the_border_is_reported():
    problems = check_plate(_plate([_square(7.3, 0)]), full_text=True)
    assert any("from the border" in p for p in problems)


def test_a_pin_hole_off_the_border_is_reported():
    problems = check_plate(_plate([_square(0, 0)], holes=[(2.0, 2.0)]), full_text=True)
    assert any("off the border line" in p for p in problems)


def test_a_missing_character_is_reported_when_the_full_text_is_required():
    plate = _plate([_square(0, 0)], chars="A", text="AB")
    assert any("missing characters" in p for p in check_plate(plate, full_text=True))
    assert check_plate(plate, full_text=False) == []


def test_letters_that_run_together_are_reported():
    problems = check_plate(_plate([_square(0, 0), _square(0.1, 0)]), full_text=True)
    assert any("run together" in p for p in problems)


def test_the_real_final_plate_passes_every_rule(final):
    assert check_plate(final, full_text=True) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_rules.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'memorial.rules'`.

- [ ] **Step 3: Implement `memorial/rules.py`**

```python
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

    # 1. narrowest slot: shrinking a cutout by half the rule must leave exactly one piece
    for label, region in cutouts:
        if _count(region.buffer(-spec.MIN_SLOT / 2)) != 1:
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_rules.py -q`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/rules.py tests/test_rules.py
git commit -m "Enforce the copper cutting rules"
```

---

### Task 6: Practice window

**Files:**
- Modify: `memorial/plate.py` (add `build_practice`, `outline_only`)
- Modify: `tests/conftest.py` (add the `practice` fixture)
- Test: `tests/test_practice.py`

**Interfaces:**
- Consumes: `Plate`, `spec.PRACTICE_*`, `check_plate`.
- Produces: `build_practice(final: Plate) -> Plate` (name `"practice"`) and `outline_only(final: Plate) -> Plate` (name `"plate_outline"`, with only the outline), plus the test fixture `practice`.

- [ ] **Step 1: Add the fixture and write the failing tests**

Append to `tests/conftest.py`:

```python


@pytest.fixture(scope="session")
def practice(final):
    from memorial.plate import build_practice

    return build_practice(final)
```

Create `tests/test_practice.py`:

```python
import pytest
from shapely.geometry import Point, box

from memorial import spec
from memorial.rules import check_plate

KEEP = box(-8.0 + 0.25, -3.75 + 0.25, 4.5 - 0.25, 3.75 - 0.25)


def test_practice_outline_is_the_12_5_by_7_5_window(practice):
    assert practice.outline.bounds == pytest.approx((-8.0, -3.75, 4.5, 3.75), abs=1e-6)


def test_practice_keeps_only_whole_glyphs_inside_the_margin(practice):
    for label, region in practice.cutouts:
        assert KEEP.contains(region), label
    for h in practice.holes:
        assert KEEP.contains(Point(h).buffer(spec.HOLE_DIAMETER / 2))


def test_practice_contains_the_hardest_details(practice):
    assert len(practice.knot) == 3
    assert "".join(practice.lines["date_left"].chars) == "Feb6,1935"
    assert "".join(practice.lines["name_left"].chars) == "MaryTheresa"
    assert "".join(practice.lines["shared"].chars) == "December30,2025"
    assert "".join(practice.lines["surname"].chars).startswith("FITZG")
    assert len(practice.holes) == 3


def test_practice_border_is_an_open_arc_inside_the_margin(practice):
    assert practice.border
    for line in practice.border:
        assert not line.is_ring
        assert KEEP.buffer(1e-9).contains(line)
    assert sum(line.length for line in practice.border) > 9.0  # the left arc is about 9.85" long


def test_practice_sits_on_its_sheet_with_quarter_inch_margins(practice):
    assert practice.sheet == (13.0, 8.0)
    assert practice.offset == (8.25, 4.0)


def test_practice_passes_every_rule(practice):
    assert check_plate(practice, full_text=False) == []


def test_outline_only_has_nothing_but_the_oval(final):
    from memorial.plate import outline_only

    plate = outline_only(final)
    assert plate.name == "plate_outline"
    assert plate.cutouts == [] and plate.holes == () and plate.border == ()
    assert plate.outline.equals(final.outline)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_practice.py -q`
Expected: errors with `ImportError: cannot import name 'build_practice' from 'memorial.plate'`.

- [ ] **Step 3: Implement the practice window**

In `memorial/plate.py`, change the shapely import line to:

```python
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge
```

Then append to `memorial/plate.py`:

```python


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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_practice.py -q`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/plate.py tests/conftest.py tests/test_practice.py
git commit -m "Add the practice window and outline-only plate"
```

---

### Task 7: DXF, SVG and PDF export

**Files:**
- Create: `memorial/export.py`
- Test: `tests/test_export.py`

**Interfaces:**
- Consumes: `Plate` (with `.cutouts`, `.offset`, `.sheet`), `spec.HOLE_DIAMETER`.
- Produces:
  - `LAYERS: dict[str, tuple[int, str]]`
  - `layer_items(plate) -> list[(layer, kind, data, closed)]`
  - `write_dxf(plate, path)`, `write_svg(plate, path)`, `write_pdf(plate, path)`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_export.py`:

```python
import re
import xml.etree.ElementTree as ET

import ezdxf
import pytest
from cadgen.drawing_checks import validate_dxf_file
from shapely.geometry import Polygon

from memorial.export import write_dxf, write_pdf, write_svg

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture(scope="module")
def final_dxf(tmp_path_factory, final):
    path = tmp_path_factory.mktemp("dxf") / "final.dxf"
    write_dxf(final, path)
    return path


def _bounds(entities):
    xs, ys = [], []
    for e in entities:
        if e.dxftype() == "LWPOLYLINE":
            for x, y in e.get_points("xy"):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def test_dxf_is_in_inches_with_the_four_layers(final_dxf):
    doc = ezdxf.readfile(final_dxf)
    assert doc.header["$INSUNITS"] == 1
    assert {"REFERENCE_SHEET", "ENGRAVE_BORDER", "CUT_INSIDE", "CUT_OUTSIDE"} <= {layer.dxf.name for layer in doc.layers}


def test_dxf_outline_measures_16_by_9_5_centred_on_the_sheet(final_dxf):
    msp = ezdxf.readfile(final_dxf).modelspace()
    assert _bounds(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]')) == pytest.approx((1.0, 0.25, 17.0, 9.75), abs=1e-4)
    assert _bounds(msp.query('LWPOLYLINE[layer=="REFERENCE_SHEET"]')) == pytest.approx((0.0, 0.0, 18.0, 10.0))


def test_dxf_pin_holes_are_eight_circles_of_0_070(final_dxf):
    circles = list(ezdxf.readfile(final_dxf).modelspace().query('CIRCLE[layer=="CUT_INSIDE"]'))
    assert len(circles) == 8
    assert all(c.dxf.radius == pytest.approx(0.035) for c in circles)


def test_dxf_writes_every_letter_ring_and_counter_as_its_own_closed_polyline(final_dxf, final):
    polys = list(ezdxf.readfile(final_dxf).modelspace().query('LWPOLYLINE[layer=="CUT_INSIDE"]'))
    assert len(polys) == sum(1 + len(region.interiors) for _, region in final.cutouts)
    assert all(p.closed for p in polys)
    for p in polys:
        pts = list(p.get_points("xy"))
        assert all(a != b for a, b in zip(pts, pts[1:] + pts[:1]))  # no zero-length segments
    # every counter ring lies inside some letter ring, so CAM keeps the island
    rings = [Polygon(list(p.get_points("xy"))) for p in polys]
    counters = [r for r in rings if any(o is not r and o.contains(r) for o in rings)]
    # 23: A, D, a, b (two each in the small-cap B) and 0, plus r, p, 6 and 9, whose narrow openings close when thickened
    assert len(counters) == sum(len(region.interiors) for _, region in final.cutouts) == 23


def test_dxf_passes_cadgens_drawing_checks(final_dxf):
    assert [f.render() for f in validate_dxf_file(final_dxf) if f.severity == "error"] == []


def test_svg_is_sized_in_inches_with_a_sheet_viewbox(tmp_path, final):
    path = tmp_path / "final.svg"
    write_svg(final, path)
    root = ET.parse(path).getroot()
    assert (root.get("width"), root.get("height"), root.get("viewBox")) == ("18in", "10in", "0 0 18 10")
    groups = {g.get("id"): g for g in root.findall(f"{SVG}g")}
    assert set(groups) == {"REFERENCE_SHEET", "ENGRAVE_BORDER", "CUT_INSIDE", "CUT_OUTSIDE"}
    assert len(groups["CUT_INSIDE"].findall(f"{SVG}path")) == sum(1 + len(r.interiors) for _, r in final.cutouts)
    assert len(groups["CUT_INSIDE"].findall(f"{SVG}circle")) == 8
    outline_d = groups["CUT_OUTSIDE"].find(f"{SVG}path").get("d")
    ys = [float(v) for v in re.findall(r"[ML]\s*[-\d.]+,([-\d.]+)", outline_d)]
    assert min(ys) == pytest.approx(0.25, abs=1e-4) and max(ys) == pytest.approx(9.75, abs=1e-4)  # y flipped for SVG


def test_practice_border_is_written_as_open_polylines(tmp_path, practice):
    path = tmp_path / "practice.dxf"
    write_dxf(practice, path)
    msp = ezdxf.readfile(path).modelspace()
    border = list(msp.query('LWPOLYLINE[layer=="ENGRAVE_BORDER"]'))
    assert border and not any(p.closed for p in border)
    assert [f.render() for f in validate_dxf_file(path) if f.severity == "error"] == []
    assert _bounds(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]')) == pytest.approx((0.25, 0.25, 12.75, 7.75), abs=1e-4)


def test_pdf_is_a_tabloid_landscape_page(tmp_path, final):
    path = tmp_path / "final_fullsize.pdf"
    write_pdf(final, path)
    box = re.search(rb"/MediaBox\s*\[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", path.read_bytes())
    assert box and (float(box.group(1)), float(box.group(2))) == (1224.0, 792.0)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_export.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'memorial.export'`.

- [ ] **Step 3: Implement `memorial/export.py`**

```python
"""Write a Plate as DXF and SVG (inches, sheet coordinates) and the final plate as a 1:1 PDF."""
from __future__ import annotations

from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402

from memorial import spec  # noqa: E402
from memorial.plate import Plate  # noqa: E402

LAYERS = {  # name: (DXF colour index, SVG stroke colour), in drawing order
    "REFERENCE_SHEET": (8, "#999999"),
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


def layer_items(plate: Plate) -> list[tuple[str, str, object, bool]]:
    """(layer, "poly" | "circle", points or centre, closed) for everything on the sheet, in sheet coordinates."""
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


def write_dxf(plate: Plate, path: Path) -> None:
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 1     # inches
    doc.header["$MEASUREMENT"] = 0  # imperial
    for name, (aci, _) in LAYERS.items():
        doc.layers.add(name, color=aci)
    msp = doc.modelspace()
    for layer, kind, data, closed in layer_items(plate):
        if kind == "circle":
            msp.add_circle(data, spec.HOLE_DIAMETER / 2, dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(data, close=closed, dxfattribs={"layer": layer})
    doc.saveas(path)


def write_svg(plate: Plate, path: Path) -> None:
    w, h = plate.sheet
    groups: dict[str, list[str]] = {name: [] for name in LAYERS}
    for layer, kind, data, closed in layer_items(plate):
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tools/py -m pytest tests/test_export.py -q`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add memorial/export.py tests/test_export.py
git commit -m "Export memorial plates as inch DXF, SVG and a 1:1 PDF"
```

---

### Task 8: Build command, real outputs, visual review and README

**Files:**
- Create: `build.py`, `README.md` (replaces the one-line stub)
- Create (generated): `out/final.dxf`, `out/final.svg`, `out/practice.dxf`, `out/practice.svg`, `out/plate_outline.dxf`, `out/plate_outline.svg`, `out/final_fullsize.pdf`, `out/previews/*.png`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `build.build(out_dir: Path = OUT) -> dict` (a report per plate), `build.BuildError(problems: dict[str, list[str]])`, and `build.main() -> int`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_build.py`:

```python
import pytest

import build
from memorial import spec

EXPECTED_FILES = {"final.dxf", "final.svg", "practice.dxf", "practice.svg",
                  "plate_outline.dxf", "plate_outline.svg", "final_fullsize.pdf"}


def test_build_writes_every_file_and_reports_the_counts(tmp_path):
    report = build.build(tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == EXPECTED_FILES
    assert report["final"]["size_in"] == (16.0, 9.5)
    assert report["final"]["cutouts"] == 68
    assert report["final"]["loose_pieces"] == 23
    assert report["final"]["pin_holes"] == 8
    assert report["practice"]["size_in"] == (12.5, 7.5)
    assert report["practice"]["cutouts"] == 55
    assert report["practice"]["loose_pieces"] == 19
    assert report["practice"]["pin_holes"] == 3


def test_build_creates_a_missing_output_folder(tmp_path):
    out = tmp_path / "new" / "out"
    build.build(out)
    assert (out / "final.dxf").exists()


def test_build_refuses_to_write_anything_when_a_rule_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(spec, "MIN_COPPER", 0.5)
    with pytest.raises(build.BuildError) as err:
        build.build(tmp_path / "out")
    assert err.value.problems["final"]
    assert not (tmp_path / "out").exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tools/py -m pytest tests/test_build.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'build'`.

- [ ] **Step 3: Implement `build.py`**

```python
"""Build every memorial plate file into out/. Writes nothing if any cutting rule fails.

Run:  tools/py build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from cadgen.drawing_checks import validate_dxf_file

from memorial import spec
from memorial.export import write_dxf, write_pdf, write_svg
from memorial.font import Font
from memorial.plate import Plate, build_final, build_practice, outline_only
from memorial.rules import check_plate

OUT = Path(__file__).resolve().parent / "out"


class BuildError(Exception):
    def __init__(self, problems: dict[str, list[str]]):
        self.problems = problems
        super().__init__("; ".join(f"{name}: {len(items)} problem(s)" for name, items in problems.items() if items))


def summarize(plate: Plate) -> dict:
    minx, miny, maxx, maxy = plate.outline.bounds
    return {
        "size_in": (round(maxx - minx, 3), round(maxy - miny, 3)),
        "cutouts": len(plate.cutouts),
        "loose_pieces": sum(len(region.interiors) for _, region in plate.cutouts),
        "pin_holes": len(plate.holes),
        "kept": {line.text: "".join(line.chars) for line in plate.lines.values()},
        "spacing_opened": {line.text: list(line.pushes) for line in plate.lines.values() if line.pushes},
    }


def build(out_dir: Path = OUT) -> dict:
    font = Font(spec.FONT_PATH)
    final = build_final(font)
    practice = build_practice(final)
    problems = {"final": check_plate(final, full_text=True), "practice": check_plate(practice, full_text=False)}
    if any(problems.values()):
        raise BuildError(problems)
    out_dir.mkdir(parents=True, exist_ok=True)
    for plate in (final, practice, outline_only(final)):
        dxf = out_dir / f"{plate.name}.dxf"
        write_dxf(plate, dxf)
        write_svg(plate, out_dir / f"{plate.name}.svg")
        errors = [f.render() for f in validate_dxf_file(dxf) if f.severity == "error"]
        if errors:
            raise BuildError({plate.name: errors})
    write_pdf(final, out_dir / "final_fullsize.pdf")
    return {"final": summarize(final), "practice": summarize(practice)}


def main() -> int:
    try:
        report = build()
    except BuildError as err:
        for name, items in err.problems.items():
            for item in items:
                print(f"[{name}] {item}", file=sys.stderr)
        print("Build failed: fix the problems above.", file=sys.stderr)
        return 1
    for name, info in report.items():
        width, height = info["size_in"]
        print(f"{name}: {width} x {height} in, {info['cutouts']} cutouts, "
              f"{info['loose_pieces']} letter centres to glue back, {info['pin_holes']} pin holes")
        if name == "practice":
            for text, kept in info["kept"].items():
                print(f"  keeps {kept!r} of {text!r}")
        for text, pushes in info["spacing_opened"].items():
            print(f"  spacing opened in {text!r}: {pushes}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass, then the whole suite**

Run: `tools/py -m pytest tests/test_build.py -q`
Expected: 3 passed.

Run: `tools/py -m pytest -q`
Expected: every test passes (94 in total).

- [ ] **Step 5: Build the real files**

Run: `tools/py build.py`

Expected: the first line reads
`final: 16.0 x 9.5 in, 68 cutouts, 23 letter centres to glue back, 8 pin holes`, followed by
`spacing opened in ...` lines (FITZGERALD shows only `('A', 0.122)`). The practice line reads
`practice: 12.5 x 7.5 in, 55 cutouts, 19 letter centres to glue back, 3 pin holes`, and its `keeps`
lines show the full `MaryTheresa`, `Feb6,1935` and `December30,2025`, 8 of the 10 surname
letters, 5 of `James Guinn` and 4 of `Apr 19, 1939`. The output ends with `wrote /Users/ry/repos/cad/out`.

- [ ] **Step 6: Render previews with cadgen and review them visually**

```bash
mkdir -p out/previews
for f in final practice plate_outline; do
  uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.20 cadgen dxf snapshot out/$f.dxf out/previews/$f.png
done
```

Expected: `saved snapshot: .../out/previews/final.png` (and the same for practice and plate_outline).

Open each PNG with the Read tool and compare it with the approved "Cuttable version" mockup
(`.superpowers/brainstorm/*/content/cuttable-v2.html`). Check:
- **Text:** all six lines are present with every character, including the "1"s.
- **Knot:** it sits between the names, with 3 visible over/under gaps.
- **Holes and border:** 8 pin holes sit on the green border.
- **Practice:** it shows the oval's left end and straight trim edges.

If anything differs, stop and report rather than adjusting the geometry.

- [ ] **Step 7: Start the CAD Viewer and collect links for the user**

```bash
uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.20 cadgen viewer --host 127.0.0.1 --json --detach
```

Read `url` from the JSON line. For each of `out/final.dxf`, `out/practice.dxf` and
`out/plate_outline.dxf`, build the link `<url>?file=<URL-encoded absolute path>`, and keep
the three links for the handoff.

- [ ] **Step 8: Write `README.md`**

````markdown
# Fitzgerald memorial plate

Pierced copper plate (0.020" sheet, 16 × 9.5" oval) for Mary Theresa and James Guinn Fitzgerald.
Design: `docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md`.

## Files (`out/`)

| File | Use |
|---|---|
| `practice.svg` / `.dxf` | Cut this first, on the 13 × 8" sheet |
| `final.svg` / `.dxf` | The real plate, on the 18 × 10" sheet |
| `plate_outline.svg` / `.dxf` | The oval's edge only, for the inlay and tile work |
| `final_fullsize.pdf` | Print at 100% on 11 × 17" paper and lay it on the slice |

## Carbide Create

1. **Import and check the scale.** Import the SVG (or the DXF), then check that the oval
   measures **16.000 × 9.500"** (practice 12.5 × 7.5"). If it doesn't, the import scale is wrong.
2. **Set the tool.** Enter the tapered bit as a **0.035" ball nose**.
3. **Build the toolpaths in this order:**

   | Vectors (colour) | Toolpath | Depth |
   |---|---|---|
   | Border (green) | Contour, no offset | 0.006" |
   | Letters, knot, pin holes (red) | Contour, **inside** | 0.043" |
   | Oval edge (blue) | Contour, **outside** | 0.043" |

4. **Feeds and speeds:** about 18,000 RPM, 10 IPM, 3 IPM plunge, 0.005" per pass, with
   cutting fluid.
5. **Preview the simulation.** Check that every letter center (in A, D, B, 0, and the small
   r, p, 6 and 9) stays as an island.
6. **Hold-down and removal:** keep the sheet fully glued down. Remove it by peeling or with
   acetone, never by prying. Save the 23 letter centers (19 on the practice piece) and glue
   them back onto the wood in place.

## Rebuild

```bash
tools/py -m pytest -q   # tests
tools/py build.py       # regenerate out/ (refuses to write if a cutting rule fails)
```
````

- [ ] **Step 9: Commit**

```bash
git add build.py README.md tests/test_build.py out
git commit -m "Build the memorial plate cut files, previews and README"
```

---

## Self-review notes

How the spec's requirements map to tasks:
- **Text strings, font hash:** Task 1.
- **Thickening and per-pair spacing:** Task 2.
- **Knot (3 pieces, 0.08" bridges):** Task 3.
- **Plate, border, holes and columns:** Task 4.
- **Cutting rules 1–5 and 7:** Task 5. **Rule 6, the built-in DXF checks:** Tasks 7 and 8.
- **Practice window:** Task 6.
- **Layers, units, PDF and outline file:** Tasks 6 and 7.
- **Verification (measurements, piece counts, snapshots, viewer):** Tasks 7 and 8.
- **Cut settings:** the README in Task 8.

Out of scope, so no task covers them: G-code, the redwood work, finishing.
