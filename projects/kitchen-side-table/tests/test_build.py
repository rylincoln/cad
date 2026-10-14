import pytest

import build
from table import spec

EXPECTED_FILES = {"aprons.dxf", "aprons.svg", "fit_test.dxf", "fit_test.svg", "legs.dxf", "legs.svg",
                  "top.dxf", "top.svg", "table.step", "table.glb",
                  "previews/aprons.png", "previews/fit_test.png", "previews/legs.png", "previews/top.png"}


def test_build_writes_every_file_into_a_new_folder_and_reports_the_numbers(tmp_path):
    out = tmp_path / "new" / "out"
    report = build.build(out)
    assert {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()} == EXPECTED_FILES
    assert report == {"top": (31.75, 23.75), "leg_length": 31.25, "long_apron": 26.75, "side_apron": 15.178,
                      "lvl_clamp_room": 0.148, "lvl_depths": {"full": 1.64, "clearance": 0.34, "first_stage": 1.3},
                      "dowel_depths": (0.5, 1.0625), "dowel_positions": (12.375, 14.375),
                      "cut_depths": {"housing": 0.75, "lap": 0.706, "groove": 0.3125, "plywood": 0.726, "top": 0.77},
                      "tip_load": 59, "nominal": ["TOP_WIDTH", "TOP_DEPTH"]}


def test_build_refuses_to_write_anything_when_a_rule_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 500.0)
    with pytest.raises(build.BuildError) as err:
        build.build(tmp_path / "out")
    assert err.value.problems == ["59 lb on the front edge would tip the table, under 500 lb"]
    assert not (tmp_path / "out").exists()


def test_rebuilding_into_an_existing_folder_replaces_the_files(tmp_path):
    build.build(tmp_path)
    (tmp_path / "top.dxf").write_text("stale")
    build.build(tmp_path)
    assert (tmp_path / "top.dxf").read_text() != "stale"


def test_main_prints_the_numbers_and_the_values_still_to_measure(tmp_path, capsys):
    assert build.main(tmp_path) == 0
    out = capsys.readouterr().out
    assert "top 31.75 x 23.75 in, legs 31.25 in long" in out
    assert "LVL: 0.148 in of wood left along each long edge for the clamps" in out
    assert ("pockets: housing 0.75 in, lap 0.706 in, groove 0.3125 in; "
            "cut-outs: plywood 0.726 in, top 0.77 in") in out
    assert ("dowel holes: 0.5 in into the top, 1.0625 in into the aprons, "
            "12.375 and 14.375 in from each end of the long aprons") in out
    assert "still nominal, measure and update spec.py: TOP_WIDTH, TOP_DEPTH" in out


def test_main_prints_the_problems_and_fails_when_a_rule_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 500.0)
    assert build.main(tmp_path / "out") == 1
    err = capsys.readouterr().err
    assert "59 lb on the front edge would tip the table, under 500 lb" in err
    assert "Build failed" in err
