# Muhoortam UI Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add score breakdowns, day-timeline breadcrumb on range cards, app-level తె/EN language toggle, and breadcrumb page navigation to `docs/muhoortam/index.html`.

**Architecture:** All changes are in a single HTML file. Add a `APP_LANG` global + `t(te,en)` helper for bilingual rendering, refactor `_renderResultCard` for the new timeline+hero+chips layout, extend score display to range cards, and add a breadcrumb bar driven by a `_navStack` state array.

**Tech Stack:** Vanilla JS + HTML/CSS in `docs/muhoortam/index.html` (no build step, no framework). Deploy via GitHub Pages (auto on push to master).

---

## File Map

| File | What changes |
|---|---|
| `docs/muhoortam/index.html` | All four changes — CSS additions, JS additions, modified render functions |

---

## Task 1 — Language Infrastructure (APP_LANG, toggle, lookup tables)

**Files:**
- Modify: `docs/muhoortam/index.html` — add CSS for toggle, add JS globals and helpers near top of `<script>` block

### What to add

#### 1a. CSS for the language toggle (add inside `<style>`)

- [ ] Find the `.header` CSS block (around line 46). Add the following toggle CSS immediately after the `.header .sub` rule:

```css
/* ── Language toggle ── */
.lang-toggle {
  position: absolute;
  top: 14px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: rgba(255,255,255,0.85);
  cursor: pointer;
  user-select: none;
  z-index: 10;
}
.lang-toggle .track {
  width: 36px; height: 18px;
  background: rgba(255,255,255,0.25);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: 9px;
  position: relative;
  transition: background 0.2s;
}
.lang-toggle .thumb {
  position: absolute;
  top: 2px; left: 2px;
  width: 14px; height: 14px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.lang-toggle.en .thumb { transform: translateX(18px); }
.lang-toggle.en { color: rgba(255,255,255,1); }

/* ── Breadcrumb bar ── */
#breadcrumb {
  display: none;
  padding: 7px 16px;
  font-size: 0.72rem;
  color: var(--brown-mid);
  background: var(--cream2);
  border-bottom: 1px solid rgba(196,154,108,0.2);
  flex-wrap: wrap;
  gap: 2px;
  align-items: center;
}
#breadcrumb a {
  color: var(--saffron-dark);
  text-decoration: none;
  font-weight: 600;
}
#breadcrumb a:hover { text-decoration: underline; }
#breadcrumb .sep { color: var(--brown-light); margin: 0 4px; }

/* ── Day timeline bar ── */
.day-timeline {
  position: relative;
  background: #f0ece4;
  border-radius: 6px;
  height: 22px;
  margin: 8px 0 10px;
  overflow: hidden;
}
.day-timeline .tl-label {
  position: absolute;
  top: 0; bottom: 0;
  display: flex;
  align-items: center;
  font-size: 8px;
  color: #999;
  padding: 0 4px;
  pointer-events: none;
}
.day-timeline .tl-label.right { right: 0; }
.day-timeline .tl-window {
  position: absolute;
  top: 2px; bottom: 2px;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.15s;
}
.day-timeline .tl-window:hover { opacity: 0.75; }
.day-timeline .tl-window span {
  font-size: 8px;
  color: #fff;
  font-weight: 700;
  padding: 0 3px;
  white-space: nowrap;
  overflow: hidden;
  display: block;
  line-height: 18px;
}

/* ── Window mini-cards (range results) ── */
.win-card {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 8px 12px;
  margin-bottom: 6px;
  background: #fff;
}
.win-card.best {
  border-color: #66BB6A;
  border-width: 1.5px;
  background: #f9fbe7;
}
.win-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.win-card-time {
  font-weight: 800;
  font-size: 1rem;
  color: #1B5E20;
}
.win-card.best .win-card-time { font-size: 1.1rem; }
.win-card-score {
  font-size: 0.72rem;
  font-weight: 700;
  color: #fff;
  background: #2E7D32;
  border-radius: 10px;
  padding: 2px 8px;
}
.win-card-meta {
  font-size: 0.72rem;
  color: #388E3C;
  margin-top: 3px;
}
.win-card-sub {
  font-size: 0.68rem;
  color: #888;
  margin-top: 1px;
}
.score-details-table {
  width: 100%;
  font-size: 0.68rem;
  border-collapse: collapse;
  margin-top: 5px;
}
.score-details-table tr td { padding: 2px 4px; }
.score-details-table tr:nth-child(even) { background: #f5f5f5; }
.score-details-table .total-row {
  font-weight: 800;
  background: #e3f2fd !important;
}
.score-details-table .pos { color: #2E7D32; text-align: right; }
.score-details-table .neg { color: #C62828; text-align: right; }
.score-details-table .neu { color: #555; text-align: right; }
```

#### 1b. Toggle button HTML in the header

- [ ] Find the `.header` HTML block (the `<div class="header">` element, around line 345–360 in the HTML body). Add this toggle button as the FIRST child inside `.header`:

```html
<button class="lang-toggle" id="langToggle" onclick="toggleLang()" title="Switch language / భాష మార్చండి" aria-label="Language toggle">
  <span id="langLabel">తె</span>
  <div class="track"><div class="thumb"></div></div>
  <span>EN</span>
</button>
```

#### 1c. Breadcrumb bar HTML — add immediately after the closing `</header>` tag:

```html
<nav id="breadcrumb" aria-label="breadcrumb"></nav>
```

#### 1d. JS globals and helpers — add near the top of the `<script>` block, before any other variables:

```js
// ── Language ──────────────────────────────────────────────────────────────────
let APP_LANG = localStorage.getItem('muhoortam_lang') || 'te';

function toggleLang() {
  APP_LANG = APP_LANG === 'te' ? 'en' : 'te';
  localStorage.setItem('muhoortam_lang', APP_LANG);
  document.getElementById('langToggle').classList.toggle('en', APP_LANG === 'en');
  document.getElementById('langLabel').textContent = APP_LANG === 'te' ? 'తె' : 'EN';
  _rerenderCurrentResults();
}

/** Return te or en string based on APP_LANG. Falls back to te if en is absent. */
function t(te, en) { return (APP_LANG === 'en' && en) ? en : te; }

// English lookup tables (transliteration)
const _VAARAM_EN   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const _VAARAM_TE_LIST = ['ఆదివారం','సోమవారం','మంగళవారం','బుధవారం','గురువారం','శుక్రవారం','శనివారం'];
const _NAKSHATRA_EN = [
  'Ashvini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu',
  'Pushyami','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta',
  'Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Moola','Purva Ashadha',
  'Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadra',
  'Uttara Bhadra','Revati'
];
const _NAKSHATRA_TE_LIST = [
  'అశ్వని','భరణి','కృత్తిక','రోహిణి','మృగశిర','ఆర్ద్ర','పునర్వసు',
  'పుష్యమి','ఆశ్లేష','మఘ','పూర్వఫల్గుణి','ఉత్తరఫల్గుణి','హస్త',
  'చిత్ర','స్వాతి','విశాఖ','అనురాధ','జ్యేష్ఠ','మూల','పూర్వాషాఢ',
  'ఉత్తరాషాఢ','శ్రవణం','ధనిష్ఠ','శతభిష','పూర్వభాద్ర',
  'ఉత్తరభాద్ర','రేవతి'
];
const _TITHI_EN = [
  'Pratipada','Dvitiya','Tritiya','Chaturthi','Panchami',
  'Shashthi','Saptami','Ashtami','Navami','Dashami',
  'Ekadashi','Dvadashi','Trayodashi','Chaturdashi','Pournami',
  'Pratipada','Dvitiya','Tritiya','Chaturthi','Panchami',
  'Shashthi','Saptami','Ashtami','Navami','Dashami',
  'Ekadashi','Dvadashi','Trayodashi','Chaturdashi','Amavasya'
];
const _TITHI_TE_LIST = [
  'పాడ్యమి','విదియ','తదియ','చవితి','పంచమి',
  'షష్ఠి','సప్తమి','అష్టమి','నవమి','దశమి',
  'ఏకాదశి','ద్వాదశి','త్రయోదశి','చతుర్దశి','పౌర్ణమి',
  'పాడ్యమి','విదియ','తదియ','చవితి','పంచమి',
  'షష్ఠి','సప్తమి','అష్టమి','నవమి','దశమి',
  'ఏకాదశి','ద్వాదశి','త్రయోదశి','చతుర్దశి','అమావాస్య'
];
const _LAGNA_EN = [
  'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
];
const _LAGNA_TE_LIST = [
  'మేషం','వృషభం','మిథునం','కర్కాటకం','సింహం','కన్య',
  'తుల','వృశ్చికం','ధనుసు','మకరం','కుంభం','మీనం'
];
const _MASAM_EN = [
  'Chaitra','Vaishakha','Jyeshtha','Ashadha','Shravana','Bhadrapada',
  'Ashvina','Kartika','Margashira','Pushya','Magha','Phalguna'
];
const _MASAM_TE_LIST = [
  'చైత్ర','వైశాఖ','జ్యేష్ఠ','ఆషాఢ','శ్రావణ','భాద్రపద',
  'ఆశ్వయుజ','కార్తీక','మార్గశిర','పుష్య','మాఘ','ఫాల్గుణ'
];

/** Translate a Telugu panchang term to English using lookup tables. */
function teToEn(teTerm, teList, enList) {
  if (!teTerm) return teTerm;
  // Strip trailing suffixes like " నక్షత్రం", " తిథి", " లగ్నం", " మాసం"
  const clean = teTerm.replace(/\s*(నక్షత్రం|తిథి|లగ్నం|మాసం|వారం)\s*$/, '').trim();
  const idx = teList.indexOf(clean);
  return idx >= 0 ? enList[idx] : teTerm;
}

function tNakshatra(te) { return t(te, teToEn(te, _NAKSHATRA_TE_LIST, _NAKSHATRA_EN)); }
function tTithi(te)     { return t(te, teToEn(te, _TITHI_TE_LIST, _TITHI_EN)); }
function tLagna(te)     { return t(te, teToEn(te, _LAGNA_TE_LIST, _LAGNA_EN)); }
function tVaaram(te)    { return t(te, teToEn(te, _VAARAM_TE_LIST, _VAARAM_EN)); }
function tMasam(te)     { return t(te, teToEn(te, _MASAM_TE_LIST, _MASAM_EN)); }
function tDate(date_te, date_raw) {
  if (APP_LANG === 'te' || !date_raw) return date_te;
  // date_raw is "DD/MM/YYYY"
  const [d, m, y] = date_raw.split('/').map(Number);
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  return `${d} ${months[m-1]} ${y}`;
}

// ── Re-render current results after lang toggle ───────────────────────────────
function _rerenderCurrentResults() {
  // If range results are showing, re-render all cards
  const container = document.getElementById('cardsContainer');
  if (container && allResults.length) {
    container.innerHTML = '';
    const end = Math.min(_resultsShown, allResults.length);
    for (let i = 0; i < end; i++) container.appendChild(_renderResultCard(allResults[i], i));
  }
  // If check result is showing, re-render it
  if (_lastCheckData) showCheckResult(_lastCheckData);
}
```

#### 1e. Store last check result for re-render

- [ ] Find the `let allResults = []` global variable declaration. Add alongside it:

```js
let _lastCheckData = null;
```

- [ ] Find the line inside `showCheckResult(data)` that reads `const list = document.getElementById("resultsList");` (around line 1695). Add `_lastCheckData = data;` immediately before it:

```js
function showCheckResult(data) {
  _lastCheckData = data;               // ← add this line
  const list = document.getElementById("resultsList");
```

#### 1f. Apply initial lang state on page load

- [ ] Find the DOMContentLoaded event or the earliest JS that runs at page load. Add this at the bottom of the `<script>` block (before the closing `</script>`):

```js
// Apply initial language state
(function() {
  if (APP_LANG === 'en') {
    const t = document.getElementById('langToggle');
    if (t) t.classList.add('en');
    const l = document.getElementById('langLabel');
    if (l) l.textContent = 'EN';
  }
})();
```

- [ ] **Verify:** Open `index.html` via GitHub Pages or a local server. The top-right of the header should show a "తె / EN" toggle. Clicking it should toggle the class. No results rendered yet so no content changes — that comes in Tasks 2–3.

- [ ] **Commit:**

```bash
cd C:\Users\schinta\telugu-panchang
git add docs/muhoortam/index.html
git commit -m "feat: add APP_LANG toggle, t() helper, and bilingual lookup tables"
```

---

## Task 2 — Refactor Range Result Cards (Timeline + Hero + Chips + Score)

**Files:**
- Modify: `docs/muhoortam/index.html` — replace `_renderResultCard` function (lines ~1515–1569)

### What to replace

- [ ] Replace the entire `_renderResultCard` function with the following:

```js
function _renderResultCard(r, i) {
  const windows = r.good_windows || [];
  const best    = windows[0] || null;
  const others  = windows.slice(1);

  // ── Zone A: Day timeline breadcrumb bar ──────────────────────────────────
  const rise = r.sunrise, set = r.sunset;
  let timelineHtml = '';
  if (rise && set && windows.length) {
    const riseM = toMins(rise), setM = toMins(set), span = setM - riseM;
    const blocks = windows.map((w, wi) => {
      const fromM = toMins(w.from), toM = toMins(w.to);
      const left  = Math.max(0, Math.min(100, ((fromM - riseM) / span) * 100));
      const width = Math.max(2, Math.min(100 - left, ((toM - fromM) / span) * 100));
      const bg    = wi === 0 ? '#2E7D32' : '#81C784';
      const label = wi === 0 ? `⭐ ${w.from}` : w.from;
      return `<div class="tl-window" style="left:${left.toFixed(1)}%;width:${width.toFixed(1)}%;background:${bg}"
                   onclick="document.getElementById('win-${i}-${wi}').scrollIntoView({behavior:'smooth',block:'nearest'})"
                   title="${w.from}–${w.to}">
                <span>${label}</span>
              </div>`;
    }).join('');
    timelineHtml = `
      <div class="day-timeline">
        <div class="tl-label">${rise}</div>
        <div class="tl-label right">${set}</div>
        ${blocks}
      </div>`;
  }

  // ── Score breakdown HTML (shared by all window cards) ────────────────────
  function _scoreHtml(w) {
    const lq = w.lagna_quality || {};
    const score = lq.score || 0;
    const components = lq.score_components || [];
    if (!score) return '';
    const barWidth = Math.round((score / 150) * 100);
    const compsHtml = components.length ? `
      <details>
        <summary style="font-size:0.65rem;color:#2E7D32;cursor:pointer;font-weight:600;list-style:none;margin-top:4px">
          స్కోర్ వివరాలు ▾
        </summary>
        <table class="score-details-table">
          ${components.map(c => `
            <tr>
              <td>${c.te}${c.en ? `<span style="color:#888;font-size:0.6rem;margin-left:4px">(${c.en})</span>` : ''}</td>
              <td class="${c.delta > 0 ? 'pos' : c.delta < 0 ? 'neg' : 'neu'}">${c.delta > 0 ? '+' : ''}${c.delta}</td>
            </tr>`).join('')}
          <tr class="total-row">
            <td>మొత్తం <span style="color:#888;font-size:0.6rem">(Total)</span></td>
            <td class="pos">${score} / 150</td>
          </tr>
        </table>
      </details>` : '';
    return `
      <div style="margin-top:5px">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
          <div style="flex:1;background:#e0e0e0;border-radius:4px;height:6px">
            <div style="width:${barWidth}%;background:#2E7D32;height:6px;border-radius:4px"></div>
          </div>
          <span style="font-size:0.7rem;font-weight:700;color:#2E7D32">${score}/150</span>
        </div>
        ${compsHtml}
      </div>`;
  }

  // ── Zone B: Best window (hero) ────────────────────────────────────────────
  let heroHtml = '';
  if (best) {
    heroHtml = `
      <div id="win-${i}-0" class="win-card best">
        <div class="win-card-header">
          <div>
            <span style="font-size:0.6rem;font-weight:700;color:#2E7D32;text-transform:uppercase;letter-spacing:0.07em">⭐ ${t('ఉత్తమ ముహూర్తం','Best Window')}</span>
            <div class="win-card-time">${best.best_time || best.from} <span style="font-size:0.72rem;font-weight:600;color:#388E3C">(${best.from}–${best.to})</span></div>
          </div>
          ${(best.lagna_quality && best.lagna_quality.score)
            ? `<div class="win-card-score">${best.lagna_quality.score}/150</div>` : ''}
        </div>
        <div class="win-card-meta">
          ${tLagna(best.lagna_te)} ${t('లగ్నం','Lagna')}
          ${best.choghadiya_te ? ` · ${t(best.choghadiya_te, best.choghadiya_te)} ${t('చోఘడియ','Choghadiya')}` : ''}
        </div>
        <div class="win-card-sub">${tNakshatra(best.nakshatra_te)} · ${tTithi(best.tithi_te)}</div>
        ${_scoreHtml(best)}
      </div>`;
  } else {
    heroHtml = `<div style="background:#FFF3E0;border-radius:8px;padding:8px 12px;margin-bottom:8px;font-size:0.78rem;color:#E65100">
      ⚠️ ${t('ఈ రోజు పండితుల సలహా తీసుకోండి','Consult a scholar for this day')}
    </div>`;
  }

  // ── Zone C: Other windows (compact → expandable) ──────────────────────────
  const othersHtml = others.map((w, wi) => `
    <div id="win-${i}-${wi + 1}" class="win-card">
      <div class="win-card-header">
        <div>
          <div class="win-card-time" style="font-size:0.9rem">${w.from}–${w.to}</div>
          <div class="win-card-meta">${tLagna(w.lagna_te)} ${t('లగ్నం','Lagna')}${w.choghadiya_te ? ` · ${t(w.choghadiya_te, w.choghadiya_te)}` : ''}</div>
        </div>
        ${(w.lagna_quality && w.lagna_quality.score)
          ? `<div class="win-card-score" style="background:#558B2F">${w.lagna_quality.score}/150</div>` : ''}
      </div>
      ${_scoreHtml(w)}
    </div>`).join('');

  // ── Vaaram display ────────────────────────────────────────────────────────
  const vaaramDisplay = (r.gregorian_vaaram_te && r.gregorian_vaaram_te !== r.vaaram_te)
    ? `${tVaaram(r.gregorian_vaaram_te)} <span style="font-size:0.65rem;background:#FFF3E0;color:#E65100;border-radius:10px;padding:1px 6px;margin-left:3px">${t('క్యాలెండర్','Cal')}</span>
       <div style="font-size:0.7rem;color:#E65100;margin-top:2px">⚠️ ${t('పంచాంగ వారం','Panchang day')}: ${tVaaram(r.vaaram_te)}</div>`
    : tVaaram(r.vaaram_te);

  // ── Assemble card ─────────────────────────────────────────────────────────
  const card = document.createElement('div');
  card.className = 'result-card';
  card.innerHTML = `
    <div class="result-card-header">
      <div class="result-date">
        <div class="day">${tDate(r.date_te, r.date_raw)}</div>
        <div class="vaaram">${vaaramDisplay}</div>
      </div>
      <div class="result-badge">${tNakshatra(r.nakshatra_te)}<br>${tTithi(r.tithi_te)}</div>
    </div>
    <div class="result-body">
      ${timelineHtml}
      ${heroHtml}
      ${othersHtml}
      <div class="result-row">
        <div class="result-chip">✨ <span>${t(r.yoga_te, r.yoga_te)}</span></div>
        <div class="result-chip">🌅 <span>${r.sunrise}</span></div>
        <div class="result-chip">🌇 <span>${r.sunset}</span></div>
      </div>
      ${best && best.planet_rashis
        ? `<details style="margin-top:6px"><summary style="font-size:0.72rem;color:var(--brown-mid);cursor:pointer;padding:4px 0">🪐 ${t('గ్రహ స్థానాలు చూడండి','View planetary positions')}</summary>${renderHoroscopeChart(best.planet_rashis, best.lagna_idx)}</details>`
        : ''}
      <button class="btn-details" onclick="showDetail(${i})">
        🔍 ${t('ముహూర్తం వివరాలు చూడండి','View muhurtam details')}
      </button>
    </div>`;
  return card;
}
```

- [ ] **Verify:** Run a range search (e.g. June 2019, Vivaha, Kakinada). Each day card should show:
  - A timeline bar with coloured blocks for each window
  - The best window as a green hero card with score bar
  - Other windows as smaller cards below
  - Clicking a timeline block scrolls to that window card
  - Score "వివరాలు ▾" expands the factor table

- [ ] **Verify language toggle:** Click EN. All nakshatra, tithi, lagna, vaaram names on cards should switch to English. Click తె — they switch back.

- [ ] **Commit:**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: refactor range result cards with timeline bar, hero window, score breakdown"
```

---

## Task 3 — Add English Labels to Check-Result Score Breakdown

**Files:**
- Modify: `docs/muhoortam/index.html` — update `showCheckResult` to use `t()` helpers and add English to score components

The single-day check result already has a collapsible score breakdown (lines ~1754–1765). It currently shows only `c.te`. We need to:
1. Add English translation in parentheses on each factor row
2. Use `tNakshatra()`, `tLagna()`, `tVaaram()`, `tDate()` for all panchang display values

- [ ] Inside `showCheckResult(data)`, find the score components map (around line 1757):

```js
${sc.map(c=>`<div style="display:flex;justify-content:space-between;gap:12px">
  <span style="color:#333">${c.te}</span>
  <span style="font-weight:700;color:${c.delta>0?'#2E7D32':c.delta<0?'#C62828':'#555'};white-space:nowrap">${c.delta>0?'+':''}${c.delta}</span>
</div>`).join('')}
```

Replace with:

```js
${sc.map(c=>`<div style="display:flex;justify-content:space-between;gap:12px">
  <span style="color:#333">${c.te}${c.en ? `<span style='color:#888;font-size:0.6rem;margin-left:4px'>(${c.en})</span>` : ''}</span>
  <span style="font-weight:700;color:${c.delta>0?'#2E7D32':c.delta<0?'#C62828':'#555'};white-space:nowrap">${c.delta>0?'+':''}${c.delta}</span>
</div>`).join('')}
```

- [ ] In the verdict card date/vaaram line (around line 1733):

Find:
```js
${data.date_te} — ${data.vaaram_te}
```
Replace with:
```js
${tDate(data.date_te, data.date_raw)} — ${tVaaram(data.vaaram_te)}
```

- [ ] In the best window display inside `showCheckResult` (around line 1773):

Find:
```js
⭐ ${bestWindow.nakshatra_te} &nbsp;·&nbsp; 📅 ${bestWindow.tithi_te} &nbsp;·&nbsp; 🌅 ${bestWindow.lagna_te} లగ్నం
```
Replace with:
```js
⭐ ${tNakshatra(bestWindow.nakshatra_te)} &nbsp;·&nbsp; 📅 ${tTithi(bestWindow.tithi_te)} &nbsp;·&nbsp; 🌅 ${tLagna(bestWindow.lagna_te)} ${t('లగ్నం','Lagna')}
```

- [ ] In the `good_windows` list inside `showCheckResult` (around line 1839):

Find the nakshatra/tithi/lagna display line:
```js
⭐ ${w.nakshatra_te||''} &nbsp;|&nbsp; 📅 ${w.tithi_te||''} &nbsp;|&nbsp; 🌅 ${w.lagna_te||''} లగ్నం
```
Replace with:
```js
⭐ ${tNakshatra(w.nakshatra_te||'')} &nbsp;|&nbsp; 📅 ${tTithi(w.tithi_te||'')} &nbsp;|&nbsp; 🌅 ${tLagna(w.lagna_te||'')} ${t('లగ్నం','Lagna')}
```

- [ ] **Verify:** Run a single-day check. Toggle to EN — the date, vaaram, nakshatra, tithi, lagna in the check result should switch to English. Expand "స్కోర్ వివరాలు ▾" — each row should show the Telugu factor name with English in grey parentheses.

- [ ] **Commit:**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add English labels to check-result score breakdown and panchang fields"
```

---

## Task 4 — Breadcrumb Navigation

**Files:**
- Modify: `docs/muhoortam/index.html` — add `_navStack`, `pushBreadcrumb()`, `renderBreadcrumb()`, update `setStep()` / `showResults()` / `showCheckResult()`

### What to add

- [ ] Add the navigation state globals near `_lastCheckData`:

```js
// Breadcrumb navigation state
// Each entry: { label_te: string, label_en: string, action: function|null }
let _navStack = [];
```

- [ ] Add the breadcrumb render function:

```js
function renderBreadcrumb() {
  const nav = document.getElementById('breadcrumb');
  if (!nav) return;
  if (_navStack.length <= 1) {
    nav.style.display = 'none';
    return;
  }
  nav.style.display = 'flex';
  nav.innerHTML = _navStack.map((crumb, i) => {
    const label = t(crumb.label_te, crumb.label_en);
    const isLast = i === _navStack.length - 1;
    const sep = i > 0 ? '<span class="sep">›</span>' : '';
    if (isLast) return `${sep}<span style="color:var(--brown)">${label}</span>`;
    return `${sep}<a href="#" onclick="event.preventDefault();_breadcrumbNav(${i})">${label}</a>`;
  }).join('');
}

function _breadcrumbNav(idx) {
  const crumb = _navStack[idx];
  if (crumb && crumb.action) {
    _navStack = _navStack.slice(0, idx + 1);
    renderBreadcrumb();
    crumb.action();
  }
}
```

- [ ] Update `setStep(n)` — find the function and add breadcrumb push for step 1 (landing/home):

```js
function setStep(n) {
  // ... existing code ...
  if (n === 1) {
    // Returning to the form — clear nav stack
    _navStack = [];
    renderBreadcrumb();
  }
  // ... rest of existing setStep code ...
}
```

- [ ] Update `showResults()` — find the call to `setStep(3)` at the end of the function (around line 1691). Add breadcrumb push before it:

```js
// Push breadcrumb for results view
const fromVal = document.getElementById('rangeFrom').value;   // "YYYY-MM"
const [fy2, fm2] = fromVal.split('-').map(Number);
const rangeLabel_te = `${MONTHS_TE[fm2 - 1]} ${fy2}`;
const rangeLabel_en = `${['January','February','March','April','May','June','July','August','September','October','November','December'][fm2 - 1]} ${fy2}`;
_navStack = [
  { label_te: '🏠 హోమ్', label_en: '🏠 Home', action: () => { setStep(1); } },
  { label_te: `ముహూర్తం వెతుకు`, label_en: 'Find Muhurtam', action: () => showResults() },
  { label_te: `${rangeLabel_te} ఫలితాలు`, label_en: `Results: ${rangeLabel_en}`, action: null },
];
renderBreadcrumb();
setStep(3);
```

Remove the standalone `setStep(3)` that was there before (it is now included above).

- [ ] Update `showCheckResult(data)` — add breadcrumb push immediately after `_lastCheckData = data;`:

```js
const checkLabel_te = data.date_te || '';
const checkLabel_en = tDate(data.date_te, data.date_raw) || checkLabel_te;
// Only push if we're not already on a check breadcrumb
if (_navStack.length === 0 || _navStack[_navStack.length - 1].label_te !== checkLabel_te) {
  if (_navStack.length === 0) {
    _navStack = [
      { label_te: '🏠 హోమ్', label_en: '🏠 Home', action: () => setStep(1) },
      { label_te: 'ముహూర్తం తనిఖీ', label_en: 'Check Muhurtam', action: null },
    ];
  }
  _navStack[_navStack.length - 1] = {
    label_te: checkLabel_te,
    label_en: checkLabel_en,
    action: null
  };
}
renderBreadcrumb();
```

- [ ] Update `showDetail(i)` — find this function (it shows the bottom sheet / overlay for a specific day from range results). Add breadcrumb push at the start:

```js
function showDetail(i) {
  const r = allResults[i];
  if (r) {
    const detailLabel_te = r.date_te || '';
    const detailLabel_en = tDate(r.date_te, r.date_raw) || detailLabel_te;
    // Replace last crumb or push new one
    const base = _navStack.filter(c => c.action !== null || _navStack.indexOf(c) < 2);
    _navStack = [
      ..._navStack.slice(0, -1),   // keep Home + Results
      { label_te: detailLabel_te, label_en: detailLabel_en, action: null }
    ];
    renderBreadcrumb();
  }
  // ... rest of existing showDetail code ...
}
```

- [ ] Update `closeSheet()` — when the detail sheet closes, pop the last crumb back to the results level:

```js
function closeSheet() {
  // ... existing code ...
  if (_navStack.length > 0 && _navStack[_navStack.length - 1].action === null) {
    const parent = _navStack[_navStack.length - 2];
    if (parent) {
      _navStack = _navStack.slice(0, -1);
      renderBreadcrumb();
    }
  }
}
```

- [ ] **Verify:** 
  - Start on the form (step 1) → breadcrumb hidden ✓
  - Submit a range search → breadcrumb shows: 🏠 హోమ్ › ముహూర్తం వెతుకు › June 2019 ఫలితాలు
  - Click "🏠 హోమ్" → returns to form, breadcrumb hides ✓
  - Run a single check → breadcrumb shows: 🏠 హోమ్ › ముహూర్తం తనిఖీ › 7 జూన్ 2019
  - Toggle to EN → breadcrumb labels switch to English ✓

- [ ] **Commit:**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add breadcrumb navigation bar with state tracking"
```

---

## Task 5 — Push and Verify Deployment

- [ ] Push all commits to master:

```bash
cd C:\Users\schinta\telugu-panchang
git push origin master
```

- [ ] Monitor deployment:

```bash
gh run list --repo sairamchinta1510/telugu-panchang --limit 3
```

Expected: `pages build and deployment` workflow completes with ✅.

- [ ] Open https://muhoortam.sanatanadharmas.com/muhoortam/ and verify all four changes end-to-end:
  1. తె/EN toggle in header switches all result text
  2. Range results show timeline bar + hero + compact window chips
  3. Clicking "స్కోర్ వివరాలు ▾" expands a factor table with English in parentheses
  4. Breadcrumb trail appears on results and check pages, links navigate correctly

- [ ] **Final commit (if any last-minute fixes needed):**

```bash
git add docs/muhoortam/index.html
git commit -m "fix: post-deploy corrections"
git push origin master
```

---

## Notes for implementer

- `MONTHS_TE` is already defined in the existing script — do not redefine it.
- `toMins(t)` and `toTime(m)` are already defined — do not redefine them.
- `renderHoroscopeChart` is already defined — call it as-is.
- `selectedCeremony`, `allResults`, `_resultsShown`, `savedBirthCharts`, `savedPersons` are existing globals — do not shadow them.
- The score `score_components[].en` field may not yet be returned by the API. If `c.en` is absent, the English label simply won't show — no error. The Telugu label always shows regardless.
- `showDetail(i)` opens a bottom sheet by setting `overlay`/`sheet` elements. Find the exact implementation before modifying to avoid breaking the open/close logic.
