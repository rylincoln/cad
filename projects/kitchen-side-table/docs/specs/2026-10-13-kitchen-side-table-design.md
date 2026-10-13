# Kitchen Side Table: Design

Date: 2026-10-13
Status: approved

## Intent

A small freestanding table beside the kitchen in a ~12 × 16' loft. It holds dishes and small
appliances (a toaster oven, a coffee maker: 15–35 lb each). Nobody sits at it. Its back stands
against the wall below a window; its front edge faces the room and sweeps in an asymmetric curve.
A shelf may be added underneath later.

Success means:

- A table about 32" tall that doesn't rack, wobble or tip with appliances on it.
- The base comes from stock the user already has: one LVL board and one piece of plywood.
- Every part is cut on the Shapeoko from files this project generates, with the bits the user owns,
  and nothing has to be flipped and re-registered.
- The files import into Carbide Create without surprises. The user builds the toolpaths there.

## Constraints (from the user)

| Item | Value |
|---|---|
| Top | Four cherry boards of finished (surfaced) stock, 24 × 8 × ¾", biscuited and glued edge to edge into a panel close to 32 × 24". The grain runs front to back. Sanding barely changes the thickness. |
| Legs | One LVL board, 1¾ × ~11⅞ × 32". The veneers run along its length. |
| Aprons | One piece of good plywood, 32 × 12 × ¾" (nominal) |
| Not allowed | Buying more LVL; anchoring the table to the wall |
| Height | About 32" |
| Machine | Shapeoko Pro XXL (about 33 × 33" work area) with a VFD spindle |
| Bits | ¼" three-flute end mill, 1" of flute. ¼" two-flute end mill, 1.4" of flute, run with ½" of shank in the collet and 2" sticking out. |
| Other tools | Biscuit joiner, drill, clamps. No roundover bit. |
| Dowels | Fluted birch dowel pins, 5/16" × 1½" |
| CAM | Carbide Create builds the toolpaths |

## Design decisions

All approved in the brainstorming session, the shapes on visual mockups.

- **Structure:** a freestanding four-leg table with aprons on all four sides. The LVL makes only the
  four legs; the plywood makes all four aprons. Rejected: more LVL (user), wall anchoring (user),
  an all-LVL base (every part at its minimum, no spare width).
- **Why aprons along the 32" length are essential:** the top's grain runs front to back, so its 32"
  length is across the grain, where ¾" cherry is weak and would sag under an appliance. The long
  aprons carry it.
- **Legs: flared top.** Slim, 1¾" square at the floor, sweeping out to 3¼" wide where they meet the
  aprons. The flare faces the room; the striped LVL edges face the ends. The shape shows from the
  front and back only, since the CNC cuts the profile through the board's thickness.
- **Top: the sweep.** The front edge runs from shallow at the **left end** (as seen from the room)
  up to the full depth near the right end, then turns a tight corner. The depth varies by 2¼".
- **Curve depth is limited by tipping.** The front legs have to stay near the front edge, so the
  edge never reaches more than 3½" past them.
- **Joinery:** every joint is a pocket in the one face of each leg that faces into the table, so the
  CNC cuts all of it with the leg lying flat. Side aprons sit in housings; long aprons lap onto the
  legs. All glued; the laps also screwed.
- **Top attachment:** four glued dowels, two at the middle of each long apron, fix the top along its
  front-to-back center line. Z-clip tabletop fasteners in grooves the CNC cuts along the aprons hold
  the rest down and let it move. Across its 32" the cherry grows and shrinks about ⅛–¼" with the
  seasons; fixed only at the middle, it moves half that each way, and the clips slide. Rejected:
  glued dowels all around (the user's first idea), which would lock that movement and risk cracking
  the top.
- **LVL in one setup, no flip:** the two-flute bit cuts through at full reach, with a clearance pass
  that widens the top of every outline slot so the bit's shank never rubs.

## Units and coordinates

Inches throughout. **Table coordinates**, used to design and check the assembly: x along the length
from the left end as seen from the room; y from the front toward the wall, with y = 0 at the front
edge's deepest point and y = D along the back edge; z up from the floor. The frame is right-handed,
so a plan drawn with y up is the table seen from above, with the wall at the top. "Left" and
"right" always mean as seen from the room.

**Sheet coordinates**, used in the cut files: origin at the lower-left corner of the stock as it sits
on the Shapeoko, x to the right, y away from the operator, seen from above. Parts go onto sheets by
rotation and translation only, never mirrored: the face that's up on the machine is the face seen
from above. Which face goes up is stated for each part below and tested.

## Inputs (`spec.py`)

`spec.py` holds every number. A **measured** block holds the real stock and bit, each value marked
measured or nominal. Everything else derives from it. While any value is still nominal, the build
prints a warning naming it. The top's width and depth can only be measured after the glue-up.

| Value | Measured (2026-10-13) or nominal |
|---|---|
| Top glue-up width × depth × thickness | nominal 32 × 24; thickness **0.75** from the finished stock |
| LVL length × width × thickness | **measured** 32.5 × 11.75 × 1.786 |
| Plywood length × width × thickness | **measured** 32 × 11.875 × 0.723 |
| Two-flute bit: flute length, stickout | **measured** 1.4; stickout 2.0 as the user sets it |
| Three-flute bit: flute length | 1.0, from the user |

Fixed design values:

| Name | Value |
|---|---|
| Table height | 32.0 |
| Top trim (CNC cuts the outline this far inside the glue-up on every side) | ⅛ |
| Leg inset from each end of the top | 1.0 |
| Back legs' back face from the wall | 3.0 |
| Front legs' front face, behind the deepest point of the front edge | 3.5 |
| Leg width: at the aprons / at the floor; leg thickness | 3.25 / 1.75; the LVL's thickness |
| Apron height | 3.0 |
| Side-apron housing: from the leg's outer face, depth | 0.375, 0.75 |
| Long-apron lap: length along the leg, depth | 1.75, the plywood's thickness |
| Fit clearance on the housing width | 0.005 |
| Sweep drop; left / right corner radius | 2.25; 2.5 / 1.25 |
| Clip groove: width, depth, upper wall below apron top | 0.25, 0.3125, 0.375 (set from the clips bought) |
| Dowels: diameter, length; apart, centered on each long apron | 0.3125, 1.5; 2.0 |
| Dowel holes: cherry left above the top's hole; how much deeper the two holes are than the dowel is long, for glue | 0.25; 1/16. Nominal holes: 0.5 into the top, 1.0625 into the apron |
| Bit diameter | 0.25 |

With these values the finished top is 31.75 × 23.75, the legs are 31.25 long and 1.786 thick, the
housings are 0.728 wide, and the laps are 0.723 deep.

## Geometry

### Top (`top.py`)

- Finished size W × D = glue-up − 2 × trim in each direction. The back edge and both ends are
  straight; the back corners are square.
- **Front edge (the sweep):** y(x) = 2.25 · (1 − sin(π/2 · min(x / (0.82 W), 1))). That is 2.25
  behind the deepest point at the left end, coming forward to the deepest point (y = 0) at 82% of
  the way along and straight from there.
- **Front corners:** filleted, 2.5 on the left and 1.25 on the right.
- Nominal result: 21.5 deep at the left end, 23.75 at the right.

### Legs (`legs.py`)

Leg length L = 32 − top thickness. In leg coordinates, seen from the leg's **inside face** (the face
toward the middle of the table), v runs from the foot (0) to the top (L) and u runs across the width
from the outer edge (0).

- **Outline:** the outer edge is straight. The inner edge is u = w(v), with w = 3.25 for v ≥ L − 3
  (the apron zone) and w = 1.75 + 1.5 · (v / (L − 3))³ below it. The flare meets the straight top
  at the aprons' bottom edge.
- **Housing** for the side apron: u from 0.375 to 0.375 + plywood thickness + clearance, v from
  L − 3 to L (open at the top), 0.75 deep. A dogbone at each bottom corner.
- **Lap** for the long apron: u from 1.5 to 3.25 (open at the inner edge), v from L − 3 to L (open
  at the top), as deep as the plywood is thick. A dogbone at its bottom-outer corner.
- **Dogbones:** a circle of the bit's radius whose edge passes through the corner, centered on the
  corner's bisector, so a ¼" bit leaves the corner square enough for the plywood's square corners.
- **Handedness:** seen from the inside face, the front-left and back-right legs have the flare on
  the left; the front-right and back-left legs are their mirror image. (Standing behind the table,
  looking at the front-left leg's inside face, the table's middle is to your left.)

### Aprons and coupon (`aprons.py`)

All plywood parts are 3.0 tall and as thick as the plywood.

- **Long aprons (front, back):** length W − 2 × (1.0 + 3.25 − 1.75). Nominal 26.75.
- **Side aprons (left, right):** they span between the legs' inside faces and run 0.75 into each
  housing. Length = (front-leg front face − back-leg back face) − 2 × leg thickness + 2 × 0.75.
  15.18 with the measured LVL.
- **Clip groove** along each apron's inside face, centered 0.5 below its top edge. It stops 0.5 short
  of the part of the apron that goes into a leg (0.5 + lap or housing depth from each end).
- **Dowel holes:** two in the top edge of each long apron, centered on its thickness, 1.0 either side
  of its middle, 1.0625 deep nominal. They reach down through the groove's height, so each long apron's
  groove stops 0.5 short of them and becomes two grooves. The side aprons have one groove each.
- **Fit-test coupon:** 3 × 1.75.

### Frame (`frame.py`)

This module places every part in table coordinates.

- **Legs:** outer faces 1.0 in from each end. With t the leg thickness, front legs from y = 3.5 to
  3.5 + t, and back legs from y = D − 3.0 − t to D − 3.0. Each leg's inside face faces the middle
  of the table.
- **Long aprons:** set into the laps, flush with the legs' inside faces. Front apron from
  y = 3.5 + t − plywood thickness to 3.5 + t; back apron from y = D − 3.0 − t to that + plywood
  thickness.
- **Side aprons:** outer face 1.375 in from each end of the top.
- **Heights:** apron tops flush with the leg tops, and both against the underside of the top.

## Stock layouts (`sheets.py`)

| Sheet | Stock | Face up | Layout |
|---|---|---|---|
| Job 1: aprons | Plywood | The plywood's worse face: the aprons' inside faces | Three 3" strips with 0.25 between parts and 0.125 from the edges: back long apron, front long apron, then both side aprons end to end. The coupon (1.75 tall) goes in the 1.875" strip left over. |
| Job 2: fit test | Any scrap ≥ 1" thick, about 6 × 4 | — | One housing pocket and one lap pocket, as cut in the legs, each long enough for the coupon's 1.75" side. |
| Job 3: legs | LVL | The legs' inside faces, so the LVL's better face goes down and shows on the front legs' fronts | Two head-to-toe pairs along the board's length, centered. One pair is the front-left and back-right legs, the other is front-right and back-left. Parts at least 0.4 apart; outer edges 0.125 from the board edges. About 0.3" of the measured 11.75" width is spare. |
| Job 4: top | Cherry glue-up | The top's show face, front (curved) edge toward the operator | The outline 0.125 inside the glue-up on every side. The shallow end is at the left. |

## Rules (`rules.py`, enforced by the build)

`check_table(...)` returns plain-English problems; an empty list means the table can be cut and
assembled. The build writes nothing if it isn't empty.

1. **Every part fits its stock.** Each part lies inside the stock with the edge margin, and parts are
   at least the sheet's gap apart (0.25 on the plywood, 0.4 on the LVL). Every stock fits the
   machine's 33 × 33 work area.
2. **The bit can cut every pocket.** Within the part, each pocket equals itself opened by the bit's
   radius, so there is no corner the ¼" bit can't reach. Each fit-test pocket takes the coupon.
3. **Joints fit, as assembled.** Each apron, where it's placed, enters a leg only inside a pocket and
   no deeper than that pocket; each leg holds two aprons; no two aprons run into each other. Every
   cut is no deeper than the flute of the bit that makes it: 1.0 for the plywood, fit test and
   top, 1.4 for the LVL's pockets.
4. **The top covers the legs.** Seen from above, every leg's top is at least 0.5 inside the top's
   outline.
5. **It won't tip.** The deepest point of the front edge is at most 3.5 past the front legs. The
   empty table also needs at least 50 lb pressing down there to tip forward. That figure uses each
   part's volume and the densities cherry 35, LVL 38 and plywood 43 lb/ft³. Nominal: about 64 lb.
6. **The shank never rubs.** The clearance pass is at least (full depth − flute length) + 0.1 deep,
   the first finishing stage stops at flute length − 0.1 so the flutes finish the top of the edge,
   and the collet nut clears the top of the LVL by at least 0.15 at full depth. Full depth is the
   LVL's thickness + 0.02.
7. **The height is right.** Leg length + top thickness = 32.0 ± 1/32, and all four legs are the same
   length.
8. **The shallow end is on the left.** It is at the left of the table as seen from the room, and at
   the left of the job 4 sheet as the operator sees it. This guards against mirroring the top.
9. **The grooves stay out of the joints.** No clip groove reaches into a housing or lap region, or
   comes within 0.5 of a dowel hole.
10. **The dowels fit.** The hole in the top leaves 0.25 of cherry above it, so it follows the
   measured thickness, and the apron's hole takes the rest of the dowel plus 1/16 for glue. At least
   ⅜ of each dowel must go into the top, and each apron hole leaves at least 0.15 of plywood on
   either side.

## Files and layers (`export.py`, `build.py`)

`build.py` checks the table, then writes `out/`. Every DXF is in inches and in sheet coordinates, and
is validated with `cadgen.drawing_checks.validate_dxf_file`. The SVGs match the DXFs.

| File | Job |
|---|---|
| `aprons.svg` / `.dxf` | 1: plywood aprons and coupon |
| `fit_test.svg` / `.dxf` | 2: test pockets in scrap |
| `legs.svg` / `.dxf` | 3: LVL legs |
| `top.svg` / `.dxf` | 4: cherry top |
| `table.step` / `.glb` | 3D model of the assembled table, for the CAD Viewer |
| `previews/*.png` | Snapshots of each DXF, with the part names, for the README |

| Layer | Colour | Toolpath in Carbide Create |
|---|---|---|
| `REFERENCE_STOCK` | grey | None. The stock's outline, for lining up. |
| `POCKET_HOUSING` | orange | Pocket, ¾" deep |
| `POCKET_LAP` | yellow | Pocket, as deep as the plywood is thick |
| `GROOVE_CENTERLINE` | red | The groove's centerline, an open line. Contour, no offset, 5/16" deep. (cadgen's DXF check allows open lines only on layers it reads as not cut-through; "centerline" is one.) |
| `CLEARANCE` | cyan | The leg outline offset 0.125 outward. Contour, outside, to the depth rule 6 sets (0.51" with the measured LVL and bit). |
| `ROUGH` | magenta | The outline offset 0.02 outward. Contour, outside, full depth. |
| `CUT_OUTSIDE` | blue | The part outline. Contour, outside, full depth. On the LVL it is two passes: to the flute length − 0.1 (1.3"), then from there to full depth. |

The part names appear only in the previews, not in the cut files.

## Machining (README)

Starting settings; tune by sound and chip.

| Job | Bit | Settings |
|---|---|---|
| 1, 2 | ¼" three-flute, 1" flute | 16,000 RPM, 50 IPM, 15 IPM plunge (ramp), 0.1" per pass. Tabs on the plywood parts. |
| 3 | ¼" two-flute, 2" stickout, ½" in the collet | 12–14,000 RPM, 40 IPM, 10 IPM plunge (ramp), 0.05" per pass. Vacuum and air throughout. The cuts go in this order: pockets, clearance, rough, finish. About 5 hours. |
| 4 | ¼" three-flute | As jobs 1 and 2, with a full-depth finishing pass on the outline |

- **Hold-down:** painter's tape and CA glue under the LVL and the top, so neither needs tabs; their
  cuts go 0.02" into the spoilboard. The plywood is held by its tabs.
- **Zero:** X and Y at the lower-left corner of the stock, Z at the top of the stock.
- **Job 3 grip:** draw a marker line on the shank at the collet nut, and check it between the cut
  steps. Watch the first full-depth pass for collet-nut clearance.

## Assembly (README)

1. **Glue up the top.** Arrange the boards and mark the front ends. Keep the biscuits between 2" and
   19" from the back ends so the cut doesn't expose them. Sand the panel smooth (the boards are finished
   stock, so it needs no flattening), then measure its width and depth, enter them in `spec.py` and
   rebuild.
2. **Cut jobs 1 to 4.** Run the fit test before the LVL, adjusting the clearance and rebuilding if
   the coupon doesn't slide in snug by hand. Mark each leg's name on it in pencil as it comes off.
3. **Dry-fit the base.**
4. **Glue the end frames:** each end's front leg, back leg and side apron. Check they're square.
5. **Drill the long aprons' dowel holes**, before they go in: two per apron in the top edge, 5/16",
   1.0 either side of the middle, centered on the plywood, 1-1/16" deep (the build prints the depth). A doweling jig keeps them
   square. Then **glue the long aprons into their laps**, with two screws each from inside.
6. **Finish:** ease every edge by sanding. Seal the cherry's end-grain front edge before finishing
   so it doesn't darken more than the face. Polyurethane on every face, the top's underside as
   well as its show face, so both sides take up moisture alike and the top stays flat.
   Keep finish out of the dowel holes and off the 2" of apron edge between them.
7. **Attach the top.** Lay it upside down. Put dowel centers in the four apron holes, set the base
   upside down on the top in its place (legs' outer faces 1" in from each end, back legs' back faces
   3" from the back edge), and press to mark the top. Drill the four marks 5/16" × ½" deep (as printed by the build), with a
   stop collar so it can't go through. Glue the dowels in, with glue only in the holes and on the 2"
   of apron edge between them; glue anywhere else would lock the top. Fit eight Z-clips (one per
   groove on the long aprons, two per side apron; buy a pack of ten) with ⅝" screws.

## Verification before handoff

- The whole test suite passes; tests were written first.
- `build.py` runs clean with the nominal values, and `check_table` returns `[]`.
- Every DXF passes cadgen's validator and opens with its layers.
- The previews and the 3D model have been looked at: the sweep's shallow end is on the left from the
  room, the flare faces the room, the aprons sit in their pockets, and the dowels sit at the middle
  of the long aprons.
- The README's settings, depths and layer names match the files.

## Out of scope

- The shelf, though the slim legs leave room to add cleats for one later.
- G-code (Carbide Create makes it) and the finish itself.
- A shared DXF package. The memorial's exporter is built around its plate, so this project has its
  own small exporter. If a third project needs one, extract it then.

## Risks

- **Collet grip:** ½" of a ¼" shank in the collet is less than the usual ¾". An upcut bit can pull
  out under load. The mitigations are the marker line, a clean and properly tightened collet, and
  light passes.
- **Collet-nut clearance** is about 0.19" at full depth with the 1.786" LVL, so the LVL must lie flat,
  the tape be thin, and the stickout be a full 2". Check it with the spindle off before the first
  full-depth pass.
- **Seasonal movement:** the top still moves ⅛–¼" across its width, half each way from the dowels.
  Let the boards sit in the loft for a week or two before the glue-up, keep glue off the apron edges
  away from the dowels, and finish the underside like the top so it takes up moisture evenly.
- **Glue-up smaller than nominal:** everything rescales from the measured block, and the rules catch
  any part that no longer fits.
- **Plywood thicker or thinner than ¾":** the housings, laps and coupon all follow the measured
  thickness.

## Revisions

- **2026-10-13:** the top is attached with four glued dowels at the middle of the long aprons
  instead of two screwed center blocks, at the user's request. The long aprons' grooves split around
  the dowels. Rules 9 and 10 cover them.
- **2026-10-13 (planning):** table coordinates are right-handed, with y from the front edge toward
  the wall, so plans, sheets and the 3D model are never mirrored; the leg handedness is corrected to
  match; rule 1 also checks the machine's work area; the finish is polyurethane on every face.
- **2026-10-13 (planning, prototype):** the groove layer is `GROOVE_CENTERLINE`; the dowel holes'
  depths follow the measured top; rules 2, 3 and 10 are restated as the prototype checks them; the
  tipping figure is about 64 lb.
