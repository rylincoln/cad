# cad

CAD projects for CNC and laser work. Each project generates its own cut files from Python and
keeps everything in its own folder: code, tests, docs, and the files to cut in `out/`.

| Project | What it is |
|---|---|
| [`fitzgerald-memorial`](projects/fitzgerald-memorial/README.md) | Pierced copper or brass memorial plate, a 16 × 9.5" oval, for Mary Theresa and James Guinn Fitzgerald |

Run everything from the repo root through `tools/py`, the shared Python environment:

```bash
tools/py -m pytest projects/<name> -q   # tests
tools/py projects/<name>/build.py       # regenerate projects/<name>/out/
```

Shared fonts are in `fonts/`. Agent and contributor rules are in `AGENTS.md`.
