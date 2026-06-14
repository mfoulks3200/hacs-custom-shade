# Custom Shades Integration — Design Spec

**Date:** 2026-06-14  
**Status:** Draft

## Problem Statement

Home Assistant's native `cover` entities (for blinds/shades) only support three commands: open, close, stop. There is no standard way to command a shade to go to an arbitrary percentage position when you don't have positional feedback from the device itself.

For roller shades that always take the same amount of time to travel fully up or down — regardless of their current position — we can compute exact movement durations and send open/close followed by stop at precisely the right moment. This integration provides a `cover` entity per shade that enables this workflow while hiding all timing logic from automations.

## Design Decisions

### Custom Cover Entity (Approach A)
Rather than exposing a service-only API, each shade is its own `CoverEntity`. This gives users native HA ecosystem support out of the box: Lovelace cover cards, built-in automation triggers (`cover.opened`), scripts using standard cover services, and state attributes.

### Per-Shade YAML Configuration
Each shade gets its own config block under a top-level `shades:` key in the integration configuration. This keeps things simple — no UI config flow needed for an initial release.

## Architecture

The entity class (`CustomShade`) is the core of the integration. It:

1. Stores a `last_known_position` (0–100%) tracking where the shade currently sits
2. Receives position commands via standard cover services (`set_cover_position`, `open_cover`, `close_cover`)
3. Computes direction and duration based on configured travel time
4. Calls open/close/stop scenes in sequence with proper timing
5. Optionally reports intermediate positions during movement (linear interpolation)

### Entity State Machine

| State | Meaning | Triggered by |
|-------|---------|-------------|
| `idle` | Shade is stopped at known position | Default, after sync |
| `opening` | Actively moving up toward target | After calling open_scene |
| `closing` | Actively moving down toward target | After calling close_scene |

During movement states, the entity:
- Reports intermediate positions (linear interpolation) to HA every second
- Calls stop_scene when elapsed time matches computed duration
- Returns to idle state with updated last_known_position

## Configuration Schema

Each shade requires these fields in the integration config:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Entity display name |
| `open_scene` | scene reference | yes | Scene to start opening (moving up) |
| `close_scene` | scene reference | yes | Scene to start closing (moving down) |
| `stop_scene` | scene reference | yes | Scene to stop movement at any position |
| `travel_time` | float (seconds) | yes | Full cycle time from 100% → 0% or 0% → 100% |
| `initial_position` | int (0-100) | no, default 50 | Where the shade sits at startup |
| `min_adjustment` | float (%) | no, default 2.5 | Ignore position changes smaller than this — prevents micro-adjustments from stale tracking or unreliable scene calls |

Example:

```yaml
shades:
  bedroom_left:
    name: "Bedroom Left Shade"
    open_scene: scene.bedroom_left_shade_open
    close_scene: scene.bedroom_left_shade_close
    stop_scene: scene.bedroom_left_shade_stop
    travel_time: 30.5
    initial_position: 75
    min_adjustment: 2.5

  living_room_main:
    name: "Living Room Main"
    open_scene: scene.living_room_main_open
    close_scene: scene.living_room_main_close
    stop_scene: scene.living_room_main_stop
    travel_time: 45
```

## Entity API (What HA users see)

### Standard Cover Services
All standard cover services are supported and work as expected:

- `cover.open_cover` — calls open_scene, then stop_scene after full travel_time
- `cover.close_cover` — calls close_scene, then stop_scene after full travel_time  
- `cover.set_cover_position` with position 0–100% — opens/closes for the computed duration to reach that position
- `cover.stop_cover` — stops movement at any time

### Sync Button (Entity Component)
A button entity is added per shade using HA's `button` platform. When pressed:

- Resets last_known_position to initial_position
- Sets state back to idle
- Useful after manual bumping or when tracking has drifted from failed scene calls

### Overlapping Commands
If a user commands a new position while the shade is actively moving toward a previous target, the entity cancels any in-progress movement timer and starts the new command. The `stop_cover` service is called for the old movement before beginning the new one. In practice HA prevents this at the API level (cover states are exclusive), so this edge case rarely occurs.

## Error Handling & Edge Cases

### Min Adjustment Threshold
If a commanded position differs from current by less than `min_adjustment`, the entity logs a debug message and does nothing (no scenes called). This prevents micro-adjustments caused by stale position tracking.

### Scene Call Failures
If open/close/stop scene calls raise an exception:
- The error is logged to HA's log system at error level
- Position state remains unchanged (the shade may have partially moved)
- User should run sync to reset tracking

### State During Movement
When the entity is in opening/closing state, it starts a timer. On each timer tick (~1 second):

```python
elapsed = time_since_start()
fraction_elapsed = elapsed / duration
remaining_distance = target_position - current_position
current_reported_position = start_position + (remaining_distance * fraction_elapsed)
self._available_state = "opening" or "closing"  # based on direction
```

### Position Wraparound Protection
- If commanded to open and shade is already at 100%, skip (log debug, no action)
- If commanded to close and shade is already at 0%, skip
- These checks happen before computing duration

## Data Flow

1. **User/Automation** calls `cover.set_cover_position` with target = 65%
2. **Entity** reads last_known_position (say, 80%)
3. **Compute direction:** 65 < 80 → closing
4. **Compute duration:** (|80 - 65| / 100) × travel_time = 0.15 × 30.5s ≈ 4.6s
5. **Call open/close scene** (close_scene in this case)
6. **Start timer** — reports intermediate positions every second during movement
7. **After duration:** call stop_scene, update last_known_position to 65%, return to idle state

## Files Structure

```
custom_shades/
├── __init__.py          # Integration setup, config parsing
├── shade.py             # CustomShade entity class (core logic)
└── services.py          # Sync service registration + handler
```

