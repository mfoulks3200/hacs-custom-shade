"""Tests for custom_shades config validation."""
import pytest
from voluptuous import Invalid as VolInvalid

from custom_shades.config import SHADE_SCHEMA, shade_schema_for_entry


def test_valid_shade_config():
    """All required fields present — basic valid case."""
    valid = {
        "name": "Test Shade",
        "open_scene": "scene.test_open",
        "close_scene": "scene.test_close",
        "stop_scene": "scene.test_stop",
        "travel_time": 30.5,
    }
    result = SHADE_SCHEMA(valid)
    assert result["name"] == "Test Shade"
    assert result["travel_time"] == 30.5
    assert result["initial_position"] == 50  # default
    assert result["min_adjustment"] == 2.5   # default


def test_valid_shade_config_with_all_options():
    """All fields including optional overrides."""
    valid = {
        "name": "Full Shade",
        "open_scene": "scene.full_open",
        "close_scene": "scene.full_close",
        "stop_scene": "scene.full_stop",
        "travel_time": 45.0,
        "initial_position": 80,
        "min_adjustment": 3.0,
    }
    result = SHADE_SCHEMA(valid)
    assert result["initial_position"] == 80
    assert result["min_adjustment"] == 3.0


def test_missing_required_field_raises():
    """Missing required fields should raise Invalid."""
    invalid = {"name": "Incomplete"}
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(invalid)


def test_missing_open_scene_raises():
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA({
            "name": "Bad",
            "close_scene": "s2",
            "stop_scene": "s3",
            "travel_time": 30,
        })


def test_missing_close_scene_raises():
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA({
            "name": "Bad",
            "open_scene": "s1",
            "stop_scene": "s3",
            "travel_time": 30,
        })


def test_missing_stop_scene_raises():
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA({
            "name": "Bad",
            "open_scene": "s1",
            "close_scene": "s2",
            "travel_time": 30,
        })


def test_missing_travel_time_raises():
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA({
            "name": "Bad",
            "open_scene": "s1",
            "close_scene": "s2",
            "stop_scene": "s3",
        })


def test_travel_time_must_be_positive():
    """travel_time must be > 0."""
    bad = {
        "name": "Bad",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": -5.0,
    }
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_travel_time_zero_raises():
    """Zero travel time is invalid (would divide by zero in duration calc)."""
    bad = {
        "name": "Bad",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": 0,
    }
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_travel_time_accepts_integer():
    """Integer travel time should coerce to float."""
    valid = {
        "name": "Bad",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": 60,
    }
    result = SHADE_SCHEMA(valid)
    assert isinstance(result["travel_time"], float)


def test_position_range():
    """initial_position must be in [0, 100]."""
    # Below minimum
    bad = {"name": "Bad", "open_scene": "s1", "close_scene": "s2",
           "stop_scene": "s3", "travel_time": 30, "initial_position": -1}
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)

    # Above maximum
    bad["initial_position"] = 101
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_position_boundary_values():
    """Boundary values should be accepted."""
    for pos in [0, 50, 100]:
        result = SHADE_SCHEMA({
            "name": "Bad",
            "open_scene": "s1",
            "close_scene": "s2",
            "stop_scene": "s3",
            "travel_time": 30,
            "initial_position": pos,
        })
        assert result["initial_position"] == pos


def test_defaults_are_applied():
    """Optional fields should default when omitted."""
    minimal = {
        "name": "Minimal",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": 30.0,
    }
    result = SHADE_SCHEMA(minimal)
    assert result["initial_position"] == 50
    assert result["min_adjustment"] == 2.5


def test_min_adjustment_zero_is_valid():
    """Zero min_adjustment means always move (edge case)."""
    valid = {
        "name": "Bad",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": 30,
        "min_adjustment": 0.0,
    }
    result = SHADE_SCHEMA(valid)
    assert result["min_adjustment"] == 0.0


def test_min_adjustment_negative_raises():
    """Negative min_adjustment is invalid."""
    bad = {
        "name": "Bad",
        "open_scene": "s1",
        "close_scene": "s2",
        "stop_scene": "s3",
        "travel_time": 30,
        "min_adjustment": -1.0,
    }
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_name_must_be_string():
    """Non-string name should raise."""
    bad = {"name": 123, "open_scene": "s1", "close_scene": "s2",
           "stop_scene": "s3", "travel_time": 30}
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_scene_reference_must_be_string():
    """Scene refs must be strings."""
    bad = {
        "name": "Bad", "open_scene": None, "close_scene": "s2",
        "stop_scene": "s3", "travel_time": 30,
    }
    with pytest.raises(VolInvalid):
        SHADE_SCHEMA(bad)


def test_shade_schema_for_entry_is_exported():
    """shade_schema_for_entry should be the same callable as _SCHEMA."""
    from custom_shades.config import shade_schema_for_entry

    valid = {
        "name": "X",
        "open_scene": "a",
        "close_scene": "b",
        "stop_scene": "c",
        "travel_time": 30,
    }
    result1 = SHADE_SCHEMA(valid)
    result2 = shade_schema_for_entry(valid)
    assert result1 == result2
