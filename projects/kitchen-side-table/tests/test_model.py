import math

import pytest

from table.model import table_model, write_model


@pytest.fixture(scope="module")
def model(table):
    return table_model(table)


def _boxes(model):
    return {c.label: c.bounding_box() for c in model.children}


def test_the_model_has_every_part_and_four_dowels(model):
    assert sorted(_boxes(model)) == sorted(["top", "front-left", "front-right", "back-left", "back-right",
                                            "front apron", "back apron", "left apron", "right apron",
                                            "dowel 1", "dowel 2", "dowel 3", "dowel 4"])


def test_every_part_lands_where_the_frame_puts_it(model):
    boxes = _boxes(model)
    expect = {"top": (0, 31.75, 0, 23.75, 31.25, 32.0),
              "front-left": (1.0, 4.25, 3.5, 5.286, 0, 31.25),
              "front-right": (27.5, 30.75, 3.5, 5.286, 0, 31.25),
              "back-left": (1.0, 4.25, 18.964, 20.75, 0, 31.25),
              "back-right": (27.5, 30.75, 18.964, 20.75, 0, 31.25),
              "left apron": (1.375, 2.098, 4.536, 19.714, 28.25, 31.25)}
    for name, (x0, x1, y0, y1, z0, z1) in expect.items():
        b = boxes[name]
        assert (b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z) == pytest.approx((x0, x1, y0, y1, z0, z1), abs=1e-3), name


def test_the_pockets_and_grooves_are_cut_out_of_the_parts(model):
    volumes = {c.label: c.volume for c in model.children}
    assert volumes["front-left"] == pytest.approx(119.18, abs=0.05)
    groove = (9.21875 * 0.25 + math.pi * 0.125 ** 2) * 0.3125  # a slot with round ends
    assert volumes["front apron"] == pytest.approx(26.75 * 3 * 0.723 - 2 * groove, abs=0.01)


def test_the_model_writes_step_and_glb(tmp_path, table):
    write_model(table, tmp_path / "table.step", tmp_path / "table.glb")
    assert (tmp_path / "table.step").read_text(errors="ignore").startswith("ISO-10303-21")
    assert (tmp_path / "table.glb").read_bytes()[:4] == b"glTF"
