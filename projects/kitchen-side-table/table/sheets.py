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


def _shifted(part: SheetPart, dy: float) -> SheetPart:
    return SheetPart(part.name, translate(part.outline, 0, dy),
                     tuple((layer, translate(shape, 0, dy)) for layer, shape in part.pockets))


def legs_sheet(table: Table) -> Sheet:
    """Two head-to-toe pairs of one handedness each, inside faces up, centered on the board both ways."""
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
    top = max(p.outline.bounds[3] for p in parts)
    dy = (spec.LVL_WIDTH - top - spec.EDGE) / 2
    return Sheet("legs", "Job 3: LVL legs", (spec.LVL_LENGTH, spec.LVL_WIDTH), spec.LVL_GAP,
                 tuple(_shifted(p, dy) for p in parts), lvl=True)


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


def lvl_clamp_room(sheet: Sheet) -> float:
    """The wood the clearance pass, the widest cut, leaves between the legs and the LVL's nearer long edge."""
    below = min(p.outline.bounds[1] for p in sheet.parts)
    above = sheet.stock[1] - max(p.outline.bounds[3] for p in sheet.parts)
    return min(below, above) - spec.CLEARANCE_OFFSET - spec.BIT_DIAMETER
