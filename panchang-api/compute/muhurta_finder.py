"""
Month scanner for auspicious muhurta dates — South Indian Telugu tradition.
Iterates every calendar day, computes panchang at sunrise,
and returns days that pass all auspiciousness checks including
Masa Shuddhi (Chaturmas), Tara Balam, and Panchaka Dosha.
Includes Rahu Kalam, Yamaganda, and Gulika Kalam in output (essential South Indian exclusion periods).
"""
from __future__ import annotations
import calendar

from .astro import (
    local_date_to_jd, get_sunrise_sunset,
    jd_to_local_datetime, moon_longitude, moon_sun_elongation,
)
from .panchang import compute_panchang
from .birth_chart import compute_lagna
from .muhurta_rules import is_auspicious, compute_kalams

_MONTH_TE = [
    "జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్",
    "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్",
]


def find_muhurtas_for_month(
    year: int,
    month: int,
    lat: float,
    lon: float,
    tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
) -> list[dict]:
    """Scan every day of the month and return auspicious muhurta days.

    Each result dict contains:
    - Telugu-formatted date, vaaram, tithi, nakshatra, yoga
    - sunrise, sunset times
    - rahu_kalam, yamaganda, gulika_kalam windows (must be avoided during ceremony)
    - dur_muhurtam and varjyam windows (from existing panchang compute)
    """
    results = []
    _, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        try:
            jd      = local_date_to_jd(year, month, day, tz_name)
            rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)

            moon_lon  = moon_longitude(rise_jd)
            elong     = moon_sun_elongation(rise_jd)
            naks_idx  = int(moon_lon / (360.0 / 27)) % 27
            tithi_idx = int(elong / 12) % 30
            day_rashi_idx = int(moon_lon / 30) % 12

            dt_rise   = jd_to_local_datetime(rise_jd, tz_name)
            sun_idx   = (dt_rise.weekday() + 1) % 7   # Sunday=0 … Saturday=6

            lagna_idx = compute_lagna(rise_jd, lat, lon)

            # Get panchang for Masa Shuddhi check (masam name + adhika flag) and Telugu labels
            pan = compute_panchang(jd, lat, lon, tz_name)
            masam_name = pan["masam"]["en"]
            is_adhika  = pan["masam"]["adhika"]

            if not is_auspicious(
                naks_idx, tithi_idx, sun_idx, lagna_idx,
                birth_charts, ceremony_type,
                masam_name=masam_name, is_adhika_masam=is_adhika,
                day_rashi_idx=day_rashi_idx,
            ):
                continue

            dt_set    = jd_to_local_datetime(set_jd, tz_name)
            rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
            set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60

            kalams = compute_kalams(rise_mins, set_mins, sun_idx)

            results.append({
                "date_te":      f"{day} {_MONTH_TE[month - 1]} {year}",
                "vaaram_te":    pan["vaaram"]["te"],
                "sunrise":      dt_rise.strftime("%H:%M"),
                "sunset":       dt_set.strftime("%H:%M"),
                "tithi_te":     pan["tithi"]["te"],
                "nakshatra_te": pan["nakshatra"]["te"],
                "yoga_te":      pan["yoga"]["te"],
                "rahu_kalam":   kalams["rahu_kalam"],
                "yamaganda":    kalams["yamaganda"],
                "gulika_kalam": kalams["gulika_kalam"],
                "dur_muhurtam": pan["dur_muhurtam"],
                "varjyam":      pan["varjyam"],
            })
        except Exception:
            continue   # skip days where calculation fails (polar extremes, etc.)

    return results
