# Custom Shades — Agent Guide

## What This Project Does

A Home Assistant custom integration that exposes smart blinds/shades as `cover` entities, tracking position via timing rather than physical feedback. Each shade fires SmartBlinds-compatible scenes at computed offsets to achieve desired positions.

## Architecture Overview

```
custom_components/custom_shades/
  __init__.py      # YAML setup + ConfigEntry lifecycle
  config.py        # Voluptuous schema & validation
  shade.py         # CustomShade (cover) + SyncButtonEntity classes
  cover.py         # Entity platform discovery & registration
  config_flow.py   # UI-based ConfigFlow / OptionsFlow
```

Key design decisions:
- **No physical sensor** — position is entirely computed from movement duration. This means the entity knows where it *thinks* it is but has no feedback if the shade jams or moves differently than expected.
- **Scene-based control** — each shade calls `scene.turn_on` on pre-configured HA scenes (open/close/stop) rather than direct API calls to a hub.
- **Dual setup path** — YAML config via `async_setup()` and UI config via ConfigFlow, both writing into the same `hass.data["custom_shades"]["configs"]` store.

## Key Code Patterns

### Duration computation (pure function)
```python
def compute_duration_for_position(start_pos: float, end_pos: float, travel_time: float) -> float:
    distance = abs(end_pos - start_pos) / 100.0
    return round(distance * travel_time, 3)
```

### Active move tracking
When a movement starts in `async_set_cover_position`, the entity records `move_start_time`, `move_duration`, and target position. An interval timer calls back every second to refresh state during transit. The timer is cancelled on stop or when another command arrives.

### Min adjustment threshold
Moves below `min_adjustment` (default 2.5%) are skipped entirely — no scene call, no timing logic. This prevents noisy micro-adjustments from degrading motor life.

## Testing Conventions

```bash
pytest tests/   # async mode enabled via pyproject.toml
```

- Tests use `asyncio` fixtures with mocked `hass.services.async_call` and `hass.helpers.event.async_track_time_interval`.
- Pure functions (duration computation) have their own test file with no mocks.
- Entity behavior is tested in isolation; integration tests are minimal at this stage.

## Known Issues & TODOs

See [TODO.md](./TODO.md) for the living backlog. Top items:

1. **SyncButtonEntity should inherit `ButtonEntity`** — currently a `CoverEntity` with zero features as a workaround
2. **ConfigFlow entries lack unique_id** — causes duplicate entries on re-add
3. **No cleanup of `_tick` timer on unload/reload** — HA tolerates it but it's technically incorrect

## Git Workflow

- Branch off `main`, work in feature branches, merge back with squash commits.
- Commit messages follow the convention: `<scope>: <description>` (e.g., `shade: add sync button entity`).
- Run tests before pushing; CI is not yet configured but local pytest should pass on every change to `custom_components/`.

## Adding a New Shade

1. Add config under `shades:` in YAML, or use the UI Config Flow.
2. The integration auto-discovers new configs via the entity platform in `cover.py` — no manual registration needed.
3. Each shade gets both a `cover.<shade_name>` and a `cover.<shade_name>_sync` (the sync button).

## Testing Changes

Before committing, verify:
```bash
cd tests && pytest -v  # all tests pass
```

If modifying entity behavior, add or update corresponding tests in the appropriate test file. Duration computation changes need their own unit test since it's pure logic.
