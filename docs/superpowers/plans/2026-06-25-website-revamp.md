# Telugu Muhurtam Website Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Telugu Muhurtam SPA from its current saffron/maroon style to a clean, professional Deep Indigo design (Option B) with a hero landing section, improved navigation, and refined ceremony icons.

**Architecture:** All changes are within `docs/muhoortam/index.html` only — replace the `<style>` block wholesale, update HTML structure for nav/hero/step-bar, and make minimal JS additions (hero show/hide). All existing JavaScript logic and IDs are preserved unchanged. No new files are created.

**Tech Stack:** Vanilla HTML/CSS/JS, Google Fonts (Inter + Noto Sans Telugu), deployed via GitHub Pages.

---

## File Map

| File | What Changes |
|---|---|
| `docs/muhoortam/index.html` | Entire `<style>` block replaced; `<head>` fonts/meta updated; nav HTML replaced; `#hero` section added; `.step-bar` HTML updated with labels; ceremony icon emojis updated; `setStep()` + `resetWizard()` updated to show/hide hero |

---

## Task 1: CSS Variables, Typography, and Global Reset

**Files:**
- Modify: `docs/muhoortam/index.html` — `<style>` block opening, `:root`, `body`, `@keyframes`

### Background

The current CSS uses `--saffron`, `--maroon`, `--cream`, `--brown` etc. These must all be replaced with the Deep Indigo design tokens. The `body` currently has `max-width: 560px; margin: 0 auto` which prevents full-width nav/hero — this must move to the panels instead.

The new Google Fonts import: **Inter** (UI) + **Noto Sans Telugu** (Telugu text).

- [ ] **Step 1: Update the Google Fonts import in `<head>`**

Find and replace:
```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Telugu:wght@400;600;700&family=Noto+Serif+Telugu:wght@600;700&display=swap" rel="stylesheet">
```
With:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Telugu:wght@400;600;700&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Update `<title>` and `theme-color` meta**

Find:
```html
<meta name="theme-color" content="#7B1E0A">
<title>శుభ ముహూర్తం</title>
```
Replace with:
```html
<meta name="theme-color" content="#4338CA">
<title>Telugu Muhurtam — Shubha Muhurtam Calculator</title>
```

- [ ] **Step 3: Replace the `:root` CSS variables**

Find the entire `:root { ... }` block (currently ends with `--transition`). Replace with:

```css
:root {
  --indigo:       #4338CA;
  --indigo-dark:  #3730A3;
  --indigo-light: #E0E7FF;
  --indigo-xl:    #EEF2FF;
  --amber:        #D97706;
  --amber-light:  #FEF3C7;
  --success:      #059669;
  --success-bg:   #D1FAE5;
  --warning:      #D97706;
  --warning-bg:   #FEF3C7;
  --text:         #111827;
  --text-2:       #6B7280;
  --text-3:       #9CA3AF;
  --border:       #E5E7EB;
  --surface:      #FFFFFF;
  --bg:           #F9FAFB;
  --radius:       12px;
  --radius-sm:    8px;
  --shadow:       0 2px 12px rgba(67,56,202,0.07);
  --shadow-lg:    0 8px 32px rgba(67,56,202,0.12);
  --transition:   0.2s cubic-bezier(0.4,0,0.2,1);
}
```

- [ ] **Step 4: Replace `body` global styles**

Find the `body { ... }` block (currently has `font-family: Noto Sans Telugu`, `background: var(--cream)`, `max-width: 560px`). Replace with:

```css
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}
```

> **Important:** The old body had `max-width: 560px; margin: 0 auto`. Removing this allows the nav and hero to be full-width. We will add `max-width: 680px; margin: 0 auto; padding: 0 16px` to the panels in Task 5.

- [ ] **Step 5: Replace error toast and generic animation CSS**

Find the `.error-toast` and `@keyframes fadeIn` blocks. Replace with:

```css
.error-toast {
  display: none;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #991B1B;
  border-radius: var(--radius-sm);
  padding: 10px 16px;
  font-size: 0.85rem;
  font-weight: 500;
  margin: 0 16px 12px;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.panel { display: none; }
.panel.active { display: block; animation: fadeIn 0.25s ease; }
```

- [ ] **Step 6: Verify the page still loads without visual explosion**

Open `docs/muhoortam/index.html` directly in a browser (file:// or local server). The page will look broken/unstyled — that is expected at this stage since most CSS classes are undefined. Confirm no JS console errors.

- [ ] **Step 7: Commit**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "style: replace CSS variables and global reset with Deep Indigo design tokens

- New :root tokens: --indigo, --indigo-dark, --indigo-light, --indigo-xl
- Remove max-width from body (moved to panels later)
- Replace Google Fonts: add Inter, keep Noto Sans Telugu
- Update title and theme-color meta

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 2: Navigation Bar

**Files:**
- Modify: `docs/muhoortam/index.html` — HTML for `.header` section + CSS for nav

### Background

The current `.header` is a saffron gradient banner with the 🕉 symbol, title, and a floating lang toggle button. This becomes a clean sticky white nav bar with:
- Left: logo mark + brand name
- Right: language toggle pill (two-segment, not a slider)

The breadcrumb `<nav id="breadcrumb">` is kept as-is structurally (JS writes into it) but restyled.

- [ ] **Step 1: Replace the header HTML**

Find the entire `<!-- ══ HEADER ══ -->` section:
```html
<!-- ══ HEADER ══ -->
<div class="header">
  <button type="button" class="lang-toggle" id="langToggle" onclick="toggleLang()" title="Switch language / భాష మార్చండి" aria-label="Language toggle">
    <span id="langLabel">తె</span>
    <span class="track"><span class="thumb"></span></span>
    <span>EN</span>
  </button>
  <div class="header-om">🕉</div>
  <h1 data-te="శుభ ముహూర్తం" data-en="Shubha Muhoortam">శుభ ముహూర్తం</h1>
  <div class="sub">Muhoortam.Sanathanadharmas.com</div>
</div>
<nav id="breadcrumb" aria-label="breadcrumb"></nav>
```

Replace with:
```html
<!-- ══ NAV ══ -->
<header class="site-nav">
  <div class="nav-logo">
    <div class="nav-logo-mark">🕉</div>
    <div class="nav-logo-text">Telugu <span>Muhurtam</span></div>
  </div>
  <div class="nav-right">
    <button
      type="button"
      class="lang-toggle"
      id="langToggle"
      onclick="toggleLang()"
      title="Switch language / భాష మార్చండి"
      aria-label="Language toggle">
      <span id="langLabel-te" class="lang-seg active">తె</span>
      <span id="langLabel-en" class="lang-seg">EN</span>
    </button>
  </div>
</header>
<nav id="breadcrumb" aria-label="breadcrumb"></nav>
```

- [ ] **Step 2: Replace nav + breadcrumb CSS**

Remove all old `.header`, `.header::before`, `.header-om`, `.header h1`, `.header .sub`, `.lang-toggle`, `.lang-toggle .track`, `.lang-toggle .thumb` CSS blocks.

Add the following CSS instead (insert after the `@keyframes fadeIn` block):

```css
/* ════════════════════════════════
   NAVIGATION
════════════════════════════════ */
.site-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 56px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 200;
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-logo-mark {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--indigo-dark), var(--indigo));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
}
.nav-logo-text {
  font-weight: 700;
  font-size: 15px;
  color: var(--text);
  font-family: 'Inter', system-ui, sans-serif;
}
.nav-logo-text span { color: var(--indigo); }

.lang-toggle {
  display: flex;
  background: var(--indigo-xl);
  border: 1.5px solid var(--indigo-light);
  border-radius: 20px;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
}
.lang-seg {
  padding: 5px 13px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-2);
  transition: all var(--transition);
  line-height: 1;
  font-family: 'Inter', system-ui, sans-serif;
}
.lang-seg.active {
  background: var(--indigo);
  color: #fff;
  border-radius: 20px;
}
.lang-toggle:hover { background: var(--indigo-light); }

/* Breadcrumb */
#breadcrumb {
  display: none;
  padding: 7px 20px;
  font-size: 0.72rem;
  color: var(--text-2);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 2px;
  align-items: center;
}
#breadcrumb a, #breadcrumb .bc-link {
  color: var(--indigo);
  text-decoration: none;
  font-weight: 600;
  background: none; border: none; padding: 0; cursor: pointer;
  font-size: inherit; font-family: inherit;
}
#breadcrumb a:hover, #breadcrumb .bc-link:hover { text-decoration: underline; }
#breadcrumb .sep, #breadcrumb .bc-sep { color: var(--text-3); margin: 0 4px; }
#breadcrumb .bc-current { color: var(--text-2); font-weight: 600; }
```

- [ ] **Step 3: Update `toggleLang()` JS — new segment pill logic**

The new lang toggle has two `<span>` elements with class `lang-seg` instead of a slider thumb. Find `toggleLang()` and update the toggle logic:

Find:
```js
  document.getElementById('langToggle').classList.toggle('en', APP_LANG === 'en');
  document.getElementById('langLabel').textContent = APP_LANG === 'te' ? 'తె' : 'EN';
```

Replace with:
```js
  document.getElementById('langLabel-te').classList.toggle('active', APP_LANG === 'te');
  document.getElementById('langLabel-en').classList.toggle('active', APP_LANG === 'en');
```

- [ ] **Step 4: Also update the initial language application (page load)**

Find the section near the end of the `<script>` block that applies the initial language on page load (it calls `_applyI18n()` or sets `langLabel`). Update it to also set the pill:

Find any occurrence of:
```js
document.getElementById('langLabel').textContent
```
(there may be one in the `_applyI18n` or initial setup). Replace with the same two-segment logic from Step 3.

Then also find the `_applyI18n` function or initial lang setup block where `langToggle` class is set, and update it similarly:
```js
  document.getElementById('langLabel-te').classList.toggle('active', APP_LANG === 'te');
  document.getElementById('langLabel-en').classList.toggle('active', APP_LANG === 'en');
```

- [ ] **Step 5: Verify nav looks correct**

Open the file in a browser. You should see:
- White sticky nav bar at top
- 🕉 indigo logo mark on the left + "Telugu **Muhurtam**" text
- Two-segment language pill on the right (active segment indigo, inactive gray)
- Clicking the pill switches between తె and EN

- [ ] **Step 6: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign navigation bar with sticky white nav + indigo language pill

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 3: Hero Section

**Files:**
- Modify: `docs/muhoortam/index.html` — add `#hero` HTML after `<nav id="breadcrumb">`, add hero CSS, update `setStep()` and `resetWizard()`

### Background

The hero is a full-width indigo gradient banner shown only when step 1 is active (landing view). It has text on the left and a decorative orrery on the right. When the user advances to step 2 or 3, `setStep()` hides it.

- [ ] **Step 1: Add hero HTML**

Immediately after `<nav id="breadcrumb" aria-label="breadcrumb"></nav>`, insert:

```html
<!-- ══ HERO (shown on step 1 only) ══ -->
<div id="hero" class="hero-section">
  <div class="hero-inner">
    <div class="hero-text">
      <div class="hero-eyebrow" data-te="తెలుగు పంచాంగం" data-en="Telugu Panchangam">తెలుగు పంచాంగం</div>
      <h1 class="hero-title" data-te="శుభ ముహూర్తం" data-en="Find Your Auspicious Moment">శుభ ముహూర్తం</h1>
      <p class="hero-sub" data-te="తెలుగు సంప్రదాయం ప్రకారం ఖచ్చితమైన ముహూర్త గణన" data-en="Precision muhurtam calculation rooted in Telugu Sampradaya — validated against authentic Panchangams">తెలుగు సంప్రదాయం ప్రకారం ఖచ్చితమైన ముహూర్త గణన</p>
    </div>
    <div class="hero-orrery" aria-hidden="true">
      <div class="nava-graha-orrery hero-orrery-inner">
        <div class="graha-sun">సూర్య</div>
        <div class="graha-orbit g-chandra" data-name="చంద్ర"></div>
        <div class="graha-orbit g-budha"   data-name="బుధ"></div>
        <div class="graha-orbit g-shukra"  data-name="శుక్ర"></div>
        <div class="graha-orbit g-kuja"    data-name="కుజ"></div>
        <div class="graha-orbit g-guru"    data-name="గురు"></div>
        <div class="graha-orbit g-shani"   data-name="శని"></div>
        <div class="graha-orbit g-rahu"    data-name="రాహు"></div>
        <div class="graha-orbit g-ketu"    data-name="కేతు"></div>
      </div>
      <div class="hero-orrery-caption" data-te="నవగ్రహ స్థానాలు" data-en="Navagraha Positions">నవగ్రహ స్థానాలు</div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Add hero CSS**

Insert after the breadcrumb CSS block:

```css
/* ════════════════════════════════
   HERO
════════════════════════════════ */
.hero-section {
  background: linear-gradient(135deg, var(--indigo-dark) 0%, var(--indigo) 60%, #6366F1 100%);
  padding: 40px 20px 48px;
}
.hero-inner {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  align-items: center;
}
.hero-eyebrow {
  color: rgba(224,231,255,0.8);
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 10px;
  font-family: 'Inter', system-ui, sans-serif;
}
.hero-title {
  font-family: 'Noto Sans Telugu', 'Inter', system-ui, sans-serif;
  color: #fff;
  font-size: 1.9rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 10px;
}
.hero-sub {
  color: rgba(255,255,255,0.75);
  font-size: 0.88rem;
  line-height: 1.6;
  max-width: 400px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.hero-orrery {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.hero-orrery-inner {
  width: 200px;
  height: 200px;
  margin: 0;
}
.hero-orrery-caption {
  color: rgba(255,255,255,0.45);
  font-size: 10px;
  text-align: center;
  font-family: 'Inter', system-ui, sans-serif;
}
@media (max-width: 560px) {
  .hero-inner { grid-template-columns: 1fr; }
  .hero-orrery { display: none; }
  .hero-title { font-size: 1.5rem; }
}
```

- [ ] **Step 3: Update the orrery CSS to work on dark background**

The existing `.graha-orbit` uses `border: 1px dashed rgba(196,154,108,0.25)` (warm amber, invisible on dark). Update to work on both light (loading area) and dark (hero) backgrounds. Find:

```css
  border: 1px dashed rgba(196,154,108,0.25);
```
Replace with:
```css
  border: 1px dashed rgba(255,255,255,0.18);
```

Also update the loading area background: find `.loading-wrap` or the `nava-graha-orrery` container CSS and ensure it has a light/neutral background:

Find the `.nava-graha-orrery` CSS block and update:
```css
.nava-graha-orrery {
  width: 220px; height: 220px;
  margin: 0 auto 14px;
  position: relative;
}
```
(This is unchanged — add `position: relative` if not already there.)

- [ ] **Step 4: Update `setStep()` to show/hide hero**

In the `setStep(n)` function, add hero visibility control. Find:

```js
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.getElementById("panel"+n).classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (n === 1) { _navStack = []; renderBreadcrumb(); }
```

Replace with:

```js
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.getElementById("panel"+n).classList.add("active");
  const hero = document.getElementById("hero");
  if (hero) hero.style.display = (n === 1) ? "" : "none";
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (n === 1) { _navStack = []; renderBreadcrumb(); }
```

- [ ] **Step 5: Verify hero renders correctly**

Open in browser. On load (step 1): indigo gradient hero with title + orrery animation. Click "ముహూర్తాలు వెతకండి" (or equivalent next button) to advance to step 2 — hero should disappear and only the white nav remains.

- [ ] **Step 6: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add indigo hero section with orrery, shown on step 1 only

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 4: Step Progress Indicator

**Files:**
- Modify: `docs/muhoortam/index.html` — `.step-bar` HTML and CSS

### Background

The current step bar has 3 dots with no labels. The new design wraps each dot+label in a `.step-item` div. The IDs `sd1`–`sd3` and `sl1`–`sl2` must stay the same (JS uses them).

- [ ] **Step 1: Replace the step bar HTML**

Find:
```html
<!-- ══ STEP PROGRESS ══ -->
<div class="step-bar">
  <div class="step-dot active" id="sd1">1</div>
  <div class="step-line" id="sl1"></div>
  <div class="step-dot" id="sd2">2</div>
  <div class="step-line" id="sl2"></div>
  <div class="step-dot" id="sd3">3</div>
</div>
```

Replace with:
```html
<!-- ══ STEP PROGRESS ══ -->
<div class="step-bar">
  <div class="step-item">
    <div class="step-dot active" id="sd1">1</div>
    <div class="step-label" data-te="వేడుక" data-en="Ceremony">వేడుక</div>
  </div>
  <div class="step-line" id="sl1"></div>
  <div class="step-item">
    <div class="step-dot" id="sd2">2</div>
    <div class="step-label" data-te="వివరాలు" data-en="Details">వివరాలు</div>
  </div>
  <div class="step-line" id="sl2"></div>
  <div class="step-item">
    <div class="step-dot" id="sd3">3</div>
    <div class="step-label" data-te="ఫలితాలు" data-en="Results">ఫలితాలు</div>
  </div>
</div>
```

- [ ] **Step 2: Replace step bar CSS**

Remove the old `.step-bar`, `.step-dot`, `.step-dot.active`, `.step-dot.done`, `.step-line`, `.step-line.done` blocks. Replace with:

```css
/* ════════════════════════════════
   STEP PROGRESS BAR
════════════════════════════════ */
.step-bar {
  display: flex;
  align-items: flex-start;
  padding: 16px 20px 0;
  max-width: 680px;
  margin: 0 auto;
  background: var(--bg);
}
.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}
.step-dot {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: var(--border);
  color: var(--text-3);
  transition: all var(--transition);
  font-family: 'Inter', system-ui, sans-serif;
}
.step-dot.active {
  background: var(--indigo);
  color: #fff;
  box-shadow: 0 0 0 4px var(--indigo-xl);
}
.step-dot.done {
  background: var(--indigo);
  color: #fff;
  font-size: 14px;
}
.step-dot.done::before { content: "✓"; }
.step-dot.done { font-size: 0; }
.step-dot.done::before { font-size: 14px; }
.step-label {
  font-size: 10px;
  color: var(--text-3);
  font-weight: 500;
  white-space: nowrap;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.step-dot.active + .step-label,
.step-item:has(.step-dot.active) .step-label {
  color: var(--indigo);
  font-weight: 700;
}
.step-line {
  flex: 1;
  height: 2px;
  background: var(--border);
  margin: 15px 4px 0;
  transition: background var(--transition);
}
.step-line.done { background: var(--indigo); }
```

- [ ] **Step 3: Verify step bar renders correctly**

Open in browser. Step 1 should show: active indigo circle "1" with label below, gray connecting lines, gray circles for steps 2 and 3. Advance to step 2 — step 1 shows ✓ checkmark, step 2 becomes active indigo.

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign step progress indicator with labels and indigo active state

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 5: Panel 1 — Ceremony Cards, Form Fields, Date Tabs

**Files:**
- Modify: `docs/muhoortam/index.html` — Panel 1 CSS (ceremony grid, cards, form, date tabs, buttons)

### Background

Panel 1 contains: ceremony category tabs + ceremony grid, ceremony location input, date range inputs, date mode tabs (range/single). The HTML structure stays; only CSS changes + panel width constraint added.

- [ ] **Step 1: Add panel-level layout CSS**

Insert before the existing `.card` CSS block:

```css
/* ════════════════════════════════
   PANELS
════════════════════════════════ */
.panel {
  max-width: 680px;
  margin: 0 auto;
  padding: 20px 16px 48px;
}
.section-title {
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-3);
  margin: 16px 0 10px;
}
```

Remove the old `.section-title` CSS block (currently has `font-family: Noto Serif Telugu`, `color: var(--maroon)`, decorative `::after` pseudo-element, large font-size).

- [ ] **Step 2: Replace `.card` CSS**

Find the old `.card` block (currently has `background: var(--white)`, `border-radius: var(--radius)`, `box-shadow: var(--shadow)`). Replace with:

```css
/* ════════════════════════════════
   CARDS
════════════════════════════════ */
.card {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  padding: 20px;
  margin-bottom: 14px;
}
.card-field-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-2);
  margin-bottom: 8px;
  display: block;
  font-family: 'Inter', system-ui, sans-serif;
}
```

- [ ] **Step 3: Replace ceremony category tab CSS**

Find `.cer-tabs` and `.cer-tab` CSS blocks. Replace with:

```css
/* Ceremony category tabs */
.cer-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.cer-tab {
  padding: 6px 13px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1.5px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  transition: all var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
  white-space: nowrap;
}
.cer-tab.active {
  background: var(--indigo);
  border-color: var(--indigo);
  color: #fff;
}
.cer-tab:hover:not(.active) {
  border-color: var(--indigo-light);
  background: var(--indigo-xl);
  color: var(--indigo);
}
```

- [ ] **Step 4: Replace ceremony grid and card CSS**

Find `.ceremony-grid` and `.ceremony-card` CSS blocks. Replace with:

```css
/* Ceremony grid */
.ceremony-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
@media (max-width: 400px) {
  .ceremony-grid { grid-template-columns: repeat(2, 1fr); }
}
.ceremony-card {
  display: none;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 10px;
  cursor: pointer;
  text-align: center;
  background: var(--surface);
  transition: all var(--transition);
}
.ceremony-card.cer-visible { display: block; }
.ceremony-card:hover {
  border-color: var(--indigo-light);
  background: var(--indigo-xl);
}
.ceremony-card:active { transform: scale(0.97); }
.ceremony-card.selected {
  border-color: var(--indigo);
  background: var(--indigo-xl);
  box-shadow: 0 0 0 2px var(--indigo-light);
}
.ceremony-card .cer-icon {
  font-size: 1.7rem;
  margin-bottom: 6px;
  display: block;
}
.ceremony-card .cer-name {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
  font-family: 'Noto Sans Telugu', system-ui, sans-serif;
}
.ceremony-card .cer-name-en {
  font-size: 0.65rem;
  color: var(--text-2);
  margin-top: 2px;
  font-family: 'Inter', system-ui, sans-serif;
}
.ceremony-card.selected .cer-name { color: var(--indigo); }
.ceremony-card.selected .cer-name-en { color: var(--indigo); opacity: 0.8; }

/* EN mode: swap name prominence */
body.lang-en .ceremony-card .cer-name    { font-size: 0.65rem; font-weight: 600; color: var(--text-2); }
body.lang-en .ceremony-card .cer-name-en { font-size: 0.78rem; font-weight: 700; color: var(--text); margin-top: 0; }
body.lang-en .ceremony-card.selected .cer-name    { color: var(--indigo); opacity: 0.8; }
body.lang-en .ceremony-card.selected .cer-name-en { color: var(--indigo); }
```

- [ ] **Step 5: Replace form field CSS**

Find all `input`, `select`, `.field`, `label` CSS blocks related to form controls. Replace with:

```css
/* ════════════════════════════════
   FORM CONTROLS
════════════════════════════════ */
.field { margin-bottom: 14px; }
.field label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-2);
  margin-bottom: 6px;
  font-family: 'Inter', system-ui, sans-serif;
}
.field input[type="text"],
.field input[type="date"],
.field select {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
  outline: none;
  transition: border-color var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
  -webkit-appearance: none;
  appearance: none;
}
.field input:focus,
.field select:focus {
  border-color: var(--indigo);
  box-shadow: 0 0 0 3px var(--indigo-xl);
}
.field input::placeholder { color: var(--text-3); }
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.input-icon-wrap { position: relative; }
.input-icon-wrap .icon {
  position: absolute;
  left: 12px; top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  pointer-events: none;
}
.input-icon-wrap input { padding-left: 36px; }

/* Date mode tabs */
.date-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}
.date-tab {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1.5px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  transition: all var(--transition);
  font-family: 'Inter', system-ui, sans-serif;
}
.date-tab.active {
  background: var(--indigo);
  border-color: var(--indigo);
  color: #fff;
}
```

- [ ] **Step 6: Replace button CSS**

Find all `.btn-primary`, `.btn-outline`, `.btn-add` CSS. Replace with:

```css
/* ════════════════════════════════
   BUTTONS
════════════════════════════════ */
.btn-primary {
  display: block;
  width: 100%;
  padding: 12px 24px;
  background: var(--indigo);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  text-align: center;
  transition: background var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
  margin-top: 8px;
}
.btn-primary:hover { background: var(--indigo-dark); }
.btn-primary:active { transform: scale(0.99); }

.btn-outline {
  display: inline-block;
  padding: 10px 18px;
  background: transparent;
  color: var(--indigo);
  border: 1.5px solid var(--indigo-light);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.btn-outline:hover { background: var(--indigo-xl); border-color: var(--indigo); }

.btn-add {
  display: block;
  width: 100%;
  padding: 12px;
  background: var(--indigo-xl);
  color: var(--indigo);
  border: 1.5px dashed var(--indigo-light);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  margin-bottom: 12px;
  transition: all var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.btn-add:hover { background: var(--indigo-light); }

.actions-row {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}
```

- [ ] **Step 7: Verify Panel 1 in browser**

Open the file, click through ceremony categories. Confirm:
- Indigo active tab, gray inactive tabs
- Ceremony cards have the correct layout (3-col grid)
- Form fields have indigo focus state
- Buttons are indigo

- [ ] **Step 8: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign Panel 1 — ceremony grid, form fields, buttons in Deep Indigo

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 6: Panel 2 — Person Detail Cards

**Files:**
- Modify: `docs/muhoortam/index.html` — person card CSS

### Background

Panel 2 renders person cards dynamically via JS. The CSS classes used by JS-generated HTML are `.person-card`, `.person-header`, `.person-name`, etc. These need to be restyled.

- [ ] **Step 1: Find and replace person card CSS**

Find all CSS blocks starting with `.person-card` (there should be several for the card, header, remove button, etc). Replace the entire person card section with:

```css
/* ════════════════════════════════
   PERSON CARDS (Panel 2)
════════════════════════════════ */
.person-card {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.person-card.highlight {
  border-color: var(--indigo-light);
  box-shadow: 0 0 0 2px var(--indigo-xl), var(--shadow);
}
.person-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--indigo-xl);
  border-bottom: 1px solid var(--indigo-light);
  cursor: pointer;
}
.person-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--indigo-dark);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.person-badge {
  font-size: 11px;
  color: var(--indigo);
  font-weight: 600;
  background: var(--indigo-light);
  padding: 2px 9px;
  border-radius: 10px;
}
.btn-remove-person {
  background: none;
  border: none;
  color: var(--text-3);
  font-size: 16px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
  line-height: 1;
  transition: color var(--transition);
}
.btn-remove-person:hover { color: #DC2626; background: #FEF2F2; }
.person-body {
  padding: 16px;
}

/* Profile chips */
#profileChips {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
}
.profile-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--indigo-xl);
  border: 1.5px solid var(--indigo-light);
  color: var(--indigo);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin: 3px;
  transition: all var(--transition);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.profile-chip:hover { background: var(--indigo-light); }
.profile-chip.active { background: var(--indigo); color: #fff; border-color: var(--indigo); }
```

- [ ] **Step 2: Verify Panel 2 renders correctly**

Navigate to Panel 2 (add a ceremony, click Next). Confirm person cards have indigo header background and clean borders.

- [ ] **Step 3: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign Panel 2 person cards in Deep Indigo

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 7: Panel 3 — Loading State, Result Cards, Win-Cards

**Files:**
- Modify: `docs/muhoortam/index.html` — loading area CSS + result card CSS + win-card CSS

- [ ] **Step 1: Replace loading area CSS**

Find `.loading-wrap`, `.progress-track`, `.progress-fill`, `.progress-label`, `.progress-sub` blocks. Replace with:

```css
/* ════════════════════════════════
   LOADING
════════════════════════════════ */
.loading-wrap {
  text-align: center;
  padding: 24px 0;
}
.progress-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.progress-track {
  background: var(--border);
  border-radius: 20px;
  height: 6px;
  overflow: hidden;
  margin: 0 0 8px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--indigo-dark), var(--indigo));
  border-radius: 20px;
  transition: width 0.5s ease;
}
.progress-sub {
  font-size: 12px;
  color: var(--text-3);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
```

- [ ] **Step 2: Replace results hero CSS**

Find `.results-hero`, `.ceremony-tag`, `.results-hero h2`, `.results-hero .count`, `.kalam-banner` blocks. Replace with:

```css
/* Results hero */
.results-hero {
  text-align: center;
  padding: 4px 0 16px;
}
.ceremony-tag {
  display: inline-block;
  background: var(--indigo-xl);
  color: var(--indigo);
  padding: 5px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
  border: 1px solid var(--indigo-light);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.results-hero h2 {
  font-family: 'Noto Sans Telugu', 'Inter', system-ui, sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
}
.results-hero .count {
  font-size: 13px;
  color: var(--text-2);
  margin-top: 4px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.kalam-banner {
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: 0.8rem;
  color: #78350F;
  line-height: 1.6;
  margin-bottom: 14px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
```

- [ ] **Step 3: Replace result card CSS**

Find the entire `/* Result Cards */` section with `.result-card`, `.result-card-header`, `.result-card-date`, `.result-card-score`, etc. blocks. Replace with:

```css
/* ════════════════════════════════
   RESULT CARDS
════════════════════════════════ */
.result-card {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  border-left: 4px solid var(--indigo);
  box-shadow: var(--shadow);
  margin-bottom: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow var(--transition), transform var(--transition);
}
.result-card:hover { box-shadow: var(--shadow-lg); }
.result-card:active { transform: scale(0.99); }
.result-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  gap: 12px;
}
.result-card-left {}
.result-card-date {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 2px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.result-card-time {
  font-size: 13px;
  color: var(--indigo);
  font-weight: 600;
  margin-bottom: 6px;
  font-family: 'Inter', system-ui, sans-serif;
}
.result-card-chips {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.result-card-right {
  text-align: right;
  flex-shrink: 0;
}
.result-badge {
  background: var(--indigo-xl);
  color: var(--indigo);
  border: 1px solid var(--indigo-light);
  border-radius: 8px;
  padding: 8px 12px;
  text-align: center;
  font-family: 'Noto Sans Telugu', 'Inter', system-ui, sans-serif;
  font-size: 11px;
  font-weight: 600;
  min-width: 70px;
}

/* Chips (nakshatra, tithi, lagna, choghadiya) */
.chip, .badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.badge-green, .chip-good {
  background: var(--success-bg);
  color: var(--success);
}
.badge-red, .chip-bad {
  background: #FEF2F2;
  color: #991B1B;
}
.chip-indigo {
  background: var(--indigo-xl);
  color: var(--indigo);
}
.chip-amber {
  background: var(--amber-light);
  color: #92400E;
}
```

- [ ] **Step 4: Replace win-card CSS (muhurtam window cards inside each result)**

Find `.win-card`, `.win-card.best`, `.win-card-header`, `.win-card-time`, `.win-card-score`, `.win-card-meta`, `.win-card-sub` blocks. Replace with:

```css
/* Win-cards (muhurtam windows inside a day result) */
.win-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  margin-bottom: 8px;
  background: var(--surface);
}
.win-card.best {
  border-color: var(--indigo-light);
  border-width: 1.5px;
  background: var(--indigo-xl);
}
.win-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.win-card-time {
  font-weight: 800;
  font-size: 1rem;
  color: var(--indigo-dark);
  font-family: 'Inter', system-ui, sans-serif;
}
.win-card.best .win-card-time { font-size: 1.05rem; }
.win-card-score {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: var(--indigo);
  border-radius: 10px;
  padding: 2px 9px;
  font-family: 'Inter', system-ui, sans-serif;
}
.win-card-meta {
  font-size: 11px;
  color: var(--indigo);
  margin-top: 3px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.win-card-sub {
  font-size: 10px;
  color: var(--text-3);
  margin-top: 2px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
```

- [ ] **Step 5: Replace score details table CSS**

Find `.score-details-table` block. Replace with:

```css
.score-details-table {
  width: 100%;
  font-size: 11px;
  border-collapse: collapse;
  margin-top: 6px;
}
.score-details-table tr td { padding: 3px 6px; }
.score-details-table tr:nth-child(even) { background: var(--bg); }
.score-details-table .total-row {
  font-weight: 800;
  background: var(--indigo-xl) !important;
}
.score-details-table .pos { color: var(--success); text-align: right; font-weight: 600; }
.score-details-table .neg { color: #DC2626; text-align: right; font-weight: 600; }
.score-details-table .neu { color: var(--text-2); text-align: right; }
```

- [ ] **Step 6: Replace timeline bar CSS**

Find `.day-timeline` block. Replace with:

```css
.day-timeline {
  position: relative;
  background: var(--bg);
  border-radius: 6px;
  height: 22px;
  margin: 8px 0 10px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.day-timeline .tl-label {
  position: absolute; top: 0; bottom: 0;
  display: flex; align-items: center;
  font-size: 9px; color: var(--text-3); padding: 0 4px;
  pointer-events: none; font-family: 'Inter', system-ui, sans-serif;
}
.day-timeline .tl-label.right { right: 0; }
.day-timeline .tl-window {
  position: absolute; top: 2px; bottom: 2px;
  border-radius: 4px; cursor: pointer;
  transition: opacity var(--transition);
}
.day-timeline .tl-window:hover { opacity: 0.75; }
.day-timeline .tl-window span {
  font-size: 8px; color: #fff; font-weight: 700;
  padding: 0 3px; white-space: nowrap; overflow: hidden;
  display: block; line-height: 18px;
}
```

- [ ] **Step 7: Verify Panel 3 in browser**

Trigger a search and verify:
- Loading area shows indigo progress bar with orrery
- Result cards have indigo left border
- Win-cards are clean with indigo time/score
- Timeline bar renders correctly

- [ ] **Step 8: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign Panel 3 loading area, result cards, and win-cards

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 8: Detail Overlay / Sheet

**Files:**
- Modify: `docs/muhoortam/index.html` — overlay + sheet CSS

- [ ] **Step 1: Replace overlay and sheet CSS**

Find the `.overlay`, `.sheet`, `.sheet-handle-wrap`, `.sheet-handle`, `.sheet-header`, `.sheet-title`, `.sheet-date`, `.sheet-body`, `.sheet-footer`, `.detail-section-title`, `.detail-item`, `.di-icon`, `.di-label`, `.di-sub`, `.di-value` blocks. Replace all with:

```css
/* ════════════════════════════════
   DETAIL OVERLAY
════════════════════════════════ */
.overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(17,24,39,0.5);
  z-index: 500;
  backdrop-filter: blur(2px);
}
.overlay.open { display: flex; align-items: flex-end; }
.sheet {
  background: var(--surface);
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  max-height: 88vh;
  overflow-y: auto;
  animation: slideUp 0.3s cubic-bezier(0.32,0.72,0,1);
}
@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
.sheet-handle-wrap {
  display: flex; justify-content: center;
  padding: 10px 0 4px;
}
.sheet-handle {
  width: 36px; height: 4px;
  background: var(--border);
  border-radius: 2px;
}
.sheet-header {
  padding: 4px 20px 16px;
  border-bottom: 1px solid var(--border);
}
.sheet-title {
  font-size: 17px;
  font-weight: 800;
  color: var(--text);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.sheet-date {
  font-size: 13px;
  color: var(--indigo);
  font-weight: 600;
  margin-top: 2px;
  font-family: 'Inter', system-ui, sans-serif;
}
.sheet-body { padding: 16px 20px; }
.sheet-footer {
  padding: 12px 20px 20px;
  border-top: 1px solid var(--border);
}

/* Detail item rows */
.detail-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-3);
  margin: 16px 0 8px;
  font-family: 'Inter', system-ui, sans-serif;
}
.detail-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.detail-item:last-child { border-bottom: none; }
.detail-item .di-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 1px; }
.di-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.di-sub {
  font-size: 11px;
  color: var(--text-2);
  margin-top: 2px;
  line-height: 1.4;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.di-value {
  margin-left: auto;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: var(--indigo);
  white-space: nowrap;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Validation badge */
.validation-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  padding: 3px 10px;
  margin-top: 4px;
  font-family: 'Inter', system-ui, sans-serif;
}
.validation-badge.verified, .validation-badge.partial {
  background: var(--success-bg);
  color: var(--success);
}
.validation-badge.mismatch {
  background: var(--warning-bg);
  color: #92400E;
}

/* Print */
@media print {
  .site-nav, .step-bar, .hero-section, .actions-row,
  .btn-primary, .btn-outline, .overlay { display: none !important; }
  .result-card { border: 1px solid #ccc !important; box-shadow: none !important; }
}
```

- [ ] **Step 2: Verify detail overlay**

Click a result card's "More Details". Confirm:
- Sheet slides up from bottom with rounded top corners
- Handle bar visible
- Indigo section date, clean detail rows

- [ ] **Step 3: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "style: redesign detail overlay sheet with clean indigo styling

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 9: Ceremony Icons + Category Tabs Update

**Files:**
- Modify: `docs/muhoortam/index.html` — ceremony card icon emojis + tab icon emojis + `data-te`/`data-en` attributes

- [ ] **Step 1: Update ceremony card icons**

Find each ceremony card `<span class="cer-icon">` and replace the emoji:

| Find | Replace |
|---|---|
| `<span class="cer-icon">💒</span>` (vivaha card) | `<span class="cer-icon">🏵️</span>` |
| `<span class="cer-icon">🌸</span>` (garbhadanam) | `<span class="cer-icon">🌱</span>` |
| `<span class="cer-icon">🧸</span>` (namakaranam) | `<span class="cer-icon">👶</span>` |
| `<span class="cer-icon">🍚</span>` (anna_prasana) | `<span class="cer-icon">🥄</span>` |
| `<span class="cer-icon">🏠</span>` (gruha_pravesam) | `<span class="cer-icon">🔑</span>` |
| `<span class="cer-icon">🏗️</span>` (sankhu_stapana) | `<span class="cer-icon">🐚</span>` |
| `<span class="cer-icon">✈️</span>` (prayanam) | `<span class="cer-icon">🧭</span>` |
| `<span class="cer-icon">👗</span>` (kotta_battalu) | `<span class="cer-icon">👘</span>` |
| `<span class="cer-icon">⚔️</span>` (yuddham) | `<span class="cer-icon">🏆</span>` |
| `<span class="cer-icon">💊</span>` (oshadha_seva) | `<span class="cer-icon">🌿</span>` |

Keep unchanged: `💎` (chelamu), `📚` (vidyarambham), `🪡` (upanayanam), `🪔` (pooja).

- [ ] **Step 2: Update category tab icons and data attributes**

Find the `.cer-tab` for vivaha:
```html
<div class="cer-tab active" data-cat="vivaha" data-te="💒 వివాహం" data-en="💒 Wedding" onclick="selectCerCat(this)">💒 వివాహం</div>
```
Replace with:
```html
<div class="cer-tab active" data-cat="vivaha" data-te="🏵️ వివాహం" data-en="🏵️ Wedding" onclick="selectCerCat(this)">🏵️ వివాహం</div>
```

Find the `.cer-tab` for home:
```html
<div class="cer-tab" data-cat="home" data-te="🏠 గృహ" data-en="🏠 Home" onclick="selectCerCat(this)">🏠 గృహ</div>
```
Replace with:
```html
<div class="cer-tab" data-cat="home" data-te="🔑 గృహ" data-en="🔑 Home" onclick="selectCerCat(this)">🔑 గృహ</div>
```

(The `🍼 శైశవం`, `🌟 జీవితం`, `🙏 పూజ` tabs are already appropriate — leave them unchanged.)

- [ ] **Step 3: Verify icons in browser**

Check all ceremony categories. Confirm 🏵️ for Vivaha, 🐚 for Sankhu Stapana, 🧭 for Prayanam etc.

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: update ceremony icons to culturally appropriate emojis

- Vivaha: 💒→🏵️ (Jayamala garland exchange)
- Garbhadanam: 🌸→🌱 (new life seedling)
- Namakaranam: 🧸→👶 (baby)
- Anna Prasana: 🍚→🥄 (spoon feeding)
- Gruha Pravesam: 🏠→🔑 (key for house entry)
- Sankhu Stapana: 🏗️→🐚 (conch shell - literal meaning)
- Prayanam: ✈️→🧭 (compass for any journey)
- Kotta Battalu: 👗→👘 (traditional garment)
- Yuddham: ⚔️→🏆 (trophy for contest)
- Oshadha Seva: 💊→🌿 (Ayurvedic herb)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 10: Final Polish, Full-Flow Test, and Deploy

**Files:**
- Modify: `docs/muhoortam/index.html` — any remaining old CSS references + mobile media queries

- [ ] **Step 1: Remove any remaining old CSS references**

Search for any remaining CSS that references old variables (`var(--saffron)`, `var(--maroon)`, `var(--cream)`, `var(--brown)`, `var(--gold)`) and replace with appropriate new tokens:

```bash
grep -n "var(--saffron)\|var(--maroon)\|var(--cream)\|var(--brown)\|var(--gold)" docs/muhoortam/index.html
```

For any found: replace `var(--saffron)` → `var(--indigo)`, `var(--maroon)` → `var(--indigo-dark)`, `var(--cream)` → `var(--bg)`, `var(--brown)` → `var(--text)`, `var(--gold)` → `var(--amber)`.

- [ ] **Step 2: Add/verify mobile media queries**

Ensure the following responsive rules exist and are correct:

```css
@media (max-width: 560px) {
  .hero-inner { grid-template-columns: 1fr; }
  .hero-orrery { display: none; }
  .hero-title { font-size: 1.5rem; }
  .ceremony-grid { grid-template-columns: repeat(2, 1fr); }
  .step-label { display: none; }
  .field-row { grid-template-columns: 1fr; }
}
```

If `.step-label { display: none }` would break label visibility on tablet, keep it visible at 400px+ and hide only at 320px:
```css
@media (max-width: 360px) {
  .step-label { display: none; }
}
```

- [ ] **Step 3: Full end-to-end test in browser**

Test the complete wizard flow:

1. **Landing**: Open `http://localhost:8080/muhoortam/`. Verify indigo hero with orrery, sticky nav, language pill.
2. **Ceremony selection**: Click a category tab. Select a ceremony. Click "Next".
3. **Step transition**: Hero hides, step 1 shows ✓, step 2 becomes active.
4. **Person details**: Add person details, submit.
5. **Loading**: Orrery spins, indigo progress bar fills.
6. **Results**: Result cards show with indigo left border, chips, score.
7. **Detail overlay**: Click a result card → sheet slides up with detail rows.
8. **Language toggle**: Switch to EN. Verify ceremony names, labels, nakshatra names all translate.
9. **Reset**: Click "↺ కొత్తగా". Hero should reappear.

Fix any visual issues found.

- [ ] **Step 4: Run existing backend tests (confirm no regressions)**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py -q
```

Expected: all 78 tests pass (frontend changes have no effect on backend).

- [ ] **Step 5: Deploy to GitHub Pages**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "style: final polish and mobile responsive pass for website revamp

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin master
```

- [ ] **Step 6: Smoke-test live site**

Open `https://muhoortam.sanathanadharmas.com`. Confirm the new design is live. Toggle EN/TE. Run a ceremony search.
