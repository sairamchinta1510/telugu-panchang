import importlib
import sys
import types
from datetime import datetime

import pytest

LAT, LON = 17.38, 78.49
TZ = "Asia/Kolkata"
MAIN_JD = 100.0
RISE_JD = 101.0
SET_JD = 102.0
PREV_AMAVASYA_JD = 10.0
NEXT_AMAVASYA_JD = 11.0


def _fmt_mins(m: float) -> str:
    m = m % (24 * 60)
    return f"{int(m // 60):02d}:{int(m % 60):02d}"


def _load_module_for(local_dt: datetime):
    fake_astro = types.ModuleType("compute.astro")
    fake_astro.sun_longitude = lambda jd: {
        PREV_AMAVASYA_JD: 0.0,
        NEXT_AMAVASYA_JD: 30.0,
    }.get(jd, 40.0)
    fake_astro.moon_longitude = lambda jd: 50.0
    fake_astro.moon_sun_elongation = lambda jd: 48.0
    fake_astro.get_sunrise_sunset = lambda jd, lat, lon: (RISE_JD, SET_JD)
    fake_astro.find_next_index_change = lambda jd, fn, idx: None

    def jd_to_local_datetime(jd, tz_name):
        if jd == RISE_JD:
            return local_dt.replace(hour=6, minute=0, second=0)
        if jd == SET_JD:
            return local_dt.replace(hour=18, minute=0, second=0)
        return local_dt

    fake_astro.jd_to_local_datetime = jd_to_local_datetime

    sys.modules["swisseph"] = types.ModuleType("swisseph")
    sys.modules["compute.astro"] = fake_astro

    panchang_module = importlib.import_module("compute.panchang")
    panchang_module = importlib.reload(panchang_module)
    panchang_module._find_amavasya = lambda jd_ref, forward=True: NEXT_AMAVASYA_JD if forward else PREV_AMAVASYA_JD
    return panchang_module


@pytest.mark.parametrize(
    ("local_dt", "expected_vaaram", "expected_slots"),
    [
        (datetime(2026, 5, 17, 12, 0), "Sunday", [(6, 1)]),
        (datetime(2026, 5, 18, 12, 0), "Monday", [(7, 1), (15, 1)]),
        (datetime(2026, 5, 19, 12, 0), "Tuesday", [(8, 2)]),
    ],
)
def test_compute_panchang_returns_dur_muhurtam_from_weekday_table(local_dt, expected_vaaram, expected_slots):
    panchang_module = _load_module_for(local_dt)
    panchang = panchang_module.compute_panchang(MAIN_JD, LAT, LON, TZ)

    rise_mins = 6 * 60
    mins_per_muhurta = (12 * 60) / 30.0
    expected_periods = []
    for start_muhurta, duration in expected_slots:
        start = rise_mins + (start_muhurta - 1) * mins_per_muhurta
        end = start + duration * mins_per_muhurta
        expected_periods.append({"start": _fmt_mins(start), "end": _fmt_mins(end)})

    assert panchang["vaaram"]["en"] == expected_vaaram
    assert panchang["dur_muhurtam"] == expected_periods
