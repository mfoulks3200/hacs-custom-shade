"""Custom Shades integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .config import validate_shades_config

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
    # Each config entry contains exactly one validated shade. Store it alongside
    # any YAML configs so cover.py can find everything in hass.data["custom_shades"].
    if "configs" not in hass.data.get("custom_shades", {}):
        hass.data.setdefault("custom_shades", {})["configs"] = []

    # entry.data is a dict because ConfigFlow.async_create_entry passes data=...
    shade_config: dict | None = (
        entry.data.get("config") if isinstance(entry.data, dict) else None
    )
    if shade_config:
        hass.data["custom_shades"]["configs"].append(shade_config)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    configs = hass.data.get("custom_shades", {}).get("configs") or []
    if isinstance(entry.data, dict):
        shade_config = entry.data.get("config")
        if shade_config and shade_config in configs:
            configs.remove(shade_config)
    return True
