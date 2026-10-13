from table import spec


def test_every_nominal_name_is_a_measured_input():
    assert all(isinstance(getattr(spec, name), float) for name in spec.NOMINAL)


def test_only_the_tops_width_and_depth_still_need_measuring():
    assert spec.NOMINAL == ("TOP_WIDTH", "TOP_DEPTH")
