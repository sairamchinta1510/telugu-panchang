# Janma Chakram Popup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Janma Chakram popup to the Muhurtam app that opens from a profile card and shows the full South Indian birth chart, key birth details, birth-time panchang, and a PDF export button.

**Architecture:** Extend `compute_birth_chart()` to return all 9 planet rashis and birth-time panchang (additive change). The frontend reuses the existing `renderHoroscopeChart()` function and `savedProfileCharts` cache inside a native `<dialog>` modal triggered from profile chips.

**Tech Stack:** Python (swisseph, pytz), pytest, HTML/CSS/JS (vanilla, no new libraries), browser `window.print()` for PDF export.

---

## File Map

| File | Change |
|------|--------|
| `panchang-api/compute/birth_chart.py` | Extend `compute_birth_chart()` — add `planet_rashis` + `birth_panchang` to return dict |
| `panchang-api/tests/test_muhoortam.py` | Add tests for new `planet_rashis` and `birth_panchang` fields |
| `docs/muhoortam/index.html` | Add modal CSS, modal HTML, `openJanmaChakram()` JS, print CSS, "జన్మ చక్రం" button on profile chips |

---

## Task 1: Extend `compute_birth_chart` with planet rashis and birth panchang

**Files:**
- Modify: `panchang-api/compute/birth_chart.py`

- [ ] **Step 1: Open `panchang-api/compute/birth_chart.py` and add the two new imports at the top**

Replace the existing imports:
```python
from .astro import moon_longitude
from .panchang import NAKSHATRA_TE
```
With:
```python
from .astro import moon_longitude, compute_planet_rashis
from .panchang import NAKSHATRA_TE, compute_panchang
```

- [ ] **Step 2: Extend `compute_birth_chart()` to compute and return the new fields**

Replace the entire `compute_birth_chart` function body (keep the signature unchanged):

```python
def compute_birth_chart(
    year: int, month: int, day: int,
    hour: int, minute: int,
    lat: float, lon: float, tz_name: str,
) -> dict:
    """Compute birth chart indices and Telugu names from birth data.

    Returns dict with janma_nakshatra_idx, janma_nakshatra_te,
    janma_rashi_idx, janma_rashi_te, lagna_idx, lagna_te,
    planet_rashis (all 9 grahas), and birth_panchang
    (tithi_te, vaara_te, nakshatra_te, yoga_te, karanam_te).
    """
    jd = _birth_jd(year, month, day, hour, minute, tz_name)
    moon_lon = moon_longitude(jd)

    nak_idx   = int(moon_lon / (360.0 / 27)) % 27
    rashi_idx = int(moon_lon / 30) % 12
    lagna_idx = compute_lagna(jd, lat, lon)

    # Nakshatra padam: each nakshatra = 13°20', each padam = 3°20'
    nak_start = nak_idx * (360.0 / 27)
    padam = int((moon_lon - nak_start) / (360.0 / 108)) + 1  # 1–4

    planet_rashis = compute_planet_rashis(jd)

    pan = compute_panchang(jd, lat, lon, tz_name)
    birth_panchang = {
        "tithi_te":     pan["tithi"]["te"],
        "vaara_te":     pan["vaaram"]["te"],
        "nakshatra_te": pan["nakshatra"]["te"],
        "yoga_te":      pan["yoga"]["te"],
        "karanam_te":   pan["karana"]["te"],
    }

    return {
        "janma_nakshatra_idx":   nak_idx,
        "janma_nakshatra_te":    NAKSHATRA_TE[nak_idx],
        "janma_nakshatra_padam": padam,
        "janma_rashi_idx":       rashi_idx,
        "janma_rashi_te":        RASHI_TE[rashi_idx],
        "lagna_idx":             lagna_idx,
        "lagna_te":              RASHI_TE[lagna_idx],
        "planet_rashis":         planet_rashis,
        "birth_panchang":        birth_panchang,
    }
```

- [ ] **Step 3: Commit**

```bash
cd panchang-api
git add compute/birth_chart.py
git commit -m "feat: extend compute_birth_chart with planet_rashis and birth_panchang"
```

---

## Task 2: Test the extended birth chart response

**Files:**
- Modify: `panchang-api/tests/test_muhoortam.py`

- [ ] **Step 1: Write failing tests for `planet_rashis` and `birth_panchang`**

Open `panchang-api/tests/test_muhoortam.py`. After the existing `test_birth_chart_lagna` test (around line 75), add the following tests. Note: `_make_birth_chart_module()` mocks `compute.astro` — we need to add `compute_planet_rashis` and `compute_panchang` to those mocks.

First update `_make_birth_chart_module()` — replace the `fake_astro` block inside it (lines that set `fake_astro.moon_longitude`):

```python
    fake_astro = types.ModuleType("compute.astro")
    fake_astro.moon_longitude = lambda jd: 54.67
    # planet_rashis: all planets in rashi 0 (Mesha) for simplicity
    fake_astro.compute_planet_rashis = lambda jd: {
        "ravi": 0, "chandra": 1, "kuja": 2, "budha": 3,
        "guru": 4, "shukra": 5, "shani": 6, "rahu": 7, "ketu": 1,
    }
    sys.modules["compute.astro"] = fake_astro
```

Then add a mock for `compute_panchang` inside `_make_birth_chart_module()`, right before the `import importlib` line:

```python
    # Mock compute_panchang on the panchang module
    sys.modules["compute.panchang"].compute_panchang = lambda jd, lat, lon, tz: {
        "tithi":    {"te": "పంచమి",    "en": "Panchami"},
        "vaaram":   {"te": "మంగళవారం", "en": "Tuesday"},
        "nakshatra":{"te": "మృగశిర",   "en": "Mrigashira"},
        "yoga":     {"te": "సిద్ధి",   "en": "Siddhi"},
        "karana":   {"te": "బవ",       "en": "Bava"},
    }
```

Then add the new test functions after `test_birth_chart_lagna`:

```python
def test_birth_chart_planet_rashis_present():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert "planet_rashis" in result
    expected_keys = {"ravi", "chandra", "kuja", "budha", "guru", "shukra", "shani", "rahu", "ketu"}
    assert set(result["planet_rashis"].keys()) == expected_keys


def test_birth_chart_planet_rashi_values_in_range():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    for planet, rashi_idx in result["planet_rashis"].items():
        assert 0 <= rashi_idx <= 11, f"{planet} rashi {rashi_idx} out of range"


def test_birth_chart_birth_panchang_present():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert "birth_panchang" in result
    bp = result["birth_panchang"]
    for key in ("tithi_te", "vaara_te", "nakshatra_te", "yoga_te", "karanam_te"):
        assert key in bp, f"Missing key: {key}"
        assert isinstance(bp[key], str) and bp[key], f"{key} must be a non-empty string"


def test_birth_chart_birth_panchang_values():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    bp = result["birth_panchang"]
    assert bp["tithi_te"]     == "పంచమి"
    assert bp["vaara_te"]     == "మంగళవారం"
    assert bp["nakshatra_te"] == "మృగశిర"
    assert bp["yoga_te"]      == "సిద్ధి"
    assert bp["karanam_te"]   == "బవ"
```

- [ ] **Step 2: Run the new tests to verify they fail (before implementation is complete)**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py::test_birth_chart_planet_rashis_present \
  tests/test_muhoortam.py::test_birth_chart_birth_panchang_present -v
```

Expected: FAIL with `KeyError: 'planet_rashis'` (or similar) until Task 1 is merged.

> **Note:** If running after Task 1, these tests should already pass. Run them regardless to confirm.

- [ ] **Step 3: Run all birth chart tests to confirm no regressions**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py -k "birth_chart" -v
```

Expected output:
```
test_birth_chart_nakshatra                PASSED
test_birth_chart_rashi                    PASSED
test_birth_chart_lagna                    PASSED
test_birth_chart_planet_rashis_present    PASSED
test_birth_chart_planet_rashi_values_in_range PASSED
test_birth_chart_birth_panchang_present   PASSED
test_birth_chart_birth_panchang_values    PASSED
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_muhoortam.py
git commit -m "test: add tests for planet_rashis and birth_panchang in birth chart response"
```

---

## Task 3: Add Janma Chakram modal — CSS and HTML skeleton

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Add modal CSS**

Find the `@media print {` block (around line 1037). Insert the following CSS block **immediately before** it:

```css
/* ════════════════════════════════
   JANMA CHAKRAM MODAL
════════════════════════════════ */
#janmaChakramModal {
  border: none;
  border-radius: var(--radius);
  padding: 0;
  width: min(480px, 96vw);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  background: var(--surface);
}
#janmaChakramModal::backdrop {
  background: rgba(0,0,0,0.45);
}
.jc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 16px 10px;
  border-bottom: 1px solid var(--border);
}
.jc-header-text h2 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  font-family: 'Noto Sans Telugu', 'Inter', system-ui, sans-serif;
}
.jc-header-text p {
  font-size: 0.75rem;
  color: var(--text-2);
  margin-top: 2px;
  font-family: 'Inter', system-ui, sans-serif;
}
.jc-close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--text-3);
  padding: 0 4px;
  line-height: 1;
  flex-shrink: 0;
}
.jc-close-btn:hover { color: var(--text); }
.jc-body { padding: 14px 16px; }
.jc-chart-wrap { display: flex; justify-content: center; margin-bottom: 14px; }
.jc-details-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}
.jc-detail-box {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  text-align: center;
}
.jc-detail-box .jc-label {
  font-size: 0.65rem;
  color: var(--text-2);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
  font-family: 'Inter', system-ui, sans-serif;
}
.jc-detail-box .jc-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text);
  font-family: 'Noto Sans Telugu', system-ui, sans-serif;
}
.jc-detail-box .jc-sub {
  font-size: 0.65rem;
  color: var(--text-2);
  margin-top: 2px;
  font-family: 'Inter', 'Noto Sans Telugu', system-ui, sans-serif;
}
.jc-panchang-strip {
  background: var(--indigo-xl);
  border: 1px solid var(--indigo-light);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-bottom: 14px;
}
.jc-panchang-strip .jc-p-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--indigo-dark);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  font-family: 'Inter', system-ui, sans-serif;
}
.jc-panchang-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.jc-pan-item {
  background: var(--surface);
  border: 1px solid var(--indigo-light);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.78rem;
  font-family: 'Noto Sans Telugu', 'Inter', system-ui, sans-serif;
  color: var(--text);
}
.jc-pan-item span { color: var(--text-2); font-size: 0.65rem; margin-right: 3px; }
.jc-pdf-btn {
  display: block;
  width: 100%;
  padding: 11px;
  background: var(--indigo);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 700;
  font-family: 'Inter', system-ui, sans-serif;
  cursor: pointer;
  letter-spacing: 0.02em;
}
.jc-pdf-btn:hover { background: var(--indigo-dark); }
.jc-loading { text-align: center; padding: 32px 16px; font-size: 0.85rem; color: var(--text-2); }
.jc-error { text-align: center; padding: 20px 16px; font-size: 0.85rem; color: #DC2626; }
```

- [ ] **Step 2: Add print CSS override inside the existing `@media print` block**

Find the existing `@media print {` block and add one line so the modal is the only visible element when printing:

```css
@media print {
  .site-nav, .hero-section, .step-bar, .actions-row, .btn-details, .btn-primary, .overlay { display: none !important; }
  body { background: white; }
  .result-card { box-shadow: none; border: 1px solid #ccc; break-inside: avoid; }
  /* Janma Chakram PDF export */
  body > *:not(#janmaChakramModal) { display: none !important; }
  #janmaChakramModal { display: block !important; position: static; box-shadow: none; width: 100%; max-height: none; }
  .jc-pdf-btn { display: none !important; }
  .jc-close-btn { display: none !important; }
}
```

- [ ] **Step 3: Add the modal HTML element to the page body**

Find the closing `</body>` tag (last line of the file). Insert the following immediately before it:

```html
<!-- ══ JANMA CHAKRAM MODAL ══ -->
<dialog id="janmaChakramModal" aria-modal="true" aria-labelledby="jcModalTitle">
  <div class="jc-header">
    <div class="jc-header-text">
      <h2 id="jcModalTitle">🪐 జన్మ చక్రం</h2>
      <p id="jcModalSubtitle"></p>
    </div>
    <button class="jc-close-btn" onclick="closeJanmaChakram()" aria-label="Close">✕</button>
  </div>
  <div class="jc-body" id="jcModalBody">
    <div class="jc-loading">⏳ లోడ్ అవుతున్నది...</div>
  </div>
</dialog>
```

- [ ] **Step 4: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add Janma Chakram modal HTML and CSS"
```

---

## Task 4: Add JavaScript for the Janma Chakram modal

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Add the modal JS functions**

Find the line `const API_BASE = "https://h3dp7amvn9.execute-api.ap-south-1.amazonaws.com";` (around line 1493). After that line, add:

```javascript
// ── Janma Chakram modal ────────────────────────────────────────────────────────

function openJanmaChakram(name, dob, time, place, cachedChart) {
  const modal = document.getElementById("janmaChakramModal");
  document.getElementById("jcModalTitle").textContent = "🪐 జన్మ చక్రం — " + name;
  document.getElementById("jcModalSubtitle").textContent =
    [dob, place].filter(Boolean).join(" · ");

  if (cachedChart && cachedChart.planet_rashis) {
    _renderJanmaChakram(cachedChart);
  } else {
    document.getElementById("jcModalBody").innerHTML =
      '<div class="jc-loading">⏳ లోడ్ అవుతున్నది...</div>';
    modal.showModal();
    _fetchAndRenderJanmaChakram(name, dob, time, place);
    return;
  }
  modal.showModal();
}

function closeJanmaChakram() {
  document.getElementById("janmaChakramModal").close();
}

async function _fetchAndRenderJanmaChakram(name, dob, time, place) {
  try {
    const resp = await fetch(API_BASE + "/muhoortam/birth-chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dob, time, place }),
    });
    if (!resp.ok) throw new Error("API error " + resp.status);
    const chart = await resp.json();
    // Cache onto the savedProfileCharts using name as a lookup key
    // so subsequent opens don't re-fetch
    for (const [id, saved] of Object.entries(savedProfileCharts)) {
      // Update any matching cached entry that lacks planet_rashis
      if (!saved.planet_rashis) savedProfileCharts[id] = { ...saved, ...chart };
    }
    _renderJanmaChakram(chart);
  } catch (e) {
    document.getElementById("jcModalBody").innerHTML =
      '<div class="jc-error">⚠️ చార్ట్ లోడ్ కాలేదు. మళ్ళీ ప్రయత్నించండి.</div>';
  }
}

function _renderJanmaChakram(chart) {
  const PADAM_TE = ["", "1వ", "2వ", "3వ", "4వ"];
  const padamLabel = chart.janma_nakshatra_padam
    ? " " + (PADAM_TE[chart.janma_nakshatra_padam] || chart.janma_nakshatra_padam) + " పాదం"
    : "";

  const chartHtml = renderHoroscopeChart(chart.planet_rashis, chart.lagna_idx);

  const bp = chart.birth_panchang || {};
  const pItems = [
    { label: "తిథి",     value: bp.tithi_te    || "—" },
    { label: "వారం",     value: bp.vaara_te    || "—" },
    { label: "నక్షత్రం", value: bp.nakshatra_te|| "—" },
    { label: "యోగం",     value: bp.yoga_te     || "—" },
    { label: "కరణం",     value: bp.karanam_te  || "—" },
  ];

  document.getElementById("jcModalBody").innerHTML = `
    <div class="jc-chart-wrap">${chartHtml}</div>
    <div class="jc-details-row">
      <div class="jc-detail-box">
        <div class="jc-label">నక్షత్రం</div>
        <div class="jc-value">${chart.janma_nakshatra_te || "—"}</div>
        ${padamLabel ? `<div class="jc-sub">${padamLabel}</div>` : ""}
      </div>
      <div class="jc-detail-box">
        <div class="jc-label">రాశి</div>
        <div class="jc-value">${chart.janma_rashi_te || "—"}</div>
      </div>
      <div class="jc-detail-box">
        <div class="jc-label">లగ్నం</div>
        <div class="jc-value">${chart.lagna_te || "—"}</div>
      </div>
    </div>
    <div class="jc-panchang-strip">
      <div class="jc-p-label">⭐ జన్మ పంచాంగం</div>
      <div class="jc-panchang-grid">
        ${pItems.map(i =>
          `<div class="jc-pan-item"><span>${i.label}:</span>${i.value}</div>`
        ).join("")}
      </div>
    </div>
    <button class="jc-pdf-btn" onclick="window.print()">📄 PDF గా Export చేయండి</button>
  `;
}
```

- [ ] **Step 2: Close the modal when clicking the backdrop**

After the functions above (still in the same JS block), add:

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("janmaChakramModal");
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.close();
    });
  }
});
```

- [ ] **Step 3: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add Janma Chakram modal JS — fetch, render, cache, PDF export"
```

---

## Task 5: Wire "జన్మ చక్రం" button onto profile chips

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Add the chart button to each saved profile chip**

Find `renderProfileChips()` (around line 1691). Inside the template literal, the profile chip currently looks like:

```javascript
        <div class="profile-chip">
          <div class="profile-chip-name">${p.name}</div>
          ${p.birthChart ? `<div class="profile-chip-nak">🌟 ${p.birthChart.janma_nakshatra_te}${p.birthChart.janma_nakshatra_padam ? " "+p.birthChart.janma_nakshatra_padam+"వ పాదం" : ""}</div>` : ""}
          <div class="profile-chip-actions">
            <button type="button" class="profile-chip-add" onclick="addFromProfile(${i})">＋ Add</button>
            <button type="button" class="profile-chip-del" onclick="deleteProfile('${p.name.replace(/'/g,"\\'")}')">✕</button>
          </div>
        </div>
```

Replace it with:

```javascript
        <div class="profile-chip">
          <div class="profile-chip-name">${p.name}</div>
          ${p.birthChart ? `<div class="profile-chip-nak">🌟 ${p.birthChart.janma_nakshatra_te}${p.birthChart.janma_nakshatra_padam ? " "+p.birthChart.janma_nakshatra_padam+"వ పాదం" : ""}</div>` : ""}
          <div class="profile-chip-actions">
            <button type="button" class="profile-chip-add" onclick="addFromProfile(${i})">＋ Add</button>
            <button type="button" class="profile-chip-add" style="background:var(--amber)"
              onclick="openJanmaChakram(${JSON.stringify(p.name)},${JSON.stringify(p.dob||'')},${JSON.stringify(p.time||'')},${JSON.stringify(p.place||'')},${p.birthChart ? JSON.stringify(p.birthChart) : 'null'})">🪐</button>
            <button type="button" class="profile-chip-del" onclick="deleteProfile('${p.name.replace(/'/g,"\\'")}')">✕</button>
          </div>
        </div>
```

- [ ] **Step 2: Verify the page opens in a browser and the 🪐 button appears on saved profiles**

Open `docs/muhoortam/index.html` in a browser (or via local server). Save a profile with a name, DOB, time, and place. Confirm:
- The profile chip shows a 🪐 button (amber colour)
- Clicking it opens the modal with a loading spinner
- The modal fetches from the API and renders the chart, key details, panchang strip, and PDF button
- The ✕ button and clicking the dark backdrop both close the modal

- [ ] **Step 3: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add Janma Chakram button to saved profile chips"
```

---

## Task 6: Run full test suite and final verification

- [ ] **Step 1: Run all backend tests**

```bash
cd panchang-api
python -m pytest tests/ -v
```

Expected: all tests pass (no regressions).

- [ ] **Step 2: Test PDF export manually**

Open the page, open a Janma Chakram modal, click "📄 PDF గా Export చేయండి". Verify:
- Browser print dialog opens
- Only the modal content is visible in the preview (nav, hero, cards are hidden)
- "Export PDF" button itself is not printed

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "chore: Janma Chakram popup — complete implementation"
```
