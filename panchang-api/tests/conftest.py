import sys
import pytest
from unittest.mock import MagicMock

# Only mock swisseph and its dependent modules when swisseph is NOT available.
# When the real swisseph is installed (e.g. for local dev with Python 3.11),
# use the real modules so that panchang/astro accuracy tests pass.
try:
    import swisseph  # noqa: F401 — just testing availability
    _swisseph_available = True
except ImportError:
    _swisseph_available = False

if not _swisseph_available:
    sys.modules['swisseph'] = MagicMock()
    if 'compute.astro' not in sys.modules:
        sys.modules['compute.astro'] = MagicMock()
    if 'compute.panchang' not in sys.modules:
        sys.modules['compute.panchang'] = MagicMock()


@pytest.fixture(autouse=True)
def _restore_compute_modules():
    """Save and restore compute.* entries in sys.modules around every test.

    _load_finder (test_muhoortam.py) replaces compute.astro / compute.panchang /
    compute.birth_chart with fakes and never restores them, which poisons
    test_panchang.py, test_sankalpam.py, and test_handler.py when they run later.
    """
    saved = {k: v for k, v in sys.modules.items() if k.startswith("compute")}
    yield
    # Remove any compute keys the test added or replaced
    for key in list(sys.modules):
        if key.startswith("compute"):
            if key in saved:
                sys.modules[key] = saved[key]
            else:
                del sys.modules[key]

