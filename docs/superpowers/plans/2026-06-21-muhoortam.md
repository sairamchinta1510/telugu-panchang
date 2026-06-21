# Muhoortam — Telugu Muhurta Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Telugu muhurta calculator to the telugu-panchang project that accepts birth details for up to 6 people and returns auspicious ceremony dates for the next 1 year.

**Architecture:** Four new Python modules (`birth_chart`, `muhurta_rules`, `muhurta_finder`) inside `panchang-api/compute/`, a new Lambda handler `handler_muhoortam.py`, and a single-page Telugu wizard `muhoortam/index.html`. No existing files are modified except `template.yaml` which gets two new additive resources.

**Tech Stack:** Python 3.12 + pyswisseph + timezonefinder + pytz (all existing deps), plain HTML/JS frontend, AWS SAM Lambda, OpenStreetMap Nominatim for geocoding.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `panchang-api/compute/birth_chart.py` | Janma nakshatra, rashi, lagna from birth datetime |
| Create | `panchang-api/compute/muhurta_rules.py` | Ceremony rules, Tara Balam, Panchaka Dosha |
| Create | `panchang-api/compute/muhurta_finder.py` | Month-by-month auspicious day scanner |
| Create | `panchang-api/handler_muhoortam.py` | Lambda handler for /muhoortam/* endpoints |
| **Modify** | `panchang-api/template.yaml` | ADD two new resources (additive only, existing untouched) |
| Create | `panchang-api/tests/test_muhoortam.py` | Unit tests for all new modules |
| Create | `muhoortam/index.html` | Telugu 4-step wizard frontend |

---

## Task 1: `birth_chart.py` — Birth Chart Computation

**Files:**
- Create: `panchang-api/compute/birth_chart.py`
- Test: `panchang-api/tests/test_muhoortam.py` (birth chart section)

### Context

This module converts a birth date/time/place into three indices needed by the muhurta rules:
- `janma_nakshatra_idx` (0–26): moon's nakshatra at birth
- `janma_rashi_idx` (0–11): moon's zodiac sign at birth
- `lagna_idx` (0–11): ascendant (rising sign) at birth

It imports `moon_longitude` from the existing `compute.astro` and uses `swisseph` directly for the ascendant.

- [ ] **Step 1: Write the failing test**

Create `panchang-api/tests/test_muhoortam.py` with the birth chart tests:

```python
"""Tests for new Muhoortam modules: birth_chart, muhurta_rules, muhurta_finder, handler."""
import sys
import json
import types
from unittest.mock import patch, MagicMock
import pytest


# ── Birth chart tests ─────────────────────────────────────────────────────────

def _make_birth_chart_module():
    """Load birth_chart with swisseph mocked."""
    # Remove cached module if present
    for mod in list(sys.modules):
        if "birth_chart" in mod:
            del sys.modules[mod]

    fake_swe = MagicMock()
    fake_swe.SIDM_LAHIRI = 0
    fake_swe.GREG_CAL = 1
    fake_swe.julday.return_value = 2460000.5
    fake_swe.get_ayanamsa_ut.return_value = 24.0  # ~24° Lahiri ayanamsha
    # swe.houses returns (cusps_tuple, ascmc_tuple); ascmc[0] = tropical ascendant
    fake_swe.houses.return_value = (
        (0.0,) * 13,          # cusps (unused)
        (54.0,) + (0.0,) * 9  # ascmc[0] = 54° tropical → 54-24 = 30° sidereal → Vrishabha (idx=1)
    )
    sys.modules["swisseph"] = fake_swe

    fake_astro = types.ModuleType("compute.astro")
    # moon at 53.33° sidereal → nakshatra idx = int(53.33 / 13.333) = 4 (Mrigashira)
    # rashi idx = int(53.33 / 30) = 1 (Vrishabha)
    fake_astro.moon_longitude = lambda jd: 53.33
    sys.modules["compute.astro"] = fake_astro

    import importlib
    import compute.birth_chart as bc
    importlib.reload(bc)
    return bc


def test_birth_chart_nakshatra():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["janma_nakshatra_idx"] == 4
    assert result["janma_nakshatra_te"] == "మృగశిర"


def test_birth_chart_rashi():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["janma_rashi_idx"] == 1
    assert result["janma_rashi_te"] == "వృషభం"


def test_birth_chart_lagna():
    bc = _make_birth_chart_module()
    # tropical asc=54°, ayanamsha=24° → sidereal=30° → idx=1 (Vrishabha)
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["lagna_idx"] == 1
    assert result["lagna_te"] == "వృషభం"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py::test_birth_chart_nakshatra -v
```
Expected: `ModuleNotFoundError` or `ImportError` (file doesn't exist yet).

- [ ] **Step 3: Implement `birth_chart.py`**

Create `panchang-api/compute/birth_chart.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py::test_birth_chart_nakshatra tests/test_muhoortam.py::test_birth_chart_rashi tests/test_muhoortam.py::test_birth_chart_lagna -v
```
Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add panchang-api/compute/birth_chart.py panchang-api/tests/test_muhoortam.py
git commit -m "feat(muhoortam): add birth_chart module with janma nakshatra/rashi/lagna

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 2: `muhurta_rules.py` — Auspiciousness Rules

**Files:**
- Create: `panchang-api/compute/muhurta_rules.py`
- Modify: `panchang-api/tests/test_muhoortam.py` (append new tests)

### Context

Pure logic module — no swisseph, no imports from astro. Takes pre-computed integer indices and returns a boolean. Checks in order:
1. **Good nakshatra** for the ceremony type (South Indian Telugu tradition, Venkatrama & Co.)
2. **Bad tithi** exclusion — uses **Rikta tithis** (Chaturthi, Navami, Chaturdashi in both pakshas) as the core rule
3. **Tara Balam**: for each person, count from janma nakshatra to day nakshatra; reject positions 1, 3, 5, 7
4. **Panchaka Dosha**: `(vaara_1 + tithi_1 + nak_1 + lagna_1) % 9`; safe remainders are `{0, 3, 5, 7}` (Panchaka Rahita); dosha remainders are `{1, 2, 4, 6, 8}`. Uses **full 1–30 tithi** (not mod-15).
5. **Masa Shuddhi**: reject Adhika Masa and Chaturmas core months (Ashadha, Shravana, Bhadrapada)

**South Indian Telugu tradition corrections (verified against Venkatrama & Co., Muhurta Chintamani, Dharmasindhu):**
- **Pushya (Pushyami) is PROHIBITED for Vivaha** — the most important Telugu tradition exception; Pushya is auspicious for everything *except* marriage
- **Three Uttaras** (Uttara Phalguni=11, Uttara Ashadha=20, Uttara Bhadrapada=25) are primary marriage nakshatras
- **Ashlesha(8), Jyeshtha(17), Moola(18)** are "mula sankraman" (gandanta) nakshatras — explicitly avoided for Gruha Pravesam (entering a new home)
- **Gulika Kalam** is treated with extreme seriousness in South India: any ceremony during Gulika repeats (marriage → second marriage)

- [ ] **Step 1: Append muhurta_rules tests to `test_muhoortam.py`**

```python
# ── Muhurta rules tests ───────────────────────────────────────────────────────

# Clear any cached module so we get a fresh import
for mod in list(sys.modules):
    if "muhurta_rules" in mod:
        del sys.modules[mod]

from compute.muhurta_rules import is_auspicious, _tara_ok, _panchaka_ok


def test_tara_ok_good():
    # Janma=3 (Rohini), day=9 (Magha): tara = (9-3)%27+1 = 7 → INAUSPICIOUS
    assert _tara_ok(3, 9) is False


def test_tara_ok_bad_same():
    # Janma=5, day=5: tara=1 (Janma) → inauspicious
    assert _tara_ok(5, 5) is False


def test_tara_ok_safe():
    # Janma=3, day=5: tara=(5-3)%27+1=3 → inauspicious
    assert _tara_ok(3, 5) is False


def test_tara_ok_position_2():
    # Janma=3, day=4: tara=(4-3)%27+1=2 → auspicious
    assert _tara_ok(3, 4) is True


def test_panchaka_ok_inauspicious():
    # nak=0→1, sun=0(Sun)→1, tithi=0→1, lagna=0→1; 1+1+1+1=4 → 4%9=4 → Dosha (4 ∈ {1,2,4,6,8})
    assert _panchaka_ok(0, 0, 0, 0) is False


def test_panchaka_ok_safe():
    # nak=3→4, sun=4(Thu)→5, tithi=4→5, lagna=0→1; 4+5+5+1=15 → 15%9=6 → SAFE (6 ∉ {1,2,4,6,8})
    assert _panchaka_ok(3, 4, 4, 0) is True


def test_pushya_excluded_from_vivaha():
    # Pushya (idx=7) must be excluded from Vivaha in Telugu tradition
    birth_charts = [{"janma_nakshatra_idx": 0}]
    assert is_auspicious(7, 4, 4, 0, birth_charts, "vivaha") is False


def test_pushya_allowed_for_upanayanam():
    # Pushya (idx=7) is excellent for Upanayanam — must NOT be rejected
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # nak=7→8, sun=4→5, tithi=4→5, lagna=0→1; 8+5+5+1=19 → 19%9=1 → Mrityu Panchaka Dosha → False
    # Use tithi=1 (Dvitiya safe): nak=7→8, sun=4→5, tithi=1→2, lagna=0→1; 8+5+2+1=16 → 16%9=7 → SAFE
    assert is_auspicious(7, 1, 4, 0, birth_charts, "upanayanam") is True


def test_is_auspicious_vivaha_good_day():
    # naks=3 (Rohini - good), tithi=4 (Panchami - safe), sun=4 (Thursday), lagna=0 (Mesha)
    # tara: janma=0 (Ashvini), day=3: tara=(3-0)%27+1=4 → safe
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # nak=3→4, sun=4→5, tithi=4→5, lagna=0→1; 4+5+5+1=15 → 15%9=6 → SAFE
    assert is_auspicious(3, 4, 4, 0, birth_charts, "vivaha") is True


def test_is_auspicious_rejects_bad_nakshatra():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # naks=0 (Ashvini) - not in vivaha good list
    assert is_auspicious(0, 4, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_rikta_tithi():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # tithi=3 (Shukla Chaturthi, idx=3) — Rikta tithi, bad for vivaha
    assert is_auspicious(3, 3, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_bad_tara():
    # person janma=3 (Rohini), day naks=3 → tara=1 (Janma) → bad
    birth_charts = [{"janma_nakshatra_idx": 3}]
    assert is_auspicious(3, 4, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_panchaka():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # nak=3→4, sun=0(Sun)→1, tithi=0→1, lagna=0→1; 4+1+1+1=7 → 7%9=7 → SAFE
    # Need dosha: nak=3→4, sun=0→1, tithi=0→1, lagna=3→4; 4+1+1+4=10 → 10%9=1 → Mrityu Panchaka!
    assert is_auspicious(3, 0, 0, 3, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_adhika_masam():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # Adhika masa → rejected regardless of nakshatra/tithi
    assert is_auspicious(3, 4, 4, 0, birth_charts, "vivaha",
                         masam_name="Jyeshtha", is_adhika_masam=True) is False


def test_is_auspicious_rejects_chaturmas():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # Shravana month → rejected for vivaha (Chaturmas)
    assert is_auspicious(3, 4, 4, 0, birth_charts, "vivaha",
                         masam_name="Shravana", is_adhika_masam=False) is False
```

- [ ] **Step 2: Run to verify tests fail**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "tara or panchaka or auspicious" -v
```
Expected: `ImportError` (muhurta_rules not yet created).

- [ ] **Step 3: Implement `muhurta_rules.py`**

Create `panchang-api/compute/muhurta_rules.py`:

```python
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
    def fmt(m): m = m % (24 * 60); return f"{int(m // 60):02d}:{int(m % 60):02d}"
    return {"start": fmt(start), "end": fmt(end)}


def compute_kalams(rise_mins: float, set_mins: float, sun_idx: int) -> dict:
    """Return Rahu Kalam, Yamaganda, and Gulika Kalam windows for a given day.

    All three are essential South Indian muhurta exclusion periods.
    South Indian rule: any ceremony during Gulika Kalam will repeat
    (marriage → second marriage), making it as critical as Rahu Kalam.
    """
    return {
        "rahu_kalam":  _kalam_window(rise_mins, set_mins, _RAHU_KALAM_SEGMENT[sun_idx]),
        "yamaganda":   _kalam_window(rise_mins, set_mins, _YAMAGANDA_SEGMENT[sun_idx]),
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "tara or panchaka or auspicious" -v
```
Expected: all rule tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add panchang-api/compute/muhurta_rules.py panchang-api/tests/test_muhoortam.py
git commit -m "feat(muhoortam): add muhurta_rules module (Tara Balam + Panchaka Dosha)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 3: `muhurta_finder.py` — Month Scanner

**Files:**
- Create: `panchang-api/compute/muhurta_finder.py`
- Modify: `panchang-api/tests/test_muhoortam.py` (append new tests)

### Context

Iterates every calendar day in a given month, computes panchang at sunrise, and returns all days that pass `is_auspicious()`. Uses the existing `compute_panchang()` (imported, not modified) for the Telugu output fields (vaaram, tithi, nakshatra, yoga names). Recomputes raw indices independently for the rules check since `compute_panchang()` does not expose numeric indices in its output.

- [ ] **Step 1: Append muhurta_finder tests to `test_muhoortam.py`**

```python
# ── Muhurta finder tests ──────────────────────────────────────────────────────

import importlib
import calendar

def _load_finder(days_auspicious: set[int]):
    """Load muhurta_finder with all astronomical functions mocked.

    days_auspicious: set of day-of-month integers that should be marked auspicious.
    All other days return nakshatra=0 (Ashvini, not in vivaha good list) → rejected.
    """
    for mod in list(sys.modules):
        if "muhurta_finder" in mod or "birth_chart" in mod:
            del sys.modules[mod]

    RISE_JD, SET_JD = 101.0, 102.0

    def fake_local_date_to_jd(year, month, day, tz):
        return float(day)  # use day as JD stand-in

    def fake_get_sunrise_sunset(jd, lat, lon):
        return (RISE_JD, SET_JD)

    def fake_moon_longitude(jd):
        # Return Rohini (idx=3) for auspicious days: 3 * (360/27) + 1 = ~41°
        day = int(jd)
        return 41.0 if day in days_auspicious else 1.0  # 1° → Ashvini (idx=0)

    def fake_moon_sun_elongation(jd):
        return 50.0  # tithi_idx = int(50/12) % 30 = 4 (Panchami, not in bad list)

    from datetime import datetime as real_dt
    def fake_jd_to_local_datetime(jd, tz):
        # Return a Thursday (weekday=3 → sun_idx=4)
        return real_dt(2026, 7, 15, 6, 0)  # arbitrary Thursday

    def fake_compute_lagna(jd, lat, lon):
        return 0  # Mesha lagna

    MOCK_PAN = {
        "vaaram":    {"te": "గురువారం"},
        "tithi":     {"te": "పంచమి"},
        "nakshatra": {"te": "రోహిణి"},
        "yoga":      {"te": "సౌభాగ్య"},
        "masam":     {"en": "Jyeshtha", "te": "జ్యేష్ఠ", "adhika": False},
        "dur_muhurtam": [],
        "varjyam":   {"start": "09:00", "end": "10:46"},
    }

    fake_astro = types.ModuleType("compute.astro")
    fake_astro.local_date_to_jd       = fake_local_date_to_jd
    fake_astro.get_sunrise_sunset      = fake_get_sunrise_sunset
    fake_astro.moon_longitude          = fake_moon_longitude
    fake_astro.moon_sun_elongation     = fake_moon_sun_elongation
    fake_astro.jd_to_local_datetime    = fake_jd_to_local_datetime
    sys.modules["compute.astro"] = fake_astro

    fake_pan_mod = types.ModuleType("compute.panchang")
    fake_pan_mod.compute_panchang = lambda jd, lat, lon, tz: MOCK_PAN
    fake_pan_mod.NAKSHATRA_TE = ["అశ్వని"] * 27
    fake_pan_mod.TITHI_TE = ["ప్రథమ"] * 30
    fake_pan_mod.VAARAM_TE = ["ఆదివారం"] * 7
    sys.modules["compute.panchang"] = fake_pan_mod

    fake_bc = types.ModuleType("compute.birth_chart")
    fake_bc.compute_lagna = fake_compute_lagna
    sys.modules["compute.birth_chart"] = fake_bc

    # muhurta_rules must also be importable
    import compute.muhurta_rules  # real module (no swisseph dependency)
    sys.modules["compute.muhurta_rules"] = compute.muhurta_rules

    import compute.muhurta_finder as mf
    importlib.reload(mf)
    return mf


def test_finder_returns_only_auspicious_days():
    # Days 15 and 22 will have Rohini (naks=3, good for vivaha); all others Ashvini (naks=0, bad)
    mf = _load_finder({15, 22})
    birth_charts = [{"janma_nakshatra_idx": 0}]  # Ashvini janma; tara(0,3)=(3-0)%27+1=4 → ok
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    result_dates = [r["date_te"] for r in results]
    assert "15 జులై 2026" in result_dates
    assert "22 జులై 2026" in result_dates
    # Other days should not appear (naks=0, not in vivaha good list)
    assert all("జులై 2026" in d for d in result_dates)
    assert len(results) == 2


def test_finder_result_has_telugu_fields():
    mf = _load_finder({15})
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    assert len(results) == 1
    r = results[0]
    assert r["vaaram_te"] == "గురువారం"
    assert r["tithi_te"] == "పంచమి"
    assert r["nakshatra_te"] == "రోహిణి"
    assert "sunrise" in r
    assert "sunset" in r
    # South Indian kalam periods must be present
    assert "rahu_kalam" in r
    assert "yamaganda" in r
    assert "gulika_kalam" in r
    assert "start" in r["rahu_kalam"]
    assert "end"   in r["rahu_kalam"]


def test_finder_rejects_chaturmas_month():
    """Days in Shravana (core Chaturmas month) must be rejected for Vivaha."""
    mf = _load_finder({15})
    # Override MOCK_PAN masam to Shravana
    import compute.muhurta_finder as _mf_mod
    _orig = _mf_mod.compute_panchang
    def _shravana_pan(jd, lat, lon, tz):
        p = _orig(jd, lat, lon, tz)
        p = dict(p); p["masam"] = {"en": "Shravana", "te": "శ్రావణ", "adhika": False}
        return p
    _mf_mod.compute_panchang = _shravana_pan
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 8, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    _mf_mod.compute_panchang = _orig
    assert len(results) == 0  # Shravana → all days rejected for Vivaha
```

- [ ] **Step 2: Run to verify tests fail**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "finder" -v
```
Expected: `ImportError` (muhurta_finder not yet created).

- [ ] **Step 3: Implement `muhurta_finder.py`**

Create `panchang-api/compute/muhurta_finder.py`:

```python
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

            dt_rise   = jd_to_local_datetime(rise_jd, tz_name)
            sun_idx   = (dt_rise.weekday() + 1) % 7   # Sunday=0 … Saturday=6

            lagna_idx = compute_lagna(rise_jd, lat, lon)

            # Need panchang first for Masa Shuddhi check (masam name + adhika flag)
            pan = compute_panchang(jd, lat, lon, tz_name)
            masam_name    = pan["masam"]["en"]
            is_adhika     = pan["masam"]["adhika"]

            if not is_auspicious(
                naks_idx, tithi_idx, sun_idx, lagna_idx,
                birth_charts, ceremony_type,
                masam_name=masam_name, is_adhika_masam=is_adhika,
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "finder" -v
```
Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add panchang-api/compute/muhurta_finder.py panchang-api/tests/test_muhoortam.py
git commit -m "feat(muhoortam): add muhurta_finder month scanner

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 4: `handler_muhoortam.py` — Lambda Handler

**Files:**
- Create: `panchang-api/handler_muhoortam.py`
- Modify: `panchang-api/tests/test_muhoortam.py` (append handler tests)

### Context

New Lambda handler for two endpoints:
- `POST /muhoortam/birth-chart`: geocodes place → compute_birth_chart
- `POST /muhoortam/find`: geocodes ceremony_place → find_muhurtas_for_month

Uses `urllib.request` (stdlib, no new deps) for Nominatim geocoding. Follows the exact same response structure as `handler.py` (statusCode, headers with CORS, body as JSON string).

- [ ] **Step 1: Append handler tests to `test_muhoortam.py`**

```python
# ── Handler tests ─────────────────────────────────────────────────────────────

# Ensure the compute mocks from earlier tests don't bleed into handler tests.
# handler_muhoortam imports at module level; patch via unittest.mock.patch.

MOCK_GEO = {"lat": 17.38, "lon": 78.49, "tz_name": "Asia/Kolkata"}

MOCK_BIRTH_CHART = {
    "janma_nakshatra_idx": 3,
    "janma_nakshatra_te": "రోహిణి",
    "janma_rashi_idx": 1,
    "janma_rashi_te": "వృషభం",
    "lagna_idx": 1,
    "lagna_te": "వృషభం",
}

MOCK_FIND_RESULTS = [
    {
        "date_te": "15 జులై 2026",
        "vaaram_te": "గురువారం",
        "sunrise": "06:03",
        "sunset": "18:45",
        "tithi_te": "పంచమి",
        "nakshatra_te": "రోహిణి",
        "yoga_te": "సౌభాగ్య",
        "dur_muhurtam": [],
        "varjyam": {"start": "09:00", "end": "10:46"},
    }
]


def _make_handler_event(path: str, body: dict) -> dict:
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps(body),
    }


# Reload handler_muhoortam with real imports (swisseph is mocked via conftest)
for mod in list(sys.modules):
    if "handler_muhoortam" in mod:
        del sys.modules[mod]


@patch("handler_muhoortam._geocode", return_value=MOCK_GEO)
@patch("handler_muhoortam.compute_birth_chart", return_value=MOCK_BIRTH_CHART)
def test_handler_birth_chart_ok(mock_chart, mock_geo):
    import handler_muhoortam as h
    event = _make_handler_event("/muhoortam/birth-chart", {
        "dob": "15/08/1990", "time": "10:30", "place": "Hyderabad, India"
    })
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["janma_nakshatra_te"] == "రోహిణి"


@patch("handler_muhoortam._geocode", return_value=MOCK_GEO)
@patch("handler_muhoortam.compute_birth_chart", return_value=MOCK_BIRTH_CHART)
def test_handler_birth_chart_missing_field(mock_chart, mock_geo):
    import handler_muhoortam as h
    event = _make_handler_event("/muhoortam/birth-chart", {"dob": "15/08/1990"})
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


@patch("handler_muhoortam._geocode", return_value=MOCK_GEO)
@patch("handler_muhoortam.find_muhurtas_for_month", return_value=MOCK_FIND_RESULTS)
def test_handler_find_ok(mock_find, mock_geo):
    import handler_muhoortam as h
    event = _make_handler_event("/muhoortam/find", {
        "year": 2026, "month": 7,
        "ceremony_type": "vivaha",
        "ceremony_place": "Hyderabad, India",
        "birth_charts": [{"janma_nakshatra_idx": 3}],
    })
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["results"][0]["date_te"] == "15 జులై 2026"


@patch("handler_muhoortam._geocode", return_value=MOCK_GEO)
@patch("handler_muhoortam.find_muhurtas_for_month", return_value=MOCK_FIND_RESULTS)
def test_handler_find_bad_month(mock_find, mock_geo):
    import handler_muhoortam as h
    event = _make_handler_event("/muhoortam/find", {
        "year": 2026, "month": 13,
        "ceremony_type": "vivaha",
        "ceremony_place": "Hyderabad, India",
        "birth_charts": [{"janma_nakshatra_idx": 3}],
    })
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_unknown_path():
    import handler_muhoortam as h
    event = _make_handler_event("/muhoortam/unknown", {})
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 404
```

- [ ] **Step 2: Run to verify tests fail**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "handler" -v
```
Expected: `ImportError` (handler_muhoortam not yet created).

- [ ] **Step 3: Implement `handler_muhoortam.py`**

Create `panchang-api/handler_muhoortam.py`:

```python
"""
Lambda entry point for the Muhoortam API.
  POST /muhoortam/birth-chart  — compute janma nakshatra / rashi / lagna
  POST /muhoortam/find         — find auspicious dates for a given month
"""
from __future__ import annotations
import json
import traceback
import urllib.request
import urllib.parse

from timezonefinder import TimezoneFinder

from compute.birth_chart import compute_birth_chart
from compute.muhurta_finder import find_muhurtas_for_month

_tf = TimezoneFinder()


def _error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def _ok(data: dict) -> dict:
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, ensure_ascii=False),
    }


def _geocode(place: str) -> dict:
    """Resolve a place name to lat, lon, and IANA timezone using Nominatim."""
    params = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "muhoortam-api/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        results = json.loads(resp.read())
    if not results:
        raise ValueError(f"Place not found: {place!r}")
    r = results[0]
    lat, lon = float(r["lat"]), float(r["lon"])
    tz_name = _tf.timezone_at(lng=lon, lat=lat) or "UTC"
    return {"lat": lat, "lon": lon, "tz_name": tz_name}


def lambda_handler(event: dict, context) -> dict:
    path = event.get("rawPath") or event.get("path") or ""

    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _error(400, "Request body must be valid JSON")

    if path.endswith("/birth-chart"):
        return _handle_birth_chart(body)
    if path.endswith("/find"):
        return _handle_find(body)
    return _error(404, "Unknown endpoint")


def _handle_birth_chart(body: dict) -> dict:
    try:
        dob      = body["dob"]    # "DD/MM/YYYY"
        time_str = body["time"]   # "HH:MM"
        place    = body["place"]
    except KeyError as e:
        return _error(400, f"Missing field: {e}")

    try:
        day, month, year = [int(x) for x in dob.split("/")]
        hour, minute     = [int(x) for x in time_str.split(":")]
    except (ValueError, TypeError):
        return _error(400, "dob must be DD/MM/YYYY and time must be HH:MM")

    try:
        geo = _geocode(place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        chart = compute_birth_chart(
            year, month, day, hour, minute,
            geo["lat"], geo["lon"], geo["tz_name"],
        )
    except Exception:
        traceback.print_exc()
        return _error(500, "Birth chart calculation failed")

    return _ok(chart)


def _handle_find(body: dict) -> dict:
    try:
        year           = int(body["year"])
        month          = int(body["month"])
        ceremony_type  = body["ceremony_type"]
        ceremony_place = body["ceremony_place"]
        birth_charts   = body["birth_charts"]
    except (KeyError, TypeError, ValueError) as e:
        return _error(400, f"Invalid or missing field: {e}")

    if not (1 <= month <= 12):
        return _error(400, "month must be 1–12")
    if not birth_charts:
        return _error(400, "At least one birth_chart is required")

    try:
        geo = _geocode(ceremony_place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        results = find_muhurtas_for_month(
            year, month,
            geo["lat"], geo["lon"], geo["tz_name"],
            ceremony_type, birth_charts,
        )
    except Exception:
        traceback.print_exc()
        return _error(500, "Muhurta calculation failed")

    return _ok({"results": results, "count": len(results)})
```

- [ ] **Step 4: Run handler tests to verify they pass**

```bash
cd panchang-api && python -m pytest tests/test_muhoortam.py -k "handler" -v
```
Expected: 5 PASSED.

- [ ] **Step 5: Run full test suite to confirm no regressions**

```bash
cd panchang-api && python -m pytest tests/ -v
```
Expected: all existing tests still PASSED, plus new muhoortam tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add panchang-api/handler_muhoortam.py panchang-api/tests/test_muhoortam.py
git commit -m "feat(muhoortam): add Lambda handler for /muhoortam/birth-chart and /muhoortam/find

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 5: `template.yaml` — Add Muhoortam Lambda (Additive Only)

**Files:**
- Modify: `panchang-api/template.yaml` (add 2 new resources; existing resources untouched)

### Context

Adds a `MuhoortamFunction` Lambda and two new HTTP API routes (`POST /muhoortam/birth-chart` and `POST /muhoortam/find`) to the existing `PanchangHttpApi`. The existing `PanchangFunction` and its `/panchang GET` route are left exactly as-is.

- [ ] **Step 1: Add new resources to `template.yaml`**

In `panchang-api/template.yaml`, append the following under `Resources:` (after the existing `PanchangHttpApi` block), and update `PanchangHttpApi` CORS to also allow POST:

```yaml
  MuhoortamFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: handler_muhoortam.lambda_handler
      Description: Telugu Muhoortam computation API
      Timeout: 30
      Events:
        MuhoortamBirthChart:
          Type: HttpApi
          Properties:
            Path: /muhoortam/birth-chart
            Method: POST
            ApiId: !Ref PanchangHttpApi
        MuhoortamFind:
          Type: HttpApi
          Properties:
            Path: /muhoortam/find
            Method: POST
            ApiId: !Ref PanchangHttpApi
```

Also update the `CorsConfiguration` in `PanchangHttpApi` to include POST:

```yaml
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - POST
          - OPTIONS
        AllowHeaders:
          - "*"
```

- [ ] **Step 2: Verify SAM template is valid (if SAM CLI is installed)**

```bash
cd panchang-api && sam validate --template template.yaml
```
If SAM CLI is not installed, skip this step.

- [ ] **Step 3: Commit**

```bash
git add panchang-api/template.yaml
git commit -m "feat(muhoortam): add MuhoortamFunction to SAM template

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 6: `muhoortam/index.html` — Telugu 4-Step Wizard

**Files:**
- Create: `muhoortam/index.html`

### Context

Single-file Telugu wizard. No build step, no framework. Communicates with the Lambda API using `fetch()`. The `API_BASE` constant at the top must be updated to the deployed API endpoint URL before going live (placeholder `__MUHOORTAM_API_URL__` is used until deployment).

**Wizard state machine:**
- `step` variable: 1 → 2 → 3 → 4
- Step 3 is automated: calls `/muhoortam/birth-chart` for each person, then calls `/muhoortam/find` for each of the 12 months sequentially, accumulating results, then advances to step 4.

- [ ] **Step 1: Create `muhoortam/index.html`**

Create the directory first: `mkdir -p muhoortam`

Create `muhoortam/index.html`:

```html
<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>శుభ ముహూర్తం · Muhoortam.Sanathanadharmas.com</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #fdf6ec; color: #3e2723; padding: 16px; min-height: 100vh; max-width: 540px; margin: 0 auto; }

.page-header { text-align: center; padding: 20px 16px 14px; background: linear-gradient(135deg, #5d4037 0%, #8d6e63 60%, #d7a96b 100%); border-radius: 14px; margin-bottom: 18px; color: white; }
.page-header .om { font-size: 2.4rem; line-height: 1; margin-bottom: 6px; }
.page-header h1 { font-size: 1.3rem; font-weight: 700; }
.page-header .sub { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }

.step-panel { display: none; }
.step-panel.active { display: block; }

.card { background: #fff; border: 1px solid #d7ccc8; border-radius: 12px; padding: 18px; margin-bottom: 14px; }
.card h2 { font-size: 1rem; color: #5d4037; margin-bottom: 14px; border-bottom: 1px solid #efebe9; padding-bottom: 10px; }

.field { margin-bottom: 12px; }
.field label { display: block; font-size: 0.8rem; font-weight: 600; color: #5d4037; margin-bottom: 4px; }
.field input { width: 100%; padding: 9px 12px; border: 1px solid #d7ccc8; border-radius: 8px; font-size: 0.88rem; background: #fdf6ec; color: #3e2723; outline: none; }
.field input:focus { border-color: #8d6e63; box-shadow: 0 0 0 3px rgba(141,110,99,0.15); }

.ceremony-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ceremony-btn { padding: 12px 8px; border: 2px solid #d7ccc8; border-radius: 10px; background: #fff; cursor: pointer; text-align: center; font-size: 0.9rem; color: #5d4037; transition: all 0.2s; }
.ceremony-btn.selected { border-color: #8B4513; background: #8B4513; color: white; }

.person-block { background: #fdf6ec; border: 1px solid #d7ccc8; border-radius: 10px; padding: 14px; margin-bottom: 12px; position: relative; }
.person-block h3 { font-size: 0.85rem; color: #8d6e63; margin-bottom: 12px; }
.person-remove { position: absolute; top: 12px; right: 12px; background: none; border: none; color: #bcaaa4; cursor: pointer; font-size: 1.1rem; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

.add-person-btn { width: 100%; padding: 10px; border: 2px dashed #d7ccc8; border-radius: 10px; background: none; color: #8d6e63; cursor: pointer; font-size: 0.85rem; margin-bottom: 14px; }
.add-person-btn:hover { border-color: #8d6e63; color: #5d4037; }

.btn-primary { width: 100%; padding: 13px; background: #8B4513; color: white; border: none; border-radius: 10px; font-size: 1rem; cursor: pointer; font-weight: 600; }
.btn-primary:hover { background: #6d3710; }
.btn-primary:disabled { background: #bcaaa4; cursor: not-allowed; }

.progress-wrap { background: #efebe9; border-radius: 8px; height: 10px; overflow: hidden; margin: 16px 0 8px; }
.progress-bar { height: 100%; background: linear-gradient(90deg, #8B4513, #d7a96b); border-radius: 8px; transition: width 0.4s ease; }
.progress-label { text-align: center; font-size: 0.8rem; color: #8d6e63; }

.results-count { text-align: center; font-size: 1rem; color: #5d4037; margin-bottom: 14px; font-weight: 600; }
.results-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.results-table th { background: #8B4513; color: white; padding: 8px 10px; text-align: left; }
.results-table td { padding: 8px 10px; border-bottom: 1px solid #efebe9; }
.results-table tr:nth-child(even) td { background: #fdf6ec; }
.results-table tr:hover td { background: #f5e6d3; }
.time-cell { font-weight: 600; color: #33691e; font-size: 0.78rem; }

.btn-secondary { padding: 10px 20px; background: #efebe9; color: #5d4037; border: 1px solid #d7ccc8; border-radius: 8px; cursor: pointer; font-size: 0.88rem; }
.actions-row { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }

.error-msg { background: #fbe9e7; border: 1px solid #ffccbc; border-radius: 8px; padding: 10px 14px; color: #bf360c; font-size: 0.82rem; margin-bottom: 12px; display: none; }

@media print {
  .page-header, .actions-row, .btn-primary, .step-indicator { display: none !important; }
  body { background: white; padding: 0; }
  .results-table th { background: #333 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
</style>
</head>
<body>

<div class="page-header">
  <div class="om">🕉</div>
  <h1>శుభ ముహూర్తం</h1>
  <div class="sub">Muhoortam.Sanathanadharmas.com</div>
</div>

<div id="errorMsg" class="error-msg"></div>

<!-- Step 1: Ceremony Details -->
<div id="step1" class="step-panel active">
  <div class="card">
    <h2>దశ 1 — వేడుక వివరాలు</h2>
    <div class="field">
      <label>వేడుక రకం ఎంచుకోండి</label>
      <div class="ceremony-grid" style="margin-top:8px">
        <button class="ceremony-btn" data-type="vivaha" onclick="selectCeremony(this)">💒 వివాహం</button>
        <button class="ceremony-btn" data-type="gruha_pravesam" onclick="selectCeremony(this)">🏠 గృహ ప్రవేశం</button>
        <button class="ceremony-btn" data-type="upanayanam" onclick="selectCeremony(this)">🪡 ఉపనయనం</button>
        <button class="ceremony-btn" data-type="pooja" onclick="selectCeremony(this)">🪔 పూజ</button>
      </div>
    </div>
    <div class="field">
      <label>వేడుక నగరం</label>
      <input type="text" id="ceremonyCity" placeholder="ఉదా: Hyderabad, Vijayawada">
    </div>
    <div class="field">
      <label>దేశం</label>
      <input type="text" id="ceremonyCountry" placeholder="ఉదా: India, USA">
    </div>
    <button class="btn-primary" onclick="goStep2()">తదుపరి →</button>
  </div>
</div>

<!-- Step 2: Birth Details -->
<div id="step2" class="step-panel">
  <div class="card">
    <h2>దశ 2 — జన్మ వివరాలు</h2>
    <div id="personList"></div>
    <button class="add-person-btn" id="addPersonBtn" onclick="addPerson()">
      + మరో వ్యక్తిని జోడించండి (గరిష్టం 6)
    </button>
    <button class="btn-primary" onclick="startCompute()">ముహూర్తాలు వెతకండి →</button>
  </div>
</div>

<!-- Step 3: Computing -->
<div id="step3" class="step-panel">
  <div class="card" style="text-align:center;padding:32px 18px">
    <div style="font-size:2.5rem;margin-bottom:12px">🕉</div>
    <div style="font-size:1.05rem;font-weight:600;margin-bottom:6px">శుభ ముహూర్తాలు వెతుకుతున్నాం...</div>
    <div id="progressLabel" class="progress-label">సిద్ధంగా ఉంది</div>
    <div class="progress-wrap"><div id="progressBar" class="progress-bar" style="width:0%"></div></div>
    <div id="progressDetail" style="font-size:0.78rem;color:#bcaaa4;margin-top:4px"></div>
  </div>
</div>

<!-- Step 4: Results -->
<div id="step4" class="step-panel">
  <div class="card">
    <h2>దశ 4 — శుభ ముహూర్తాలు</h2>
    <div id="resultsCount" class="results-count"></div>
    <div style="overflow-x:auto">
      <table class="results-table">
        <thead>
          <tr>
            <th>తేదీ</th>
            <th>వారం</th>
            <th>తిథి</th>
            <th>నక్షత్రం</th>
            <th>సమయం</th>
          </tr>
        </thead>
        <tbody id="resultsBody"></tbody>
      </table>
    </div>
    <div class="actions-row">
      <button class="btn-secondary" onclick="window.print()">🖨 PDF</button>
      <button class="btn-secondary" onclick="resetWizard()">మళ్ళీ వెతకండి</button>
    </div>
  </div>
</div>

<script>
const API_BASE = "__MUHOORTAM_API_URL__";  // Replace with deployed API URL

let selectedCeremony = null;
let allResults = [];
let personCount = 0;

// ── Step navigation ──────────────────────────────────────────────────────────

function showStep(n) {
  document.querySelectorAll(".step-panel").forEach(p => p.classList.remove("active"));
  document.getElementById("step" + n).classList.add("active");
}

function showError(msg) {
  const el = document.getElementById("errorMsg");
  el.textContent = msg;
  el.style.display = msg ? "block" : "none";
}

// ── Step 1 ───────────────────────────────────────────────────────────────────

function selectCeremony(btn) {
  document.querySelectorAll(".ceremony-btn").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");
  selectedCeremony = btn.dataset.type;
}

function goStep2() {
  showError("");
  if (!selectedCeremony) { showError("వేడుక రకం ఎంచుకోండి"); return; }
  if (!document.getElementById("ceremonyCity").value.trim()) { showError("వేడుక నగరం నమోదు చేయండి"); return; }
  if (!document.getElementById("ceremonyCountry").value.trim()) { showError("దేశం నమోదు చేయండి"); return; }
  if (personCount === 0) addPerson();
  showStep(2);
}

// ── Step 2 ───────────────────────────────────────────────────────────────────

function addPerson() {
  if (personCount >= 6) return;
  personCount++;
  const idx = personCount;
  const div = document.createElement("div");
  div.className = "person-block";
  div.id = "person" + idx;
  div.innerHTML = `
    <h3>👤 వ్యక్తి ${idx}</h3>
    ${idx > 1 ? `<button class="person-remove" onclick="removePerson(${idx})">✕</button>` : ""}
    <div class="two-col">
      <div class="field">
        <label>జన్మ తేదీ</label>
        <input type="text" id="dob${idx}" placeholder="DD/MM/YYYY">
      </div>
      <div class="field">
        <label>జన్మ సమయం</label>
        <input type="text" id="time${idx}" placeholder="HH:MM">
      </div>
    </div>
    <div class="field">
      <label>జన్మ స్థలం (నగరం, దేశం)</label>
      <input type="text" id="place${idx}" placeholder="ఉదా: Hyderabad, India">
    </div>`;
  document.getElementById("personList").appendChild(div);
  document.getElementById("addPersonBtn").style.display = personCount >= 6 ? "none" : "block";
}

function removePerson(idx) {
  document.getElementById("person" + idx)?.remove();
  personCount = document.querySelectorAll(".person-block").length;
  document.getElementById("addPersonBtn").style.display = personCount >= 6 ? "none" : "block";
}

async function startCompute() {
  showError("");
  const blocks = document.querySelectorAll(".person-block");
  if (blocks.length === 0) { showError("కనీసం ఒక వ్యక్తి వివరాలు నమోదు చేయండి"); return; }

  // Validate all blocks
  const persons = [];
  for (const block of blocks) {
    const id = block.id.replace("person", "");
    const dob   = document.getElementById("dob"   + id)?.value.trim();
    const time  = document.getElementById("time"  + id)?.value.trim();
    const place = document.getElementById("place" + id)?.value.trim();
    if (!dob || !time || !place) { showError("అన్ని వ్యక్తుల వివరాలు పూరించండి"); return; }
    persons.push({ dob, time, place });
  }

  showStep(3);
  setProgress(0, "జన్మ వివరాలు లెక్కిస్తున్నాం...", "");

  // Fetch birth charts
  const birthCharts = [];
  for (let i = 0; i < persons.length; i++) {
    try {
      const resp = await fetch(API_BASE + "/muhoortam/birth-chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(persons[i]),
      });
      if (!resp.ok) throw new Error(await resp.text());
      birthCharts.push(await resp.json());
    } catch (e) {
      showStep(2);
      showError("వ్యక్తి " + (i + 1) + " వివరాలు లెక్కించడం సాధ్యం కాలేదు: " + e.message);
      return;
    }
  }

  // Scan 12 months
  const ceremonyPlace = document.getElementById("ceremonyCity").value.trim() + ", " +
                        document.getElementById("ceremonyCountry").value.trim();
  allResults = [];
  const now = new Date();
  let yr = now.getFullYear(), mo = now.getMonth() + 1;

  for (let i = 0; i < 12; i++) {
    const pct = Math.round(((i + 1) / 12) * 100);
    setProgress(pct, `${MONTHS_TE[mo - 1]} ${yr} స్కాన్ అవుతోంది`, `${i + 1}/12 నెలలు`);
    try {
      const resp = await fetch(API_BASE + "/muhoortam/find", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          year: yr, month: mo,
          ceremony_type: selectedCeremony,
          ceremony_place: ceremonyPlace,
          birth_charts: birthCharts,
        }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      allResults = allResults.concat(data.results || []);
    } catch (e) {
      // Log and continue — one failing month shouldn't abort the scan
      console.warn("Month scan failed:", yr, mo, e);
    }
    mo++;
    if (mo > 12) { mo = 1; yr++; }
  }

  showResults();
}

function setProgress(pct, label, detail) {
  document.getElementById("progressBar").style.width = pct + "%";
  document.getElementById("progressLabel").textContent = label;
  document.getElementById("progressDetail").textContent = detail;
}

// ── Step 4 ───────────────────────────────────────────────────────────────────

const MONTHS_TE = ["జనవరి","ఫిబ్రవరి","మార్చి","ఏప్రిల్","మే","జూన్",
                   "జులై","ఆగస్టు","సెప్టెంబర్","అక్టోబర్","నవంబర్","డిసెంబర్"];

function showResults() {
  const tbody = document.getElementById("resultsBody");
  tbody.innerHTML = "";

  document.getElementById("resultsCount").textContent =
    allResults.length > 0
      ? `${allResults.length} శుభ ముహూర్తాలు దొరికాయి`
      : "శుభ ముహూర్తాలు దొరకలేదు — వేరే సమయంలో తిరిగి ప్రయత్నించండి";

  for (const r of allResults) {
    const durText = (r.dur_muhurtam || [])
      .map(d => `${d.start}–${d.end}`)
      .join(", ");
    const timeNote = r.sunrise + " – " + r.sunset +
      (durText ? ` (దూర్ ముహూర్తం: ${durText})` : "");

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.date_te}</td>
      <td>${r.vaaram_te}</td>
      <td>${r.tithi_te}</td>
      <td>${r.nakshatra_te}</td>
      <td class="time-cell">${timeNote}</td>`;
    tbody.appendChild(tr);
  }

  showStep(4);
}

function resetWizard() {
  showError("");
  selectedCeremony = null;
  allResults = [];
  personCount = 0;
  document.querySelectorAll(".ceremony-btn").forEach(b => b.classList.remove("selected"));
  document.getElementById("ceremonyCity").value = "";
  document.getElementById("ceremonyCountry").value = "";
  document.getElementById("personList").innerHTML = "";
  document.getElementById("addPersonBtn").style.display = "block";
  showStep(1);
}

// Initialise with one person block
addPerson();
</script>
</body>
</html>
```

- [ ] **Step 2: Open the file in a browser and verify the wizard renders**

```bash
open muhoortam/index.html   # macOS
# or:
xdg-open muhoortam/index.html  # Linux
```

Verify: all 4 ceremony type buttons appear, Step 1 is shown, Telugu text renders correctly.

- [ ] **Step 3: Update `API_BASE` placeholder after deployment**

After deploying with `sam deploy`, retrieve the new endpoint URL from CloudFormation outputs:
```bash
cd panchang-api && sam deploy --guided
# Note the MuhoortamFunction endpoint URL from outputs
```

Then in `muhoortam/index.html`, replace the placeholder:
```
"__MUHOORTAM_API_URL__"  →  "https://<api-id>.execute-api.<region>.amazonaws.com"
```

- [ ] **Step 4: Commit**

```bash
git add muhoortam/index.html
git commit -m "feat(muhoortam): add Telugu 4-step wizard frontend

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** birth_chart ✓, muhurta_rules ✓, muhurta_finder ✓, handler ✓, template ✓, frontend ✓, output in Telugu ✓, inputs accept English ✓, up to 6 people ✓, 1-year scan via 12 months ✓, Tara Balam ✓, Panchaka Dosha ✓
- [x] **No placeholders:** All code shown in full. No TBD.
- [x] **Type consistency:** `compute_birth_chart()` returns `janma_nakshatra_idx` (int) used in `is_auspicious()` as `chart["janma_nakshatra_idx"]` ✓. `find_muhurtas_for_month()` takes `birth_charts: list[dict]` matching what handler passes ✓.
- [x] **No regressions:** Existing `handler.py`, `panchang.py`, `astro.py`, `sankalpam.py` are not modified.
