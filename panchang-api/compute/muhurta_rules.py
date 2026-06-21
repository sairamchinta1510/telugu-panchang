"""
Muhurta auspiciousness rules — South Indian Telugu tradition.
Pure logic — no astronomical calculations. All inputs are pre-computed integer indices.
Sources: Venkatrama & Co. Telugu Panchangam (Rajahmundry), Muhurta Chintamani, Dharmasindhu.
"""
from __future__ import annotations

CEREMONY_VIVAHA         = "vivaha"
CEREMONY_GRUHA_PRAVESAM = "gruha_pravesam"
CEREMONY_UPANAYANAM     = "upanayanam"
CEREMONY_POOJA          = "pooja"

# ── Auspicious nakshatras per ceremony (0-indexed: 0=Ashvini … 26=Revati) ────
# VIVAHA: 11 standard nakshatras per Muhurta Chintamani Ch.6 + South Indian tradition.
#   Pushya(7) is PROHIBITED despite being excellent for other ceremonies.
#   "Three Uttaras" = Uttara Phalguni(11), Uttara Ashadha(20), Uttara Bhadrapada(25).
# GRUHA PRAVESAM: Ashlesha(8), Jyeshtha(17), Moola(18) = "mula sankraman" gandanta
#   nakshatras — explicitly vetoed (uprooting symbolism, destructive for new home entry).
# UPANAYANAM: Pushya(7) is excellent (Guru-Pushya Yoga prized); included here.
_GOOD_NAKSHATRAS: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         {3, 4, 9, 11, 12, 14, 16, 18, 20, 25, 26},
    #                         Rohini, Mrigashira, Magha, UttaraPhalguni, Hasta,
    #                         Swati, Anuradha, Moola*, UttaraAshadha, UttaraBhadra, Revati
    #                         (* Moola 1st pada forbidden — enforced via pada rules in future)
    CEREMONY_GRUHA_PRAVESAM: {3, 4, 7, 11, 12, 13, 14, 16, 20, 21, 23, 25, 26},
    #                         Rohini, Mrigashira, Pushyami✓, UttaraPhalguni, Hasta, Chitra,
    #                         Swati, Anuradha, UttaraAshadha, Shravana, Shatabhisha,
    #                         UttaraBhadra, Revati  (Ashlesha/Jyeshtha/Moola excluded)
    CEREMONY_UPANAYANAM:     {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
    #                         Ashwini, Rohini, Mrigashira, Punarvasu, Pushyami✓,
    #                         UttaraPhalguni, Hasta, Chitra, Swati, Anuradha,
    #                         UttaraAshadha, Shravana, Dhanishtha, Shatabhisha,
    #                         UttaraBhadra, Revati
    CEREMONY_POOJA:          {0, 3, 4, 6, 7, 9, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
}

# ── Bad tithis per ceremony (0-indexed: 0=Shukla Prathama … 14=Purnima … 29=Amavasya) ─
# Rikta tithis (universally inauspicious): Chaturthi(3/18), Navami(8/23), Chaturdashi(13/28)
# in BOTH pakshas.  Additional exclusions vary by ceremony.
_RIKTA: set[int] = {3, 8, 13, 18, 23, 28}

_BAD_TITHIS: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         _RIKTA | {7, 14, 29},
    #                         + Ashtami Shukla(7), Purnima(14), Amavasya(29)
    CEREMONY_GRUHA_PRAVESAM: _RIKTA | {14, 29},
    #                         + Purnima(14), Amavasya(29)
    CEREMONY_UPANAYANAM:     _RIKTA | {14, 29},
    CEREMONY_POOJA:          {29},   # Only Amavasya rejected for general poojas
}

# ── Masa Shuddhi — forbidden lunar months ────────────────────────────────────
# Chaturmas core prohibition (Dharmasindhu): Ashadha, Shravana, Bhadrapada.
# Any Adhika (intercalary) masa is forbidden for all samskaras.
_CHATURMAS_MASAM: dict[str, set[str]] = {
    CEREMONY_VIVAHA:         {"Ashadha", "Shravana", "Bhadrapada"},
    CEREMONY_GRUHA_PRAVESAM: {"Ashadha", "Shravana", "Bhadrapada"},
    CEREMONY_UPANAYANAM:     {"Shravana", "Bhadrapada"},
    CEREMONY_POOJA:          set(),   # Poojas are allowed in all months
}

# ── Rahu Kalam / Yamaganda / Gulika segments ─────────────────────────────────
# Day (sunrise→sunset) divided into 8 equal parts; one part per weekday is inauspicious.
# sun_idx: 0=Sunday … 6=Saturday  (matches existing panchang.py convention)
# Source: Venkatrama & Co. + bidyashish/vedicpanchanga.com verified tables.
_RAHU_KALAM_SEGMENT:  dict[int, int] = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
_YAMAGANDA_SEGMENT:   dict[int, int] = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
_GULIKA_SEGMENT:      dict[int, int] = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}


def _kalam_window(rise_mins: float, set_mins: float, segment: int) -> dict:
    """Return {start, end} for the given 1-indexed day segment (1–8)."""
    part = (set_mins - rise_mins) / 8.0
    start = rise_mins + (segment - 1) * part
    end   = start + part
    def fmt(m: float) -> str:
        m = m % (24 * 60)
        return f"{int(m // 60):02d}:{int(m % 60):02d}"
    return {"start": fmt(start), "end": fmt(end)}


def compute_kalams(rise_mins: float, set_mins: float, sun_idx: int) -> dict:
    """Return Rahu Kalam, Yamaganda, and Gulika Kalam windows for a given day.

    All three are essential South Indian muhurta exclusion periods.
    South Indian rule: any ceremony during Gulika Kalam will repeat
    (marriage → second marriage), making it as critical as Rahu Kalam.
    """
    return {
        "rahu_kalam":   _kalam_window(rise_mins, set_mins, _RAHU_KALAM_SEGMENT[sun_idx]),
        "yamaganda":    _kalam_window(rise_mins, set_mins, _YAMAGANDA_SEGMENT[sun_idx]),
        "gulika_kalam": _kalam_window(rise_mins, set_mins, _GULIKA_SEGMENT[sun_idx]),
    }


def _masam_ok(masam_name: str, is_adhika: bool, ceremony_type: str) -> bool:
    """Return False if the lunar month is forbidden for this ceremony type."""
    if is_adhika:
        return False  # Adhika (intercalary) masa forbidden for all samskaras per Dharmasindhu
    return masam_name not in _CHATURMAS_MASAM.get(ceremony_type, set())


def _tara_ok(janma_nak: int, day_nak: int) -> bool:
    """Return True if the day nakshatra is auspicious for this person's janma nakshatra.

    Computes 1-indexed Tara position (Tara Balam) and rejects:
    1=Janma, 3=Vipat, 5=Pratyak, 7=Naidhana.
    """
    tara = ((day_nak - janma_nak) % 27) + 1
    return tara not in {1, 3, 5, 7}


def _panchaka_ok(naks_idx: int, sun_idx: int, tithi_idx: int, lagna_idx: int) -> bool:
    """Return True if there is no Panchaka Dosha (South Indian formula).

    Formula (all 1-indexed, using FULL tithi 1–30):
        (vaara + tithi + nakshatra + lagna) % 9
    Safe remainders: {0, 3, 5, 7} = Panchaka Rahita.
    Dosha remainders: {1=Mrityu, 2=Agni, 4=Raja, 6=Chora, 8=Roga}.
    Source: Astro-Engine/Astro_Engine_ORGNL docs/02_SOUTH_INDIAN_TRADITIONS.md.
    """
    vaara_1 = sun_idx + 1     # Sunday=1 … Saturday=7
    tithi_1 = tithi_idx + 1   # 1–30 (Shukla Prathama=1 … Amavasya=30)
    nak_1   = naks_idx + 1    # 1–27
    lagna_1 = lagna_idx + 1   # 1–12
    result  = (vaara_1 + tithi_1 + nak_1 + lagna_1) % 9
    return result in {0, 3, 5, 7}


def is_auspicious(
    naks_idx: int,
    tithi_idx: int,
    sun_idx: int,
    lagna_idx: int,
    birth_charts: list[dict],
    ceremony_type: str,
    masam_name: str = "",
    is_adhika_masam: bool = False,
) -> bool:
    """Return True if the given panchang state is auspicious for the ceremony.

    Checks in order (fastest eliminations first):
    1. Masa Shuddhi (Chaturmas / Adhika Masa prohibition)
    2. Good nakshatra for ceremony type
    3. Bad tithi exclusion (Rikta tithis + ceremony-specific)
    4. Tara Balam for every person
    5. Panchaka Dosha
    """
    if masam_name and not _masam_ok(masam_name, is_adhika_masam, ceremony_type):
        return False
    if naks_idx not in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
        return False
    if tithi_idx in _BAD_TITHIS.get(ceremony_type, set()):
        return False
    for chart in birth_charts:
        if not _tara_ok(chart["janma_nakshatra_idx"], naks_idx):
            return False
    if not _panchaka_ok(naks_idx, sun_idx, tithi_idx, lagna_idx):
        return False
    return True
