"""
Vimshottari dasha computation for Telugu Jyotish.

Computes the full 120-year dasha sequence from the moon's sidereal longitude
and birth datetime, following the standard South Indian Vimshottari system.
"""
from __future__ import annotations

from datetime import datetime, timedelta

DASHA_SEQUENCE = [
    "ketu",
    "shukra",
    "ravi",
    "chandra",
    "kuja",
    "rahu",
    "guru",
    "shani",
    "budha",
]

DASHA_YEARS: dict[str, int] = {
    "ketu": 7,
    "shukra": 20,
    "ravi": 6,
    "chandra": 10,
    "kuja": 7,
    "rahu": 18,
    "guru": 16,
    "shani": 19,
    "budha": 17,
}

DASHA_LORD_TE: dict[str, str] = {
    "ketu": "కేతు",
    "shukra": "శుక్ర",
    "ravi": "రవి",
    "chandra": "చంద్ర",
    "kuja": "కుజ",
    "rahu": "రాహు",
    "guru": "గురు",
    "shani": "శని",
    "budha": "బుధ",
}

DASHA_EMOJI: dict[str, str] = {
    "ketu": "☋",
    "shukra": "♀",
    "ravi": "☀️",
    "chandra": "🌙",
    "kuja": "♂",
    "rahu": "☊",
    "guru": "♃",
    "shani": "♄",
    "budha": "☿",
}

_DAYS_PER_YEAR = 365.25
_NAK_SPAN = 360.0 / 27


def compute_vimshottari_dasha(moon_lon: float, birth_dt: datetime) -> list[dict]:
    """Compute full 120-year Vimshottari dasha sequence from birth."""
    nak_idx = int(moon_lon / _NAK_SPAN) % 27
    lord_seq_start = nak_idx % 9

    nak_start_lon = nak_idx * _NAK_SPAN
    traversed_fraction = (moon_lon - nak_start_lon) / _NAK_SPAN
    first_lord = DASHA_SEQUENCE[lord_seq_start]
    balance_years = (1.0 - traversed_fraction) * DASHA_YEARS[first_lord]

    dashas: list[dict] = []
    current_dt = birth_dt

    for i in range(9):
        lord = DASHA_SEQUENCE[(lord_seq_start + i) % 9]
        full_years = float(DASHA_YEARS[lord])
        if i == 0:
            elapsed_years = full_years - balance_years
            maha_true_start = birth_dt - timedelta(days=elapsed_years * _DAYS_PER_YEAR)
            years = balance_years
        else:
            maha_true_start = current_dt
            years = full_years
        end_dt = current_dt + timedelta(days=years * _DAYS_PER_YEAR)

        dashas.append(
            {
                "lord": lord,
                "lord_te": DASHA_LORD_TE[lord],
                "lord_emoji": DASHA_EMOJI[lord],
                "years": round(years, 4),
                "start_date": current_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "antardashas": _compute_antardashas(
                    lord, full_years, maha_true_start
                ),
            }
        )
        current_dt = end_dt

    return dashas


def _compute_antardashas(
    maha_lord: str, maha_years: float, maha_start: datetime
) -> list[dict]:
    """Compute 9 antardasha sub-periods for a given mahadasha."""
    lord_seq_idx = DASHA_SEQUENCE.index(maha_lord)
    antardashas: list[dict] = []
    ad_start = maha_start

    for j in range(9):
        sub_lord = DASHA_SEQUENCE[(lord_seq_idx + j) % 9]
        sub_years = (maha_years * DASHA_YEARS[sub_lord]) / 120.0
        ad_end = ad_start + timedelta(days=sub_years * _DAYS_PER_YEAR)
        antardashas.append(
            {
                "lord": sub_lord,
                "lord_te": DASHA_LORD_TE[sub_lord],
                "start": ad_start.strftime("%Y-%m-%d"),
                "end": ad_end.strftime("%Y-%m-%d"),
            }
        )
        ad_start = ad_end

    return antardashas
