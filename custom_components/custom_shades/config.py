"""Config validation for custom shades."""
import voluptuous as vol

_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("open_scene"): str,
    vol.Required("close_scene"): str,
    vol.Required("stop_scene"): str,
    vol.Required("travel_time"): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
    vol.Optional("initial_position", default=50): vol.All(
        vol.Coerce(int), vol.Range(min=0, max=100)
    ),
    vol.Optional("min_adjustment", default=2.5): vol.All(
        vol.Coerce(float), vol.Range(min=0.0)
    ),
})

# Map shade entity IDs to validated config dicts
shade_schema_for_entry = _SCHEMA

# Public alias for tests and downstream consumers.
SHADE_SCHEMA = _SCHEMA


def validate_shades_config(config: dict[str, dict]) -> list[dict]:
    """Validate the top-level 'shades' key and return a list of per-shade configs."""
    shades_key = "shades"
    if shades_key not in config:
        raise vol.Invalid(f"No '{shades_key}' key found")

    shade_entries = config[shades_key]
    if not isinstance(shade_entries, dict):
        raise vol.Invalid("'shades' must be a mapping of entity_id -> config")

    return [_SCHEMA(entry) for entry in shade_entries.values()]
