"""Tests for custom_shades shade entity."""
import asyncio
from unittest import mock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.cover import CoverEntityFeature

from custom_shades.shade import (
    CustomShade,
    SyncButtonEntity,
    compute_duration_for_position,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config():
    return {
        "name": "Test Shade",
        "open_scene": "scene.test_open",
        "close_scene": "scene.test_close",
        "stop_scene": "scene.test_stop",
        "travel_time": 30.5,
        "initial_position": 50,
        "min_adjustment": 2.5,
    }


@pytest.fixture()
def shade(config):
    """Create a CustomShade with mocked hass for service calling."""
    s = CustomShade(config)
    # Provide a mock hass so scene calls don't blow up in tests that trigger them.
    mock_hass = mock.MagicMock()

    async def _async_call(*args, **kwargs):
        return None

    mock_hass.services.async_call = mock.AsyncMock(side_effect=_async_call)

    # async_track_time_interval returns a callable cancel function (no-op for tests).
    mock_hass.helpers.event.async_track_time_interval.return_value = lambda: None
    s.hass = mock_hass  # type: ignore[attr-defined]
    return s


# ---------------------------------------------------------------------------
# Duration computation -- pure function, easy to unit-test
# ---------------------------------------------------------------------------


def test_compute_duration_full_open():
    assert compute_duration_for_position(0, 100, 30.5) == pytest.approx(30.5)


def test_compute_duration_full_close():
    assert compute_duration_for_position(100, 0, 30.5) == pytest.approx(30.5)


def test_compute_duration_halfway_opening():
    # Half the distance = half the time
    assert compute_duration_for_position(50, 100, 30.5) == pytest.approx(15.25)


def test_compute_duration_halfway_closing():
    assert compute_duration_for_position(75, 50, 30.5) == pytest.approx(7.625)


def test_compute_duration_no_movement():
    # Same start and end: zero time
    assert compute_duration_for_position(50, 50, 30.5) == 0.0


def test_compute_duration_small_change():
    distance = abs(50 - 48) / 100.0  # 2% of full cycle
    expected = round(distance * 30.5, 3)
    assert compute_duration_for_position(50, 48, 30.5) == pytest.approx(expected)


def test_compute_duration_roundtrip():
    duration_open = compute_duration_for_position(0, 100, 60.0)
    duration_close = compute_duration_for_position(100, 0, 60.0)
    assert duration_open == pytest.approx(duration_close)


# ---------------------------------------------------------------------------
# Entity initialization
# ---------------------------------------------------------------------------


def test_entity_name(config):
    shade_obj = CustomShade(config)
    assert shade_obj.name == "Test Shade"


def test_entity_initial_position(config):
    s = CustomShade(config)
    # initial_position is 50; current_cover_position should round to int
    assert s.current_cover_position == 50


def test_entity_is_closed_at_zero():
    cfg = {**{"name": "X", "open_scene": "a", "close_scene": "b",
              "stop_scene": "c", "travel_time": 30}, "initial_position": 0}
    s = CustomShade(cfg)
    assert s._attr_is_closed is True


def test_entity_not_closed_at_mid():
    cfg = {**{"name": "X", "open_scene": "a", "close_scene": "b",
              "stop_scene": "c", "travel_time": 30}, "initial_position": 50}
    s = CustomShade(cfg)
    assert s._attr_is_closed is False


# ---------------------------------------------------------------------------
# State reporting -- no movement in progress
# ---------------------------------------------------------------------------


def test_current_cover_position_returns_tracked_value(shade):
    shade._last_known_position = 73.0
    assert shade.current_cover_position == 73


def test_current_cover_position_rounds_down():
    cfg = {"name": "X", "open_scene": "a", "close_scene": "b",
           "stop_scene": "c", "travel_time": 30, "initial_position": 74}
    s = CustomShade(cfg)
    assert s.current_cover_position == 74


def test_current_cover_position_rounds_up():
    cfg = {"name": "X", "open_scene": "a", "close_scene": "b",
           "stop_scene": "c", "travel_time": 30, "initial_position": 76}
    s = CustomShade(cfg)
    assert s.current_cover_position == 76


def test_is_opening_false_at_rest(shade):
    shade._is_opening = False
    assert shade.is_opening is False


def test_is_closing_false_at_rest(shade):
    shade._is_closing = False
    assert shade.is_closing is False


# ---------------------------------------------------------------------------
# State reporting -- during movement
# ---------------------------------------------------------------------------


def test_state_is_opening_when_moving_up(config, shade):
    """When target > start => opening."""
    shade._move_start_time = 100.0  # arbitrary base time
    shade._move_duration = 10.0
    shade._move_target_pos = 80
    shade._move_start_pos = 50
    assert shade.is_opening is True


def test_state_is_closing_when_moving_down(config, shade):
    """When target < start => closing."""
    shade._move_start_time = 100.0
    shade._move_duration = 10.0
    shade._move_target_pos = 20
    shade._move_start_pos = 50
    assert shade.is_closing is True


def test_state_neither_opening_nor_closing_at_rest(config, shade):
    """At rest, both should be False."""
    assert not shade.is_opening and not shade.is_closing


# ---------------------------------------------------------------------------
# supported_features
# ---------------------------------------------------------------------------


def test_supported_features_has_set_position(shade):
    features = shade.supported_features
    assert features & CoverEntityFeature.SET_POSITION is CoverEntityFeature.SET_POSITION
    assert features & CoverEntityFeature.OPEN is CoverEntityFeature.OPEN
    assert features & CoverEntityFeature.CLOSE is CoverEntityFeature.CLOSE


def test_supported_features_no_set_position_when_unknown():
    """Without an initial position, SET_POSITION should not be advertised."""
    cfg = {**{"name": "X", "open_scene": "a", "close_scene": "b",
              "stop_scene": "c", "travel_time": 30},
           "initial_position": None}
    s = CustomShade(cfg)
    # current_cover_position returns None, so SET_POSITION absent
    assert (s.supported_features & CoverEntityFeature.SET_POSITION) == 0


# ---------------------------------------------------------------------------
# Min adjustment threshold
# ---------------------------------------------------------------------------


async def test_set_position_below_min_adjustment_is_ignored(shade):
    """If position change < min_adjustment, no scenes are called."""
    shade._last_known_position = 50.0
    mock_hass = shade.hass  # from fixture -- already has async_call mocked

    await shade.async_set_cover_position(position=51)

    assert shade._last_known_position == pytest.approx(50.0)
    mock_hass.services.async_call.assert_not_called()


async def test_set_position_above_min_adjustment_proceeds(shade):
    """If position change >= min_adjustment, movement proceeds."""
    shade._last_known_position = 50.0

    await shade.async_set_cover_position(position=54)

    assert shade._last_known_position == pytest.approx(50.0)  # hasn't updated yet (async move in progress)
    assert shade.hass.services.async_call.call_count == 1


# ---------------------------------------------------------------------------
# async_open_cover / async_close_cover
# ---------------------------------------------------------------------------


async def test_async_open_calls_set_position_to_100(shade):
    """open_cover should call set_cover_position(position=100)."""
    shade._last_known_position = 25.0

    await shade.async_open_cover()

    # Should have called open_scene (direction: opening)
    args, _kwargs = shade.hass.services.async_call.call_args
    assert "scene.test_open" in str(args)


async def test_async_close_calls_set_position_to_0(shade):
    """close_cover should call set_cover_position(position=0)."""
    shade._last_known_position = 75.0

    await shade.async_close_cover()

    # Should have called close_scene (direction: closing)
    args, _kwargs = shade.hass.services.async_call.call_args
    assert "scene.test_close" in str(args)


# ---------------------------------------------------------------------------
# async_stop_cover
# ---------------------------------------------------------------------------


async def test_async_stop_calls_stop_scene(shade):
    await shade.async_stop_cover()

    args, _kwargs = shade.hass.services.async_call.call_args
    assert "scene.test_stop" in str(args)


async def test_async_cancel_current_move_clears_state(shade):
    """After cancelling, all move state should be None."""
    shade._move_start_time = 100.0
    shade._move_duration = 10.0
    shade._move_target_pos = 80
    shade._move_start_pos = 50

    await shade._cancel_current_move()

    assert shade._move_start_time is None
    assert shade._move_duration is None
    assert shade._move_target_pos is None
    assert shade._move_start_pos is None


# ---------------------------------------------------------------------------
# update_position
# ---------------------------------------------------------------------------


def test_update_position_sets_last_known(shade):
    shade.update_position(73.5)
    assert shade._last_known_position == pytest.approx(73.5)
    assert shade.current_cover_position == 74


def test_update_position_at_zero_marks_closed(shade):
    shade.update_position(0)
    assert shade._attr_is_closed is True


# ---------------------------------------------------------------------------
# SyncButtonEntity
# ---------------------------------------------------------------------------


async def test_sync_button_resets_position(shade):
    btn = SyncButtonEntity(shade)
    await btn.async_press()

    # Should have reset to initial_position (50 in default config)
    assert shade._last_known_position == pytest.approx(50)


def test_sync_button_name_contains_sync():
    cfg = {**{"name": "My Shade", "open_scene": "a", "close_scene": "b",
              "stop_scene": "c", "travel_time": 30}, "initial_position": 25}
    shade_obj = CustomShade(cfg)
    btn = SyncButtonEntity(shade_obj)
    assert btn.name == "My Shade (Sync)"
