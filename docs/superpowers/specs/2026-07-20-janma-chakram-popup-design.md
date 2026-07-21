# Janma Chakram Popup — Design Spec

**Date:** 2026-07-20  
**Status:** Approved

---

## Overview

Add a Janma Chakram (birth horoscope) popup to the Muhurtam app. When a user taps a person's profile card, a modal opens showing their full South Indian–style birth chart, critical birth details (Nakshatra, Rashi, Lagna), birth-time Panchang, and an option to export as PDF.

---

## Background

The Muhurtam page (`docs/muhoortam/index.html`) already holds profile cards with DOB, birth time, and birth place for each candidate. The backend already:

- Geocodes the birth place to `lat/lon/tz` via Nominatim
- Computes Janma Nakshatra (with padam), Janma Rashi, and Lagna in `compute/birth_chart.py`
- Has `compute_planet_rashis(jd)` in `compute/astro.py` for all 9 planet positions
- Has `compute_panchang(jd, lat, lon, tz)` for Tithi, Vara, Yoga, Karanam
- Renders a South Indian 4×4 horoscope grid via `renderHoroscopeChart()` in the frontend

This feature wires those existing pieces together into a popup, without introducing new dependencies.

---

## Scope

**In scope:**
- Extend `/muhoortam/birth-chart` API response with all 9 planet rashis and birth-time panchang
- Add Janma Chakram popup modal to `docs/muhoortam/index.html`
- PDF export via `window.print()` with print-scoped CSS
- Telugu + English bilingual labels (matching existing app style)

**Out of scope:**
- Dasha/Bhukti periods
- Compatibility matching (Porutham)
- Separate standalone Janma Chakram page

---

## Architecture

### Backend: `compute/birth_chart.py`

Extend `compute_birth_chart()` to call `compute_planet_rashis(jd)` and `compute_panchang(jd, lat, lon, tz_name)` at the birth Julian Day already computed in the function.

**New fields added to the return dict:**

```python
{
    # existing fields unchanged
    "janma_nakshatra_idx": int,
    "janma_nakshatra_te": str,
    "janma_nakshatra_padam": int,        # 1–4
    "janma_rashi_idx": int,
    "janma_rashi_te": str,
    "lagna_idx": int,
    "lagna_te": str,

    # NEW
    "planet_rashis": {
        "ravi": int, "chandra": int, "kuja": int,
        "budha": int, "guru": int, "shukra": int,
        "shani": int, "rahu": int, "ketu": int
    },
    "birth_panchang": {
        "tithi_te": str,
        "vaara_te": str,
        "nakshatra_te": str,     # same as janma_nakshatra_te, included for completeness
        "yoga_te": str,
        "karanam_te": str
    }
}
```

The `compute_panchang` return uses nested dicts (`tithi.te`, `vaaram.te`, `yoga.te`, `karana.te`); we extract the `te` (Telugu) string from each into the flat `birth_panchang` dict.  
The change is **additive** — no existing callers break.

### Backend: `handler_muhoortam.py`

No changes required. `_handle_birth_chart` passes through whatever `compute_birth_chart` returns.

### Frontend: `docs/muhoortam/index.html`

#### 1. Profile card tap handler

Each person's profile chip/card gets an `onclick` that calls `openJanmaChakram(personIdx)`.

The function:
1. Checks if `savedProfileCharts[id]` already has `planet_rashis` (cached from a prior call)
2. If not, calls `POST /muhoortam/birth-chart` with the profile's `dob`, `time`, `place` and caches the full response
3. Opens the `<dialog id="janmaChakramModal">` and renders the content

#### 2. Modal structure

```
┌─────────────────────────────────────────────┐
│  [×]  జన్మ చక్రం — <Name>                   │
│       DOB · Place                           │
├─────────────────────────────────────────────│
│  South Indian 4×4 chart (renderHoroscopeChart) │
│  (reuses existing grid — Lagna cell highlighted) │
├─────────────────────────────────────────────│
│  Nakshatra     Rashi        Lagna           │
│  రోహిణి 3వ    వృషభం        మేషం            │
├─────────────────────────────────────────────│
│  Birth Panchang strip                       │
│  తిథి: పంచమి  వారం: మంగళ  యోగం: సిద్ధి   │
│  కరణం: బవ                                  │
├─────────────────────────────────────────────│
│            [ 📄 Export PDF ]                │
└─────────────────────────────────────────────┘
```

The modal is a native `<dialog>` element. Clicking the backdrop or `[×]` closes it.

#### 3. PDF export

A `<style media="print">` block hides everything except `#janmaChakramModal`. The Export PDF button calls `window.print()`. The browser's native print dialog handles save-as-PDF.

No external libraries needed.

#### 4. Data caching

`savedProfileCharts[personId]` already exists in the frontend. After fetching, store the full enriched response (including `planet_rashis` and `birth_panchang`) so repeat opens don't make another API call.

---

## Data Flow

```
User taps profile card
       │
       ▼
openJanmaChakram(id)
       │
       ├─ cache hit? ──yes──► render modal
       │
       └─ no ──► POST /muhoortam/birth-chart
                    { dob, time, place }
                          │
                          ▼
                 compute_birth_chart()
                   ├── moon_longitude(jd)       → nakshatra, rashi
                   ├── compute_lagna(jd,lat,lon) → lagna
                   ├── compute_planet_rashis(jd) → 9 planet positions
                   └── compute_panchang(jd,...)  → tithi, vara, yoga, karanam
                          │
                          ▼
                 API response → cache → render modal
```

---

## Error Handling

- If the API call fails, show an inline error inside the modal ("చార్ట్ లోడ్ కాలేదు. మళ్ళీ ప్రయత్నించండి.")
- If `planet_rashis` is missing from a cached old response (backward compatibility), re-fetch

---

## Testing

- Extend `tests/test_muhoortam.py` to assert `planet_rashis` and `birth_panchang` are present in birth-chart response
- Verify all 9 planets present in `planet_rashis` dict
- Verify `birth_panchang` contains `tithi_te`, `vaara_te`, `yoga_te`, `karanam_te`
- Manual: open popup, verify chart renders, verify PDF print preview shows chart only
