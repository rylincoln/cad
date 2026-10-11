# Fitzgerald memorial plate

Pierced copper plate (0.020" sheet, 16 × 9.5" oval) for Mary Theresa and James Guinn Fitzgerald.
Design: `docs/superpowers/specs/2026-10-11-copper-memorial-plaque-design.md`.

## Files (`out/`)

| File | Use |
|---|---|
| `practice.svg` / `.dxf` | Cut this first, on the 13 × 8" sheet |
| `final.svg` / `.dxf` | The real plate, on the 18 × 10" sheet |
| `plate_outline.svg` / `.dxf` | The oval's edge only, for the inlay and tile work |
| `final_fullsize.pdf` | Print at 100% on 11 × 17" paper and lay it on the slice |

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

## Rebuild

```bash
tools/py -m pytest -q   # tests
tools/py build.py       # regenerate out/ (refuses to write if a cutting rule fails)
```
