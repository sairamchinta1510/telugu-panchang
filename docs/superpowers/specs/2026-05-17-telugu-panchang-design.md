# Telugu Hindu Panchang — Dynamic Web Calendar Design

**Date:** 2026-05-17  
**Status:** Approved

---

## Problem Statement

Display a dynamic, accurate South Indian (Telugu/Andhra tradition) daily Panchang on a webpage. The page auto-detects the user's location via the browser, reads the current date/time, and computes all panchang fields in real time — no backend required.

---

## Approach

**SunCalc.js + Custom Panchang Math** (CDN + inline JS)

- Use the well-tested `SunCalc.js` library (loaded via CDN) for accurate sunrise/sunset and sun ecliptic longitude.
- Implement moon ecliptic longitude using simplified Jean Meeus astronomical algorithms (pure JS, no extra dependencies).
- Compute all panchang fields (tithi, nakshatra, yoga, karana) from sun/moon longitudes.
- Compute Rahu Kalam, Yamagandam, Gulikai from weekday + sunrise/sunset times using standard South Indian tables.
- Use the browser Geolocation API for coordinates; reverse-geocode to a city name using the free `nominatim.openstreetmap.org` API.

---

## Deliverable

A single standalone file: `panchang.html` (placed in the `frontend/` folder of the workday-agent project). All CSS and JS is inline or in sibling files referenced relatively. No build step required — open directly in a browser.

---

## Visual Design

**Layout:** Elegant vertical list, sectioned.  
**Color Theme:** Sandstone & Saffron
- Background: `#fdf6ec` (warm ivory)
- Header gradient: `#5d4037` → `#8d6e63` → `#d7a96b` (temple stone to saffron)
- Section headers: `#5d4037` (dark brown)
- Accent text: `#bf360c` (deep saffron/danger)
- Success/good: `#33691e` (forest green)
- Body text: `#3e2723`
- Card background: `#efebe9` (light sandstone)

**Language:** Telugu script + English bilingual labels throughout.

---

## Page Sections (in order)

### 1. Page Header
- 🕉 Om symbol
- Title: "Daily Panchang" / "నిత్య పంచాంగం"
- Sandstone-to-saffron gradient background

### 2. Location Bar
- Auto-detected city name (from Geolocation + Nominatim reverse geocode)
- Coordinates (lat/lon) and timezone abbreviation
- Shows "Detecting location…" while loading; falls back to "Location unavailable" with a manual coords note if permission denied

### 3. Calendar Info Section (`📅 Calendar · కాలమానం`)
| Field | Telugu | Description |
|---|---|---|
| Rutuvu | రుతువు | One of 6 Hindu seasons (Vasanta, Grishma, Varsha, Sharad, Hemanta, Shishira) — derived from solar longitude |
| Masam | మాసం | Telugu lunar month (Chaitra through Phalguna) — derived from sun's entry into zodiac signs |
| Paksham | పక్షం | Shukla (Waxing) or Krishna (Waning) — determined by current tithi number |

### 4. Panchangam Section (`☀️ Panchangam · పంచాంగం`)
The 5 classical limbs of the panchang:

| Field | Telugu | Calculation |
|---|---|---|
| Tithi | తిథి | `floor((moon_lon - sun_lon) / 12) + 1`, mod 30. Shows name + "until HH:MM" end time |
| Nakshatra | నక్షత్రం | `floor(moon_lon / (360/27))`. Shows name + end time |
| Yoga | యోగం | `floor((sun_lon + moon_lon) / (360/27)) mod 27` |
| Karana | కరణం | Half-tithi. `floor((moon_lon - sun_lon) / 6) mod 11` |
| Vara | వారం | Day of week in Telugu (ఆదివారం, సోమవారం …) |

### 5. Sun Timings Section (`🌅 Sun Timings · సూర్యోదయ అస్తమయం`)
| Field | Telugu | Source |
|---|---|---|
| Sunrise | సూర్యోదయం | SunCalc.getTimes() |
| Sunset | సూర్యాస్తమయం | SunCalc.getTimes() |
| Abhijit Muhurta | అభిజిత్ ముహూర్తం | Midday ± 24 min (8th muhurta of day) |

### 6. Inauspicious Periods Section (`⚠️ Inauspicious Periods · అశుభ సమయాలు`)

All three are computed from the **day duration** (sunrise to sunset, divided into 8 equal slots) using fixed South Indian weekday tables:

**Rahu Kalam** (రాహు కాలం) — by weekday:
| Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|-----|-----|-----|-----|-----|-----|-----|
| 8th | 2nd | 7th | 5th | 6th | 3rd | 4th |

**Yamagandam** (యమగండం) — by weekday:
| Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|-----|-----|-----|-----|-----|-----|-----|
| 5th | 4th | 3rd | 2nd | 1st | 7th | 6th |

**Gulikai Kalam** (గులికై కాలం) — by weekday:
| Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|-----|-----|-----|-----|-----|-----|-----|
| 6th | 5th | 4th | 3rd | 2nd | 1st | 7th |

Each slot = `(sunset - sunrise) / 8`. Slot N starts at `sunrise + (N-1) × slot_duration`.

Footer note: "Avoid starting important activities during these periods."

---

## Technical Architecture

The single `panchang.html` file organises its JavaScript into clearly separated IIFE modules:

### `Geo` module
- Calls `navigator.geolocation.getCurrentPosition()`
- On success: stores lat/lon, calls Nominatim for city name
- On failure: stores null coordinates, shows graceful error
- Nominatim call: `https://nominatim.openstreetmap.org/reverse?lat=X&lon=Y&format=json`

### `Astro` module
- Depends on `SunCalc` (loaded via CDN: `https://unpkg.com/suncalc@1.9.0/suncalc.js`) — used **only** for `getTimes()` (sunrise/sunset). SunCalc provides altitude/azimuth, not ecliptic longitude.
- `getJulianDay(date)` → Julian Day Number helper
- `getSunLongitude(jd)` → sun ecliptic longitude (°0–360) computed from JD using low-precision Meeus Ch.25 solar formula (accurate to ~0.01°)
- `getMoonLongitude(jd)` → moon ecliptic longitude (°0–360) using simplified Meeus Ch.47 formulas (accurate to ~0.3°)

### `Panchang` module
- `compute(date, lat, lon)` → returns object with all fields
- Calls `Astro` for sun/moon longitudes
- Returns: `{ tithi, tithiEnd, nakshatra, nakshatraEnd, yoga, karana, vara }`

### `TeluguCalendar` module
- Static lookup tables: Telugu month names, Samvatsara cycle (60 years), Rutuvu ranges, Vara names in Telugu
- `getMasam(sunLon)` → Telugu month from sun's zodiac position
- `getRutuvu(sunLon)` → Season from sun's zodiac position
- `getPaksham(tithiNum)` → "Shukla" (1–15) or "Krishna" (16–30)
- `getSamvatsara(year)` → returns name from 60-year cycle

### `SouthIndian` module
- `getRahuKalam(weekday, sunrise, sunset)` → `{ start, end }` Date objects
- `getYamagandam(weekday, sunrise, sunset)` → `{ start, end }`
- `getGulikai(weekday, sunrise, sunset)` → `{ start, end }`
- `getAbhijitMuhurta(sunrise, sunset)` → `{ start, end }` (midday ± 24 min)

### `UI` module
- `render(data)` → populates all DOM elements
- Shows skeleton/loading state while Geolocation is pending
- Formats all times as `H:MM AM/PM`
- Refreshes at midnight (setTimeout to next midnight)

---

## Data Flow

```
Page Load
  ↓
Geo.detect()  ←── navigator.geolocation
  ↓
Astro.compute(date, lat, lon)  ←── SunCalc.js
  ↓
Panchang.compute()  ←── moon longitude formulas
TeluguCalendar.compute()  ←── lookup tables
SouthIndian.compute()  ←── weekday + slot tables
  ↓
UI.render(allData)  ←── DOM update
  ↓
setTimeout(refresh, msUntilMidnight)
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Geolocation denied | Show "📍 Location unavailable. Panchang shown for UTC+5:30." Use lat=17.38, lon=78.48 (Hyderabad) as default |
| Nominatim fails | Show raw coordinates instead of city name |
| SunCalc CDN unreachable | Show error banner: "Could not load astronomy library. Check internet connection." |
| Midnight rollover | Page auto-refreshes panchang data silently |

---

## File Structure

```
frontend/
  panchang.html      ← standalone page (all CSS + JS inline)
```

The page is self-contained. No npm, no build step, no server required.

---

## Telugu Name Reference Tables

**6 Rutuvu (Seasons):**
Vasanta (వసంత) · Grishma (గ్రీష్మ) · Varsha (వర్ష) · Sharad (శరత్) · Hemanta (హేమంత) · Shishira (శిశిర)

**12 Masam (Months):**
Chaitra · Vaishakha · Jyeshtha · Ashadha · Shravana · Bhadrapada · Ashvina · Kartika · Margashirsha · Pausha · Magha · Phalguna

**30 Tithi names:** Pratipada through Amavasya (30th), with Purnima at 15th.

**27 Nakshatra names:** Ashvini through Revati.

**27 Yoga names:** Vishkambha through Vaidhrti.

**11 Karana names** (repeating): Bava, Balava, Kaulava, Taitila, Garaja, Vanija, Vishti + 4 fixed (Shakuni, Chatushpada, Naga, Kimstughna).
