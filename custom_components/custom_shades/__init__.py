"""Custom Shades integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {"shades": {str: vol.Any(dict, lambda v: True)}},
    extra=vol.ALLOW_EXTRA,
)

__all__ = ["CONFIG_SCHEMA"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the custom_shades component."""
    if "shades" not in config:
        return False

    shade_configs = validate_shades_config(config)
    if not shade_configs:
        return False

    # We store validated configs on hass for entity setup to consume.
    # In a real integration you'd use ConfigEntry options, but for YAML-only
    # we attach them here and register entities under the platform mechanism.
    hass.data.setdefault("custom_shades", {})["configs"] = shade_configs

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up custom shades from a config entry."""
    # For YAML-based setup (no config_flow), we delegate to the module-level setup.
    # If using entry storage in the future, shade configs would come from here.
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
