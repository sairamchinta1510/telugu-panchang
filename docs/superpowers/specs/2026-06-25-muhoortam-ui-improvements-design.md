# Muhoortam UI Improvements — Design Spec
**Date:** 2026-06-25  
**Status:** Approved  
**Scope:** `docs/muhoortam/index.html` (frontend only)

---

## Overview

Four UI improvements to the muhoortam results page, focused on transparency (show calculations), clarity (windows across the full day), accessibility (bilingual), and navigation (breadcrumbs).

---

## Change 1 — Collapsible Score Breakdown (x/150)

### Problem
Each muhurtam window shows a score (e.g. 117/150) but users cannot see how it was calculated.

### Design
- Every muhurtam window card shows a score bar (`████░░ 117/150`) always visible.
- Below the score bar: a `<details>` / `<summary>` element labelled **"స్కోర్ వివరాలు ▾"** (Score Details).
- Clicking it expands a table with one row per scoring factor:

| Factor (Telugu) | Factor (English) | Delta |
|---|---|---|
| బేస్ స్కోర్ | Base score | +50 |
| గురు లగ్న దృష్టి | Jupiter aspects Lagna | +25 |
| స్థిర లగ్నం | Fixed Lagna | +25 |
| 7వ స్థానం శుభం | Clean 7th house | +10 |
| చంద్రుడు 8వ స్థానం | Moon in 8th house | −8 |
| **మొత్తం** | **Total** | **117/150** |

- Green rows for positive deltas, amber for negative, blue for total.
- Both Telugu and English shown on every row — no language toggle needed inside the table.
- Applies to: range-search result windows AND the single-day check result windows.

### Data source
`lagna_quality.score_components[]` from the API response — already returned per window. Each component has `te` (Telugu label) and `delta` (numeric).

---

## Change 2 — Date-Range Cards: Windows Across the Day

### Problem
Range-search result cards previously showed a single sunrise-time assessment. Users need to see all auspicious windows across the full day, when they occur, and their individual scores.

### Design

Each day result card has three zones stacked vertically:

#### Zone A — Day Timeline Breadcrumb
A horizontal bar from sunrise to sunset with coloured blocks showing where each muhurtam window falls.

```
05:26 ░░░▓▓░░░▓░░▓░░░░░░░░ 18:40
           ↑     ↑  ↑
        08:18  10:50 13:30
```

- Dark green block = best window (highest score).
- Light green blocks = other good windows.
- Labels show start time of each window inside/beside the block if space allows.
- Clicking a block scrolls to / highlights that window's card below.

#### Zone B — Best Window (Hero)
The highest-scoring window displayed prominently:
- Time range in large bold text.
- Lagna + Choghadiya on one line.
- Score bar + collapsible breakdown (Change 1 pattern).
- Tagged with ⭐ ఉత్తమ ముహూర్తం.

#### Zone C — Other Windows (Compact chips)
Remaining windows shown as compact horizontal chips:
- Format: `10:50–12:10 · సింహం · 94/150`
- Clicking a chip expands it to a full mini-card (same layout as hero, without the ⭐).

### Behaviour
- If only one window exists, show only Zone A (timeline) + Zone B (hero). No chips.
- If no windows exist for a day, the card is not shown in range results (existing behaviour).

### Data source
`good_windows[]` array per day — already returned by the API with `from`, `to`, `lagna_te`, `choghadiya_te`, `lagna_quality.score`, `lagna_quality.score_components`.

---

## Change 3 — App-Level తె / EN Language Toggle

### Problem
All result text is currently Telugu-only. Users unfamiliar with Telugu script cannot read the results.

### Design
- A `తె / EN` toggle switch placed in the **green top app header**, right-aligned.
- Default: **తె** (Telugu).
- Toggling to **EN** switches all dynamic result text in the entire page to English simultaneously.
- Static UI chrome (buttons, form labels) remains in Telugu — only panchang result values switch.

### Fields that switch language

| Telugu field | English equivalent |
|---|---|
| `vaaram_te` | Day of week in English (e.g. Friday) |
| `nakshatra_te` | Nakshatra name in English (e.g. Pushyami) |
| `tithi_te` | Tithi name in English (e.g. Panchami) |
| `yoga_te` | Yoga name in English |
| `masam_te` | Month name in English |
| `lagna_te` | Lagna name in English (e.g. Cancer) |
| `choghadiya_te` | Choghadiya quality in English |
| Score factor labels | English column always visible in the score table (Change 1) |
| `date_te` | `date_raw` formatted as "7 June 2019" |

### Implementation
- Store language preference in `localStorage` so it persists across page refreshes.
- All result-rendering functions read a global `window.appLang` variable (`'te'` or `'en'`).
- Toggle button updates `window.appLang` and re-renders the current results.
- API response already returns both `_te` and `_en` / raw fields — no backend change needed.

---

## Change 4 — Page-Level Breadcrumb Navigation

### Problem
The app has multiple views (landing form → range results → single-day check → detail). Users lose context of where they are and cannot navigate back easily.

### Design
A breadcrumb bar appears below the app header whenever the user is past the landing page:

```
🏠 Home  ›  Find Muhurtam  ›  Results: June 2019  ›  7 June 2019
```

- **Home** — always links back to the landing form (clears results).
- **Find Muhurtam / Check Muhurtam** — the search type used.
- **Results: [Month Year]** — clicking returns to the month results list.
- **[Date]** — current day detail (only shown when drilling into a specific day).

#### Breadcrumb rules
| View | Breadcrumb shown |
|---|---|
| Landing form | None |
| Range results | Home › Find Muhurtam › Results: June 2019 |
| Single-day check result | Home › Check Muhurtam › [Date] |
| Day detail (from range) | Home › Find Muhurtam › Results: June 2019 › [Date] |

- Each crumb except the last is clickable.
- Styled as small text below the header, separated by `›`.
- No extra page loads — all navigation is in-page state changes (existing SPA pattern).

---

## Files Changed

| File | Changes |
|---|---|
| `docs/muhoortam/index.html` | All four changes — JS rendering functions, CSS, toggle button in header, breadcrumb bar |

No backend changes required. All data needed is already returned by the API.

---

## Out of Scope
- Translating form labels, placeholders, or error messages to English.
- Server-side language switching.
- Adding new API fields.
