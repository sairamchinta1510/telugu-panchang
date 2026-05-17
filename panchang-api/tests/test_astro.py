import pytest
from compute.astro import (
    local_date_to_jd,
    sun_longitude,
    moon_longitude,
    moon_sun_elongation,
    get_sunrise_sunset,
    jd_to_local_datetime,
)

LAT, LON = 17.38, 78.49  # Vizag/Hyderabad
TZ = "Asia/Kolkata"
# 2026-05-17 local noon JD
JD_2026_05_17 = local_date_to_jd(2026, 5, 17, TZ)


def test_sun_longitude_range():
    lon = sun_longitude(JD_2026_05_17)
    assert 0 <= lon < 360


def test_moon_longitude_range():
    lon = moon_longitude(JD_2026_05_17)
    assert 0 <= lon < 360


def test_elongation_range():
    e = moon_sun_elongation(JD_2026_05_17)
    assert 0 <= e < 360


def test_sun_in_vrishabha_may_2026():
    # Sun should be in Vrishabha (Taurus) sidereal, rashi index 1 (30-60°)
    lon = sun_longitude(JD_2026_05_17)
    rashi = int(lon / 30)
    assert rashi == 1, f"Expected Vrishabha (1), got rashi {rashi} (lon={lon:.2f})"


def test_sunrise_sunset_order():
    rise_jd, set_jd = get_sunrise_sunset(JD_2026_05_17, LAT, LON)
    assert rise_jd < set_jd
    # Sunrise should be roughly 6am local = ~0:44 UTC for IST (UTC+5:30)
    rise_hour_utc = ((rise_jd + 0.5) % 1) * 24
    assert 0 <= rise_hour_utc <= 4, f"Unexpected sunrise UTC hour: {rise_hour_utc:.2f}"


def test_jd_to_local_datetime():
    # JD 2461178.0 is approximately 2026-05-17 noon UTC
    # In IST (UTC+5:30) that is still 2026-05-17
    dt = jd_to_local_datetime(JD_2026_05_17, TZ)
    assert dt.year == 2026
    assert dt.month == 5
    assert dt.day == 17
    assert dt.tzinfo is not None
