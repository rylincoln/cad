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
