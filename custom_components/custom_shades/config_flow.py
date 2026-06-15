"""Config flow for Custom Shades."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorMode,
    TextSelector,
)

from .config import SHADE_SCHEMA

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain="custom_shades"):
    """Handle a user config entry for Custom Shades."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler()

    async def _show_form(self, errors: dict[str, str] | None = None) -> FlowResult:
        """Show the form to the user."""
        schema = self._default_schema()

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors or {},
        )

    @staticmethod
    def _default_schema() -> vol.Schema:
        """Return a schema with defaults pre-filled for UI display."""
        return vol.Schema({
            vol.Required("name", default="New Shade"): TextSelector({"type": "text"}),
            vol.Required("open_scene", default=""): TextSelector({"type": "text"}),
            vol.Required("close_scene", default=""): TextSelector({"type": "text"}),
            vol.Required("stop_scene", default=""): TextSelector({"type": "text"}),
            vol.Required("travel_time", default=30.0): NumberSelector(
                {"mode": NumberSelectorMode.BOX},
            ),
            vol.Optional("initial_position", default=50): NumberSelector(
                {"min": 0, "max": 100, "mode": NumberSelectorMode.BOX},
            ),
            vol.Optional("min_adjustment", default=2.5): NumberSelector(
                {"min": 0, "mode": NumberSelectorMode.BOX},
            ),
        })

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a step initiated by the user."""
        if user_input is not None:
            return await self._async_handle_submit(user_input)

        return await self._show_form()

    async def _async_handle_submit(
        self, user_input: dict[str, Any]
    ) -> FlowResult:
        """Validate and submit shade config."""
        errors: dict[str, str] = {}

        # Check that the name isn't already used by another entry.
        existing_names = {e.title for e in self._async_current_entries()}
        if user_input["name"] in existing_names:
            errors["base"] = "already_configured"

        if not errors:
            validated = SHADE_SCHEMA(user_input)
            return self.async_create_entry(
                title=validated["name"],
                data=dict(validated),
            )

        # Re-show the form on error.
        schema = vol.Schema({
            key: (vol.DefaultTo(val, key.schema))
            for key, val in self._default_schema().schema.items()
        })

        return await self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options updates (no-op for now; keeps the entry editable)."""

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
