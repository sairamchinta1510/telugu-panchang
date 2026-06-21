"""
Birth chart computation for Muhurta calculations.
Computes janma nakshatra, janma rashi, and lagna from birth date/time/place.
"""
from __future__ import annotations
import swisseph as swe
import pytz
from datetime import datetime

from .astro import moon_longitude
from .panchang import NAKSHATRA_TE

RASHI_TE = [
    "మేషం", "వృషభం", "మిథునం", "కర్కాటకం",
    "సింహం", "కన్య", "తులం", "వృశ్చికం",
    "ధనుస్సు", "మకరం", "కుంభం", "మీనం",
]

RASHI_EN = [
    "Mesha", "Vrishabha", "Mithuna", "Karkataka",
    "Simha", "Kanya", "Tula", "Vrischika",
    "Dhanus", "Makara", "Kumbha", "Meena",
]


def _birth_jd(year: int, month: int, day: int, hour: int, minute: int,
               tz_name: str) -> float:
    """Convert local birth datetime to Julian Day (UTC)."""
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(year, month, day, hour, minute))
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )


def compute_lagna(jd: float, lat: float, lon: float) -> int:
    """Return sidereal lagna (ascendant) index 0–11 for the given JD and location."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsha = swe.get_ayanamsa_ut(jd)
    _cusps, ascmc = swe.houses(jd, lat, lon, b"P")
    tropical_asc = ascmc[0]
    sidereal_asc = (tropical_asc - ayanamsha) % 360
    return int(sidereal_asc / 30) % 12


def compute_birth_chart(
    year: int, month: int, day: int,
    hour: int, minute: int,
    lat: float, lon: float, tz_name: str,
) -> dict:
    """Compute birth chart indices and Telugu names from birth data.

    Returns dict with janma_nakshatra_idx, janma_nakshatra_te,
    janma_rashi_idx, janma_rashi_te, lagna_idx, lagna_te.
    """
    jd = _birth_jd(year, month, day, hour, minute, tz_name)
    moon_lon = moon_longitude(jd)

    nak_idx   = int(moon_lon / (360.0 / 27)) % 27
    rashi_idx = int(moon_lon / 30) % 12
    lagna_idx = compute_lagna(jd, lat, lon)

    return {
        "janma_nakshatra_idx": nak_idx,
        "janma_nakshatra_te":  NAKSHATRA_TE[nak_idx],
        "janma_rashi_idx":     rashi_idx,
        "janma_rashi_te":      RASHI_TE[rashi_idx],
        "lagna_idx":           lagna_idx,
        "lagna_te":            RASHI_TE[lagna_idx],
    }
