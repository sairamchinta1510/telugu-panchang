# People Tab & Full Kundali Report — Design Spec

**Date:** 2026-07-20  
**Status:** Approved

## Overview

Add a dedicated "👥 జనాలు" (People) tab to the nav bar. The tab opens an unlimited profile book where users manage saved people. Each person has a full Kundali page showing: natal chart, planet positions with degrees, and a complete 120-year Vimshottari dasha accordion with highlighted mini charts per mahadasha.

---

## 1. People Tab — Nav Bar

Add a second nav button "👥 జనాలు" to the `<header class="site-nav">` alongside the existing language toggle. The active tab is highlighted gold (`background: var(--gold)`).

- **ముహూర్తం tab** → shows the existing ceremony planner panels (default/current behavior)
- **జనాలు tab** → shows the People panel, hides all ceremony panels

Tab state is managed in JS (`showTab('muhurtam' | 'people')`). URL hash may optionally reflect `#people`.

---

## 2. People Page

A new `#people-panel` div, hidden by default, shown when the People tab is active.

### Layout
- Title: "👥 నా జనాలు"
- Responsive card grid (2–4 cols)
- One card per saved profile
- A "＋ కొత్త వ్యక్తిని జోడించు" add-card (always last)

### Profile Card Contents
```
Name (bold)
DOB · Birth place
Nakshatra (padam) | Rashi | Lagna
[ 🪐 పూర్ణ కుండలి చూడండి ]   ← primary
[ + ముహూర్తంలో జోడించు ]      ← secondary
[ ✕ తొలగించు ]                ← small delete
```

### No Profile Limit
Unlike the muhurtam ceremony form (max 6 person blocks), the People profile store has **no limit**. Users can add as many people as they want. Profiles are stored in `localStorage` under the existing `PROFILES_KEY`.

### Add Person Form
Clicking "＋ కొత్త వ్యక్తిని జోడించు" expands an inline form on the card:
- Name (text)
- Date of birth (`<input type="date">`)
- Time of birth (`<input type="time">`)
- Birth place (text, required for Kundali)
- **Save** button → calls `/muhoortam/birth-chart`, stores profile (same flow as existing person-block save)

No redirect. On save, the add-card collapses and the new profile card appears.

### "ముహూర్తంలో జోడించు"
Copies the person into the ceremony planner (switches to ముహూర్తం tab, adds a person block pre-filled). Still subject to the 6-person muhurtam limit; if at limit, show an inline message.

---

## 3. Full Kundali Page

A new `#kundali-panel` div. Shown when user clicks "🪐 పూర్ణ కుండలి చూడండి" on a profile card.

### Header
```
← జనాలు  |  [Name] — పూర్ణ కుండలి       [ 📄 PDF ఎగుమతి ]
```

### Section 1 — Natal Chart + Planet Table

**Left:** Existing 4×4 South Indian natal chart (`renderHoroscopeChart()`).  
**Right:** Planet details table (9 rows):

| గ్రహం | రాశి | డిగ్రీ | వక్రి |
|-------|------|--------|-------|
| ☀️ రవి | కర్కాటక | 23°14' | — |
| 🌙 చంద్ర | వృషభం | 18°42' | — |
| ♂ కుజ | మేష | 07°55' | వ |
| … | … | … | … |

"వ" = వక్రి (retrograde). Degrees derived from `planet_details` response field.

**Below the table:** Birth panchang strip (existing: తిథి, వారం, నక్షత్రం, యోగం, కరణం).

### Section 2 — Vimshottari Dasha Accordion

Header: "వింశోత్తరి దశలు — 120 సంవత్సరాల పూర్ణ పట్టిక"

9 accordion rows, one per Mahadasha in sequence starting from birth. The row whose date range contains today is marked **"ప్రస్తుతం"** (red badge) and auto-expanded on load.

**Collapsed row:**
```
▶ [Planet emoji] [Lord] మహాదశ   [N సం.]  ·  DD/MM/YYYY – DD/MM/YYYY
```

**Expanded row:**
```
▼ [Planet emoji] [Lord] మహాదశ   [N సం.]  ·  DD/MM/YYYY – DD/MM/YYYY
┌─────────────────────────────────────────┐
│  Mini 4×4 chart                Antardasha table       │
│  (dasha lord cell              Lord–Lord  start  end  │
│   highlighted gold)            Lord–x     start  end  │
│                                …9 rows                │
└─────────────────────────────────────────┘
```

The mini chart is the same natal chart but the cell containing the dasha lord's rashi is highlighted gold (`background: #ffd700`).

Antardasha table: 9 rows (all 9 sub-period lords), each showing start and end date in DD/MM/YYYY format. The currently active antardasha (if within the current mahadasha) is highlighted.

### PDF Export
Button "📄 PDF ఎగుమతి" adds `body.kundali-printing` class, calls `window.print()`, removes class. Print CSS expands all accordions and hides nav/buttons. Scoped to avoid triggering on regular Ctrl+P.

---

## 4. Backend — Enhanced `/muhoortam/birth-chart` API

All additions are **additive** (new keys only; existing response keys unchanged).

### New response fields

```json
{
  "planet_details": {
    "ravi":    { "rashi_idx": 3, "deg": 23, "min": 14, "retrograde": false },
    "chandra": { "rashi_idx": 1, "deg": 18, "min": 42, "retrograde": false },
    "kuja":    { "rashi_idx": 0, "deg":  7, "min": 55, "retrograde": true  },
    "budha":   { ... },
    "guru":    { ... },
    "shukra":  { ... },
    "shani":   { ... },
    "rahu":    { ... },
    "ketu":    { ... }
  },
  "vimshottari_dasha": [
    {
      "lord":      "chandra",
      "lord_te":   "చంద్ర",
      "lord_emoji":"🌙",
      "years":     10,
      "start_date":"1990-08-15",
      "end_date":  "2000-08-14",
      "antardashas": [
        { "lord": "chandra", "lord_te": "చంద్ర", "start": "1990-08-15", "end": "1991-02-14" },
        { "lord": "kuja",    "lord_te": "కుజ",   "start": "1991-02-15", "end": "1991-09-14" },
        ...
      ]
    },
    ...
  ]
}
```

### New file: `panchang-api/compute/dasha.py`

```python
DASHA_SEQUENCE = ["ketu","shukra","ravi","chandra","kuja","rahu","guru","shani","budha"]
DASHA_YEARS    = { "ketu":7, "shukra":20, "ravi":6, "chandra":10,
                   "kuja":7, "rahu":18, "guru":16, "shani":19, "budha":17 }
DASHA_LORD_TE  = { ... }   # Telugu names
DASHA_EMOJI    = { ... }   # ☀️🌙♂☿♃♀♄☊☋

def compute_vimshottari_dasha(moon_lon: float, birth_datetime: datetime) -> list[dict]:
    """
    Compute full 120-year Vimshottari dasha sequence from birth.

    Args:
        moon_lon: Sidereal moon longitude at birth in degrees [0, 360)
        birth_datetime: Python datetime of birth (timezone-aware)

    Returns:
        List of 9 mahadasha dicts, each with start_date, end_date, antardashas list.
    """
```

**Algorithm:**
1. `nakshatra_idx = int(moon_lon / (360/27))` → 0–26
2. `lord_idx = nakshatra_idx % 9` → index into `DASHA_SEQUENCE`
3. `traversed_fraction = (moon_lon % (360/27)) / (360/27)`
4. `balance_years = (1 - traversed_fraction) × DASHA_YEARS[first_lord]`
5. First mahadasha: `start = birth_datetime`, `end = birth + balance_years`
6. Sequence remaining 8 mahadashas in order (wrapping), each full duration
7. For each mahadasha: compute 9 antardashas proportionally:
   - `antardasha_days = (maha_years × sub_years / 120) × 365.25`
   - sequence starts from the mahadasha lord itself, cycles through all 9

### Modified: `panchang-api/compute/birth_chart.py`

- Import `compute_planet_longitudes` from `.astro` (already exists)
- Import `compute_vimshottari_dasha` from `.dasha` (new)
- Build `planet_details` from longitudes: `rashi_idx = int(lon / 30)`, `deg = int(lon % 30)`, `min = int((lon % 1) * 60)`
- Retrograde: call `swe.calc_ut` with speed flag; speed < 0 means retrograde
- Append `planet_details` and `vimshottari_dasha` to response dict

### Tests

New `panchang-api/tests/test_dasha.py`:
- Nakshatra index from moon longitude
- Dasha balance calculation
- Full sequence length = 120 years
- Antardasha sub-period sum = mahadasha years
- Known birth: validate first lord and end date

Extended `test_muhoortam.py`:
- `planet_details` present in birth-chart response
- All 9 planets present with valid deg/min values
- `vimshottari_dasha` present with 9 entries

---

## 5. What Is NOT Changing

- Existing 🪐 popup (quick Kundali from Step 2 muhurtam form) — remains as-is
- Muhurtam ceremony form — max 6 person blocks unchanged
- Profile save/load format — existing `birthChart` field kept; new fields added alongside
- All existing API consumers — unaffected (additive only)

---

## 6. File Changelist

| File | Change |
|------|--------|
| `panchang-api/compute/dasha.py` | **New** — Vimshottari dasha computation |
| `panchang-api/compute/birth_chart.py` | **Modified** — add planet_details + vimshottari_dasha |
| `panchang-api/tests/test_dasha.py` | **New** — dasha unit tests |
| `panchang-api/tests/test_muhoortam.py` | **Modified** — new birth-chart response field tests |
| `docs/muhoortam/index.html` | **Modified** — People tab, People panel, Kundali panel |
