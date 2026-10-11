# Fitzgerald memorial plate

Pierced copper plate (0.020" sheet, 16 × 9.5" oval), or brass from SendCutSend, for Mary Theresa and James Guinn Fitzgerald.
Design: `docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md`.

## Files (`out/`)

| File | Use |
|---|---|
| `practice.svg` / `.dxf` | Cut this first, on the 13 × 8" sheet |
| `final.svg` / `.dxf` | The real plate, on the 18 × 10" sheet |
| `plate_outline.svg` / `.dxf` | The oval's edge only, for the inlay and tile work |
| `final_fullsize.pdf` | Print at 100% on 11 × 17" paper and lay it on the slice |
| `final_sendcutsend.dxf` | The real plate with stencil ties, through-cuts only, for ordering from SendCutSend |
| `border_engrave.svg` / `.dxf` | The border line only, to engrave on the plate SendCutSend sends back |

## Carbide Create

1. **Set up the job before importing.** Stock **18 × 10"** for the final (**13 × 8"** for the
   practice piece), thickness **0.020"**. Zero X and Y at the **lower-left corner of the copper
   sheet**, and Z at the **top of the copper**. The files are drawn in those sheet coordinates.
2. **Import and check the scale.** Import the SVG (or the DXF), then check that the oval
   measures **16.000 × 9.500"** (practice 12.5 × 7.5"). If it doesn't, the import scale is wrong.
   The **grey rectangle** is just the sheet's outline, for lining things up. Give it no
   toolpath (or delete it).
3. **Set the tool.** The bit is a tapered ball nose, R1/64" × 1.5" × 1/4": a **1/32" ball** at
   the tip. Use Carbide Create's **1/32" ball mill** preset, and replace its feeds with the
   ones below.
4. **Build the toolpaths in this order:**

   | Vectors (colour) | Toolpath | Depth |
   |---|---|---|
   | Border (green) | Contour, no offset | 0.006" (a groove about 0.025" wide) |
   | Letters, knot, pin holes (red) | Contour, **inside** | 0.043" |
   | Oval edge (blue) | Contour, **outside** | 0.043" |

   0.043" is the copper (0.020"), plus the ball's radius (0.016") so the cut is full width at
   the bottom, plus a little into the tape.
5. **Feeds and speeds:** about 18,000 RPM, 10 IPM, 3 IPM plunge, 0.005" per pass, with
   cutting fluid.
6. **Preview the simulation.** Check that every letter center (in A, D, B, 0, and the small
   r, p, 6 and 9) stays as an island.
7. **Hold-down and removal:** keep the sheet fully glued down. Remove it by peeling or with
   acetone, never by prying. Save the 23 letter centers (19 on the practice piece) and glue
   them back onto the wood in place.

## SendCutSend

Upload `final_sendcutsend.dxf`, confirm units as **INCH**, and check the part reads **16 × 9.5"**.
Choose **Brass, 0.040"**. The file also passes every minimum for 0.063". The file holds only the
through-cuts: the oval, the lettering, the knot and the 8 pin holes. A laser cuts every line it's
sent, so the grey sheet rectangle and the border line are left out.

SendCutSend keeps nothing that falls free. So every letter center (in A, D, B, 0, and the small r,
p, 6 and 9) is held in the plate by a **stencil tie**: a 0.06" strip of brass left across the
stroke, where stencil lettering puts it. D and 0 get two ties, every other letter one. The ties
stay, so there's nothing to glue back. The narrowest brass anywhere is 0.06", three times their
0.020" minimum for 0.040" brass.

SendCutSend cuts holes to ±0.005". If a #16 pin won't go into a 0.070" hole, run a #50 drill
through it.

## Border engraving (after SendCutSend)

SendCutSend can't add the border line: their engraving only takes parts up to 12.1 × 12.1", and
they don't etch brass. Engrave it on the Shapeoko before mounting. The 8 pin holes sit exactly on
the border line, so they're used to line the job up.

1. **Set up the job.** Stock **16 × 9.5"**, thickness **0.040"**, XY zero at the **center**, Z
   zero at the **top**. Import `border_engrave.svg` (or the DXF) and check it lands exactly on
   the stock. Grey is reference only: give the oval and the holes no toolpath.
2. **Toolpath.** The green line only: contour, **no offset** (on the line), 1/32" ball mill
   preset, depth **0.006"**, 0.003" per pass, 18,000 RPM, 10 IPM, 3 IPM plunge.
3. **Hold it flat.** Tape the plate face up with double-sided tape under the solid brass all
   around the border. It must lie flat: a 0.006" groove shows any bow as a line that thins
   and fades.
4. **Find the center from the pin holes.** With the spindle off, lower the bit tip into the
   center of the **left** pin hole and zero X and Y. Lift the bit, then send `G0 X15.25 Y0` in
   the MDI screen: the tip should be over the **right** pin hole. If it's above or below the hole,
   the plate is turned: square it up and start this step again. Then send `G0 X7.625 Y0` and
   zero X only. To check, send `G0 X0 Y4.375` and `G0 X0 Y-4.375`: the tip should be over the
   top and bottom holes.
5. **Zero Z on the brass** next to the border, then run the job. The line passes through the
   middle of every pin hole.

## Rebuild

```bash
tools/py -m pytest -q   # tests
tools/py build.py       # regenerate out/ (refuses to write if a cutting rule fails)
```
