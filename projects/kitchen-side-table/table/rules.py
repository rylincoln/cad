"""The spec's rules. check_table returns plain-English problems; an empty list means cut it and build it."""
from __future__ import annotations

import itertools

from shapely.geometry import Polygon, box

from table import spec
from table.aprons import dowel_depths, dowel_hole
from table.frame import Placed, Table, extent, front_leg_face_y, tip_load
from table.legs import fit_test_pockets
from table.sheets import Sheet, lvl_clamp_room, lvl_depths, top_clamp_room

TOL = 1e-6
SLIVER = 0.002  # uncut bits of pocket thinner than this are curve-flattening noise, not a missed corner


def check_table(table: Table, sheets: list[Sheet]) -> list[str]:
    return (_fits_stock(sheets) + _bit_reaches(table) + _joints_fit(table) + _top_covers_legs(table)
            + _stands(table) + _shank_clear() + _height(table) + _shallow_left(table, sheets)
            + _grooves_clear(table) + _dowels_fit() + _clamps_hold(sheets))


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
    reach = spec.CLEARANCE_OFFSET + spec.BIT_DIAMETER
    if reach > spec.LVL_GAP + TOL:
        problems.append(f"the clearance pass reaches {reach:.3f}\" outside each leg, past the {spec.LVL_GAP}\" gap to the next leg")
    return problems


def _clamps_hold(sheets: list[Sheet]) -> list[str]:
    problems = []
    room = lvl_clamp_room(next(s for s in sheets if s.lvl))
    if room < spec.CLAMP_ROOM - TOL:
        problems.append(f"the cutter leaves only {room:.3f}\" of wood along the LVL's long edges for the clamps, under {spec.CLAMP_ROOM}\"")
    room = top_clamp_room(next(s for s in sheets if s.name == "top"))
    if room < spec.CLAMP_ROOM - TOL:
        problems.append(f"the cutter leaves only {room:.3f}\" of wood along the glue-up's front and back edges for the clamps, under {spec.CLAMP_ROOM}\"")
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
