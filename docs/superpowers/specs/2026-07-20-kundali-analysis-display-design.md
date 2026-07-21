# Kundali Analysis Display — Design Spec
**Date:** 2026-07-20  
**Status:** Approved  
**Scope:** Frontend only — backend (`analysis.py`) is already complete and deployed.

---

## Overview

Display the new astrology analysis data (Navamsa D-9 chart, planet strength/nakshatra, Doshas, Graha Drishti, Parivartana Yogas) in the existing Kundali panel using Option B: Scroll Sections layout. All sections are always visible (no tabs), scrolling naturally. The Dasha accordion remains at the bottom.

---

## Layout — 6 Scroll Sections

Rendered inside `_renderKundaliBody()` in `docs/muhoortam/index.html`.

### Section 1 — 🗺 జన్మ చక్రాలు (Birth Charts)

Two charts side by side on desktop, stacked vertically on mobile (≤480px).

- **Left:** D-1 chart — existing `renderHoroscopeChart(chart.planet_rashis, chart.lagna_idx)`
- **Right:** D-9 chart — `renderHoroscopeChart(chart.navamsa_rashis, chart.navamsa_lagna_idx)`
  - `navamsa_lagna_idx` = `chart.planet_details.Lagna.navamsa_rashi_idx` (already in enriched data)
- Each chart has a Telugu label above it: "D-1 జన్మ చక్రం" / "D-9 నవాంశ చక్రం"

### Section 2 — 🪐 గ్రహ స్థితి (Planet Status)

Enhanced planet table. Columns:

| గ్రహం | రాశి | నక్షత్రం · పాద | నక్ష. స్వామి | బలం | D-9 రాశి |
|-------|------|----------------|--------------|-----|----------|

- **బలం** shown as a coloured badge:
  - `exalted` → "ఉచ్చ" (green)
  - `debilitated` → "నీచ" (red); append " వ" if retrograde
  - `own` → "స్వక్షేత్ర" (blue)
  - `moolatrikona` → "మూలత్రికోణ" (indigo)
  - `combust` → "అస్తమయ" (orange)
  - `normal` → "సాధారణ" (grey)
- Rows in order: రవి, చంద్ర, కుజ, బుధ, గురు, శుక్ర, శని, రాహు, కేతు, లగ్నం
- Retrograde (R) shown as small superscript "వ" after planet name
- On mobile: table scrolls horizontally with a "← స్వైప్" hint below

### Section 3 — జన్మ పంచాంగ (Birth Panchang)

Existing panchang strip — already rendered. No changes needed; just keep it as a section.

### Section 4 — ⚠️ దోషాలు & యోగాలు (Doshas & Yogas)

Three cards in a row on desktop, stacked on mobile:

1. **మాంగళిక దోషం** card
   - Red border + "🔴 మాంగళిక దోషం — Nth భావం" if `mangala_dosha.present === true`
   - Green border + "✅ మాంగళిక దోషం లేదు" if false
2. **కాళసర్ప దోషం** card
   - Red border + "🔴 కాళసర్ప దోషం — [type]" if `kala_sarpa_dosha.present === true`
   - Green border + "✅ కాళసర్ప దోషం లేదు" if false
3. **పరివర్తన యోగాలు** card
   - List each yoga: `[planet_a] ↔ [planet_b]` with type badge
     - `maha` → "మహా పరివర్తన" (gold)
     - `dainya` → "దైన్య పరివర్తన" (red)
     - `kahala` → "కహళ పరివర్తన" (grey)
   - "పరివర్తన యోగాలు లేవు" if empty array

### Section 5 — 👁 గ్రహ దృష్టి (Planetary Aspects)

Aspect pills — one pill per aspect, wrapping freely.

Format: `[from] → [to] [house]వ`

- Full 7th aspect: dark pill (`.asp-full`)
- Special aspects (4th, 5th, 8th, 9th, 3rd, 10th): gold-bordered pill (`.asp-special`)
- Planet names in Telugu abbreviations: రవి, చంద్ర, కుజ, బుధ, గురు, శుక్ర, శని, రా, కే

### Section 6 — ⏳ వింశోత్తరి దశలు (Dasha Accordion)

Existing dasha accordion — no structural changes. Current mahadasha auto-expanded. Each expanded mahadasha shows:
- Mini horoscope chart with that planet's rashi highlighted (yellow)
- Antardasha table with current antardasha row highlighted

---

## Responsive Breakpoints

```css
/* Desktop: charts side by side, dosha cards in a row */
@media (min-width: 481px) { .charts-row { flex-direction: row; } .dosha-row { flex-direction: row; } }

/* Mobile: charts stack, doshas stack, planet table scrolls */
@media (max-width: 480px) { .charts-row { flex-direction: column; } .dosha-row { flex-direction: column; } }
```

Planet table wrapped in `overflow-x: auto` div at all sizes; the `min-width` on the table ensures it doesn't collapse on mobile.

---

## Print / PDF

The new sections print naturally within `body.kundali-printing`. Additions:
- Section 4 (Doshas) gets `break-inside: avoid`
- Section 5 (Aspects) gets `break-inside: avoid`
- Section 2 planet table `break-inside: avoid`
- Aspect pills: font bumped to 10pt in print

No section forces a page break — the PDF already has `break-before: page` per `.dasha-row`.

---

## Data Sources (API Response Fields)

All fields already returned by `birth_chart.py`:

| Field | Used in Section |
|-------|----------------|
| `planet_rashis` | S1 D-1 chart |
| `navamsa_rashis` | S1 D-9 chart |
| `lagna_idx` | S1 both charts |
| `planet_details[p].navamsa_rashi_idx` | S1 D-9 lagna; S2 D-9 column |
| `planet_details[p].nakshatra_te`, `.nakshatra_pada`, `.nakshatra_lord` | S2 |
| `planet_details[p].strength`, `.retrograde` | S2 |
| `mangala_dosha` | S4 |
| `kala_sarpa_dosha` | S4 |
| `parivartana_yogas` | S4 |
| `graha_drishti` | S5 |
| `vimshottari_dasha` | S6 |
| `birth_panchang`, `janma_nakshatra_*`, `janma_rashi_*`, `lagna_*` | S3 |

---

## Files Changed

- `docs/muhoortam/index.html` — only file modified
  - `_renderKundaliBody()`: replace/extend with 6-section layout
  - Add CSS for new components (badges, dosha cards, aspect pills, charts-row)
  - Update `@media print` block

No backend changes required.

---

## Success Criteria

1. All 6 sections render with real API data when a Kundali is opened
2. No existing functionality broken (Muhurtam, People tab, existing Kundali chart, PDF)
3. D-9 chart displays correctly using `navamsa_rashis` data
4. Strength badges show correct Telugu labels with correct colours
5. Doshas show red (present) or green (absent)
6. On mobile (≤480px): charts stack, dosha cards stack, planet table scrolls horizontally
7. PDF includes all new sections without clipping
