# Copper Memorial Plaque: Design

Date: 2026-10-11
Status: approved (revised after measuring the font's real outlines; see "Revision 1")

## Intent

A memorial for **Mary Theresa** and **James Guinn Fitzgerald**, who died together in a
house fire on December 30, 2025. A pierced copper plate is the centerpiece of a ~36"
round redwood slice. Other people will inlay and tile around the plate; this project
covers only the copper.

Success means:

- A dignified, clearly legible plate that looks considerably better than the original
  printout.
- The final sheet is cut cleanly on the first attempt, after one practice cut.
- The files import into Carbide Create without surprises, so the user can build the
  toolpaths there and send the G-code with Carbide Motion.

## Constraints (from the user)

| Item | Value |
|---|---|
| Material | Copper sheet, **0.020"** thick (measured) |
| Practice sheet | 13 × 8" (assumed also 0.020") |
| Final sheet | about 18 × 10" |
| Space on the slice | about 16" wide × 10" tall, centered |
| Machine | Shapeoko Pro with a VFD spindle. The slice does not fit on the machine. |
| Finest bit | Tapered ball nose, R1/64" × 1.5" × 1/4" (a 1/32" ball tip); Carbide Create's 1/32" ball mill preset |
| Hold-down | Sheet taped or glued flat to a wasteboard (painter's tape plus CA recommended) |
| CAM | Carbide Create builds the toolpaths, Carbide Motion runs the G-code |
| Mounting | Flexible adhesive plus #16 copper escutcheon pins through 8 holes |
| Environment | **Outdoors** |

## Design decisions

All of these were approved in the brainstorming session, most of them on the visual mockups.

- **Style: pierced plaque.** One copper plate with the lettering cut through it, so the
  redwood shows through as the text. The letter centers that drop out are saved and
  glued back onto the wood in place: the counters of A, B, D and 0. In the thickened names
  and dates, the narrow openings of r, p, 6 and 9 also close, so their centers drop out
  too: 23 pieces on the final plate, 19 on the practice piece. The surname's R stays open. The "cut-out letters
  glued to the wood" alternative was considered and dropped.
- **Plate shape:** a true ellipse, 16.000 × 9.500".
- **Lettering:** Cinzel Bold (Roman inscriptional capitals; lowercase letters render as
  small capitals).
- **Text:** months abbreviated without periods. The date they died is shown once, beneath
  both of them. The exact strings:

  | Line | Text |
  |---|---|
  | Surname | `FITZGERALD` |
  | Left name | `Mary Theresa` |
  | Right name | `James Guinn` (G confirmed by the user; Guinn is his middle name) |
  | Left date | `Feb 6, 1935` |
  | Right date | `Apr 19, 1939` |
  | Shared date | `December 30, 2025` |

- **Decoration:** an **engraved border** following the oval, plus a **trinity knot
  (triquetra)** cut through the plate and centered between the two names.
- **Mounting holes:** 8 pin holes on the border line.

## Geometry

Units are inches. The origin is the plate center, with +y up.

### Plate and border

- **Plate outline:** an ellipse with semi-axes 8.000 and 4.750.
- **Border:** the inward offset of the outline by **0.375"**, a true offset curve (not a
  smaller ellipse). It is engraved, not cut through.
- **Pin holes:** 8 circles of **Ø0.070"** (sized for #16 escutcheon pins), centered on the
  border curve at equal arc-length spacing, the first at top center (0, +4.375).

### Lettering

Sizes are capital-letter heights. The positions are the approved mockup's baselines.

| Line | Cap height | Em size | Tracking | Thicken | Center x | Baseline y |
|---|---|---|---|---|---|---|
| FITZGERALD | 1.165" | 1.664" | +0.045 em | none | 0 | +0.966 |
| Mary Theresa / James Guinn | 0.540" | 0.771" | 0 | 0.012" | ∓column x | −0.098 |
| Feb 6, 1935 / Apr 19, 1939 | 0.475" | 0.679" | 0 | 0.012" | ∓column x | −1.001 |
| December 30, 2025 | 0.490" | 0.700" | 0 | 0.012" | 0 | −2.082 |

- **Glyph outlines:** from `fonts/Cinzel-Bold.ttf`, with the font's pair kerning (GPOS
  `kern`) applied. Each glyph is filled with the exact nonzero-winding rule, so
  overlapping and reversed contours (the "1" has one) come out right.
- **Thicken:** the names and dates are grown outward by **0.012"** on every edge (mitred
  corners), which lifts their thinnest strokes from 0.026–0.032" to about 0.05".
- **Per-pair spacing:** after thickening, each glyph is pushed right just far enough that
  at least **0.06"** of copper separates it from the glyphs already set on the line. Only
  pairs that were too tight move.
- **Closed loops:** where thickening closes a loop (the small r, p, 6, 9 and B) with a wall
  thinner than 0.05", that wall is grown just enough to reach 0.05" (+0.005"). It grows
  into the letter center, or both ways when it separates two centers, and never past the
  letter's outline.
- **Centering:** each line is centered on its ink, not its advance width.
- **Column x:** half the widest column, plus half the knot's cut width, plus a **0.24"**
  space between the knot's cut edge and the nearest letter (about ±4.12", exactly the
  approved preview; its "0.30"" was measured from the knot's centerline extent).
- **Positions:** the baselines are the approved mockup's. The checks below are the
  authority, not these reference numbers.

### Trinity knot

- **Size and orientation:** 1.20" tall, one leaf pointing up, centered at (0, −0.32).
- **Centerline:** three circular arcs, each swinging through the middle between two leaf
  tips. The arcs' circles are placed so the two arcs meeting at each tip enclose
  **90°**. Leaf tips sit at radius 2ρ, with ρ scaled to the target height.
- **Band:** the centerline widened to **0.10"** (±0.05"). This is the cut-through part.
- **Over/under:** alternating along the line, 3 crossings. At each crossing the strand
  that passes under stops short of the strand that passes over, leaving a copper
  **bridge of 0.08"** on each side. Each gap is cut only from the under strand's own
  band, so neighboring crossings can't disturb each other.
- **Consequence:** the band becomes exactly **3 cutout pieces**, and the bridges keep the
  leaf centers and the middle triangle attached to the plate, so the knot drops no loose
  pieces.

## Cutting rules (enforced by the build)

The build fails with a clear message if any rule fails.

1. **Narrowest slot: 0.05".** No cutout has a neck narrower than 0.05": shrinking any
   cutout by 0.025" never splits it, makes it vanish, or opens a wall around a letter
   center. Sharp corners are exempt, since they simply round off to about 0.02" radius.
2. **Narrowest copper: 0.06"** between any two separate cutouts, which covers neighboring
   letters and the knot's bridges (designed at 0.08").
3. **Loose pieces:** every letter center that drops out is at least 0.06" across, so it
   can be handled and glued back. Pointed copper corners, such as wedges inside the knot
   leaves or the triangle in an A, are exempt.
4. **Every character present:** each line's cut geometry contains one cutout region per
   visible character, so a glyph can never silently vanish.
5. **Clearances:**
   - every lettering and knot cut stays at least **0.30"** from the border line;
   - the border sits 0.375" from the plate edge by construction;
   - the pin holes are centered on the border line.
6. **Built-in DXF checks** (`cadgen.drawing_checks.validate_dxf_file`): cut layers
   contain only closed profiles; no duplicate geometry; units set; nothing empty.
7. **Text check:** the six strings above are asserted exactly.

## Files and layers

Each sheet's file uses these layers:

| Layer | Contents | Carbide Create toolpath | Order |
|---|---|---|---|
| `ENGRAVE_BORDER` | border curve | Contour, no offset, **0.006"** deep | 1st |
| `CUT_INSIDE` | letters, knot, pin holes | Contour, inside, through | 2nd |
| `CUT_OUTSIDE` | plate outline | Contour, outside, through | last |
| `REFERENCE_SHEET` | sheet rectangle (not cut) | none, for alignment only | n/a |

Geometry is placed in sheet coordinates, with the origin at the sheet's lower-left corner.

- **Final:** on an 18 × 10" sheet, the oval centered at (9, 5).
- **Practice:** on a 13 × 8" sheet, the window placed with 0.25" margins.

Files written to `out/`:

| File | Purpose |
|---|---|
| `final.svg`, `final.dxf` | Final plate. Both are in inches and hold only closed polylines (curves as fine straight segments, within 0.0005" of the true curve) and circles, the forms Carbide Create imports most reliably. Use either. |
| `practice.svg`, `practice.dxf` | Practice window |
| `plate_outline.svg`, `plate_outline.dxf` | The oval's edge only, for the inlay and tile worker |
| `final_fullsize.pdf` | 1:1 print on 11 × 17" landscape paper, with a 1" scale bar, for checking size and look on the slice |

The sources are a small Python package that runs in the cadgen environment (installed with
text-to-cad, run through `uvx`). It builds all the geometry with **shapely**, writes the DXF
with **ezdxf** (`LWPOLYLINE` and `CIRCLE` entities, `$INSUNITS` = inches), writes the SVG
directly, and draws the PDF with **matplotlib**. cadgen's own tools validate the DXF,
render snapshots of it, and show it in the CAD Viewer. The font is `fonts/Cinzel-Bold.ttf`
(Google Fonts' static weight-700 Cinzel) with its `OFL.txt` license. Every output is
written from the same geometry.

## Practice sheet

- **Window:** 12.5 × 7.5", taken from the final design at x ∈ [−8.0, 4.5], y ∈ [−3.75, 3.75]
  in plate coordinates.
- **Outline:** the ellipse clipped to that window, so the oval's left end and straight
  trim edges elsewhere.
- **Content:** the same coordinates and shapes as the final. A letter, the knot or a pin
  hole is kept only if it lies entirely inside the window, at least 0.25" from the
  window's edges. The engraved border is clipped to stay 0.25" inside the trim edges.
- **What it tests:** the large surname letters, the smallest date text, the knot's
  bridges, pin holes, the engraved border, the curved edge, hold-down, depth and feed
  settings, and getting the plate off the wasteboard.

## Recommended cut settings

These are starting points to tune on the practice sheet; the user sets them in Carbide
Create.

- **Tool:** Carbide Create's 1/32" ball mill preset, which matches the R1/64" tip. At these
  depths the taper only widens the cut about 0.003", which is negligible.
- **Through-cuts:** about **0.043"** deep: the copper (0.020"), plus the ball's radius
  (0.016") so the full width breaks through, plus about 0.005" into the tape and
  wasteboard.
- **Feeds and speeds:** about 0.005" per pass (9 passes), about 18,000 RPM, about 10 IPM,
  3 IPM plunge, with cutting fluid.
- **Engraving:** 0.006" deep, which leaves a groove about 0.025" wide with the ball tip.
- **Order:** engrave, then inside cuts, then the outline last.
- **Hold-down:** keep the sheet fully adhered during the cut. Release it by peeling or
  with acetone, never by prying, since the 0.020" plate bends easily.

## Verification before handoff

- All the build checks above pass.
- `ezdxf` measurements of the DXF:
  - outline extents 16.000 × 9.500" (practice window 12.500 × 7.500");
  - 8 holes, Ø0.070";
  - each layer holds the expected entities.
- The SVG's extents are checked the same way.
- A count of closed cut profiles and of loose pieces (letter centers that drop out) is
  reported to the user.
- Every file is rendered with `cadgen dxf snapshot`, compared against the approved
  mockup, and shared as a CAD Viewer link.
- **User's import check:** after importing into Carbide Create, the oval must measure
  16.000 × 9.500" (practice 12.5 × 7.5"). If it doesn't, the import scale is wrong.

## Out of scope

- Generating G-code, and any CAM settings beyond the recommendations above.
- The redwood slice, the inlay and tile work, and mounting hardware.
- The cut-out-letters design (dropped).
- Finishing and outdoor mounting materials. Advice comes with the handoff: an outdoor
  clear coat versus natural patina, outdoor-rated flexible adhesive, and copper-only pins
  to avoid corrosion between different metals.

## Revision 1 (during planning)

Measuring Cinzel's real outlines at the plaque's sizes showed two problems with the
approved preview:

- **Hairlines too thin:** the names' and dates' thinnest strokes were 0.026–0.032",
  narrower than the 0.035" bit.
- **Letters touching:** several pairs touched or nearly touched (MA, RE and AM in the
  names, RA in the surname).

The user approved the fix on a side-by-side render of the real cut geometry:
- thicken the small text by 0.012";
- open only the pairs that are too tight, to 0.06" of copper;
- set the narrowest-slot rule to 0.05" and the narrowest-copper rule to 0.06";
- make the knot 1.20" tall, with a 0.24" edge-to-edge gap to the names (quoted as 0.30", measured from the knot's centerline).

The geometry engine moved from build123d to shapely, with polyline and circle output, for
Carbide Create compatibility.

## Revision 2 (final review)

The whole-branch review found that thickening closed the loops of the small r, p, 6, 9 and
B with walls of only 0.012–0.030", thinner than the bit. Rule 1's piece count could not see
a wall vanishing around a letter center, so 12 letters passed. Rule 1 now also requires
every letter center to stay surrounded. Those walls are grown inward to 0.05", which keeps
80–92% of each center and leaves every outline unchanged. The spec's choice to close these
loops (23 loose pieces) stands.

## Revision 3 (SendCutSend in brass)

The plate can also be ordered from SendCutSend in 0.040" brass. SendCutSend doesn't return
pieces that fall free. 21 of the 23 letter centers are also below their 0.375 × 0.25" minimum
part size, so they can't be ordered as separate parts. The user chose stencil ties:
- Each letter center stays joined to the plate by a 0.06" strip of brass across the stroke,
  left at the stroke's thinnest square crossing and centered along it.
- D and 0 get two ties, top and bottom; every other letter gets one.
- No tie may leave a scrap of stroke narrower than 0.05".

The laser file (`final_sendcutsend.dxf`) holds only the through-cuts, on one layer, with the
plate's lower-left corner at the origin. The build checks it with every rule plus one more:
no letter center is left to drop out.

SendCutSend can't engrave a 16 × 9.5" part (their limit is 12.1 × 12.1") and doesn't etch
brass. The user engraves the border on the Shapeoko after delivery from `border_engrave`
(stock = the plate's own outline, XY zero at the center), lining up on the pin holes.
The Carbide Create files and the glue-back design are unchanged.

## Revision 4 (script surname, ties on every file)

**The surname** is "Fitzgerald" in Great Vibes script (OFL, pinned by SHA-256 in `fonts/`). The user
chose it from eight script fonts shown on the plate.
- It's set as one joined word at a 2.58" em, about 9.8" wide, baseline at y = 1.30".
- That leaves 0.24" above the names and knot (at least 0.2" required) and 0.37" inside the border.
- The word is thickened (mitred) just until every stroke is at least **0.065"**, "a bit thicker"
  than the 0.05" slot rule.
- The F's crossbar swash tapered to within 0.036" of the t. Its tip is trimmed back 0.025" to leave
  0.06" of copper.

**Ties** are now **0.08"** (was 0.06"), the widest that fits the small A of "Mary". They're on every
file, the Carbide Create final and practice included, so nothing drops out on the Shapeoko either.
There are no letter centers to glue back.
- That covers 25 centers: 21 in the names and dates, plus the script's z, g, e and d loops.
- The build checks every plate with no drop-outs allowed.

**The practice window** moves 0.7" right, to x = −7.3 … 5.2 (same 12.5 × 7.5"), so it holds the
whole script word, which can't be split at a letter. It loses the M of "Mary" and the oval's left
tip.

## Revision 5 (hairline necks)

The user spotted a hairline "tie" at the top of the script g, then the same thing in the small E's.
In each, a stroke curls back almost onto itself: the g's ball end to its downstroke, an E's arm to
the next arm's serif. The plate between them was the only thing holding the copper inside, and
here it was 0.01–0.05" wide. The rules only measured copper *between* separate cuts, so they missed
it.
- **Rule 6.** Shrinking the plate's copper by half the 0.06" copper rule must leave each piece of
  copper whole.
- **The fix.** Each letter is checked the same way before tying. Any copper that splits off is
  joined back to the plate with a square-ended 0.08" strip, which trims the strokes on either side.
- **Where the strip goes.** It runs straight across the neck if it can. Otherwise it goes straight
  along the thin plate, or bends once through the middle of a curved channel (the script a).

Places fixed:
- the E's in Theresa, James, Feb and December;
- the script g and a;
- the r in Apr;
- the 3's top hook;
- the 2, 5 and 9.

Openings that already clear 0.06" are left as drawn. A second pass that opened every neck to 0.08"
was tried and dropped: it bit into an S whose mouth was already 0.077".
