# AGENTS.md

CAD projects for CNC and laser work, written in Python. Each project generates its own cut files
(DXF, SVG, PDF) from code. Every project lives in its own folder under `projects/`, with an
`AGENTS.md` of its own for that project's rules. Read the one for the project you're working in.

## Layout

- `projects/<name>/`: one self-contained project. See "Starting a project" below.
- `fonts/`: shared fonts, each with its licence. A project pins the fonts it uses by SHA-256.
  When you add a font or a library, credit it in the README's Credits section.
- `tools/py`: the shared Python environment.
- `README.md`: the index of projects. Add a line when you add a project.

## Commands

Always run Python through `tools/py`, from the repo root. It runs the pinned cadgen 0.7.20
environment (Python 3.13, shapely, fontTools, ezdxf, matplotlib, numpy, pytest) with uvx. There
is no virtualenv or requirements file, and nothing to install.

```bash
tools/py -m pytest projects/<name> -q     # one project's tests, using its own pytest.ini
tools/py projects/<name>/build.py         # regenerate that project's out/
```

A bare `pytest` at the repo root runs nothing useful. Each project's packages are importable only
through its own `pytest.ini`, so always name the project.

## Starting a project

Make `projects/<name>/` (lowercase, hyphenated) with the same shape as the existing projects:

- `README.md`: what it is, and the machining guide for whoever cuts it.
- `AGENTS.md`: the project's rules.
- `build.py`: writes into the project's own `out/`, using `Path(__file__)`, never the working
  directory.
- `pytest.ini`: `testpaths = tests`, `pythonpath = .`.
- the code package.
- `tests/`.
- `docs/specs/` and `docs/plans/`: design specs and implementation plans. Keep them here, not in
  a repo-wide `docs/`.
- `out/`: the generated files, committed.

Don't import one project's code from another. When a second project needs something from an
existing one, such as glyph outlines or DXF export, move it into a shared package at the repo root
and point both projects at it.

## Working here

- Write the failing test first, then the code. Run the project's whole suite before committing.
- Match the existing style: `from __future__ import annotations`, a one-line module docstring,
  few comments, and test names that read as sentences.
- Commit messages are a single imperative sentence in sentence case, with no type prefix.
- Never add AI attribution: no `Co-Authored-By` trailers, no "Generated with" lines, and no
  notes in code or docs saying an AI wrote them.
- `.superpowers/`, `.playwright-mcp/` and the caches are git-ignored scratch space.
