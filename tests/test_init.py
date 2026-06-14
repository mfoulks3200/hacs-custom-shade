"""Tests for custom_shades integration setup."""
import pytest

from custom_shades import async_setup


@pytest.fixture()
def hass():
    """Minimal HA mock with data dict for config storage."""
    return _FakeHass()


class _FakeHass:
    """Lightweight HA mock — enough for __init__.py tests."""

    def __init__(self) -> None:
        self.data: dict = {}

    # ConfigEntry and other HA classes are mocked at module level by conftest.


async def test_async_setup_parses_shade_config():
    """A valid 'shades' mapping should return True and store configs."""
    config = {
        "shades": {
            "bedroom_left": {
                "name": "Bedroom Left Shade",
                "open_scene": "scene.bl_open",
                "close_scene": "scene.bl_close",
                "stop_scene": "scene.bl_stop",
                "travel_time": 30.5,
                "initial_position": 75,
            }
        }
    }

    hass = _FakeHass()
    result = await async_setup(hass, config)

    assert result is True
    assert hass.data["custom_shades"]["configs"] is not None
    configs = hass.data["custom_shades"]["configs"]
    assert len(configs) == 1
    assert configs[0]["name"] == "Bedroom Left Shade"
    assert configs[0]["travel_time"] == pytest.approx(30.5)


async def test_async_setup_parses_multiple_shades():
    """Multiple shade entries should all be stored."""
    config = {
        "shades": {
            "living_room": {
                "name": "Living Room",
                "open_scene": "scene.lr_open",
                "close_scene": "scene.lr_close",
                "stop_scene": "scene.lr_stop",
                "travel_time": 45.0,
            },
            "office": {
                "name": "Office",
                "open_scene": "scene.of_open",
                "close_scene": "scene.of_close",
                "stop_scene": "scene.of_stop",
                "travel_time": 60.0,
            }
        }
    }

    hass = _FakeHass()
    result = await async_setup(hass, config)

    assert result is True
    configs = hass.data["custom_shades"]["configs"]
    assert len(configs) == 2


async def test_async_setup_returns_false_without_shades_key():
    """Missing 'shades' key should return False without touching hass.data."""
    config = {"something_else": {}}

    hass = _FakeHass()
    result = await async_setup(hass, config)

    assert result is False
    assert "custom_shades" not in hass.data


async def test_invalid_config_raises_error():
    """A shade with missing required fields should raise voluptuous.Invalid."""
    bad = {"shades": {"bad_entity": {"name": "Missing fields"}}}

    hass = _FakeHass()
    with pytest.raises(Exception):  # voluptuous raises vol.Invalid
        await async_setup(hass, bad)


async def test_empty_shades_mapping_returns_false():
    """Empty 'shades: {}' should return False — nothing to set up."""
    config = {"shades": {}}

    hass = _FakeHass()
    result = await async_setup(hass, config)

    assert result is False


async def test_hass_data_is_reattached():
    """Config storage uses hass.data.setdefault so it survives multiple setups."""
    config1 = {"shades": {}}  # missing key — returns False immediately
    config2 = {
        "shades": {
            "kitchen": {
                "name": "Kitchen",
                "open_scene": "scene.k_open",
                "close_scene": "scene.k_close",
                "stop_scene": "scene.k_stop",
                "travel_time": 20.0,
            }
        }
    }

    hass = _FakeHass()
    await async_setup(hass, config1)  # returns False, no data written
    assert "custom_shades" not in hass.data

    result2 = await async_setup(hass, config2)
    assert result2 is True
    assert len(hass.data["custom_shades"]["configs"]) == 1


async def test_async_setup_stores_defaults():
    """Optional fields should be filled with defaults before storage."""
    config = {
        "shades": {
            "minimal": {
                "name": "Minimal Shade",
                "open_scene": "s1",
                "close_scene": "s2",
                "stop_scene": "s3",
                "travel_time": 30.0,
            }
        }
    }

    hass = _FakeHass()
    await async_setup(hass, config)

    cfg = hass.data["custom_shades"]["configs"][0]
    assert cfg["initial_position"] == 50
    assert cfg["min_adjustment"] == 2.5


async def test_config_schema_allows_extra_top_level_keys():
    """Config may include other keys (e.g., 'automation') alongside 'shades'."""
    config = {
        "automation": {"some_thing": True},
        "shades": {
            "hallway": {
                "name": "Hallway",
                "open_scene": "scene.h_open",
                "close_scene": "scene.h_close",
                "stop_scene": "scene.h_stop",
                "travel_time": 15.0,
            }
        },
    }

    hass = _FakeHass()
    result = await async_setup(hass, config)

    assert result is True
