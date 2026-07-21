# People Tab & Full Kundali Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "👥 జనాలు" nav tab with an unlimited profile book and a full Kundali page showing natal chart, planet degrees, and a 120-year Vimshottari dasha accordion with highlighted mini charts per mahadasha.

**Architecture:** New `compute/dasha.py` handles Vimshottari maths. `compute/astro.py` gains `compute_planet_details()` returning exact degrees + retrograde. `birth_chart.py` wires both into the existing API response additively. The frontend gets three new sections in `index.html`: a nav tab toggle, a `#people-panel`, and a `#kundali-panel`.

**Tech Stack:** Python (pyswisseph, pytz), pytest, vanilla JS/CSS (no new dependencies)

---

## File Changelist

| File | Change |
|------|--------|
| `panchang-api/compute/dasha.py` | **New** — Vimshottari dasha computation |
| `panchang-api/compute/astro.py` | **Modified** — add `compute_planet_details()` |
| `panchang-api/compute/birth_chart.py` | **Modified** — add `planet_details` + `vimshottari_dasha` to response |
| `panchang-api/tests/test_dasha.py` | **New** — dasha unit tests |
| `panchang-api/tests/test_muhoortam.py` | **Modified** — new birth-chart response field tests |
| `docs/muhoortam/index.html` | **Modified** — People tab, People panel, Kundali panel |

---

## Task 1: Vimshottari Dasha Module (`compute/dasha.py`)

**Files:**
- Create: `panchang-api/compute/dasha.py`
- Create: `panchang-api/tests/test_dasha.py`

- [ ] **Step 1: Create the failing tests**

Create `panchang-api/tests/test_dasha.py`:

```python
"""Tests for Vimshottari dasha computation."""
import sys
import types
from datetime import datetime, timezone, timedelta
import pytest


def _load_dasha():
    """Load dasha module without swisseph dependency."""
    for mod in list(sys.modules):
        if "dasha" in mod:
            del sys.modules[mod]
    import importlib
    import compute.dasha as d
    importlib.reload(d)
    return d


def _birth_dt(year, month, day, hour=0, minute=0):
    """UTC-aware datetime for tests."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_dasha_sequence_sums_to_120_years():
    d = _load_dasha()
    assert sum(d.DASHA_YEARS.values()) == 120


def test_nakshatra_lord_rohini():
    """Rohini is nakshatra 3; lord_idx = 3 % 9 = 3 → 'chandra'."""
    d = _load_dasha()
    # Moon at 44°00' = nakshatra idx 3 (Rohini starts at 40°00')
    moon_lon = 44.0
    nak_idx = int(moon_lon / (360 / 27))
    assert nak_idx == 3
    assert d.DASHA_SEQUENCE[nak_idx % 9] == "chandra"


def test_balance_at_start_of_nakshatra():
    """Moon exactly at nakshatra start → full dasha years remaining."""
    d = _load_dasha()
    # Rohini starts at 40°00' exactly
    moon_lon = 40.0
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(moon_lon, birth_dt)
    # First dasha lord = chandra (10 years), full balance
    assert dashas[0]["lord"] == "chandra"
    assert abs(dashas[0]["years"] - 10.0) < 0.01


def test_balance_at_midpoint_of_nakshatra():
    """Moon at nakshatra midpoint → half the dasha years remaining."""
    d = _load_dasha()
    # Rohini spans 40°00'–53°20' = 13.333°; midpoint = 46.667°
    moon_lon = 40.0 + (360 / 27) / 2
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(moon_lon, birth_dt)
    assert dashas[0]["lord"] == "chandra"
    assert abs(dashas[0]["years"] - 5.0) < 0.05


def test_returns_nine_mahadashas():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    assert len(dashas) == 9


def test_each_mahadasha_has_nine_antardashas():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    for maha in dashas:
        assert len(maha["antardashas"]) == 9, f"{maha['lord']} has {len(maha['antardashas'])} antardashas"


def test_antardasha_dates_are_contiguous():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    maha = dashas[1]  # second mahadasha (full period)
    ads = maha["antardashas"]
    for i in range(len(ads) - 1):
        assert ads[i]["end"] == ads[i + 1]["start"], \
            f"Gap between antardasha {i} and {i+1}"


def test_mahadasha_dates_are_contiguous():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    for i in range(len(dashas) - 1):
        assert dashas[i]["end_date"] == dashas[i + 1]["start_date"]


def test_antardasha_years_sum_to_mahadasha_years():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    maha = dashas[1]  # use a full mahadasha
    ad_days = sum(
        (datetime.fromisoformat(a["end"]) - datetime.fromisoformat(a["start"])).days
        for a in maha["antardashas"]
    )
    maha_days = (
        datetime.fromisoformat(maha["end_date"]) -
        datetime.fromisoformat(maha["start_date"])
    ).days
    assert abs(ad_days - maha_days) <= 1  # allow 1 day rounding


def test_first_mahadasha_starts_at_birth():
    d = _load_dasha()
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(44.0, birth_dt)
    assert dashas[0]["start_date"] == "1990-08-15"


def test_response_includes_telugu_name_and_emoji():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    chandra = dashas[0]
    assert chandra["lord_te"] == "చంద్ర"
    assert chandra["lord_emoji"] == "🌙"
    assert chandra["antardashas"][0]["lord_te"] == "చంద్ర"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_dasha.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'compute.dasha'`

- [ ] **Step 3: Create `panchang-api/compute/dasha.py`**

```python
"""
Vimshottari dasha computation for Telugu Jyotish.

Computes the full 120-year dasha sequence from the moon's sidereal longitude
and birth datetime, following the standard South Indian Vimshottari system.
"""
from __future__ import annotations
from datetime import datetime, timedelta

DASHA_SEQUENCE = [
    "ketu", "shukra", "ravi", "chandra", "kuja",
    "rahu", "guru", "shani", "budha"
]

DASHA_YEARS: dict[str, int] = {
    "ketu": 7, "shukra": 20, "ravi": 6, "chandra": 10, "kuja": 7,
    "rahu": 18, "guru": 16, "shani": 19, "budha": 17,
}

DASHA_LORD_TE: dict[str, str] = {
    "ketu": "కేతు", "shukra": "శుక్ర", "ravi": "రవి", "chandra": "చంద్ర",
    "kuja": "కుజ", "rahu": "రాహు", "guru": "గురు", "shani": "శని", "budha": "బుధ",
}

DASHA_EMOJI: dict[str, str] = {
    "ketu": "☋", "shukra": "♀", "ravi": "☀️", "chandra": "🌙",
    "kuja": "♂", "rahu": "☊", "guru": "♃", "shani": "♄", "budha": "☿",
}

_DAYS_PER_YEAR = 365.25
_NAK_SPAN = 360.0 / 27  # 13.333...° per nakshatra


def compute_vimshottari_dasha(moon_lon: float, birth_dt: datetime) -> list[dict]:
    """Compute full 120-year Vimshottari dasha sequence from birth.

    Args:
        moon_lon: Sidereal moon longitude at birth in degrees [0, 360).
        birth_dt: Birth datetime (timezone-aware or naive UTC).

    Returns:
        List of 9 mahadasha dicts ordered from birth. Each dict has:
        lord, lord_te, lord_emoji, years (float), start_date (YYYY-MM-DD),
        end_date (YYYY-MM-DD), antardashas (list of 9 dicts with lord,
        lord_te, start, end in YYYY-MM-DD).
    """
    nak_idx = int(moon_lon / _NAK_SPAN) % 27
    lord_seq_start = nak_idx % 9           # index into DASHA_SEQUENCE

    nak_start_lon = nak_idx * _NAK_SPAN
    traversed_fraction = (moon_lon - nak_start_lon) / _NAK_SPAN
    first_lord = DASHA_SEQUENCE[lord_seq_start]
    balance_years = (1.0 - traversed_fraction) * DASHA_YEARS[first_lord]

    dashas: list[dict] = []
    current_dt = birth_dt

    for i in range(9):
        lord = DASHA_SEQUENCE[(lord_seq_start + i) % 9]
        years = balance_years if i == 0 else float(DASHA_YEARS[lord])
        end_dt = current_dt + timedelta(days=years * _DAYS_PER_YEAR)

        antardashas = _compute_antardashas(lord, years, current_dt)

        dashas.append({
            "lord":       lord,
            "lord_te":    DASHA_LORD_TE[lord],
            "lord_emoji": DASHA_EMOJI[lord],
            "years":      round(years, 4),
            "start_date": current_dt.strftime("%Y-%m-%d"),
            "end_date":   end_dt.strftime("%Y-%m-%d"),
            "antardashas": antardashas,
        })
        current_dt = end_dt

    return dashas


def _compute_antardashas(
    maha_lord: str, maha_years: float, maha_start: datetime
) -> list[dict]:
    """Compute 9 antardasha sub-periods for a given mahadasha."""
    lord_seq_idx = DASHA_SEQUENCE.index(maha_lord)
    ads: list[dict] = []
    ad_start = maha_start

    for j in range(9):
        sub_lord = DASHA_SEQUENCE[(lord_seq_idx + j) % 9]
        sub_years = (maha_years * DASHA_YEARS[sub_lord]) / 120.0
        ad_end = ad_start + timedelta(days=sub_years * _DAYS_PER_YEAR)
        ads.append({
            "lord":    sub_lord,
            "lord_te": DASHA_LORD_TE[sub_lord],
            "start":   ad_start.strftime("%Y-%m-%d"),
            "end":     ad_end.strftime("%Y-%m-%d"),
        })
        ad_start = ad_end

    return ads
```

- [ ] **Step 4: Run tests and confirm they pass**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_dasha.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add panchang-api/compute/dasha.py panchang-api/tests/test_dasha.py
git commit -m "feat: add Vimshottari dasha computation module"
```

---

## Task 2: Planet Details in `astro.py`

**Files:**
- Modify: `panchang-api/compute/astro.py` (add `compute_planet_details` after `compute_planet_rashis`)

- [ ] **Step 1: Add `compute_planet_details()` to `astro.py`**

Add this function after `compute_planet_rashis` (around line 175):

```python
def compute_planet_details(jd: float) -> dict[str, dict]:
    """Return rashi_idx, deg, min, retrograde for all 9 Jyotish grahas at jd.

    deg and min are the planet's position within its rashi (0–29°, 0–59').
    retrograde is True when the planet's apparent motion is backward.
    Rahu and Ketu are always retrograde by convention.
    """
    _init_swe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    bodies = {
        "ravi":    swe.SUN,
        "chandra": swe.MOON,
        "kuja":    swe.MARS,
        "budha":   swe.MERCURY,
        "guru":    swe.JUPITER,
        "shukra":  swe.VENUS,
        "shani":   swe.SATURN,
    }
    details: dict[str, dict] = {}
    for name, pid in bodies.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        lon = xx[0] % 360
        speed = xx[3]            # degrees/day; negative = retrograde
        deg_in_rashi = lon % 30
        details[name] = {
            "rashi_idx":  int(lon / 30) % 12,
            "deg":        int(deg_in_rashi),
            "min":        int((deg_in_rashi % 1) * 60),
            "retrograde": speed < 0,
        }
    # Rahu (TRUE_NODE moves retrograde by definition)
    xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    rahu_lon = xx[0] % 360
    rahu_deg = rahu_lon % 30
    details["rahu"] = {
        "rashi_idx":  int(rahu_lon / 30) % 12,
        "deg":        int(rahu_deg),
        "min":        int((rahu_deg % 1) * 60),
        "retrograde": True,
    }
    # Ketu is always 180° from Rahu
    ketu_lon = (rahu_lon + 180) % 360
    ketu_deg = ketu_lon % 30
    details["ketu"] = {
        "rashi_idx":  int(ketu_lon / 30) % 12,
        "deg":        int(ketu_deg),
        "min":        int((ketu_deg % 1) * 60),
        "retrograde": True,
    }
    return details
```

- [ ] **Step 2: Run existing tests to make sure nothing is broken**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_muhoortam.py -v -x 2>&1 | tail -10
```

Expected: all previously passing tests still PASS.

- [ ] **Step 3: Commit**

```bash
git add panchang-api/compute/astro.py
git commit -m "feat: add compute_planet_details() to astro module"
```

---

## Task 3: Enhance `birth_chart.py` + Update Tests

**Files:**
- Modify: `panchang-api/compute/birth_chart.py`
- Modify: `panchang-api/tests/test_muhoortam.py`

- [ ] **Step 1: Add failing tests to `test_muhoortam.py`**

In `_make_birth_chart_module()`, add `compute_planet_details` to `fake_astro` and add a `compute.dasha` mock. Find the line `sys.modules["compute.astro"] = fake_astro` and add before it:

```python
    fake_astro.compute_planet_details = lambda jd: {
        p: {"rashi_idx": i % 12, "deg": 5, "min": 30, "retrograde": False}
        for i, p in enumerate(["ravi","chandra","kuja","budha","guru","shukra","shani","rahu","ketu"])
    }
```

After the `sys.modules["compute.astro"] = fake_astro` line, add:

```python
    # Mock dasha module
    fake_dasha = types.ModuleType("compute.dasha")
    fake_dasha.compute_vimshottari_dasha = lambda moon_lon, birth_dt: [
        {
            "lord": "chandra", "lord_te": "చంద్ర", "lord_emoji": "🌙",
            "years": 10.0, "start_date": "1990-08-15", "end_date": "2000-08-14",
            "antardashas": [
                {"lord": "chandra", "lord_te": "చంద్ర",
                 "start": "1990-08-15", "end": "1991-02-14"}
            ] * 9,
        }
    ] * 9
    sys.modules["compute.dasha"] = fake_dasha
```

Then add these test functions after the existing birth chart tests:

```python
def test_birth_chart_planet_details_present():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert "planet_details" in result
    assert set(result["planet_details"].keys()) == {
        "ravi","chandra","kuja","budha","guru","shukra","shani","rahu","ketu"
    }


def test_birth_chart_planet_details_structure():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    for name, d in result["planet_details"].items():
        assert "rashi_idx" in d, f"{name} missing rashi_idx"
        assert "deg" in d, f"{name} missing deg"
        assert "min" in d, f"{name} missing min"
        assert "retrograde" in d, f"{name} missing retrograde"
        assert 0 <= d["rashi_idx"] <= 11
        assert 0 <= d["deg"] <= 29
        assert 0 <= d["min"] <= 59


def test_birth_chart_vimshottari_dasha_present():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert "vimshottari_dasha" in result
    assert len(result["vimshottari_dasha"]) == 9


def test_birth_chart_vimshottari_dasha_structure():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    maha = result["vimshottari_dasha"][0]
    for key in ("lord", "lord_te", "lord_emoji", "years", "start_date", "end_date", "antardashas"):
        assert key in maha, f"missing key: {key}"
    assert len(maha["antardashas"]) == 9
```

- [ ] **Step 2: Run new tests to confirm they fail**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_muhoortam.py::test_birth_chart_planet_details_present tests/test_muhoortam.py::test_birth_chart_vimshottari_dasha_present -v
```

Expected: FAIL — `planet_details` and `vimshottari_dasha` not in response yet.

- [ ] **Step 3: Update `birth_chart.py` to add new fields**

Replace the imports section and `compute_birth_chart` function:

```python
"""
Birth chart computation for Muhurta calculations.
Computes janma nakshatra, janma rashi, and lagna from birth date/time/place.
"""
from __future__ import annotations
import swisseph as swe
import pytz
from datetime import datetime

from .astro import moon_longitude, compute_planet_rashis, compute_planet_details
from .panchang import NAKSHATRA_TE, compute_panchang
from .dasha import compute_vimshottari_dasha

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


def _birth_datetime(year: int, month: int, day: int, hour: int, minute: int,
                    tz_name: str) -> datetime:
    """Return timezone-aware local datetime of birth."""
    tz = pytz.timezone(tz_name)
    return tz.localize(datetime(year, month, day, hour, minute))


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

    Returns dict with: janma_nakshatra_idx, janma_nakshatra_te,
    janma_rashi_idx, janma_rashi_te, lagna_idx, lagna_te,
    planet_rashis, planet_details, birth_panchang, vimshottari_dasha.

    Note: birth_panchang elements reflect the panchang at sunrise on the birth
    day, following Telugu traditional convention — not the exact birth moment.
    """
    jd = _birth_jd(year, month, day, hour, minute, tz_name)
    moon_lon = moon_longitude(jd)

    nak_idx   = int(moon_lon / (360.0 / 27)) % 27
    rashi_idx = int(moon_lon / 30) % 12
    lagna_idx = compute_lagna(jd, lat, lon)

    nak_start = nak_idx * (360.0 / 27)
    padam = int((moon_lon - nak_start) / (360.0 / 108)) + 1

    planet_rashis  = compute_planet_rashis(jd)
    planet_details = compute_planet_details(jd)

    pan = compute_panchang(jd, lat, lon, tz_name)
    birth_panchang = {
        "tithi_te":     pan["tithi"]["te"],
        "vaara_te":     pan["vaaram"]["te"],
        "nakshatra_te": pan["nakshatra"]["te"],
        "yoga_te":      pan["yoga"]["te"],
        "karanam_te":   pan["karana"]["te"],
    }

    birth_dt = _birth_datetime(year, month, day, hour, minute, tz_name)
    vimshottari_dasha = compute_vimshottari_dasha(moon_lon, birth_dt)

    return {
        "janma_nakshatra_idx":   nak_idx,
        "janma_nakshatra_te":    NAKSHATRA_TE[nak_idx],
        "janma_nakshatra_padam": padam,
        "janma_rashi_idx":       rashi_idx,
        "janma_rashi_te":        RASHI_TE[rashi_idx],
        "lagna_idx":             lagna_idx,
        "lagna_te":              RASHI_TE[lagna_idx],
        "planet_rashis":         planet_rashis,
        "planet_details":        planet_details,
        "birth_panchang":        birth_panchang,
        "vimshottari_dasha":     vimshottari_dasha,
    }
```

- [ ] **Step 4: Run all birth chart tests**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_muhoortam.py -k "birth_chart" -v
```

Expected: all birth chart tests PASS (including the 4 new ones).

- [ ] **Step 5: Run full test suite**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_muhoortam.py tests/test_dasha.py -v 2>&1 | tail -20
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add panchang-api/compute/birth_chart.py panchang-api/tests/test_muhoortam.py
git commit -m "feat: add planet_details and vimshottari_dasha to birth chart API"
```

---

## Task 4: People Tab + People Panel (Frontend)

**Files:**
- Modify: `docs/muhoortam/index.html`

This task adds the nav tab toggle and the People panel (profile cards + add form). Does **not** yet add the Full Kundali panel (Task 5).

- [ ] **Step 1: Add tab buttons to the nav header**

Find the `<header class="site-nav">` block and replace its content with:

```html
<header class="site-nav">
  <div class="nav-logo">
    <div class="nav-logo-mark">🕉</div>
    <div class="nav-logo-text">Telugu <span>Muhurtam</span></div>
  </div>
  <div class="nav-right">
    <button type="button" class="nav-tab active" id="tabMuhurtam"
      onclick="showAppTab('muhurtam')" aria-label="ముహూర్తం">
      🗓 <span class="nav-tab-label">ముహూర్తం</span>
    </button>
    <button type="button" class="nav-tab" id="tabPeople"
      onclick="showAppTab('people')" aria-label="జనాలు">
      👥 <span class="nav-tab-label">జనాలు</span>
    </button>
    <button
      type="button"
      class="lang-toggle"
      id="langToggle"
      onclick="toggleLang()"
      title="Switch language / భాష మార్చండి"
      aria-label="Language toggle">
      <span id="langLabel-te" class="lang-seg active">తె</span>
      <span id="langLabel-en" class="lang-seg">EN</span>
    </button>
  </div>
</header>
```

- [ ] **Step 2: Add nav-tab CSS**

In the CSS section (find `.nav-right` styles around line 82), add after the existing `.nav-right` rule:

```css
.nav-tab {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.25);
  color: rgba(255,255,255,0.8);
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.82rem;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}
.nav-tab.active {
  background: var(--gold, #f5c842);
  border-color: var(--gold, #f5c842);
  color: var(--brown-dark, #3b1f0a);
  font-weight: 700;
}
.nav-tab:hover:not(.active) {
  background: rgba(255,255,255,0.1);
}
.nav-tab-label { display: inline; }
@media (max-width: 420px) {
  .nav-tab-label { display: none; }
}
```

- [ ] **Step 3: Add the `#people-panel` div**

After the closing `</header>` tag and before `<nav id="breadcrumb"...>`, add:

```html
<!-- ══ PEOPLE PANEL ══ -->
<div id="people-panel" style="display:none">
  <div class="people-header">
    <div class="section-title">👥 నా జనాలు</div>
  </div>
  <div class="people-grid" id="peopleGrid"></div>
</div>
```

- [ ] **Step 4: Add People panel CSS**

In the CSS section, add:

```css
/* ── People panel ──────────────────────────────── */
#people-panel { max-width: 900px; margin: 0 auto; padding: 16px; }
.people-header { margin-bottom: 16px; }
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.people-card {
  background: var(--card-bg, #fff);
  border: 1px solid var(--gold-light, #d4a96a);
  border-radius: 10px;
  padding: 14px;
}
.people-card-name { font-weight: 700; font-size: 1rem; color: var(--brown-dark, #3b1f0a); }
.people-card-meta { font-size: 0.78rem; color: var(--text-2, #888); margin-top: 2px; }
.people-card-astro {
  display: grid; grid-template-columns: 1fr 1fr; gap: 2px 8px;
  font-size: 0.76rem; margin: 8px 0; color: var(--brown-mid, #6b3a2a);
}
.people-card-astro b { color: var(--text-1, #444); }
.people-card-actions { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.people-card-btn-primary {
  background: var(--brown-dark, #3b1f0a);
  color: var(--gold, #f5c842);
  border: none; border-radius: 5px;
  padding: 6px 10px; cursor: pointer; font-size: 0.8rem; font-weight: 700;
  font-family: inherit; width: 100%;
}
.people-card-btn-secondary {
  background: transparent;
  border: 1px solid var(--gold-light, #d4a96a);
  color: var(--brown-dark, #3b1f0a);
  border-radius: 5px; padding: 5px 10px;
  cursor: pointer; font-size: 0.78rem; font-family: inherit; width: 100%;
}
.people-card-btn-del {
  background: transparent; border: none;
  color: var(--text-2, #888); font-size: 0.72rem;
  cursor: pointer; text-align: right; padding: 0; font-family: inherit;
}
.people-card-add {
  border: 2px dashed var(--gold-light, #d4a96a);
  border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  color: var(--gold-light, #d4a96a); cursor: pointer;
  min-height: 120px; background: transparent;
  font-size: 0.88rem; gap: 6px;
}
.people-card-add:hover { background: rgba(212,169,106,0.07); }
.people-add-form { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.people-add-form input {
  border: 1px solid var(--gold-light, #d4a96a);
  border-radius: 5px; padding: 6px 8px;
  font-size: 0.82rem; font-family: inherit; width: 100%; box-sizing: border-box;
}
.people-add-form label { font-size: 0.75rem; color: var(--text-2, #888); }
```

- [ ] **Step 5: Add `showAppTab()` and `renderPeoplePanel()` JS functions**

Find the JS section (around line 1510 where `APP_LANG` is defined). Add these functions nearby:

```javascript
// ── App tab switching ────────────────────────────────────────────────────────
function showAppTab(tab) {
  const muhurtamEls = [
    document.getElementById("hero"),
    document.querySelector(".step-bar"),
    document.getElementById("panel1"),
    document.getElementById("panel2"),
    document.getElementById("panel3"),
    document.getElementById("breadcrumb"),
  ].filter(Boolean);
  const peoplePanel   = document.getElementById("people-panel");
  const kundaliPanel  = document.getElementById("kundali-panel");
  const tabMuhurtam   = document.getElementById("tabMuhurtam");
  const tabPeople     = document.getElementById("tabPeople");

  if (tab === "people") {
    muhurtamEls.forEach(el => el.style.display = "none");
    if (kundaliPanel) kundaliPanel.style.display = "none";
    if (peoplePanel)  peoplePanel.style.display  = "";
    if (tabMuhurtam)  tabMuhurtam.classList.remove("active");
    if (tabPeople)    tabPeople.classList.add("active");
    renderPeoplePanel();
  } else {
    if (peoplePanel)  peoplePanel.style.display  = "none";
    if (kundaliPanel) kundaliPanel.style.display  = "none";
    muhurtamEls.forEach(el => {
      // restore display only for elements that were shown before
      if (el.id === "breadcrumb" || el.id === "hero") el.style.display = "";
      else el.style.display = "";
    });
    if (tabMuhurtam)  tabMuhurtam.classList.add("active");
    if (tabPeople)    tabPeople.classList.remove("active");
    // re-trigger current panel display (step logic handles the rest)
    goToCurrentStep();
  }
}

// ── People panel rendering ────────────────────────────────────────────────────
function renderPeoplePanel() {
  const grid = document.getElementById("peopleGrid");
  if (!grid) return;
  const profiles = loadProfiles();
  const cards = profiles.map((p, i) => {
    const bc = p.birthChart || {};
    const nak = bc.janma_nakshatra_te
      ? `${bc.janma_nakshatra_te}${bc.janma_nakshatra_padam ? " " + bc.janma_nakshatra_padam + "వ పాదం" : ""}`
      : "—";
    const dob = p.dob ? p.dob.split("-").reverse().join("/") : "—";
    return `
      <div class="people-card">
        <div class="people-card-name">${_escHtml(p.name)}</div>
        <div class="people-card-meta">${dob}${p.place ? " · " + _escHtml(p.place) : ""}</div>
        <div class="people-card-astro">
          <b>నక్షత్రం</b><span>${nak}</span>
          <b>రాశి</b><span>${bc.janma_rashi_te || "—"}</span>
          <b>లగ్నం</b><span>${bc.lagna_te || "—"}</span>
        </div>
        <div class="people-card-actions">
          <button class="people-card-btn-primary" onclick="openFullKundali(${i})">🪐 పూర్ణ కుండలి చూడండి</button>
          <button class="people-card-btn-secondary" onclick="addProfileToMuhurtam(${i})">+ ముహూర్తంలో జోడించు</button>
          <button class="people-card-btn-del" onclick="deletePeopleProfile(${i})">✕ తొలగించు</button>
        </div>
      </div>`;
  }).join("");

  grid.innerHTML = cards + `
    <div class="people-card-add" id="peopleAddCard" onclick="togglePeopleAddForm()">
      <span style="font-size:1.8rem">＋</span>
      <span>కొత్త వ్యక్తిని జోడించు</span>
      <div id="peopleAddFormWrap" style="display:none;width:100%" onclick="event.stopPropagation()">
        <div class="people-add-form" id="peopleAddForm">
          <label>పేరు</label>
          <input id="paName" type="text" placeholder="పేరు నమోదు చేయండి">
          <label>పుట్టిన తేదీ</label>
          <input id="paDob"  type="date">
          <label>పుట్టిన సమయం</label>
          <input id="paTime" type="time">
          <label>పుట్టిన స్థలం</label>
          <input id="paPlace" type="text" placeholder="ఊరు పేరు">
          <button class="people-card-btn-primary" onclick="savePeopleProfile()">💾 సేవ్ చేయండి</button>
          <div id="paError" style="color:#c00;font-size:0.75rem;display:none"></div>
        </div>
      </div>
    </div>`;
}

function togglePeopleAddForm() {
  const wrap = document.getElementById("peopleAddFormWrap");
  if (wrap) wrap.style.display = wrap.style.display === "none" ? "" : "none";
}

async function savePeopleProfile() {
  const name  = (document.getElementById("paName")?.value  || "").trim();
  const dobRaw= (document.getElementById("paDob")?.value   || "").trim();
  const time  = (document.getElementById("paTime")?.value  || "").trim();
  const place = (document.getElementById("paPlace")?.value || "").trim();
  const errEl = document.getElementById("paError");
  if (!name || !dobRaw || !time || !place) {
    if (errEl) { errEl.textContent = "అన్ని వివరాలు నమోదు చేయండి"; errEl.style.display = ""; }
    return;
  }
  if (errEl) errEl.style.display = "none";
  const [y, m, d] = dobRaw.split("-");
  const btn = document.querySelector("#peopleAddForm .people-card-btn-primary");
  if (btn) btn.textContent = "⏳ ...";
  try {
    const r = await fetch(API_BASE + "/muhoortam/birth-chart", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dob: `${d}/${m}/${y}`, time, place }),
    });
    if (!r.ok) throw new Error(await r.text());
    const birthChart = await r.json();
    saveProfileToStorage({ name, dob: dobRaw, time, place, birthChart });
    renderPeoplePanel();
  } catch (e) {
    if (btn) btn.textContent = "💾 సేవ్ చేయండి";
    if (errEl) { errEl.textContent = "సేవ్ విఫలమైంది: " + e.message; errEl.style.display = ""; }
  }
}

function deletePeopleProfile(idx) {
  const profiles = loadProfiles();
  const p = profiles[idx];
  if (!p) return;
  if (!confirm(`"${p.name}" ని తొలగించాలా?`)) return;
  profiles.splice(idx, 1);
  localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles));
  renderProfileChips();
  renderPeoplePanel();
}

function addProfileToMuhurtam(idx) {
  const profiles = loadProfiles();
  const p = profiles[idx];
  if (!p) return;
  const blocks = document.querySelectorAll(".person-block");
  if (blocks.length >= 6) {
    alert("ముహూర్తం ఫారంలో గరిష్టం 6 వ్యక్తులు మాత్రమే జోడించవచ్చు.");
    return;
  }
  showAppTab("muhurtam");
  // Switch to step 2 so person blocks are visible, then add and fill
  goPanel2();
  setTimeout(() => {
    addPerson();
    const newBlocks = document.querySelectorAll(".person-block");
    const last = newBlocks[newBlocks.length - 1];
    if (!last) return;
    const bid = last.id.replace("person", "");
    const nameEl  = document.getElementById("pname"  + bid);
    const dobEl   = document.getElementById("dob"    + bid);
    const timeEl  = document.getElementById("time"   + bid);
    const placeEl = document.getElementById("place"  + bid);
    if (nameEl)  nameEl.value  = p.name;
    if (dobEl)   dobEl.value   = p.dob;
    if (timeEl)  timeEl.value  = p.time;
    if (placeEl) placeEl.value = p.place;
  }, 150);
}

function _escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function goToCurrentStep() {
  // Re-show whichever step panel is currently active
  const panels = ["panel1","panel2","panel3"];
  let found = false;
  panels.forEach(id => {
    const el = document.getElementById(id);
    if (el && el.style.display !== "none") found = true;
  });
  if (!found) {
    const p1 = document.getElementById("panel1");
    if (p1) p1.style.display = "";
  }
}
```

- [ ] **Step 6: Smoke test in browser**

Open the app, click "👥 జనాలు" tab — should show People panel with profile cards and "＋ కొత్త వ్యక్తిని జోడించు" card. Click the add card to expand the form. Add a person and save — should appear as a profile card. Click "ముహూర్తం" tab — should return to ceremony planner.

- [ ] **Step 7: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add People nav tab and People panel with unlimited profiles"
```

---

## Task 5: Full Kundali Panel — HTML, CSS, and Rendering Logic

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Add `#kundali-panel` HTML**

After the `#people-panel` div (before `<nav id="breadcrumb"`), add:

```html
<!-- ══ KUNDALI PANEL ══ -->
<div id="kundali-panel" style="display:none">
  <div class="kundali-header">
    <button class="kundali-back-btn" onclick="showAppTab('people')">← జనాలు</button>
    <div class="kundali-title" id="kundaliTitle">పూర్ణ కుండలి</div>
    <button class="kundali-pdf-btn" onclick="printKundaliPage()">📄 PDF ఎగుమతి</button>
  </div>
  <div class="kundali-body" id="kundaliBody">
    <div class="jc-loading">⏳ లోడ్ అవుతున్నది...</div>
  </div>
</div>
```

- [ ] **Step 2: Add Kundali panel CSS**

```css
/* ── Kundali full page ──────────────────────────────── */
#kundali-panel { max-width: 900px; margin: 0 auto; padding: 16px; }
.kundali-header {
  display: flex; align-items: center; gap: 10px;
  background: var(--brown-dark, #3b1f0a); color: #fff;
  padding: 10px 14px; border-radius: 8px; margin-bottom: 16px;
}
.kundali-back-btn {
  background: transparent; border: 1px solid rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.85); padding: 4px 10px; border-radius: 4px;
  cursor: pointer; font-size: 0.8rem; font-family: inherit;
}
.kundali-title { flex: 1; font-weight: 700; font-size: 1rem; }
.kundali-pdf-btn {
  background: var(--gold, #f5c842); border: none;
  color: var(--brown-dark, #3b1f0a); padding: 5px 12px;
  border-radius: 4px; cursor: pointer; font-size: 0.82rem;
  font-weight: 700; font-family: inherit;
}
/* Top section: chart + planet table */
.kundali-top {
  display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;
}
.kundali-chart-wrap { flex: 0 0 auto; }
.kundali-planet-table-wrap { flex: 1; min-width: 220px; }
.kundali-planet-table {
  width: 100%; border-collapse: collapse; font-size: 0.82rem;
}
.kundali-planet-table th {
  background: var(--cream2, #fdf0e0); padding: 5px 8px;
  text-align: left; font-size: 0.75rem; color: var(--brown-mid, #6b3a2a);
  border-bottom: 2px solid var(--gold-light, #d4a96a);
}
.kundali-planet-table td {
  padding: 4px 8px; border-bottom: 1px solid var(--border, #e8d5c4);
}
.kundali-planet-table tr:nth-child(even) td {
  background: var(--cream, #fdf6ee);
}
.kundali-retro { color: #c00; font-size: 0.72rem; font-weight: 700; }
/* Birth info strip */
.kundali-birth-strip {
  background: var(--cream, #fdf6ee);
  border: 1px solid var(--border, #e8d5c4);
  border-radius: 6px; padding: 10px 14px; margin-bottom: 16px;
  display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 0.82rem;
}
.kundali-birth-strip b { color: var(--brown-mid, #6b3a2a); }
/* Dasha accordion */
.kundali-dasha-header {
  background: var(--gold, #f5c842); color: var(--brown-dark, #3b1f0a);
  padding: 8px 12px; font-weight: 700; font-size: 0.9rem;
  border-radius: 6px 6px 0 0; margin-top: 16px;
}
.dasha-row {
  border: 1px solid var(--border, #e8d5c4);
  border-top: none; background: #fff;
}
.dasha-row-header {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 12px; cursor: pointer; font-size: 0.85rem;
  color: var(--brown-dark, #3b1f0a); user-select: none;
}
.dasha-row-header:hover { background: var(--cream, #fdf6ee); }
.dasha-row.current > .dasha-row-header {
  background: #fff9e6; font-weight: 700;
}
.dasha-current-badge {
  background: #e63946; color: #fff;
  font-size: 0.68rem; padding: 1px 7px; border-radius: 10px; font-weight: 700;
}
.dasha-row-dates { margin-left: auto; font-size: 0.78rem; color: var(--text-2, #888); }
.dasha-row-body {
  display: none; padding: 10px 12px;
  border-top: 1px solid var(--border, #e8d5c4);
  background: var(--cream, #fdf6ee);
}
.dasha-row.open > .dasha-row-body { display: flex; gap: 14px; flex-wrap: wrap; }
.dasha-mini-chart { flex: 0 0 auto; }
.dasha-ad-table {
  flex: 1; min-width: 200px; border-collapse: collapse; font-size: 0.78rem;
}
.dasha-ad-table th {
  background: var(--cream2, #fdf0e0); padding: 4px 8px;
  text-align: left; font-size: 0.72rem; color: var(--brown-mid, #6b3a2a);
  border-bottom: 1px solid var(--gold-light, #d4a96a);
}
.dasha-ad-table td { padding: 3px 8px; border-bottom: 1px solid var(--border, #e8d5c4); }
.dasha-ad-table tr.current-ad > td { background: #fff9c4; font-weight: 700; }
/* ── Print CSS ──────────────────────────────────────── */
@media print {
  body.kundali-printing .site-nav,
  body.kundali-printing #people-panel,
  body.kundali-printing .kundali-back-btn,
  body.kundali-printing .kundali-pdf-btn { display: none !important; }
  body.kundali-printing #kundali-panel { display: block !important; }
  body.kundali-printing .dasha-row-body { display: flex !important; }
}
```

- [ ] **Step 3: Add `openFullKundali()` and `renderKundaliPanel()` JS**

```javascript
// ── Full Kundali panel ───────────────────────────────────────────────────────

async function openFullKundali(idx) {
  const profiles = loadProfiles();
  const p = profiles[idx];
  if (!p) return;

  // Switch to kundali panel
  document.getElementById("people-panel").style.display   = "none";
  document.getElementById("kundali-panel").style.display  = "";
  document.getElementById("kundaliTitle").textContent =
    p.name + " — పూర్ణ కుండలి";

  const body = document.getElementById("kundaliBody");
  const bc   = p.birthChart || {};

  // If cached chart already has full data, render immediately
  if (bc.planet_details && bc.vimshottari_dasha) {
    _renderKundaliBody(bc, p);
    return;
  }

  // Fetch enriched data
  body.innerHTML = '<div class="jc-loading">⏳ లోడ్ అవుతున్నది...</div>';
  try {
    let dob = p.dob || "";
    if (dob.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [y, m, d] = dob.split("-");
      dob = `${d}/${m}/${y}`;
    }
    const resp = await fetch(API_BASE + "/muhoortam/birth-chart", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dob, time: p.time || "", place: p.place || "" }),
    });
    if (!resp.ok) {
      const txt = await resp.text().catch(() => "");
      throw new Error("API " + resp.status + ": " + txt);
    }
    const chart = await resp.json();
    // Cache the enriched chart
    p.birthChart = chart;
    saveProfileToStorage(p);
    _renderKundaliBody(chart, p);
  } catch (e) {
    body.innerHTML = `<div class="jc-error">⚠️ లోడ్ విఫలమైంది.<br><small>${_escHtml(e.message)}</small></div>`;
  }
}

function _renderKundaliBody(chart, profile) {
  const body = document.getElementById("kundaliBody");
  if (!body) return;

  const RASHI_TE_LIST = ["మేషం","వృషభం","మిథునం","కర్కాటకం","సింహం","కన్య",
                          "తులం","వృశ్చికం","ధనుస్సు","మకరం","కుంభం","మీనం"];
  const PLANET_LABELS = {
    ravi:"☀️ రవి", chandra:"🌙 చంద్ర", kuja:"♂ కుజ", budha:"☿ బుధ",
    guru:"♃ గురు", shukra:"♀ శుక్ర", shani:"♄ శని", rahu:"☊ రాహు", ketu:"☋ కేతు"
  };
  const PLANET_ORDER = ["ravi","chandra","kuja","budha","guru","shukra","shani","rahu","ketu"];

  // ── Section 1: Top (chart + planet table) ──
  const chartHtml = renderHoroscopeChart(chart.planet_rashis, chart.lagna_idx);

  let planetRows = "";
  for (const name of PLANET_ORDER) {
    const d  = (chart.planet_details || {})[name] || {};
    const ri = d.rashi_idx ?? (chart.planet_rashis || {})[name] ?? 0;
    const deg = d.deg !== undefined ? `${String(d.deg).padStart(2,"0")}°${String(d.min||0).padStart(2,"0")}'` : "—";
    const retro = d.retrograde ? '<span class="kundali-retro">వ</span>' : "";
    planetRows += `<tr>
      <td>${PLANET_LABELS[name] || name}</td>
      <td>${RASHI_TE_LIST[ri] || ri}</td>
      <td>${deg}</td>
      <td>${retro}</td>
    </tr>`;
  }

  const bp = chart.birth_panchang || {};
  const dob = (profile.dob || "").split("-").reverse().join("/");

  const dashaHtml = _renderDashaAccordion(
    chart.vimshottari_dasha || [], profile.dob || "",
    chart.planet_rashis || {}, chart.lagna_idx ?? 0
  );

  body.innerHTML = `
    <div class="kundali-top">
      <div class="kundali-chart-wrap">${chartHtml}</div>
      <div class="kundali-planet-table-wrap">
        <table class="kundali-planet-table">
          <thead><tr><th>గ్రహం</th><th>రాశి</th><th>స్థానం</th><th></th></tr></thead>
          <tbody>${planetRows}</tbody>
        </table>
        <div style="font-size:0.7rem;color:var(--text-2);margin-top:4px">వ = వక్రి (retrograde)</div>
      </div>
    </div>
    <div class="kundali-birth-strip">
      <span><b>నక్షత్రం:</b> ${chart.janma_nakshatra_te || "—"}${chart.janma_nakshatra_padam ? " " + chart.janma_nakshatra_padam + "వ పాదం" : ""}</span>
      <span><b>రాశి:</b> ${chart.janma_rashi_te || "—"}</span>
      <span><b>లగ్నం:</b> ${chart.lagna_te || "—"}</span>
      <span><b>తిథి:</b> ${bp.tithi_te || "—"}</span>
      <span><b>వారం:</b> ${bp.vaara_te || "—"}</span>
      <span><b>యోగం:</b> ${bp.yoga_te || "—"}</span>
      <span><b>కరణం:</b> ${bp.karanam_te || "—"}</span>
    </div>
    <div class="kundali-dasha-header">వింశోత్తరి దశలు — 120 సంవత్సరాల పూర్ణ పట్టిక</div>
    ${dashaHtml}`;
}
```

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add full Kundali panel with natal chart and planet table"
```

---

## Task 6: Dasha Accordion + PDF Print

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Add `_renderDashaAccordion()` and helpers**

```javascript
function _renderDashaAccordion(dashas, birthDobIso, planetRashis, lagnaIdx) {
  const today = new Date().toISOString().slice(0, 10);

  return dashas.map((maha, i) => {
    const isCurrent = maha.start_date <= today && today <= maha.end_date;
    const currentCls = isCurrent ? " current" : "";
    const badge = isCurrent ? '<span class="dasha-current-badge">ప్రస్తుతం</span>' : "";
    const openCls = isCurrent ? " open" : "";

    // Find current antardasha
    const currentAdIdx = maha.antardashas.findIndex(
      a => a.start <= today && today <= a.end
    );

    const adRows = maha.antardashas.map((ad, j) => {
      const adCurrent = (isCurrent && j === currentAdIdx) ? " class=\"current-ad\"" : "";
      const startFmt = _fmtDate(ad.start);
      const endFmt   = _fmtDate(ad.end);
      return `<tr${adCurrent}>
        <td>${maha.lord_emoji} ${maha.lord_te} – ${ad.lord_te}</td>
        <td>${startFmt}</td>
        <td>${endFmt}</td>
      </tr>`;
    }).join("");

    // Mini chart: same natal chart but dasha lord's rashi cell highlighted
    const mahaRashiIdx = (planetRashis || {})[maha.lord];
    const miniChart = _renderMiniDashaChart(planetRashis, lagnaIdx, mahaRashiIdx);

    return `
      <div class="dasha-row${currentCls}${openCls}" id="dashaRow${i}">
        <div class="dasha-row-header" onclick="toggleDashaRow(${i})">
          <span>${isCurrent ? "▼" : "▶"} ${maha.lord_emoji} ${maha.lord_te} మహాదశ</span>
          ${badge}
          <span class="dasha-row-dates">${_fmtDate(maha.start_date)} – ${_fmtDate(maha.end_date)}</span>
        </div>
        <div class="dasha-row-body">
          <div class="dasha-mini-chart">${miniChart}</div>
          <table class="dasha-ad-table">
            <thead><tr><th>అంతర్దశ</th><th>ప్రారంభం</th><th>ముగింపు</th></tr></thead>
            <tbody>${adRows}</tbody>
          </table>
        </div>
      </div>`;
  }).join("");
}

function toggleDashaRow(idx) {
  const row = document.getElementById("dashaRow" + idx);
  if (!row) return;
  const isOpen = row.classList.contains("open");
  row.classList.toggle("open", !isOpen);
  const arrow = row.querySelector(".dasha-row-header > span:first-child");
  if (arrow) arrow.textContent = arrow.textContent.replace(isOpen ? "▼" : "▶", isOpen ? "▶" : "▼");
}

function _renderMiniDashaChart(planetRashis, lagnaIdx, highlightRashiIdx) {
  // Build a compact 4×4 chart identical to renderHoroscopeChart but smaller,
  // with the dasha lord's rashi cell highlighted gold.
  if (!planetRashis) return "";
  const RASHI_TE_SHORT = ["మే","వృ","మి","క","సి","క","తు","వృశ్చి","ధ","మక","కుం","మీ"];
  const PLANET_TE_MAP = {
    ravi:"ర",chandra:"చ",kuja:"కు",budha:"బు",guru:"గు",shukra:"శు",shani:"శ",rahu:"రా",ketu:"కే"
  };
  const RASHI_POS_4X4 = [
    [0,1],[0,2],[0,3],[1,3],[2,3],[3,3],[3,2],[3,1],[3,0],[2,0],[1,0],[0,0]
  ];

  const cells = Array.from({length: 12}, () => []);
  for (const [p, ri] of Object.entries(planetRashis)) {
    if (ri >= 0 && ri < 12) cells[ri].push(PLANET_TE_MAP[p] || p);
  }
  const grid = Array.from({length: 4}, () => Array(4).fill(null));
  for (let ri = 0; ri < 12; ri++) {
    const [r, c] = RASHI_POS_4X4[ri];
    grid[r][c] = { ri, planets: cells[ri], isLagna: ri === lagnaIdx };
  }
  let rows = "";
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const cell = grid[r][c];
      if (!cell) {
        rows += `<div class="horo-cell horo-center"></div>`;
      } else {
        const highlight = cell.ri === highlightRashiIdx
          ? "background:#ffd700;border-color:#f5c842;" : "";
        const cls = cell.isLagna ? "horo-cell horo-lagna" : "horo-cell";
        rows += `<div class="${cls}" style="${highlight}">
          <div class="horo-rashi" style="font-size:0.55rem">${RASHI_TE_SHORT[cell.ri]}</div>
          <div class="horo-planets" style="font-size:0.62rem">${cell.planets.join(" ")}</div>
          ${cell.isLagna ? '<span class="horo-lagna-mark">ల</span>' : ""}
        </div>`;
      }
    }
  }
  return `<div class="horo-wrap"><div class="horo-grid" style="width:80px;height:80px">${rows}</div></div>`;
}

function _fmtDate(iso) {
  if (!iso || !iso.includes("-")) return iso || "";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function printKundaliPage() {
  document.body.classList.add("kundali-printing");
  // Expand all dasha rows for print
  document.querySelectorAll(".dasha-row").forEach(r => r.classList.add("open"));
  window.print();
  document.body.classList.remove("kundali-printing");
  // Collapse rows that were not originally open (re-render to restore state)
  document.querySelectorAll(".dasha-row:not(.current)").forEach(r => r.classList.remove("open"));
}
```

- [ ] **Step 2: Smoke test the full Kundali flow**

1. Open the app and go to the People tab
2. Add a person (e.g. Name: "Test", DOB: 15/08/1990, Time: 10:30, Place: Rajahmundry)
3. Click "🪐 పూర్ణ కుండలి చూడండి"
4. Verify:
   - Natal chart renders (4×4 grid)
   - Planet table shows 9 planets with degrees (e.g. `23°14'`)
   - Birth panchang strip shows tithi, vaara, nakshatra, yoga, karanam
   - Dasha accordion shows 9 rows
   - Current mahadasha is highlighted gold and auto-expanded
   - Expanding a row shows mini chart (dasha lord's cell gold) + antardasha table with dates
5. Click "📄 PDF ఎగుమతి" — browser print dialog opens; all rows are expanded

- [ ] **Step 3: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add dasha accordion, mini charts, and PDF export to Kundali panel"
```

---

## Task 7: Deploy + Smoke Test

- [ ] **Step 1: Run the full test suite**

```bash
cd /path/to/repo/panchang-api && python -m pytest tests/test_muhoortam.py tests/test_dasha.py -v 2>&1 | tail -20
```

Expected: all tests PASS (the 9 pre-existing failures in other test files are pre-existing, not regressions).

- [ ] **Step 2: Push to master to trigger deploy**

```bash
cd /path/to/repo && git push origin master
```

- [ ] **Step 3: Verify GitHub Actions complete**

```bash
curl -s "https://api.github.com/repos/sairamchinta1510/telugu-panchang/actions/runs?per_page=3" \
  | python3 -c "import json,sys; [print(r['name'],'|',r['status'],'|',r.get('conclusion','')) for r in json.load(sys.stdin)['workflow_runs']]"
```

Expected: `Deploy Panchang API | completed | success` and `pages build and deployment | completed | success`.

- [ ] **Step 4: Production smoke test**

```bash
curl -s -X POST \
  "https://h3dp7amvn9.execute-api.ap-south-1.amazonaws.com/muhoortam/birth-chart" \
  -H "Content-Type: application/json" \
  -d '{"dob":"15/08/1990","time":"10:30","place":"Rajahmundry"}' \
  | python3 -c "
import json,sys
r = json.load(sys.stdin)
print('planet_details keys:', list(r.get('planet_details',{}).keys()))
print('vimshottari_dasha length:', len(r.get('vimshottari_dasha',[])))
print('first maha lord:', r['vimshottari_dasha'][0]['lord'] if r.get('vimshottari_dasha') else 'MISSING')
print('first maha antardashas:', len(r['vimshottari_dasha'][0].get('antardashas',[])) if r.get('vimshottari_dasha') else 0)
"
```

Expected output:
```
planet_details keys: ['ravi', 'chandra', 'kuja', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']
vimshottari_dasha length: 9
first maha lord: chandra
first maha antardashas: 9
```

- [ ] **Step 5: Hard-refresh the app and verify end-to-end**

1. Go to `https://sairamchinta1510.github.io/telugu-panchang/muhoortam/`
2. Hard refresh (`Cmd+Shift+R` / `Ctrl+Shift+R`)
3. Click "👥 జనాలు" tab — People panel shows
4. Add a new person with DOB + birthplace
5. Click "🪐 పూర్ణ కుండలి చూడండి" — full Kundali loads with planet degrees and dasha accordion
6. Click "📄 PDF ఎగుమతి" — print dialog opens
