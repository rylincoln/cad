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
