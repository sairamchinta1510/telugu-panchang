# Muhoortam — Telugu Muhurta Calculator
**Date:** 2026-06-21  
**Domain:** Muhoortam.Sanathanadharmas.com  
**Repo:** telugu-panchang (added alongside existing code — no changes to existing implementation)

---

## Overview

A Telugu-language muhurta calculator that accepts birth details for up to 6 people, a ceremony type and location, and returns a list of auspicious dates and time windows over the next 1 year. All output is in Telugu. Form inputs accept English text.

---

## User Journey — 4-Step Wizard

### Step 1 — వేడుక వివరాలు (Ceremony Details)
- User selects ceremony type (pill/chip buttons, one at a time):
  - వివాహం (Vivaha — Marriage)
  - గృహ ప్రవేశం (Gruha Pravesam — House Warming)
  - ఉపనయనం (Upanayanam — Thread Ceremony)
  - పూజ (Pooja)
- User enters ceremony location: city (text, English accepted) + country (text, English accepted)
- "తదుపరి →" button advances to Step 2

### Step 2 — జన్మ వివరాలు (Birth Details)
- Repeatable person block (minimum 1, maximum 6):
  - జన్మ తేదీ (Date of birth — DD/MM/YYYY)
  - జన్మ సమయం (Time of birth — HH:MM)
  - జన్మ స్థలం (Place of birth — city + country, English accepted)
- "+ మరో వ్యక్తిని జోడించండి" adds another person block
- "ముహూర్తాలు వెతకండి →" submits and advances to Step 3

### Step 3 — లెక్కింపు (Computing)
- Progress screen shown while frontend calls `/muhoortam/find` month by month (12 sequential calls)
- Shows: current month being scanned, progress bar (X/12 నెలలు పూర్తయ్యాయి)
- On completion, auto-advances to Step 4

### Step 4 — శుభ ముహూర్తాలు (Results)
- Summary line: "X శుభ ముహూర్తాలు దొరికాయి"
- Results table (all Telugu):

| తేదీ | వారం | సమయం | తిథి | నక్షత్రం | యోగం |
|------|------|------|------|----------|------|

- PDF download button ("PDF డౌన్లోడ్")
- "మళ్ళీ వెతకండి" button to restart wizard

---

## Architecture

### Principle
**No existing files are modified.** All new functionality is in new files only.

### New Files

```
telugu-panchang/
├── muhoortam/
│   └── index.html                          ← Telugu-only 4-step wizard UI
└── panchang-api/
    ├── compute/
    │   ├── birth_chart.py                  ← Birth chart computation
    │   ├── muhurta_rules.py                ← Ceremony rules + Panchaka dosha
    │   └── muhurta_finder.py              ← Date scanner (1 month at a time)
    └── handler_muhoortam.py               ← New Lambda handler (separate from handler.py)
```

### Technology
- Frontend: Plain HTML + vanilla JavaScript (same as existing `frontend/panchang.html`)
- Backend: Python AWS Lambda + swisseph (same as existing `panchang-api/`)
- Geocoding: OpenStreetMap Nominatim (free, no key required) to resolve city names → lat/lon/timezone

---

## Backend Modules

### `birth_chart.py`
Computes a person's birth chart from their date, time, and place of birth.

**Input:** `dob: str`, `time_of_birth: str`, `lat: float`, `lon: float`, `tz_name: str`

**Output:**
```json
{
  "janma_nakshatra_idx": 3,
  "janma_nakshatra_te": "రోహిణి",
  "janma_rashi_idx": 1,
  "janma_rashi_te": "వృషభం",
  "lagna_idx": 4,
  "lagna_te": "సింహం"
}
```

**Method:** Uses `swisseph` (already a dependency) to compute moon longitude at the exact birth moment → nakshatra index (0–26), rashi index (0–11), lagna (ascendant) index (0–11).

---

### `muhurta_rules.py`
Encodes ceremony-specific auspiciousness rules from South Indian Telugu tradition, verified against Venkatrama & Co. Telugu Panchangam (Rajahmundry edition), Muhurta Chintamani, and Dharmasindhu.

**Exports:**
- `is_auspicious(naks_idx, tithi_idx, sun_idx, lagna_idx, birth_charts, ceremony_type, masam_name, is_adhika_masam) -> bool`
- `compute_kalams(rise_mins, set_mins, sun_idx) -> dict` — Rahu Kalam, Yamaganda, Gulika windows

**Rules applied (in order):**

#### 1. Masa Shuddhi (Month Purity)
- **Adhika (intercalary) masa**: always forbidden for all samskaras (Dharmasindhu)
- **Chaturmas core months**: Ashadha, Shravana, Bhadrapada → rejected for Vivaha and Gruha Pravesam; Shravana + Bhadrapada → rejected for Upanayanam

#### 2. Good Nakshatras per Ceremony

| Ceremony | Auspicious Nakshatras | Key Notes |
|----------|-----------------------|-----------|
| వివాహం | రోహిణి, మృగశిర, మఘ, ఉత్తర ఫల్గుని, హస్త, స్వాతి, అనూరాధ, మూల*, ఉత్తరాషాఢ, ఉత్తరభాద్ర, రేవతి | **పుష్యమి నిషేధం** (PROHIBITED); "Three Uttaras" are primary |
| గృహ ప్రవేశం | రోహిణి, మృగశిర, పుష్యమి✓, ఉత్తర ఫల్గుని, హస్త, చిత్ర, స్వాతి, అనూరాధ, ఉత్తరాషాఢ, శ్రావణ, శతభిష, ఉత్తరభాద్ర, రేవతి | Ashlesha, Jyeshtha, Moola = **mula sankraman** — explicitly vetoed |
| ఉపనయనం | అశ్వని, రోహిణి, మృగశిర, పునర్వసు, పుష్యమి✓, ఉత్తర ఫల్గుని, హస్త, చిత్ర, స్వాతి, అనూరాధ, ఉత్తరాషాఢ, శ్రావణ, ధనిష్ఠ, శతభిష, ఉత్తరభాద్ర, రేవతి | Pushya is EXCELLENT for Upanayanam (Guru-Pushya Yoga) |
| పూజ | All of the above + Punarvasu, Magha | Only Amavasya hard-rejected |

*Moola 1st pada traditionally forbidden for marriage — first-pada check deferred to future iteration.

#### 3. Bad Tithis — Rikta Tithis (Core Rule)
Chaturthi, Navami, Chaturdashi in **both** Shukla and Krishna pakshas are universally inauspicious (Rikta = "empty"). Additionally: Ashtami Shukla and Purnima for Vivaha; Purnima for Gruha Pravesam; Amavasya for all.

#### 4. Tara Balam (Nakshatra Compatibility)
For each person, count from janma nakshatra to the day's nakshatra (1-indexed mod 27).
Inauspicious positions: 1 (Janma), 3 (Vipat), 5 (Pratyak), 7 (Naidhana).
A day is rejected if **any** person has an inauspicious tara.

#### 5. Panchaka Dosha (South Indian formula)
`(vaara + tithi + nakshatra + lagna) % 9`  — all **1-indexed**, tithi uses **full 1–30** (not mod-15).
- Safe remainders: 0, 3, 5, 7 (Panchaka Rahita — no dosha)
- Dosha remainders: 1=Mrityu, 2=Agni, 4=Raja, 6=Chora, 8=Roga
- Source: Astro-Engine/Astro_Engine_ORGNL `02_SOUTH_INDIAN_TRADITIONS.md`

#### 6. South Indian Kalam Periods (in output, not rejection criteria)
Every result day includes computed windows for:
- **రాహు కాలం** (Rahu Kalam): strictly avoid for all auspicious activities
- **యమగండ కాలం** (Yamaganda): strongly avoided in South India
- **గులిక కాలం** (Gulika Kalam): uniquely critical in Telugu/Tamil tradition — "any ceremony during Gulika repeats" (marriage → second marriage)

Day divided into 8 equal parts (sunrise→sunset). Segment per weekday:

| Weekday | Rahu | Yamaganda | Gulika |
|---------|------|-----------|--------|
| ఆదివారం (Sun) | 8th | 5th | 7th |
| సోమవారం (Mon) | 2nd | 4th | 6th |
| మంగళవారం (Tue) | 7th | 3rd | 5th |
| బుధవారం (Wed) | 5th | 2nd | 4th |
| గురువారం (Thu) | 6th | 1st | 3rd |
| శుక్రవారం (Fri) | 4th | 7th | 2nd |
| శనివారం (Sat) | 3rd | 6th | 1st |

Source: Venkatrama & Co. + `bidyashish/vedicpanchanga.com` verified tables.

---

### `muhurta_finder.py`
Scans a one-month window and returns all auspicious dates.

**Input:**
```json
{
  "year": 2026,
  "month": 7,
  "ceremony_lat": 17.38,
  "ceremony_lon": 78.46,
  "tz_name": "Asia/Kolkata",
  "ceremony_type": "vivaha",
  "birth_charts": [...]
}
```

**Method:**
1. For each calendar day in the month, call `compute_panchang()` (imported, not modified)
2. Pass result to `is_auspicious()`
3. If auspicious, compute the best time window (avoiding Dur Muhurtam and Varjyam)
4. Return list of matching days with Telugu-formatted output

**Output per matching day:**
```json
{
  "date_te": "15 జులై 2026",
  "vaaram_te": "గురువారం",
  "time_start": "08:15",
  "time_end": "10:30",
  "tithi_te": "పంచమి",
  "nakshatra_te": "రోహిణి",
  "yoga_te": "సౌభాగ్య"
}
```

---

### `handler_muhoortam.py`
New AWS Lambda handler, registered separately from `handler.py`.

**Endpoints:**

#### POST `/muhoortam/birth-chart`
Request: `{ "dob": "15/08/1990", "time": "10:30", "place": "Hyderabad, India" }`  
Response: birth chart dict (nakshatra, rashi, lagna in Telugu)

#### POST `/muhoortam/find`
Request: `{ "year": 2026, "month": 7, "ceremony_type": "vivaha", "ceremony_place": "Hyderabad, India", "birth_charts": [...] }`  
Response: list of auspicious day objects for that month

Both endpoints handle CORS and return JSON. Geocoding (place → lat/lon/tz) done via Nominatim at request time.

---

## Frontend — `muhoortam/index.html`

- Single HTML file, no build step, no framework
- Telugu labels throughout; inputs accept English text
- State machine: `currentStep` variable (1–4) drives which panel is visible
- Step 3 runs 12 sequential `fetch()` calls (one per month), updates progress bar, accumulates results
- Step 4 renders results table in Telugu; PDF generated client-side using `window.print()` with print-specific CSS
- Mobile-responsive via CSS flexbox/grid

---

## Geocoding

Place names (ceremony location, birth places) are resolved to lat/lon + IANA timezone using the **OpenStreetMap Nominatim API** (`https://nominatim.openstreetmap.org/search`). This is called from the Lambda backend (not the browser) to avoid CORS issues. No API key required.

---

## Testing

New test file: `panchang-api/tests/test_muhoortam.py`

- `test_birth_chart_known_person` — verify nakshatra/rashi/lagna for a known birth date
- `test_tara_balam_rejection` — verify inauspicious tara positions are rejected
- `test_panchaka_dosha` — verify the Panchaka formula rejects the right days
- `test_find_vivaha_muhurtas` — end-to-end scan returns expected results for a known month

---

## Out of Scope

- User accounts / saving results
- Email/WhatsApp sharing (PDF download is sufficient)
- Multi-language toggle (Telugu-only as specified)
- Horoscope matching (Ashtakoota) — only Tara Balam compatibility included in this version
