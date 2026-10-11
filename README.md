# cad

CAD projects for CNC and laser work. Each project generates its own cut files from Python and
keeps everything in its own folder: code, tests, docs, and the files to cut in `out/`.

| Project | What it is |
|---|---|
| [`fitzgerald-memorial`](projects/fitzgerald-memorial/README.md) | Pierced copper or brass memorial plate, a 16 × 9.5" oval, for Mary Theresa and James Guinn Fitzgerald |

Run everything from the repo root through `tools/py`, the shared Python environment (the pinned
cadgen environment from [text-to-cad](https://www.texttocad.dev)):

```bash
tools/py -m pytest projects/<name> -q   # tests
tools/py projects/<name>/build.py       # regenerate projects/<name>/out/
```

Shared fonts are in `fonts/`. Agent and contributor rules are in `AGENTS.md`.

## Credits

**Fonts**, in `fonts/`. Both are under the SIL Open Font License 1.1, and the licence text sits next
to each font:

- **Cinzel**, designed by Natanael Gama. © The Cinzel Project Authors,
  [github.com/NDISCOVER/Cinzel](https://github.com/NDISCOVER/Cinzel). Licence: `fonts/OFL.txt`.
- **Great Vibes**, designed by Robert Leuschke (TypeSETit). © The Great Vibes Pro Project Authors,
  [github.com/googlefonts/great-vibes](https://github.com/googlefonts/great-vibes). Licence:
  `fonts/OFL-GreatVibes.txt`.

**Toolkit:** [text-to-cad](https://www.texttocad.dev) by earthtojake (Thompson Labs LLC), MIT,
[github.com/earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad). Its
[cadgen](https://pypi.org/project/cadgen/) package (pinned at 0.7.20) is the Python environment
`tools/py` runs, and supplies the DXF checks and the preview snapshots.

**Libraries**, installed by `tools/py` and not stored in this repo:

- [shapely](https://github.com/shapely/shapely), BSD-3-Clause: all the 2D geometry.
- [fontTools](https://github.com/fonttools/fonttools), MIT: glyph outlines and kerning.
- [ezdxf](https://github.com/mozman/ezdxf), MIT: reading and writing DXF.
- [matplotlib](https://matplotlib.org), Matplotlib licence (PSF-based): the 1:1 PDF prints.
- [NumPy](https://numpy.org), BSD-3-Clause, and [pytest](https://pytest.org), MIT.
