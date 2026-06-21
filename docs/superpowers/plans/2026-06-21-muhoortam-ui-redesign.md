# Muhoortam UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Muhoortam wizard into a clean 3-step flow (People → Event → Results) with localStorage saved profiles, past-date support, and an integrated single-date check feature.

**Architecture:** Frontend-only redesign of `docs/muhoortam/index.html` plus deployment of the already-written `/muhoortam/check` backend endpoint. All profile data stored in browser `localStorage`. Date check mode shares the same Step 1 (persons) and Step 2 (event) as the range find mode.

**Tech Stack:** Vanilla HTML/JS, Flatpickr 4.6.13, Nominatim autocomplete, AWS Lambda (Python), GitHub Pages, GitHub Actions CI/CD

---

## File Map

| File | Change |
|------|--------|
| `panchang-api/compute/muhurta_finder.py` | Already has `check_muhurta_day()` — fix test mock, commit |
| `panchang-api/handler_muhoortam.py` | Already has `/muhoortam/check` handler — commit |
| `panchang-api/template.yaml` | Already has `MuhoortamCheck` route — commit |
| `panchang-api/tests/test_muhoortam.py` | Fix failing `test_check_muhurta_day_time_in_rahu_kalam` |
| `docs/muhoortam/index.html` | Major restructure — 9 targeted edit sections below |

---

## Task 1: Fix failing test + deploy `/muhoortam/check`

**Files:**
- Modify: `panchang-api/tests/test_muhoortam.py` (function `_load_finder`)

The mock `fake_jd_to_local_datetime` always returns 06:00 for both sunrise AND sunset. `fake_get_sunrise_sunset` returns `(jd, jd+0.5)` — so set_jd has a fractional part. Fix the mock to return 18:00 for set_jd.

- [ ] **Step 1: Fix `fake_jd_to_local_datetime` in `_load_finder`**

Find this function in `tests/test_muhoortam.py`:
```python
from datetime import datetime as real_dt
def fake_jd_to_local_datetime(jd, tz):
    # July 16, 2026 is a Thursday (weekday=3 → sun_idx=4)
    return real_dt(2026, 7, 16, 6, 0)
```

Replace with:
```python
from datetime import datetime as real_dt
def fake_jd_to_local_datetime(jd, tz):
    # rise_jd is integer (float(day)), set_jd is integer+0.5
    if jd % 1 != 0:
        return real_dt(2026, 7, 16, 18, 0)   # sunset
    return real_dt(2026, 7, 16, 6, 0)         # sunrise, Thursday → sun_idx=4
```

- [ ] **Step 2: Run all tests**

```bash
cd panchang-api && python3 -m pytest tests/test_muhoortam.py -q
```

Expected: `45 passed`

- [ ] **Step 3: Commit and push all pending backend changes**

```bash
cd panchang-api && python3 -m pytest tests/test_muhoortam.py -q  # verify first
cd ..
git add panchang-api/
git commit -m "feat(muhoortam): add /muhoortam/check endpoint with day+time analysis

- check_muhurta_day() in muhurta_finder.py returns good/bad factor breakdown
- /muhoortam/check POST handler in handler_muhoortam.py
- MuhoortamCheck route added to template.yaml
- 10 new tests, all passing (45 total)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

Expected: GitHub Actions triggers deploy workflow (watch at github.com/sairamchinta1510/telugu-panchang/actions). Lambda update takes ~5 min.

---

## Task 2: Update step bar from 4 to 3 steps

**Files:**
- Modify: `docs/muhoortam/index.html` (step bar HTML ~line 550, `setStep()` JS ~line 710)

- [ ] **Step 1: Replace step bar HTML**

Find:
```html
<div class="step-bar">
  <div class="step-dot active" id="sd1">1</div>
  <div class="step-line" id="sl1"></div>
  <div class="step-dot" id="sd2">2</div>
  <div class="step-line" id="sl2"></div>
  <div class="step-dot" id="sd3">3</div>
  <div class="step-line" id="sl3"></div>
  <div class="step-dot" id="sd4">4</div>
</div>
```

Replace with:
```html
<div class="step-bar">
  <div class="step-dot active" id="sd1">1</div>
  <div class="step-line" id="sl1"></div>
  <div class="step-dot" id="sd2">2</div>
  <div class="step-line" id="sl2"></div>
  <div class="step-dot" id="sd3">3</div>
</div>
```

- [ ] **Step 2: Replace `setStep()` JS function**

Find:
```js
function setStep(n) {
  [1,2,3,4].forEach(i => {
    const d = document.getElementById("sd"+i);
    d.classList.remove("active","done");
    if(i < n) d.classList.add("done");
    else if(i === n) d.classList.add("active");
  });
  [1,2,3].forEach(i => {
    const l = document.getElementById("sl"+i);
    l.classList.toggle("done", i < n);
  });
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.getElementById("panel"+n).classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
```

Replace with:
```js
function setStep(n) {
  [1,2,3].forEach(i => {
    const d = document.getElementById("sd"+i);
    d.classList.remove("active","done");
    if(i < n) d.classList.add("done");
    else if(i === n) d.classList.add("active");
  });
  [1,2].forEach(i => {
    const l = document.getElementById("sl"+i);
    l.classList.toggle("done", i < n);
  });
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.getElementById("panel"+n).classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
```

- [ ] **Step 3: No test needed (visual change) — commit**

```bash
git add docs/muhoortam/index.html
git commit -m "ui: step bar 4→3 steps"
```

---

## Task 3: Add localStorage profile JS functions

**Files:**
- Modify: `docs/muhoortam/index.html` (JS section, near top of `<script>`)

- [ ] **Step 1: Add global variables and profile functions**

After the line `let selectedCeremony = null, allResults = [], personCount = 0;`, add:

```js
let savedProfileCharts = {};   // personBlockId → pre-computed birth chart
const PROFILES_KEY = "muhurta_profiles";

function loadProfiles() {
  try { return JSON.parse(localStorage.getItem(PROFILES_KEY) || "[]"); }
  catch { return []; }
}

function saveProfileToStorage(profile) {
  const profiles = loadProfiles();
  const idx = profiles.findIndex(p => p.name === profile.name);
  if (idx >= 0) profiles[idx] = profile;
  else profiles.push(profile);
  localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles));
  renderProfileChips();
}

function deleteProfile(name) {
  if (!confirm(`"${name}" ని తొలగించాలా?`)) return;
  const profiles = loadProfiles().filter(p => p.name !== name);
  localStorage.setItem(PROFILES_KEY, JSON.stringify(profiles));
  renderProfileChips();
}

function renderProfileChips() {
  const container = document.getElementById("profileChips");
  if (!container) return;
  const profiles = loadProfiles();
  if (!profiles.length) { container.style.display = "none"; return; }
  container.style.display = "";
  container.innerHTML = `
    <div style="font-size:0.7rem;font-weight:700;color:var(--brown-light);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">💾 Saved Profiles</div>
    <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:4px">
      ${profiles.map((p,i) => `
        <div style="background:var(--gold-light);border:1.5px solid var(--gold);border-radius:12px;padding:8px 10px;flex-shrink:0;min-width:110px">
          <div style="font-weight:700;font-size:0.82rem;color:var(--maroon);cursor:pointer" onclick="addFromProfile(${i})">${p.name}</div>
          ${p.birthChart ? `<div style="font-size:0.7rem;color:var(--brown-mid);cursor:pointer" onclick="addFromProfile(${i})">🌟 ${p.birthChart.janma_nakshatra_te}${p.birthChart.janma_nakshatra_padam ? " "+p.birthChart.janma_nakshatra_padam+"వ పాదం" : ""}</div>` : ""}
          <div style="font-size:0.65rem;color:var(--brown-light);margin-top:4px;cursor:pointer" onclick="deleteProfile('${p.name.replace(/'/g,"\\'")}')">✕ తొలగించు</div>
        </div>`).join("")}
    </div>`;
}

function addFromProfile(idx) {
  const profiles = loadProfiles();
  const p = profiles[idx];
  if (!p) return;
  addPerson();
  const id = personCount;
  document.getElementById("pname"+id).value = p.name;
  if (p.dob) {
    const input = document.getElementById("dob"+id);
    const fp = input._flatpickr;
    if (fp) fp.setDate(p.dob, true); else input.value = p.dob;
  }
  if (p.time) document.getElementById("time"+id).value = p.time;
  if (p.place) document.getElementById("place"+id).value = p.place;
  if (p.birthChart) savedProfileCharts[id] = p.birthChart;
}

async function savePersonProfile(idx) {
  showError("");
  const name   = document.getElementById("pname"+idx)?.value.trim();
  const dobRaw = document.getElementById("dob"+idx)?.value.trim();
  const time   = document.getElementById("time"+idx)?.value.trim();
  const place  = document.getElementById("place"+idx)?.value.trim();
  if (!name || !dobRaw || !time || !place) {
    showError("పేరు, తేదీ, సమయం మరియు స్థలం నమోదు చేయండి");
    return;
  }
  const [y,m,d] = dobRaw.split("-");
  const btn = document.querySelector(`#person${idx} .save-profile-btn`);
  if (btn) btn.textContent = "⏳ ...";
  try {
    const r = await fetch(API_BASE+"/muhoortam/birth-chart", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ name, dob:`${d}/${m}/${y}`, time, place })
    });
    if (!r.ok) throw new Error(await r.text());
    const birthChart = await r.json();
    saveProfileToStorage({ name, dob: dobRaw, time, place, birthChart });
    if (btn) { btn.textContent = "✓ Saved!"; setTimeout(()=>{ btn.textContent="💾 Save Profile"; },2500); }
  } catch(e) {
    if (btn) btn.textContent = "💾 Save Profile";
    showError("Profile save failed: " + e.message);
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: localStorage profile functions (save/load/delete/render)"
```

---

## Task 4: Rewrite Panel 1 — People with saved profiles

**Files:**
- Modify: `docs/muhoortam/index.html` (Panel 1 HTML)

The current Panel 1 is the ceremony/date panel. Replace it entirely with the persons panel (currently Panel 2). Move person content here and add profile chips + save button.

- [ ] **Step 1: Replace Panel 1 HTML**

Find the entire `<!-- PANEL 1 — Ceremony Details -->` block (from `<div id="panel1"` to its closing `</div>`) and replace with:

```html
<!-- ══════════════════════════════════════════════════
     PANEL 1 — People
══════════════════════════════════════════════════ -->
<div id="panel1" class="panel active">
  <div class="section-title">వ్యక్తుల వివరాలు</div>

  <!-- Saved profiles chips (hidden until profiles exist) -->
  <div id="profileChips" style="display:none;background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);padding:14px;margin-bottom:12px;border:1px solid rgba(196,154,108,0.2)"></div>

  <div id="personList"></div>
  <button class="btn-add" id="addPersonBtn" onclick="addPerson()">
    ＋ మరో వ్యక్తిని జోడించండి (గరిష్టం 6)
  </button>
  <button class="btn-primary" onclick="goPanel2()">తదుపరి దశ →</button>
</div>
```

- [ ] **Step 2: Add 💾 Save Profile button to `addPerson()` person block template**

In `addPerson()`, find:
```js
    <div class="field" style="margin-top:10px;margin-bottom:0">
```

And replace the full `div.innerHTML` template. The key addition is a save button after the place field. Find the closing of the template (after the `</div>` for `acP${idx}`) and add before the closing backtick:

```js
    <button class="save-profile-btn" style="margin-top:8px;background:var(--gold-light);border:1px solid var(--gold);border-radius:8px;padding:6px 14px;font-size:0.75rem;font-family:inherit;color:var(--brown);cursor:pointer" onclick="savePersonProfile(${idx})">💾 Save Profile</button>
```

- [ ] **Step 3: Update `goPanel2()` to validate persons then go to panel 2**

Find the existing `function goPanel2()` and replace with:

```js
function goPanel2() {
  showError("");
  const blocks = document.querySelectorAll(".person-block");
  if (!blocks.length) { showError("కనీసం ఒక వ్యక్తి వివరాలు నమోదు చేయండి"); return; }
  for (const b of blocks) {
    const id = b.id.replace("person","");
    const dobRaw = document.getElementById("dob"+id)?.value.trim();
    const time   = document.getElementById("time"+id)?.value.trim();
    const place  = document.getElementById("place"+id)?.value.trim();
    if (!dobRaw || !time || !place) { showError("అన్ని వ్యక్తుల వివరాలు పూరించండి"); return; }
  }
  setStep(2);
}
```

- [ ] **Step 4: Call `renderProfileChips()` after the `addPerson()` call at the bottom of the script**

Find the last line `addPerson();` and change to:
```js
addPerson();
renderProfileChips();
```

- [ ] **Step 5: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: panel 1 = persons with saved profile chips and save button"
```

---

## Task 5: Rewrite Panel 2 — Event details with date mode toggle

**Files:**
- Modify: `docs/muhoortam/index.html` (Panel 2 HTML + JS)

Replace current Panel 2 (persons) with the event details form. Add date mode toggle.

- [ ] **Step 1: Replace Panel 2 HTML entirely**

Find the entire `<!-- PANEL 2 — Birth Details -->` block and replace with:

```html
<!-- ══════════════════════════════════════════════════
     PANEL 2 — Event Details
══════════════════════════════════════════════════ -->
<div id="panel2" class="panel">
  <div class="section-title">వేడుక వివరాలు</div>

  <div class="card">
    <div class="field">
      <label>వేడుక రకం</label>
      <div class="ceremony-grid">
        <div class="ceremony-card" data-type="vivaha" onclick="selectCeremony(this)">
          <span class="cer-icon">💒</span>
          <div class="cer-name">వివాహం</div>
        </div>
        <div class="ceremony-card" data-type="gruha_pravesam" onclick="selectCeremony(this)">
          <span class="cer-icon">🏠</span>
          <div class="cer-name">గృహ ప్రవేశం</div>
        </div>
        <div class="ceremony-card" data-type="upanayanam" onclick="selectCeremony(this)">
          <span class="cer-icon">🪡</span>
          <div class="cer-name">ఉపనయనం</div>
        </div>
        <div class="ceremony-card" data-type="pooja" onclick="selectCeremony(this)">
          <span class="cer-icon">🪔</span>
          <div class="cer-name">పూజ</div>
        </div>
      </div>
    </div>

    <div class="field">
      <label>వేడుక జరిగే స్థలం</label>
      <div class="ac-wrap">
        <div class="input-icon-wrap">
          <span class="icon">📍</span>
          <input type="text" id="ceremonyPlace" placeholder="నగరం వెతకండి... (ఉదా: Hyderabad)"
                 oninput="acSearch(this,'acCeremony')" autocomplete="off">
        </div>
        <div class="ac-list" id="acCeremony"></div>
      </div>
    </div>

    <div class="field">
      <label>తేదీ ఎంచుకోండి</label>
      <div style="display:flex;background:var(--cream2);border-radius:10px;padding:3px;margin-bottom:10px">
        <button id="tabRange" class="date-tab active" onclick="setDateMode('range')">📅 తేదీ పరిధి</button>
        <button id="tabSingle" class="date-tab" onclick="setDateMode('single')">🔍 నిర్దిష్ట తేదీ తనిఖీ</button>
      </div>

      <!-- Range mode -->
      <div id="dateRangeFields">
        <div class="date-range">
          <div>
            <label style="font-size:0.72rem;color:var(--brown-mid);display:block;margin-bottom:5px">🗓 నుండి</label>
            <input type="text" id="rangeFrom" placeholder="తేదీ ఎంచుకోండి" style="cursor:pointer">
          </div>
          <div>
            <label style="font-size:0.72rem;color:var(--brown-mid);display:block;margin-bottom:5px">🗓 వరకు</label>
            <input type="text" id="rangeTo" placeholder="తేదీ ఎంచుకోండి" style="cursor:pointer">
          </div>
        </div>
      </div>

      <!-- Single date mode -->
      <div id="dateSingleFields" style="display:none">
        <div class="two-col">
          <div class="field" style="margin-bottom:0">
            <label>తనిఖీ చేయాల్సిన తేదీ</label>
            <input type="text" id="checkDate" placeholder="తేదీ ఎంచుకోండి" style="cursor:pointer">
          </div>
          <div class="field" style="margin-bottom:0">
            <label>సమయం (ఐచ్ఛికం)</label>
            <input type="time" id="checkTime" style="padding:11px 10px;font-size:15px">
          </div>
        </div>
      </div>
    </div>
  </div>

  <div style="display:flex;gap:10px;margin-top:4px">
    <button class="btn-outline" style="flex:0 0 auto" onclick="setStep(1);showError('')">← వెనక్కి</button>
    <button id="findBtn" class="btn-primary" style="flex:1" onclick="startCompute()">ముహూర్తాలు వెతకండి 🔍</button>
  </div>
</div>
```

- [ ] **Step 2: Add CSS for date tabs**

Inside the `<style>` block, add after existing `.date-range` rule:

```css
.date-tab {
  flex: 1; padding: 9px 4px; border: none; background: transparent; border-radius: 8px;
  font-family: inherit; font-size: 0.8rem; font-weight: 600; color: var(--brown-mid); cursor: pointer;
  transition: var(--transition);
}
.date-tab.active { background: var(--saffron); color: white; box-shadow: 0 2px 8px rgba(193,68,14,0.3); }
```

- [ ] **Step 3: Add `dateMode` global and `setDateMode()` function**

After `let selectedCeremony = null, allResults = [], personCount = 0;`, add:

```js
let dateMode = "range"; // "range" | "single"

function setDateMode(mode) {
  dateMode = mode;
  document.getElementById("tabRange").classList.toggle("active", mode === "range");
  document.getElementById("tabSingle").classList.toggle("active", mode === "single");
  document.getElementById("dateRangeFields").style.display = mode === "range" ? "" : "none";
  document.getElementById("dateSingleFields").style.display = mode === "single" ? "" : "none";
  document.getElementById("findBtn").textContent =
    mode === "range" ? "ముహూర్తాలు వెతకండి 🔍" : "తనిఖీ చేయండి ✓";
}
```

- [ ] **Step 4: Update the default dates IIFE — remove minDate restriction, add checkDate flatpickr**

Find:
```js
  const fpOpts = { dateFormat: "Y-m-d", disableMobile: true, allowInput: false,
    onOpen(_, __, fp) { fp.input.blur(); } };
  flatpickr("#rangeFrom", { ...fpOpts, minDate: "today", defaultDate: todayStr });
  flatpickr("#rangeTo",   { ...fpOpts, minDate: "today", defaultDate: endStr });
```

Replace with:
```js
  const fpOpts = { dateFormat: "Y-m-d", disableMobile: true, allowInput: false,
    onOpen(_, __, fp) { fp.input.blur(); } };
  flatpickr("#rangeFrom", { ...fpOpts, defaultDate: todayStr });
  flatpickr("#rangeTo",   { ...fpOpts, defaultDate: endStr });
  flatpickr("#checkDate", { ...fpOpts });
```

- [ ] **Step 5: Update `goPanel2()` validation (now it validates ceremony/place)**

The old `goPanel2()` checked ceremony/place. Rename the existing logic. The new `goPanel2()` (from Task 4) validates persons. We need a new `startCompute()` guard:

In `startCompute()` add at the top:
```js
  if (!selectedCeremony) { showError("వేడుక రకం ఎంచుకోండి"); return; }
  if (!document.getElementById("ceremonyPlace").value.trim()) { showError("వేడుక స్థలం నమోదు చేయండి"); return; }
  if (dateMode === "range") {
    const from = document.getElementById("rangeFrom").value;
    const to   = document.getElementById("rangeTo").value;
    if (!from || !to) { showError("తేదీ పరిధి నమోదు చేయండి"); return; }
    if (from > to) { showError("'నుండి' తేదీ 'వరకు' తేదీ కంటే తర్వాత ఉండకూడదు"); return; }
  } else {
    if (!document.getElementById("checkDate").value) { showError("తనిఖీ చేయాల్సిన తేదీ నమోదు చేయండి"); return; }
  }
```

- [ ] **Step 6: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: panel 2 = event details with date range/single-date toggle, past dates allowed"
```

---

## Task 6: Rewrite Panel 3 — Combined loading + results

**Files:**
- Modify: `docs/muhoortam/index.html` (Panels 3+4 HTML → single Panel 3)

Remove old Panel 3 (loading) and Panel 4 (results). Replace with a single Panel 3 that handles both states.

- [ ] **Step 1: Replace Panels 3 and 4 HTML with new Panel 3**

Find the `<!-- PANEL 3 — Computing -->` block through to the end of the `<!-- PANEL 4 — Results -->` closing `</div>`, and replace the entire thing with:

```html
<!-- ══════════════════════════════════════════════════
     PANEL 3 — Results (loading + results)
══════════════════════════════════════════════════ -->
<div id="panel3" class="panel">
  <!-- Loading area -->
  <div id="loadingArea" class="card" style="display:none">
    <div class="loading-wrap">
      <span class="lotus-spin">🌸</span>
      <div class="progress-label" id="progressLabel">సిద్ధంగా ఉంది</div>
      <div class="progress-track"><div class="progress-fill" id="progressBar" style="width:0%"></div></div>
      <div class="progress-sub" id="progressSub"></div>
    </div>
  </div>

  <!-- Results hero (range mode) -->
  <div id="resultsHero" class="results-hero" style="display:none">
    <div id="ceremonyTag" class="ceremony-tag"></div>
    <h2 id="resultsTitle"></h2>
    <div id="resultsCount" class="count"></div>
  </div>

  <!-- Kalam warning banner (range mode) -->
  <div class="kalam-banner" id="kalamBanner" style="display:none">
    ⚠️ <strong>గమనిక:</strong> రాహు కాలం, యమగండ కాలం మరియు గులిక కాలం సమయంలో వేడుకలు నిర్వహించవద్దు.
    ప్రతి ముహూర్తం మీద <strong>"వివరాలు చూడండి"</strong> నొక్కి మరింత సమాచారం తెలుసుకోండి.
  </div>

  <!-- Results list (both modes) -->
  <div id="resultsList"></div>

  <!-- Actions row -->
  <div class="actions-row" id="resultsActions" style="display:none">
    <button class="btn-outline" onclick="window.print()">🖨 PDF</button>
    <button class="btn-outline" onclick="setStep(2);showError('')">← వివరాలు మార్చండి</button>
    <button class="btn-outline" onclick="resetWizard()">↺ కొత్తగా</button>
  </div>
</div>
```

- [ ] **Step 2: Add `showLoading()` JS function**

After `function setStep(n)`, add:

```js
function showLoading(on) {
  document.getElementById("loadingArea").style.display = on ? "" : "none";
  document.getElementById("resultsHero").style.display = "none";
  document.getElementById("kalamBanner").style.display = "none";
  document.getElementById("resultsActions").style.display = "none";
  if (on) document.getElementById("resultsList").innerHTML = "";
}
```

- [ ] **Step 3: Update `setProgress()` to work with the new inline loading area**

Find `function setProgress(` and verify it references `progressLabel`, `progressBar`, `progressSub` — these still exist in the new panel 3. No change needed if references are correct.

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: panel 3 = combined loading+results panel"
```

---

## Task 7: Update `startCompute()` — handle both range and single-date modes

**Files:**
- Modify: `docs/muhoortam/index.html` (JS `startCompute()` function)

- [ ] **Step 1: Replace the entire `startCompute()` function**

Find `async function startCompute()` through its closing `}` and replace with:

```js
async function startCompute() {
  showError("");

  // Validate event details
  if (!selectedCeremony) { showError("వేడుక రకం ఎంచుకోండి"); return; }
  if (!document.getElementById("ceremonyPlace").value.trim()) { showError("వేడుక స్థలం నమోదు చేయండి"); return; }
  if (dateMode === "range") {
    const from = document.getElementById("rangeFrom").value;
    const to   = document.getElementById("rangeTo").value;
    if (!from || !to) { showError("తేదీ పరిధి నమోదు చేయండి"); return; }
    if (from > to) { showError("'నుండి' తేదీ 'వరకు' తేదీ కంటే తర్వాత ఉండకూడదు"); return; }
  } else {
    if (!document.getElementById("checkDate").value) { showError("తనిఖీ చేయాల్సిన తేదీ నమోదు చేయండి"); return; }
  }

  // Collect persons
  const blocks = document.querySelectorAll(".person-block");
  const persons = [];
  for (const b of blocks) {
    const id = b.id.replace("person","");
    const name   = document.getElementById("pname"+id)?.value.trim() || `వ్యక్తి ${id}`;
    const dobRaw = document.getElementById("dob"+id)?.value.trim();
    const time   = document.getElementById("time"+id)?.value.trim();
    const place  = document.getElementById("place"+id)?.value.trim();
    if (!dobRaw || !time || !place) { showError("అన్ని వ్యక్తుల వివరాలు పూరించండి"); return; }
    const [y,m,d] = dobRaw.split("-");
    persons.push({ id, name, dob:`${d}/${m}/${y}`, time, place });
  }

  setStep(3);
  showLoading(true);
  setProgress(0, "జన్మ వివరాలు లెక్కిస్తున్నాం...", "");

  // Compute / retrieve birth charts
  const birthCharts = [];
  for (let i = 0; i < persons.length; i++) {
    const p = persons[i];
    if (savedProfileCharts[p.id]) {
      birthCharts.push({ ...savedProfileCharts[p.id], name: p.name });
    } else {
      try {
        const r = await fetch(API_BASE+"/muhoortam/birth-chart", {
          method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({ name: p.name, dob: p.dob, time: p.time, place: p.place })
        });
        if (!r.ok) throw new Error(await r.text());
        birthCharts.push({ ...await r.json(), name: p.name });
      } catch(e) {
        showLoading(false);
        setStep(2);
        showError((p.name)+" వివరాలు లెక్కించడం సాధ్యం కాలేదు: "+e.message);
        return;
      }
    }
  }
  savedBirthCharts = birthCharts;
  savedPersons = persons;

  if (dateMode === "single") {
    await _runCheck(birthCharts);
  } else {
    await _runFind(birthCharts);
  }
}

async function _runCheck(birthCharts) {
  const dateRaw = document.getElementById("checkDate").value;
  const time    = document.getElementById("checkTime").value;
  const place   = document.getElementById("ceremonyPlace").value.trim();
  const [y,m,d] = dateRaw.split("-");
  try {
    const r = await fetch(API_BASE+"/muhoortam/check", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({
        date: `${d}/${m}/${y}`,
        ...(time ? { time } : {}),
        ceremony_place: place,
        ceremony_type: selectedCeremony,
        birth_charts: birthCharts,
      })
    });
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    showLoading(false);
    showCheckResult(data);
  } catch(e) {
    showLoading(false);
    setStep(2);
    showError("తనిఖీ విఫలమైంది: "+e.message);
  }
}

async function _runFind(birthCharts) {
  const fromDate = new Date(document.getElementById("rangeFrom").value);
  const toDate   = new Date(document.getElementById("rangeTo").value);
  const months = [];
  let cur = new Date(fromDate.getFullYear(), fromDate.getMonth(), 1);
  while (cur <= toDate) {
    months.push({ year: cur.getFullYear(), month: cur.getMonth()+1 });
    cur.setMonth(cur.getMonth()+1);
  }
  const place = document.getElementById("ceremonyPlace").value.trim();
  allResults = [];
  for (let i = 0; i < months.length; i++) {
    const { year, month } = months[i];
    setProgress(Math.round(((i+1)/months.length)*100), `${MONTHS_TE[month-1]} ${year} స్కాన్ అవుతోంది`, `${i+1}/${months.length} నెలలు`);
    try {
      const r = await fetch(API_BASE+"/muhoortam/find", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ year, month, ceremony_type: selectedCeremony, ceremony_place: place, birth_charts: birthCharts })
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      allResults.push(...(data.results||[]));
    } catch(e) {
      showLoading(false);
      setStep(2);
      showError("లెక్కింపులో లోపం: "+e.message);
      return;
    }
  }
  showLoading(false);
  showResults();
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: startCompute handles both range-find and single-date-check modes"
```

---

## Task 8: Add `showCheckResult()` and update `showResults()` for new panel structure

**Files:**
- Modify: `docs/muhoortam/index.html` (JS)

- [ ] **Step 1: Add `showCheckResult()` function**

After `function showResults()`, add:

```js
function showCheckResult(data) {
  const list = document.getElementById("resultsList");
  list.innerHTML = "";

  // Birth chart summary
  if (savedBirthCharts.length) {
    const bcDiv = document.createElement("div");
    bcDiv.style.cssText = "background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);padding:16px;margin-bottom:16px;border:1px solid rgba(196,154,108,0.2)";
    bcDiv.innerHTML = `
      <div style="font-size:0.7rem;font-weight:700;color:var(--brown-light);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px">వ్యక్తుల జన్మ వివరాలు</div>
      ${savedBirthCharts.map((bc,i)=>`
        <div style="display:flex;align-items:flex-start;gap:12px;padding:10px;background:var(--cream2);border-radius:10px;margin-bottom:8px">
          <div style="font-size:1.3rem;flex-shrink:0">👤</div>
          <div style="flex:1">
            <div style="font-weight:700;font-size:0.88rem;color:var(--maroon);margin-bottom:6px">${savedPersons[i]?.name||"వ్యక్తి "+(i+1)}</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <span style="background:var(--gold-light);border:1px solid var(--gold);border-radius:20px;padding:3px 10px;font-size:0.76rem;color:var(--brown)">🌟 ${bc.janma_nakshatra_te}${bc.janma_nakshatra_padam?" ("+bc.janma_nakshatra_padam+"వ పాదం)":""}</span>
              <span style="background:#EDE7F6;border:1px solid #B39DDB;border-radius:20px;padding:3px 10px;font-size:0.76rem;color:#4A148C">♈ ${bc.janma_rashi_te}</span>
              <span style="background:#E8F5E9;border:1px solid #A5D6A7;border-radius:20px;padding:3px 10px;font-size:0.76rem;color:#1B5E20">⬆️ ${bc.lagna_te}</span>
            </div>
          </div>
        </div>`).join("")}`;
    list.appendChild(bcDiv);
  }

  // Verdict card
  const verdictMap = {
    good:  { icon:"✅", label:"శుభ ముహూర్తం",   bg:"linear-gradient(135deg,#E8F5E9,#F1F8E9)", border:"#4CAF50", color:"#2E7D32" },
    mixed: { icon:"⚠️", label:"మిశ్రమ ముహూర్తం", bg:"linear-gradient(135deg,#FFF8E1,#FFF3E0)", border:"#FB8C00", color:"#E65100" },
    bad:   { icon:"❌", label:"అశుభ ముహూర్తం",   bg:"linear-gradient(135deg,#FFEBEE,#FFF3E0)", border:"#E53935", color:"#C62828" },
  };
  const v = verdictMap[data.verdict] || verdictMap.bad;

  const card = document.createElement("div");
  card.innerHTML = `
    <div style="background:${v.bg};border:2px solid ${v.border};border-radius:16px;padding:18px;margin-bottom:14px;text-align:center">
      <div style="font-size:2.8rem">${v.icon}</div>
      <div style="font-weight:800;font-size:1.15rem;color:${v.color};margin-top:6px">${v.label}</div>
      <div style="font-size:0.88rem;color:var(--brown-mid);margin-top:6px">${data.date_te} — ${data.vaaram_te}</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:10px">
        <span style="background:var(--gold-light);border:1px solid var(--gold);border-radius:20px;padding:3px 10px;font-size:0.76rem;color:var(--brown)">🌟 ${data.nakshatra_te}</span>
        <span style="background:#EDE7F6;border:1px solid #B39DDB;border-radius:20px;padding:3px 10px;font-size:0.76rem;color:#4A148C">📅 ${data.tithi_te}</span>
        <span style="background:#E3F2FD;border:1px solid #90CAF9;border-radius:20px;padding:3px 10px;font-size:0.76rem;color:#0D47A1">☀️ ${data.masam_te}</span>
      </div>
      <div style="font-size:0.78rem;color:var(--brown-mid);margin-top:8px">🌅 ${data.sunrise} — 🌇 ${data.sunset}</div>
    </div>

    ${data.good_factors.length ? `
    <div style="background:#E8F5E9;border-radius:12px;padding:14px;margin-bottom:10px">
      <div style="font-size:0.7rem;font-weight:700;color:#2E7D32;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">✅ అనుకూల అంశాలు</div>
      ${data.good_factors.map(f=>`<div style="font-size:0.82rem;color:#1B5E20;padding:5px 0;border-bottom:1px solid rgba(0,100,0,0.08)">${f}</div>`).join("")}
    </div>` : ""}

    ${data.bad_factors.length ? `
    <div style="background:#FFEBEE;border-radius:12px;padding:14px;margin-bottom:10px">
      <div style="font-size:0.7rem;font-weight:700;color:#C62828;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">❌ అననుకూల అంశాలు</div>
      ${data.bad_factors.map(f=>`<div style="font-size:0.82rem;color:#B71C1C;padding:5px 0;border-bottom:1px solid rgba(180,0,0,0.08)">${f}</div>`).join("")}
    </div>` : ""}

    ${data.time_issues.length ? `
    <div style="background:#FFF3E0;border-radius:12px;padding:14px;margin-bottom:10px">
      <div style="font-size:0.7rem;font-weight:700;color:#E65100;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">⏰ సమయ విశ్లేషణ</div>
      ${data.time_issues.map(f=>`<div style="font-size:0.82rem;color:#BF360C;padding:5px 0">${f}</div>`).join("")}
    </div>` : ""}

    <div style="background:white;border-radius:12px;padding:14px;border:1px solid rgba(196,154,108,0.2)">
      <div style="font-size:0.7rem;font-weight:700;color:var(--brown-light);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px">⚠️ నివారించాల్సిన సమయాలు</div>
      ${data.rahu_kalam?`<div style="display:flex;justify-content:space-between;font-size:0.8rem;padding:5px 0;border-bottom:1px solid #f0e8d8"><span>🔴 రాహు కాలం</span><span style="font-weight:700">${data.rahu_kalam.start}–${data.rahu_kalam.end}</span></div>`:""}
      ${data.yamaganda?`<div style="display:flex;justify-content:space-between;font-size:0.8rem;padding:5px 0;border-bottom:1px solid #f0e8d8"><span>🔴 యమగండ కాలం</span><span style="font-weight:700">${data.yamaganda.start}–${data.yamaganda.end}</span></div>`:""}
      ${data.gulika_kalam?`<div style="display:flex;justify-content:space-between;font-size:0.8rem;padding:5px 0"><span>⚠️ గులిక కాలం</span><span style="font-weight:700">${data.gulika_kalam.start}–${data.gulika_kalam.end}</span></div>`:""}
    </div>`;
  list.appendChild(card);

  document.getElementById("resultsActions").style.display = "";
}
```

- [ ] **Step 2: Update `showResults()` to show/hide the new hero + banner**

Find `function showResults()` and add these lines at the start (after `const list = ...`):

```js
  // Show results hero and kalam banner for range mode
  const hero = document.getElementById("resultsHero");
  const banner = document.getElementById("kalamBanner");
  if (hero) hero.style.display = "";
  if (banner) banner.style.display = "";
  document.getElementById("resultsActions").style.display = "";
```

- [ ] **Step 3: Update `resetWizard()` to go to panel 1 and clear new state**

Find `function resetWizard()` and update to:

```js
function resetWizard() {
  showError("");
  selectedCeremony = null;
  allResults = [];
  personCount = 0;
  dateMode = "range";
  savedProfileCharts = {};
  document.querySelectorAll(".ceremony-card").forEach(c => c.classList.remove("selected"));
  document.getElementById("ceremonyPlace").value = "";
  document.getElementById("personList").innerHTML = "";
  document.getElementById("addPersonBtn").style.display = "block";
  document.getElementById("resultsList").innerHTML = "";
  showLoading(false);
  // Reset date toggle to range
  if (document.getElementById("tabRange")) setDateMode("range");
  setStep(1);
  addPerson();
}
```

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: showCheckResult verdict card + update showResults/resetWizard for 3-panel flow"
```

---

## Task 9: Final wiring, cleanup, and deploy

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Remove the old `goPanel2()` ceremony-validation logic**

The old `goPanel2()` validated ceremony/location. Now `goPanel2()` (Task 4) validates persons. Make sure there is no duplicate `goPanel2()` function. Keep only the one from Task 4 that validates persons and calls `setStep(2)`.

- [ ] **Step 2: Remove old Panel 4 reference from `resetWizard` (if any remain)**

Search for any remaining `panel4` or `setStep(4)` references and remove/replace with `panel3`/`setStep(3)`.

```bash
grep -n "panel4\|setStep(4)" docs/muhoortam/index.html
```

Expected: no results (or fix any found).

- [ ] **Step 3: Verify Flatpickr init includes `#checkDate`**

The default dates IIFE already has `flatpickr("#checkDate", { ...fpOpts })` from Task 5. Verify:

```bash
grep "checkDate" docs/muhoortam/index.html
```

Expected output includes `flatpickr("#checkDate"`.

- [ ] **Step 4: Add `.superpowers/` to `.gitignore`**

```bash
echo ".superpowers/" >> /Users/schinta/MyDrive/MyCode/telugu-panchang/.gitignore
git add .gitignore
```

- [ ] **Step 5: Final commit and push**

```bash
git add docs/muhoortam/index.html .gitignore
git commit -m "feat: complete 3-step UI redesign with saved profiles and date check

- Step 1: People with localStorage saved profiles (save/load/delete)
- Step 2: Event details with date range / single-date-check toggle
  - Past dates allowed for historical muhurta verification
- Step 3: Combined results panel (find list OR verdict card)
  - Verdict card: good/mixed/bad with factor breakdown
- /muhoortam/check backend deployed via Task 1

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

- [ ] **Step 6: Verify deployment**

Wait ~2 minutes then:
```bash
curl -s "http://muhoortam.sanatanadharmas.com/muhoortam/" | grep -c "profileChips\|dateMode\|checkDate\|showCheckResult"
```

Expected: `4` (all 4 identifiers present on live page)

---

## Self-Review Checklist

- ✅ localStorage profiles: save, load, delete, render, add-from-profile
- ✅ Step bar: 4→3 steps
- ✅ Panel 1: persons + profiles
- ✅ Panel 2: ceremony + location + date toggle (range / single)
- ✅ Past dates: minDate removed from range pickers
- ✅ Single date: checkDate flatpickr + optional checkTime
- ✅ Panel 3: inline loading + results (both modes)
- ✅ `showCheckResult()`: verdict card, good/bad factors, time issues, kalams
- ✅ `startCompute()`: validates, computes charts (with cache), dispatches to `_runFind` or `_runCheck`
- ✅ `resetWizard()`: clears all state including `savedProfileCharts`, `dateMode`
- ✅ Backend check endpoint: deployed in Task 1
- ✅ `.superpowers/` added to `.gitignore`
