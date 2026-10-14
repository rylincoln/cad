# AGENTS.md: Kitchen side table

The repo-wide rules are in `../../AGENTS.md`. This file adds the rules for this project.

Python that generates the cut files for a kitchen side table: four flared LVL legs, four plywood
aprons, and a cherry top with a swept front edge, all cut on a Shapeoko Pro XXL. The geometry is
built with shapely and checked against the spec's rules. It's written to `out/` as DXF and SVG
with PNG previews, and assembled into a 3D model with build123d. `README.md` is the machining and
assembly guide. The design is in `docs/specs/2026-10-13-kitchen-side-table-design.md`.

## Commands (from the repo root)

```bash
tools/py -m pytest projects/kitchen-side-table -q        # whole suite, a few seconds
tools/py -m pytest projects/kitchen-side-table/tests/test_rules.py -q
tools/py projects/kitchen-side-table/build.py            # regenerate out/; writes nothing if a rule fails
```

## Layout

- `table/spec.py`: every number, in inches. The measured stock and bits come first. A name stays in
  `NOMINAL` until it has been measured, and the build reminds you of each one.
- `table/top.py`: the top's outline.
- `table/legs.py`: the legs and their pockets, in leg coordinates, and the fit-test pockets.
- `table/aprons.py`: the aprons, with their grooves and dowel holes, and the coupon.
- `table/frame.py`: places every part in table coordinates (`Placed`), and works out the weight,
  the balance and the tipping load.
- `table/sheets.py`: the four jobs, each part on its stock in sheet coordinates.
- `table/rules.py`: `check_table` returns plain-English problems. An empty list means the table can
  be cut and built.
- `table/export.py`: DXF, SVG and PNG previews of each sheet.
- `table/model.py`: the 3D model, as STEP and GLB.
- `build.py`: checks, then writes everything in `out/`.
- `tests/`: one file per module, plus `test_build.py`. The shared `table` and `sheets` fixtures are
  in `conftest.py`.

## Rules that must hold

- **Units are inches, and table coordinates are right-handed:** x from the left end as seen from
  the room, y from the front edge's deepest point toward the wall, z up. A plan drawn with y up is
  the table seen from above, with the wall at the top.
- **Nothing is ever mirrored onto a sheet.** Each part goes on by rotation and translation, with
  the face that's cut first facing up: the legs' and aprons' inside faces, and the top's show face.
  `test_the_legs_go_on_by_rotation_only_never_mirrored` and the shallow-end rule guard this.
- **The sweep's shallow end is on the left** as seen from the room, and on the left of job 4.
- **`check_table` must return `[]`** before the build writes anything. Fix the design, not the rule.
- **Numbers live in `spec.py`.** Every function reads spec values when it runs, so tests can
  monkeypatch them. Never copy a spec value into a module-level constant.
- **The groove layer is `GROOVE_CENTERLINE`**, an open line. cadgen's DXF check rejects open lines
  on layers it reads as cut-through.

## Working here

- After any geometry change, run the build, look at `out/previews/*.png`, and commit the regenerated
  `out/` with the change. The rules can pass on a shape that still looks wrong.
- Every build rewrites the DXF timestamps and the STEP file's header. If a file changed only in that
  metadata, restore it with `git checkout -- <file>`.
- When the design changes, add a revision to the spec and update `README.md`. Keep the README's
  depths in step with the build's printout.
- `out/*.c2d` are the owner's own Carbide Create jobs. Never regenerate, overwrite, revert or stage them.
