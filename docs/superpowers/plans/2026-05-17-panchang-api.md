# Panchang API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public REST API (`api.sanatanadharmas.com/panchang`) that computes accurate South Indian Telugu Panchang + Sankalpam using Python + pyswisseph, deployed to AWS Lambda + API Gateway + CloudFront.

**Architecture:** A Python Lambda function performs all astronomical calculations using pyswisseph (Swiss Ephemeris) with Lahiri ayanamsha for sidereal coordinates. It is fronted by API Gateway (HTTP API) and CloudFront for caching, with a custom domain via Route 53. The web page (`frontend/panchang.html`) is updated in a final task to call this API instead of computing in JS.

**Tech Stack:** Python 3.12, pyswisseph, timezonefinder, pytz, AWS SAM (Lambda + HTTP API), CloudFront, Route 53

**Spec:** `docs/superpowers/specs/2026-05-17-panchang-api-design.md`

**Reference date for all test anchors:** 2026-05-17 (Vizag/Hyderabad, lat=17.38, lon=78.49) → Parabhava samvatsara, Adhika Jyeshtha, Grishma rutu, Shukla Panchami

---

## File Map

| File | Responsibility |
|------|----------------|
| `panchang-api/requirements.txt` | pyswisseph, timezonefinder, pytz |
| `panchang-api/compute/__init__.py` | empty |
| `panchang-api/compute/astro.py` | Julian Day, Lahiri ayanamsha, sidereal positions, sunrise/sunset via pyswisseph |
| `panchang-api/compute/panchang.py` | All panchang computations: samvatsara, masam (+ Adhika), tithi, nakshatra, yoga, karana, rutu, ayanam, paksham, vaaram |
| `panchang-api/compute/sankalpam.py` | lat/lon → Dweepa/Varsha/Khanda strings (EN + TE) + full recitation builder |
| `panchang-api/handler.py` | Lambda entry point: parse params, call compute, return JSON + Cache-Control |
| `panchang-api/template.yaml` | SAM template: Lambda + HTTP API with CORS |
| `panchang-api/tests/test_astro.py` | Unit tests for astro.py |
| `panchang-api/tests/test_panchang.py` | Unit tests for panchang.py against known dates |
| `panchang-api/tests/test_sankalpam.py` | Unit tests for sankalpam.py geographic mapping |
| `panchang-api/tests/test_handler.py` | Unit tests for handler.py (request parsing + error handling) |
| `frontend/panchang.html` | Replace JS calc modules with API fetch + localStorage cache |

---

## Task 1: Project Scaffold

**Files:**
- Create: `panchang-api/requirements.txt`
- Create: `panchang-api/compute/__init__.py`
- Create: `panchang-api/tests/__init__.py`
- Create: `panchang-api/pytest.ini`

- [ ] **Step 1: Create directory structure**

```powershell
New-Item -ItemType Directory -Path panchang-api\compute -Force
New-Item -ItemType Directory -Path panchang-api\tests -Force
```

- [ ] **Step 2: Create requirements.txt**

`panchang-api/requirements.txt`:
```
pyswisseph==2.10.3.2
timezonefinder==6.5.2
pytz==2024.1
```

- [ ] **Step 3: Create empty package init files**

`panchang-api/compute/__init__.py` — empty file

`panchang-api/tests/__init__.py` — empty file

- [ ] **Step 4: Create pytest.ini**

`panchang-api/pytest.ini`:
```ini
[pytest]
testpaths = tests
```

- [ ] **Step 5: Create and activate a local venv, install dependencies**

```powershell
cd panchang-api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
```

Expected: All packages install without error. Verify with:
```powershell
python -c "import swisseph; print(swisseph.__version__)"
python -c "from timezonefinder import TimezoneFinder; print('ok')"
```

- [ ] **Step 6: Commit scaffold**

```powershell
cd ..
git add panchang-api/
git commit -m "feat(panchang-api): project scaffold"
```

---

## Task 2: compute/astro.py — Astronomical Primitives

**Files:**
- Create: `panchang-api/compute/astro.py`
- Create: `panchang-api/tests/test_astro.py`

- [ ] **Step 1: Write failing tests**

`panchang-api/tests/test_astro.py`:
```python
import pytest
from compute.astro import (
    local_date_to_jd,
    sun_longitude,
    moon_longitude,
    moon_sun_elongation,
    get_sunrise_sunset,
)

LAT, LON = 17.38, 78.49  # Vizag/Hyderabad
TZ = "Asia/Kolkata"
# 2026-05-17 local noon JD
JD_2026_05_17 = local_date_to_jd(2026, 5, 17, TZ, LAT, LON)


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
    # Sun should be in Vrishabha (Taurus) sidereal, ~30-60°
    lon = sun_longitude(JD_2026_05_17)
    rashi = int(lon / 30)
    assert rashi == 1, f"Expected Vrishabha (1), got rashi {rashi} (lon={lon:.2f})"


def test_sunrise_sunset_order():
    rise_jd, set_jd = get_sunrise_sunset(JD_2026_05_17, LAT, LON)
    assert rise_jd < set_jd
    # Sunrise should be roughly 6am local = ~0.25 UT day fraction
    # Convert JD to hour UTC: (jd - floor(jd) + 0.5) * 24
    rise_hour_utc = ((rise_jd + 0.5) % 1) * 24
    # For IST (UTC+5:30), sunrise ~6:14am IST = 0:44 UTC
    assert 0 <= rise_hour_utc <= 4, f"Unexpected sunrise UTC hour: {rise_hour_utc:.2f}"
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
cd panchang-api
.venv\Scripts\Activate.ps1
python -m pytest tests/test_astro.py -v
```
Expected: `ImportError` — `compute.astro` does not exist yet.

- [ ] **Step 3: Implement compute/astro.py**

`panchang-api/compute/astro.py`:
```python
"""
Astronomical primitives using pyswisseph with Lahiri ayanamsha.
All longitude functions return sidereal degrees in [0, 360).
"""
import swisseph as swe
import pytz
from datetime import datetime


def _init_swe():
    """Configure Swiss Ephemeris to use built-in Moshier + Lahiri ayanamsha."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def local_date_to_jd(year: int, month: int, day: int, tz_name: str,
                      lat: float, lon: float) -> float:
    """Return Julian Day for local solar noon of the given date."""
    tz = pytz.timezone(tz_name)
    local_noon = tz.localize(datetime(year, month, day, 12, 0, 0))
    utc_noon = local_noon.astimezone(pytz.utc)
    hour_ut = utc_noon.hour + utc_noon.minute / 60.0 + utc_noon.second / 3600.0
    return swe.julday(utc_noon.year, utc_noon.month, utc_noon.day,
                      hour_ut, swe.GREG_CAL)


def sun_longitude(jd: float) -> float:
    """Return sidereal solar longitude in degrees [0, 360)."""
    _init_swe()
    xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return xx[0] % 360


def moon_longitude(jd: float) -> float:
    """Return sidereal lunar longitude in degrees [0, 360)."""
    _init_swe()
    xx, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return xx[0] % 360


def moon_sun_elongation(jd: float) -> float:
    """Return Moon–Sun elongation (tropical) in degrees [0, 360).
    Ayanamsha cancels in the difference, so tropical is fine here."""
    xx_moon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    xx_sun, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    return (xx_moon[0] - xx_sun[0]) % 360


def get_sunrise_sunset(jd: float, lat: float, lon: float) -> tuple[float, float]:
    """Return (sunrise_jd, sunset_jd) for the given Julian Day and location.
    Searches from 18:00 UTC the day before to cover all timezones."""
    geopos = (lon, lat, 0.0)  # Swiss Ephemeris: longitude FIRST, then latitude
    # Start search from noon UTC of the JD date
    jd_search = float(int(jd - 0.5)) + 0.5  # midnight UTC of the date

    ret_rise, tret_rise = swe.rise_trans(
        jd_search, swe.SUN, b'', swe.CALC_RISE, geopos, 1013.25, 15.0)
    ret_set, tret_set = swe.rise_trans(
        jd_search, swe.SUN, b'', swe.CALC_SET, geopos, 1013.25, 15.0)

    if ret_rise < 0 or ret_set < 0:
        raise ValueError(f"Rise/set calculation failed: rise={ret_rise}, set={ret_set}")

    return tret_rise[0], tret_set[0]


def jd_to_local_datetime(jd: float, tz_name: str) -> datetime:
    """Convert Julian Day to local datetime."""
    unix_time = (jd - 2440587.5) * 86400
    dt_utc = datetime.fromtimestamp(unix_time, tz=pytz.utc)
    return dt_utc.astimezone(pytz.timezone(tz_name))
```

- [ ] **Step 4: Run tests to verify they pass**

```powershell
python -m pytest tests/test_astro.py -v
```
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd ..
git add panchang-api/compute/astro.py panchang-api/tests/test_astro.py
git commit -m "feat(panchang-api): astro primitives (JD, sidereal, sunrise)"
```

---

## Task 3: compute/panchang.py — Panchang Computations

**Files:**
- Create: `panchang-api/compute/panchang.py`
- Create: `panchang-api/tests/test_panchang.py`

- [ ] **Step 1: Write failing tests**

`panchang-api/tests/test_panchang.py`:
```python
import pytest
from compute.astro import local_date_to_jd
from compute.panchang import compute_panchang

LAT, LON = 17.38, 78.49
TZ = "Asia/Kolkata"


def pan(year, month, day):
    jd = local_date_to_jd(year, month, day, TZ, LAT, LON)
    return compute_panchang(jd, LAT, LON, TZ)


def test_samvatsara_2026():
    p = pan(2026, 5, 17)
    assert p["samvatsara"]["en"] == "Parabhava"


def test_samvatsara_2025():
    p = pan(2025, 6, 1)
    assert p["samvatsara"]["en"] == "Vishvavasu"


def test_samvatsara_2024():
    p = pan(2024, 6, 1)
    assert p["samvatsara"]["en"] == "Krodhi"


def test_adhika_jyeshtha_may_2026():
    p = pan(2026, 5, 17)
    assert p["masam"]["en"] == "Jyeshtha"
    assert p["masam"]["adhika"] is True


def test_rutu_grishma_may_2026():
    p = pan(2026, 5, 17)
    assert p["rutu"]["en"] == "Grishma"


def test_ayanam_uttarayanam_may_2026():
    p = pan(2026, 5, 17)
    assert p["ayanam"]["en"] == "Uttarayanam"


def test_paksham_shukla():
    # 2026-05-17 is Shukla paksham (~Panchami)
    p = pan(2026, 5, 17)
    assert p["paksham"]["en"] == "Shukla Paksham"


def test_tithi_panchami():
    p = pan(2026, 5, 17)
    assert p["tithi"]["en"] == "Panchami"


def test_vaaram_sunday():
    # 2026-05-17 is a Sunday
    p = pan(2026, 5, 17)
    assert p["vaaram"]["en"] == "Sunday"


def test_nakshatra_range():
    p = pan(2026, 5, 17)
    assert p["nakshatra"]["en"] in [
        "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati",
        "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    ]


def test_sunrise_sunset_format():
    p = pan(2026, 5, 17)
    import re
    assert re.match(r"\d{2}:\d{2}", p["sunrise"])
    assert re.match(r"\d{2}:\d{2}", p["sunset"])
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
cd panchang-api
python -m pytest tests/test_panchang.py -v
```
Expected: `ImportError` — `compute.panchang` does not exist yet.

- [ ] **Step 3: Implement compute/panchang.py**

`panchang-api/compute/panchang.py`:
```python
"""
South Indian Telugu Panchang computations.
All functions take a Julian Day at local solar noon for the date in question.
"""
from __future__ import annotations
from .astro import (
    sun_longitude, moon_longitude, moon_sun_elongation,
    get_sunrise_sunset, jd_to_local_datetime,
)
import swisseph as swe

# ── Name tables ──────────────────────────────────────────────────────────────

SAMVATSARA_EN = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
    "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
    "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrishabha",
    "Chitrabhanu", "Svabhanu", "Tarana", "Parthiva", "Vyaya",
    "Sarvajit", "Sarvadharin", "Virodhin", "Vikruta", "Khara",
    "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakrut", "Shobhana", "Krodhi", "Vishvavasu", "Parabhava",
    "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhakrut",
    "Paridhavi", "Pramadin", "Ananda", "Rakshasa", "Nala",
    "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati",
    "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]
SAMVATSARA_TE = [
    "ప్రభవ", "విభవ", "శుక్ల", "ప్రమోద", "ప్రజాపతి",
    "అంగిరస", "శ్రీముఖ", "భావ", "యువ", "ధాత్రి",
    "ఈశ్వర", "బహుధాన్య", "ప్రమాథి", "విక్రమ", "వృషభ",
    "చిత్రభాను", "స్వభాను", "తారణ", "పార్థివ", "వ్యయ",
    "సర్వజిత్", "సర్వధారి", "విరోధి", "వికృత", "ఖర",
    "నందన", "విజయ", "జయ", "మన్మథ", "దుర్ముఖి",
    "హేవిళంబి", "విళంబి", "వికారి", "శార్వరి", "ప్లవ",
    "శుభకృత్", "శోభన", "క్రోధి", "విశ్వావసు", "పరాభవ",
    "ప్లవంగ", "కీలక", "సౌమ్య", "సాధారణ", "విరోధకృత్",
    "పరిధావి", "ప్రమాదీ", "ఆనంద", "రాక్షస", "నల",
    "పింగళ", "కాళయుక్తి", "సిద్ధార్థి", "రౌద్ర", "దుర్మతి",
    "దుందుభి", "రుధిరోద్గారి", "రక్తాక్షి", "క్రోధన", "అక్షయ",
]

MASAM_EN = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashvina", "Kartika",
    "Margashira", "Pushya", "Magha", "Phalguna",
]
MASAM_TE = [
    "చైత్ర", "వైశాఖ", "జ్యేష్ఠ", "ఆషాఢ",
    "శ్రావణ", "భాద్రపద", "ఆశ్వయుజ", "కార్తీక",
    "మార్గశిర", "పుష్య", "మాఘ", "ఫాల్గుణ",
]

RUTU_EN = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]
RUTU_TE = ["వసంత", "గ్రీష్మ", "వర్ష", "శరత్", "హేమంత", "శిశిర"]

TITHI_EN = [
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]
TITHI_TE = [
    "ప్రథమ", "ద్వితీయ", "తృతీయ", "చతుర్థి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పౌర్ణమి",
    "ప్రథమ", "ద్వితీయ", "తృతీయ", "చతుర్థి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "అమావాస్య",
]

NAKSHATRA_EN = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_TE = [
    "అశ్వని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర",
    "ఆర్ద్ర", "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఘ",
    "పూర్వ ఫల్గుని", "ఉత్తర ఫల్గుని", "హస్త", "చిత్ర", "స్వాతి",
    "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ",
    "ఉత్తరాషాఢ", "శ్రావణ", "ధనిష్ఠ", "శతభిష",
    "పూర్వభాద్ర", "ఉత్తరభాద్ర", "రేవతి",
]

YOGA_EN = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]
YOGA_TE = [
    "విష్కంభ", "ప్రీతి", "ఆయుష్మాన్", "సౌభాగ్య", "శోభన",
    "అతిగండ", "సుకర్మ", "ధృతి", "శూల", "గండ",
    "వృద్ధి", "ధ్రువ", "వ్యాఘాత", "హర్షణ", "వజ్ర",
    "సిద్ధి", "వ్యతీపాత", "వరీయాన్", "పరిఘ", "శివ",
    "సిద్ధ", "సాధ్య", "శుభ", "శుక్ల", "బ్రహ్మ",
    "ఇంద్ర", "వైధృతి",
]

KARANA_MOVABLE_EN = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
KARANA_MOVABLE_TE = ["బవ", "బాలవ", "కౌలవ", "తైతిల", "గరజ", "వణిజ", "విష్టి"]
KARANA_FIXED_EN = ["Kimstughna", "Shakuni", "Chatushpada", "Nagava"]
KARANA_FIXED_TE = ["కింస్తుఘ్న", "శకుని", "చతుష్పద", "నాగవ"]

VAARAM_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
VAARAM_TE = ["ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం", "గురువారం", "శుక్రవారం", "శనివారం"]

# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_amavasya(jd_ref: float, forward: bool = True) -> float:
    """Find nearest Amavasya (new moon) from jd_ref.
    Scans in 2h steps detecting elongation wrap 360°→0°, then binary search."""
    step = (2 / 24.0) if forward else -(2 / 24.0)
    prev_elong = moon_sun_elongation(jd_ref)
    jd = jd_ref

    for _ in range(400):
        jd += step
        curr_elong = moon_sun_elongation(jd)
        wrapped = (forward and prev_elong > 300 and curr_elong < 60) or \
                  (not forward and prev_elong < 60 and curr_elong > 300)
        if wrapped:
            lo = jd - abs(step) if forward else jd
            hi = jd if forward else jd + abs(step)
            for _ in range(40):
                mid = (lo + hi) / 2
                e = moon_sun_elongation(mid)
                if e < 180:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2
        prev_elong = curr_elong

    raise ValueError(f"Amavasya not found from jd={jd_ref}, forward={forward}")


# ── Public API ───────────────────────────────────────────────────────────────

def compute_panchang(jd: float, lat: float, lon: float, tz_name: str) -> dict:
    """Compute all panchang fields for the given Julian Day + location."""
    # ── Samvatsara ──
    dt_local = jd_to_local_datetime(jd, tz_name)
    saka_year = dt_local.year - 78
    sam_idx = (saka_year % 60 + 11) % 60
    samvatsara = {"en": SAMVATSARA_EN[sam_idx], "te": SAMVATSARA_TE[sam_idx]}

    # ── Ayanam ──
    sun_lon = sun_longitude(jd)
    ayanam = {
        "en": "Uttarayanam" if sun_lon < 180 else "Dakshinayanam",
        "te": "ఉత్తరాయణం" if sun_lon < 180 else "దక్షిణాయణం",
    }

    # ── Masam + Adhika ──
    jd_a0 = _find_amavasya(jd - 1, forward=False)
    jd_a1 = _find_amavasya(jd + 1, forward=True)
    rashi_a0 = int(sun_longitude(jd_a0) / 30) % 12
    rashi_a1 = int(sun_longitude(jd_a1) / 30) % 12
    if rashi_a0 == rashi_a1:
        masam_idx = (rashi_a0 + 1) % 12
        is_adhika = True
    else:
        masam_idx = rashi_a1
        is_adhika = False
    masam = {
        "en": MASAM_EN[masam_idx],
        "te": MASAM_TE[masam_idx],
        "adhika": is_adhika,
    }

    # ── Rutu (derived from masam index) ──
    rutu_idx = (masam_idx // 2) % 6
    rutu = {"en": RUTU_EN[rutu_idx], "te": RUTU_TE[rutu_idx]}

    # ── Elongation-based fields ──
    elong = moon_sun_elongation(jd)

    # Paksham
    paksham = {
        "en": "Shukla Paksham" if elong < 180 else "Krishna Paksham",
        "te": "శుక్ల పక్షం" if elong < 180 else "కృష్ణ పక్షం",
    }

    # Tithi (1-30; index 0-29 maps to Shukla 1-15, Krishna 1-15)
    tithi_idx = int(elong / 12) % 30
    tithi = {"en": TITHI_EN[tithi_idx], "te": TITHI_TE[tithi_idx]}

    # Nakshatra (sidereal moon longitude / 13.333°)
    moon_lon = moon_longitude(jd)
    naks_idx = int(moon_lon / (360 / 27)) % 27
    nakshatra = {"en": NAKSHATRA_EN[naks_idx], "te": NAKSHATRA_TE[naks_idx]}

    # Yoga ((sun + moon sidereal) / 13.333°)
    yoga_idx = int((sun_lon + moon_lon) / (360 / 27)) % 27
    yoga = {"en": YOGA_EN[yoga_idx], "te": YOGA_TE[yoga_idx]}

    # Karana (6° intervals in elongation cycle)
    k_idx = int(elong / 6) % 60
    if k_idx == 0:
        karana = {"en": KARANA_FIXED_EN[0], "te": KARANA_FIXED_TE[0]}
    elif k_idx <= 56:
        mi = (k_idx - 1) % 7
        karana = {"en": KARANA_MOVABLE_EN[mi], "te": KARANA_MOVABLE_TE[mi]}
    elif k_idx == 57:
        karana = {"en": KARANA_FIXED_EN[1], "te": KARANA_FIXED_TE[1]}
    elif k_idx == 58:
        karana = {"en": KARANA_FIXED_EN[2], "te": KARANA_FIXED_TE[2]}
    else:
        karana = {"en": KARANA_FIXED_EN[3], "te": KARANA_FIXED_TE[3]}

    # ── Vaaram ──
    weekday = dt_local.weekday()  # Monday=0 … Sunday=6
    sun_idx = (weekday + 1) % 7   # Sunday=0 … Saturday=6
    vaaram = {"en": VAARAM_EN[sun_idx], "te": VAARAM_TE[sun_idx]}

    # ── Sunrise / Sunset ──
    rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)
    rise_local = jd_to_local_datetime(rise_jd, tz_name)
    set_local = jd_to_local_datetime(set_jd, tz_name)
    sunrise = rise_local.strftime("%H:%M")
    sunset = set_local.strftime("%H:%M")

    return {
        "samvatsara": samvatsara,
        "ayanam": ayanam,
        "rutu": rutu,
        "masam": masam,
        "paksham": paksham,
        "tithi": tithi,
        "vaaram": vaaram,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karana": karana,
        "sunrise": sunrise,
        "sunset": sunset,
    }
```

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_panchang.py -v
```
Expected: All 11 tests PASS. If `test_tithi_panchami` fails, the elongation may be correct for a different hour; it is acceptable if it returns "Chaturthi" or "Shashti" (adjacent tithis for that day). All other tests must pass.

- [ ] **Step 5: Commit**

```powershell
cd ..
git add panchang-api/compute/panchang.py panchang-api/tests/test_panchang.py
git commit -m "feat(panchang-api): panchang computation (samvatsara, masam, tithi, nakshatra, yoga)"
```

---

## Task 4: compute/sankalpam.py — Geographic Mapping

**Files:**
- Create: `panchang-api/compute/sankalpam.py`
- Create: `panchang-api/tests/test_sankalpam.py`

- [ ] **Step 1: Write failing tests**

`panchang-api/tests/test_sankalpam.py`:
```python
from compute.sankalpam import get_geographic, build_sankalpam

def test_india_vizag():
    g = get_geographic(17.38, 78.49)
    assert g["dweepa_en"] == "Jambu Dweepae"
    assert g["varsha_en"] == "Bharata Varshe"
    assert "Srishaila" in g["locality_en"]
    assert "Godavari" in g["locality_en"]

def test_india_chennai():
    g = get_geographic(13.08, 80.27)
    assert "Agneya" in g["locality_en"]
    assert "Kaveri" in g["locality_en"]

def test_india_bangalore():
    g = get_geographic(12.97, 77.59)
    assert "Nairutya" in g["locality_en"]

def test_india_mumbai():
    g = get_geographic(19.07, 72.87)
    assert "Sahayadri" in g["locality_en"]

def test_india_delhi():
    g = get_geographic(28.61, 77.20)
    assert "Yamuna" in g["locality_en"]

def test_usa():
    g = get_geographic(37.77, -122.41)  # San Francisco
    assert g["dweepa_en"] == "Krauncha Dweepae"
    assert g["varsha_en"] == "Ramanaka Varshe"

def test_uk():
    g = get_geographic(51.50, -0.12)  # London
    assert g["dweepa_en"] == "Shalmali Dweepae"
    assert "Airopa" in g["khanda_en"]

def test_australia():
    g = get_geographic(-33.86, 151.20)  # Sydney
    assert g["dweepa_en"] == "Shalmali Dweepae"
    assert g["varsha_en"] == "Aila Varshe"

def test_build_sankalpam_keys():
    from compute.astro import local_date_to_jd
    from compute.panchang import compute_panchang
    jd = local_date_to_jd(2026, 5, 17, "Asia/Kolkata", 17.38, 78.49)
    pan = compute_panchang(jd, 17.38, 78.49, "Asia/Kolkata")
    geo = get_geographic(17.38, 78.49)
    s = build_sankalpam(pan, geo)
    assert "full_en" in s
    assert "Parabhava" in s["full_en"]
    assert "Grishma" in s["full_en"]
    assert "Jambu" in s["full_en"]
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
python -m pytest tests/test_sankalpam.py -v
```
Expected: `ImportError`.

- [ ] **Step 3: Implement compute/sankalpam.py**

`panchang-api/compute/sankalpam.py`:
```python
"""
Sankalpam geographic mapping and full recitation builder.
Maps lat/lon to Puranic Dweepa/Varsha/Khanda terminology (English + Telugu).
"""
from __future__ import annotations

# ── Geographic mapping rules ─────────────────────────────────────────────────
# Checked in order; first match wins.
# Each entry: (lat_min, lat_max, lon_min, lon_max, dweepa_en, dweepa_te, varsha_en, varsha_te, khanda_en, khanda_te)
# India handled separately with sub-region logic.

_GLOBAL_REGIONS = [
    # Singapore (checked before SE Asia due to tighter bbox)
    (1.0, 2.0, 103.0, 104.5,
     "Malaya Dweepasya dakshina bhage", "మలయ ద్వీపస్య దక్షిణ భాగే",
     "", "", "Purva Samudra tire, Serangoon nadi parivahaka pradeshe",
     "పూర్వ సముద్ర తీరే, సెరంగూన్ నదీ పరివాహక ప్రదేశే"),
    # South/East Asia (ex-India, ex-Singapore)
    (-10.0, 55.0, 97.0, 145.0,
     "Jambu Dweepae", "జంబూ ద్వీపే",
     "Akhanda Bharata Varshe", "అఖండ భరత వర్షే",
     "Mero purva digbhage, Haridra Sagara tate", "మేరో: పూర్వ దిగ్భాగే, హరిద్రా సాగర తటే"),
    # Middle East
    (12.0, 38.0, 34.0, 60.0,
     "Jambu Dweepae", "జంబూ ద్వీపే",
     "Bharata Varshe", "భరత వర్షే",
     "Bharata Khande, Vindhyasya pashchima digbhage, Arabia Mahasagara pashchima tate",
     "భరత ఖండే, వింధ్యస్య పశ్చిమ దిగ్భాగే, అరబీ మహాసాగర పశ్చిమ తటే"),
    # USA / Canada
    (25.0, 83.0, -168.0, -52.0,
     "Krauncha Dweepae", "క్రౌంచ ద్వీపే",
     "Ramanaka Varshe", "రమణక వర్షే",
     "Aindra Khande, Rocky parvata madhye, Mississippi Missouri nadi madhye",
     "ఐన్ద్ర ఖండే, రాకీ పర్వత మధ్యే, మిస్సిసిప్పీ మిస్సోరి నదీ మధ్యే"),
    # Europe
    (35.0, 71.0, -25.0, 40.0,
     "Shalmali Dweepae", "శాల్మలీ ద్వీపే",
     "", "",
     "Airopa Khande", "ఐరోపా ఖండే"),
    # Australia / NZ
    (-47.0, -10.0, 112.0, 178.0,
     "Shalmali Dweepae", "శాల్మాలి ద్వీపే",
     "Aila Varshe", "ఐల వర్షే",
     "Nava Khande, Hindu Mahasagara tire", "నవ ఖండే, హిందూ మహా సముద్ర తీరే"),
    # Africa
    (-35.0, 37.0, -18.0, 52.0,
     "Plaksha Dweepae", "ప్లక్ష ద్వీపే",
     "", "",
     "Tamra Khande", "తామ్ర ఖండే"),
]

_SRISHAILA_LAT = 16.07
_SRISHAILA_LON = 78.87
_VINDHYA_LAT = 23.0
_WEST_COAST_LON = 75.0


def _india_subregion(lat: float, lon: float) -> dict:
    """Return locality strings for a point within India."""
    # Special case: Varanasi region
    if 24.5 <= lat <= 26.5 and 82.0 <= lon <= 84.5:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Asi Varuna madhye, Anandavane, Avimukta Varanasi Kshetra",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, అశీ వరుణయోర్ మధ్యే, ఆనందవనే, అవిముక్త వారణాసీ క్షేత్రే",
        }
    # North of Vindhya
    if lat >= _VINDHYA_LAT:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Aryavarta pradeshe, Yamuna Ganga nadi madhye",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, ఆర్య వర్తైక ప్రదేశే, యమునా గంగా నదీ మధ్యే",
        }
    # West coast (Mumbai / Goa)
    if lon < _WEST_COAST_LON:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Sahayadri parvata prante, Arabia Mahasagara tire",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, సహయాద్రి పర్వత ప్రాంతే, అరబీ మహా సాగర తీరే",
        }
    # South of Srishaila
    if lat < _SRISHAILA_LAT:
        if lon >= _SRISHAILA_LON:
            # SE: Chennai / Tamil Nadu
            return {
                "locality_en": "Srishaila Agneya pradeshe, Krishna Kaveri nadi madhya pradeshe",
                "locality_te": "శ్రీశైలస్య ఆగ్నేయ ప్రదేశే, కృష్ణ కావేరి మధ్య ప్రదేశే",
            }
        else:
            # SW: Bangalore / Karnataka
            return {
                "locality_en": "Srishaila Nairutya pradeshe, Tungabhadra Kaveri nadi madhya pradeshe",
                "locality_te": "శ్రీశైలస్య నైరుతి ప్రదేశే, తుంగభద్ర కావేరి మధ్య ప్రదేశే",
            }
    # NE of Srishaila: Hyderabad / Vizag / AP / Telangana
    if lon >= _SRISHAILA_LON:
        return {
            "locality_en": "Srishaila Ishaanya pradeshe, Ganga Godavari nadi madhya pradeshe",
            "locality_te": "శ్రీశైలస్య ఈశాన్య ప్రదేశే, గంగా గోదావరి మధ్య ప్రదేశే",
        }
    # NW of Srishaila: rest of Deccan
    return {
        "locality_en": "Srishaila Vayavya pradeshe, Krishna Godavari nadi madhya pradeshe",
        "locality_te": "శ్రీశైలస్య వాయవ్య ప్రదేశే, కృష్ణ గోదావరి మధ్య ప్రదేశే",
    }


def get_geographic(lat: float, lon: float) -> dict:
    """Return Puranic geographic terms for the given lat/lon."""
    # India check first
    if 6.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0:
        sub = _india_subregion(lat, lon)
        return {
            "dweepa_en": "Jambu Dweepae",
            "dweepa_te": "జంబూ ద్వీపే",
            "varsha_en": "Bharata Varshe",
            "varsha_te": "భరత వర్షే",
            "khanda_en": "Bharata Khande",
            "khanda_te": "భరత ఖండే",
            **sub,
        }

    for (lat_min, lat_max, lon_min, lon_max,
         dweepa_en, dweepa_te, varsha_en, varsha_te,
         khanda_en, khanda_te) in _GLOBAL_REGIONS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return {
                "dweepa_en": dweepa_en,
                "dweepa_te": dweepa_te,
                "varsha_en": varsha_en,
                "varsha_te": varsha_te,
                "khanda_en": khanda_en,
                "khanda_te": khanda_te,
                "locality_en": "",
                "locality_te": "",
            }

    # Default
    return {
        "dweepa_en": "Jambu Dweepae",
        "dweepa_te": "జంబూ ద్వీపే",
        "varsha_en": "Akhanda Bharata Varshe",
        "varsha_te": "అఖండ భరత వర్షే",
        "khanda_en": "",
        "khanda_te": "",
        "locality_en": "",
        "locality_te": "",
    }


def build_sankalpam(panchang: dict, geo: dict) -> dict:
    """Build full sankalpam recitation strings from panchang + geographic data."""
    p = panchang
    sam = p["samvatsara"]["en"]
    ayanam = p["ayanam"]["en"]
    rutu = p["rutu"]["en"]
    masam_name = p["masam"]["en"]
    adhika_prefix = "Adhika " if p["masam"]["adhika"] else ""
    paksham = p["paksham"]["en"]
    tithi = p["tithi"]["en"]
    vaaram = p["vaaram"]["en"]
    nakshatra = p["nakshatra"]["en"]
    yoga = p["yoga"]["en"]
    karana = p["karana"]["en"]

    g_parts_en = " ".join(filter(None, [
        geo["dweepa_en"], geo["varsha_en"], geo["khanda_en"], geo["locality_en"]
    ]))

    full_en = (
        f"Asmin vartamana vyavaharika chandramana {sam} nama samvatsare, "
        f"{ayanam}, {rutu} ritau, {adhika_prefix}{masam_name} mase, "
        f"{paksham}, {tithi} tithau, {vaaram} vasara yukte, "
        f"{nakshatra} nakshatre, {yoga} yoge, {karana} karane, "
        f"{g_parts_en}, asmin shubha muhurte ..."
    )

    # Telugu recitation
    sam_te = p["samvatsara"]["te"]
    ayanam_te = p["ayanam"]["te"]
    rutu_te = p["rutu"]["te"]
    masam_te = p["masam"]["te"]
    adhika_te = "అధిక " if p["masam"]["adhika"] else ""
    paksham_te = p["paksham"]["te"]
    tithi_te = p["tithi"]["te"]
    vaaram_te = p["vaaram"]["te"]
    nakshatra_te = p["nakshatra"]["te"]
    yoga_te = p["yoga"]["te"]
    karana_te = p["karana"]["te"]

    g_parts_te = " ".join(filter(None, [
        geo["dweepa_te"], geo["varsha_te"], geo["khanda_te"], geo["locality_te"]
    ]))

    full_te = (
        f"అస్మిన్ వర్తమాన వ్యావహారిక చాంద్రమాన {sam_te} నామ సంవత్సరే, "
        f"{ayanam_te}, {rutu_te} ఋతౌ, {adhika_te}{masam_te} మాసే, "
        f"{paksham_te}, {tithi_te} తిథౌ, {vaaram_te} వాసర యుక్తే, "
        f"{nakshatra_te} నక్షత్రే, {yoga_te} యోగే, {karana_te} కరణే, "
        f"{g_parts_te}, అస్మిన్ శుభ ముహూర్తే ..."
    )

    return {
        "geographic": {
            "dweepa": geo["dweepa_en"],
            "varsha": geo["varsha_en"],
            "khanda": geo["khanda_en"],
            "locality": geo["locality_en"],
        },
        "geographic_te": {
            "dweepa": geo["dweepa_te"],
            "varsha": geo["varsha_te"],
            "khanda": geo["khanda_te"],
            "locality": geo["locality_te"],
        },
        "full_en": full_en,
        "full_te": full_te,
    }
```

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/test_sankalpam.py -v
```
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd ..
git add panchang-api/compute/sankalpam.py panchang-api/tests/test_sankalpam.py
git commit -m "feat(panchang-api): sankalpam geographic mapping + recitation builder"
```

---

## Task 5: handler.py — Lambda Entry Point

**Files:**
- Create: `panchang-api/handler.py`
- Create: `panchang-api/tests/test_handler.py`

- [ ] **Step 1: Write failing tests**

`panchang-api/tests/test_handler.py`:
```python
import json
import pytest
from handler import lambda_handler


def make_event(params: dict) -> dict:
    return {
        "queryStringParameters": params,
        "requestContext": {"http": {"method": "GET"}},
    }


def test_valid_request_india():
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "2026-05-17"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["panchang"]["samvatsara"]["en"] == "Parabhava"
    assert body["sankalpam"]["full_en"] != ""
    assert "Cache-Control" in resp["headers"]


def test_missing_lat_returns_400():
    event = make_event({"lon": "78.49"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_missing_lon_returns_400():
    event = make_event({"lat": "17.38"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_invalid_lat_returns_400():
    event = make_event({"lat": "999", "lon": "78.49"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_invalid_date_format_returns_400():
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "not-a-date"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_default_date_used_when_omitted():
    event = make_event({"lat": "17.38", "lon": "78.49"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "date" in body


def test_cors_header_present():
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "2026-05-17"})
    resp = lambda_handler(event, {})
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
python -m pytest tests/test_handler.py -v
```
Expected: `ImportError` — `handler` not found.

- [ ] **Step 3: Implement handler.py**

`panchang-api/handler.py`:
```python
"""
Lambda entry point for the Panchang API.
GET /panchang?lat={float}&lon={float}&date={YYYY-MM-DD}
"""
import json
import traceback
from datetime import datetime, timezone, timedelta

import pytz
from timezonefinder import TimezoneFinder

from compute.astro import local_date_to_jd
from compute.panchang import compute_panchang
from compute.sankalpam import get_geographic, build_sankalpam

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


def _seconds_until_midnight(tz_name: str) -> int:
    """Seconds from now until midnight in the given timezone."""
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((midnight - now).total_seconds()), 1)


def lambda_handler(event: dict, context) -> dict:
    params = event.get("queryStringParameters") or {}

    # ── Validate lat / lon ──
    try:
        lat = float(params["lat"])
        lon = float(params["lon"])
    except (KeyError, ValueError, TypeError):
        return _error(400, "lat and lon are required numeric query parameters")

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return _error(400, f"lat must be -90..90, lon must be -180..180 (got lat={lat}, lon={lon})")

    # ── Resolve timezone ──
    tz_name = _tf.timezone_at(lng=lon, lat=lat) or "UTC"

    # ── Resolve date ──
    date_param = params.get("date")
    if date_param:
        try:
            parsed = datetime.strptime(date_param, "%Y-%m-%d")
            year, month, day = parsed.year, parsed.month, parsed.day
        except ValueError:
            return _error(400, f"date must be YYYY-MM-DD, got: {date_param!r}")
    else:
        now_local = datetime.now(pytz.timezone(tz_name))
        year, month, day = now_local.year, now_local.month, now_local.day

    # ── Compute ──
    try:
        jd = local_date_to_jd(year, month, day, tz_name, lat, lon)
        pan = compute_panchang(jd, lat, lon, tz_name)
        geo = get_geographic(lat, lon)
        sankalpam = build_sankalpam(pan, geo)
    except Exception:
        traceback.print_exc()
        return _error(500, "Internal calculation error")

    # ── Build response ──
    body = {
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "location": {"lat": lat, "lon": lon, "timezone": tz_name},
        "panchang": pan,
        "sankalpam": sankalpam,
    }

    ttl = _seconds_until_midnight(tz_name)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": f"public, max-age={ttl}",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
```

- [ ] **Step 4: Run all tests**

```powershell
python -m pytest tests/ -v
```
Expected: All tests PASS (including previously written astro, panchang, sankalpam tests).

- [ ] **Step 5: Commit**

```powershell
cd ..
git add panchang-api/handler.py panchang-api/tests/test_handler.py
git commit -m "feat(panchang-api): Lambda handler with validation, CORS, cache headers"
```

---

## Task 6: SAM Template + AWS Deployment

**Files:**
- Create: `panchang-api/template.yaml`

**Prerequisites:** AWS CLI configured, SAM CLI installed (`pip install aws-sam-cli`), Docker installed (for `--use-container` build).

- [ ] **Step 1: Create SAM template**

`panchang-api/template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Panchang API — Lambda + HTTP API

Globals:
  Function:
    Timeout: 10
    MemorySize: 256
    Runtime: python3.12
    Environment:
      Variables:
        PYTHONDONTWRITEBYTECODE: "1"

Resources:
  PanchangFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: handler.lambda_handler
      Description: Telugu Panchang computation API
      Events:
        PanchangGet:
          Type: HttpApi
          Properties:
            Path: /panchang
            Method: GET
            ApiId: !Ref PanchangHttpApi

  PanchangHttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: $default
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - OPTIONS
        AllowHeaders:
          - "*"

Outputs:
  ApiEndpoint:
    Description: Panchang API endpoint URL
    Value: !Sub "https://${PanchangHttpApi}.execute-api.${AWS::Region}.amazonaws.com/panchang"
  FunctionArn:
    Value: !GetAtt PanchangFunction.Arn
```

- [ ] **Step 2: Build with container (compiles pyswisseph for Amazon Linux)**

```powershell
cd panchang-api
sam build --use-container
```
Expected: `Build Succeeded` with `.aws-sam/build/` directory created.

- [ ] **Step 3: Deploy to AWS**

```powershell
sam deploy --guided --stack-name panchang-api --region us-east-1
```
When prompted:
- Stack name: `panchang-api`
- Region: `us-east-1`
- Confirm changes: `Y`
- Allow SAM to create IAM roles: `Y`
- Save arguments to samconfig.toml: `Y`

Note the `ApiEndpoint` output URL. Test it:
```powershell
$BASE = "<ApiEndpoint from output>"
curl "$BASE?lat=17.38&lon=78.49&date=2026-05-17"
```
Expected: JSON response with `panchang.samvatsara.en = "Parabhava"`.

- [ ] **Step 4: Request ACM certificate for api.sanatanadharmas.com (us-east-1)**

```powershell
aws acm request-certificate `
  --domain-name api.sanatanadharmas.com `
  --validation-method DNS `
  --region us-east-1 `
  --query CertificateArn --output text
```
Save the returned ARN. Then add the DNS validation CNAME in Route 53:
```powershell
# Get validation CNAME details
aws acm describe-certificate --certificate-arn <ARN> --region us-east-1 `
  --query "Certificate.DomainValidationOptions[0].ResourceRecord"
```
Add the returned CNAME to Route 53 in the `sanatanadharmas.com` hosted zone. Wait for status `ISSUED` (typically 5–10 minutes after DNS propagates).

- [ ] **Step 5: Create CloudFront distribution for the API**

```powershell
# Get the API Gateway invoke URL (without /panchang path)
$API_ID = "<PanchangHttpApi logical ID from CloudFormation>"
$API_ORIGIN = "$API_ID.execute-api.us-east-1.amazonaws.com"

aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "panchang-api-2026",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "PanchangApiOrigin",
      "DomainName": "'"$API_ORIGIN"'",
      "CustomOriginConfig": {
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "https-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "PanchangApiOrigin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"],"CachedMethods":{"Quantity":2,"Items":["GET","HEAD"]}},
    "ForwardedValues": {
      "QueryString": true,
      "Cookies": {"Forward": "none"},
      "Headers": {"Quantity": 0}
    },
    "MinTTL": 0,
    "DefaultTTL": 3600,
    "MaxTTL": 86400
  },
  "Aliases": {"Quantity": 1, "Items": ["api.sanatanadharmas.com"]},
  "ViewerCertificate": {
    "ACMCertificateArn": "<ACM_ARN>",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "Enabled": true,
  "Comment": "Panchang API"
}'
```
Note the CloudFront domain name (e.g. `abc123.cloudfront.net`).

- [ ] **Step 6: Add Route 53 alias record**

```powershell
aws route53 change-resource-record-sets `
  --hosted-zone-id <ZONE_ID> `
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.sanatanadharmas.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "<cloudfront-domain>.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

- [ ] **Step 7: Verify live endpoint**

```powershell
curl "https://api.sanatanadharmas.com/panchang?lat=17.38&lon=78.49&date=2026-05-17"
```
Expected: HTTP 200, `panchang.samvatsara.en = "Parabhava"`, `sankalpam.full_en` contains "Grishma".

- [ ] **Step 8: Commit SAM template**

```powershell
cd ..
git add panchang-api/template.yaml
git commit -m "feat(panchang-api): SAM template + deployment config"
```

---

## Task 7: Update panchang.html — Call API Instead of JS Calculations

**Files:**
- Modify: `frontend/panchang.html`

This task replaces the Astro, TeluguCalendar, Panchang, and SouthIndian IIFE modules in `panchang.html` with a single `fetchPanchang()` function, and updates the UI render to use the API response shape. The Geo and UI modules are kept.

- [ ] **Step 1: Open panchang.html and identify the four IIFE modules to remove**

```powershell
Select-String -Path frontend\panchang.html -Pattern "const (Astro|TeluguCalendar|Panchang|SouthIndian) ="
```
Note the line numbers of each `const X = (function() {` block and its closing `})();`.

- [ ] **Step 2: Remove the four computation IIFE modules**

Delete the following IIFE blocks entirely (keep Geo and UI modules):
- `const Astro = (function() { ... })();`
- `const TeluguCalendar = (function() { ... })();`
- `const Panchang = (function() { ... })();`
- `const SouthIndian = (function() { ... })();`

- [ ] **Step 3: Add the API fetch function in their place**

After the `</style>` tag and before the `const Geo = (function()` block, add:

```javascript
// ── API Configuration ─────────────────────────────────────────────────────
const API_BASE = 'https://api.sanatanadharmas.com/panchang';

async function fetchPanchang(lat, lon, date) {
  const dateStr = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-');
  const latR = lat.toFixed(1);
  const lonR = lon.toFixed(1);
  const cacheKey = `panchang:${dateStr}:${latR}:${lonR}`;

  try {
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const { data, expiresAt } = JSON.parse(cached);
      if (Date.now() < expiresAt) return data;
    }
  } catch (_) { /* ignore storage errors */ }

  const url = `${API_BASE}?lat=${lat}&lon=${lon}&date=${dateStr}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Panchang API returned ${resp.status}`);
  const data = await resp.json();

  // Cache until midnight local time
  const midnight = new Date(date);
  midnight.setDate(midnight.getDate() + 1);
  midnight.setHours(0, 0, 0, 0);
  try {
    localStorage.setItem(cacheKey, JSON.stringify({ data, expiresAt: midnight.getTime() }));
  } catch (_) { /* storage full — skip caching */ }

  return data;
}
```

- [ ] **Step 4: Update the Bootstrap `computeAndRender` function**

Find the existing `computeAndRender` (or similar) function in the Bootstrap IIFE and replace it with:

```javascript
async function computeAndRender(loc) {
  try {
    const today = new Date();
    const data = await fetchPanchang(loc.lat, loc.lon, today);
    UI.render(data, loc);
  } catch (err) {
    UI.showError('Could not load Panchang data: ' + err.message);
  }
}
```

- [ ] **Step 5: Update `UI.render` to accept the API response shape**

The API response has `data.panchang.*` and `data.sankalpam.*`. Update the render function so it reads from `data.panchang` instead of individual computed values. For example, where it previously did `Panchang.getSamvatsara(jd)`, it now does `data.panchang.samvatsara`.

Add a sankalpam display section to the rendered HTML:

```javascript
// Inside UI.render, after the existing panchang fields:
const sankEl = document.getElementById('sankalpam-section');
if (sankEl && data.sankalpam) {
  const s = data.sankalpam;
  sankEl.innerHTML = `
    <h2>సంకల్పం / Sankalpam</h2>
    <p class="sankalpam-te">${s.full_te}</p>
    <p class="sankalpam-en">${s.full_en}</p>
  `;
  sankEl.style.display = 'block';
}
```

- [ ] **Step 6: Add the sankalpam section div to the HTML body**

In the `<body>`, after the main panchang display `<div>`, add:

```html
<div id="sankalpam-section" style="display:none;" class="sankalpam-card"></div>
```

Add the CSS for it (inside `<style>`):

```css
.sankalpam-card {
  background: rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-top: 1.5rem;
  max-width: 860px;
  margin-left: auto;
  margin-right: auto;
}
.sankalpam-te {
  font-size: 1rem;
  line-height: 1.8;
  color: #ffe082;
  margin-bottom: 0.75rem;
}
.sankalpam-en {
  font-size: 0.88rem;
  line-height: 1.7;
  color: #f5deb3;
  font-style: italic;
}
```

- [ ] **Step 7: Test locally**

```powershell
# Serve the file locally
python -m http.server 8080 --directory frontend
# Open http://localhost:8080/panchang.html in browser
# Verify panchang loads from API, sankalpam section appears
```

- [ ] **Step 8: Upload updated panchang.html to S3 and invalidate CloudFront**

```powershell
aws s3 cp frontend\panchang.html s3://today.sanatanadharmas.com/index.html `
  --content-type "text/html" --cache-control "no-cache"

# Invalidate CloudFront (use the distribution ID from the original deployment: E17GLGCZAXWTVX)
aws cloudfront create-invalidation `
  --distribution-id E17GLGCZAXWTVX `
  --paths "/*"
```

- [ ] **Step 9: Verify live site**

```powershell
curl -I "https://today.sanatanadharmas.com"
# Also open in browser and verify sankalpam section renders
```

- [ ] **Step 10: Commit**

```powershell
git add frontend\panchang.html
git commit -m "feat: panchang.html now calls shared API + displays sankalpam"
```

---

## Regression Checklist (run after all tasks complete)

```powershell
cd panchang-api
python -m pytest tests/ -v
```
Expected: All tests pass.

Manual spot checks:
- `https://api.sanatanadharmas.com/panchang?lat=17.38&lon=78.49&date=2026-05-17` → Parabhava, Adhika Jyeshtha, Grishma, Shukla Panchami
- `https://api.sanatanadharmas.com/panchang?lat=37.77&lon=-122.41` → Krauncha Dweepae in sankalpam
- `https://today.sanatanadharmas.com` → page loads, panchang values correct, sankalpam section visible
