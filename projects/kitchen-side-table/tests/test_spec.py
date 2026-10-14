from table import spec


def test_every_nominal_name_is_a_measured_input():
    assert all(isinstance(getattr(spec, name), float) for name in spec.NOMINAL)


def test_every_input_has_been_measured():
    assert spec.NOMINAL == ()
