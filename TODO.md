# Custom Shades — Remaining Work (2026-06-14)

## Before 1.0 Release

### [ ] Fix SyncButtonEntity to use ButtonEntity instead of CoverEntity

In `custom_shades/shade.py`, the `SyncButtonEntity` class inherits from `CoverEntity` with `_attr_supported_features = 0`. This is a workaround for HA's button platform registration mechanism, but it's semantically wrong and won't integrate properly with HA UI components.

**Fix:** Replace:
```python
class SyncButtonEntity(CoverEntity):
    _attr_should_poll = False
    _attr_supported_features = CoverEntityFeature(0)
```
With:
```python
from homeassistant.components.button import Button, ButtonEntityDescription

class SyncButtonEntity(ButtonEntity):
    def __init__(self, shade):
        self._shade = shade
        self._name = f"{shade.name} (Sync)"

    @property
    def name(self) -> str:
        return self._name

    async def async_press(self) -> None:
        initial = self._shade._config.get("initial_position", 50)
        self._shade.update_position(initial)
        await self._shade._cancel_current_move()
        self.async_write_ha_state()
```

### [ ] Set unique_id on ConfigFlow entries

In `custom_shades/config_flow.py`, the entry is created via `self.async_create_entry(title=..., data=dict(validated))` without setting `unique_id`. HA generates a random UUID, so removing and re-adding the same shade creates two independent entries.

**Fix:** In `async_step_user`, add:
```python
if existing := next((e for e in self._async_current_entries() if e.title == user_input["name"]), None):
    return self.async_abort(reason="already_exists")
# ... then before async_create_entry, set unique_id:
self.context["unique_id"] = user_input["name"]  # or some stable identifier
```

## Completed (9 commits)

- Scaffolding + manifest
- Config validation with voluptuous  
- CustomShade entity with position tracking and scene calling
- Integration setup — YAML config wiring
- Entity platform (cover.py) for shade discovery
- HACS distribution structure + README
- Pytest/asyncio test infrastructure
- UI configuration flow via ConfigFlow

## Known Issues (from final review)

- `_tick` closure captures `self`; no cleanup on unload/reload (not critical — HA tolerates it)
- No explicit wraparound protection when shade is already at 0% or 100% (duration=0 handles this naturally, but min_adjustment could still trigger a scene call if distance >= threshold)
