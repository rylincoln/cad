"""Build the kitchen side table's cut files, previews and 3D model into out/. Writes nothing if any rule fails.

Run from the repo root:  tools/py projects/kitchen-side-table/build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from cadgen.drawing_checks import validate_dxf_file

from table import spec
from table.aprons import dowel_depths, long_apron_length, side_apron_length
from table.export import write_dxf, write_preview, write_svg
from table.frame import build_table, tip_load
from table.legs import leg_length
from table.model import write_model
from table.rules import check_table
from table.sheets import lvl_depths, lvl_spare, make_sheets
from table.top import top_size

OUT = Path(__file__).resolve().parent / "out"


class BuildError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(f"{len(problems)} problem(s)")


def build(out_dir: Path = OUT) -> dict:
    table = build_table()
    sheets = make_sheets(table)
    problems = check_table(table, sheets)
    if problems:
        raise BuildError(problems)
    (out_dir / "previews").mkdir(parents=True, exist_ok=True)
    for sheet in sheets:
        dxf = out_dir / f"{sheet.name}.dxf"
        write_dxf(sheet, dxf)
        write_svg(sheet, out_dir / f"{sheet.name}.svg")
        write_preview(sheet, out_dir / "previews" / f"{sheet.name}.png")
        errors = [f.render() for f in validate_dxf_file(dxf) if f.severity == "error"]
        if errors:
            raise BuildError([f"{dxf.name}: {error}" for error in errors])
    write_model(table, out_dir / "table.step", out_dir / "table.glb")
    w, d = top_size()
    depths = lvl_depths()
    legs = next(s for s in sheets if s.name == "legs")
    return {
        "top": (round(w, 3), round(d, 3)),
        "leg_length": round(leg_length(), 3),
        "long_apron": round(long_apron_length(), 3),
        "side_apron": round(side_apron_length(), 3),
        "lvl_spare": round(lvl_spare(legs), 3),
        "lvl_depths": {name: round(value, 3) for name, value in depths.items()},
        "dowel_depths": tuple(round(depth, 4) for depth in dowel_depths()),
        "tip_load": round(tip_load(table)),
        "nominal": list(spec.NOMINAL),
    }


def main(out_dir: Path = OUT) -> int:
    try:
        report = build(out_dir)
    except BuildError as err:
        for problem in err.problems:
            print(problem, file=sys.stderr)
        print("Build failed: fix the problems above.", file=sys.stderr)
        return 1
    w, d = report["top"]
    depths = report["lvl_depths"]
    print(f"top {w} x {d} in, legs {report['leg_length']} in long")
    print(f"aprons: long {report['long_apron']} in, side {report['side_apron']} in")
    print(f"LVL: {report['lvl_spare']} in spare; clearance pass {depths['clearance']} in deep, "
          f"finish to {depths['first_stage']} in, then to {depths['full']} in")
    in_top, in_apron = report["dowel_depths"]
    print(f"dowel holes: {in_top} in into the top, {in_apron} in into the aprons")
    print(f"{report['tip_load']} lb on the front edge would tip it")
    if report["nominal"]:
        print(f"still nominal, measure and update spec.py: {', '.join(report['nominal'])}")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
