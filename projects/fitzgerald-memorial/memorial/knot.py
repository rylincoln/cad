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
