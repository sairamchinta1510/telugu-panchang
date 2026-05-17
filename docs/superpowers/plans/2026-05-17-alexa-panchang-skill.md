# Telugu Panchang Alexa Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AWS Lambda (Python) Alexa Skill that speaks daily Telugu Panchang — full briefing or specific queries — bilingually (English + Telugu SSML), using the device's location for accurate calculations.

**Architecture:** Python 3.12 Lambda using `ask-sdk-core`; `ephem` library for sun/moon ecliptic longitudes; stateless handlers (one class per intent); location resolved from Alexa Geolocation API with Device Address API fallback; language preference detected from utterance slot and stored in session attributes.

**Tech Stack:** Python 3.12, `ask-sdk-core 1.x`, `ephem 4.x`, `requests 2.x`, pytest, AWS Lambda (ZIP deployment), Alexa Developer Console

---

## File Map

| File | Purpose |
|---|---|
| `lambda/telugu_calendar.py` | All name tables + lookup functions |
| `lambda/south_indian.py` | Rahu Kalam / Yamagandam / Gulikai / Abhijit slot calculations |
| `lambda/panchang.py` | ephem-based calculation engine, `PanchangData` dataclass |
| `lambda/geo.py` | Location resolution (Geolocation API → Address API → Nominatim → default) |
| `lambda/speech.py` | SSML response builders for each intent, bilingual |
| `lambda/lambda_function.py` | Alexa SDK handler classes wired to panchang + speech |
| `lambda/requirements.txt` | `ephem`, `ask-sdk-core`, `requests` |
| `skill-package/interactionModels/custom/en-IN.json` | Interaction model with all intents + LanguagePreference slot |
| `skill-package/skill.json` | Skill manifest with permissions |
| `tests/test_telugu_calendar.py` | Unit tests for lookup functions |
| `tests/test_south_indian.py` | Unit tests for slot calculations |
| `tests/test_panchang.py` | Unit tests for panchang calculations |
| `tests/test_speech.py` | Unit tests for SSML builders |

---

### Task 1: Repo Scaffold

**Files:**
- Create: `lambda/requirements.txt`
- Create: `tests/__init__.py`
- Create: `lambda/__init__.py`

- [ ] **Step 1: Create the repository structure**

Run from the new repo root (`telugu-panchang-alexa/`):

```bash
mkdir -p lambda tests skill-package/interactionModels/custom
touch lambda/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create `lambda/requirements.txt`**

```
ephem==4.1.6
ask-sdk-core==1.19.0
requests==2.31.0
```

- [ ] **Step 3: Install dependencies locally for testing**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r lambda/requirements.txt pytest
```

Expected: All packages install without errors.

- [ ] **Step 4: Commit**

```bash
git init
git add .
git commit -m "chore: initial repo scaffold with requirements"
```

---

### Task 2: `telugu_calendar.py` — Name Tables + Lookup Functions

**Files:**
- Create: `lambda/telugu_calendar.py`
- Create: `tests/test_telugu_calendar.py`

- [ ] **Step 1: Write the failing tests first**

Create `tests/test_telugu_calendar.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from telugu_calendar import get_tithi, get_nakshatra, get_yoga, get_karana, \
                             get_masam, get_rutuvu, get_paksham, get_vara, get_samvatsara

def test_masam_jyeshtha():
    # Sun at 75° = Gemini = Jyeshtha
    m = get_masam(75.0)
    assert m['en'] == 'Jyeshtha'
    assert m['te'] == 'జ్యేష్ఠ'

def test_rutuvu_grishma():
    # Sun at 75° falls in 60°–120° = Grishma
    r = get_rutuvu(75.0)
    assert r['en'] == 'Grishma'

def test_tithi_chaturthi():
    # diff = 36° → floor(36/12) = 3 → Chaturthi (index 3)
    t = get_tithi(136.0, 100.0)
    assert t['en'] == 'Chaturthi'
    assert t['idx'] == 3

def test_tithi_amavasya():
    # diff = 348° → floor(348/12) = 29 → Amavasya
    t = get_tithi(448.0, 100.0)
    assert t['en'] == 'Amavasya'

def test_paksham_shukla():
    assert get_paksham(0)['en'] == 'Shukla Paksham'
    assert get_paksham(14)['en'] == 'Shukla Paksham'

def test_paksham_krishna():
    assert get_paksham(15)['en'] == 'Krishna Paksham'
    assert get_paksham(29)['en'] == 'Krishna Paksham'

def test_nakshatra_rohini():
    # Rohini is index 3; each nakshatra spans 360/27 ≈ 13.33°
    # Index 3 starts at 3*13.33 = 40°
    n = get_nakshatra(43.0)
    assert n['en'] == 'Rohini'

def test_karana_vishti():
    # half = floor(diff/6); Vishti = repeating index 6 → (half-1)%7 == 6
    # half=7 → (7-1)%7 = 6 → Vishti
    k = get_karana(100.0 + 7*6, 100.0)
    assert k['en'] == 'Vishti'

def test_karana_shakuni():
    # half=57 → Shakuni
    k = get_karana(100.0 + 57*6, 100.0)
    assert k['en'] == 'Shakuni'

def test_vara_sunday():
    from datetime import datetime
    d = datetime(2026, 5, 17)  # Sunday
    v = get_vara(d)
    assert v['en'] == 'Sunday'
    assert v['te'] == 'ఆదివారం'
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_telugu_calendar.py -v
```

Expected: `ImportError: No module named 'telugu_calendar'`

- [ ] **Step 3: Create `lambda/telugu_calendar.py`**

```python
"""Telugu calendar name tables and lookup functions."""

TITHI = [
    {'en': 'Pratipada',   'te': 'పాడ్యమి'},
    {'en': 'Dwitiya',     'te': 'విదియ'},
    {'en': 'Tritiya',     'te': 'తదియ'},
    {'en': 'Chaturthi',   'te': 'చవితి'},
    {'en': 'Panchami',    'te': 'పంచమి'},
    {'en': 'Shashthi',    'te': 'షష్ఠి'},
    {'en': 'Saptami',     'te': 'సప్తమి'},
    {'en': 'Ashtami',     'te': 'అష్టమి'},
    {'en': 'Navami',      'te': 'నవమి'},
    {'en': 'Dashami',     'te': 'దశమి'},
    {'en': 'Ekadashi',    'te': 'ఏకాదశి'},
    {'en': 'Dwadashi',    'te': 'ద్వాదశి'},
    {'en': 'Trayodashi',  'te': 'త్రయోదశి'},
    {'en': 'Chaturdashi', 'te': 'చతుర్దశి'},
    {'en': 'Purnima',     'te': 'పౌర్ణమి'},
    {'en': 'Pratipada',   'te': 'పాడ్యమి'},
    {'en': 'Dwitiya',     'te': 'విదియ'},
    {'en': 'Tritiya',     'te': 'తదియ'},
    {'en': 'Chaturthi',   'te': 'చవితి'},
    {'en': 'Panchami',    'te': 'పంచమి'},
    {'en': 'Shashthi',    'te': 'షష్ఠి'},
    {'en': 'Saptami',     'te': 'సప్తమి'},
    {'en': 'Ashtami',     'te': 'అష్టమి'},
    {'en': 'Navami',      'te': 'నవమి'},
    {'en': 'Dashami',     'te': 'దశమి'},
    {'en': 'Ekadashi',    'te': 'ఏకాదశి'},
    {'en': 'Dwadashi',    'te': 'ద్వాదశి'},
    {'en': 'Trayodashi',  'te': 'త్రయోదశి'},
    {'en': 'Chaturdashi', 'te': 'చతుర్దశి'},
    {'en': 'Amavasya',    'te': 'అమావాస్య'},
]

NAKSHATRA = [
    {'en': 'Ashwini',            'te': 'అశ్విని'},
    {'en': 'Bharani',            'te': 'భరణి'},
    {'en': 'Krittika',           'te': 'కృత్తిక'},
    {'en': 'Rohini',             'te': 'రోహిణి'},
    {'en': 'Mrigashira',         'te': 'మృగశిర'},
    {'en': 'Ardra',              'te': 'ఆర్ద్ర'},
    {'en': 'Punarvasu',          'te': 'పునర్వసు'},
    {'en': 'Pushya',             'te': 'పుష్యమి'},
    {'en': 'Ashlesha',           'te': 'ఆశ్లేష'},
    {'en': 'Magha',              'te': 'మఖ'},
    {'en': 'Purva Phalguni',     'te': 'పూర్వ ఫల్గుణి'},
    {'en': 'Uttara Phalguni',    'te': 'ఉత్తర ఫల్గుణి'},
    {'en': 'Hasta',              'te': 'హస్త'},
    {'en': 'Chitra',             'te': 'చిత్త'},
    {'en': 'Swati',              'te': 'స్వాతి'},
    {'en': 'Vishakha',           'te': 'విశాఖ'},
    {'en': 'Anuradha',           'te': 'అనూరాధ'},
    {'en': 'Jyeshtha',           'te': 'జ్యేష్ఠ'},
    {'en': 'Mula',               'te': 'మూల'},
    {'en': 'Purva Ashadha',      'te': 'పూర్వాషాఢ'},
    {'en': 'Uttara Ashadha',     'te': 'ఉత్తరాషాఢ'},
    {'en': 'Shravana',           'te': 'శ్రవణం'},
    {'en': 'Dhanishta',          'te': 'ధనిష్ట'},
    {'en': 'Shatabhisha',        'te': 'శతభిష'},
    {'en': 'Purva Bhadrapada',   'te': 'పూర్వభాద్ర'},
    {'en': 'Uttara Bhadrapada',  'te': 'ఉత్తరభాద్ర'},
    {'en': 'Revati',             'te': 'రేవతి'},
]

YOGA = [
    {'en': 'Vishkambha', 'te': 'విష్కంభ'}, {'en': 'Priti',       'te': 'ప్రీతి'},
    {'en': 'Ayushman',   'te': 'ఆయుష్మాన్'},{'en': 'Saubhagya',   'te': 'సౌభాగ్య'},
    {'en': 'Shobhana',   'te': 'శోభన'},     {'en': 'Atiganda',    'te': 'అతిగండ'},
    {'en': 'Sukarma',    'te': 'సుకర్మ'},   {'en': 'Dhriti',      'te': 'ధృతి'},
    {'en': 'Shoola',     'te': 'శూల'},      {'en': 'Ganda',       'te': 'గండ'},
    {'en': 'Vriddhi',    'te': 'వృద్ధి'},   {'en': 'Dhruva',      'te': 'ధ్రువ'},
    {'en': 'Vyaghata',   'te': 'వ్యాఘాత'}, {'en': 'Harshana',    'te': 'హర్షణ'},
    {'en': 'Vajra',      'te': 'వజ్ర'},     {'en': 'Siddhi',      'te': 'సిద్ధి'},
    {'en': 'Vyatipata',  'te': 'వ్యతీపాత'},{'en': 'Variyana',    'te': 'వరీయాన్'},
    {'en': 'Parigha',    'te': 'పరిఘ'},     {'en': 'Shiva',       'te': 'శివ'},
    {'en': 'Siddha',     'te': 'సిద్ధ'},    {'en': 'Sadhya',      'te': 'సాధ్య'},
    {'en': 'Shubha',     'te': 'శుభ'},      {'en': 'Shukla',      'te': 'శుక్ల'},
    {'en': 'Brahma',     'te': 'బ్రహ్మ'},   {'en': 'Indra',       'te': 'ఐంద్ర'},
    {'en': 'Vaidhriti',  'te': 'వైధృతి'},
]

KARANA = [
    {'en': 'Bava',         'te': 'బవ'},
    {'en': 'Balava',       'te': 'బాలవ'},
    {'en': 'Kaulava',      'te': 'కౌలవ'},
    {'en': 'Taitila',      'te': 'తైతుల'},
    {'en': 'Garaja',       'te': 'గరజ'},
    {'en': 'Vanija',       'te': 'వణిజ'},
    {'en': 'Vishti',       'te': 'విష్టి'},
    {'en': 'Shakuni',      'te': 'శకుని'},
    {'en': 'Chatushpada',  'te': 'చతుష్పద'},
    {'en': 'Naga',         'te': 'నాగ'},
    {'en': 'Kimstughna',   'te': 'కింస్తుఘ్న'},
]

MASAM = [
    {'en': 'Chaitra',      'te': 'చైత్ర'},
    {'en': 'Vaishakha',    'te': 'వైశాఖ'},
    {'en': 'Jyeshtha',     'te': 'జ్యేష్ఠ'},
    {'en': 'Ashadha',      'te': 'ఆషాఢ'},
    {'en': 'Shravana',     'te': 'శ్రావణ'},
    {'en': 'Bhadrapada',   'te': 'భాద్రపద'},
    {'en': 'Ashvina',      'te': 'ఆశ్వయుజ'},
    {'en': 'Kartika',      'te': 'కార్తీక'},
    {'en': 'Margashirsha', 'te': 'మార్గశిర'},
    {'en': 'Pausha',       'te': 'పుష్య'},
    {'en': 'Magha',        'te': 'మాఘ'},
    {'en': 'Phalguna',     'te': 'ఫాల్గుణ'},
]

RUTUVU = [
    {'en': 'Vasanta',  'te': 'వసంత'},
    {'en': 'Grishma',  'te': 'గ్రీష్మ'},
    {'en': 'Varsha',   'te': 'వర్ష'},
    {'en': 'Sharad',   'te': 'శరత్'},
    {'en': 'Hemanta',  'te': 'హేమంత'},
    {'en': 'Shishira', 'te': 'శిశిర'},
]

VARA = [
    {'en': 'Sunday',    'te': 'ఆదివారం'},
    {'en': 'Monday',    'te': 'సోమవారం'},
    {'en': 'Tuesday',   'te': 'మంగళవారం'},
    {'en': 'Wednesday', 'te': 'బుధవారం'},
    {'en': 'Thursday',  'te': 'గురువారం'},
    {'en': 'Friday',    'te': 'శుక్రవారం'},
    {'en': 'Saturday',  'te': 'శనివారం'},
]

SAMVATSARA = [
    'Prabhava','Vibhava','Shukla','Pramoda','Prajapati','Angirasa','Shrimukha','Bhava',
    'Yuva','Dhatri','Ishvara','Bahudhanya','Pramathi','Vikrama','Vrisha','Chitrabhanu',
    'Subhanu','Tarana','Parthiva','Vyaya','Sarvajit','Sarvadhari','Virodhi','Vikrita',
    'Khara','Nandana','Vijaya','Jaya','Manmatha','Durmukhi','Hevilambi','Vilambi',
    'Vikari','Sharvari','Plava','Shubhakrit','Shobhana','Krodhi','Vishvavasu','Parabhava',
    'Plavanga','Kilaka','Saumya','Sadharana','Virodhikrit','Paritapi','Pramadi','Ananda',
    'Rakshasa','Nala','Pingala','Kalayukti','Siddharthi','Raudra','Durmati','Dundubhi',
    'Rudhirodgari','Raktakshi','Krodhana','Kshaya',
]


def get_tithi(moon_lon: float, sun_lon: float) -> dict:
    diff = (moon_lon - sun_lon) % 360
    idx  = int(diff / 12) % 30
    return {**TITHI[idx], 'idx': idx}


def get_nakshatra(moon_lon: float) -> dict:
    idx = int(moon_lon / (360 / 27)) % 27
    return {**NAKSHATRA[idx], 'idx': idx}


def get_yoga(moon_lon: float, sun_lon: float) -> dict:
    idx = int(((moon_lon + sun_lon) % 360) / (360 / 27)) % 27
    return {**YOGA[idx], 'idx': idx}


def get_karana(moon_lon: float, sun_lon: float) -> dict:
    diff = (moon_lon - sun_lon) % 360
    half = int(diff / 6) % 60
    if half == 0:  return KARANA[10]   # Kimstughna
    if half == 57: return KARANA[7]    # Shakuni
    if half == 58: return KARANA[8]    # Chatushpada
    if half == 59: return KARANA[9]    # Naga
    return KARANA[(half - 1) % 7]


def get_masam(sun_lon: float) -> dict:
    return MASAM[int(sun_lon / 30) % 12]


def get_rutuvu(sun_lon: float) -> dict:
    return RUTUVU[int(sun_lon / 60) % 6]


def get_paksham(tithi_idx: int) -> dict:
    if tithi_idx < 15:
        return {'en': 'Shukla Paksham', 'te': 'శుక్ల పక్షం'}
    return {'en': 'Krishna Paksham', 'te': 'కృష్ణ పక్షం'}


def get_vara(dt) -> dict:
    return VARA[dt.weekday() + 1 if dt.weekday() < 6 else 0]
    # Python weekday(): Mon=0 … Sun=6; we want Sun=0 … Sat=6
    # Remap: (dt.weekday() + 1) % 7
def get_vara(dt) -> dict:
    return VARA[(dt.weekday() + 1) % 7]


def get_samvatsara(year: int) -> str:
    saka_year = year - 78
    idx = (saka_year - 1) % 60
    return SAMVATSARA[idx]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_telugu_calendar.py -v
```

Expected: All 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lambda/telugu_calendar.py tests/test_telugu_calendar.py
git commit -m "feat: add telugu_calendar module with all name tables and lookup functions"
```

---

### Task 3: `south_indian.py` — Slot Calculations

**Files:**
- Create: `lambda/south_indian.py`
- Create: `tests/test_south_indian.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_south_indian.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from datetime import datetime, timezone, timedelta
from south_indian import get_rahu_kalam, get_yamagandam, get_gulikai, get_abhijit_muhurta

IST = timezone(timedelta(hours=5, minutes=30))

def _times():
    # Sunrise 6:00 AM IST, Sunset 6:00 PM IST on a Sunday
    sr = datetime(2026, 5, 17, 6, 0, tzinfo=IST)
    ss = datetime(2026, 5, 17, 18, 0, tzinfo=IST)
    return sr, ss

def test_rahu_kalam_sunday():
    sr, ss = _times()
    rahu = get_rahu_kalam(6, sr, ss)  # weekday 6 = Sunday
    # Slot 8 of 8: starts at 6AM + 7*(12h/8) = 6AM + 7*90min = 4:30PM
    assert rahu['start'].hour == 16 and rahu['start'].minute == 30
    assert rahu['end'].hour   == 18 and rahu['end'].minute   == 0

def test_rahu_kalam_monday():
    sr, ss = _times()
    rahu = get_rahu_kalam(0, sr, ss)  # weekday 0 = Monday
    # Slot 2: starts 6AM + 1*90min = 7:30AM, ends 9:00AM
    assert rahu['start'].hour == 7  and rahu['start'].minute == 30
    assert rahu['end'].hour   == 9  and rahu['end'].minute   == 0

def test_yamagandam_sunday():
    sr, ss = _times()
    yama = get_yamagandam(6, sr, ss)  # Sunday = slot 5
    # Slot 5: starts 6AM + 4*90min = 12PM, ends 1:30PM
    assert yama['start'].hour == 12 and yama['start'].minute == 0
    assert yama['end'].hour   == 13 and yama['end'].minute   == 30

def test_abhijit_muhurta():
    sr, ss = _times()
    abhijit = get_abhijit_muhurta(sr, ss)
    # Midday = 12:00 PM; ±24min → 11:36 AM – 12:24 PM
    assert abhijit['start'].hour == 11 and abhijit['start'].minute == 36
    assert abhijit['end'].hour   == 12 and abhijit['end'].minute   == 24
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_south_indian.py -v
```

Expected: `ImportError: No module named 'south_indian'`

- [ ] **Step 3: Create `lambda/south_indian.py`**

```python
"""South Indian inauspicious period calculations."""

from datetime import datetime, timedelta
from typing import Tuple

# Slot tables indexed by weekday where 0=Monday (Python weekday convention).
# Remap: Sunday=6 in Python → index 6 here maps to the traditional "Sunday" row.
# Tables are Sun=0,Mon=1,...,Sat=6 in traditional form;
# we accept Python weekday (Mon=0..Sun=6) and convert.

# Traditional order: Sun Mon Tue Wed Thu Fri Sat
_RAHU_TRAD    = [8, 2, 7, 5, 6, 3, 4]
_YAMA_TRAD    = [5, 4, 3, 2, 1, 7, 6]
_GULIKAI_TRAD = [6, 5, 4, 3, 2, 1, 7]

def _python_weekday_to_traditional(python_weekday: int) -> int:
    """Convert Python weekday (Mon=0..Sun=6) to traditional Hindu (Sun=0..Sat=6)."""
    return (python_weekday + 1) % 7


def _slot_times(slot_num: int, sunrise: datetime, sunset: datetime) -> dict:
    """Return start/end datetime for the Nth slot (1-based) of the day."""
    day_secs   = (sunset - sunrise).total_seconds()
    slot_secs  = day_secs / 8
    start      = sunrise + timedelta(seconds=(slot_num - 1) * slot_secs)
    end        = start   + timedelta(seconds=slot_secs)
    return {'start': start, 'end': end}


def get_rahu_kalam(python_weekday: int, sunrise: datetime, sunset: datetime) -> dict:
    trad = _python_weekday_to_traditional(python_weekday)
    return _slot_times(_RAHU_TRAD[trad], sunrise, sunset)


def get_yamagandam(python_weekday: int, sunrise: datetime, sunset: datetime) -> dict:
    trad = _python_weekday_to_traditional(python_weekday)
    return _slot_times(_YAMA_TRAD[trad], sunrise, sunset)


def get_gulikai(python_weekday: int, sunrise: datetime, sunset: datetime) -> dict:
    trad = _python_weekday_to_traditional(python_weekday)
    return _slot_times(_GULIKAI_TRAD[trad], sunrise, sunset)


def get_abhijit_muhurta(sunrise: datetime, sunset: datetime) -> dict:
    midday = sunrise + (sunset - sunrise) / 2
    return {
        'start': midday - timedelta(minutes=24),
        'end':   midday + timedelta(minutes=24),
    }
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_south_indian.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lambda/south_indian.py tests/test_south_indian.py
git commit -m "feat: add south_indian module (Rahu Kalam, Yamagandam, Gulikai, Abhijit Muhurta)"
```

---

### Task 4: `panchang.py` — ephem Calculation Engine

**Files:**
- Create: `lambda/panchang.py`
- Create: `tests/test_panchang.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_panchang.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from datetime import datetime, timezone
from panchang import compute

def test_compute_returns_all_fields():
    dt  = datetime(2026, 5, 17, 6, 30, 0, tzinfo=timezone.utc)
    res = compute(dt, 17.38, 78.48)
    assert res['tithi']['en'] in [t['en'] for t in __import__('telugu_calendar').TITHI]
    assert res['nakshatra']['en'] is not None
    assert res['yoga']['en'] is not None
    assert res['karana']['en'] is not None
    assert res['vara']['en'] is not None
    assert res['masam']['en'] is not None
    assert res['rutuvu']['en'] is not None
    assert 'Shukla' in res['paksham']['en'] or 'Krishna' in res['paksham']['en']
    assert isinstance(res['samvatsara'], str)

def test_tithi_end_is_datetime_or_none():
    dt  = datetime(2026, 5, 17, 6, 30, 0, tzinfo=timezone.utc)
    res = compute(dt, 17.38, 78.48)
    # tithi_end should be a datetime after the input time
    if res['tithi_end'] is not None:
        assert res['tithi_end'] > dt

def test_sunrise_sunset_present():
    dt  = datetime(2026, 5, 17, 0, 0, 0, tzinfo=timezone.utc)
    res = compute(dt, 17.38, 78.48)
    assert res['sunrise'] is not None
    assert res['sunset']  is not None
    # Sunrise in Hyderabad should be roughly 00:00–02:00 UTC (5:30–8:00 IST)
    assert 0 <= res['sunrise'].hour <= 3
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_panchang.py -v
```

Expected: `ImportError: No module named 'panchang'`

- [ ] **Step 3: Create `lambda/panchang.py`**

```python
"""Panchang calculation engine using ephem for sun/moon positions."""

import ephem
from datetime import datetime, timezone, timedelta
from typing import Optional
import telugu_calendar as tc


def _to_ephem_date(dt: datetime) -> ephem.Date:
    """Convert a UTC-aware datetime to ephem.Date."""
    return ephem.Date(dt.strftime('%Y/%m/%d %H:%M:%S'))


def _sun_lon(dt: datetime) -> float:
    """Return geocentric ecliptic longitude of Sun in degrees [0, 360)."""
    sun = ephem.Sun()
    sun.compute(_to_ephem_date(dt), epoch=ephem.J2000)
    return float(ephem.degrees(sun.hlong)) * 180 / 3.141592653589793 % 360


def _moon_lon(dt: datetime) -> float:
    """Return geocentric ecliptic longitude of Moon in degrees [0, 360)."""
    moon = ephem.Moon()
    moon.compute(_to_ephem_date(dt), epoch=ephem.J2000)
    return float(ephem.degrees(moon.hlong)) * 180 / 3.141592653589793 % 360


def _find_end_time(start_dt: datetime, get_idx_fn, start_idx: int) -> Optional[datetime]:
    """Binary search for when a panchang index changes from start_idx."""
    lo = start_dt
    hi = start_dt + timedelta(hours=48)
    # Extend hi until different
    for _ in range(60):
        if get_idx_fn(hi) != start_idx:
            break
        hi += timedelta(hours=1)
    else:
        return None  # couldn't find transition

    while (hi - lo).total_seconds() > 60:
        mid = lo + (hi - lo) / 2
        if get_idx_fn(mid) == start_idx:
            lo = mid
        else:
            hi = mid
    return hi


def _get_sunrise_sunset(dt: datetime, lat: float, lon: float):
    """Return (sunrise, sunset) as UTC-aware datetimes using ephem."""
    obs         = ephem.Observer()
    obs.lat     = str(lat)
    obs.lon     = str(lon)
    obs.date    = _to_ephem_date(datetime(dt.year, dt.month, dt.day, 0, 0, tzinfo=timezone.utc))
    obs.horizon = '-0:34'  # standard refraction
    sun         = ephem.Sun()

    try:
        sr = obs.next_rising(sun)
        ss = obs.next_setting(sun)
        to_dt = lambda e: datetime.strptime(str(e), '%Y/%m/%d %H:%M:%S').replace(tzinfo=timezone.utc)
        return to_dt(sr), to_dt(ss)
    except ephem.AlwaysUpError:
        return None, None
    except ephem.NeverUpError:
        return None, None


def compute(dt: datetime, lat: float, lon: float) -> dict:
    """
    Compute full panchang for given UTC datetime and location.

    Returns dict with keys: tithi, tithi_end, nakshatra, nakshatra_end,
    yoga, karana, vara, masam, rutuvu, paksham, samvatsara, sunrise, sunset.
    """
    sun_lon  = _sun_lon(dt)
    moon_lon = _moon_lon(dt)

    tithi     = tc.get_tithi(moon_lon, sun_lon)
    nakshatra = tc.get_nakshatra(moon_lon)
    yoga      = tc.get_yoga(moon_lon, sun_lon)
    karana    = tc.get_karana(moon_lon, sun_lon)
    vara      = tc.get_vara(dt)
    masam     = tc.get_masam(sun_lon)
    rutuvu    = tc.get_rutuvu(sun_lon)
    paksham   = tc.get_paksham(tithi['idx'])
    samvatsara = tc.get_samvatsara(dt.year)

    tithi_end = _find_end_time(
        dt,
        lambda d: tc.get_tithi(_moon_lon(d), _sun_lon(d))['idx'],
        tithi['idx']
    )
    nakshatra_end = _find_end_time(
        dt,
        lambda d: tc.get_nakshatra(_moon_lon(d))['idx'],
        nakshatra['idx']
    )

    sunrise, sunset = _get_sunrise_sunset(dt, lat, lon)

    return {
        'tithi': tithi, 'tithi_end': tithi_end,
        'nakshatra': nakshatra, 'nakshatra_end': nakshatra_end,
        'yoga': yoga, 'karana': karana, 'vara': vara,
        'masam': masam, 'rutuvu': rutuvu,
        'paksham': paksham, 'samvatsara': samvatsara,
        'sunrise': sunrise, 'sunset': sunset,
    }
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_panchang.py -v
```

Expected: All 3 tests pass. (Note: `tithi_end` test takes ~5–15s due to binary search iterations.)

- [ ] **Step 5: Commit**

```bash
git add lambda/panchang.py tests/test_panchang.py
git commit -m "feat: add panchang module using ephem for sun/moon positions"
```

---

### Task 5: `geo.py` — Location Resolution

**Files:**
- Create: `lambda/geo.py`

- [ ] **Step 1: Create `lambda/geo.py`**

```python
"""Resolve Alexa device location to (lat, lon, city_name)."""

import requests
from typing import Tuple, Optional

DEFAULT_LAT  = 17.38
DEFAULT_LON  = 78.48
DEFAULT_CITY = 'Hyderabad (default)'


def _nominatim_geocode(address_line: str) -> Optional[Tuple[float, float]]:
    """Geocode a free-text address string to (lat, lon) via Nominatim."""
    try:
        resp = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': address_line, 'format': 'json', 'limit': 1},
            headers={'Accept-Language': 'en'},
            timeout=5
        )
        results = resp.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except Exception:
        pass
    return None


def resolve_location(handler_input) -> Tuple[float, float, str]:
    """
    Return (lat, lon, city_name) from Alexa request.
    Priority: Geolocation API → Device Address API + Nominatim → defaults.
    """
    req_envelope = handler_input.request_envelope
    sys_obj      = req_envelope.context.system

    # 1. Try Alexa Geolocation API (Echo Auto / Alexa app)
    try:
        geo = req_envelope.context.geolocation
        if geo and geo.coordinate:
            lat  = geo.coordinate.latitude_in_degrees
            lon  = geo.coordinate.longitude_in_degrees
            city = f'{lat:.2f}°N {lon:.2f}°E'
            return lat, lon, city
    except Exception:
        pass

    # 2. Try Device Address API
    try:
        device_id    = sys_obj.device.device_id
        api_endpoint = sys_obj.api_endpoint
        api_token    = sys_obj.api_access_token
        url  = f'{api_endpoint}/v1/devices/{device_id}/settings/address'
        resp = requests.get(url, headers={'Authorization': f'Bearer {api_token}'}, timeout=5)
        if resp.status_code == 200:
            addr = resp.json()
            parts = [addr.get('city'), addr.get('stateOrRegion'), addr.get('countryCode')]
            address_str = ', '.join(p for p in parts if p)
            if address_str:
                coords = _nominatim_geocode(address_str)
                if coords:
                    lat, lon = coords
                    return lat, lon, addr.get('city') or address_str
    except Exception:
        pass

    # 3. Fall back to Hyderabad defaults
    return DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY
```

- [ ] **Step 2: Commit** (Geo requires a live Alexa request; tested implicitly via Lambda integration test in Task 8)

```bash
git add lambda/geo.py
git commit -m "feat: add geo module (Geolocation → Device Address → Nominatim → default)"
```

---

### Task 6: `speech.py` — SSML Response Builders

**Files:**
- Create: `lambda/speech.py`
- Create: `tests/test_speech.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_speech.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from datetime import datetime, timezone, timedelta
from speech import build_daily_briefing, build_tithi_response, build_rahu_kalam_response, fmt_time

IST = timezone(timedelta(hours=5, minutes=30))

SAMPLE_DATA = {
    'tithi':     {'en': 'Tritiya', 'te': 'తదియ', 'idx': 2},
    'tithi_end': datetime(2026, 5, 17, 20, 22, tzinfo=IST),
    'nakshatra': {'en': 'Rohini',  'te': 'రోహిణి', 'idx': 3},
    'nakshatra_end': None,
    'yoga':      {'en': 'Siddha',  'te': 'సిద్ధ',   'idx': 20},
    'karana':    {'en': 'Bava',    'te': 'బవ'},
    'vara':      {'en': 'Sunday',  'te': 'ఆదివారం'},
    'masam':     {'en': 'Jyeshtha','te': 'జ్యేష్ఠ'},
    'rutuvu':    {'en': 'Grishma', 'te': 'గ్రీష్మ'},
    'paksham':   {'en': 'Shukla Paksham', 'te': 'శుక్ల పక్షం'},
    'samvatsara': 'Krodhana',
    'sunrise':   datetime(2026, 5, 17, 0, 32, tzinfo=timezone.utc),
    'sunset':    datetime(2026, 5, 17, 13, 12, tzinfo=timezone.utc),
    'rahu':      {'start': datetime(2026,5,17,11,0,tzinfo=timezone.utc), 'end': datetime(2026,5,17,12,30,tzinfo=timezone.utc)},
    'yama':      {'start': datetime(2026,5,17,6,30,tzinfo=timezone.utc), 'end': datetime(2026,5,17,8,0,tzinfo=timezone.utc)},
    'gulikai':   {'start': datetime(2026,5,17,9,0,tzinfo=timezone.utc),  'end': datetime(2026,5,17,10,30,tzinfo=timezone.utc)},
    'abhijit':   {'start': datetime(2026,5,17,6,58,tzinfo=timezone.utc), 'end': datetime(2026,5,17,7,46,tzinfo=timezone.utc)},
}

def test_daily_briefing_en_contains_tithi():
    speech = build_daily_briefing(SAMPLE_DATA, 'en')
    assert 'Tritiya' in speech

def test_daily_briefing_en_contains_rahu():
    speech = build_daily_briefing(SAMPLE_DATA, 'en')
    assert 'Rahu Kalam' in speech

def test_daily_briefing_te_contains_telugu():
    speech = build_daily_briefing(SAMPLE_DATA, 'te')
    assert 'తదియ' in speech or 'Tritiya' in speech

def test_tithi_response_en():
    speech = build_tithi_response(SAMPLE_DATA, 'en')
    assert 'Tritiya' in speech
    assert '8:22' in speech  # tithi_end in IST

def test_rahu_kalam_response_en():
    speech = build_rahu_kalam_response(SAMPLE_DATA, 'en')
    assert 'Rahu Kalam' in speech
    assert 'avoid' in speech.lower()

def test_fmt_time():
    dt = datetime(2026, 5, 17, 6, 2, tzinfo=timezone.utc)
    # No timezone conversion in fmt_time — it just formats the hour/minute
    result = fmt_time(dt)
    assert ':' in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_speech.py -v
```

Expected: `ImportError: No module named 'speech'`

- [ ] **Step 3: Create `lambda/speech.py`**

```python
"""SSML response builders for each Alexa intent, bilingual EN/TE."""

from datetime import datetime


REPROMPT = "What else would you like to know?"
REPROMPT_TE = "మీకు ఇంకేమైనా కావాలా?"


def fmt_time(dt: datetime) -> str:
    """Format datetime as 'H:MM AM/PM' in its own timezone."""
    if dt is None:
        return ''
    return dt.strftime('%-I:%M %p').lstrip('0') if hasattr(dt, 'strftime') else ''


def _reprompt(lang: str) -> str:
    return REPROMPT_TE if lang == 'te' else REPROMPT


def build_daily_briefing(data: dict, lang: str) -> str:
    d = data
    sr = fmt_time(d['sunrise'])
    ss = fmt_time(d['sunset'])
    rahu_s = fmt_time(d['rahu']['start'])
    rahu_e = fmt_time(d['rahu']['end'])
    yama_s = fmt_time(d['yama']['start'])
    yama_e = fmt_time(d['yama']['end'])
    ab_s   = fmt_time(d['abhijit']['start'])
    ab_e   = fmt_time(d['abhijit']['end'])

    if lang == 'te':
        return (
            f"నమస్కారం! నేడు {d['vara']['te']}, "
            f"{d['masam']['te']} మాసం, {d['paksham']['te']}, {d['rutuvu']['te']} ఋతువు. "
            f"తిథి {d['tithi']['te']}, నక్షత్రం {d['nakshatra']['te']}, యోగం {d['yoga']['te']}. "
            f"సూర్యోదయం {sr}కి, సూర్యాస్తమయం {ss}కి. "
            f"రాహు కాలం {rahu_s} నుండి {rahu_e} వరకు. "
            f"యమగండం {yama_s} నుండి {yama_e} వరకు. "
            f"అభిజిత్ ముహూర్తం {ab_s} నుండి {ab_e} వరకు. "
            f"{REPROMPT_TE}"
        )
    return (
        f"నమస్కారం! Today is {d['vara']['en']}. "
        f"{d['masam']['en']} Masam, {d['paksham']['en']}, {d['rutuvu']['en']} Ritu. "
        f"Tithi is {d['tithi']['en']}, Nakshatra is {d['nakshatra']['en']}, Yoga is {d['yoga']['en']}. "
        f"Sunrise at {sr}, Sunset at {ss}. "
        f"Rahu Kalam is from {rahu_s} to {rahu_e}. "
        f"Yamagandam from {yama_s} to {yama_e}. "
        f"Abhijit Muhurta, the most auspicious time, is from {ab_s} to {ab_e}. "
        f"{REPROMPT}"
    )


def build_tithi_response(data: dict, lang: str) -> str:
    t   = data['tithi']
    end = fmt_time(data['tithi_end']) if data.get('tithi_end') else None
    if lang == 'te':
        base = f"నేటి తిథి {t['te']}."
        return base + (f" ఇది {end} వరకు ఉంటుంది. {REPROMPT_TE}" if end else f" {REPROMPT_TE}")
    base = f"Today's Tithi is {t['en']}."
    return base + (f" It continues until {end}. {REPROMPT}" if end else f" {REPROMPT}")


def build_nakshatra_response(data: dict, lang: str) -> str:
    n   = data['nakshatra']
    end = fmt_time(data['nakshatra_end']) if data.get('nakshatra_end') else None
    if lang == 'te':
        base = f"నేటి నక్షత్రం {n['te']}."
        return base + (f" ఇది {end} వరకు ఉంటుంది. {REPROMPT_TE}" if end else f" {REPROMPT_TE}")
    base = f"Today's Nakshatra is {n['en']}."
    return base + (f" It continues until {end}. {REPROMPT}" if end else f" {REPROMPT}")


def build_rahu_kalam_response(data: dict, lang: str) -> str:
    s = fmt_time(data['rahu']['start'])
    e = fmt_time(data['rahu']['end'])
    if lang == 'te':
        return f"నేటి రాహు కాలం {s} నుండి {e} వరకు. ఈ సమయంలో ముఖ్యమైన పనులు మొదలు పెట్టకండి. {REPROMPT_TE}"
    return f"Today's Rahu Kalam is from {s} to {e}. Avoid starting important activities during this time. {REPROMPT}"


def build_yamagandam_response(data: dict, lang: str) -> str:
    s = fmt_time(data['yama']['start'])
    e = fmt_time(data['yama']['end'])
    if lang == 'te':
        return f"యమగండం {s} నుండి {e} వరకు. {REPROMPT_TE}"
    return f"Yamagandam is from {s} to {e}. {REPROMPT}"


def build_gulikai_response(data: dict, lang: str) -> str:
    s = fmt_time(data['gulikai']['start'])
    e = fmt_time(data['gulikai']['end'])
    if lang == 'te':
        return f"గులికై కాలం {s} నుండి {e} వరకు. {REPROMPT_TE}"
    return f"Gulikai Kalam is from {s} to {e}. {REPROMPT}"


def build_abhijit_response(data: dict, lang: str) -> str:
    s = fmt_time(data['abhijit']['start'])
    e = fmt_time(data['abhijit']['end'])
    if lang == 'te':
        return f"అభిజిత్ ముహూర్తం, అత్యంత శుభప్రదమైన సమయం, {s} నుండి {e} వరకు. {REPROMPT_TE}"
    return f"Abhijit Muhurta, the most auspicious time today, is from {s} to {e}. {REPROMPT}"


def build_sun_timings_response(data: dict, lang: str) -> str:
    sr = fmt_time(data['sunrise'])
    ss = fmt_time(data['sunset'])
    if lang == 'te':
        return f"సూర్యోదయం {sr}కి మరియు సూర్యాస్తమయం {ss}కి. {REPROMPT_TE}"
    return f"Sunrise is at {sr} and Sunset is at {ss}. {REPROMPT}"


def build_yoga_response(data: dict, lang: str) -> str:
    y = data['yoga']
    if lang == 'te':
        return f"నేటి యోగం {y['te']}. {REPROMPT_TE}"
    return f"Today's Yoga is {y['en']}. {REPROMPT}"


def build_help_response(lang: str) -> str:
    if lang == 'te':
        return ("మీరు అడగవచ్చు: నేటి పంచాంగం చెప్పు, తిథి ఏమిటి, నక్షత్రం ఏమిటి, "
                "రాహు కాలం ఎప్పుడు, యమగండం ఎప్పుడు, సూర్యోదయం ఎప్పుడు. " + REPROMPT_TE)
    return ("You can ask: Give me today's panchang, What is today's tithi, "
            "What nakshatra is today, When is Rahu Kalam, When is Yamagandam, "
            "What time is sunrise. " + REPROMPT)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_speech.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add lambda/speech.py tests/test_speech.py
git commit -m "feat: add speech module with bilingual SSML response builders"
```

---

### Task 7: `lambda_function.py` — Alexa SDK Handler

**Files:**
- Create: `lambda/lambda_function.py`

- [ ] **Step 1: Create `lambda/lambda_function.py`**

```python
"""Alexa Skill handler — Telugu Daily Panchang."""

import logging
from datetime import datetime, timezone

from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_model import Response
from ask_sdk_model.ui import AskForPermissionsConsentCard

import panchang as panch
import south_indian as si
import geo
import speech as sp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LOCATION_PERMISSIONS = [
    'alexa::devices:all:geolocation:read',
    'alexa::devices:all:address:full:read',
]


def _get_lang(handler_input: HandlerInput) -> str:
    attrs = handler_input.attributes_manager.session_attributes
    return attrs.get('lang', 'en')


def _build_panchang_data(handler_input: HandlerInput) -> dict:
    lat, lon, city = geo.resolve_location(handler_input)
    now = datetime.now(timezone.utc)
    data = panch.compute(now, lat, lon)

    sunrise = data['sunrise']
    sunset  = data['sunset']
    weekday = now.weekday()

    if sunrise and sunset:
        data['rahu']    = si.get_rahu_kalam(weekday, sunrise, sunset)
        data['yama']    = si.get_yamagandam(weekday, sunrise, sunset)
        data['gulikai'] = si.get_gulikai(weekday, sunrise, sunset)
        data['abhijit'] = si.get_abhijit_muhurta(sunrise, sunset)
    else:
        data.update({'rahu': None, 'yama': None, 'gulikai': None, 'abhijit': None})

    data['city'] = city
    return data


def _respond(handler_input: HandlerInput, speech_text: str, end_session: bool = False) -> Response:
    return (
        handler_input.response_builder
            .speak(speech_text)
            .ask(sp.REPROMPT if not end_session else None)
            .set_should_end_session(end_session)
            .response
    )


# ── Handlers ──────────────────────────────────────────────

class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, hi): return hi.request_envelope.request.object_type == 'LaunchRequest'
    def handle(self, hi):
        lang = _get_lang(hi)
        try:
            data   = _build_panchang_data(hi)
            speech = sp.build_daily_briefing(data, lang)
        except Exception as e:
            logger.error(e)
            speech = "I had trouble calculating today's panchang. Please try again."
        return _respond(hi, speech)


class DailyBriefingHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'DailyBriefingIntent')
    def handle(self, hi):
        # Check for LanguagePreference slot
        intent = hi.request_envelope.request.intent
        try:
            lang_val = intent.slots.get('LanguagePreference')
            if lang_val and lang_val.value and 'telugu' in lang_val.value.lower():
                hi.attributes_manager.session_attributes['lang'] = 'te'
        except Exception:
            pass
        lang = _get_lang(hi)
        try:
            data   = _build_panchang_data(hi)
            speech = sp.build_daily_briefing(data, lang)
        except Exception as e:
            logger.error(e)
            speech = "I had trouble calculating today's panchang. Please try again."
        return _respond(hi, speech)


class TithiHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'TithiIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_tithi_response(data, lang))


class NakshatraHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'NakshatraIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_nakshatra_response(data, lang))


class YogaHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'YogaIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_yoga_response(data, lang))


class RahuKalamHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'RahuKalamIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_rahu_kalam_response(data, lang))


class YamagandamHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'YamagandamIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_yamagandam_response(data, lang))


class GulikaiHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'GulikaiIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_gulikai_response(data, lang))


class AbhijitHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'AbhijitIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_abhijit_response(data, lang))


class SunTimingsHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name == 'SunTimingsIntent')
    def handle(self, hi):
        lang = _get_lang(hi)
        data = _build_panchang_data(hi)
        return _respond(hi, sp.build_sun_timings_response(data, lang))


class HelpHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name in ('AMAZON.HelpIntent',))
    def handle(self, hi):
        return _respond(hi, sp.build_help_response(_get_lang(hi)))


class StopHandler(AbstractRequestHandler):
    def can_handle(self, hi):
        return (hi.request_envelope.request.object_type == 'IntentRequest'
                and hi.request_envelope.request.intent.name in ('AMAZON.StopIntent', 'AMAZON.CancelIntent'))
    def handle(self, hi):
        lang = _get_lang(hi)
        msg = 'శుభం. Goodbye!' if lang == 'te' else 'శుభం. Goodbye!'
        return _respond(hi, msg, end_session=True)


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, hi, exception): return True
    def handle(self, hi, exception):
        logger.error(exception, exc_info=True)
        return _respond(hi, "Sorry, I couldn't process that. Please try again.")


# ── Skill builder ──────────────────────────────────────────
sb = SkillBuilder()
for h in [LaunchHandler, DailyBriefingHandler, TithiHandler, NakshatraHandler,
          YogaHandler, RahuKalamHandler, YamagandamHandler, GulikaiHandler,
          AbhijitHandler, SunTimingsHandler, HelpHandler, StopHandler]:
    sb.add_request_handler(h())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
```

- [ ] **Step 2: Verify import works**

```bash
cd lambda && python -c "import lambda_function; print('lambda_function imports OK')" && cd ..
```

Expected: `lambda_function imports OK`

- [ ] **Step 3: Commit**

```bash
git add lambda/lambda_function.py
git commit -m "feat: add lambda_function with all Alexa SDK intent handlers"
```

---

### Task 8: Interaction Model + Skill Manifest

**Files:**
- Create: `skill-package/interactionModels/custom/en-IN.json`
- Create: `skill-package/skill.json`

- [ ] **Step 1: Create `skill-package/interactionModels/custom/en-IN.json`**

```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "telugu panchang",
      "intents": [
        {
          "name": "DailyBriefingIntent",
          "slots": [
            {"name": "LanguagePreference", "type": "LANGUAGE_PREF"}
          ],
          "samples": [
            "give me today's panchang",
            "tell me today's panchang",
            "what is today's panchang",
            "today's panchang",
            "tell me panchang in {LanguagePreference}",
            "give me panchang in {LanguagePreference}"
          ]
        },
        {
          "name": "TithiIntent",
          "slots": [],
          "samples": [
            "what is today's tithi",
            "today's tithi",
            "which tithi is today",
            "tell me the tithi"
          ]
        },
        {
          "name": "NakshatraIntent",
          "slots": [],
          "samples": [
            "what nakshatra is today",
            "today's nakshatra",
            "today's star",
            "which star is today"
          ]
        },
        {
          "name": "YogaIntent",
          "slots": [],
          "samples": [
            "what is today's yoga",
            "today's yoga"
          ]
        },
        {
          "name": "RahuKalamIntent",
          "slots": [],
          "samples": [
            "what is rahu kalam",
            "when is rahu kalam today",
            "rahu kalam today",
            "tell me rahu kalam"
          ]
        },
        {
          "name": "YamagandamIntent",
          "slots": [],
          "samples": [
            "when is yamagandam",
            "yamagandam today",
            "tell me yamagandam time"
          ]
        },
        {
          "name": "GulikaiIntent",
          "slots": [],
          "samples": [
            "when is gulikai kalam",
            "gulikai kalam today",
            "tell me gulikai"
          ]
        },
        {
          "name": "AbhijitIntent",
          "slots": [],
          "samples": [
            "what is abhijit muhurta",
            "best time today",
            "auspicious time today",
            "when is abhijit muhurta"
          ]
        },
        {
          "name": "SunTimingsIntent",
          "slots": [],
          "samples": [
            "what time is sunrise",
            "when does the sun set",
            "sunrise and sunset today",
            "tell me sunrise time",
            "when is sunset"
          ]
        },
        {"name": "AMAZON.HelpIntent",   "samples": []},
        {"name": "AMAZON.StopIntent",   "samples": []},
        {"name": "AMAZON.CancelIntent", "samples": []}
      ],
      "types": [
        {
          "name": "LANGUAGE_PREF",
          "values": [
            {"name": {"value": "Telugu",  "synonyms": ["telugu", "telugu language"]}},
            {"name": {"value": "English", "synonyms": ["english", "english language"]}}
          ]
        }
      ]
    }
  }
}
```

- [ ] **Step 2: Create `skill-package/skill.json`**

```json
{
  "manifest": {
    "publishingInformation": {
      "locales": {
        "en-IN": {
          "name": "Telugu Panchang",
          "summary": "Daily South Indian panchang — tithi, nakshatra, Rahu Kalam and more.",
          "description": "Get today's Telugu/Andhra panchang by voice. Hear the tithi, nakshatra, yoga, Rahu Kalam, Yamagandam, Gulikai Kalam, sunrise and sunset — in English or Telugu. Location-aware for accurate timings.",
          "examplePhrases": [
            "Alexa, open Telugu Panchang",
            "What is today's tithi?",
            "When is Rahu Kalam?"
          ],
          "keywords": ["panchang", "panchangam", "telugu", "hindu calendar", "rahu kalam", "tithi"]
        }
      },
      "isAvailableWorldwide": true,
      "testingInstructions": "Say 'open Telugu Panchang' to launch. Grant location permission when prompted.",
      "category": "EDUCATION_AND_REFERENCE"
    },
    "apis": {
      "custom": {
        "endpoint": {
          "sourceDir": "lambda"
        },
        "interfaces": [
          {"type": "ALEXA_PRESENTATION_APL"}
        ]
      }
    },
    "permissions": [
      {"name": "alexa::devices:all:geolocation:read"},
      {"name": "alexa::devices:all:address:full:read"}
    ],
    "privacyAndCompliance": {
      "allowsPurchases": false,
      "usesPersonalInfo": false,
      "isChildDirected": false,
      "isExportCompliant": true,
      "containsAds": false
    }
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add skill-package/
git commit -m "feat: add Alexa interaction model (en-IN) and skill manifest"
```

---

### Task 9: Package + Deploy

**Files:**
- Create: `Makefile` (optional helper)

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (typically ~12 tests total).

- [ ] **Step 2: Package the Lambda ZIP**

```bash
pip install -r lambda/requirements.txt -t package/
cp lambda/*.py package/
cd package && zip -r ../skill.zip . && cd ..
```

Expected: `skill.zip` created. Check size: `ls -lh skill.zip` — should be ~10–12 MB.

- [ ] **Step 3: Upload to AWS Lambda**

In AWS Console:
1. Create Lambda function: Runtime = Python 3.12, architecture = x86_64
2. Upload `skill.zip` via "Upload from ZIP"
3. Set handler to `lambda_function.lambda_handler`
4. Set timeout to 10 seconds, memory to 256 MB

- [ ] **Step 4: Link Lambda to Alexa Developer Console**

1. In Alexa Developer Console → Create Skill → Custom → Provision your own
2. Paste Lambda ARN into Endpoint field
3. Upload interaction model JSON from `skill-package/interactionModels/custom/en-IN.json`
4. Enable permissions: Alexa Location Services + Device Address

- [ ] **Step 5: Test in Alexa Developer Console simulator**

Open the Test tab. Type: `open telugu panchang`

Expected: Response speech includes today's tithi, nakshatra, masam, Rahu Kalam, sunrise time.

Type: `when is rahu kalam today`

Expected: Rahu Kalam time range spoken.

- [ ] **Step 6: Final commit**

```bash
git add Makefile skill.zip  # only if you created Makefile
git commit -m "feat: add deployment packaging — Telugu Panchang Alexa Skill complete

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
