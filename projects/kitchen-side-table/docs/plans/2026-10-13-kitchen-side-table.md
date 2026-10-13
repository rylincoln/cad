# Kitchen Side Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate validated, Carbide Create-ready cut files (DXF + SVG, inches), labelled previews
and a 3D model for the kitchen side table: four flared LVL legs, four plywood aprons with clip
grooves, a fit test, and a cherry top with a swept front edge.

**Architecture:** A small Python package, `table/`, in `projects/kitchen-side-table/`. `spec.py`
holds every number. `top.py`, `legs.py` and `aprons.py` draw each part flat in its own face
coordinates with shapely. `frame.py` places every part in table coordinates through a `Placed`
record: a part's outline plus the origin and axes of the face that's cut first. Every assembly
check, the weight and the 3D model work from that record. `sheets.py` lays the parts on their stock
by rotation and translation only. `rules.py` checks the spec's ten rules. `export.py` writes DXF,
SVG and PNG; `model.py` writes STEP and GLB with build123d. `build.py` refuses to write anything
when a rule fails.

**Tech Stack:** Python 3.13 through `tools/py` (cadgen 0.7.20's environment): shapely 2.2, ezdxf
1.4.4, matplotlib 3.11, numpy 2.5, build123d 0.11.1, pytest 8.4.2, and
`cadgen.drawing_checks.validate_dxf_file`.

**Spec:** `projects/kitchen-side-table/docs/specs/2026-10-13-kitchen-side-table-design.md`

Every code block below was run before this plan was written: the full suite passes (84 tests in
about 5 seconds), the build is clean, and cadgen's validator finds nothing in the DXFs.

## Global Constraints

- Run Python only through `tools/py`, from the repo root (`/Users/ry/repos/cad`). Name the project:
  `tools/py -m pytest projects/kitchen-side-table -q`. There is nothing to install.
- Units are inches everywhere.
- Table coordinates are right-handed: x from the left end as seen from the room; y from the front
  edge's deepest point (y = 0) toward the wall (y = D); z up from the floor.
- Sheet coordinates: origin at the stock's lower-left corner on the machine, x right, y away from
  the operator, seen from above. Parts go on by rotation and translation only, never mirrored.
- Measured stock: LVL 32.5 × 11.75 × 1.786; plywood 32 × 11.875 × 0.723; top glue-up nominal 32 × 24
  and 0.75 thick (finished stock). Two-flute bit: 1.4" flute, 2.0" stickout. Three-flute bit: 1.0"
  flute. Bit diameter 0.25.
- Nominal results: top 31.75 × 23.75; legs 31.25 long; long aprons 26.75; side aprons 15.178;
  housings 0.728 wide; laps 0.723 deep; LVL spare about 0.3; clearance pass 0.506 deep; first
  finishing stage 1.3; full depth 1.806; dowel holes 0.5 into the top and 1.0625 into the aprons;
  about 64 lb to tip it.
- Layers, in this order: `REFERENCE_STOCK`, `POCKET_HOUSING`, `POCKET_LAP`, `GROOVE_CENTERLINE`,
  `CLEARANCE`, `ROUGH`, `CUT_OUTSIDE`. The part names appear only in the previews.
- Every function reads `spec` values when it runs, never at import, so tests can monkeypatch them.
- Style: `from __future__ import annotations`, a one-line module docstring, few comments, and test
  names that read as sentences.
- Write the failing test first, and run the project's whole suite before every commit.
- Commit messages are a single imperative sentence in sentence case, with no type prefix and no
  trailers. Never add AI attribution: no `Co-Authored-By`, no "Generated with", no session links.
- Stage only this project's files and the repo `README.md`, by path. Never stage
  `projects/fitzgerald-memorial/out/*.c2d`; they are modified in the working tree on purpose.
- Don't import from `projects/fitzgerald-memorial`. This project has its own small exporter.

## Review Focus

These are the inputs the spec implies but no rule test exercises. Each one is the most likely
thing to bite once the real measurements go in, and each has a test in the task that owns the code:

1. **A glue-up a little smaller than nominal** (31.5 × 23.5). Everything should rescale and still
   pass. Test: `test_a_glue_up_a_little_smaller_than_nominal_still_passes_and_rescales` (Task 6).
2. **A top sanded thinner** (0.72). The legs should grow to keep the table 32" tall, and the dowel
   holes should get shallower so ¼" of cherry stays above them. Tests:
   `test_the_dowel_holes_follow_a_top_sanded_thinner` (Task 3) and
   `test_a_top_sanded_to_0_72_still_passes_with_longer_legs` (Task 6).
3. **Plywood a little thinner or thicker** (0.70–0.75). The housings, laps and coupon should follow.
   Test: `test_plywood_a_little_thinner_or_thicker_still_passes` (Task 6).
4. **Rebuilding after measuring**, into an `out/` that already exists. The files should be
   replaced, not refused. Test: `test_rebuilding_into_an_existing_folder_replaces_the_files`
   (Task 9).
5. **The console report.** It should print the depths to set in Carbide Create and the values
   still nominal, and print the problems and exit 1 when a rule fails. Tests:
   `test_main_prints_the_numbers_and_the_values_still_to_measure` and
   `test_main_prints_the_problems_and_fails_when_a_rule_fails` (Task 9).

---

## File structure

```
projects/kitchen-side-table/
  AGENTS.md          project rules (Task 9)
  README.md          machining and assembly guide (Task 9)
  build.py           checks, then writes out/ (Task 9)
  pytest.ini         testpaths = tests, pythonpath = . (Task 1)
  table/
    __init__.py      package marker (Task 1)
    spec.py          every number; the measured block and NOMINAL (Task 1)
    top.py           the top's outline (Task 1)
    legs.py          legs, pockets, dogbones, fit-test pockets (Task 2)
    aprons.py        aprons, grooves, dowel holes, coupon (Task 3)
    frame.py         Placed, Table, placement, weight and tipping (Task 4)
    sheets.py        the four jobs on their stock, LVL depths (Task 5)
    rules.py         check_table (Task 6)
    export.py        DXF, SVG, PNG previews (Task 7)
    model.py         STEP and GLB with build123d (Task 8)
  tests/             conftest.py and one test file per module, plus test_build.py
  docs/specs/        the design (already written)
  docs/plans/        this plan
  out/               generated files, committed (Task 9)
```

Modify: the repo's `README.md` (Task 9): one line in the projects table, and build123d in Credits.

---

### Task 1: Project skeleton, the spec, and the top outline

**Files:**
- Create: `projects/kitchen-side-table/pytest.ini`
- Create: `projects/kitchen-side-table/table/__init__.py`
- Create: `projects/kitchen-side-table/table/spec.py`
- Create: `projects/kitchen-side-table/table/top.py`
- Test: `projects/kitchen-side-table/tests/test_spec.py`, `projects/kitchen-side-table/tests/test_top.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `table.spec` (module of float constants, `NOMINAL: tuple[str, ...]`,
  `DENSITY: dict[str, float]`, tuples `COUPON`, `WORK_AREA`, `FIT_TEST_STOCK`);
  `table.top.top_size() -> tuple[float, float]`; `table.top.front_edge_y(x: float) -> float`;
  `table.top.top_outline() -> shapely Polygon` in table (x, y).

- [ ] **Step 1: Create the project's pytest config and package marker**

`projects/kitchen-side-table/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

`projects/kitchen-side-table/table/__init__.py`:

```python
"""Kitchen side table: cut files for the legs, aprons and top."""
```

- [ ] **Step 2: Write the failing tests**

`projects/kitchen-side-table/tests/test_spec.py`:

```python
from table import spec


def test_every_nominal_name_is_a_measured_input():
    assert all(isinstance(getattr(spec, name), float) for name in spec.NOMINAL)


def test_only_the_tops_width_and_depth_still_need_measuring():
    assert spec.NOMINAL == ("TOP_WIDTH", "TOP_DEPTH")
```

`projects/kitchen-side-table/tests/test_top.py`:

```python
import pytest
from shapely.geometry import Point

from table.top import front_edge_y, top_outline, top_size


def test_the_finished_top_is_the_glue_up_less_the_trim():
    assert top_size() == pytest.approx((31.75, 23.75))


def test_the_front_edge_starts_2_25_back_at_the_left_and_reaches_the_front_at_82_percent():
    w, _ = top_size()
    assert front_edge_y(0.0) == pytest.approx(2.25)
    assert front_edge_y(0.82 * w) == pytest.approx(0.0)
    assert front_edge_y(w) == pytest.approx(0.0)
    assert all(front_edge_y(w * i / 20) >= front_edge_y(w * (i + 1) / 20) for i in range(20))


def test_the_top_is_21_5_deep_at_the_left_end_and_23_75_at_the_right():
    w, d = top_size()
    assert d - front_edge_y(0.0) == pytest.approx(21.5)
    assert d - front_edge_y(w) == pytest.approx(23.75)


def test_the_outline_fills_the_finished_size():
    assert top_outline().is_valid
    assert top_outline().bounds == pytest.approx((0.0, 0.0, 31.75, 23.75))


def test_the_back_corners_are_square_and_the_front_corners_rounded():
    outline = top_outline()
    w, d = top_size()
    assert outline.boundary.distance(Point(0, d)) < 1e-9
    assert outline.boundary.distance(Point(w, d)) < 1e-9
    assert outline.distance(Point(w, 0)) == pytest.approx(1.25 * (2 ** 0.5 - 1), abs=0.005)
    assert outline.distance(Point(0, front_edge_y(0.0))) > 0.5


def test_the_shallow_end_is_on_the_left():
    outline = top_outline()
    lowest = lambda x0, x1: min(y for x, y in outline.exterior.coords if x0 <= x <= x1)  # noqa: E731
    assert lowest(0, 3) > lowest(28.75, 31.75) + 1.5
```

- [ ] **Step 3: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: 2 errors during collection (`ImportError: cannot import name 'spec' from 'table'` and
`ModuleNotFoundError: No module named 'table.top'`).

- [ ] **Step 4: Write `table/spec.py`**

The measured block comes first. Everything else is the approved design.

```python
"""Every number the approved design fixes, in inches, and the measured stock and bit.

Table coordinates: x from the left end as seen from the room, y from the front edge's deepest point
toward the wall, z up from the floor (right-handed).
"""
from __future__ import annotations

# measured stock and bit; a name stays in NOMINAL until it has been measured
TOP_WIDTH = 32.0              # cherry glue-up, along the wall
TOP_DEPTH = 24.0              # cherry glue-up, front to back
TOP_THICKNESS = 0.75          # finished stock
LVL_LENGTH = 32.5
LVL_WIDTH = 11.75
LVL_THICKNESS = 1.786
PLY_LENGTH = 32.0
PLY_WIDTH = 11.875
PLY_THICKNESS = 0.723
TWO_FLUTE_LENGTH = 1.4        # the 1/4" two-flute bit, for the LVL
THREE_FLUTE_LENGTH = 1.0      # the 1/4" three-flute bit, for the plywood, fit test and top
STICKOUT = 2.0                # the two-flute bit, out of the collet
NOMINAL = ("TOP_WIDTH", "TOP_DEPTH")

# table
HEIGHT = 32.0
TOP_TRIM = 0.125              # the outline is cut this far inside the glue-up on every side
LEG_INSET = 1.0               # legs' outer faces in from each end of the top
BACK_LEG_FROM_WALL = 3.0      # back legs' back faces from the back edge
FRONT_LEG_BEHIND_EDGE = 3.5   # front legs' front faces behind the front edge's deepest point
SWEEP_DROP = 2.25
SWEEP_FLAT_FROM = 0.82        # the sweep reaches the deepest point this fraction of the way along
RADIUS_LEFT = 2.5
RADIUS_RIGHT = 1.25

# legs and joints
LEG_TOP_WIDTH = 3.25
LEG_FOOT_WIDTH = 1.75
APRON_HEIGHT = 3.0
HOUSING_FROM_OUTER = 0.375
HOUSING_DEPTH = 0.75
FIT_CLEARANCE = 0.005         # added to the housing's width
LAP_LENGTH = 1.75
SIDE_APRON_INSET = 1.375      # side aprons' outer faces in from each end of the top
OPEN_END = 0.2                # open pocket sides run this far past the leg's edge
BIT_DIAMETER = 0.25

# top attachment
GROOVE_WIDTH = 0.25
GROOVE_DEPTH = 0.3125
GROOVE_TOP = 0.375            # the groove's upper wall below the apron's top edge
GROOVE_STOP = 0.5             # grooves end this far from a joint or dowel hole
DOWEL_DIAMETER = 0.3125
DOWEL_LENGTH = 1.5
DOWEL_APART = 2.0             # the two dowels at the middle of each long apron
CHERRY_OVER_DOWEL = 0.25      # left above each dowel hole in the top
DOWEL_GLUE_ROOM = 1 / 16      # the two holes together are this much deeper than the dowel is long
COUPON = (3.0, 1.75)

# sheets and machining
WORK_AREA = (33.0, 33.0)      # Shapeoko Pro XXL
EDGE = 0.125                  # parts in from the stock's edges
PLY_GAP = 0.25
LVL_GAP = 0.4
FIT_TEST_STOCK = (6.0, 4.0)
FIT_TEST_SLACK = 0.1          # test pockets are this much longer than the coupon
FIT_TEST_GAP = 0.75           # between the two test pockets
CLEARANCE_OFFSET = 0.125
ROUGH_OFFSET = 0.02
THROUGH = 0.02                # through-cuts go this far into the spoilboard
FLUTE_MARGIN = 0.1
MIN_COLLET_NUT_CLEARANCE = 0.15

# rule limits
MIN_TOP_OVER_LEG = 0.5
MAX_OVERHANG = 3.5
MIN_TIP_LOAD = 50.0           # lb
HEIGHT_TOLERANCE = 1 / 32
MIN_DOWEL_IN_TOP = 0.375
MIN_PLY_BESIDE_DOWEL = 0.15
DENSITY = {"cherry": 35.0, "lvl": 38.0, "plywood": 43.0}  # lb/ft³
```

- [ ] **Step 5: Write `table/top.py`**

The sweep is sampled at 400 points. The rounded corners come from opening the raw outline
(`buffer(-R).buffer(R)`), once per radius, keeping each radius's half and the square back half.
The curve itself is unaffected: its tightest radius is about 120".

```python
"""The cherry top's outline: the sweep along the front edge, rounded front corners, square back."""
from __future__ import annotations

import math

from shapely.geometry import Polygon, box

from table import spec

SAMPLES = 400


def top_size() -> tuple[float, float]:
    """Finished width and depth: the glue-up less the trim on every side."""
    return spec.TOP_WIDTH - 2 * spec.TOP_TRIM, spec.TOP_DEPTH - 2 * spec.TOP_TRIM


def front_edge_y(x: float) -> float:
    """How far the front edge sits behind its deepest point, x along from the left end."""
    w, _ = top_size()
    return spec.SWEEP_DROP * (1 - math.sin(math.pi / 2 * min(x / (spec.SWEEP_FLAT_FROM * w), 1.0)))


def top_outline() -> Polygon:
    w, d = top_size()
    front = [(w * i / SAMPLES, front_edge_y(w * i / SAMPLES)) for i in range(SAMPLES + 1)]
    raw = Polygon(front + [(w, d), (0.0, d)])
    left = raw.buffer(-spec.RADIUS_LEFT, quad_segs=32).buffer(spec.RADIUS_LEFT, quad_segs=32)
    right = raw.buffer(-spec.RADIUS_RIGHT, quad_segs=32).buffer(spec.RADIUS_RIGHT, quad_segs=32)
    shape = (left.intersection(box(0, 0, w / 2, d))
             .union(right.intersection(box(w / 2, 0, w, d)))
             .union(box(0, d / 2, w, d)))
    return Polygon(shape.buffer(0).exterior)
```

- [ ] **Step 6: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `8 passed`

- [ ] **Step 7: Commit**

```bash
git add projects/kitchen-side-table/pytest.ini projects/kitchen-side-table/table projects/kitchen-side-table/tests
git commit -m "Add the kitchen table's spec values and top outline"
```

---

### Task 2: The flared legs and their pockets

**Files:**
- Create: `projects/kitchen-side-table/table/legs.py`
- Test: `projects/kitchen-side-table/tests/test_legs.py`

**Interfaces:**
- Consumes: `table.spec`; `table.top.top_size()`.
- Produces:
  - `LEG_NAMES = ("front-left", "front-right", "back-left", "back-right")`, and
    `FLARE_RIGHT = {"front-right", "back-left"}`.
  - `@dataclass(frozen=True) Leg(name: str, outline: Polygon, housing: Polygon, lap: Polygon)`, in
    leg coordinates: u across the leg, to the right as seen from the inside face, 0 at the outer
    edge; v along the leg from the foot. Flare-left legs have u ≤ 0.
  - `leg_length() -> float`, `leg_width(v: float) -> float`, `housing_width() -> float`,
    `inside_faces_apart() -> float`.
  - `dogbone(corner: tuple[float, float], into: tuple[int, int]) -> Polygon`.
  - `make_leg(name: str) -> Leg`, `make_legs() -> list[Leg]` (in `LEG_NAMES` order).
  - `closed_pocket(width: float, height: float) -> Polygon` and
    `fit_test_pockets() -> tuple[Polygon, Polygon]` (housing, lap), each with its core rectangle
    from (0, 0).

Handedness: standing behind the table and looking at the front-left leg's inside face, the
table's middle is on your left, so the front-left and back-right legs flare to the left as seen
from the inside face. The housing and lap run `OPEN_END` (0.2) past the leg's top, and the lap
also past its inner edge, so the bit clears the open sides. Each closed inside corner gets a
dogbone.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_legs.py`:

```python
import pytest
from shapely.geometry import Point, box

from table import spec
from table.legs import (dogbone, fit_test_pockets, housing_width, inside_faces_apart, leg_length, leg_width,
                        make_leg, make_legs)


def test_the_legs_are_31_25_long_so_the_table_is_32_tall():
    assert leg_length() == pytest.approx(31.25)


def test_a_leg_is_1_75_wide_at_the_foot_and_flares_to_3_25_at_the_aprons():
    assert leg_width(0.0) == pytest.approx(1.75)
    assert leg_width(28.25) == pytest.approx(3.25)
    assert leg_width(31.25) == pytest.approx(3.25)
    widths = [leg_width(28.25 * i / 50) for i in range(51)]
    assert widths == sorted(widths)


def test_the_front_left_and_back_right_legs_flare_to_the_left_seen_from_the_inside_face():
    assert make_leg("front-left").outline.bounds == pytest.approx((-3.25, 0.0, 0.0, 31.25))
    assert make_leg("back-right").outline.bounds == pytest.approx((-3.25, 0.0, 0.0, 31.25))
    assert make_leg("front-right").outline.bounds == pytest.approx((0.0, 0.0, 3.25, 31.25))
    assert make_leg("back-left").outline.bounds == pytest.approx((0.0, 0.0, 3.25, 31.25))


def test_the_housing_is_the_plywood_plus_clearance_wide_and_open_at_the_top():
    leg = make_leg("front-right")
    assert housing_width() == pytest.approx(0.728)
    assert leg.housing.contains(box(0.375, 28.25, 1.103, 31.25))
    assert leg.housing.bounds[3] == pytest.approx(31.25 + spec.OPEN_END)


def test_the_lap_is_open_at_the_inner_edge_and_the_top():
    leg = make_leg("front-right")
    assert leg.lap.contains(box(1.5, 28.25, 3.25, 31.25))
    assert leg.lap.bounds[2] == pytest.approx(3.25 + spec.OPEN_END)
    assert leg.lap.bounds[3] == pytest.approx(31.25 + spec.OPEN_END)


def test_a_dogbone_lets_the_bit_reach_right_into_a_square_corner():
    r = spec.BIT_DIAMETER / 2
    with_dogbone = box(0, 0, 1, 1).union(dogbone((0, 0), (1, 1)))
    without = box(0, 0, 1, 1)
    corner = Point(0.002, 0.002)
    assert with_dogbone.buffer(-r, quad_segs=32).buffer(r, quad_segs=32).contains(corner)
    assert not without.buffer(-r, quad_segs=32).buffer(r, quad_segs=32).contains(corner)


def test_there_are_four_legs_named_for_their_corners():
    assert [leg.name for leg in make_legs()] == ["front-left", "front-right", "back-left", "back-right"]


def test_the_legs_inside_faces_are_13_678_apart_front_to_back():
    assert inside_faces_apart() == pytest.approx(13.678)


def test_the_fit_test_pockets_take_the_coupon():
    housing, lap = fit_test_pockets()
    assert housing.contains(box(0, 0, 0.723, 1.75))
    assert lap.contains(box(0, 0, 3.0, 1.75))
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_legs.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.legs'`

- [ ] **Step 3: Write `table/legs.py`**

```python
"""The four flared LVL legs and their pockets, seen from each leg's inside face.

Leg coordinates: u across the leg, to the right as seen from the inside face, 0 at the outer edge;
v along the leg from the foot.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.affinity import scale
from shapely.geometry import Point, Polygon, box

from table import spec
from table.top import top_size

LEG_NAMES = ("front-left", "front-right", "back-left", "back-right")
FLARE_RIGHT = {"front-right", "back-left"}  # seen from the inside face; the other two are mirrored
SAMPLES = 160


@dataclass(frozen=True)
class Leg:
    name: str
    outline: Polygon
    housing: Polygon  # takes the side apron, HOUSING_DEPTH deep
    lap: Polygon      # takes the long apron, as deep as the plywood is thick


def leg_length() -> float:
    return spec.HEIGHT - spec.TOP_THICKNESS


def leg_width(v: float) -> float:
    flare_top = leg_length() - spec.APRON_HEIGHT
    if v >= flare_top:
        return spec.LEG_TOP_WIDTH
    return spec.LEG_FOOT_WIDTH + (spec.LEG_TOP_WIDTH - spec.LEG_FOOT_WIDTH) * (v / flare_top) ** 3


def housing_width() -> float:
    return spec.PLY_THICKNESS + spec.FIT_CLEARANCE


def inside_faces_apart() -> float:
    """Front to back, between the front legs' inside faces and the back legs'."""
    _, d = top_size()
    return d - spec.BACK_LEG_FROM_WALL - spec.FRONT_LEG_BEHIND_EDGE - 2 * spec.LVL_THICKNESS


def dogbone(corner: tuple[float, float], into: tuple[int, int]) -> Polygon:
    """A bit-radius circle through a square inside corner, centered on its bisector, into the pocket."""
    r = spec.BIT_DIAMETER / 2
    step = r / math.sqrt(2)
    return Point(corner[0] + into[0] * step, corner[1] + into[1] * step).buffer(r, quad_segs=32)


def make_leg(name: str) -> Leg:
    length = leg_length()
    flare_top = length - spec.APRON_HEIGHT
    vs = [flare_top * i / SAMPLES for i in range(SAMPLES + 1)] + [length]
    outline = Polygon([(0.0, v) for v in vs] + [(leg_width(v), v) for v in reversed(vs)])
    h0, h1 = spec.HOUSING_FROM_OUTER, spec.HOUSING_FROM_OUTER + housing_width()
    top = length + spec.OPEN_END
    housing = (box(h0, flare_top, h1, top)
               .union(dogbone((h0, flare_top), (1, 1)))
               .union(dogbone((h1, flare_top), (-1, 1))))
    l0 = spec.LEG_TOP_WIDTH - spec.LAP_LENGTH
    lap = box(l0, flare_top, spec.LEG_TOP_WIDTH + spec.OPEN_END, top).union(dogbone((l0, flare_top), (1, 1)))
    if name not in FLARE_RIGHT:
        outline, housing, lap = (scale(g, -1, 1, origin=(0, 0)) for g in (outline, housing, lap))
    return Leg(name, outline, housing, lap)


def make_legs() -> list[Leg]:
    return [make_leg(name) for name in LEG_NAMES]


def closed_pocket(width: float, height: float) -> Polygon:
    """A rectangle from (0, 0) with a dogbone in every corner."""
    pocket = box(0, 0, width, height)
    corners = (((0, 0), (1, 1)), ((width, 0), (-1, 1)), ((width, height), (-1, -1)), ((0, height), (1, -1)))
    for corner, into in corners:
        pocket = pocket.union(dogbone(corner, into))
    return pocket


def fit_test_pockets() -> tuple[Polygon, Polygon]:
    """A housing and a lap as cut in the legs, closed all round, each a little longer than the coupon."""
    length, width = spec.COUPON
    return (closed_pocket(housing_width(), width + spec.FIT_TEST_SLACK),
            closed_pocket(length + spec.FIT_TEST_SLACK, width + spec.FIT_TEST_SLACK))
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_legs.py -q`
Expected: `9 passed`

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `17 passed`

- [ ] **Step 6: Commit**

```bash
git add projects/kitchen-side-table/table/legs.py projects/kitchen-side-table/tests/test_legs.py
git commit -m "Add the kitchen table's flared legs and their pockets"
```

---

### Task 3: The aprons, grooves, dowel holes and coupon

**Files:**
- Create: `projects/kitchen-side-table/table/aprons.py`
- Test: `projects/kitchen-side-table/tests/test_aprons.py`

**Interfaces:**
- Consumes: `table.spec`; `table.top.top_size()`; `table.legs.inside_faces_apart()`.
- Produces:
  - `@dataclass(frozen=True) PlyPart(name: str, outline: Polygon, grooves: tuple[LineString, ...] = (),
    joints: tuple[Polygon, ...] = (), dowels: tuple[float, ...] = ())`, in part coordinates: a along
    the length, to the right as seen from the inside face; b up from the bottom edge.
  - `long_apron_length() -> float`, `side_apron_length() -> float`.
  - `dowel_depths() -> tuple[float, float]` (into the top, into the apron) and
    `dowel_hole(a: float) -> Polygon` (the hole as it shows on the inside face).
  - `make_aprons() -> list[PlyPart]`, named `"front apron"`, `"back apron"`, `"left apron"`,
    `"right apron"`, in that order.
  - `make_coupon() -> PlyPart`, named `"coupon"`.

Each groove is a centerline, 0.5 below the apron's top edge. The cut slot is the centerline
buffered by the bit's radius, so each end stops `GROOVE_STOP` + radius short of the joint or the
pair of dowel holes. The long aprons' dowel holes reach down through the groove's height, so their
grooves split in two around them.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_aprons.py`:

```python
import pytest

from table import spec
from table.aprons import dowel_depths, long_apron_length, make_aprons, make_coupon, side_apron_length


def _aprons():
    return {a.name: a for a in make_aprons()}


def test_the_long_aprons_are_26_75_and_the_side_aprons_15_178():
    assert long_apron_length() == pytest.approx(26.75)
    assert side_apron_length() == pytest.approx(15.178)
    assert _aprons()["front apron"].outline.bounds == pytest.approx((0, 0, 26.75, 3.0))
    assert _aprons()["left apron"].outline.bounds == pytest.approx((0, 0, 15.178, 3.0))


def test_the_dowel_holes_sit_an_inch_either_side_of_each_long_aprons_middle():
    aprons = _aprons()
    assert aprons["front apron"].dowels == pytest.approx((12.375, 14.375))
    assert aprons["back apron"].dowels == pytest.approx((12.375, 14.375))
    assert aprons["left apron"].dowels == () and aprons["right apron"].dowels == ()


def test_the_long_aprons_grooves_split_around_the_dowels():
    grooves = [list(g.coords) for g in _aprons()["front apron"].grooves]
    assert grooves == [pytest.approx([(2.375, 2.5), (11.59375, 2.5)]), pytest.approx([(15.15625, 2.5), (24.375, 2.5)])]


def test_the_side_aprons_groove_stops_half_an_inch_short_of_the_housings():
    grooves = [list(g.coords) for g in _aprons()["left apron"].grooves]
    assert grooves == [pytest.approx([(1.375, 2.5), (13.803, 2.5)])]


def test_each_joint_is_the_end_that_goes_into_a_leg():
    aprons = _aprons()
    assert [j.bounds for j in aprons["front apron"].joints] == [pytest.approx((0, 0, 1.75, 3)), pytest.approx((25.0, 0, 26.75, 3))]
    assert [j.bounds for j in aprons["left apron"].joints] == [pytest.approx((0, 0, 0.75, 3)), pytest.approx((14.428, 0, 15.178, 3))]


def test_the_coupon_is_3_by_1_75():
    assert make_coupon().outline.bounds == pytest.approx((0, 0, 3.0, 1.75))


def test_the_dowel_holes_leave_a_quarter_inch_of_cherry_and_room_for_glue():
    assert dowel_depths() == pytest.approx((0.5, 1.0625))


def test_the_dowel_holes_follow_a_top_sanded_thinner(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.72)
    assert dowel_depths() == pytest.approx((0.47, 1.0925))
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_aprons.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.aprons'`

- [ ] **Step 3: Write `table/aprons.py`**

```python
"""The plywood parts: four aprons with their clip grooves and dowel holes, and the fit-test coupon.

Part coordinates: a along the length, to the right as seen from the inside face; b up from the
bottom edge.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Polygon, box

from table import spec
from table.legs import inside_faces_apart
from table.top import top_size

@dataclass(frozen=True)
class PlyPart:
    name: str
    outline: Polygon
    grooves: tuple[LineString, ...] = ()  # centerlines, cut GROOVE_DEPTH deep with the bit
    joints: tuple[Polygon, ...] = ()      # the ends that go into a leg
    dowels: tuple[float, ...] = ()        # a of each dowel hole in the top edge


def long_apron_length() -> float:
    w, _ = top_size()
    return w - 2 * (spec.LEG_INSET + spec.LEG_TOP_WIDTH - spec.LAP_LENGTH)


def side_apron_length() -> float:
    return inside_faces_apart() + 2 * spec.HOUSING_DEPTH


def dowel_depths() -> tuple[float, float]:
    """How deep to drill for each dowel: into the top's underside, and into the apron's top edge."""
    in_top = spec.TOP_THICKNESS - spec.CHERRY_OVER_DOWEL
    return in_top, spec.DOWEL_LENGTH + spec.DOWEL_GLUE_ROOM - in_top


def dowel_hole(a: float) -> Polygon:
    """A dowel hole in the top edge, as it shows on the inside face."""
    r = spec.DOWEL_DIAMETER / 2
    return box(a - r, spec.APRON_HEIGHT - dowel_depths()[1], a + r, spec.APRON_HEIGHT)


def _grooves(length: float, joint: float, dowels: tuple[float, ...]) -> tuple[LineString, ...]:
    r = spec.GROOVE_WIDTH / 2
    b = spec.APRON_HEIGHT - spec.GROOVE_TOP - r
    blocked = [(0.0, joint), (length - joint, length)]
    if dowels:
        blocked.append((min(dowels) - spec.DOWEL_DIAMETER / 2, max(dowels) + spec.DOWEL_DIAMETER / 2))
    blocked.sort()
    return tuple(LineString([(a0 + spec.GROOVE_STOP + r, b), (a1 - spec.GROOVE_STOP - r, b)])
                 for (_, a0), (a1, _) in zip(blocked, blocked[1:]))


def _apron(name: str, length: float, joint: float, dowels: tuple[float, ...] = ()) -> PlyPart:
    h = spec.APRON_HEIGHT
    return PlyPart(name, box(0, 0, length, h), _grooves(length, joint, dowels),
                   (box(0, 0, joint, h), box(length - joint, 0, length, h)), dowels)


def make_aprons() -> list[PlyPart]:
    long, side = long_apron_length(), side_apron_length()
    dowels = (long / 2 - spec.DOWEL_APART / 2, long / 2 + spec.DOWEL_APART / 2)
    return [_apron("front apron", long, spec.LAP_LENGTH, dowels),
            _apron("back apron", long, spec.LAP_LENGTH, dowels),
            _apron("left apron", side, spec.HOUSING_DEPTH),
            _apron("right apron", side, spec.HOUSING_DEPTH)]


def make_coupon() -> PlyPart:
    return PlyPart("coupon", box(0, 0, *spec.COUPON))
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_aprons.py -q`
Expected: `8 passed`

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `25 passed`

- [ ] **Step 6: Commit**

```bash
git add projects/kitchen-side-table/table/aprons.py projects/kitchen-side-table/tests/test_aprons.py
git commit -m "Add the kitchen table's aprons, clip grooves, dowel holes and coupon"
```

---

### Task 4: Every part placed in table coordinates

**Files:**
- Create: `projects/kitchen-side-table/table/frame.py`
- Create: `projects/kitchen-side-table/tests/conftest.py`
- Test: `projects/kitchen-side-table/tests/test_frame.py`

**Interfaces:**
- Consumes: `table.spec`; `top_outline()`, `top_size()`; `Leg`, `make_legs()`, `leg_length()`,
  `inside_faces_apart()`; `PlyPart`, `make_aprons()`, `long_apron_length()`.
- Produces:
  - `Vec = tuple[float, float, float]`.
  - `@dataclass(frozen=True) Placed(name, material, outline, thickness, pockets, origin, a_axis, b_axis)`.
    `material` is `"cherry"`, `"lvl"` or `"plywood"`; `pockets` is a tuple of `(Polygon, depth)`.
    It has the property `normal -> Vec` (a_axis × b_axis, out of the face) and the methods
    `to_table(a, b, depth=0.0) -> Vec` and `to_face(point: Vec) -> Vec` (returns a, b, depth).
  - `@dataclass(frozen=True) Table(top: Polygon, legs: tuple[Leg, ...], aprons: tuple[PlyPart, ...], placed: tuple[Placed, ...])`,
    with `placed` in the order top, the four legs in `LEG_NAMES` order, then the four aprons.
  - `build_table() -> Table`, `front_inside_y() -> float`, `back_inside_y() -> float`.
  - `dowel_spots(table) -> list[Vec]`.
  - `weight_and_center_y(table) -> tuple[float, float]` (lb, y).
  - `extent(part: Placed) -> tuple[Vec, Vec]` (lowest corner, highest corner).
  - `front_leg_face_y(table) -> float` and `tip_load(table) -> float` (lb).
  - Test fixture `table` (session scope) in `tests/conftest.py`.

Each part's face is the one cut first: the top's show face, and the legs' and aprons' inside faces.
The material lies behind the face, so each placement is a proper rotation. The front parts' inside
faces look toward the wall, so a viewer looking at one has −x on their right, and those parts get
`a_axis = (-1, 0, 0)`.

- [ ] **Step 1: Write the shared fixture**

`projects/kitchen-side-table/tests/conftest.py`. Task 5 adds a `sheets` fixture to it.

```python
import pytest


@pytest.fixture(scope="session")
def table():
    from table.frame import build_table

    return build_table()
```

- [ ] **Step 2: Write the failing tests**

`projects/kitchen-side-table/tests/test_frame.py`:

```python
import pytest

from table.frame import back_inside_y, dowel_spots, extent, front_inside_y, tip_load, weight_and_center_y


def _placed(table):
    return {p.name: p for p in table.placed}


def test_the_legs_stand_an_inch_in_from_each_end_with_the_flare_toward_the_middle(table):
    for name, part in _placed(table).items():
        if part.material != "lvl":
            continue
        lo, hi = extent(part)
        outer = 1.0 if name.endswith("left") else 30.75
        assert (lo[0], hi[0]) == pytest.approx((1.0, 4.25) if name.endswith("left") else (27.5, 30.75))
        foot = [part.to_table(a, b)[0] for a, b in part.outline.exterior.coords if b == 0.0]
        assert min(abs(x - outer) for x in foot) == pytest.approx(0.0)
        assert max(abs(x - outer) for x in foot) == pytest.approx(1.75)


def test_the_front_legs_stand_3_5_behind_the_front_edge_and_the_back_legs_3_from_the_wall(table):
    placed = _placed(table)
    for name in ("front-left", "front-right"):
        lo, hi = extent(placed[name])
        assert (lo[1], hi[1]) == pytest.approx((3.5, 5.286))
    for name in ("back-left", "back-right"):
        lo, hi = extent(placed[name])
        assert (lo[1], hi[1]) == pytest.approx((18.964, 20.75))


def test_every_inside_face_faces_the_middle_of_the_table(table):
    middle = (31.75 / 2, 23.75 / 2)
    for part in (p for p in table.placed if p.name != "top"):
        to_middle = (middle[0] - part.origin[0], middle[1] - part.origin[1])
        assert part.normal[0] * to_middle[0] + part.normal[1] * to_middle[1] > 0, part.name


def test_the_long_aprons_are_flush_with_the_legs_inside_faces(table):
    placed = _placed(table)
    assert extent(placed["front apron"])[1][1] == pytest.approx(front_inside_y())
    assert extent(placed["back apron"])[0][1] == pytest.approx(back_inside_y())


def test_the_aprons_are_flush_with_the_leg_tops_under_the_top(table):
    placed = _placed(table)
    for name in ("front apron", "back apron", "left apron", "right apron"):
        lo, hi = extent(placed[name])
        assert (lo[2], hi[2]) == pytest.approx((28.25, 31.25))
    lo, hi = extent(placed["top"])
    assert (lo[2], hi[2]) == pytest.approx((31.25, 32.0))


def test_the_side_aprons_outer_faces_are_1_375_in_from_each_end(table):
    placed = _placed(table)
    assert extent(placed["left apron"])[0][0] == pytest.approx(1.375)
    assert extent(placed["right apron"])[1][0] == pytest.approx(31.75 - 1.375)


def test_to_face_undoes_to_table(table):
    for part in table.placed:
        assert part.to_face(part.to_table(1.25, 2.5, 0.375)) == pytest.approx((1.25, 2.5, 0.375))


def test_the_dowels_sit_at_the_middle_of_the_long_aprons_where_they_meet_the_top(table):
    spots = sorted(dowel_spots(table))
    assert [x for x, _, _ in spots] == pytest.approx([14.875, 14.875, 16.875, 16.875])
    assert sorted({round(y, 4) for _, y, _ in spots}) == pytest.approx([front_inside_y() - 0.3615, back_inside_y() + 0.3615])
    assert all(z == pytest.approx(31.25) for _, _, z in spots)


def test_the_empty_table_weighs_about_26_lb_centered_about_12_in_back(table):
    weight, center_y = weight_and_center_y(table)
    assert weight == pytest.approx(26.0, abs=0.5)
    assert center_y == pytest.approx(12.16, abs=0.1)


def test_it_takes_about_64_lb_on_the_front_edge_to_tip_it(table):
    assert tip_load(table) == pytest.approx(64.4, abs=1.0)
```

- [ ] **Step 3: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_frame.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.frame'`

- [ ] **Step 4: Write `table/frame.py`**

```python
"""Every part placed in table coordinates, and the table's weight and balance."""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Polygon

from table import spec
from table.aprons import PlyPart, long_apron_length, make_aprons
from table.legs import Leg, inside_faces_apart, leg_length, make_legs
from table.top import top_outline, top_size

Vec = tuple[float, float, float]


@dataclass(frozen=True)
class Placed:
    """A flat part in table coordinates.

    The part's face coordinates (a, b) run along a_axis and b_axis from origin. That face is the one
    up on the machine; its outward normal is a_axis × b_axis, and the material lies behind it.
    """
    name: str
    material: str                                # "cherry", "lvl" or "plywood"
    outline: Polygon
    thickness: float
    pockets: tuple[tuple[Polygon, float], ...]   # (shape, depth), cut into the face
    origin: Vec
    a_axis: Vec
    b_axis: Vec

    @property
    def normal(self) -> Vec:
        (ax, ay, az), (bx, by, bz) = self.a_axis, self.b_axis
        return (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)

    def to_table(self, a: float, b: float, depth: float = 0.0) -> Vec:
        """Face coordinates, and a depth behind the face, to table coordinates."""
        return tuple(o + a * u + b * v - depth * n
                     for o, u, v, n in zip(self.origin, self.a_axis, self.b_axis, self.normal))

    def to_face(self, point: Vec) -> Vec:
        """Table coordinates to (a, b, depth behind the face)."""
        rel = [p - o for p, o in zip(point, self.origin)]
        dot = lambda axis: sum(r * c for r, c in zip(rel, axis))  # noqa: E731
        return dot(self.a_axis), dot(self.b_axis), -dot(self.normal)


@dataclass(frozen=True)
class Table:
    top: Polygon
    legs: tuple[Leg, ...]
    aprons: tuple[PlyPart, ...]
    placed: tuple[Placed, ...]


def front_inside_y() -> float:
    """The front legs' inside faces, which the front apron is flush with."""
    return spec.FRONT_LEG_BEHIND_EDGE + spec.LVL_THICKNESS


def back_inside_y() -> float:
    return front_inside_y() + inside_faces_apart()


def _place_leg(leg: Leg) -> Placed:
    w, _ = top_size()
    x = spec.LEG_INSET if leg.name.endswith("left") else w - spec.LEG_INSET
    if leg.name.startswith("front"):  # inside face toward the wall, seen from behind
        origin, a_axis = (x, front_inside_y(), 0.0), (-1.0, 0.0, 0.0)
    else:                             # inside face toward the room
        origin, a_axis = (x, back_inside_y(), 0.0), (1.0, 0.0, 0.0)
    pockets = ((leg.housing, spec.HOUSING_DEPTH), (leg.lap, spec.PLY_THICKNESS))
    return Placed(leg.name, "lvl", leg.outline, spec.LVL_THICKNESS, pockets, origin, a_axis, (0.0, 0.0, 1.0))


def _place_apron(part: PlyPart) -> Placed:
    w, _ = top_size()
    z = leg_length() - spec.APRON_HEIGHT
    lap_x = spec.LEG_INSET + spec.LEG_TOP_WIDTH - spec.LAP_LENGTH
    side_y0 = front_inside_y() - spec.HOUSING_DEPTH
    side_y1 = back_inside_y() + spec.HOUSING_DEPTH
    side_x = spec.SIDE_APRON_INSET + spec.PLY_THICKNESS  # the side aprons' inside faces, from each end
    origin, a_axis = {
        "front apron": ((lap_x + long_apron_length(), front_inside_y(), z), (-1.0, 0.0, 0.0)),
        "back apron": ((lap_x, back_inside_y(), z), (1.0, 0.0, 0.0)),
        "left apron": ((side_x, side_y0, z), (0.0, 1.0, 0.0)),
        "right apron": ((w - side_x, side_y1, z), (0.0, -1.0, 0.0)),
    }[part.name]
    pockets = tuple((g.buffer(spec.GROOVE_WIDTH / 2), spec.GROOVE_DEPTH) for g in part.grooves)
    return Placed(part.name, "plywood", part.outline, spec.PLY_THICKNESS, pockets, origin, a_axis, (0.0, 0.0, 1.0))


def build_table() -> Table:
    outline = top_outline()
    legs, aprons = tuple(make_legs()), tuple(make_aprons())
    top = Placed("top", "cherry", outline, spec.TOP_THICKNESS, (),
                 (0.0, 0.0, spec.HEIGHT), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    placed = (top, *(_place_leg(leg) for leg in legs), *(_place_apron(a) for a in aprons))
    return Table(outline, legs, aprons, placed)


def dowel_spots(table: Table) -> list[Vec]:
    """Where each dowel crosses the joint between apron and top, in table coordinates."""
    placed = {p.name: p for p in table.placed}
    return [placed[part.name].to_table(a, spec.APRON_HEIGHT, spec.PLY_THICKNESS / 2)
            for part in table.aprons for a in part.dowels]


def weight_and_center_y(table: Table) -> tuple[float, float]:
    """The empty table's weight in lb, and how far back from the front its weight is centered."""
    total = moment = 0.0
    for part in table.placed:
        volume = part.outline.area * part.thickness - sum(
            shape.intersection(part.outline).area * depth for shape, depth in part.pockets)
        pounds = volume / 1728 * spec.DENSITY[part.material]
        c = part.outline.centroid
        total += pounds
        moment += pounds * part.to_table(c.x, c.y, part.thickness / 2)[1]
    return total, moment / total


def extent(part: Placed) -> tuple[Vec, Vec]:
    """The part's lowest and highest corner in table coordinates (every part is square to the table)."""
    points = [part.to_table(a, b, depth) for a, b in part.outline.exterior.coords for depth in (0.0, part.thickness)]
    return tuple(min(p[i] for p in points) for i in range(3)), tuple(max(p[i] for p in points) for i in range(3))


def front_leg_face_y(table: Table) -> float:
    """The front of the front legs: the line the table would tip over."""
    return min(extent(p)[0][1] for p in table.placed if p.name.startswith("front-"))


def tip_load(table: Table) -> float:
    """The weight in lb on the front edge's deepest point that would tip the empty table forward."""
    weight, center_y = weight_and_center_y(table)
    axis = front_leg_face_y(table)
    return weight * (center_y - axis) / (axis - table.top.bounds[1])
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_frame.py -q`
Expected: `10 passed`

- [ ] **Step 6: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `35 passed`

- [ ] **Step 7: Commit**

```bash
git add projects/kitchen-side-table/table/frame.py projects/kitchen-side-table/tests/conftest.py projects/kitchen-side-table/tests/test_frame.py
git commit -m "Place the kitchen table's parts in table coordinates"
```

---

### Task 5: The four jobs on their stock

**Files:**
- Create: `projects/kitchen-side-table/table/sheets.py`
- Modify: `projects/kitchen-side-table/tests/conftest.py` (add the `sheets` fixture)
- Test: `projects/kitchen-side-table/tests/test_sheets.py`

**Interfaces:**
- Consumes: `table.spec`; `Table`; `Leg`, `fit_test_pockets()`, `housing_width()`, `leg_length()`;
  `PlyPart`, `make_coupon()`.
- Produces:
  - `@dataclass(frozen=True) SheetPart(name: str, outline: Polygon | None, pockets: tuple[tuple[str, Polygon], ...], grooves: tuple[LineString, ...] = ())`,
    where each pocket's str is its layer name, `"POCKET_HOUSING"` or `"POCKET_LAP"`.
  - `@dataclass(frozen=True) Sheet(name: str, title: str, stock: tuple[float, float], gap: float, parts: tuple[SheetPart, ...], lvl: bool = False)`.
  - `legs_sheet(table)`, `aprons_sheet(table)`, `fit_test_sheet()`, `top_sheet(table)`, and
    `make_sheets(table) -> list[Sheet]`, which returns them in job order: `aprons`, `fit_test`,
    `legs`, `top`.
  - `lvl_depths() -> dict[str, float]` with keys `"full"`, `"clearance"` and `"first_stage"`.
  - `lvl_spare(sheet: Sheet) -> float`.
  - Test fixture `sheets` (session scope): a dict of sheet name to `Sheet`, in job order.

The legs go on as two head-to-toe pairs: front-left with back-right, then front-right with
back-left. The lower leg of each pair is turned so its flare points up. The upper leg is turned a
further 180° and slid down, by bisection, until it is exactly `LVL_GAP` from the lower one.
Rotation keeps a ring's winding and a mirror would flip it, so
`test_the_legs_go_on_by_rotation_only_never_mirrored` compares windings.

- [ ] **Step 1: Add the `sheets` fixture**

Replace `projects/kitchen-side-table/tests/conftest.py` with:

```python
import pytest


@pytest.fixture(scope="session")
def table():
    from table.frame import build_table

    return build_table()


@pytest.fixture(scope="session")
def sheets(table):
    from table.sheets import make_sheets

    return {sheet.name: sheet for sheet in make_sheets(table)}
```

- [ ] **Step 2: Write the failing tests**

`projects/kitchen-side-table/tests/test_sheets.py`:

```python
import pytest

from table.legs import make_leg
from table.sheets import lvl_depths, lvl_spare


def test_there_are_four_jobs(sheets):
    assert list(sheets) == ["aprons", "fit_test", "legs", "top"]


def test_the_legs_nest_head_to_toe_in_two_pairs_of_one_handedness(sheets):
    parts = sheets["legs"].parts
    assert [p.name for p in parts] == ["front-left", "back-right", "front-right", "back-left"]
    for lower, upper in ((parts[0], parts[1]), (parts[2], parts[3])):
        assert lower.outline.distance(upper.outline) == pytest.approx(0.4, abs=1e-6)
        lower_top = dict(lower.pockets)["POCKET_HOUSING"].centroid.x
        upper_top = dict(upper.pockets)["POCKET_HOUSING"].centroid.x
        assert (lower_top > 16) != (upper_top > 16)  # one leg's top at each end
    assert parts[1].outline.distance(parts[2].outline) == pytest.approx(0.4, abs=1e-6)


def test_the_legs_go_on_by_rotation_only_never_mirrored(sheets):
    for part in sheets["legs"].parts:
        leg = make_leg(part.name)
        assert part.outline.area == pytest.approx(leg.outline.area)
        assert part.outline.exterior.is_ccw == leg.outline.exterior.is_ccw


def test_the_lvl_has_about_0_3_in_to_spare(sheets):
    assert lvl_spare(sheets["legs"]) == pytest.approx(0.296, abs=0.005)


def test_the_aprons_go_in_three_strips_with_the_coupon_above(sheets):
    bounds = {p.name: p.outline.bounds for p in sheets["aprons"].parts}
    assert bounds["back apron"] == pytest.approx((2.625, 0.125, 29.375, 3.125))
    assert bounds["front apron"] == pytest.approx((2.625, 3.375, 29.375, 6.375))
    assert bounds["left apron"][1] == pytest.approx(6.625) and bounds["right apron"][1] == pytest.approx(6.625)
    assert bounds["right apron"][0] - bounds["left apron"][2] == pytest.approx(0.25)
    assert bounds["coupon"] == pytest.approx((14.5, 9.875, 17.5, 11.625))


def test_the_grooves_go_on_with_their_aprons(sheets):
    back = next(p for p in sheets["aprons"].parts if p.name == "back apron")
    starts = [g.coords[0] for g in back.grooves]
    assert starts == [pytest.approx((2.625 + 2.375, 0.125 + 2.5)), pytest.approx((2.625 + 15.15625, 0.125 + 2.5))]


def test_the_top_sits_show_face_up_with_its_front_edge_toward_the_operator(sheets):
    outline = sheets["top"].parts[0].outline
    assert outline.bounds == pytest.approx((0.125, 0.125, 31.875, 23.875))
    left_front = min(y for x, y in outline.exterior.coords if x < 3.3)
    right_front = min(y for x, y in outline.exterior.coords if x > 28.8)
    assert left_front > right_front + 1.5


def test_the_fit_test_pockets_sit_side_by_side_on_the_scrap(sheets):
    pockets = dict(sheets["fit_test"].parts[0].pockets)
    housing, lap = pockets["POCKET_HOUSING"].bounds, pockets["POCKET_LAP"].bounds
    assert housing[2] < lap[0]
    assert 0 < housing[0] and lap[2] < 6.0 and 0 < housing[1] and housing[3] < 4.0


def test_the_lvl_cut_depths_follow_the_flute(sheets):
    assert lvl_depths() == pytest.approx({"full": 1.806, "clearance": 0.506, "first_stage": 1.3})
```

- [ ] **Step 3: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_sheets.py -q`
Expected: errors, `ModuleNotFoundError: No module named 'table.sheets'`

- [ ] **Step 4: Write `table/sheets.py`**

```python
"""The four jobs: each part on its stock, in sheet coordinates (origin at the stock's lower-left, seen from above)."""
from __future__ import annotations

from dataclasses import dataclass

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon

from table import spec
from table.aprons import PlyPart, make_coupon
from table.frame import Table
from table.legs import Leg, fit_test_pockets, housing_width, leg_length

BISECT_STEPS = 60


@dataclass(frozen=True)
class SheetPart:
    name: str
    outline: Polygon | None                     # None for the fit test, whose scrap stays whole
    pockets: tuple[tuple[str, Polygon], ...]    # (layer, shape)
    grooves: tuple[LineString, ...] = ()


@dataclass(frozen=True)
class Sheet:
    name: str
    title: str
    stock: tuple[float, float]
    gap: float
    parts: tuple[SheetPart, ...]
    lvl: bool = False                           # adds the clearance and rough passes


def _moved(geom, angle: float, dx: float, dy: float):
    return translate(rotate(geom, angle, origin=(0, 0)), dx, dy)


def _leg_part(leg: Leg, angle: float, dx: float, dy: float) -> SheetPart:
    return SheetPart(leg.name, _moved(leg.outline, angle, dx, dy),
                     (("POCKET_HOUSING", _moved(leg.housing, angle, dx, dy)),
                      ("POCKET_LAP", _moved(leg.lap, angle, dx, dy))))


def _ply_part(part: PlyPart, dx: float, dy: float) -> SheetPart:
    return SheetPart(part.name, translate(part.outline, dx, dy), (),
                     tuple(translate(g, dx, dy) for g in part.grooves))


def _lowest(leg: Leg, angle: float, x0: float, y0: float) -> SheetPart:
    """The leg turned by angle, its lower-left corner at (x0, y0)."""
    minx, miny, _, _ = rotate(leg.outline, angle, origin=(0, 0)).bounds
    return _leg_part(leg, angle, x0 - minx, y0 - miny)


def _stack(below: SheetPart, leg: Leg, angle: float, x0: float, gap: float) -> SheetPart:
    """The leg turned by angle, slid down onto the part below until they are exactly gap apart."""
    turned = rotate(leg.outline, angle, origin=(0, 0))
    minx, miny, _, _ = turned.bounds
    lo, hi = below.outline.bounds[1], below.outline.bounds[3] + gap
    for _ in range(BISECT_STEPS):
        mid = (lo + hi) / 2
        if translate(turned, x0 - minx, mid - miny).distance(below.outline) < gap:
            lo = mid
        else:
            hi = mid
    return _leg_part(leg, angle, x0 - minx, hi - miny)


def legs_sheet(table: Table) -> Sheet:
    """Two head-to-toe pairs of one handedness each, inside faces up, centered along the board."""
    legs = {leg.name: leg for leg in table.legs}
    x0 = (spec.LVL_LENGTH - leg_length()) / 2
    parts: list[SheetPart] = []
    y = spec.EDGE
    for lower, upper in (("front-left", "back-right"), ("front-right", "back-left")):
        angle = 90.0 if lower in ("front-right", "back-left") else -90.0  # flare up, outer edge down
        first = _lowest(legs[lower], angle, x0, y)
        second = _stack(first, legs[upper], angle + 180.0, x0, spec.LVL_GAP)
        parts += [first, second]
        y = second.outline.bounds[3] + spec.LVL_GAP
    return Sheet("legs", "Job 3: LVL legs", (spec.LVL_LENGTH, spec.LVL_WIDTH), spec.LVL_GAP, tuple(parts), lvl=True)


def aprons_sheet(table: Table) -> Sheet:
    """Three 3" strips (back, front, both sides end to end), then the coupon, inside faces up."""
    aprons = {a.name: a for a in table.aprons}
    row = spec.APRON_HEIGHT + spec.PLY_GAP
    parts = []
    for i, name in enumerate(("back apron", "front apron")):
        length = aprons[name].outline.bounds[2]
        parts.append(_ply_part(aprons[name], (spec.PLY_LENGTH - length) / 2, spec.EDGE + i * row))
    side = aprons["left apron"].outline.bounds[2]
    x = (spec.PLY_LENGTH - 2 * side - spec.PLY_GAP) / 2
    parts.append(_ply_part(aprons["left apron"], x, spec.EDGE + 2 * row))
    parts.append(_ply_part(aprons["right apron"], x + side + spec.PLY_GAP, spec.EDGE + 2 * row))
    coupon = make_coupon()
    parts.append(_ply_part(coupon, (spec.PLY_LENGTH - spec.COUPON[0]) / 2, spec.EDGE + 3 * row))
    return Sheet("aprons", "Job 1: plywood aprons", (spec.PLY_LENGTH, spec.PLY_WIDTH), spec.PLY_GAP, tuple(parts))


def fit_test_sheet() -> Sheet:
    """The two test pockets side by side, centered on the scrap."""
    housing, lap = fit_test_pockets()
    w, h = spec.FIT_TEST_STOCK
    length = spec.COUPON[1] + spec.FIT_TEST_SLACK
    lap_width = spec.COUPON[0] + spec.FIT_TEST_SLACK
    x = (w - housing_width() - spec.FIT_TEST_GAP - lap_width) / 2
    y = (h - length) / 2
    pockets = (("POCKET_HOUSING", translate(housing, x, y)),
               ("POCKET_LAP", translate(lap, x + housing_width() + spec.FIT_TEST_GAP, y)))
    return Sheet("fit_test", "Job 2: fit test", (w, h), spec.FIT_TEST_GAP, (SheetPart("fit test", None, pockets),))


def top_sheet(table: Table) -> Sheet:
    """The show face up and the front edge toward the operator, so the shallow end is on the left."""
    part = SheetPart("top", translate(table.top, spec.TOP_TRIM, spec.TOP_TRIM), ())
    return Sheet("top", "Job 4: cherry top", (spec.TOP_WIDTH, spec.TOP_DEPTH), 0.0, (part,))


def make_sheets(table: Table) -> list[Sheet]:
    return [aprons_sheet(table), fit_test_sheet(), legs_sheet(table), top_sheet(table)]


def lvl_depths() -> dict[str, float]:
    """The LVL's cut depths: full, the clearance pass, and the first finishing stage."""
    full = spec.LVL_THICKNESS + spec.THROUGH
    return {"full": full,
            "clearance": full - spec.TWO_FLUTE_LENGTH + spec.FLUTE_MARGIN,
            "first_stage": spec.TWO_FLUTE_LENGTH - spec.FLUTE_MARGIN}


def lvl_spare(sheet: Sheet) -> float:
    """The LVL's width left over above the legs and their edge margin."""
    return spec.LVL_WIDTH - spec.EDGE - max(p.outline.bounds[3] for p in sheet.parts)
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_sheets.py -q`
Expected: `9 passed`

- [ ] **Step 6: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `44 passed`

- [ ] **Step 7: Commit**

```bash
git add projects/kitchen-side-table/table/sheets.py projects/kitchen-side-table/tests/conftest.py projects/kitchen-side-table/tests/test_sheets.py
git commit -m "Lay the kitchen table's parts out on their stock"
```

---

### Task 6: The spec's rules

**Files:**
- Create: `projects/kitchen-side-table/table/rules.py`
- Test: `projects/kitchen-side-table/tests/test_rules.py`

**Interfaces:**
- Consumes: `table.spec`; `dowel_depths()`, `dowel_hole()`; `Placed`, `Table`, `extent()`,
  `front_leg_face_y()`, `tip_load()`; `fit_test_pockets()`; `Sheet`, `lvl_depths()`.
- Produces: `check_table(table: Table, sheets: list[Sheet]) -> list[str]`, which returns
  plain-English problems; `[]` means the table can be cut and built. Problems come in rule order.

How each rule is checked:
1. **Stock:** every outline is `EDGE` inside its stock; pockets stay on the stock and out of other
   parts; parts are at least the sheet's gap apart; every stock fits `WORK_AREA` in either
   orientation.
2. **The bit's reach:** the part of each pocket inside its part, less the pocket opened by the
   bit's radius, must vanish when shrunk by `SLIVER` (0.002). A missed square corner leaves a
   curved triangle about 0.03 across, which survives; curve-flattening slivers don't. Each
   fit-test pocket takes the coupon.
3. **Joints, as assembled:** each apron's box, mapped into each leg's face coordinates, enters the
   leg only inside one pocket and no deeper than it. Each leg holds 2 aprons; no two aprons'
   boxes overlap. Every cut is within its bit's flute.
4. **The top covers the legs:** each leg's plan footprint lies within the top shrunk by 0.5.
5. **It won't tip:** overhang ≤ 3.5, and the tip load ≥ 50 lb.
6. **The shank never rubs:** collet-nut clearance ≥ 0.15; the clearance pass stays above the first
   finishing stage; no ridge is left between the clearance and rough passes.
7. **Height:** every leg runs from the floor to the top's underside, and the top's surface is at
   32 ± 1/32.
8. **Shallow end on the left:** the front edge reaches further forward in the right tenth than in
   the left tenth, by more than half the sweep, both in the table and on job 4.
9. **Grooves:** every groove slot stays inside its apron and at least `GROOVE_STOP` from the joints
   and dowel holes.
10. **Dowels:** at least `MIN_DOWEL_IN_TOP` of each dowel goes into the top, and each apron hole
   leaves at least `MIN_PLY_BESIDE_DOWEL` either side.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_rules.py`. The last four tests are Review Focus items 1–3.

```python
import dataclasses

import pytest
from shapely.affinity import scale, translate
from shapely.geometry import LineString, box

from table import spec
from table.frame import build_table
from table.rules import check_table
from table.sheets import make_sheets


def _problems() -> list[str]:
    table = build_table()
    return check_table(table, make_sheets(table))


def _with_placed(table, name, **changes):
    return dataclasses.replace(table, placed=tuple(
        dataclasses.replace(p, **changes) if p.name == name else p for p in table.placed))


def test_the_approved_table_passes_every_rule(table, sheets):
    assert check_table(table, list(sheets.values())) == []


def test_a_part_too_close_to_the_stocks_edge_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "LVL_WIDTH", 11.4)
    assert _problems() == ['legs: the back-left is not 0.125" inside the stock']


def test_parts_closer_than_the_sheets_gap_are_reported(table, sheets):
    aprons = sheets["aprons"]
    crowded = dataclasses.replace(aprons.parts[1], outline=translate(aprons.parts[1].outline, 0, -0.2))
    doctored = dict(sheets, aprons=dataclasses.replace(aprons, parts=(aprons.parts[0], crowded, *aprons.parts[2:])))
    assert check_table(table, list(doctored.values())) == [
        'aprons: only 0.050" between the back apron and the front apron, needs 0.25"']


def test_stock_too_big_for_the_machine_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "TOP_WIDTH", 36.0)
    assert _problems() == ['top: the 36 x 24" stock doesn\'t fit the 33 x 33" work area']


def test_a_square_corner_the_bit_cant_reach_is_reported(table, sheets):
    leg = table.legs[0]
    plain = box(-1.103, 28.25, -0.375, 31.45)  # the front-left housing with no dogbones
    doctored = dataclasses.replace(table, legs=(dataclasses.replace(leg, housing=plain), *table.legs[1:]))
    assert check_table(doctored, list(sheets.values())) == ["the bit can't reach every corner of the front-left leg's housing"]


def test_a_housing_narrower_than_the_plywood_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "FIT_CLEARANCE", -0.01)
    problems = _problems()
    assert "the coupon doesn't fit the fit test's housing" in problems
    assert "the left apron runs into the front-left leg outside its pockets" in problems
    assert len(problems) == 5


def test_a_pocket_too_shallow_for_its_apron_is_reported(table, sheets):
    leg = next(p for p in table.placed if p.name == "front-left")
    doctored = _with_placed(table, "front-left", pockets=((leg.pockets[0][0], 0.5), leg.pockets[1]))
    assert check_table(doctored, list(sheets.values())) == [
        'the left apron goes 0.750" into the front-left leg, but its pocket is 0.500" deep']


def test_a_cut_deeper_than_the_three_flute_bits_flute_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "THREE_FLUTE_LENGTH", 0.7)
    assert _problems() == ['the plywood cut-out is 0.743" deep, past the three-flute bit\'s 0.7" flute',
                           'the fit-test housing is 0.750" deep, past the three-flute bit\'s 0.7" flute',
                           'the top cut-out is 0.770" deep, past the three-flute bit\'s 0.7" flute']


def test_legs_too_near_the_tops_edge_are_reported(monkeypatch):
    monkeypatch.setattr(spec, "LEG_INSET", 0.25)
    assert 'the front-left leg\'s top is not 0.5" inside the top\'s edge' in _problems()


def test_a_front_edge_too_far_past_the_legs_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "FRONT_LEG_BEHIND_EDGE", 5.0)
    assert _problems() == ['the front edge reaches 5.00" past the front legs, more than 3.5"',
                           "39 lb on the front edge would tip the table, under 50 lb"]


def test_a_table_too_easy_to_tip_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 100.0)
    assert _problems() == ["64 lb on the front edge would tip the table, under 100 lb"]


def test_a_collet_nut_too_close_to_the_lvl_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "STICKOUT", 1.9)
    assert _problems() == ['the collet nut clears the LVL by only 0.094" at full depth, under 0.15"']


def test_a_ridge_between_the_clearance_and_rough_passes_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "CLEARANCE_OFFSET", 0.3)
    assert _problems() == ["the clearance pass leaves a ridge between itself and the rough pass"]


def test_a_leg_that_doesnt_reach_the_top_is_reported(table, sheets):
    leg = next(p for p in table.placed if p.name == "front-left")
    doctored = _with_placed(table, "front-left", outline=translate(leg.outline, 0, -0.1))
    assert check_table(doctored, list(sheets.values())) == [
        'the front-left leg runs from -0.100 to 31.150", not from the floor to the top']


def test_a_mirrored_top_is_reported(table, sheets):
    mirrored = scale(table.top, -1, 1, origin=(31.75 / 2, 0))
    assert check_table(dataclasses.replace(table, top=mirrored), list(sheets.values())) == [
        "the top's shallow end is not on the left as seen from the room"]


def test_a_mirrored_top_on_job_4_is_reported(table, sheets):
    top = sheets["top"]
    mirrored = dataclasses.replace(top.parts[0], outline=scale(top.parts[0].outline, -1, 1, origin=(16, 0)))
    doctored = dict(sheets, top=dataclasses.replace(top, parts=(mirrored,)))
    assert check_table(table, list(doctored.values())) == ["the top's shallow end is not on the left of job 4"]


def test_a_groove_reaching_into_a_joint_is_reported(table, sheets):
    front = table.aprons[0]
    long_groove = dataclasses.replace(front, grooves=(LineString([(1.0, 2.5), (11.0, 2.5)]), front.grooves[1]))
    doctored = dataclasses.replace(table, aprons=(long_groove, *table.aprons[1:]))
    assert check_table(doctored, list(sheets.values())) == [
        'a clip groove in the front apron comes within 0.5" of a joint or dowel']


def test_a_groove_running_through_the_dowels_is_reported(table, sheets):
    front = table.aprons[0]
    through = dataclasses.replace(front, grooves=(LineString([(2.375, 2.5), (24.375, 2.5)]),))
    doctored = dataclasses.replace(table, aprons=(through, *table.aprons[1:]))
    assert check_table(doctored, list(sheets.values())) == [
        'a clip groove in the front apron comes within 0.5" of a joint or dowel']


def test_a_top_too_thin_to_hold_the_dowels_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.6)
    assert _problems() == ['only 0.350" of each dowel goes into the top, under 0.375"']


def test_a_dowel_too_fat_for_the_plywood_edge_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "DOWEL_DIAMETER", 0.5)
    assert _problems() == ['the dowel holes leave only 0.111" of plywood either side']


def test_a_glue_up_a_little_smaller_than_nominal_still_passes_and_rescales(monkeypatch):
    monkeypatch.setattr(spec, "TOP_WIDTH", 31.5)
    monkeypatch.setattr(spec, "TOP_DEPTH", 23.5)
    table = build_table()
    assert check_table(table, make_sheets(table)) == []
    assert next(a for a in table.aprons if a.name == "front apron").outline.bounds[2] == pytest.approx(26.25)


def test_a_top_sanded_to_0_72_still_passes_with_longer_legs(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.72)
    table = build_table()
    assert check_table(table, make_sheets(table)) == []
    assert table.legs[0].outline.bounds[3] == pytest.approx(31.28)


@pytest.mark.parametrize("thickness", [0.70, 0.75])
def test_plywood_a_little_thinner_or_thicker_still_passes(monkeypatch, thickness):
    monkeypatch.setattr(spec, "PLY_THICKNESS", thickness)
    assert _problems() == []
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_rules.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.rules'`

- [ ] **Step 3: Write `table/rules.py`**

```python
"""The spec's rules. check_table returns plain-English problems; an empty list means cut it and build it."""
from __future__ import annotations

import itertools

from shapely.geometry import Polygon, box

from table import spec
from table.aprons import dowel_depths, dowel_hole
from table.frame import Placed, Table, extent, front_leg_face_y, tip_load
from table.legs import fit_test_pockets
from table.sheets import Sheet, lvl_depths

TOL = 1e-6
SLIVER = 0.002  # uncut bits of pocket thinner than this are curve-flattening noise, not a missed corner


def check_table(table: Table, sheets: list[Sheet]) -> list[str]:
    return (_fits_stock(sheets) + _bit_reaches(table) + _joints_fit(table) + _top_covers_legs(table)
            + _stands(table) + _shank_clear() + _height(table) + _shallow_left(table, sheets)
            + _grooves_clear(table) + _dowels_fit())


def _fits_stock(sheets: list[Sheet]) -> list[str]:
    problems = []
    reach_w, reach_h = spec.WORK_AREA
    for sheet in sheets:
        w, h = sheet.stock
        if not (w <= reach_w and h <= reach_h) and not (h <= reach_w and w <= reach_h):
            problems.append(f"{sheet.name}: the {w:g} x {h:g}\" stock doesn't fit the {reach_w:g} x {reach_h:g}\" work area")
        inner = box(spec.EDGE, spec.EDGE, w - spec.EDGE, h - spec.EDGE).buffer(TOL)
        stock = box(0, 0, w, h).buffer(TOL)
        outlined = [p for p in sheet.parts if p.outline is not None]
        for part in outlined:
            if not inner.contains(part.outline):
                problems.append(f"{sheet.name}: the {part.name} is not {spec.EDGE}\" inside the stock")
        for part in sheet.parts:
            for layer, pocket in part.pockets:
                if not stock.contains(pocket):
                    problems.append(f"{sheet.name}: a {layer} pocket in the {part.name} runs off the stock")
                for other in outlined:
                    if other is not part and pocket.intersection(other.outline).area > TOL:
                        problems.append(f"{sheet.name}: a {layer} pocket in the {part.name} cuts into the {other.name}")
        for a, b in itertools.combinations(outlined, 2):
            gap = a.outline.distance(b.outline)
            if gap < sheet.gap - TOL:
                problems.append(f"{sheet.name}: only {gap:.3f}\" between the {a.name} and the {b.name}, needs {sheet.gap}\"")
    return problems


def _uncut(pocket: Polygon, region: Polygon) -> bool:
    """Whether any of the pocket inside region is out of the bit's reach."""
    r = spec.BIT_DIAMETER / 2
    opened = pocket.buffer(-r, quad_segs=32).buffer(r, quad_segs=32)
    return not pocket.intersection(region).difference(opened).buffer(-SLIVER).is_empty


def _bit_reaches(table: Table) -> list[str]:
    problems = []
    for leg in table.legs:
        for label, pocket in (("housing", leg.housing), ("lap", leg.lap)):
            if _uncut(pocket, leg.outline):
                problems.append(f"the bit can't reach every corner of the {leg.name} leg's {label}")
    housing, lap = fit_test_pockets()
    length, width = spec.COUPON
    for label, pocket, coupon_end in (("housing", housing, box(0, 0, spec.PLY_THICKNESS, width)),
                                      ("lap", lap, box(0, 0, length, width))):
        if _uncut(pocket, pocket):
            problems.append(f"the bit can't reach every corner of the fit test's {label}")
        if not pocket.buffer(TOL).contains(coupon_end):
            problems.append(f"the coupon doesn't fit the fit test's {label}")
    return problems


def _box_in(part: Placed, frame: Placed) -> tuple[float, float, float, float, float, float]:
    """The part's bounding box in another part's face coordinates: u0, v0, u1, v1, depth0, depth1."""
    minx, miny, maxx, maxy = part.outline.bounds
    points = [frame.to_face(part.to_table(a, b, depth))
              for a in (minx, maxx) for b in (miny, maxy) for depth in (0.0, part.thickness)]
    us, vs, ds = zip(*points)
    return min(us), min(vs), max(us), max(vs), min(ds), max(ds)


def _joints_fit(table: Table) -> list[str]:
    problems = []
    placed = {p.name: p for p in table.placed}
    aprons = [placed[a.name] for a in table.aprons]
    for leg in (placed[leg.name] for leg in table.legs):
        held = 0
        for apron in aprons:
            u0, v0, u1, v1, d0, d1 = _box_in(apron, leg)
            inside = box(u0, v0, u1, v1).intersection(leg.outline)
            if inside.area < TOL or d1 < TOL or d0 > leg.thickness - TOL:
                continue
            held += 1
            depth = next((depth for shape, depth in leg.pockets if shape.buffer(TOL).contains(inside)), None)
            if depth is None:
                problems.append(f"the {apron.name} runs into the {leg.name} leg outside its pockets")
            elif d1 > depth + TOL:
                problems.append(f"the {apron.name} goes {d1:.3f}\" into the {leg.name} leg, but its pocket is {depth:.3f}\" deep")
        if held != 2:
            problems.append(f"the {leg.name} leg holds {held} aprons, not 2")
    for a, b in itertools.combinations(aprons, 2):
        (alo, ahi), (blo, bhi) = extent(a), extent(b)
        if all(min(ahi[i], bhi[i]) - max(alo[i], blo[i]) > TOL for i in range(3)):
            problems.append(f"the {a.name} and the {b.name} run into each other")
    three_flute = {"plywood cut-out": spec.PLY_THICKNESS + spec.THROUGH, "clip groove": spec.GROOVE_DEPTH,
                   "fit-test housing": spec.HOUSING_DEPTH, "top cut-out": spec.TOP_THICKNESS + spec.THROUGH}
    for label, depth in three_flute.items():
        if depth > spec.THREE_FLUTE_LENGTH + TOL:
            problems.append(f"the {label} is {depth:.3f}\" deep, past the three-flute bit's {spec.THREE_FLUTE_LENGTH}\" flute")
    for label, depth in (("housing", spec.HOUSING_DEPTH), ("lap", spec.PLY_THICKNESS)):
        if depth > spec.TWO_FLUTE_LENGTH + TOL:
            problems.append(f"the legs' {label} is {depth:.3f}\" deep, past the two-flute bit's {spec.TWO_FLUTE_LENGTH}\" flute")
    return problems


def _top_covers_legs(table: Table) -> list[str]:
    problems = []
    covered = table.top.buffer(-spec.MIN_TOP_OVER_LEG).buffer(TOL)
    for part in table.placed:
        if part.material != "lvl":
            continue
        (x0, y0, _), (x1, y1, _) = extent(part)
        if not covered.contains(box(x0, y0, x1, y1)):
            problems.append(f"the {part.name} leg's top is not {spec.MIN_TOP_OVER_LEG}\" inside the top's edge")
    return problems


def _stands(table: Table) -> list[str]:
    problems = []
    overhang = front_leg_face_y(table) - table.top.bounds[1]
    if overhang > spec.MAX_OVERHANG + TOL:
        problems.append(f"the front edge reaches {overhang:.2f}\" past the front legs, more than {spec.MAX_OVERHANG}\"")
    load = tip_load(table)
    if load < spec.MIN_TIP_LOAD:
        problems.append(f"{load:.0f} lb on the front edge would tip the table, under {spec.MIN_TIP_LOAD:.0f} lb")
    return problems


def _shank_clear() -> list[str]:
    problems = []
    depths = lvl_depths()
    nut = spec.STICKOUT - depths["full"]
    if nut < spec.MIN_COLLET_NUT_CLEARANCE - TOL:
        problems.append(f"the collet nut clears the LVL by only {nut:.3f}\" at full depth, under {spec.MIN_COLLET_NUT_CLEARANCE}\"")
    if depths["clearance"] >= depths["first_stage"]:
        problems.append(f"the clearance pass ({depths['clearance']:.3f}\") reaches below the first finishing stage")
    if spec.CLEARANCE_OFFSET > spec.ROUGH_OFFSET + spec.BIT_DIAMETER + TOL:
        problems.append("the clearance pass leaves a ridge between itself and the rough pass")
    return problems


def _height(table: Table) -> list[str]:
    problems = []
    top_lo, top_hi = extent(next(p for p in table.placed if p.name == "top"))
    for part in table.placed:
        if part.material != "lvl":
            continue
        lo, hi = extent(part)
        if abs(lo[2]) > TOL or abs(hi[2] - top_lo[2]) > TOL:
            problems.append(f"the {part.name} leg runs from {lo[2]:.3f} to {hi[2]:.3f}\", not from the floor to the top")
    if abs(top_hi[2] - spec.HEIGHT) > spec.HEIGHT_TOLERANCE:
        problems.append(f"the table is {top_hi[2]:.3f}\" tall, not {spec.HEIGHT}\"")
    return problems


def _front_reach(outline: Polygon, x0: float, x1: float) -> float:
    _, miny, _, maxy = outline.bounds
    return outline.intersection(box(x0, miny - 1, x1, maxy + 1)).bounds[1]


def _shallow_on_left(outline: Polygon) -> bool:
    minx, _, maxx, _ = outline.bounds
    tenth = (maxx - minx) / 10
    return _front_reach(outline, minx, minx + tenth) > _front_reach(outline, maxx - tenth, maxx) + spec.SWEEP_DROP / 2


def _shallow_left(table: Table, sheets: list[Sheet]) -> list[str]:
    problems = []
    if not _shallow_on_left(table.top):
        problems.append("the top's shallow end is not on the left as seen from the room")
    top = next(s for s in sheets if s.name == "top")
    if not _shallow_on_left(top.parts[0].outline):
        problems.append("the top's shallow end is not on the left of job 4")
    return problems


def _grooves_clear(table: Table) -> list[str]:
    problems = []
    for part in table.aprons:
        keep_out = list(part.joints) + [dowel_hole(a) for a in part.dowels]
        for groove in part.grooves:
            slot = groove.buffer(spec.GROOVE_WIDTH / 2)
            if not part.outline.buffer(TOL).contains(slot):
                problems.append(f"a clip groove runs off the {part.name}")
            if any(slot.distance(zone) < spec.GROOVE_STOP - TOL for zone in keep_out):
                problems.append(f"a clip groove in the {part.name} comes within {spec.GROOVE_STOP}\" of a joint or dowel")
    return problems


def _dowels_fit() -> list[str]:
    problems = []
    in_top, _ = dowel_depths()
    if in_top < spec.MIN_DOWEL_IN_TOP - TOL:
        problems.append(f"only {in_top:.3f}\" of each dowel goes into the top, under {spec.MIN_DOWEL_IN_TOP}\"")
    wall = (spec.PLY_THICKNESS - spec.DOWEL_DIAMETER) / 2
    if wall < spec.MIN_PLY_BESIDE_DOWEL - TOL:
        problems.append(f"the dowel holes leave only {wall:.3f}\" of plywood either side")
    return problems
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_rules.py -q`
Expected: `24 passed`. If a message test fails on wording, fix the message in `rules.py` to match
the test; the tests carry the approved wording.

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `68 passed`

- [ ] **Step 6: Commit**

```bash
git add projects/kitchen-side-table/table/rules.py projects/kitchen-side-table/tests/test_rules.py
git commit -m "Check the kitchen table against the spec's rules"
```

---

### Task 7: DXF, SVG and PNG previews

**Files:**
- Create: `projects/kitchen-side-table/table/export.py`
- Test: `projects/kitchen-side-table/tests/test_export.py`

**Interfaces:**
- Consumes: `table.spec`; `Sheet`.
- Produces:
  - `LAYERS: dict[str, tuple[int, str]]`, mapping each layer to its DXF colour index and SVG
    colour, in drawing order.
  - `sheet_items(sheet) -> list[tuple[str, list[tuple[float, float]], bool]]`, giving each item's
    layer, points and whether it's closed.
  - `write_dxf(sheet, path)`, `write_svg(sheet, path)` and `write_preview(sheet, path)`.

The DXF is R2010, with `$INSUNITS` = 1 (inches), one LWPOLYLINE per item, and only the layers it
uses. `CLEARANCE` and `ROUGH` are the legs' outlines offset outward (round joins) and appear only
on the LVL sheet. Grooves are open polylines on `GROOVE_CENTERLINE`. cadgen's validator allows open
lines only on a layer whose name it reads as not cut-through, and "centerline" is one of those
names.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_export.py`:

```python
import xml.etree.ElementTree as ET

import ezdxf
import pytest
from cadgen.drawing_checks import validate_dxf_file
from shapely.geometry import Polygon

from table.export import write_dxf, write_preview, write_svg

SVG = "{http://www.w3.org/2000/svg}"
EXPECTED_LAYERS = {
    "aprons": {"REFERENCE_STOCK", "GROOVE_CENTERLINE", "CUT_OUTSIDE"},
    "fit_test": {"REFERENCE_STOCK", "POCKET_HOUSING", "POCKET_LAP"},
    "legs": {"REFERENCE_STOCK", "POCKET_HOUSING", "POCKET_LAP", "CLEARANCE", "ROUGH", "CUT_OUTSIDE"},
    "top": {"REFERENCE_STOCK", "CUT_OUTSIDE"},
}


@pytest.fixture(scope="module")
def dxfs(tmp_path_factory, sheets):
    folder = tmp_path_factory.mktemp("dxf")
    for name, sheet in sheets.items():
        write_dxf(sheet, folder / f"{name}.dxf")
    return folder


def test_each_dxf_is_in_inches_with_the_layers_its_job_needs(dxfs):
    for name, layers in EXPECTED_LAYERS.items():
        doc = ezdxf.readfile(dxfs / f"{name}.dxf")
        assert doc.header["$INSUNITS"] == 1
        assert {layer.dxf.name for layer in doc.layers} - {"0", "Defpoints"} == layers


def test_each_dxf_passes_cadgens_drawing_checks(dxfs):
    for name in EXPECTED_LAYERS:
        assert [f.render() for f in validate_dxf_file(dxfs / f"{name}.dxf") if f.severity == "error"] == []


def test_grooves_are_open_lines_and_everything_else_closed(dxfs):
    for name in EXPECTED_LAYERS:
        for line in ezdxf.readfile(dxfs / f"{name}.dxf").modelspace().query("LWPOLYLINE"):
            assert line.closed == (line.dxf.layer != "GROOVE_CENTERLINE")


def test_the_legs_clearance_and_rough_lines_sit_outside_each_leg_by_their_offsets(dxfs):
    msp = ezdxf.readfile(dxfs / "legs.dxf").modelspace()
    shapes = lambda layer: [Polygon(list(p.get_points("xy"))) for p in msp.query(f'LWPOLYLINE[layer=="{layer}"]')]  # noqa: E731
    legs, clearance, rough = shapes("CUT_OUTSIDE"), shapes("CLEARANCE"), shapes("ROUGH")
    assert len(legs) == len(clearance) == len(rough) == 4
    for leg, wide, near in zip(legs, clearance, rough):
        assert wide.contains(leg) and near.contains(leg)
        assert leg.hausdorff_distance(wide) == pytest.approx(0.125, abs=0.002)
        assert leg.hausdorff_distance(near) == pytest.approx(0.02, abs=0.002)


def test_the_top_dxf_has_the_shallow_end_on_the_left(dxfs):
    msp = ezdxf.readfile(dxfs / "top.dxf").modelspace()
    points = list(next(iter(msp.query('LWPOLYLINE[layer=="CUT_OUTSIDE"]'))).get_points("xy"))
    assert min(y for x, y in points if x < 3.3) > min(y for x, y in points if x > 28.8) + 1.5


def test_the_svg_is_sized_in_inches_with_a_group_per_layer(tmp_path, sheets):
    path = tmp_path / "legs.svg"
    write_svg(sheets["legs"], path)
    root = ET.parse(path).getroot()
    assert (root.get("width"), root.get("height"), root.get("viewBox")) == ("32.5in", "11.75in", "0 0 32.5 11.75")
    assert {g.get("id") for g in root.findall(f"{SVG}g")} == EXPECTED_LAYERS["legs"]


def test_the_preview_is_a_png(tmp_path, sheets):
    path = tmp_path / "aprons.png"
    write_preview(sheets["aprons"], path)
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_export.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.export'`

- [ ] **Step 3: Write `table/export.py`**

```python
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
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_export.py -q`
Expected: `7 passed`

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `75 passed`

- [ ] **Step 6: Commit**

```bash
git add projects/kitchen-side-table/table/export.py projects/kitchen-side-table/tests/test_export.py
git commit -m "Write the kitchen table's sheets as DXF, SVG and previews"
```

---

### Task 8: The 3D model

**Files:**
- Create: `projects/kitchen-side-table/table/model.py`
- Test: `projects/kitchen-side-table/tests/test_model.py`

**Interfaces:**
- Consumes: `table.spec`; `dowel_depths()`; `Placed`, `Table`, `dowel_spots()`.
- Produces: `part_solid(part: Placed)`, which returns a labelled, coloured build123d solid;
  `table_model(table) -> Compound`, with 13 children: the 9 parts and `"dowel 1"` to
  `"dowel 4"`; and `write_model(table, step: Path, glb: Path)`.

Pitfall, found while prototyping: extrude with an explicit direction,
`extrude(face, amount=t, dir=(0, 0, -1))`. With `amount=-t` and no direction, the result depends on
each face's winding, and the mirrored (flare-left) legs then land on the wrong side of their
faces. `test_every_part_lands_where_the_frame_puts_it` catches this. Outlines are simplified by
0.002" for the model only, which keeps the STEP file near 2.3 MB rather than 9 MB.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_model.py`:

```python
import math

import pytest

from table.model import table_model, write_model


@pytest.fixture(scope="module")
def model(table):
    return table_model(table)


def _boxes(model):
    return {c.label: c.bounding_box() for c in model.children}


def test_the_model_has_every_part_and_four_dowels(model):
    assert sorted(_boxes(model)) == sorted(["top", "front-left", "front-right", "back-left", "back-right",
                                            "front apron", "back apron", "left apron", "right apron",
                                            "dowel 1", "dowel 2", "dowel 3", "dowel 4"])


def test_every_part_lands_where_the_frame_puts_it(model):
    boxes = _boxes(model)
    expect = {"top": (0, 31.75, 0, 23.75, 31.25, 32.0),
              "front-left": (1.0, 4.25, 3.5, 5.286, 0, 31.25),
              "front-right": (27.5, 30.75, 3.5, 5.286, 0, 31.25),
              "back-left": (1.0, 4.25, 18.964, 20.75, 0, 31.25),
              "back-right": (27.5, 30.75, 18.964, 20.75, 0, 31.25),
              "left apron": (1.375, 2.098, 4.536, 19.714, 28.25, 31.25)}
    for name, (x0, x1, y0, y1, z0, z1) in expect.items():
        b = boxes[name]
        assert (b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z) == pytest.approx((x0, x1, y0, y1, z0, z1), abs=1e-3), name


def test_the_pockets_and_grooves_are_cut_out_of_the_parts(model):
    volumes = {c.label: c.volume for c in model.children}
    assert volumes["front-left"] == pytest.approx(119.18, abs=0.05)
    groove = (9.21875 * 0.25 + math.pi * 0.125 ** 2) * 0.3125  # a slot with round ends
    assert volumes["front apron"] == pytest.approx(26.75 * 3 * 0.723 - 2 * groove, abs=0.01)


def test_the_model_writes_step_and_glb(tmp_path, table):
    write_model(table, tmp_path / "table.step", tmp_path / "table.glb")
    assert (tmp_path / "table.step").read_text(errors="ignore").startswith("ISO-10303-21")
    assert (tmp_path / "table.glb").read_bytes()[:4] == b"glTF"
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_model.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'table.model'`

- [ ] **Step 3: Write `table/model.py`**

```python
"""The assembled table as a 3D model (STEP and GLB), for looking at in the CAD Viewer."""
from __future__ import annotations

from pathlib import Path

from build123d import (Align, Color, Compound, Cylinder, Face, Plane, Pos, Vector, Wire, export_gltf, export_step,
                       extrude)
from shapely.geometry import Polygon

from table import spec
from table.aprons import dowel_depths
from table.frame import Placed, Table, dowel_spots

SIMPLIFY = 0.002  # the preview's outlines may stray this far from the cut files', to keep the files small
COLORS = {"cherry": (0.62, 0.32, 0.2), "lvl": (0.84, 0.69, 0.48), "plywood": (0.92, 0.86, 0.72)}


def _face(polygon: Polygon) -> Face:
    ring = polygon.simplify(SIMPLIFY).exterior.coords[:-1]
    return Face(Wire.make_polygon([Vector(x, y, 0) for x, y in ring], close=True))


def part_solid(part: Placed):
    """The part with its pockets cut, moved into table coordinates."""
    solid = extrude(_face(part.outline), amount=part.thickness, dir=(0, 0, -1))
    for shape, depth in part.pockets:
        solid = solid - extrude(_face(shape), amount=depth, dir=(0, 0, -1))
    placed = Plane(origin=part.origin, x_dir=part.a_axis, z_dir=part.normal).location * solid
    placed.label = part.name
    placed.color = Color(*COLORS[part.material])
    return placed


def table_model(table: Table) -> Compound:
    parts = [part_solid(p) for p in table.placed]
    r = spec.DOWEL_DIAMETER / 2
    for i, (x, y, z) in enumerate(dowel_spots(table), start=1):
        dowel = Pos(x, y, z + dowel_depths()[0] - spec.DOWEL_LENGTH) * Cylinder(
            r, spec.DOWEL_LENGTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
        dowel.label = f"dowel {i}"
        dowel.color = Color(0.95, 0.9, 0.75)
        parts.append(dowel)
    return Compound(children=parts, label="kitchen side table")


def write_model(table: Table, step: Path, glb: Path) -> None:
    model = table_model(table)
    export_step(model, step)
    export_gltf(model, str(glb), binary=True)
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_model.py -q`
Expected: `4 passed`

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `79 passed`

- [ ] **Step 6: Commit**

```bash
git add projects/kitchen-side-table/table/model.py projects/kitchen-side-table/tests/test_model.py
git commit -m "Build the kitchen table's 3D model"
```

---

### Task 9: The build, the generated files, and the docs

**Files:**
- Create: `projects/kitchen-side-table/build.py`
- Test: `projects/kitchen-side-table/tests/test_build.py`
- Create: `projects/kitchen-side-table/README.md`, `projects/kitchen-side-table/AGENTS.md`
- Create (generated): `projects/kitchen-side-table/out/` (4 DXF, 4 SVG, `table.step`, `table.glb`,
  `previews/*.png`)
- Modify: `README.md` (repo root): add a projects-table line and credit build123d

**Interfaces:**
- Consumes: everything above.
- Produces: `build.build(out_dir: Path = OUT) -> dict`, `build.main(out_dir: Path = OUT) -> int`,
  and `build.BuildError(problems: list[str])`. The report has the keys `top`, `leg_length`,
  `long_apron`, `side_apron`, `lvl_spare`, `lvl_depths`, `dowel_depths`, `tip_load` and `nominal`.

- [ ] **Step 1: Write the failing tests**

`projects/kitchen-side-table/tests/test_build.py`. The last three tests are Review Focus items 4
and 5.

```python
import pytest

import build
from table import spec

EXPECTED_FILES = {"aprons.dxf", "aprons.svg", "fit_test.dxf", "fit_test.svg", "legs.dxf", "legs.svg",
                  "top.dxf", "top.svg", "table.step", "table.glb",
                  "previews/aprons.png", "previews/fit_test.png", "previews/legs.png", "previews/top.png"}


def test_build_writes_every_file_into_a_new_folder_and_reports_the_numbers(tmp_path):
    out = tmp_path / "new" / "out"
    report = build.build(out)
    assert {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()} == EXPECTED_FILES
    assert report == {"top": (31.75, 23.75), "leg_length": 31.25, "long_apron": 26.75, "side_apron": 15.178,
                      "lvl_spare": 0.296, "lvl_depths": {"full": 1.806, "clearance": 0.506, "first_stage": 1.3},
                      "dowel_depths": (0.5, 1.0625), "tip_load": 64, "nominal": ["TOP_WIDTH", "TOP_DEPTH"]}


def test_build_refuses_to_write_anything_when_a_rule_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 500.0)
    with pytest.raises(build.BuildError) as err:
        build.build(tmp_path / "out")
    assert err.value.problems == ["64 lb on the front edge would tip the table, under 500 lb"]
    assert not (tmp_path / "out").exists()


def test_rebuilding_into_an_existing_folder_replaces_the_files(tmp_path):
    build.build(tmp_path)
    (tmp_path / "top.dxf").write_text("stale")
    build.build(tmp_path)
    assert (tmp_path / "top.dxf").read_text() != "stale"


def test_main_prints_the_numbers_and_the_values_still_to_measure(tmp_path, capsys):
    assert build.main(tmp_path) == 0
    out = capsys.readouterr().out
    assert "top 31.75 x 23.75 in, legs 31.25 in long" in out
    assert "dowel holes: 0.5 in into the top, 1.0625 in into the aprons" in out
    assert "still nominal, measure and update spec.py: TOP_WIDTH, TOP_DEPTH" in out


def test_main_prints_the_problems_and_fails_when_a_rule_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 500.0)
    assert build.main(tmp_path / "out") == 1
    err = capsys.readouterr().err
    assert "64 lb on the front edge would tip the table, under 500 lb" in err
    assert "Build failed" in err
```

- [ ] **Step 2: Run them to see them fail**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_build.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: Write `build.py`**

```python
"""Build the kitchen side table's cut files, previews and 3D model into out/. Writes nothing if any rule fails.

Run from the repo root:  tools/py projects/kitchen-side-table/build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from cadgen.drawing_checks import validate_dxf_file

from table import spec
from table.aprons import dowel_depths, long_apron_length, side_apron_length
from table.export import write_dxf, write_preview, write_svg
from table.frame import build_table, tip_load
from table.legs import leg_length
from table.model import write_model
from table.rules import check_table
from table.sheets import lvl_depths, lvl_spare, make_sheets
from table.top import top_size

OUT = Path(__file__).resolve().parent / "out"


class BuildError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(f"{len(problems)} problem(s)")


def build(out_dir: Path = OUT) -> dict:
    table = build_table()
    sheets = make_sheets(table)
    problems = check_table(table, sheets)
    if problems:
        raise BuildError(problems)
    (out_dir / "previews").mkdir(parents=True, exist_ok=True)
    for sheet in sheets:
        dxf = out_dir / f"{sheet.name}.dxf"
        write_dxf(sheet, dxf)
        write_svg(sheet, out_dir / f"{sheet.name}.svg")
        write_preview(sheet, out_dir / "previews" / f"{sheet.name}.png")
        errors = [f.render() for f in validate_dxf_file(dxf) if f.severity == "error"]
        if errors:
            raise BuildError([f"{dxf.name}: {error}" for error in errors])
    write_model(table, out_dir / "table.step", out_dir / "table.glb")
    w, d = top_size()
    depths = lvl_depths()
    legs = next(s for s in sheets if s.name == "legs")
    return {
        "top": (round(w, 3), round(d, 3)),
        "leg_length": round(leg_length(), 3),
        "long_apron": round(long_apron_length(), 3),
        "side_apron": round(side_apron_length(), 3),
        "lvl_spare": round(lvl_spare(legs), 3),
        "lvl_depths": {name: round(value, 3) for name, value in depths.items()},
        "dowel_depths": tuple(round(depth, 4) for depth in dowel_depths()),
        "tip_load": round(tip_load(table)),
        "nominal": list(spec.NOMINAL),
    }


def main(out_dir: Path = OUT) -> int:
    try:
        report = build(out_dir)
    except BuildError as err:
        for problem in err.problems:
            print(problem, file=sys.stderr)
        print("Build failed: fix the problems above.", file=sys.stderr)
        return 1
    w, d = report["top"]
    depths = report["lvl_depths"]
    print(f"top {w} x {d} in, legs {report['leg_length']} in long")
    print(f"aprons: long {report['long_apron']} in, side {report['side_apron']} in")
    print(f"LVL: {report['lvl_spare']} in spare; clearance pass {depths['clearance']} in deep, "
          f"finish to {depths['first_stage']} in, then to {depths['full']} in")
    in_top, in_apron = report["dowel_depths"]
    print(f"dowel holes: {in_top} in into the top, {in_apron} in into the aprons")
    print(f"{report['tip_load']} lb on the front edge would tip it")
    if report["nominal"]:
        print(f"still nominal, measure and update spec.py: {', '.join(report['nominal'])}")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `tools/py -m pytest projects/kitchen-side-table/tests/test_build.py -q`
Expected: `5 passed`

- [ ] **Step 5: Run the whole suite**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `84 passed`

- [ ] **Step 6: Run the build**

Run: `tools/py projects/kitchen-side-table/build.py`
Expected output:

```
top 31.75 x 23.75 in, legs 31.25 in long
aprons: long 26.75 in, side 15.178 in
LVL: 0.296 in spare; clearance pass 0.506 in deep, finish to 1.3 in, then to 1.806 in
dowel holes: 0.5 in into the top, 1.0625 in into the aprons
64 lb on the front edge would tip it
still nominal, measure and update spec.py: TOP_WIDTH, TOP_DEPTH
wrote /Users/ry/repos/cad/projects/kitchen-side-table/out
```

- [ ] **Step 7: Look at every preview**

Open each of `out/previews/aprons.png`, `fit_test.png`, `legs.png` and `top.png` with the Read
tool, and check:
- **legs:** four legs head to toe, front-left at the bottom; the pockets at each leg's wide end,
  the orange housing nearer the outer (straight) edge; the dashed cyan and magenta lines outside
  every outline.
- **aprons:** back and front aprons in the bottom two strips, the side aprons end to end above
  them, the coupon at the top; red grooves near each apron's top edge, the long aprons' split in
  two at the middle.
- **fit_test:** a narrow housing and a wide lap, each with four dogbones.
- **top:** the shallow end and the larger rounded corner at the left, the front edge at the
  bottom, square back corners.

Then show the 3D model to the user: call `mcp__plugin_text-to-cad_cad__cad_show` with
`/Users/ry/repos/cad/projects/kitchen-side-table/out/table.glb`, and share its link. Check that the
sweep's shallow end is on the left as seen from the front (the side away from the wall), and the
flares face front and back.

- [ ] **Step 8: Write `projects/kitchen-side-table/README.md`**

````markdown
# Kitchen side table

A small side table for beside the kitchen: 31¾ × 23¾" and 32" tall. The back stands against the
wall. The front edge sweeps in an asymmetric curve, shallow at the left end as seen from the room.
It has four flared LVL legs, plywood aprons on all four sides, and a cherry top held by four glued
dowels at its middle and eight Z-clips. Every part is cut on a Shapeoko Pro XXL from files this
project generates.

The design and its reasons are in `docs/specs/2026-10-13-kitchen-side-table-design.md`, and the
build plan is in `docs/plans/`.

![The four legs on the LVL, head to toe](out/previews/legs.png)

## Before you cut

1. Glue up the top (Assembly, step 1), then measure its width and depth. Set `TOP_WIDTH` and
   `TOP_DEPTH` in `table/spec.py`, and take both names out of `NOMINAL`.
2. Rebuild from the repo root: `tools/py projects/kitchen-side-table/build.py`. It prints the sizes,
   the LVL's depths and the dowel holes' depths, and it writes nothing if any rule fails.

## Files

| File | Job | Stock, as it sits on the machine |
|---|---|---|
| `out/aprons.dxf` / `.svg` | 1 | Plywood, 32 × 11⅞ × 0.723", the worse face up |
| `out/fit_test.dxf` / `.svg` | 2 | Any scrap at least 1" thick, about 6 × 4" |
| `out/legs.dxf` / `.svg` | 3 | LVL, 32½ × 11¾ × 1.786", the worse face up |
| `out/top.dxf` / `.svg` | 4 | The cherry glue-up, show face up, curved edge toward you |
| `out/table.step` / `.glb` | – | The assembled table in 3D. Open the GLB in the CAD Viewer. |
| `out/previews/*.png` | – | Each job seen from above, with the parts named |

Every file is in inches, with its origin at the lower-left corner of the stock, seen from above.
Zero X and Y there, and Z on top of the stock.

## Layers and toolpaths (Carbide Create)

| Layer | Colour | Toolpath |
|---|---|---|
| `REFERENCE_STOCK` | grey | None. The stock's outline, to line up by. |
| `POCKET_HOUSING` | orange | Pocket, 0.75" deep |
| `POCKET_LAP` | yellow | Pocket, as deep as the plywood is thick: 0.723" |
| `GROOVE_CENTERLINE` | red | Contour, no offset, 5/16" deep |
| `CLEARANCE` | cyan | Contour, outside, 0.506" deep. Legs only. |
| `ROUGH` | magenta | Contour, outside, to full depth: 1.806". Legs only. |
| `CUT_OUTSIDE` | blue | Contour, outside, to full depth. On the legs, two passes: to 1.3", then from 1.3" to 1.806". |

These depths are what the build prints for the measured stock and bits. If a measurement changes,
rebuild and use the new figures.

## Machining

These are starting settings; tune them by sound and chip.

| Job | Bit | Settings |
|---|---|---|
| 1 aprons, 2 fit test | ¼" three-flute, 1" flute | 16,000 RPM, 50 IPM, 15 IPM plunge (ramp), 0.1" per pass. Tabs on the plywood parts. |
| 3 legs | ¼" two-flute, 1.4" flute: ½" in the collet, 2" out | 12–14,000 RPM, 40 IPM, 10 IPM plunge (ramp), 0.05" per pass. Vacuum and air throughout. About 5 hours. |
| 4 top | ¼" three-flute | As job 1, with a full-depth finishing pass on the outline |

- **Hold-down:** painter's tape and CA glue under the LVL and the top, so neither needs tabs. Their
  cuts go 0.02" into the spoilboard. The plywood is held by its tabs.
- **Job 2 before job 3:** the coupon from job 1 should slide into the test housing snug by hand, and
  sit flush in the test lap. If it doesn't, change `FIT_CLEARANCE` in `table/spec.py`, rebuild, and
  test again before you cut the LVL.
- **Job 3, in this order:** the pockets; the clearance pass; the rough pass; the outline to 1.3";
  then the outline from 1.3" to full depth. The clearance pass widens the top of each slot, so the
  bit's smooth shank never rubs once it goes deeper than the flutes.
- **Job 3, grip and clearance:** draw a marker line on the shank at the collet nut, and check it
  between steps. With the spindle off, jog the bit down beside the LVL until it touches the
  spoilboard, and check that the collet nut is about 0.2" above the top of the board.
- **Mark each leg** with its name in pencil as it comes off (see `out/previews/legs.png`). The
  pockets face into the table.

## Assembly

1. **Glue up the top.** Let the boards sit in the loft for a week or two first. Arrange the four
   boards with the grain front to back, and mark the front ends. Keep the biscuits between 2" and
   19" from the back ends so the cut doesn't expose them. Sand the panel smooth, then measure it
   (see "Before you cut").
2. **Cut jobs 1 to 4**, with the fit test before the LVL.
3. **Dry-fit the base.** The side aprons drop into the housings. The long aprons sit in the laps,
   flush with the legs' inside faces.
4. **Glue the end frames:** each end's front leg, back leg and side apron. Check they're square.
5. **Drill the long aprons' dowel holes** before they go in: two per apron, in the top edge, 5/16"
   wide and 1-1/16" deep. They go 12⅜" and 14⅜" from either end (an inch either side of the
   middle), centered on the plywood's thickness. A doweling jig keeps them square. Then glue the
   long aprons into their laps, with two screws each from inside.
6. **Finish.** Ease every edge by sanding. Seal the top's end-grain front and back edges first, so
   they don't darken more than the face. Put polyurethane on every face, the top's underside
   included, so both sides take up moisture alike and the top stays flat. Tape off the dowel holes
   and the 2" of apron edge between them.
7. **Attach the top.** Lay it upside down on a blanket. Put dowel centers in the four apron holes,
   set the base upside down on the top in its place (legs' outer faces 1" in from each end, back
   legs' back faces 3" from the back edge), and press to mark the top. Drill the four marks 5/16"
   wide and ½" deep, with a stop collar so the bit can't go through. Glue the dowels in, with glue
   only in the holes and on the 2" of apron edge between them; glue anywhere else would lock the
   top. Fit eight Z-clips in the grooves with ⅝" screws: one in each long-apron groove, two in each
   side apron's.

The top grows and shrinks about ⅛–¼" across its width with the seasons. Fixed only at the middle,
it moves half that each way, and the clips slide.

## Code

Python, run from the repo root through `tools/py`:

```bash
tools/py -m pytest projects/kitchen-side-table -q   # tests
tools/py projects/kitchen-side-table/build.py       # regenerate out/
```

`AGENTS.md` describes how the code is laid out and the rules it keeps.
````

- [ ] **Step 9: Write `projects/kitchen-side-table/AGENTS.md`**

````markdown
# AGENTS.md: Kitchen side table

The repo-wide rules are in `../../AGENTS.md`. This file adds the rules for this project.

Python that generates the cut files for a kitchen side table: four flared LVL legs, four plywood
aprons, and a cherry top with a swept front edge, all cut on a Shapeoko Pro XXL. The geometry is
built with shapely and checked against the spec's rules. It's written to `out/` as DXF and SVG
with PNG previews, and assembled into a 3D model with build123d. `README.md` is the machining and
assembly guide. The design is in `docs/specs/2026-10-13-kitchen-side-table-design.md`.

## Commands (from the repo root)

```bash
tools/py -m pytest projects/kitchen-side-table -q        # whole suite, a few seconds
tools/py -m pytest projects/kitchen-side-table/tests/test_rules.py -q
tools/py projects/kitchen-side-table/build.py            # regenerate out/; writes nothing if a rule fails
```

## Layout

- `table/spec.py`: every number, in inches. The measured stock and bits come first. A name stays in
  `NOMINAL` until it has been measured, and the build reminds you of each one.
- `table/top.py`: the top's outline.
- `table/legs.py`: the legs and their pockets, in leg coordinates, and the fit-test pockets.
- `table/aprons.py`: the aprons, with their grooves and dowel holes, and the coupon.
- `table/frame.py`: places every part in table coordinates (`Placed`), and works out the weight,
  the balance and the tipping load.
- `table/sheets.py`: the four jobs, each part on its stock in sheet coordinates.
- `table/rules.py`: `check_table` returns plain-English problems. An empty list means the table can
  be cut and built.
- `table/export.py`: DXF, SVG and PNG previews of each sheet.
- `table/model.py`: the 3D model, as STEP and GLB.
- `build.py`: checks, then writes everything in `out/`.
- `tests/`: one file per module, plus `test_build.py`. The shared `table` and `sheets` fixtures are
  in `conftest.py`.

## Rules that must hold

- **Units are inches, and table coordinates are right-handed:** x from the left end as seen from
  the room, y from the front edge's deepest point toward the wall, z up. A plan drawn with y up is
  the table seen from above, with the wall at the top.
- **Nothing is ever mirrored onto a sheet.** Each part goes on by rotation and translation, with
  the face that's cut first facing up: the legs' and aprons' inside faces, and the top's show face.
  `test_the_legs_go_on_by_rotation_only_never_mirrored` and the shallow-end rule guard this.
- **The sweep's shallow end is on the left** as seen from the room, and on the left of job 4.
- **`check_table` must return `[]`** before the build writes anything. Fix the design, not the rule.
- **Numbers live in `spec.py`.** Every function reads spec values when it runs, so tests can
  monkeypatch them. Never copy a spec value into a module-level constant.
- **The groove layer is `GROOVE_CENTERLINE`**, an open line. cadgen's DXF check rejects open lines
  on layers it reads as cut-through.

## Working here

- After any geometry change, run the build, look at `out/previews/*.png`, and commit the regenerated
  `out/` with the change. The rules can pass on a shape that still looks wrong.
- Every build rewrites the DXF timestamps and the STEP file's header. If a file changed only in that
  metadata, restore it with `git checkout -- <file>`.
- When the design changes, add a revision to the spec and update `README.md`. Keep the README's
  depths in step with the build's printout.
````

- [ ] **Step 10: Update the repo's `README.md`**

In the projects table, add this row below the `fitzgerald-memorial` row:

```markdown
| [`kitchen-side-table`](projects/kitchen-side-table/README.md) | A 32" kitchen side table: flared LVL legs, plywood aprons and a cherry top with a swept front edge |
```

In **Credits → Libraries**, change the matplotlib line to:

```markdown
- [matplotlib](https://matplotlib.org), Matplotlib licence (PSF-based): the 1:1 PDF prints and the
  table's previews.
```

and add this line after the ezdxf line:

```markdown
- [build123d](https://github.com/gumyr/build123d), Apache-2.0: the table's 3D model.
```

- [ ] **Step 11: Run the whole suite one last time**

Run: `tools/py -m pytest projects/kitchen-side-table -q`
Expected: `84 passed`

- [ ] **Step 12: Commit**

Check `git status` first: the two memorial `.c2d` files will show as modified. Leave them alone.

```bash
git add projects/kitchen-side-table/build.py projects/kitchen-side-table/tests/test_build.py \
  projects/kitchen-side-table/README.md projects/kitchen-side-table/AGENTS.md \
  projects/kitchen-side-table/out README.md
git commit -m "Build the kitchen table's cut files and write its machining guide"
```

---

## After the plan

- When the top is glued up and measured: set `TOP_WIDTH` and `TOP_DEPTH` in `table/spec.py`,
  remove them from `NOMINAL`, rebuild, look at the previews again, and commit the code and `out/`
  together.
- If the fit test calls for a different clearance: change `FIT_CLEARANCE`, rebuild, re-cut job 2.
