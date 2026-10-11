import pytest

import build
from memorial import spec

EXPECTED_FILES = {"final.dxf", "final.svg", "practice.dxf", "practice.svg",
                  "plate_outline.dxf", "plate_outline.svg", "final_fullsize.pdf",
                  "final_sendcutsend.dxf", "border_engrave.dxf", "border_engrave.svg"}


def test_build_writes_every_file_and_reports_the_counts(tmp_path):
    report = build.build(tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == EXPECTED_FILES
    assert report["final"]["size_in"] == (16.0, 9.5)
    assert report["final"]["cutouts"] == 68
    assert report["final"]["loose_pieces"] == 23
    assert report["final"]["pin_holes"] == 8
    assert report["practice"]["size_in"] == (12.5, 7.5)
    assert report["practice"]["cutouts"] == 55
    assert report["practice"]["loose_pieces"] == 19
    assert report["practice"]["pin_holes"] == 3
    assert report["final_sendcutsend"]["loose_pieces"] == 0
    assert report["final_sendcutsend"]["pin_holes"] == 8


def test_build_creates_a_missing_output_folder(tmp_path):
    out = tmp_path / "new" / "out"
    build.build(out)
    assert (out / "final.dxf").exists()


def test_build_refuses_to_write_anything_when_a_rule_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(spec, "MIN_COPPER", 0.5)
    with pytest.raises(build.BuildError) as err:
        build.build(tmp_path / "out")
    assert err.value.problems["final"]
    assert not (tmp_path / "out").exists()
