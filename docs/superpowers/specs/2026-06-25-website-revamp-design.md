# Telugu Muhurtam Website Revamp — Design Spec
**Date:** 2026-06-25  
**Scope:** Full layout and visual redesign of `docs/muhoortam/index.html`  
**Direction:** Option B — Clean & Modern, Deep Indigo

---

## 1. Goals

Replace the existing saffron/maroon gradient SPA with a clean, professional design that:
- Feels like a polished, trustworthy web product (not a personal project)
- Works for all audiences — Telugu-speaking diaspora worldwide, not just India
- Preserves full existing functionality (wizard flow, API calls, bilingual toggle, orrery)
- Passes a "first impression" test: a visitor who doesn't know the app should immediately understand what it does

---

## 2. Color System

| Token | Value | Usage |
|---|---|---|
| `--indigo` | `#4338CA` | Primary CTA buttons, active steps, accents |
| `--indigo-dark` | `#3730A3` | Button hover, hero gradient start |
| `--indigo-light` | `#E0E7FF` | Chip backgrounds, focus rings |
| `--indigo-xlight` | `#EEF2FF` | Card hover states, selected ceremony bg |
| `--amber` | `#D97706` | Choghadiya "Amrita" chip, score accent |
| `--amber-light` | `#FEF3C7` | Amber chip background |
| `--success` | `#059669` | ✓ Verified badge text |
| `--success-light` | `#D1FAE5` | ✓ Verified badge background |
| `--warning` | `#D97706` | ⚠ mismatch badge |
| `--warning-light` | `#FEF3C7` | ⚠ mismatch badge background |
| `--text` | `#111827` | Primary body text |
| `--text-2` | `#6B7280` | Secondary / labels |
| `--text-3` | `#9CA3AF` | Placeholder / disabled |
| `--border` | `#E5E7EB` | Card borders, dividers |
| `--surface` | `#FFFFFF` | Card backgrounds |
| `--bg` | `#F9FAFB` | Page background |

Saffron and maroon are fully retired. The orrery keeps its astronomy colours (amber sun, coloured planets).

---

## 3. Typography

| Use | Font | Weight |
|---|---|---|
| All English UI | `Inter`, `system-ui`, `sans-serif` | 400 / 500 / 600 / 700 / 800 |
| All Telugu text | `Noto Sans Telugu`, `sans-serif` | 400 / 600 / 700 |
| Code / numbers | inherit | — |

Load via Google Fonts: `Inter:wght@400;500;600;700;800` + `Noto+Sans+Telugu:wght@400;600;700`

---

## 4. Layout: Navigation Bar (sticky)

Fixed top bar, `56px` height, white background, 1px bottom border + subtle shadow.

**Left:** Logo mark (32×32px deep indigo rounded square with 🕉) + "Telugu **Muhurtam**" (brand word in indigo)  
**Right:** "Today's Panchang" text link (opens panchang tab/modal) + Language toggle pill (EN / తె)

Language toggle: two-segment pill, active segment gets indigo background + white text. Replaces the current floating toggle button.

---

## 5. Layout: Hero Section

Full-width indigo gradient banner (`#3730A3 → #4338CA → #6366F1`), displayed only on the landing view (before wizard starts).

**Left column (text):**
- Eyebrow: `TELUGU PANCHANGAM` (small caps, indigo-100 at 80% opacity)
- Headline (32px/800): "Find Your **Auspicious** Moment" — "Auspicious" in indigo-300 (`#A5B4FC`)
- Subtext (14px): "Precision muhurtam calculation rooted in Telugu Sampradaya. Validated against authentic Panchangams."
- Two buttons: `Find Muhurtam →` (white/indigo, solid) + `Today's Panchang` (ghost)

**Right column (orrery):**
- Existing CSS orrery animation, fixed bug: all planets orbit around a single shared centre (no margin offsets — use `transform: translate(-50%,-50%) rotate()` only on orbit divs, planet dots at `top:-radius; left:50%; margin-left:-radius`)
- Sun: amber radial-gradient + glow
- 3 orbits with 3 planets (keep existing planets: Mercury, Mars, Jupiter or similar)
- Caption: "Vedic Navagraha · Live Positions"

Hero is **hidden** once the wizard is in progress (step > 0). A breadcrumb/back link replaces it.

---

## 6. Layout: Wizard Container

Max-width `680px`, centred, padding `32px 16px 64px`. Page background `--bg`.

### 6a. Step Progress Indicator

4-step horizontal indicator shown on all wizard steps:

```
[1 Ceremony] ——— [2 Dates] ——— [3 Birth Details] ——— [4 Results]
```

- Circles: 36px diameter. Done = solid indigo + ✓. Active = solid indigo + 4px indigo-light ring. Todo = light gray.
- Labels below each circle (10px, hidden on mobile <380px).
- Connecting lines: 2px. Done segment = indigo. Todo segment = `--border`.

### 6b. Step 1 — Ceremony Selection

Card with:
- Title: "What ceremony are you planning?"
- Subtitle: "We'll apply the correct Vedic rules for your ceremony."
- 3×3 grid of ceremony buttons (2 cols on mobile). Each button: 1.5px border, 10px radius, ceremony emoji (24px) + English name (12px bold) + Telugu name (11px, Noto Sans Telugu).
- Selected state: indigo border + `--indigo-xlight` background + 2px outer ring.
- Primary button: "Next: Set Dates →"

Ceremonies (8 total, same as current): Vivaha, Gruha Pravesam, Upanayanam, Anna Prasana, Chelamu, Prayanam, Vidyarambham, Namakaranam.

### 6c. Step 2 — Dates & Location

Card with:
- "Ceremony Location" text input (full-width, geocoded on submit)
- Date row: Month selector + Scan mode (Full month / Specific date)
- If "Specific date" selected: date picker appears
- Primary button: "Next: Birth Details →"

### 6d. Step 3 — Birth Details

Same as current (per-person birth date/time/place for janma nakshatra). Each person rendered as a collapsible card. "Add person" button at bottom. Primary button: "Find Muhurtam →"

### 6e. Step 4 — Results

Results list header: "Found N auspicious dates for [Ceremony] in [Month] [Year], [City]" (13px, secondary text).

**Result day card** (per result):
- Left-border accent: 4px indigo (good score), lighter indigo (moderate), gray (borderline)
- Date line: weekday + full date (16px/700)
- Time line: "HH:MM – HH:MM AM" in indigo (13px/600)
- Chips row: nakshatra, tithi, lagna, choghadiya — all translated per current lang
- Right column: validation badge (✓ Verified / ⚠ Check Pandit) + score "NNN/150" + 5px score bar
- Full card is tappable → opens "More Details" overlay

"More Details" overlay (sheet from bottom, existing functionality retained):
- Header with ceremony name + date
- Score breakdown table (with English labels from new `en` field)
- Panchangam Cross-Check section (new, from validation task)
- Rahu Kalam / Yamaganda avoidance times
- Good muhurtam windows list

---

## 7. Component Library (reusable CSS classes)

| Class | Purpose |
|---|---|
| `.btn-primary` | Indigo filled button |
| `.btn-ghost` | Transparent + white border (on dark bg) |
| `.btn-outline` | Indigo border + transparent (on light bg) |
| `.chip` | Small indigo pill (nakshatra, tithi) |
| `.chip-amber` | Amber pill (Amrita choghadiya, best time) |
| `.chip-gray` | Gray pill (neutral info) |
| `.badge-verified` | Green ✓ Verified pill |
| `.badge-warning` | Amber ⚠ pill |
| `.card` | White surface, 16px radius, 1px border, subtle shadow |
| `.field` + `label` + `input`/`select` | Consistent form controls |
| `.step-circle` variants | Wizard step states |
| `.validation-badge` | From validation feature (already designed) |

---

## 8. Responsive Behaviour

| Breakpoint | Change |
|---|---|
| `< 640px` (mobile) | Hero stacks vertically (text top, orrery below, smaller); ceremony grid 2 cols; step labels hidden |
| `640px+` (tablet) | Hero side-by-side; ceremony grid 2–3 cols |
| `1000px+` (desktop) | Max-width containers centred; hero within `1100px` max |

---

## 9. What Is NOT Changing

- All JavaScript logic (wizard state machine, API calls, result rendering, breadcrumb nav)
- API integration (`/muhoortam/find`, `/panchang` endpoints)
- Bilingual data structures (`t()`, `teToEn()`, `_applyI18n()`)
- The 4-step wizard flow order
- The `index.html` single-file structure (no new files introduced)
- Validation badge feature (already designed in muhurtam-accuracy spec)

---

## 10. Implementation Approach

Full CSS replacement + HTML structure refactor within `docs/muhoortam/index.html`:

1. Replace entire `<style>` block with new design system
2. Rewrite HTML structure for nav, hero, wizard container, step indicator, cards
3. Update JS references to class names that changed (search-and-replace)
4. Preserve all JS logic verbatim — only the HTML scaffolding and CSS change
5. Test both EN and TE modes after refactor

The file will remain a single HTML file. No new assets, no build step.

---

## 11. Out of Scope

- Backend changes (this is purely a frontend redesign)
- Adding new pages beyond the SPA
- Dark mode
- PWA / offline support
- Analytics integration
