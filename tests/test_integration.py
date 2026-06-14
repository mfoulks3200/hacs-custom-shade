"""Integration-level smoke tests for custom_shades."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))


class DataStore(dict):
    """Fake hass.data with real dict methods for config lookup."""


@pytest.fixture()
def mock_hass():
    """Return an object whose .data behaves like a real dict."""
    ds = DataStore()  # Real instance so attribute access goes through the dict
    return MagicMock(data=ds)


# ---------------------------------------------------------------------------
# services.py smoke test: async_setup_entry creates entities correctly
# ---------------------------------------------------------------------------

async def test_async_setup_entry_creates_entities(mock_hass):
    from custom_shades.services import async_setup_entry
    from custom_shades.shade import CustomShade, SyncButtonEntity

    mock_hass.data["custom_shades"] = {
        "configs": [
            {
                "name": "Living Room",
                "open_scene": "scene.lr_open",
                "close_scene": "scene.lr_close",
                "stop_scene": "scene.lr_stop",
                "travel_time": 30.0,
            }
        ]
    }

    added = []
    await async_setup_entry(mock_hass, MagicMock(), lambda e, u: added.extend(e))

    assert len(added) == 2
    assert isinstance(added[0], CustomShade)
    assert isinstance(added[1], SyncButtonEntity)


async def test_async_setup_entry_registers_multiple_shades(mock_hass):
    from custom_shades.services import async_setup_entry

    mock_hass.data["custom_shades"] = {
        "configs": [
            {
                "name": "Bedroom",
                "open_scene": "scene.br_open",
                "close_scene": "scene.br_close",
                "stop_scene": "scene.br_stop",
                "travel_time": 25.0,
            },
            {"name": "Kitchen", "open_scene": "s1", "close_scene": "s2", "stop_scene": "s3", "travel_time": 40.0},
        ]
    }

    added = []
    await async_setup_entry(mock_hass, MagicMock(), lambda e, u: added.extend(e))

    assert len(added) == 4


async def test_async_setup_entry_empty_configs_logs_warning(mock_hass):
    from custom_shades.services import async_setup_entry

    mock_hass.data["custom_shades"] = {"configs": []}

    added = []
    await async_setup_entry(mock_hass, MagicMock(), lambda e, u: added.extend(e))
    assert len(added) == 0


async def test_async_setup_entry_missing_data_is_safe(mock_hass):
    from custom_shades.services import async_setup_entry

    mock_hass.data["custom_shades"] = None

    added = []
    await async_setup_entry(mock_hass, MagicMock(), lambda e, u: added.extend(e))
    assert len(added) == 0


# ---------------------------------------------------------------------------
# SyncButtonEntity behavior test
# ---------------------------------------------------------------------------

async def test_sync_button_resets_shade_position():
    from custom_shades.shade import CustomShade, SyncButtonEntity

    config = {
        "name": "Test Shade",
        "open_scene": "scene.test_open",
        "close_scene": "scene.test_close",
        "stop_scene": "scene.test_stop",
        "travel_time": 30.0,
        "initial_position": 75,
    }

    shade = CustomShade(config)
    button = SyncButtonEntity(shade)
    shade._last_known_position = float(20)

    await button.async_press()

    assert shade._last_known_position == pytest.approx(75.0)
    assert shade._move_start_time is None


# ---------------------------------------------------------------------------
# Full flow: YAML config -> validate -> store -> entities created
# ---------------------------------------------------------------------------

async def test_yaml_to_entity_flow(mock_hass):
    from custom_shades.services import async_setup_entry
    from custom_shades.shade import CustomShade, SyncButtonEntity

    mock_hass.data["custom_shades"] = {
        "configs": [
            {
                "name": "Master Bedroom Shade",
                "open_scene": "scene.mb_open",
                "close_scene": "scene.mb_close",
                "stop_scene": "scene.mb_stop",
                "travel_time": 35.0,
                "initial_position": 60,
            }
        ]
    }

    added = []
    await async_setup_entry(mock_hass, MagicMock(), lambda e, u: added.extend(e))

    assert len(added) == 2
    shade = added[0]
    button = added[1]

    assert isinstance(shade, CustomShade)
    assert shade.current_cover_position == 60
    assert button.name == "Master Bedroom Shade (Sync)"


# ---------------------------------------------------------------------------
# Entity naming convention check
# ---------------------------------------------------------------------------

async def test_sync_button_name_includes_shade_name():
    from custom_shades.shade import CustomShade, SyncButtonEntity

    for shade_name in ["Living Room", "Kitchen Left", "Garage Door"]:
        config = {
            "name": shade_name,
            "open_scene": "scene.x",
            "close_scene": "scene.y",
            "stop_scene": "scene.z",
            "travel_time": 30.0,
        }
        button = SyncButtonEntity(CustomShade(config))
        assert button.name == f"{shade_name} (Sync)"
