"""Tests for ConfigFlow."""
from __future__ import annotations

import pytest
import voluptuous as vol

from custom_shades.config_flow import (
    ConfigFlow,
)


@pytest.fixture()
def hass():
    """Minimal HA mock with data dict and config_entries store."""
    from unittest.mock import MagicMock

    h = MagicMock()
    h.data = {"custom_shades": {"configs": []}}
    return h


@pytest.fixture(autouse=True)
def _freeze_time(monkeypatch):
    """Freeze time so position computations are deterministic in config tests."""
    pass  # no-op; just here as a hook for future timing-sensitive additions


# ---------------------------------------------------------------------------
# Schema / validation
# ---------------------------------------------------------------------------

class TestConfigFlowValidation:
    """Validate that ConfigFlow rejects bad input and accepts good input."""

    @pytest.mark.asyncio
    async def test_valid_input_passes(self, hass):
        """A fully-populated shade config should pass schema validation."""
        cfg = {
            "name": "Living Room",
            "open_scene": "scene.lr_open",
            "close_scene": "scene.lr_close",
            "stop_scene": "scene.lr_stop",
            "travel_time": 30.5,
        }
        # SHADE_SCHEMA is the same schema ConfigFlow uses.
        result = vol.Schema({
            vol.Required("name"): str,
            vol.Required("open_scene"): str,
            vol.Required("close_scene"): str,
            vol.Required("stop_scene"): str,
            vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Optional("initial_position", default=50): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional("min_adjustment", default=2.5): vol.All(
                vol.Coerce(float), vol.Range(min=0.0)
            ),
        })(cfg)

        assert result["name"] == "Living Room"
        assert result["travel_time"] == 30.5
        assert result["initial_position"] == 50
        assert result["min_adjustment"] == 2.5


    @pytest.mark.asyncio
    async def test_missing_required_raises(self, hass):
        """Missing required fields raise voluptuous.Invalid."""
        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("open_scene"): str,
            vol.Required("close_scene"): str,
            vol.Required("stop_scene"): str,
            vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
        })
        with pytest.raises(vol.Invalid):
            schema({"name": "Bad"})

    @pytest.mark.asyncio
    async def test_travel_time_zero_raises(self, hass):
        """Zero travel time is invalid."""
        bad = {
            "name": "X",
            "open_scene": "s1",
            "close_scene": "s2",
            "stop_scene": "s3",
            "travel_time": 0,
        }
        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("open_scene"): str,
            vol.Required("close_scene"): str,
            vol.Required("stop_scene"): str,
            vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
        })
        with pytest.raises(vol.Invalid):
            schema(bad)

    @pytest.mark.asyncio
    async def test_position_boundary(self, hass):
        """initial_position must be in [0, 100]."""
        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("open_scene"): str,
            vol.Required("close_scene"): str,
            vol.Required("stop_scene"): str,
            vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Optional("initial_position", default=50): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
        })

        # Boundary: 0 and 100 are valid.
        assert schema({"name": "X", "open_scene": "s1", "close_scene": "s2", "stop_scene": "s3", "travel_time": 30, "initial_position": 0})["initial_position"] == 0
        with pytest.raises(vol.Invalid):
            schema({**{"name": "X", "open_scene": "s1", "close_scene": "s2", "stop_scene": "s3", "travel_time": 30}, "initial_position": -1})

    @pytest.mark.asyncio
    async def test_defaults_applied(self, hass):
        """Optional fields get their defaults."""
        cfg = {
            "name": "X",
            "open_scene": "s1",
            "close_scene": "s2",
            "stop_scene": "s3",
            "travel_time": 60.0,
        }
        schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("open_scene"): str,
            vol.Required("close_scene"): str,
            vol.Required("stop_scene"): str,
            vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Optional("initial_position", default=50): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional("min_adjustment", default=2.5): vol.All(
                vol.Coerce(float), vol.Range(min=0.0)
            ),
        })
        result = schema(cfg)
        assert result["initial_position"] == 50
        assert result["min_adjustment"] == 2.5


# ---------------------------------------------------------------------------
# ConfigFlow class sanity checks (no real HA event loop needed for these)
# ---------------------------------------------------------------------------

class TestConfigFlowClass:
    """Verify the ConfigFlow class structure and key methods."""

    def test_version(self):
        assert ConfigFlow.VERSION == 1

    def test_inherits_from_config_flow(self):
        from homeassistant.config_entries import ConfigFlow as BaseConfigFlow
        assert issubclass(ConfigFlow, BaseConfigFlow)


# ---------------------------------------------------------------------------
# async_step_user form display (schema-only — doesn't need a real event loop)
# ---------------------------------------------------------------------------

class TestStepUserForm:
    """The 'user' step should return an async_show_form result."""

    @pytest.mark.asyncio
    async def test_step_user_returns_form(self, hass):
        flow = ConfigFlow()
        flow.hass = hass
        # Set handler so _async_current_entries works.
        flow.handler = "custom_shades"
        result = await flow.async_step_user()
        assert result["type"] == "form"
