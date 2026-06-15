"""Custom Shades integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

def async_migrate_entry(hass, entry):
    """Migrate old config entries to the current version."""
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
