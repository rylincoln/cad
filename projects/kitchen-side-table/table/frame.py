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
