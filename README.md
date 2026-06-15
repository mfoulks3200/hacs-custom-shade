# Custom Shades Integration for Home Assistant

A custom integration that adds per-shade `cover` entities to Home Assistant, tracking each shade's position via timing rather than physical feedback.

## Features

- **Position tracking** — each shade reports a 0–100% position in real time during movement
- **Linear interpolation** — duration between positions is proportional to configured travel time (e.g. half-way = half the configured time)
- **Min adjustment threshold** — movements below `min_adjustment` are silently skipped, avoiding unnecessary scene calls
- **Sync button** — a companion entity resets position tracking back to `initial_position`
- **Open / Close / Stop / Set Position** — full cover API support via scene triggers on your SmartBlinds hub

## Installation

Add this repository as a [Custom Repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS:

1. In HACS, go to **Configuration → Custom repositories**
2. Select "Integration" and paste the URL of this repo
3. Install and restart Home Assistant
4. Add your shades via YAML config or through the UI Config Flow

## Configuration

### YAML (top-level)

Add a `shades:` block under `custom_shades:` in your YAML configuration:

```yaml
custom_shades:
  shades:
    bedroom_left:
      name: "Bedroom Left"
      open_scene: scene.bedroom_left_open
      close_scene: scene.bedroom_left_close
      stop_scene: scene.bedroom_left_stop
      travel_time: 45.0         # time to go from fully closed (0%) to fully open (100%)
      initial_position: 75       # optional — start position in percent, default 50
      min_adjustment: 2.5        # optional — skip moves below this %, default 2.5

    living_room:
      name: "Living Room"
      open_scene: scene.living_open
      close_scene: scene.living_close
      stop_scene: scene.living_stop
      travel_time: 30.0
```

### UI (Config Flow)

Alternatively, add shades through the Home Assistant UI. Each config entry represents one shade and its settings.

## Configuration Options

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | — | Display name for the shade entity |
| `open_scene` | Yes | — | HA scene entity to call when opening |
| `close_scene` | Yes | — | HA scene entity to call when closing |
| `stop_scene` | Yes | — | HA scene entity to call when stopping |
| `travel_time` | Yes | — | Seconds for full travel from closed → open (must be ≥ 0.1) |
| `initial_position` | No | 50 | Starting position in percent (0–100) |
| `min_adjustment` | No | 2.5 | Minimum position change to trigger a scene call |

## How It Works

Each shade entity is backed by scenes on your SmartBlinds-compatible hub. The integration:

1. Computes the distance between current and target positions (0–100%)
2. Scales that distance proportionally against `travel_time` to get a duration
3. Calls `scene.turn_on` for the appropriate scene (`open_scene` or `close_scene`) at that computed offset
4. Tracks position updates every second during movement via an interval timer
5. Reports accurate real-time position through `current_cover_position`

## Requirements

- Home Assistant 2026.6+
- SmartBlinds or compatible device with scenes set up for open/close/stop per shade

## Testing

```bash
pytest tests/
```

Test coverage includes:
- Duration computation (pure function, fully unit-tested)
- Entity initialization and state reporting
- Movement tracking during active moves
- Supported features flags
- Min adjustment threshold behavior
- Open/close/stop operations
- Sync button reset

## Development & Architecture

Key files:

| File | Purpose |
|------|---------|
| `config.py` | Voluptuous validation schema for shade configs |
| `shade.py` | `CustomShade` (CoverEntity) and `SyncButtonEntity` classes |
| `cover.py` | Entity platform setup — discovers configs and registers entities |
| `config_flow.py` | UI Config Flow and Options Flow handlers |
| `__init__.py` | YAML config setup + entry lifecycle |

## Known Issues & TODOs

See [TODO.md](./TODO.md) for the current backlog.

Known issues:
- **SyncButtonEntity inherits from CoverEntity** (workaround until ButtonEntity platform is wired up)
- **No unique_id on ConfigFlow entries** — removing and re-adding a shade creates duplicate entries
- `_tick` closure captures `self`; no explicit cleanup on unload/reload (HA tolerates this in practice)
