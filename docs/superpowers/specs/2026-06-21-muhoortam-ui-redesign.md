# Muhoortam UI Redesign — 3-Step Flow with Saved Profiles & Date Check

**Date:** 2026-06-21  
**Scope:** `docs/muhoortam/index.html` (frontend only) + deploy `/muhoortam/check` backend endpoint

---

## Overview

Redesign the Muhoortam wizard from a 4-panel flow into a clean 3-step flow:

1. **Step 1 — People** — enter/select person details, save profiles to localStorage
2. **Step 2 — Event** — ceremony type, location, and date selection (range OR single date check)
3. **Step 3 — Results** — auspicious date list (range) OR verdict card (single date)

The backend `/muhoortam/check` endpoint (already written, not yet deployed) is activated as part of this work.

---

## Step 1 — People (వ్యక్తుల వివరాలు)

### Saved Profiles
- Profiles persisted to `localStorage` key `muhurta_profiles`
- Each profile: `{ name, dob, time, place, birthChart }` where `birthChart` is the pre-computed JSON from `/muhoortam/birth-chart`
- Displayed as horizontal-scroll chip cards at the top of the panel: `"రాము · 🌟 రోహిణి 2వ పాదం"`
- Tapping a chip adds that person's data as a new person block (or fills the first empty one)
- A profile can be deleted via a ✕ on the chip (with confirmation)

### Person Blocks
- Same structure as current: Name, DOB (Flatpickr), Time, Place (Nominatim autocomplete)
- **💾 Save Profile** button per block: geocodes place, calls `/muhoortam/birth-chart`, stores result to localStorage
- Remove button (✕) on block (except if only 1 person)
- Up to 6 persons

### Navigation
- "← Back" is hidden on Step 1 (it's the first step)
- "తదుపరి →" validates all blocks (name + dob + time + place filled) then advances to Step 2

---

## Step 2 — Event Details (వేడుక వివరాలు)

### Ceremony Type
- Same 4 ceremony cards: వివాహం, గృహ ప్రవేశం, ఉపనయనం, పూజ
- Selection required to proceed

### Location
- Nominatim autocomplete (same as now)
- Required to proceed

### Date Selection — Toggle
A segmented toggle with two modes:

#### Mode A: Date Range (📅 తేదీ పరిధి)
- Two Flatpickr inputs: From / To
- **No `minDate` restriction** — past dates allowed (users can verify historical muhurtas)
- Default: today → today + 3 months
- Validation: From must be ≤ To

#### Mode B: Single Date Check (🔍 నిర్దిష్ట తేదీ తనిఖీ)
- One Flatpickr date picker (no date restriction)
- Optional `type="time"` field for time-specific check
- If time is given, result includes time-level verdict (in rahu kalam? varjyam? etc.)

### Navigation
- "← వెనక్కి" returns to Step 1 (all Step 1 values preserved)
- "ముహూర్తాలు వెతకండి 🔍" (range) or "తనిఖీ చేయండి ✓" (single) — button label changes with toggle

---

## Step 3 — Results

### Loading State
- Inline spinner replaces results area while fetching (same lotus loader)
- Progress bar for range mode (scanning month by month)

### Range Mode Results
- Existing muhurta result cards (date, nakshatra, best window, "వివరాలు చూడండి" bottom sheet)
- Birth chart summary panel at top (person name + nakshatra + padam)
- Empty state if no muhurtas found

### Single Date Check Results
- **Verdict card** at top:
  - ✅ `శుభ ముహూర్తం` (green) — day is auspicious AND time (if given) is clean
  - ⚠️ `మిశ్రమ ముహూర్తం` (amber) — day is auspicious BUT time falls in a bad window
  - ❌ `అశుభ ముహూర్తం` (red) — day-level rules fail
  - Shows date, vaaram, nakshatra, tithi, masam
- **అనుకూల అంశాలు** (green list) — good factors from backend
- **అననుకూల అంశాలు** (red list) — bad factors from backend
- **సమయ విశ్లేషణ** (time analysis) — if time was given, show which windows it falls in
- Kalam windows (Rahu, Yamaganda, Gulika) always shown
- Birth chart summary for each person (same chip row as range mode)

### Navigation (Step 3)
- "← వివరాలు మార్చండి" — goes back to Step 2, preserving all values
- "↺ కొత్తగా" — full reset, back to Step 1
- "🖨 PDF" — print

---

## Backend

### `/muhoortam/check` (POST) — already written, needs deployment
- Input: `{ date, time?, ceremony_place, ceremony_type, birth_charts[] }`
- Output: `{ verdict, overall_day_good, time_verdict, good_factors[], bad_factors[], time_issues[], date_te, vaaram_te, nakshatra_te, tithi_te, masam_te, sunrise, sunset, rahu_kalam, yamaganda, gulika_kalam, varjyam, dur_muhurtam }`
- Deployed via existing GitHub Actions workflow (triggers on `panchang-api/**` push)

### Birth chart pre-computation for saved profiles
- When user saves a profile, frontend calls `/muhoortam/birth-chart` and stores the result in localStorage alongside the personal details
- When profile is loaded for a check/find, the stored `birthChart` is passed directly — no re-computation needed
- If `birthChart` is missing from a saved profile (legacy), it is recomputed on use

---

## Data Flow

```
Step 1: Person fills blocks → [💾 Save] → localStorage.muhurta_profiles
         ↓ (Next)
Step 2: Ceremony + Location + Date mode
         ↓ (Find / Check)
Step 3 (Range):
  For each person: POST /muhoortam/birth-chart → birthChart[]
  For each month:  POST /muhoortam/find        → results[]
  Render result cards

Step 3 (Single date):
  For each person: POST /muhoortam/birth-chart → birthChart[]  (skip if pre-saved)
  POST /muhoortam/check → verdict + factors
  Render verdict card
```

---

## Step Bar

3 visible steps (replaces current 4):
- `1 — 2 — 3`
- Step 3 is active during both loading and results display

---

## Non-Goals (out of scope for this work)
- Cross-device profile sync
- Editing saved profiles (delete and re-add)
- More than 6 persons
- Exporting profiles
