"""pytest configuration -- make custom_shades importable from tests."""
import sys
from pathlib import Path

# The actual package lives at custom_components/custom_shades/ but tests
# import via `custom_shades.config`, so add that directory as a top-level
# import path so the module namespace works.
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

import unittest.mock

# homeassistant is not installed in our test env -- mock it so config tests can
# run without pulling in the full HA framework (Task 3+ will use real hass).

# Build a proper chain for async_track_time_interval.
_mock_helpers = unittest.mock.MagicMock()
_mock_helpers.event.async_track_time_interval.return_value = lambda: None
_typing_mod = unittest.mock.MagicMock()
_typing_mod.ConfigType = dict  # pragma: no cover
_mock_helpers.typing = _typing_mod
sys.modules.setdefault("homeassistant.helpers", _mock_helpers)
sys.modules["homeassistant.helpers.event"] = _mock_helpers
sys.modules["homeassistant.helpers.typing"] = _typing_mod

# homeassistant.helpers.entity_platform — needed by services.py.
entity_platform_module = sys.modules.setdefault(
    "homeassistant.helpers.entity_platform", _mock_helpers  # noqa: F821
)

# homeassistant.components.cover with CoverEntityFeature enum.
_mock_cover = unittest.mock.MagicMock()
_mock_cover.CoverEntityFeature.OPEN = 1
_mock_cover.CoverEntityFeature.CLOSE = 2
_mock_cover.CoverEntityFeature.SET_POSITION = 4
_mock_cover.CoverEntityFeature.STOP = 8


class _FakeCoverEntity:
    def __init__(self, *a, **kw):
        pass

    async_write_ha_state = lambda self: None


_mock_cover.CoverEntity = _FakeCoverEntity
sys.modules.setdefault("homeassistant.components", unittest.mock.MagicMock())
sys.modules["homeassistant.components.cover"] = _mock_cover

# Top-level and sub-modules.
for _mod in ("homeassistant", "homeassistant.config_entries", "homeassistant.core"):
    sys.modules.setdefault(_mod, unittest.mock.MagicMock())

# voluptuous — not installed in test env; mock enough for import paths used by tests.
_mock_vo = unittest.mock.MagicMock()
_mock_vo.Invalid = type("Invalid", (Exception,), {})  # pragma: no cover
_mock_vo.Required = str  # minimal stub that works for our use cases
_mock_vo.Optional = unittest.mock.MagicMock(side_effect=lambda k, **kw: k)
_mock_vo.All = unittest.mock.MagicMock(return_value=lambda x: x)
_mock_vo.Coerce = unittest.mock.MagicMock(side_effect=lambda f: lambda x: f(x))
_mock_vo.Range = unittest.mock.MagicMock()
_mock_vo.Any = unittest.mock.MagicMock()
sys.modules.setdefault("voluptuous", _mock_vo)
