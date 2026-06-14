"""pytest configuration — make custom_shades importable from tests."""
import sys
from pathlib import Path

# The actual package lives at custom_components/custom_shades/ but tests
# import via `custom_shades.config`, so add that directory as a top-level
# import path so the module namespace works.
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

import unittest.mock

# homeassistant is not installed in our test env — mock it so config tests can
# run without pulling in the full HA framework (Task 3+ will use real hass).
for _mod in ("homeassistant", "homeassistant.config_entries", "homeassistant.core"):
    sys.modules.setdefault(_mod, unittest.mock.MagicMock())

