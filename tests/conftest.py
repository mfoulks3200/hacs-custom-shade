import pytest
"""pytest configuration -- make custom_shades importable from tests."""
import asyncio
import sys
from pathlib import Path

# The actual package lives at custom_components/custom_shades/ but tests
# import via `custom_shades.config`, so add that directory as a top-level
# import path so the module namespace works.
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    return asyncio.new_event_loop()
