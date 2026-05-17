# Telugu Panchang Alexa Skill — Design Spec

**Date:** 2026-05-17  
**Status:** Approved  
**Repo:** Separate GitHub repository (`telugu-panchang-alexa`)

---

## Problem Statement

An Amazon Alexa Skill that delivers daily Telugu Panchang information by voice. Users can ask for a full daily briefing or query specific fields (tithi, nakshatra, Rahu Kalam, etc.). The skill responds bilingually in English and Telugu, and computes panchang for the user's real device location.

---

## Approach

**PyEphem + Custom Panchang Math on AWS Lambda (Python)**

- Use the `ephem` library (PyPI) for sun/moon ecliptic longitude calculations.
- Custom Python panchang module computes all five classical limbs (tithi, nakshatra, yoga, karana, vara) plus South Indian timings (Rahu Kalam, Yamagandam, Gulikai) from the `ephem` positions.
- Hosted on AWS Lambda (Python 3.12), deployed via AWS SAM or the Alexa Developer Console ZIP upload.
- Accuracy: `ephem` is accurate to ±1–2 minutes on tithi/nakshatra transitions — sufficient for panchang purposes.

---

## Repository Structure

```
telugu-panchang-alexa/
├── lambda/
│   ├── lambda_function.py       ← Alexa SDK handler (entry point)
│   ├── panchang.py              ← Panchang calculation engine
│   ├── telugu_calendar.py       ← Telugu names, lookup tables
│   ├── south_indian.py          ← Rahu Kalam / Yamagandam / Gulikai
│   ├── geo.py                   ← Location resolution (Geolocation + Nominatim)
│   ├── speech.py                ← Speech text builders (EN + TE SSML)
│   └── requirements.txt         ← ephem, ask-sdk-core, requests
├── skill-package/
│   ├── interactionModels/
│   │   └── custom/
│   │       └── en-IN.json       ← Single en-IN interaction model (Telugu via LanguagePreference slot)
│   └── skill.json               ← Skill manifest
├── tests/
│   ├── test_panchang.py
│   ├── test_south_indian.py
│   └── test_speech.py
└── README.md
```

---

## Location Resolution

The skill resolves the user's coordinates at request time (not stored):

1. **Alexa Geolocation API** — available on Echo Auto and Alexa mobile app with location enabled. Gives precise `lat/lon`.
2. **Device Address API fallback** — if geolocation unavailable, request the device's postal address from the Alexa Address API, then reverse-geocode to `lat/lon` via Nominatim (`nominatim.openstreetmap.org`).
3. **Permission prompt** — if neither permission is granted, the skill sends a permissions card to the Alexa app and speaks: *"To give you accurate panchang, I need your location. Please enable it in the Alexa app."* Default fallback: Hyderabad (17.38°N, 78.48°E) with a spoken caveat.

The skill requests both `alexa::devices:all:geolocation:read` and `alexa::devices:all:address:full:read` permissions in `skill.json`.

---

## Voice Intents

| Intent | Sample Utterances | Response |
|---|---|---|
| `LaunchRequest` | "Open Telugu Panchang" | Full daily briefing (all fields) |
| `DailyBriefingIntent` | "Give me today's panchang", "Tell me panchang in Telugu" | Full daily briefing |
| `TithiIntent` | "What is today's tithi?", "నేడు తిథి ఏమిటి?" | Tithi name + end time |
| `NakshatraIntent` | "What nakshatra is today?", "Today's star" | Nakshatra name + end time |
| `YogaIntent` | "What is today's yoga?" | Yoga name |
| `RahuKalamIntent` | "What is Rahu Kalam?", "When is Rahu Kalam today?" | Time range + avoid-activities note |
| `YamagandamIntent` | "When is Yamagandam?" | Time range |
| `GulikaiIntent` | "When is Gulikai Kalam?" | Time range |
| `AbhijitIntent` | "What is Abhijit Muhurta?", "Best time today?" | Time range + auspicious note |
| `SunTimingsIntent` | "What time is sunrise?", "When does the sun set?" | Sunrise + sunset times |
| `AMAZON.HelpIntent` | "Help" | Lists all available queries |
| `AMAZON.StopIntent` | "Stop", "Exit", "Cancel" | "శుభం. Goodbye!" |

---

## Bilingual Response Strategy

Alexa does not support `te-IN` as a standalone locale. The skill uses a **single `en-IN` interaction model**. Language preference is detected from utterances via a `LanguagePreference` slot (values: `english`, `telugu`) and stored in session attributes for the session duration.

- User says **"in Telugu"** → `language_pref = "te"` stored in session; all subsequent responses in Telugu SSML
- User says **"in English"** (or no preference) → default English responses with Telugu terms inline

Telugu text is rendered using SSML `<lang xml:lang="te-IN">` tags. Where Alexa's TTS mispronounces Telugu words, `<phoneme>` tags provide pronunciation hints.

---

## Daily Briefing Speech Template

**English (en-IN):**
> "నమస్కారం! Today is {weekday}, {gregorian_date}. {masam} Masam, {paksham} Paksham, {rutuvu} Ritu. Tithi is {tithi}, Nakshatra is {nakshatra}, Yoga is {yoga}. Sunrise at {sunrise}, Sunset at {sunset}. Rahu Kalam is from {rahu_start} to {rahu_end}. Yamagandam from {yama_start} to {yama_end}. Abhijit Muhurta, the most auspicious time, is from {abhijit_start} to {abhijit_end}. What else would you like to know?"

**Telugu (te-IN):**
> "నమస్కారం! నేడు {weekday_te}, {gregorian_date}. {masam_te} మాసం, {paksham_te} పక్షం, {rutuvu_te} ఋతువు. తిథి {tithi_te}, నక్షత్రం {nakshatra_te}, యోగం {yoga_te}. సూర్యోదయం {sunrise}కి, సూర్యాస్తమయం {sunset}కి. రాహు కాలం {rahu_start} నుండి {rahu_end} వరకు. మీకు ఇంకేమైనా కావాలా?"

---

## Technical Architecture

### `panchang.py`
- `compute(dt: datetime, lat: float, lon: float) -> PanchangData`
- Uses `ephem.Sun()` and `ephem.Moon()` for ecliptic longitudes at given UTC time + location
- Returns dataclass with: `tithi, tithi_end, nakshatra, nakshatra_end, yoga, karana, vara`
- `tithi_end` and `nakshatra_end`: binary-search forward in time until longitude threshold is crossed

### `telugu_calendar.py`
- Lookup tables: 30 tithi names (EN + TE), 27 nakshatra names, 27 yoga names, 12 masam names, 6 rutuvu names, 60 samvatsara names, 7 vara names
- `get_masam(sun_lon)` → lunar month index from sun's zodiac position
- `get_rutuvu(sun_lon)` → season index from sun's zodiac position
- `get_paksham(tithi_num)` → "Shukla" / "Krishna"
- `get_samvatsara(year)` → 60-year cycle name

### `south_indian.py`
- Rahu Kalam slot table by weekday: `[8,2,7,5,6,3,4]` (Sun→Sat)
- Yamagandam slot table: `[5,4,3,2,1,7,6]`
- Gulikai slot table: `[6,5,4,3,2,1,7]`
- `get_rahu_kalam(weekday, sunrise, sunset)` → `(start: datetime, end: datetime)`
- `get_yamagandam(weekday, sunrise, sunset)` → `(start, end)`
- `get_gulikai(weekday, sunrise, sunset)` → `(start, end)`
- `get_abhijit_muhurta(sunrise, sunset)` → midday ± 24 min

### `geo.py`
- `resolve_location(handler_input) -> (lat, lon, city_name)`
- Checks geolocation coordinates first; falls back to device address + Nominatim geocoding
- Returns default Hyderabad coords if both fail

### `speech.py`
- `build_daily_briefing(data: PanchangData, locale: str) -> str` → SSML string
- `build_tithi_response(data, locale)`, `build_rahu_kalam_response(data, locale)`, etc.
- All responses end with a reprompt: *"What else would you like to know?"*

### `lambda_function.py`
- `ask_sdk_core` request handler classes, one per intent
- All handlers call `geo.resolve_location()` then `panchang.compute()` then the relevant `speech.*` builder
- Session attributes not used (stateless — each request is fully independent)

---

## Data Flow

```
Alexa Cloud → Lambda invocation
  ↓
geo.resolve_location()  ←── Alexa Geolocation API / Device Address API
  ↓
panchang.compute(now_utc, lat, lon)  ←── ephem sun/moon positions
TeluguCalendar lookups  ←── static tables
SouthIndian timings  ←── slot tables
  ↓
speech.build_*()  ←── locale-aware SSML
  ↓
Alexa response → spoken to user
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| No location permission | Sends permissions card; speaks fallback message; uses Hyderabad default |
| Nominatim geocoding fails | Uses raw coordinates; continues with panchang |
| `ephem` calculation error | Speaks: "I had trouble calculating today's panchang. Please try again." |
| Lambda timeout (>3s) | Pre-warm with Provisioned Concurrency if needed; typical execution ~200ms |

---

## Deployment

1. Package Lambda: `pip install -r requirements.txt -t package/ && zip -r skill.zip package/ lambda/`
2. Upload ZIP to AWS Lambda console or deploy via AWS SAM
3. Link Lambda ARN in Alexa Developer Console
4. Upload interaction models (`en-IN.json`, `te-IN.json`) to Alexa Developer Console
5. Enable permissions: Geolocation + Device Address in skill manifest

---

## Testing

- Unit tests in `tests/` cover `panchang.py`, `south_indian.py`, and `speech.py` with known date/location fixtures
- Run with: `pytest tests/ -v`
- Integration test: use Alexa Developer Console simulator or `ask dialog` CLI
