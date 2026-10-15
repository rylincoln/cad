# Kitchen side table

A 32"-tall side table that stands against a wall, with four flared LVL legs, plywood aprons, and a
cherry top whose front edge sweeps in an asymmetric curve. Four glued dowels hold the top at its
middle and eight Z-clips hold the rest, so it can move with the seasons. Every part is cut on a
Shapeoko Pro XXL from files this project generates. The design and its reasons are in
`docs/specs/2026-10-13-kitchen-side-table-design.md`.

![The four legs on the LVL, head to toe](out/previews/legs.png)

## Build the files

Set your measured stock and bits at the top of `table/spec.py`, then from the repo root:

```bash
tools/py projects/kitchen-side-table/build.py       # check the rules, write out/, print every depth
tools/py -m pytest projects/kitchen-side-table -q   # tests
```

The build writes nothing if a rule fails. The depths below are for the stock in `spec.py` now; use
the ones the build prints for yours. `AGENTS.md` describes the code.

## Jobs

Files are in inches. Zero X and Y at the stock's lower-left corner seen from above, and Z on its
top. `out/*.c2d` are Carbide Create jobs with toolpaths and tabs, and `out/table.glb` is the
assembled table in 3D.

| Job | Stock, face up | Bit and starting settings |
|---|---|---|
| 1 aprons | Plywood, 32 × 11⅞", worse face up | ¼" three-flute: 16,000 RPM, 50 IPM, 15 IPM ramped plunge, 0.1" per pass |
| 2 fit test | LVL offcut, 6 × 4" or more | As job 3's housings |
| 3 legs | LVL, 32½ × 11¾", worse face up | ¼" two-flute, 1.4" flute, 2" out of the collet. Housings: 13,000 RPM, 40 IPM, 0.05" per pass. Laps, clearance and rough: 16,000 RPM, 75 IPM, 0.1" per pass (rough 0.08"). Finish: 60 IPM. About 3 hours. |
| 4 top | Cherry glue-up, show face up, curved edge toward you | As job 1, plus a full-depth finishing pass |

| Layer | Toolpath |
|---|---|
| `REFERENCE_STOCK` | None: the stock's outline |
| `POCKET_HOUSING` | Pocket, 0.75" |
| `POCKET_LAP` | Pocket, the plywood's thickness: 0.706" |
| `GROOVE_CENTERLINE` | Contour, no offset, 5/16" |
| `CLEARANCE` | Contour, outside, 0.34" (legs) |
| `ROUGH` | Contour, outside, 1.64" (legs) |
| `CUT_OUTSIDE` | Contour, outside: plywood 0.726", top 0.77", legs 1.64" in two stages (to 1.3", then full depth) |

## Cutting

- **Hold-down:** tabs hold the plywood parts. Clamp the LVL and the top at their front and back
  edges, 8½" and 24" from the left end, where the jobs put their tabs. Every pass leaves at least
  ⅛" of wood under the clamps. Keep the clamps low: on the legs the collet nut passes 0.36" above
  the board. With the spindle off, jog down to full depth beside each clamp to check.
- **Fit test before the legs:** the plywood coupon from job 1 should slide into the test housing
  snug by hand and sit flush in the test lap. If it doesn't, adjust `FIT_CLEARANCE` (housing) or
  `PLY_THICKNESS` (lap), rebuild, and cut the test again.
- **Legs, in order:** pockets, clearance, rough, outline to 1.3", outline to full depth. The
  clearance pass keeps the bit's shank from rubbing below the flutes.
- **Tabs:** re-importing a DXF drops them, so add them again. Saw them off and sand flush; the
  top's front tabs are on its show edge. Pencil each leg's name on it as it comes off.

## Assembly

1. **Before job 4,** glue up the top with the grain running front to back. Keep the biscuits 2–19"
   from the back ends so the cut-out can't expose them. Measure it and set `TOP_WIDTH` and
   `TOP_DEPTH`.
2. **Dry-fit the base.** The side aprons drop into the housings, and the long aprons sit in the
   laps, flush with the legs' inside faces. Each apron's clip groove goes on the inside, ⅜" below
   its top edge.
3. **Glue each end frame** square: two legs and a side apron. Drill two 5/16" dowel holes in each
   long apron's top edge where the build says, then glue and screw the long aprons into their laps.
4. **Finish** every face, including the top's underside, so the top stays flat. Seal the end grain
   first. Keep finish off the dowel holes and the 2" of apron edge between them.
5. **Attach the top.** Set the base upside down on the upside-down top, with the legs 1" in from the
   ends and the back legs 2.53" from the back edge. Mark the dowels with dowel centers and drill to
   the printed depth with a stop collar. Glue only the dowels and the 2" between them, then fit the
   eight Z-clips: one per long apron, two per side apron.
