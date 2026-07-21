# Kundali Analysis Display — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing simple Kundali panel body with a 6-section scroll layout that displays D-1 + D-9 charts, enriched planet table, doshas, graha drishti, and parivartana yogas — all using data already returned by the API.

**Architecture:** All changes are in `docs/muhoortam/index.html` (inline CSS + JS). The function `_renderKundaliBody(chart, profile)` at line ~2542 is rewritten. New CSS classes are added in the `<style>` block (around line 186). No backend changes — all API fields (`navamsa_rashis`, `graha_drishti`, `parivartana_yogas`, `mangala_dosha`, `kala_sarpa_dosha`, enriched `planet_details`) are already returned.

**Tech Stack:** Vanilla JS, CSS3, inline HTML templates (no build step). Repo: `/Users/schinta/telugu-panchang`. Tests: Python backend tests unchanged (`cd panchang-api && python3 -m pytest`). Frontend verified by loading `http://127.0.0.1:8080/muhoortam/` with a real person's birth chart.

---

## File Map

| File | Change |
|------|--------|
| `docs/muhoortam/index.html` lines ~186–254 (CSS) | Add CSS for new components |
| `docs/muhoortam/index.html` lines ~256–320 (`@media print`) | Add print CSS for new sections |
| `docs/muhoortam/index.html` lines ~2542–2644 (`_renderKundaliBody`) | Full rewrite |

---

## Key API Data Shapes (reference for every task)

```js
// chart.planet_details[planet] — after enrich_planet_details
{ rashi_idx: 4, deg: 12, min: 34, retrograde: false,
  nakshatra_te: "పుష్యమి", nakshatra_pada: 3,
  nakshatra_lord: "శని", navamsa_rashi_idx: 3,
  navamsa_rashi_te: "కర్కాటకం", strength: "exalted" }

// chart.graha_drishti
[{ from: "guru", to: "shukra", aspect_house: 7, type: "full" },
 { from: "kuja", to: "rahu", aspect_house: 4, type: "special" }, ...]

// chart.parivartana_yogas
[{ planet_a: "guru", planet_b: "shukra", rashi_a_te: "మీనం",
   rashi_b_te: "తులం", house_a: 8, house_b: 3, type: "dainya" }, ...]

// chart.mangala_dosha
{ present: true, from_lagna: true, from_moon: false, from_venus: false,
  kuja_house_lagna: 7, severity: "మధ్యమం" }

// chart.kala_sarpa_dosha
{ present: false }
// OR
{ present: true, type: "kalasarpa", rahu_rashi_te: "మిథునం", ketu_rashi_te: "ధనుస్సు" }

// chart.navamsa_rashis — same shape as planet_rashis
{ ravi: 4, chandra: 3, kuja: 0, budha: 1, guru: 8, shukra: 6, shani: 6, rahu: 2, ketu: 8 }
```

---

## Task 1: Add CSS for New Components

**Files:**
- Modify: `docs/muhoortam/index.html` — CSS block around line 205 (after `.kundali-retro`)

- [ ] **Step 1: Add the new CSS**

Find the line `.kundali-retro { color: #c00; font-size: 0.72rem; font-weight: 700; }` (around line 205) and insert the following block immediately after it:

```css
/* ── Section layout ── */
.kundali-section { margin-bottom: 18px; }
.kundali-section-header {
  background: var(--gold, #f5c842); color: var(--brown-dark, #3b1f0a);
  padding: 7px 12px; font-weight: 700; font-size: 0.88rem;
  border-radius: 6px 6px 0 0; margin-bottom: 0;
}
.kundali-section-body {
  border: 1px solid var(--border, #e8d5c4); border-top: none;
  border-radius: 0 0 6px 6px; padding: 12px;
  background: #fff;
}

/* ── D-1 + D-9 charts row ── */
.kundali-charts-row {
  display: flex; gap: 16px; flex-wrap: wrap;
}
.kundali-chart-col { flex: 1 1 200px; }
.kundali-chart-label {
  font-size: 0.75rem; font-weight: 700; color: var(--brown-mid, #6b3a2a);
  text-align: center; margin-bottom: 6px;
}

/* ── Enhanced planet table ── */
.kundali-pt {
  width: 100%; border-collapse: collapse; font-size: 0.8rem;
}
.kundali-pt th {
  background: var(--cream2, #fdf0e0); padding: 5px 8px;
  text-align: left; font-size: 0.73rem; color: var(--brown-mid, #6b3a2a);
  border-bottom: 2px solid var(--gold-light, #d4a96a); white-space: nowrap;
}
.kundali-pt td {
  padding: 4px 8px; border-bottom: 1px solid var(--border, #e8d5c4);
  vertical-align: middle; white-space: nowrap;
}
.kundali-pt tr:nth-child(even) td { background: var(--cream, #fdf6ee); }
.kundali-pt-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.kundali-pt-hint { font-size: 0.65rem; color: var(--text-2, #888); margin-top: 3px; display: none; }
@media (max-width: 480px) { .kundali-pt-hint { display: block; } }

/* ── Strength badges ── */
.str-badge {
  display: inline-block; padding: 1px 7px; border-radius: 10px;
  font-size: 0.7rem; font-weight: 700; white-space: nowrap;
}
.str-exalted    { background: #d1fae5; color: #065f46; }
.str-debilitated{ background: #fee2e2; color: #dc2626; }
.str-own        { background: #dbeafe; color: #1e40af; }
.str-moolatrikona { background: #ede9fe; color: #5b21b6; }
.str-combust    { background: #ffedd5; color: #c2410c; }
.str-normal     { background: var(--cream2, #fdf0e0); color: var(--brown-mid, #6b3a2a); }

/* ── Dosha & yoga cards ── */
.kundali-dosha-row {
  display: flex; gap: 10px; flex-wrap: wrap;
}
.kundali-dosha-card {
  flex: 1 1 160px; border-radius: 8px; padding: 10px 12px;
  font-size: 0.82rem; line-height: 1.45;
}
.kundali-dosha-card.danger { background: #fef2f2; border: 1.5px solid #fca5a5; color: #7f1d1d; }
.kundali-dosha-card.safe   { background: #f0fdf4; border: 1.5px solid #86efac; color: #14532d; }
.kundali-dosha-card.info   { background: #eff6ff; border: 1.5px solid #93c5fd; color: #1e3a5f; }
.kundali-dosha-card .dc-title { font-weight: 700; margin-bottom: 4px; font-size: 0.85rem; }
.kundali-yoga-item {
  display: flex; align-items: center; gap: 6px; margin: 3px 0; font-size: 0.78rem;
}
.yoga-badge {
  display: inline-block; padding: 1px 7px; border-radius: 10px;
  font-size: 0.68rem; font-weight: 700;
}
.yoga-maha    { background: #fef9c3; color: #854d0e; border: 1px solid #f5c842; }
.yoga-dainya  { background: #fee2e2; color: #7f1d1d; border: 1px solid #fca5a5; }
.yoga-kahala  { background: var(--cream2, #fdf0e0); color: var(--brown-mid, #6b3a2a); border: 1px solid var(--gold-light, #d4a96a); }

/* ── Graha Drishti aspect pills ── */
.kundali-asp-wrap {
  display: flex; flex-wrap: wrap; gap: 5px;
}
.asp-pill {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 12px; font-size: 0.75rem;
  white-space: nowrap;
}
.asp-full    { background: var(--cream2, #fdf0e0); border: 1px solid var(--gold-light, #d4a96a); color: var(--brown-dark, #3b1f0a); }
.asp-special { background: #fff9e6; border: 1.5px solid var(--gold, #f5c842); color: #7c4700; font-weight: 600; }
.asp-dot     { font-size: 0.6rem; }
```

- [ ] **Step 2: Verify no syntax errors**

Open the browser at `http://127.0.0.1:8080/muhoortam/` (serve with `cd /Users/schinta/telugu-panchang/docs && python3 -m http.server 8080`). Open browser console — zero JS errors. Page loads as before. Existing Kundali panel (if opened) still works.

- [ ] **Step 3: Commit**

```bash
cd /Users/schinta/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "style: add CSS for kundali analysis sections (badges, dosha cards, aspect pills)"
```

---

## Task 2: Rewrite `_renderKundaliBody` — Full 6-Section Layout

**Files:**
- Modify: `docs/muhoortam/index.html` — function `_renderKundaliBody` (~line 2542)

- [ ] **Step 1: Replace the entire `_renderKundaliBody` function**

Find and replace everything from `function _renderKundaliBody(chart, profile) {` through its closing `}` (ending at line ~2644, just before `function _renderDashaAccordion`) with the following:

```js
function _renderKundaliBody(chart, profile) {
  const body = document.getElementById("kundaliBody");
  if (!body) return;

  const RASHI_TE = ["మేషం","వృషభం","మిథునం","కర్కాటకం","సింహం","కన్య",
                    "తులం","వృశ్చికం","ధనుస్సు","మకరం","కుంభం","మీనం"];
  const PLANET_LABELS = {
    ravi:"☀️ రవి", chandra:"🌙 చంద్ర", kuja:"♂ కుజ", budha:"☿ బుధ",
    guru:"♃ గురు", shukra:"♀ శుక్ర", shani:"♄ శని", rahu:"☊ రాహు", ketu:"☋ కేతు"
  };
  const PLANET_SHORT = {
    ravi:"రవి", chandra:"చంద్ర", kuja:"కుజ", budha:"బుధ",
    guru:"గురు", shukra:"శుక్ర", shani:"శని", rahu:"రా", ketu:"కే"
  };
  const PLANET_ORDER = ["ravi","chandra","kuja","budha","guru","shukra","shani","rahu","ketu"];
  const STRENGTH_LABELS = {
    exalted: ["ఉచ్చ", "str-exalted"],
    debilitated: ["నీచ", "str-debilitated"],
    own: ["స్వక్షేత్ర", "str-own"],
    moolatrikona: ["మూలత్రికోణ", "str-moolatrikona"],
    combust: ["అస్తమయ", "str-combust"],
    normal: ["సాధారణ", "str-normal"]
  };

  const bp = chart.birth_panchang || {};
  const pd = chart.planet_details || {};
  const dobDisplay = (profile.dob || "").split("-").reverse().join("/");

  // ── Print cover (hidden on screen) ──────────────────────────────────────
  const printCover = `
    <div class="kundali-print-cover">
      <div class="kpc-om">🕉</div>
      <div class="kpc-heading">జాతక కుండలి</div>
      <div class="kpc-subheading">Telugu Muhurtam · Godavari Sampradaya</div>
      <div class="kpc-name">${_escHtml(profile.name || "")}</div>
      <div class="kpc-info-grid">
        <div class="kpc-info-item"><span class="kpc-info-label">జన్మ తేదీ</span><span class="kpc-info-val">${dobDisplay || "—"}</span></div>
        <div class="kpc-info-item"><span class="kpc-info-label">జన్మ సమయం</span><span class="kpc-info-val">${profile.time || "—"}</span></div>
        <div class="kpc-info-item"><span class="kpc-info-label">జన్మ స్థలం</span><span class="kpc-info-val">${_escHtml(profile.place || "—")}</span></div>
      </div>
      <div class="kpc-divider"></div>
      <div class="kpc-astro-boxes">
        <div class="kpc-astro-box"><div class="kpc-astro-label">నక్షత్రం</div><div class="kpc-astro-val">${chart.janma_nakshatra_te || "—"}${chart.janma_nakshatra_padam ? " · " + chart.janma_nakshatra_padam + "వ పాదం" : ""}</div></div>
        <div class="kpc-astro-box"><div class="kpc-astro-label">రాశి</div><div class="kpc-astro-val">${chart.janma_rashi_te || "—"}</div></div>
        <div class="kpc-astro-box"><div class="kpc-astro-label">లగ్నం</div><div class="kpc-astro-val">${chart.lagna_te || "—"}</div></div>
      </div>
      <div class="kpc-panchang">
        <span><b>తిథి:</b> ${bp.tithi_te || "—"}</span>
        <span><b>వారం:</b> ${bp.vaara_te || "—"}</span>
        <span><b>నక్షత్రం:</b> ${bp.nakshatra_te || "—"}</span>
        <span><b>యోగం:</b> ${bp.yoga_te || "—"}</span>
        <span><b>కరణం:</b> ${bp.karanam_te || "—"}</span>
      </div>
    </div>`;

  // ── Section 1: D-1 + D-9 charts ─────────────────────────────────────────
  const d1Html = renderHoroscopeChart(chart.planet_rashis || {}, chart.lagna_idx ?? 0);
  const d9Html = renderHoroscopeChart(chart.navamsa_rashis || {}, null);
  const sec1 = `
    <div class="kundali-section">
      <div class="kundali-section-header">🗺 జన్మ చక్రాలు</div>
      <div class="kundali-section-body">
        <div class="kundali-charts-row">
          <div class="kundali-chart-col">
            <div class="kundali-chart-label">D-1 జన్మ చక్రం</div>
            ${d1Html}
          </div>
          <div class="kundali-chart-col">
            <div class="kundali-chart-label">D-9 నవాంశ చక్రం</div>
            ${d9Html}
          </div>
        </div>
      </div>
    </div>`;

  // ── Section 2: Enhanced planet table ────────────────────────────────────
  let ptRows = "";
  for (const name of PLANET_ORDER) {
    const d = pd[name] || {};
    const ri = d.rashi_idx ?? (chart.planet_rashis || {})[name] ?? 0;
    const retro = d.retrograde ? '<sup class="kundali-retro">వ</sup>' : "";
    const nak = d.nakshatra_te ? `${d.nakshatra_te} · ${d.nakshatra_pada || ""}` : "—";
    const lord = d.nakshatra_lord || "—";
    const [strLabel, strCls] = STRENGTH_LABELS[d.strength] || ["—", "str-normal"];
    const d9Rashi = d.navamsa_rashi_te || (chart.navamsa_rashis ? RASHI_TE[chart.navamsa_rashis[name]] : "—") || "—";
    ptRows += `<tr>
      <td>${PLANET_LABELS[name] || name}${retro}</td>
      <td>${RASHI_TE[ri] || ri}</td>
      <td>${nak}</td>
      <td>${lord}</td>
      <td><span class="str-badge ${strCls}">${strLabel}</span></td>
      <td>${d9Rashi}</td>
    </tr>`;
  }
  const sec2 = `
    <div class="kundali-section">
      <div class="kundali-section-header">🪐 గ్రహ స్థితి</div>
      <div class="kundali-section-body">
        <div class="kundali-pt-scroll">
          <table class="kundali-pt">
            <thead><tr>
              <th>గ్రహం</th><th>రాశి</th><th>నక్షత్రం · పాద</th>
              <th>నక్ష. స్వామి</th><th>బలం</th><th>D-9 రాశి</th>
            </tr></thead>
            <tbody>${ptRows}</tbody>
          </table>
        </div>
        <div class="kundali-pt-hint">← స్వైప్ చేయండి</div>
        <div style="font-size:0.68rem;color:var(--text-2,#888);margin-top:4px">వ = వక్రి (retrograde)</div>
      </div>
    </div>`;

  // ── Section 3: Birth panchang strip ─────────────────────────────────────
  const sec3 = `
    <div class="kundali-birth-strip">
      <span><b>నక్షత్రం:</b> ${chart.janma_nakshatra_te || "—"}${chart.janma_nakshatra_padam ? " " + chart.janma_nakshatra_padam + "వ పాదం" : ""}</span>
      <span><b>రాశి:</b> ${chart.janma_rashi_te || "—"}</span>
      <span><b>లగ్నం:</b> ${chart.lagna_te || "—"}</span>
      <span><b>తిథి:</b> ${bp.tithi_te || "—"}</span>
      <span><b>వారం:</b> ${bp.vaara_te || "—"}</span>
      <span><b>యోగం:</b> ${bp.yoga_te || "—"}</span>
      <span><b>కరణం:</b> ${bp.karanam_te || "—"}</span>
    </div>`;

  // ── Section 4: Doshas & Parivartana yogas ───────────────────────────────
  // Mangala Dosha card
  const md = chart.mangala_dosha || {};
  let mdDetail = "";
  if (md.present) {
    const froms = [];
    if (md.from_lagna) froms.push(`లగ్నం నుండి ${md.kuja_house_lagna}వ భావం`);
    if (md.from_moon)  froms.push(`చంద్రుని నుండి ${md.kuja_house_moon}వ భావం`);
    if (md.from_venus) froms.push(`శుక్రుని నుండి ${md.kuja_house_venus}వ భావం`);
    mdDetail = froms.join(", ");
  }
  const mdCard = md.present
    ? `<div class="kundali-dosha-card danger"><div class="dc-title">🔴 మాంగళిక దోషం</div><div>${mdDetail}</div><div style="margin-top:4px;font-size:0.75rem">తీవ్రత: ${md.severity || "—"}</div></div>`
    : `<div class="kundali-dosha-card safe"><div class="dc-title">✅ మాంగళిక దోషం లేదు</div></div>`;

  // Kala Sarpa card
  const ks = chart.kala_sarpa_dosha || {};
  const ksCard = ks.present
    ? `<div class="kundali-dosha-card danger"><div class="dc-title">🔴 కాళసర్ప దోషం</div><div>${ks.type === "kalamrita" ? "కాళామృత" : "కాళసర్ప"}</div><div style="margin-top:4px;font-size:0.75rem">రాహు: ${ks.rahu_rashi_te || "—"} · కేతు: ${ks.ketu_rashi_te || "—"}</div></div>`
    : `<div class="kundali-dosha-card safe"><div class="dc-title">✅ కాళసర్ప దోషం లేదు</div></div>`;

  // Parivartana card
  const yogas = chart.parivartana_yogas || [];
  const YOGA_TYPE_LABELS = { maha: ["మహా పరివర్తన", "yoga-maha"], dainya: ["దైన్య పరివర్తన", "yoga-dainya"], kahala: ["కహళ పరివర్తన", "yoga-kahala"] };
  const yogaItems = yogas.length === 0
    ? `<div style="font-size:0.78rem;color:var(--text-2,#888)">పరివర్తన యోగాలు లేవు</div>`
    : yogas.map(y => {
        const [label, cls] = YOGA_TYPE_LABELS[y.type] || ["పరివర్తన", "yoga-kahala"];
        return `<div class="kundali-yoga-item"><span>${PLANET_SHORT[y.planet_a]||y.planet_a} ↔ ${PLANET_SHORT[y.planet_b]||y.planet_b}</span><span class="yoga-badge ${cls}">${label}</span></div>`;
      }).join("");
  const yogaCard = `<div class="kundali-dosha-card info"><div class="dc-title">♻️ పరివర్తన యోగాలు</div>${yogaItems}</div>`;

  const sec4 = `
    <div class="kundali-section">
      <div class="kundali-section-header">⚠️ దోషాలు & యోగాలు</div>
      <div class="kundali-section-body">
        <div class="kundali-dosha-row">
          ${mdCard}${ksCard}${yogaCard}
        </div>
      </div>
    </div>`;

  // ── Section 5: Graha Drishti ─────────────────────────────────────────────
  const aspects = chart.graha_drishti || [];
  const aspPills = aspects.length === 0
    ? `<div style="font-size:0.78rem;color:var(--text-2,#888)">దృష్టి సమాచారం లేదు</div>`
    : aspects.map(a => {
        const cls = a.type === "special" ? "asp-special" : "asp-full";
        const dot = a.type === "special" ? "◆" : "●";
        return `<span class="asp-pill ${cls}"><span class="asp-dot">${dot}</span>${PLANET_SHORT[a.from]||a.from} → ${PLANET_SHORT[a.to]||a.to} <span style="font-size:0.68rem;opacity:0.75">${a.aspect_house}వ</span></span>`;
      }).join("");
  const sec5 = `
    <div class="kundali-section">
      <div class="kundali-section-header">👁 గ్రహ దృష్టి</div>
      <div class="kundali-section-body">
        <div class="kundali-asp-wrap">${aspPills}</div>
        <div style="font-size:0.65rem;color:var(--text-2,#888);margin-top:6px">● పూర్ణ దృష్టి &nbsp; ◆ విశేష దృష్టి</div>
      </div>
    </div>`;

  // ── Section 6: Dasha accordion ──────────────────────────────────────────
  const dashaHtml = _renderDashaAccordion(
    chart.vimshottari_dasha || [], profile.dob || "",
    chart.planet_rashis || {}, chart.lagna_idx ?? 0
  );
  const sec6 = `
    <div class="kundali-section">
      <div class="kundali-section-header">⏳ వింశోత్తరి దశలు — 120 సంవత్సరాల పూర్ణ పట్టిక</div>
      ${dashaHtml}
    </div>`;

  body.innerHTML = printCover + sec1 + sec2 + sec3 + sec4 + sec5 + sec6;
}
```

- [ ] **Step 2: Quick sanity — verify the old function is gone**

```bash
grep -n "kundali-planet-table-wrap\|kundali-dasha-header" /Users/schinta/telugu-panchang/docs/muhoortam/index.html
```

Expected: zero matches (both class names were part of the old function body). If either still appears, the replace was incomplete.

- [ ] **Step 3: Serve and open a Kundali**

```bash
cd /Users/schinta/telugu-panchang/docs && python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/muhoortam/` in a browser. Go to the People tab, add a person with known birth details, click "జాతకం చూడండి". Verify in the browser console: zero JS errors. Verify all 6 section headers are visible: "🗺 జన్మ చక్రాలు", "🪐 గ్రహ స్థితి", "⚠️ దోషాలు & యోగాలు", "👁 గ్రహ దృష్టి", "⏳ వింశోత్తరి దశలు".

- [ ] **Step 4: Commit**

```bash
cd /Users/schinta/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "feat: rewrite kundali panel with 6-section scroll layout (D-1+D-9, planet table, doshas, aspects)"
```

---

## Task 3: Update Print CSS for New Sections

**Files:**
- Modify: `docs/muhoortam/index.html` — `@media print` block (~line 256)

- [ ] **Step 1: Add print rules for new components**

Find the existing `@media print` block. After the last rule in the block (around line 320, before the closing `}`), insert:

```css
  /* New section layout */
  body.kundali-printing .kundali-section { break-inside: avoid; margin-bottom: 12pt; }
  body.kundali-printing .kundali-section-header { font-size: 11pt; padding: 6px 10px; }
  body.kundali-printing .kundali-section-body { padding: 10px; }

  /* Charts row: side by side in print */
  body.kundali-printing .kundali-charts-row { flex-wrap: nowrap; gap: 16pt; }
  body.kundali-printing .kundali-chart-col { flex: 1; }

  /* Planet table */
  body.kundali-printing .kundali-pt { font-size: 10pt; width: 100%; }
  body.kundali-printing .kundali-pt th,
  body.kundali-printing .kundali-pt td { padding: 5px 7px; font-size: 10pt; }
  body.kundali-printing .kundali-pt-hint { display: none !important; }
  body.kundali-printing .str-badge { font-size: 9pt; padding: 1px 5px; }

  /* Dosha cards: row in print */
  body.kundali-printing .kundali-dosha-row { flex-wrap: nowrap; gap: 10pt; }
  body.kundali-printing .kundali-dosha-card { font-size: 10pt; }

  /* Aspect pills */
  body.kundali-printing .kundali-asp-wrap { gap: 4pt; }
  body.kundali-printing .asp-pill { font-size: 9pt; padding: 2px 7px; }

  /* Dasha section: each row on its own page (pre-existing break-before) */
  body.kundali-printing .kundali-section:last-child .kundali-section-header {
    border-radius: 6px; margin-bottom: 8pt;
  }
```

Also find the two existing rules referencing `.kundali-dasha-header` and `.kundali-planet-table-wrap` in the print block and **remove them** — they reference old class names that no longer exist. Search for:

```css
body.kundali-printing .kundali-planet-table-wrap { flex: 1; }
```
and
```css
body.kundali-printing .kundali-planet-table {
```
and remove/replace those blocks (they refer to `.kundali-planet-table-wrap` and `.kundali-planet-table` which the new code no longer uses in the same way).

- [ ] **Step 2: Test PDF export**

Open the Kundali panel for a person. Click "PDF డౌన్‌లోడ్" (or use browser print). Verify:
- Cover page shows first with person's name / nakshatra
- D-1 and D-9 charts appear side by side on second page
- Planet table is fully readable (not cut off)
- Dosha cards are on same page, not broken mid-card
- Each Mahadasha still starts on its own page

- [ ] **Step 3: Commit**

```bash
cd /Users/schinta/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "style: update print CSS for new kundali section layout"
```

---

## Task 4: Run Backend Tests + Deploy

**Files:** No changes — verify existing tests still pass, then push to deploy.

- [ ] **Step 1: Run backend tests**

```bash
cd /Users/schinta/telugu-panchang/panchang-api && python3 -m pytest tests/test_muhoortam.py tests/test_analysis.py tests/test_dasha.py -v 2>&1 | tail -20
```

Expected: all 122 tests pass (94 + 15 + 13). The 9 pre-existing failures in other test files are **not regressions** — ignore them.

- [ ] **Step 2: Push to deploy**

```bash
cd /Users/schinta/telugu-panchang
git push origin master
```

Wait ~3 minutes for GitHub Actions to complete.

- [ ] **Step 3: Production smoke test**

```bash
curl -s -X POST https://h3dp7amvn9.execute-api.ap-south-1.amazonaws.com/muhoortam/birth-chart \
  -H "Content-Type: application/json" \
  -d '{"dob":"15/08/1990","time":"10:30","place":"Rajahmundry, Andhra Pradesh, India"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('graha_drishti:', len(d.get('graha_drishti',[])), 'aspects'); print('mangala_dosha:', d.get('mangala_dosha',{}).get('present')); print('navamsa_rashis keys:', list(d.get('navamsa_rashis',{}).keys())[:3])"
```

Expected output (exact values vary by birth data):
```
graha_drishti: N aspects    ← some number > 0
mangala_dosha: True/False
navamsa_rashis keys: ['ravi', 'chandra', 'kuja']
```

- [ ] **Step 4: Verify live site**

Open `https://sairamchinta1510.github.io/telugu-panchang/muhoortam/`. Add a person, open their Kundali. All 6 section headers visible. No console errors.

---

## Self-Review Checklist

After writing this plan, verified:

| Check | Result |
|-------|--------|
| Spec requirement: D-1 + D-9 charts side by side | ✅ Task 2, sec1 |
| Spec requirement: enhanced planet table (nakshatra, lord, strength, D-9) | ✅ Task 2, sec2 |
| Spec requirement: panchang strip | ✅ Task 2, sec3 (preserved from existing code) |
| Spec requirement: dosha cards (Mangala, Kala Sarpa, Parivartana) | ✅ Task 2, sec4 |
| Spec requirement: aspect pills (full vs special) | ✅ Task 2, sec5 |
| Spec requirement: dasha accordion preserved | ✅ Task 2, sec6 |
| Spec requirement: mobile responsive (charts stack, table scrolls) | ✅ Task 1 CSS (`flex: 1 1 200px`, `overflow-x: auto`) |
| Spec requirement: print CSS | ✅ Task 3 |
| No TBD / placeholders | ✅ |
| Type consistency (`PLANET_SHORT` used in sec4 and sec5) | ✅ defined once in Task 2, used in both sections |
| Old class names removed from print CSS | ✅ Task 3 Step 1 explicitly calls this out |
| Backend tests pass before deploy | ✅ Task 4 Step 1 |
