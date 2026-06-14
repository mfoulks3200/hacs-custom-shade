"""Services and entities for custom shades."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .shade import CustomShade, SyncButtonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up shade and sync-button entities from a config entry."""
    # For YAML-based setup (no config_flow), configs live in hass.data["custom_shades"]
    store = hass.data.get("custom_shades") or {}
    raw_configs = store.get("configs", [])

    if not raw_configs:
        _LOGGER.warning("No shade configs found -- nothing to register")
        return

    entities: list[CustomShade | SyncButtonEntity] = []
    for cfg in raw_configs:
        shade = CustomShade(cfg)
        entities.append(shade)
        # Each shade gets its own sync button so users can reset tracking from Lovelace
        entities.append(SyncButtonEntity(shade))

    async_add_entities(entities, True)
