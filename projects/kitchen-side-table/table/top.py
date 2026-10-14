"""The cherry top's outline: the sweep along the front edge, rounded front corners, square back."""
from __future__ import annotations

import math

from shapely.geometry import Polygon, box

from table import spec

SAMPLES = 400


def top_size() -> tuple[float, float]:
    """Finished width and depth: the glue-up less the trim at its ends and along its front and back."""
    return spec.TOP_WIDTH - 2 * spec.TOP_TRIM, spec.TOP_DEPTH - 2 * spec.TOP_CLAMP_TRIM


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
