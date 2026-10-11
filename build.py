"""Build every memorial plate file into out/. Writes nothing if any cutting rule fails.

Run:  tools/py build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from cadgen.drawing_checks import validate_dxf_file

from memorial import spec
from memorial.export import write_dxf, write_pdf, write_svg
from memorial.font import Font
from memorial.plate import Plate, build_final, build_practice, outline_only
from memorial.rules import check_plate

OUT = Path(__file__).resolve().parent / "out"


class BuildError(Exception):
    def __init__(self, problems: dict[str, list[str]]):
        self.problems = problems
        super().__init__("; ".join(f"{name}: {len(items)} problem(s)" for name, items in problems.items() if items))


def summarize(plate: Plate) -> dict:
    minx, miny, maxx, maxy = plate.outline.bounds
    return {
        "size_in": (round(maxx - minx, 3), round(maxy - miny, 3)),
        "cutouts": len(plate.cutouts),
        "loose_pieces": sum(len(region.interiors) for _, region in plate.cutouts),
        "pin_holes": len(plate.holes),
        "kept": {line.text: "".join(line.chars) for line in plate.lines.values()},
        "spacing_opened": {line.text: list(line.pushes) for line in plate.lines.values() if line.pushes},
    }


def build(out_dir: Path = OUT) -> dict:
    font = Font(spec.FONT_PATH)
    final = build_final(font)
    practice = build_practice(final)
    problems = {"final": check_plate(final, full_text=True), "practice": check_plate(practice, full_text=False)}
    if any(problems.values()):
        raise BuildError(problems)
    out_dir.mkdir(parents=True, exist_ok=True)
    for plate in (final, practice, outline_only(final)):
        dxf = out_dir / f"{plate.name}.dxf"
        write_dxf(plate, dxf)
        write_svg(plate, out_dir / f"{plate.name}.svg")
        errors = [f.render() for f in validate_dxf_file(dxf) if f.severity == "error"]
        if errors:
            raise BuildError({plate.name: errors})
    write_pdf(final, out_dir / "final_fullsize.pdf")
    return {"final": summarize(final), "practice": summarize(practice)}


def main() -> int:
    try:
        report = build()
    except BuildError as err:
        for name, items in err.problems.items():
            for item in items:
                print(f"[{name}] {item}", file=sys.stderr)
        print("Build failed: fix the problems above.", file=sys.stderr)
        return 1
    for name, info in report.items():
        width, height = info["size_in"]
        print(f"{name}: {width} x {height} in, {info['cutouts']} cutouts, "
              f"{info['loose_pieces']} letter centres to glue back, {info['pin_holes']} pin holes")
        if name == "practice":
            for text, kept in info["kept"].items():
                print(f"  keeps {kept!r} of {text!r}")
        for text, pushes in info["spacing_opened"].items():
            print(f"  spacing opened in {text!r}: {pushes}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
