"""Custom cover entity for smart shades with position tracking."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval


_LOGGER = logging.getLogger(__name__)


def compute_duration_for_position(
    start_pos: float, end_pos: float, travel_time: float
) -> float:
    """Compute how long it takes to move between two positions.

    Positions are 0-100 (0=closed, 100=open). Travel time is the full
    cycle from one extreme to the other. Returns seconds -- never negative.
    """
    distance = abs(end_pos - start_pos) / 100.0
    return round(distance * travel_time, 3)


class CustomShade(CoverEntity):
    """A shade entity that tracks position via timing."""

    _attr_should_poll = False
    _attr_device_class: str | None = "shade"
    # These are overridden by properties with computation logic.
    _attr_current_cover_position: int | None = None
    _attr_is_closed: bool | None = None

    def __init__(self, config: dict) -> None:
        super().__init__()
        self._config = config
        self._name = self._config["name"]
        self._travel_time = float(self._config["travel_time"])
        self._min_adjustment = float(
            self._config.get("min_adjustment", 2.5)
        )

        # Internal state (not exposed to HA directly, set via properties)
        raw_pos = self._config.get("initial_position")
        self._last_known_position: float | None = float(raw_pos) if raw_pos is not None else None
        self._is_opening = False
        self._is_closing = False

        # Initialize closed state from initial position.
        self._attr_is_closed = (self._last_known_position == 0) if self._last_known_position is not None else None

        # Movement tracking during active moves
        self._move_start_time: float | None = None
        self._move_duration: float | None = None
        self._move_target_pos: int | None = None
        self._move_start_pos: int | None = None
        self._cancel_move_timer = None  # callable; cancelled when movement ends

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_cover_position(self) -> int | None:
        """Return tracked position, accounting for active move progress."""
        if (
            self._move_start_time is not None
            and self._move_duration is not None
            and self._move_target_pos is not None
        ):
            elapsed = time.monotonic() - self._move_start_time
            fraction = min(elapsed / self._move_duration, 1.0)
            start = float(self._move_start_pos or 0)
            return round(start + (self._move_target_pos - start) * fraction)
        return int(round(self._last_known_position)) if self._last_known_position is not None else None

    @property
    def is_opening(self) -> bool:
        """Return True while actively moving up."""
        if (
            self._move_start_time is not None
            and self._move_target_pos is not None
            and self._move_start_pos is not None
        ):
            return self._move_target_pos >= self._move_start_pos
        return False

    @property
    def is_closing(self) -> bool:
        """Return True while actively moving down."""
        if (
            self._move_start_time is not None
            and self._move_target_pos is not None
            and self._move_start_pos is not None
        ):
            return self._move_target_pos < self._move_start_pos
        return False

    @property
    def supported_features(self) -> CoverEntityFeature:
        features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        if self.current_cover_position is not None:
            features |= CoverEntityFeature.SET_POSITION
        return features

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set shade to a specific position."""
        target = int(kwargs["position"])  # HA validates 0-100 range
        current = self.current_cover_position
        if current is None:
            _LOGGER.warning("Cannot set position -- unknown current position")
            return

        distance = abs(target - current)
        if distance < self._min_adjustment:
            _LOGGER.debug(
                "Position change %.0f%% below min threshold %s%% -- skipping",
                distance, self._min_adjustment,
            )
            return

        # Cancel any in-progress movement (HA API prevents overlapping, but be safe)
        await self._cancel_current_move()

        duration = compute_duration_for_position(current, target, self._travel_time)
        if duration <= 0:
            self._last_known_position = float(target)
            return

        direction_opening = target > current
        scene_to_call = (
            self._config["open_scene"] if direction_opening else self._config["close_scene"]
        )

        try:
            await self.hass.services.async_call(  # type: ignore[union-attr]
                "scene", "turn_on", {"entity_id": scene_to_call}
            )
        except Exception as exc:
            _LOGGER.error("Failed to call %s: %s", scene_to_call, exc)
            return

        # Start tracking movement state and position updates
        self._move_start_time = time.monotonic()
        self._move_duration = duration
        self._move_target_pos = target
        self._move_start_pos = current

        def _tick(now: Any) -> None:  # noqa: ANN401
            """Called every second during move to refresh reported position."""
            self.async_write_ha_state()

        self._cancel_move_timer = async_track_time_interval(  # type: ignore[union-attr]
            self.hass, _tick, timedelta(seconds=1)
        )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop shade movement."""
        await self._cancel_current_move()
        try:
            await self.hass.services.async_call(  # type: ignore[union-attr]
                "scene", "turn_on", {"entity_id": self._config["stop_scene"]}
            )
        except Exception as exc:
            _LOGGER.error("Failed to call stop scene %s: %s", self._config["stop_scene"], exc)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the shade fully."""
        await self.async_set_cover_position(position=100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the shade fully."""
        await self.async_set_cover_position(position=0)

    async def _cancel_current_move(self) -> None:
        """Cancel any in-progress movement and stop scenes."""
        if self._cancel_move_timer is not None:
            self._cancel_move_timer()  # type: ignore[misc]
            self._cancel_move_timer = None

        self._move_start_time = None
        self._move_duration = None
        self._move_target_pos = None
        self._move_start_pos = None

    def update_position(self, new_position: float) -> None:
        """Update tracked position after movement completes."""
        self._last_known_position = new_position
        # is_closed depends on position -- 0% means closed.
        self._attr_is_closed = (new_position <= 0)


class SyncButtonEntity(CoverEntity):
    """A button-like entity for resetting shade position tracking.

    Uses CoverEntity as a base solely to leverage HA's existing button platform
    which we register via the integration setup. In practice this behaves like
    an input_button -- when pressed it resets the associated shade's state.
    """

    _attr_should_poll = False
    # We override supported_features so users see a "button" in Lovelace
    _attr_supported_features: CoverEntityFeature = CoverEntityFeature(0)  # no cover features

    def __init__(self, shade: CustomShade):
        super().__init__()
        self._shade = shade
        self._name = f"{shade.name} (Sync)"

    @property
    def name(self) -> str:
        return self._name

    async def async_press(self) -> None:
        """Reset position tracking to initial value."""
        initial = float(self._shade._config.get("initial_position", 50))
        self._shade.update_position(initial)
        await self._shade._cancel_current_move()
        # Update our own state too (for HA entity platform consistency)
        self.async_write_ha_state()
