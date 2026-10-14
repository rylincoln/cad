import dataclasses

import pytest
from shapely.affinity import scale, translate
from shapely.geometry import LineString, box

from table import spec
from table.frame import build_table
from table.rules import check_table
from table.sheets import make_sheets


def _problems() -> list[str]:
    table = build_table()
    return check_table(table, make_sheets(table))


def _with_placed(table, name, **changes):
    return dataclasses.replace(table, placed=tuple(
        dataclasses.replace(p, **changes) if p.name == name else p for p in table.placed))


def test_the_approved_table_passes_every_rule(table, sheets):
    assert check_table(table, list(sheets.values())) == []


def test_a_part_too_close_to_the_stocks_edge_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "LVL_WIDTH", 11.4)
    assert _problems() == ['legs: the back-left is not 0.125" inside the stock']


def test_parts_closer_than_the_sheets_gap_are_reported(table, sheets):
    aprons = sheets["aprons"]
    crowded = dataclasses.replace(aprons.parts[1], outline=translate(aprons.parts[1].outline, 0, -0.2))
    doctored = dict(sheets, aprons=dataclasses.replace(aprons, parts=(aprons.parts[0], crowded, *aprons.parts[2:])))
    assert check_table(table, list(doctored.values())) == [
        'aprons: only 0.050" between the back apron and the front apron, needs 0.25"']


def test_stock_too_big_for_the_machine_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "TOP_WIDTH", 36.0)
    assert _problems() == ['top: the 36 x 24" stock doesn\'t fit the 33 x 33" work area']


def test_a_square_corner_the_bit_cant_reach_is_reported(table, sheets):
    leg = table.legs[0]
    plain = box(-1.103, 28.25, -0.375, 31.45)  # the front-left housing with no dogbones
    doctored = dataclasses.replace(table, legs=(dataclasses.replace(leg, housing=plain), *table.legs[1:]))
    assert check_table(doctored, list(sheets.values())) == ["the bit can't reach every corner of the front-left leg's housing"]


def test_a_housing_narrower_than_the_plywood_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "FIT_CLEARANCE", -0.01)
    problems = _problems()
    assert "the coupon doesn't fit the fit test's housing" in problems
    assert "the left apron runs into the front-left leg outside its pockets" in problems
    assert len(problems) == 5


def test_a_pocket_too_shallow_for_its_apron_is_reported(table, sheets):
    leg = next(p for p in table.placed if p.name == "front-left")
    doctored = _with_placed(table, "front-left", pockets=((leg.pockets[0][0], 0.5), leg.pockets[1]))
    assert check_table(doctored, list(sheets.values())) == [
        'the left apron goes 0.750" into the front-left leg, but its pocket is 0.500" deep']


def test_a_cut_deeper_than_the_three_flute_bits_flute_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "THREE_FLUTE_LENGTH", 0.7)
    assert _problems() == ['the plywood cut-out is 0.743" deep, past the three-flute bit\'s 0.7" flute',
                           'the fit-test housing is 0.750" deep, past the three-flute bit\'s 0.7" flute',
                           'the top cut-out is 0.770" deep, past the three-flute bit\'s 0.7" flute']


def test_legs_too_near_the_tops_edge_are_reported(monkeypatch):
    monkeypatch.setattr(spec, "LEG_INSET", 0.25)
    assert 'the front-left leg\'s top is not 0.5" inside the top\'s edge' in _problems()


def test_a_front_edge_too_far_past_the_legs_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "FRONT_LEG_BEHIND_EDGE", 5.0)
    assert _problems() == ['the front edge reaches 5.00" past the front legs, more than 3.5"',
                           "39 lb on the front edge would tip the table, under 50 lb"]


def test_a_table_too_easy_to_tip_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "MIN_TIP_LOAD", 100.0)
    assert _problems() == ["64 lb on the front edge would tip the table, under 100 lb"]


def test_a_collet_nut_too_close_to_the_lvl_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "STICKOUT", 1.9)
    assert _problems() == ['the collet nut clears the LVL by only 0.094" at full depth, under 0.15"']


def test_a_ridge_between_the_clearance_and_rough_passes_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "CLEARANCE_OFFSET", 0.3)
    assert _problems() == ["the clearance pass leaves a ridge between itself and the rough pass",
                           'the clearance pass reaches 0.550" outside each leg, past the 0.4" gap to the next leg']


def test_a_clearance_pass_reaching_the_next_leg_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "LVL_GAP", 0.35)
    assert _problems() == ['the clearance pass reaches 0.375" outside each leg, past the 0.35" gap to the next leg']


def test_a_leg_that_doesnt_reach_the_top_is_reported(table, sheets):
    leg = next(p for p in table.placed if p.name == "front-left")
    doctored = _with_placed(table, "front-left", outline=translate(leg.outline, 0, -0.1))
    assert check_table(doctored, list(sheets.values())) == [
        'the front-left leg runs from -0.100 to 31.150", not from the floor to the top']


def test_a_mirrored_top_is_reported(table, sheets):
    mirrored = scale(table.top, -1, 1, origin=(31.75 / 2, 0))
    assert check_table(dataclasses.replace(table, top=mirrored), list(sheets.values())) == [
        "the top's shallow end is not on the left as seen from the room"]


def test_a_mirrored_top_on_job_4_is_reported(table, sheets):
    top = sheets["top"]
    mirrored = dataclasses.replace(top.parts[0], outline=scale(top.parts[0].outline, -1, 1, origin=(16, 0)))
    doctored = dict(sheets, top=dataclasses.replace(top, parts=(mirrored,)))
    assert check_table(table, list(doctored.values())) == ["the top's shallow end is not on the left of job 4"]


def test_a_groove_reaching_into_a_joint_is_reported(table, sheets):
    front = table.aprons[0]
    long_groove = dataclasses.replace(front, grooves=(LineString([(1.0, 2.5), (11.0, 2.5)]), front.grooves[1]))
    doctored = dataclasses.replace(table, aprons=(long_groove, *table.aprons[1:]))
    assert check_table(doctored, list(sheets.values())) == [
        'a clip groove in the front apron comes within 0.5" of a joint or dowel']


def test_a_groove_running_through_the_dowels_is_reported(table, sheets):
    front = table.aprons[0]
    through = dataclasses.replace(front, grooves=(LineString([(2.375, 2.5), (24.375, 2.5)]),))
    doctored = dataclasses.replace(table, aprons=(through, *table.aprons[1:]))
    assert check_table(doctored, list(sheets.values())) == [
        'a clip groove in the front apron comes within 0.5" of a joint or dowel']


def test_a_top_too_thin_to_hold_the_dowels_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.6)
    assert _problems() == ['only 0.350" of each dowel goes into the top, under 0.375"']


def test_a_dowel_too_fat_for_the_plywood_edge_is_reported(monkeypatch):
    monkeypatch.setattr(spec, "DOWEL_DIAMETER", 0.5)
    assert _problems() == ['the dowel holes leave only 0.111" of plywood either side']


def test_a_glue_up_a_little_smaller_than_nominal_still_passes_and_rescales(monkeypatch):
    monkeypatch.setattr(spec, "TOP_WIDTH", 31.5)
    monkeypatch.setattr(spec, "TOP_DEPTH", 23.5)
    table = build_table()
    assert check_table(table, make_sheets(table)) == []
    assert next(a for a in table.aprons if a.name == "front apron").outline.bounds[2] == pytest.approx(26.25)


def test_a_top_sanded_to_0_72_still_passes_with_longer_legs(monkeypatch):
    monkeypatch.setattr(spec, "TOP_THICKNESS", 0.72)
    table = build_table()
    assert check_table(table, make_sheets(table)) == []
    assert table.legs[0].outline.bounds[3] == pytest.approx(31.28)


@pytest.mark.parametrize("thickness", [0.70, 0.75])
def test_plywood_a_little_thinner_or_thicker_still_passes(monkeypatch, thickness):
    monkeypatch.setattr(spec, "PLY_THICKNESS", thickness)
    assert _problems() == []
