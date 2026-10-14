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
LVL_THICKNESS = 1.62          # faced; 1.786 as bought
PLY_LENGTH = 32.0
PLY_WIDTH = 11.875
PLY_THICKNESS = 0.706         # the aprons as cut
TWO_FLUTE_LENGTH = 1.4        # the 1/4" two-flute bit, for the LVL
THREE_FLUTE_LENGTH = 1.0      # the 1/4" three-flute bit, for the plywood, fit test and top
STICKOUT = 2.0                # the two-flute bit, out of the collet
NOMINAL = ("TOP_WIDTH", "TOP_DEPTH")

# table
HEIGHT = 32.0
TOP_TRIM = 0.125              # the outline is cut this far inside the glue-up on every side
LEG_INSET = 1.0               # legs' outer faces in from each end of the top
BACK_LEG_FROM_WALL = 3.332    # back legs' back faces from the back edge; 3.0 at first, moved
                              # forward with the faced LVL so the side aprons as cut still fit
FRONT_LEG_BEHIND_EDGE = 3.5   # front legs' front faces behind the front edge's deepest point
SWEEP_DROP = 2.25
SWEEP_FLAT_FROM = 0.82        # the sweep reaches the deepest point this fraction of the way along
RADIUS_LEFT = 2.5
RADIUS_RIGHT = 1.25

# legs and joints
LEG_TOP_WIDTH = 3.25
LEG_FOOT_WIDTH = 1.5          # 1.75 at first; narrowed to leave the clamps wood along the LVL's edges
APRON_HEIGHT = 2.971          # the aprons as cut; drawn 3.0 at first
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
CLAMP_ROOM = 0.125            # wood the cutter leaves along the LVL's long edges, for the clamps
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
