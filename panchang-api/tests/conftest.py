import sys
from unittest.mock import MagicMock

# Only mock swisseph and astro (which requires swisseph)
# Don't mock sankalpam since it doesn't depend on swisseph
sys.modules['swisseph'] = MagicMock()

# Mock only astro and panchang (which depend on swisseph)
# sankalpam and compute package will be imported normally
if 'compute.astro' not in sys.modules:
    sys.modules['compute.astro'] = MagicMock()
if 'compute.panchang' not in sys.modules:
    sys.modules['compute.panchang'] = MagicMock()

