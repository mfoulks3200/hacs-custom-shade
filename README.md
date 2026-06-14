# Custom Shades Integration for Home Assistant

A custom integration that adds per-shade `cover` entities to Home Assistant. Each shade tracks its position via timing (using configured travel time) and supports open, close, stop, and set-position operations through scene calls on a SmartBlinds-compatible hub.

## Installation

Add this repository as a [Custom Repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS:

1. In HACS, go to **Configuration → Custom repositories**
2. Select "Integration" and paste the URL of this repo
3. Install and restart Home Assistant

## Configuration

Add a `shades:` block under `custom_shades:` in your YAML configuration:

```yaml
# Example: two shades with different travel times
homeassistant:
  custom_components:
    custom_shades:

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

Each shade config requires an `open_scene`, `close_scene`, and `stop_scene` — these are Home Assistant `scene.turn_on` calls that the integration invokes at computed durations based on how far the shade needs to move.

## Features

- **Position tracking** — each shade reports a 0–100% position, updated every second during movement
- **Linear interpolation** — duration between two positions is proportional to travel time (e.g., half-way = half the configured travel time)
- **Min adjustment threshold** — small movements below `min_adjustment` are silently skipped to avoid unnecessary scene calls
- **Sync button** — a companion button entity resets position tracking back to `initial_position`

## Requirements

- Home Assistant 2026.6+
- SmartBlinds or compatible device with scenes set up for open/close/stop per shade
