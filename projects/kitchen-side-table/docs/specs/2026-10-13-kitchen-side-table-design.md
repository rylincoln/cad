# Kitchen Side Table: Design

Date: 2026-10-13
Status: approved in brainstorming, awaiting review of this written spec

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
| Top | Four cherry boards, 24 × 8 × ~¾", biscuited and glued edge to edge into a ~32 × 24" panel. The grain runs front to back. |
| Legs | One LVL board, 1¾ × ~11⅞ × 32". The veneers run along its length. |
| Aprons | One piece of good plywood, 32 × 12 × ¾" (nominal) |
| Not allowed | Buying more LVL; anchoring the table to the wall |
| Height | About 32" |
| Machine | Shapeoko Pro XXL (about 33 × 33" work area) with a VFD spindle |
| Bits | ¼" three-flute end mill, 1" of flute. ¼" two-flute end mill, ~1½" of flute, run with ½" of shank in the collet and 2" sticking out. |
| Other tools | Biscuit joiner, drill, clamps. No roundover bit. |
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
- **Top attachment:** Z-clip tabletop fasteners in a groove the CNC cuts along each apron, plus a
  fixed block at the middle of each long apron.
- **LVL in one setup, no flip:** the two-flute bit cuts through at full reach, with a clearance pass
  that widens the top of every outline slot so the bit's shank never rubs.

## Units and coordinates

Inches throughout. **Table coordinates**, used to design and check the assembly: x along the length
from the left end as seen from the room, y from the wall toward the room, z up from the floor.
"Left" and "right" always mean as seen from the room.

**Sheet coordinates**, used in the cut files: origin at the lower-left corner of the stock as it sits
on the Shapeoko, x to the right, y away from the operator, seen from above. Parts go onto sheets by
rotation and translation only. Nothing is mirrored by accident; the one face-down choice per part is
stated below and tested.

## Inputs (`spec.py`)

`spec.py` holds every number. A **measured** block holds the real stock, entered by the user after
the glue-up and before any cutting. Everything else derives from it. Until it is filled in, the
build uses these nominal values and prints a warning that the sizes are not measured:

| Measured value | Nominal |
|---|---|
| Top glue-up width × depth × thickness | 32 × 24 × 0.75 |
| LVL length × width × thickness | 32 × 11.875 × 1.75 |
| Plywood length × width × thickness | 32 × 12 × 0.75 |
| Two-flute bit: flute length, stickout | 1.5, 2.0 |

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
| Bit diameter | 0.25 |

With the nominal values the finished top is 31.75 × 23.75 and the legs are 31.25 long.

## Geometry

### Top (`top.py`)

- Finished size W × D = glue-up − 2 × trim in each direction. The back edge and both ends are
  straight; the back corners are square.
- **Front edge (the sweep):** depth(x) = D − 2.25 + 2.25 · sin(π/2 · min(x / (0.82 W), 1)). That is
  D − 2.25 at the left end, rising to D at 82% of the way along and flat from there.
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
  the right; the front-right and back-left legs are their mirror image.

### Aprons, blocks and coupon (`aprons.py`)

All plywood parts are 3.0 tall and as thick as the plywood.

- **Long aprons (front, back):** length W − 2 × (1.0 + 3.25 − 1.75). Nominal 26.75.
- **Side aprons (left, right):** they span between the legs' inside faces and run 0.75 into each
  housing. Length = (front-leg front face − back-leg back face) − 2 × leg thickness + 2 × 0.75.
  Nominal 15.25.
- **Clip groove** along each apron's inside face, centered 0.5 below its top edge. It stops 0.5 short
  of the part of the apron that goes into a leg (0.5 + lap or housing depth from each end).
- **Center blocks:** two, 2 × 1.75. Each is glued to the inside face of a long apron at its middle,
  top flush, and screwed up into the top from below through a counterbored hole.
- **Fit-test coupon:** 3 × 1.75.

### Frame (`frame.py`)

This module places every part in table coordinates.

- **Legs:** outer faces 1.0 in from each end. Back legs from y = 3.0 to 4.75; front legs with their
  front face at y = D − 3.5. Each leg's inside face faces the middle of the table.
- **Long aprons:** set into the laps, flush with the legs' inside faces. Front apron from y = (front
  face − 1.75) to + plywood thickness; back apron from y = 4.75 − plywood thickness to 4.75.
- **Side aprons:** outer face 1.375 in from each end of the top.
- **Heights:** apron tops flush with the leg tops, and both against the underside of the top.

## Stock layouts (`sheets.py`)

| Sheet | Stock | Face up | Layout |
|---|---|---|---|
| Job 1: aprons | Plywood | The plywood's worse face: the aprons' inside faces | Three 3" strips with 0.25 between parts and 0.125 from the edges: back long apron, front long apron, then both side aprons end to end. The coupon and both blocks (1.75 tall) go in the 2" strip left over. |
| Job 2: fit test | Any scrap ≥ 1" thick, about 6 × 4 | — | One housing pocket and one lap pocket, as cut in the legs, each long enough for the coupon's 1.75" side. |
| Job 3: legs | LVL | The legs' inside faces, so the LVL's better face goes down and shows on the front legs' fronts | Two head-to-toe pairs along the board's length, centered. One pair is the front-left and back-right legs, the other is front-right and back-left. Parts at least 0.4 apart; outer edges 0.125 from the board edges. |
| Job 4: top | Cherry glue-up | The top's show face, front (curved) edge toward the operator | The outline 0.125 inside the glue-up on every side. The shallow end is at the left. |

## Rules (`rules.py`, enforced by the build)

`check_table(...)` returns plain-English problems; an empty list means the table can be cut and
assembled. The build writes nothing if it isn't empty.

1. **Every part fits its stock.** Each part lies inside the stock with the edge margin, and parts are
   at least the sheet's gap apart (0.25 on the plywood, 0.4 on the LVL).
2. **The bit can cut every pocket.** Each pocket equals itself opened by the bit's radius, so there
   is no corner the ¼" bit can't reach. Each pocket also contains the plywood end it receives: a
   full rectangle of the plywood's thickness by 3.0, or 1.75 for the test pocket.
3. **Joints fit.** The housing width is the plywood's thickness plus the clearance. The lap depth is
   the plywood's thickness. Every pocket is shallower than the shortest flute.
4. **The top covers the legs.** Seen from above, every leg's top is at least 0.5 inside the top's
   outline.
5. **It won't tip.** The deepest point of the front edge is at most 3.5 past the front legs. The
   empty table also needs at least 50 lb pressing down there to tip forward. That figure uses each
   part's volume and the densities cherry 35, LVL 38 and plywood 43 lb/ft³. Nominal: about 60 lb.
6. **The shank never rubs.** The clearance pass is at least (full depth − flute length) + 0.1 deep,
   and the collet nut clears the top of the LVL by at least 0.15 at full depth. Full depth is the
   LVL's thickness + 0.02.
7. **The height is right.** Leg length + top thickness = 32.0 ± 1/32, and all four legs are the same
   length.
8. **The shallow end is on the left.** It is at the left of the table as seen from the room, and at
   the left of the job 4 sheet as the operator sees it. This guards against mirroring the top.
9. **The grooves stay out of the joints.** No clip groove reaches into a housing or lap region.

## Files and layers (`export.py`, `build.py`)

`build.py` checks the table, then writes `out/`. Every DXF is in inches and in sheet coordinates, and
is validated with `cadgen.drawing_checks.validate_dxf_file`. The SVGs match the DXFs.

| File | Job |
|---|---|
| `aprons.svg` / `.dxf` | 1: plywood aprons, blocks, coupon |
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
| `GROOVE` | red | The groove's centerline. Contour, no offset, 5/16" deep. |
| `CLEARANCE` | cyan | The leg outline offset 0.125 outward. Contour, outside, ⅜" deep. |
| `ROUGH` | magenta | The outline offset 0.02 outward. Contour, outside, full depth. |
| `CUT_OUTSIDE` | blue | The part outline. Contour, outside, full depth. On the LVL it is two passes: to 1.4", then from 1.4" to full depth. |

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
   19" from the back ends so the cut doesn't expose them. Flatten the panel, then measure it and
   enter the measured block in `spec.py`, along with the LVL and plywood. Rebuild.
2. **Cut jobs 1 to 4.** Run the fit test before the LVL, adjusting the clearance and rebuilding if
   the coupon doesn't slide in snug by hand. Mark each leg's name on it in pencil as it comes off.
3. **Dry-fit the base.**
4. **Glue the end frames:** each end's front leg, back leg and side apron. Check they're square.
5. **Glue the long aprons into their laps**, with two screws each from inside. Glue on the center
   blocks.
6. **Finish:** ease every edge by sanding. Seal the cherry's end-grain front edge before finishing
   so it doesn't darken more than the face.
7. **Attach the top.** Lay it upside down and center the base on it. Fit eight Z-clips (two per
   apron, buy a pack of ten) with ⅝" screws, and screw the two center blocks up into the top.

## Verification before handoff

- The whole test suite passes; tests were written first.
- `build.py` runs clean with the nominal values, and `check_table` returns `[]`.
- Every DXF passes cadgen's validator and opens with its layers.
- The previews and the 3D model have been looked at: the sweep's shallow end is on the left from the
  room, the flare faces the room, and the aprons sit in their pockets.
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
- **Collet-nut clearance** is about 0.23" at full depth, so the LVL must lie flat and the tape be thin.
- **Glue-up smaller than nominal:** everything rescales from the measured block, and the rules catch
  any part that no longer fits.
- **Plywood thicker or thinner than ¾":** the housings, laps and coupon all follow the measured
  thickness.
