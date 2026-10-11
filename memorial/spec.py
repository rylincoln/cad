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
KNOT_SIDE_GAP = 0.24  # between the knot's cut edge and the nearest letter (reproduces the approved preview)

# stencil ties, for a laser shop that can't return drop-outs: strips of plate left across a stroke
TIE_WIDTH = 0.06        # in: the copper rule, three times SendCutSend's 0.020" bridge minimum for 0.040" brass
TWO_TIE_CHARS = "D0"    # bowls tied top and bottom, as stencil lettering does; every other centre gets one tie

# sheets
FINAL_SHEET = (18.0, 10.0)
PRACTICE_SHEET = (13.0, 8.0)
PRACTICE_WINDOW = (-8.0, -3.75, 4.5, 3.75)  # minx, miny, maxx, maxy in plate coordinates
PRACTICE_MARGIN = 0.25
