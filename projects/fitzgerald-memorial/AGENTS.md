# AGENTS.md: Fitzgerald memorial plate

The repo-wide rules are in `../../AGENTS.md`. This file adds the rules for this project.

Python that generates the cut files for the Fitzgerald memorial plate: a 16 × 9.5" pierced oval
cut from 0.020" copper on a Shapeoko Pro, or from brass by SendCutSend. The geometry is built
with shapely from the font outlines, checked against the cutting rules, and written to `out/` as
DXF, SVG and a 1:1 PDF. `README.md` is the machining guide for whoever cuts the plate. The design
and its revisions are in `docs/specs/2026-10-11-copper-memorial-plaque-design.md`.

## Commands (from the repo root)

```bash
tools/py -m pytest projects/fitzgerald-memorial -q          # whole suite, a few seconds
tools/py -m pytest projects/fitzgerald-memorial/tests/test_ties.py -q
tools/py projects/fitzgerald-memorial/build.py              # regenerate out/; writes nothing if a cutting rule fails
uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.20 cadgen dxf snapshot \
  projects/fitzgerald-memorial/out/final.dxf projects/fitzgerald-memorial/out/previews/final.png
```

## Layout

- `memorial/spec.py`: every dimension the design fixes, in inches, plus the approved text
  (`LINES`). Change numbers here, not inline. Fonts come from the repo's shared `fonts/` and
  are pinned by SHA-256.
- `memorial/font.py`: glyph outlines as shapely polygons, with advances and GPOS kerning.
- `memorial/text.py`: sets kerned lines of separate letters (Cinzel), or one joined script word
  (`set_word`, Great Vibes), thickened to a minimum stroke.
- `memorial/knot.py`: the trinity knot.
- `memorial/ties.py`: stencil ties, and opening hairline necks inside a letter into full ties.
- `memorial/plate.py`: assembles the final plate, the practice window, and the outline-only and
  border-only plates.
- `memorial/rules.py`: `check_plate` returns plain-English problems. An empty list means
  cuttable.
- `memorial/export.py`: DXF/SVG in sheet coordinates, the cut-only SendCutSend DXF, and the PDF.
- `build.py`: builds, checks and writes everything in `out/`.
- `tests/`: about one file per module, plus `test_practice.py` and `test_build.py`. The shared
  fixtures (`font`, `script_font`, `untied`, `final`, `practice`) are in `conftest.py`.
- `docs/`: the design spec (`specs/`) and the original implementation plan (`plans/`).

## Rules that must hold

- **The text is fixed.** `test_text_is_exactly_what_the_family_approved` pins it. Never change
  a name, date or spelling.
- **Units are inches.** Plate coordinates put the origin at the plate center, +y up. Export
  shifts to sheet coordinates: lower-left of the copper sheet for the Shapeoko files, lower-left
  of the plate for the SendCutSend DXF.
- **Nothing may drop out.** Every letter center and script loop is held by a `TIE_WIDTH` tie.
  D and 0 get two ties; every other center gets one. `check_plate(..., drop_outs=False)` must
  return `[]` for the final and practice plates.
- **Copper must stay whole.** `check_plate` fails any neck of copper narrower than
  `MIN_COPPER`. Where a stroke curls back almost onto itself, the gap is opened into a full
  tie, not left as a hairline.
- **The bit sets the minimums.** It is a 1/32" ball, so slots must be at least `MIN_SLOT`.
  `TIE_WIDTH` = 0.08" is the widest tie that fits the small A of "Mary"; wider ties don't fit.
- **The SendCutSend file is through-cuts only.** It holds the oval, the lettering, the knot and
  the pin holes. A laser cuts every line it's sent, so the border is a separate engrave file and
  the sheet rectangle is reference only.

## Working here

- After any geometry change, run the build, commit the regenerated `out/` files with the change,
  and look at a snapshot or the SVG. The rules can pass on a shape that still looks wrong.
- Every build rewrites DXF header timestamps, GUIDs and object order, and the PDF's date. If a
  file changed only in that metadata, restore that one file with `git checkout -- <file>`.
  Never check out the whole `out/` folder: it would wipe the edits in the `.c2d` jobs.
- `out/*.c2d` are the owner's own Carbide Create jobs. Never regenerate, overwrite, revert or
  stage them.
- When the design changes, add a revision to the spec and update `README.md`. Keep the README's
  machining steps in step with the files.
