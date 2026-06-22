from __future__ import annotations

import calendar
from typing import Callable

from .astro import (
    compute_planet_rashis,
    find_next_index_change,
    get_sunrise_sunset,
    jd_to_local_datetime,
    local_date_to_jd,
    moon_longitude,
    moon_sun_elongation,
    sun_longitude,
)
from .birth_chart import compute_lagna
from .muhurta_rules import compute_kalams
from .panchang import compute_panchang

_NAKSHATRA_SPAN = 360.0 / 27
_TRANSITION_EPSILON = 1.0 / (24 * 60 * 60)


def _all_transitions(
    start_jd: float,
    fn: Callable[[float], int],
    start_idx: int,
    step_hours: float,
    max_hours: float,
    end_jd: float,
) -> list[dict]:
    transitions = [{"jd": start_jd, "idx": start_idx}]
    current_jd = start_jd
    current_idx = start_idx

    while True:
        next_jd = find_next_index_change(
            current_jd,
            fn,
            current_idx,
            step_hours=step_hours,
            max_hours=max_hours,
        )
        if next_jd is None or next_jd >= end_jd:
            break

        probe_jd = min(next_jd + _TRANSITION_EPSILON, end_jd)
        next_idx = fn(probe_jd)
        transitions.append({"jd": next_jd, "idx": next_idx})
        current_jd = next_jd
        current_idx = next_idx

    return transitions


def compute_day_cache_data(
    year: int,
    month: int,
    day: int,
    lat: float,
    lon: float,
    tz_name: str,
) -> dict:
    noon_jd = local_date_to_jd(year, month, day, tz_name)
    rise_jd, set_jd = get_sunrise_sunset(noon_jd, lat, lon)
    end_jd = rise_jd + 1.0

    pan = compute_panchang(rise_jd, lat, lon, tz_name)
    dt_rise = jd_to_local_datetime(rise_jd, tz_name)
    dt_set = jd_to_local_datetime(set_jd, tz_name)

    moon_lon = moon_longitude(rise_jd)
    sun_lon = sun_longitude(rise_jd)
    elong = moon_sun_elongation(rise_jd)

    nak_idx = int(moon_lon / _NAKSHATRA_SPAN) % 27
    tithi_idx = int(elong / 12) % 30
    yoga_idx = int((moon_lon + sun_lon) / _NAKSHATRA_SPAN) % 27
    day_rashi_idx = int(moon_lon / 30) % 12
    sun_idx = (dt_rise.weekday() + 1) % 7
    initial_lagna = compute_lagna(rise_jd, lat, lon)

    def _lagna_idx(jd: float) -> int:
        return compute_lagna(jd, lat, lon)

    def _nakshatra_idx(jd: float) -> int:
        return int(moon_longitude(jd) / _NAKSHATRA_SPAN) % 27

    def _tithi_idx(jd: float) -> int:
        return int(moon_sun_elongation(jd) / 12) % 30

    lagna_transitions = _all_transitions(
        rise_jd,
        _lagna_idx,
        initial_lagna,
        step_hours=0.25,
        max_hours=3.0,
        end_jd=end_jd,
    )
    nak_transitions = _all_transitions(
        rise_jd,
        _nakshatra_idx,
        nak_idx,
        step_hours=1.0,
        max_hours=26.0,
        end_jd=end_jd,
    )
    tithi_transitions = _all_transitions(
        rise_jd,
        _tithi_idx,
        tithi_idx,
        step_hours=1.0,
        max_hours=26.0,
        end_jd=end_jd,
    )

    rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
    set_mins = dt_set.hour * 60 + dt_set.minute + dt_set.second / 60
    kalams = compute_kalams(rise_mins, set_mins, sun_idx)

    return {
        "nak_idx": nak_idx,
        "tithi_idx": tithi_idx,
        "yoga_idx": yoga_idx,
        "masam": pan["masam"]["en"],
        "is_adhika": pan["masam"]["adhika"],
        "sun_idx": sun_idx,
        "day_rashi_idx": day_rashi_idx,
        "sunrise": dt_rise.strftime("%H:%M"),
        "sunset": dt_set.strftime("%H:%M"),
        "sunrise_jd": rise_jd,
        "sunset_jd": set_jd,
        "lagna_transitions": lagna_transitions,
        "nak_transitions": nak_transitions,
        "tithi_transitions": tithi_transitions,
        "planet_rashis": compute_planet_rashis(rise_jd),
        "dur_muhurtam": pan["dur_muhurtam"],
        "varjyam": pan["varjyam"],
        "rahu_kalam": kalams["rahu_kalam"],
        "yamaganda": kalams["yamaganda"],
        "gulika_kalam": kalams["gulika_kalam"],
    }


def precompute_month(
    year: int,
    month: int,
    lat: float,
    lon: float,
    tz_name: str,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    _, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        try:
            results[f"{year}-{month:02d}-{day:02d}"] = compute_day_cache_data(
                year,
                month,
                day,
                lat,
                lon,
                tz_name,
            )
        except Exception:
            continue

    return results
