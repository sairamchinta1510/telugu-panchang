# Muhurtam Accuracy — Rules + Panchangam Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the missing Guru Asta rule, add English translations to score components, fix frontend Telugu→English translation gaps, then validate every muhurtam result against Prokerala Panchangam and display a verified badge in the UI.

**Architecture:** Backend additions are in `muhurta_rules.py` (new rule + EN keys), `muhurta_finder.py` (add nak_idx/tithi_idx to day results), new `panchangam_validator.py` (scrape+cache Prokerala), and `handler_muhoortam.py` (call validator after results). Frontend additions are isolated to `docs/muhoortam/index.html` (lookup tables, badge rendering).

**Tech Stack:** Python 3.11, pyswisseph, boto3 (S3 cache), urllib (scraping, stdlib only), pytest; JavaScript ES2020, no new dependencies.

---

## File Map

| File | Change |
|---|---|
| `docs/muhoortam/index.html` | Fix `_LAGNA_TE_LIST`; add `tChoghadiya()`; add validation badge HTML |
| `panchang-api/compute/muhurta_rules.py` | Add `_GRAHA_SHORT_EN`, `_HOUSE_ORD_EN`; extend `_add()` with `en` param; add `guru_combust` rule to `_LAGNA_RULES` and `check_lagna_graha_quality()` |
| `panchang-api/compute/muhurta_finder.py` | Add `nak_idx` and `tithi_idx` to day result dict |
| `panchang-api/compute/panchangam_validator.py` | **Create** — Prokerala scraper + S3 cache + comparison logic |
| `panchang-api/handler_muhoortam.py` | Import validator; call after `find_muhurtas_for_month`; attach `validation` key |
| `panchang-api/tests/test_muhoortam.py` | Add 3 unit tests: guru_combust block, guru_combust only warns for pooja, all score_components have `en` key |
| `panchang-api/tests/test_panchangam_validator.py` | **Create** — integration test with mock HTTP + mock S3 |

---

## Task 1: Fix Frontend Lagna Lookup and Add Choghadiya Translation

**Files:**
- Modify: `docs/muhoortam/index.html` (lines ~1162–1186 and ~1956–2328)

### Background

`_LAGNA_TE_LIST[6]` is `'తుల'` but the backend returns `'తులం'` (from `RASHI_TE[6]`).
`_LAGNA_TE_LIST[8]` is `'ధనుసు'` but the backend returns `'ధనుస్సు'` (from `RASHI_TE[8]`).
This means `tLagna()` never finds a match and falls back to Telugu even in EN mode.

Also, choghadiya is rendered raw as `w.choghadiya_te` (same string whether EN or TE).
The `_CHO_TE` list in `muhurta_rules.py` is: `["అమృత", "చర", "లాభ", "శుభ", "ఉద్వేగ", "కాల", "రోగ"]`
(indices 0–6, same order used by the backend).

- [ ] **Step 1: Fix `_LAGNA_TE_LIST`**

In `docs/muhoortam/index.html`, find and replace:

```js
// FIND (around line 1162):
const _LAGNA_TE_LIST = [
  'మేషం','వృషభం','మిథునం','కర్కాటకం','సింహం','కన్య',
  'తుల','వృశ్చికం','ధనుసు','మకరం','కుంభం','మీనం'
];
```

Replace with:
```js
const _LAGNA_TE_LIST = [
  'మేషం','వృషభం','మిథునం','కర్కాటకం','సింహం','కన్య',
  'తులం','వృశ్చికం','ధనుస్సు','మకరం','కుంభం','మీనం'
];
```

- [ ] **Step 2: Add `tChoghadiya()` function**

Immediately after the `tMasam` function definition (around line 1186), add:

```js
const _CHO_TE_LIST = ['అమృత','చర','లాభ','శుభ','ఉద్వేగ','కాల','రోగ'];
const _CHO_EN      = ['Amrita','Chara','Labha','Shubha','Udvega','Kala','Roga'];
function tChoghadiya(te) {
  if (!te) return te;
  return t(te, teToEn(te, _CHO_TE_LIST, _CHO_EN));
}
```

- [ ] **Step 3: Replace raw choghadiya_te usages with tChoghadiya()**

There are 6 occurrences. Apply all 6 replacements:

**Line ~1956** — replace:
```js
`${best.choghadiya_te ? ` · ${t(best.choghadiya_te, best.choghadiya_te)} ${t('చోఘడియ','Choghadiya')}` : ''}`
```
with:
```js
`${best.choghadiya_te ? ` · ${tChoghadiya(best.choghadiya_te)} ${t('చోఘడియ','Choghadiya')}` : ''}`
```

**Line ~1973** — replace:
```js
${w.choghadiya_te ? ` · ${t(w.choghadiya_te, w.choghadiya_te)}` : ''}
```
with:
```js
${w.choghadiya_te ? ` · ${tChoghadiya(w.choghadiya_te)}` : ''}
```

**Line ~2233** — replace:
```js
${bestWindow.choghadiya_te ? bestWindow.choghadiya_te + ' చోఘడియ' : ''}
```
with:
```js
${bestWindow.choghadiya_te ? tChoghadiya(bestWindow.choghadiya_te) + ' ' + t('చోఘడియ','Choghadiya') : ''}
```

**Line ~2296** — replace:
```js
${w.choghadiya_te?`<span style="font-size:0.72rem;background:#C8E6C9;color:#1B5E20;border-radius:10px;padding:1px 7px;font-weight:600">${w.choghadiya_te}</span>`:''}
```
with:
```js
${w.choghadiya_te?`<span style="font-size:0.72rem;background:#C8E6C9;color:#1B5E20;border-radius:10px;padding:1px 7px;font-weight:600">${tChoghadiya(w.choghadiya_te)}</span>`:''}
```

**Line ~2323** — replace:
```js
${w.choghadiya_te?`<span style="font-size:0.72rem;background:#D1C4E9;color:#4A148C;border-radius:10px;padding:1px 7px;font-weight:600">${w.choghadiya_te}</span>`:''}
```
with:
```js
${w.choghadiya_te?`<span style="font-size:0.72rem;background:#D1C4E9;color:#4A148C;border-radius:10px;padding:1px 7px;font-weight:600">${tChoghadiya(w.choghadiya_te)}</span>`:''}
```

- [ ] **Step 4: Verify fix in browser (local)**

Open `http://localhost:8080/muhoortam/`, switch to EN, run a search. Verify:
- Lagna shows "Tula Lagna" not "తులం లగ్నం" when in EN mode
- Choghadiya shows "Amrita" not "అమృత" when in EN mode

- [ ] **Step 5: Commit**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang
git add docs/muhoortam/index.html
git commit -m "fix: lagna lookup and choghadiya translation in EN mode

- Fix _LAGNA_TE_LIST entries for Tula ('తులం') and Dhanus ('ధనుస్సు')
  to match backend RASHI_TE exactly
- Add tChoghadiya() with _CHO_TE_LIST/_CHO_EN lookup table
- Replace all raw choghadiya_te usages with tChoghadiya()

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 2: Add English Keys to `score_components` in muhurta_rules.py

**Files:**
- Modify: `panchang-api/compute/muhurta_rules.py` (lines ~588–900)

### Background

The `_add()` inner function in `check_lagna_graha_quality()` currently produces:
`{"te": "...", "delta": N}` — no `"en"` key.
The frontend already renders `c.en || c.te` when `c.en` exists, so just adding `en` is enough.

- [ ] **Step 1: Add `_GRAHA_SHORT_EN` and `_HOUSE_ORD_EN` dicts**

In `muhurta_rules.py`, directly after the `_GRAHA_SHORT_TE` dict (around line 600), add:

```python
_GRAHA_SHORT_EN: dict[str, str] = {
    "ravi":    "Sun",
    "chandra": "Moon",
    "kuja":    "Mars",
    "budha":   "Mercury",
    "guru":    "Jupiter",
    "shukra":  "Venus",
    "shani":   "Saturn",
    "rahu":    "Rahu",
    "ketu":    "Ketu",
}
```

Directly after `_HOUSE_ORD_TE` dict (around line 617), add:

```python
_HOUSE_ORD_EN: dict[int, str] = {
    1: "1st", 2: "2nd",  3: "3rd",  4: "4th",
    5: "5th", 6: "6th",  7: "7th",  8: "8th",
    9: "9th", 10: "10th", 11: "11th", 12: "12th",
}
```

- [ ] **Step 2: Extend `_add()` and the base score component**

Inside `check_lagna_graha_quality()`, replace:

```python
    score_components: list[dict] = [{"te": "ప్రాథమిక బేస్ స్కోర్", "delta": 50}]
    score = 50  # neutral baseline

    def _add(delta: int, te: str) -> None:
        score_components.append({"te": te, "delta": delta})
```

with:

```python
    score_components: list[dict] = [{"te": "ప్రాథమిక బేస్ స్కోర్", "delta": 50, "en": "Base score"}]
    score = 50  # neutral baseline

    def _add(delta: int, te: str, en: str = "") -> None:
        score_components.append({"te": te, "delta": delta, "en": en})
```

- [ ] **Step 3: Update rule 1 — malefics in lagna**

Replace the entire rule 1 block (starting `# 1. Malefics in lagna`):

```python
    # 1. Malefics in lagna ────────────────────────────────────────────────────
    if _rule("malefic_in_lagna") != "none":
        malefics_here = sorted(p for p in _PAPA_GRAHAS if planet_rashis.get(p, -1) == lagna_idx)
        if malefics_here:
            names_te = ", ".join(_GRAHA_SHORT_TE.get(p, p) for p in malefics_here)
            names_en = ", ".join(_GRAHA_SHORT_EN.get(p, p) for p in malefics_here)
            msg_te = f"లగ్నంలో పాప గ్రహం ({names_te}) — లగ్న బలం తగ్గింది"
            msg_en = f"Malefic in Lagna ({names_en}) — Lagna strength reduced"
            if _rule("malefic_in_lagna") == "hard":
                hard_blocks.append(msg_te)
                score -= 30
                _add(-30, msg_te, msg_en)
            else:
                warnings.append(msg_te)
                score -= 15
                _add(-15, msg_te, msg_en)
        else:
            score += 5  # clean lagna bonus
            _add(+5, "లగ్నంలో పాప గ్రహం లేదు — లగ్న శుద్ధి ✓",
                 "No malefics in Lagna — Lagna is pure ✓")
```

- [ ] **Step 4: Update rule 2 — malefics in 7th**

Replace the entire rule 2 block (starting `# 2. Malefics in 7th from lagna`):

```python
    # 2. Malefics in 7th from lagna (critical for Vivaha) ────────────────────
    if _rule("malefic_in_7th") != "none":
        seventh = (lagna_idx + 6) % 12
        malefics_7th = sorted(p for p in _PAPA_GRAHAS if planet_rashis.get(p, -1) == seventh)
        if malefics_7th:
            names_te = ", ".join(_GRAHA_SHORT_TE.get(p, p) for p in malefics_7th)
            names_en = ", ".join(_GRAHA_SHORT_EN.get(p, p) for p in malefics_7th)
            msg_te = f"సప్తమ స్థానంలో పాప గ్రహం ({names_te}) — వివాహ స్థానంలో అశుభం"
            msg_en = f"Malefic in 7th house ({names_en}) — Inauspicious for wedding"
            if _rule("malefic_in_7th") == "hard":
                hard_blocks.append(msg_te)
                score -= 25
                _add(-25, msg_te, msg_en)
            else:
                warnings.append(msg_te)
                score -= 12
                _add(-12, msg_te, msg_en)
        else:
            score += 10  # clean 7th is especially auspicious for Vivaha
            _add(+10, "సప్తమ స్థానంలో పాప గ్రహం లేదు — వివాహ స్థానం శుద్ధి ✓",
                 "No malefics in 7th house — Wedding house is pure ✓")
```

- [ ] **Step 5: Update rule 3 — Shukra combustion**

Replace the Shukra combustion block (starting `# 3. Shukra (Venus) combustion`):

```python
    # 3. Shukra (Venus) combustion — requires exact longitudes ────────────────
    if _rule("shukra_combust") != "none" and planet_longitudes:
        sun_lon = planet_longitudes.get("ravi")
        shukra_lon = planet_longitudes.get("shukra")
        if sun_lon is not None and shukra_lon is not None:
            if _is_combust("shukra", shukra_lon, sun_lon):
                msg_te = "శుక్రుడు అస్తంగతం (సూర్యుడికి సమీపంగా) — వివాహ కారకుడు నిర్బలం"
                msg_en = "Venus combust (near Sun) — Wedding significator is weakened"
                if _rule("shukra_combust") == "hard":
                    hard_blocks.append(msg_te)
                    score -= 20
                    _add(-20, msg_te, msg_en)
                else:
                    warnings.append(msg_te)
                    score -= 10
                    _add(-10, msg_te, msg_en)
            else:
                score += 5  # Venus visible and strong
                _add(+5, "శుక్రుడు అస్తంగతం కాదు — వివాహ కారకుడు బలవంతుడు ✓",
                     "Venus not combust — Wedding significator is strong ✓")
```

- [ ] **Step 6: Update rule 4 — Guru aspects lagna**

Replace the Guru aspects block (starting `# 4. Guru (Jupiter) aspects lagna`):

```python
    # 4. Guru (Jupiter) aspects lagna ─────────────────────────────────────────
    if _rule("guru_aspect_lagna") != "none":
        guru_rashi = planet_rashis.get("guru", -1)
        if guru_rashi >= 0 and _guru_aspects_lagna(guru_rashi, lagna_idx):
            msg_te = "గురువు లగ్నాన్ని వీక్షిస్తున్నాడు — శుభ దృష్టి ✓"
            benefits.append(msg_te)
            score += 25
            _add(+25, msg_te, "Jupiter aspects Lagna — Auspicious aspect ✓")
```

- [ ] **Step 7: Update rules 5, 6, 7, 8 — Moon, Shukra position, Guru position, Lagna type**

Replace the Moon in 6/8 block (starting `# 5. Moon in 6th or 8th from lagna`):

```python
    # 5. Moon in 6th or 8th from lagna ────────────────────────────────────────
    if _rule("moon_in_6_8") != "none":
        chandra_rashi = planet_rashis.get("chandra", -1)
        if chandra_rashi >= 0:
            moon_house = _house(chandra_rashi)
            if moon_house in (6, 8):
                ord_te = _HOUSE_ORD_TE.get(moon_house, f"{moon_house}వ")
                ord_en = _HOUSE_ORD_EN.get(moon_house, f"{moon_house}th")
                msg_te = f"చంద్రుడు లగ్నానికి {ord_te} స్థానంలో — అశుభ స్థానం ⚠"
                msg_en = f"Moon in {ord_en} house from Lagna — Inauspicious placement ⚠"
                warnings.append(msg_te)
                score -= 8
                _add(-8, msg_te, msg_en)
```

Replace the Shukra in dusthana block (starting `# 6. Shukra in dusthana`):

```python
    # 6. Shukra in dusthana (6/8/12) or auspicious (2/5/11) from lagna ────────
    if _rule("shukra_in_dusthana") != "none":
        shukra_rashi = planet_rashis.get("shukra", -1)
        if shukra_rashi >= 0:
            shukra_house = _house(shukra_rashi)
            if shukra_house in (6, 8, 12):
                ord_te = _HOUSE_ORD_TE.get(shukra_house, f"{shukra_house}వ")
                ord_en = _HOUSE_ORD_EN.get(shukra_house, f"{shukra_house}th")
                msg_te = f"శుక్రుడు లగ్నానికి {ord_te} స్థానంలో (దుస్థానం) — వివాహ కారకుడికి అశుభ ⚠"
                msg_en = f"Venus in {ord_en} house (dusthana) — Inauspicious for Venus ⚠"
                warnings.append(msg_te)
                score -= 10
                _add(-10, msg_te, msg_en)
            elif shukra_house in (2, 5, 11):
                ord_te = _HOUSE_ORD_TE.get(shukra_house, f"{shukra_house}వ")
                ord_en = _HOUSE_ORD_EN.get(shukra_house, f"{shukra_house}th")
                msg_te = f"శుక్రుడు లగ్నానికి {ord_te} స్థానంలో — వివాహ కారకుడికి శుభ స్థానం ✓"
                msg_en = f"Venus in {ord_en} house — Auspicious placement for Venus ✓"
                benefits.append(msg_te)
                score += 8
                _add(+8, msg_te, msg_en)
```

Replace the Guru in kendra/trikona block (starting `# 7. Guru in kendra`):

```python
    # 7. Guru in kendra (1/4/7/10) or trikona (5/9) from lagna ───────────────
    if _rule("guru_in_kendra_trikona") != "none":
        guru_rashi = planet_rashis.get("guru", -1)
        if guru_rashi >= 0:
            guru_house = _house(guru_rashi)
            if guru_house in (1, 4, 7, 10):
                ord_te = _HOUSE_ORD_TE.get(guru_house, f"{guru_house}వ")
                ord_en = _HOUSE_ORD_EN.get(guru_house, f"{guru_house}th")
                msg_te = f"గురువు {ord_te} స్థానంలో (కేంద్రం) — శుభం ✓"
                msg_en = f"Jupiter in {ord_en} house (kendra) — Auspicious ✓"
                benefits.append(msg_te)
                score += 10
                _add(+10, msg_te, msg_en)
            elif guru_house in (5, 9):
                ord_te = _HOUSE_ORD_TE.get(guru_house, f"{guru_house}వ")
                ord_en = _HOUSE_ORD_EN.get(guru_house, f"{guru_house}th")
                msg_te = f"గురువు {ord_te} స్థానంలో (త్రికోణం) — శుభం ✓"
                msg_en = f"Jupiter in {ord_en} house (trikona) — Auspicious ✓"
                benefits.append(msg_te)
                score += 8
                _add(+8, msg_te, msg_en)
```

Replace the Sthira lagna block (starting `# 8. Sthira (fixed) lagna`):

```python
    # 8. Sthira (fixed) lagna — preferred for permanent ceremonies ────────────
    if _rule("sthira_lagna") != "none":
        if lagna_idx in _STHIRA_LAGNAS:
            msg_te = "స్థిర లగ్నం — శాశ్వత శుభ కార్యాలకు ఉత్తమం ✓"
            benefits.append(msg_te)
            score += 25
            _add(+25, msg_te, "Fixed sign Lagna (Sthira) — Excellent for permanent ceremonies ✓")
        elif lagna_idx in _CHARA_LAGNAS:
            msg_te = "చర లగ్నం — స్థిర లగ్నం ఉత్తమం; ఈ లగ్నం శాశ్వత కార్యాలకు తక్కువ అనువైనది ⚠"
            warnings.append(msg_te)
            score -= 10
            _add(-10, msg_te, "Moveable sign Lagna (Chara) — Fixed sign preferred for permanent ceremonies ⚠")
```

- [ ] **Step 8: Run existing tests to confirm no regression**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py -q
```

Expected: same number of tests as before (currently 78), all pass. Any failure here means a typo or variable name error in the above edits — compare the original code with the replacement.

- [ ] **Step 9: Commit**

```bash
git add panchang-api/compute/muhurta_rules.py
git commit -m "feat: add English keys to all score_components

- Add _GRAHA_SHORT_EN and _HOUSE_ORD_EN dicts
- Extend _add() with optional en= param (default empty string)
- Base score component gets en='Base score'
- All 17 _add() call sites now include English translation strings
- Dynamic planet/house names use _GRAHA_SHORT_EN / _HOUSE_ORD_EN

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 3: Add Guru Asta (Jupiter Combust) Rule

**Files:**
- Modify: `panchang-api/compute/muhurta_rules.py`

### Background

`_COMBUSTION_ORB["guru"] = 11.0` is already defined. `_is_combust()` already handles any planet key.
We just need to: (1) add `"guru_combust"` to `_LAGNA_RULES` entries, (2) add the check in `check_lagna_graha_quality()`.

The rule is a hard block for vivaha, gruha_pravesam, upanayanam (most sacred ceremonies).
For all others it is a soft warning.

- [ ] **Step 1: Add `guru_combust` to `_LAGNA_RULES`**

In `_LAGNA_RULES`, add `"guru_combust"` to each ceremony dict. Replace the entire `_LAGNA_RULES` dict:

```python
_LAGNA_RULES: dict[str, dict[str, str]] = {
    CEREMONY_VIVAHA: {
        "malefic_in_lagna":       "hard",
        "malefic_in_7th":         "hard",
        "shukra_combust":         "hard",
        "guru_combust":           "hard",
        "guru_aspect_lagna":      "benefit",
        "moon_in_6_8":            "warn",
        "shukra_in_dusthana":     "warn",
        "guru_in_kendra_trikona": "benefit",
        "sthira_lagna":           "benefit",
    },
    CEREMONY_GRUHA_PRAVESAM: {
        "malefic_in_lagna":       "hard",
        "guru_combust":           "hard",
        "guru_aspect_lagna":      "benefit",
        "moon_in_6_8":            "warn",
        "guru_in_kendra_trikona": "benefit",
        "sthira_lagna":           "benefit",
    },
    CEREMONY_UPANAYANAM: {
        "malefic_in_lagna":       "hard",
        "guru_combust":           "hard",
        "guru_aspect_lagna":      "benefit",
        "guru_in_kendra_trikona": "benefit",
        "sthira_lagna":           "benefit",
    },
    CEREMONY_GARBHADANAM: {
        "malefic_in_lagna":       "hard",
        "shukra_combust":         "hard",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
        "guru_in_kendra_trikona": "benefit",
        "sthira_lagna":           "benefit",
    },
    CEREMONY_SANKHU_STAPANA: {
        "malefic_in_lagna":       "hard",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
        "guru_in_kendra_trikona": "benefit",
        "sthira_lagna":           "benefit",
    },
    CEREMONY_ANNA_PRASANA: {
        "malefic_in_lagna":       "warn",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
    },
    CEREMONY_NAMAKARANAM: {
        "malefic_in_lagna":       "warn",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
    },
    CEREMONY_CHELAMU: {
        "malefic_in_lagna":       "warn",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
    },
    CEREMONY_VIDYARAMBHAM: {
        "malefic_in_lagna":       "warn",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
    },
    CEREMONY_KOTTA_BATTALU: {
        "malefic_in_lagna":       "warn",
        "guru_combust":           "warn",
        "guru_aspect_lagna":      "benefit",
    },
}
```

- [ ] **Step 2: Add the Guru Asta check in `check_lagna_graha_quality()`**

After the Shukra combustion block (rule 3, ending with `_add(+5, ...)`) and before the Guru aspects lagna block (rule 4), insert:

```python
    # 3.5. Guru (Jupiter) combustion — Guru Asta ──────────────────────────────
    # When Jupiter is within 11° of the Sun, it is considered "asta" (combust).
    # Per Telugu Sampradaya, this eliminates Jupiter's protective power for
    # major life ceremonies. Source: Muhurta Chintamani §Guru-bala.
    if _rule("guru_combust") != "none" and planet_longitudes:
        sun_lon = planet_longitudes.get("ravi")
        guru_lon = planet_longitudes.get("guru")
        if sun_lon is not None and guru_lon is not None:
            if _is_combust("guru", guru_lon, sun_lon):
                msg_te = "గురువు అస్తంగతం (సూర్యుడికి సమీపంగా) — గురు శక్తి నిర్బలం"
                msg_en = "Jupiter combust (Guru Asta) — Jupiter's benefic power is eliminated"
                if _rule("guru_combust") == "hard":
                    hard_blocks.append(msg_te)
                    score -= 25
                    _add(-25, msg_te, msg_en)
                else:
                    warnings.append(msg_te)
                    score -= 10
                    _add(-10, msg_te, msg_en)
            else:
                score += 5
                _add(+5,
                     "గురువు అస్తంగతం కాదు — గురు శక్తి పూర్తిగా ఉంది ✓",
                     "Jupiter not combust — Jupiter's full benefic power active ✓")
```

- [ ] **Step 3: Run tests to confirm no regression**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py -q
```

Expected: all existing tests pass (78+). The guru_combust rule does not affect existing tests because those tests don't pass `planet_longitudes` with Jupiter near the Sun.

- [ ] **Step 4: Commit**

```bash
git add panchang-api/compute/muhurta_rules.py
git commit -m "feat: add Guru Asta (Jupiter combust) rule

- Add 'guru_combust' to _LAGNA_RULES for all ceremony types
  - Hard block for vivaha, gruha_pravesam, upanayanam
  - Soft warning for all other ceremonies
- Add rule 3.5 check in check_lagna_graha_quality() using _is_combust()
- Combustion orb is 11° (already defined in _COMBUSTION_ORB)
- Source: Muhurta Chintamani §Guru-bala / Telugu Sampradaya

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 4: Unit Tests for Guru Asta and English Score Keys

**Files:**
- Modify: `panchang-api/tests/test_muhoortam.py`

- [ ] **Step 1: Add three new test functions**

Append these tests at the end of `tests/test_muhoortam.py`:

```python
# ── Guru Asta (Jupiter combust) tests ────────────────────────────────────────

def test_lagna_quality_guru_combust_blocks_vivaha():
    """Jupiter within 11° of Sun should hard-block vivaha."""
    from compute.muhurta_rules import check_lagna_graha_quality
    result = check_lagna_graha_quality(
        lagna_idx=1,
        planet_rashis={"guru": 1, "shukra": 3},
        ceremony_type="vivaha",
        planet_longitudes={
            "ravi":   30.0,
            "guru":   38.0,   # 8° from Sun — within 11° orb → combust
            "shukra": 90.0,   # not combust
        },
    )
    assert result["blocked"] is True, "Vivaha should be blocked when Jupiter is combust"
    en_labels = [c.get("en", "") for c in result["score_components"]]
    assert any("Jupiter combust" in label for label in en_labels), (
        "Expected 'Jupiter combust' in English score component labels"
    )


def test_lagna_quality_guru_combust_only_warns_for_pooja():
    """Jupiter combust should NOT block pooja — only a soft warning."""
    from compute.muhurta_rules import check_lagna_graha_quality
    result = check_lagna_graha_quality(
        lagna_idx=1,
        planet_rashis={"guru": 1, "shukra": 3},
        ceremony_type="pooja",
        planet_longitudes={
            "ravi":   30.0,
            "guru":   38.0,   # combust
            "shukra": 90.0,
        },
    )
    assert result["blocked"] is False, "Pooja should not be blocked by Jupiter combust"


def test_all_score_components_have_en_key():
    """Every component in score_components must have an 'en' key (may be empty string)."""
    from compute.muhurta_rules import check_lagna_graha_quality
    result = check_lagna_graha_quality(
        lagna_idx=0,           # Mesha lagna
        planet_rashis={
            "guru":    4,      # Simha (not in kendra/trikona from 0, house=5 → trikona)
            "shukra":  2,      # Mithuna, house=3 — neutral
            "chandra": 5,      # Kanya, house=6 → moon_in_6_8 warning
            "kuja":    0,      # Mesha = lagna → malefic in lagna
            "shani":   6,      # Tula, house=7 → malefic in 7th
        },
        ceremony_type="vivaha",
        planet_longitudes={
            "ravi":   0.0,
            "guru":  120.0,    # 120° from Sun — not combust
            "shukra": 60.0,    # 60° from Sun — not combust
        },
    )
    for comp in result["score_components"]:
        assert "en" in comp, f"score_component missing 'en' key: {comp}"
```

- [ ] **Step 2: Run the new tests**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py -q -k "guru_combust or score_components"
```

Expected output:
```
test_lagna_quality_guru_combust_blocks_vivaha PASSED
test_lagna_quality_guru_combust_only_warns_for_pooja PASSED
test_all_score_components_have_en_key PASSED
3 passed
```

- [ ] **Step 3: Run full test suite to confirm no regressions**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py -q
```

Expected: 81 passed (78 original + 3 new).

- [ ] **Step 4: Commit**

```bash
git add panchang-api/tests/test_muhoortam.py
git commit -m "test: add unit tests for guru_combust rule and EN score keys

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 5: Add nak_idx and tithi_idx to Day Results in muhurta_finder.py

**Files:**
- Modify: `panchang-api/compute/muhurta_finder.py` (around line 550)

### Background

The validator needs to know which tithi and nakshatra our engine computed, expressed as numeric indices so it can map to English names for comparison with Prokerala. Currently the day result dict has `tithi_te` and `nakshatra_te` (Telugu strings) but not the indices.

- [ ] **Step 1: Add `nak_idx` and `tithi_idx` to the day result dict**

In `muhurta_finder.py`, find the `results.append({` block (around line 550) and add two fields:

```python
            results.append({
                "date_te":      f"{day} {_MONTH_TE[month - 1]} {year}",
                "date_raw":     f"{day:02d}/{month:02d}/{year}",
                "vaaram_te":    vaaram_te,
                "sunrise":      sunrise,
                "sunset":       sunset,
                "tithi_te":     tithi_te,
                "nakshatra_te": nakshatra_te,
                "yoga_te":      yoga_te,
                "tithi_idx":    tithi_idx,    # ← ADD THIS LINE
                "nak_idx":      naks_idx,     # ← ADD THIS LINE
                "rahu_kalam":   kalams["rahu_kalam"],
                # ... rest of fields unchanged
```

> Note: The existing local variables `tithi_idx` and `naks_idx` are already in scope at this point — they are computed a few lines earlier from either the cache or `compute_panchang()`.

- [ ] **Step 2: Run tests to confirm no regression**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py -q
```

Expected: 81 passed (no change from previous step).

- [ ] **Step 3: Commit**

```bash
git add panchang-api/compute/muhurta_finder.py
git commit -m "feat: expose nak_idx and tithi_idx in day result dicts

Needed by panchangam_validator to map to English names for Prokerala comparison.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 6: Create panchangam_validator.py

**Files:**
- Create: `panchang-api/compute/panchangam_validator.py`

### Background

This module fetches Prokerala Panchangam HTML for a given date + lat/lon, parses the panchang elements (tithi, nakshatra, sunrise), and compares them against our computed values. Results are cached in S3 (same bucket as month cache, different key prefix).

**Important:** Web scraping is inherently fragile. If the fetch or parse fails for ANY reason, the function returns `status="unavailable"` and never raises. This ensures the main API never fails because of validation issues.

**Prokerala URL:** `https://www.prokerala.com/astrology/panchangam/date/{YYYY}/{MM}/{DD}/?la={lat}&lo={lon}&tz={tz_offset}&ayanamsa=1`
Example: `https://www.prokerala.com/astrology/panchangam/date/2026/06/25/?la=17.3850&lo=78.4867&tz=5.5&ayanamsa=1`

Prokerala HTML uses `<td>` table rows where each row has a label and value. The parser scans for all `<td>` text content and builds a label→value map using a sliding window (label, value, label, value...).

- [ ] **Step 1: Verify the Prokerala URL and HTML structure**

Before writing the parser, manually fetch the page to see the HTML:

```bash
curl -s "https://www.prokerala.com/astrology/panchangam/date/2026/06/25/?la=17.3850&lo=78.4867&tz=5.5&ayanamsa=1" \
  -A "Mozilla/5.0" | python3 -c "
import sys
from html.parser import HTMLParser

class TdCollect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False; self.cells = []
    def handle_starttag(self, t, a):
        if t=='td': self.in_td=True
    def handle_endtag(self, t):
        if t=='td': self.in_td=False
    def handle_data(self, d):
        if self.in_td and d.strip():
            self.cells.append(d.strip())
p = TdCollect(); p.feed(sys.stdin.read())
for i in range(0, min(len(p.cells), 40), 2):
    print(f'{p.cells[i]:30s} = {p.cells[i+1] if i+1<len(p.cells) else \"?\"}')"
```

Look at the output and identify the exact label strings for:
- Tithi (e.g. "Tithi" or "Thithi")
- Nakshatra (e.g. "Nakshatra" or "Star")
- Sunrise (e.g. "Sunrise" or "Sun Rise")

Record these label strings — you will use them in the `_FIELD_ALIASES` dict below. If the output is empty, try fetching without `ayanamsa=1` or try the Telugu version at: `https://www.prokerala.com/astrology/telugu-panchangam/date/2026/06/25/?la=17.3850&lo=78.4867&tz=5.5`

- [ ] **Step 2: Create the validator module**

Create `panchang-api/compute/panchangam_validator.py`:

```python
"""Cross-validates a muhurtam date's panchang elements against Prokerala Panchangam.

Never raises — returns status="unavailable" on any error.
"""
from __future__ import annotations

import datetime
import json
import os
import urllib.request
from html.parser import HTMLParser


# Prokerala label aliases — the labels Prokerala uses in its HTML table.
# Key = canonical name, Value = list of labels to look for (case-insensitive).
_FIELD_ALIASES: dict[str, list[str]] = {
    "tithi":     ["tithi", "thithi"],
    "nakshatra": ["nakshatra", "star", "nakshatram"],
    "sunrise":   ["sunrise", "sun rise", "sun-rise"],
}

_PROKERALA_BASE = "https://www.prokerala.com/astrology/panchangam/date"
_SUNRISE_TOL_MIN = 2   # sunrise match tolerance in minutes


class _TdPairParser(HTMLParser):
    """Collect <td> text content as alternating label/value pairs."""

    def __init__(self) -> None:
        super().__init__()
        self._in_td = False
        self._cells: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "td":
            self._in_td = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            self._in_td = False

    def handle_data(self, data: str) -> None:
        if self._in_td:
            cleaned = data.strip()
            if cleaned:
                self._cells.append(cleaned)

    def label_value_map(self) -> dict[str, str]:
        """Return {label.lower(): value} from alternating td pairs."""
        result: dict[str, str] = {}
        cells = self._cells
        for i in range(0, len(cells) - 1, 2):
            result[cells[i].lower()] = cells[i + 1]
        return result


def _tz_offset(tz_name: str) -> float:
    """Return UTC offset in decimal hours for a timezone name string."""
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
        offset = datetime.datetime.now(tz).utcoffset()
        return offset.total_seconds() / 3600 if offset else 5.5
    except Exception:
        return 5.5  # default to IST


def _cache_key(date: datetime.date, lat: float, lon: float) -> str:
    return f"panchang-ref/{date.year}/{date.month:02d}/{date.day:02d}/{lat:.2f}_{lon:.2f}.json"


def _read_s3(key: str) -> dict | None:
    bucket = os.environ.get("PANCHANG_CACHE_BUCKET")
    if not bucket:
        return None
    try:
        import boto3
        resp = boto3.client("s3").get_object(Bucket=bucket, Key=key)
        return json.loads(resp["Body"].read())
    except Exception:
        return None


def _write_s3(key: str, data: dict) -> None:
    bucket = os.environ.get("PANCHANG_CACHE_BUCKET")
    if not bucket:
        return
    try:
        import boto3
        boto3.client("s3").put_object(
            Bucket=bucket, Key=key,
            Body=json.dumps(data).encode(),
            ContentType="application/json",
        )
    except Exception:
        pass


def _fetch_prokerala(date: datetime.date, lat: float, lon: float, tz_name: str) -> dict[str, str]:
    """Fetch Prokerala panchangam page and return label→value map."""
    tz_off = _tz_offset(tz_name)
    url = (
        f"{_PROKERALA_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"
        f"?la={lat:.4f}&lo={lon:.4f}&tz={tz_off:.1f}&ayanamsa=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = _TdPairParser()
    parser.feed(html)
    return parser.label_value_map()


def _lookup(raw: dict[str, str], canonical: str) -> str:
    """Look up a canonical field using any of its aliases."""
    for alias in _FIELD_ALIASES.get(canonical, [canonical]):
        val = raw.get(alias)
        if val:
            return val
    return ""


def _parse_time_to_hours(s: str) -> float | None:
    """Parse time string like '05:43 AM' or '05:43' → decimal hours."""
    import time as _time
    s = s.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            t = _time.strptime(s, fmt)
            return t.tm_hour + t.tm_min / 60.0
        except ValueError:
            continue
    return None


def validate_muhurtam_date(
    date: datetime.date,
    lat: float,
    lon: float,
    tz_name: str,
    tithi_en: str,
    nakshatra_en: str,
    sunrise: str,
) -> dict:
    """Cross-check our panchang elements against Prokerala for the given date/location.

    Args:
        date: calendar date of the muhurtam
        lat, lon: location coordinates (decimal degrees)
        tz_name: IANA timezone name (e.g. "Asia/Kolkata")
        tithi_en: English tithi name from our engine (e.g. "Dashami")
        nakshatra_en: English nakshatra name from our engine (e.g. "Rohini")
        sunrise: "HH:MM" sunrise time from our engine

    Returns dict with keys:
        status: "verified" | "partial" | "mismatch" | "unavailable"
        source: display name of the reference source
        source_url: URL that was checked
        checked_at: ISO UTC timestamp
        details: {element: {"ours": str, "reference": str, "match": bool}}
    """
    tz_off = _tz_offset(tz_name)
    source_url = (
        f"{_PROKERALA_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"
        f"?la={lat:.4f}&lo={lon:.4f}&tz={tz_off:.1f}&ayanamsa=1"
    )
    checked_at = datetime.datetime.utcnow().isoformat() + "Z"
    base = {
        "source": "Prokerala Panchangam",
        "source_url": source_url,
        "checked_at": checked_at,
        "details": {},
    }

    cache_key = _cache_key(date, lat, lon)
    raw = _read_s3(cache_key)
    if raw is None:
        try:
            raw = _fetch_prokerala(date, lat, lon, tz_name)
            if raw:
                _write_s3(cache_key, raw)
        except Exception:
            return {**base, "status": "unavailable"}

    if not raw:
        return {**base, "status": "unavailable"}

    details: dict[str, dict] = {}

    # Tithi comparison (case-insensitive prefix match)
    ref_tithi = _lookup(raw, "tithi")
    tithi_match = bool(
        tithi_en and ref_tithi and tithi_en.lower() in ref_tithi.lower()
    )
    details["tithi"] = {"ours": tithi_en, "reference": ref_tithi, "match": tithi_match}

    # Nakshatra comparison (case-insensitive prefix match)
    ref_nak = _lookup(raw, "nakshatra")
    nak_match = bool(
        nakshatra_en and ref_nak and nakshatra_en.lower() in ref_nak.lower()
    )
    details["nakshatra"] = {"ours": nakshatra_en, "reference": ref_nak, "match": nak_match}

    # Sunrise comparison (within ±2 min)
    ref_sunrise_raw = _lookup(raw, "sunrise")
    our_h = _parse_time_to_hours(sunrise)
    ref_h = _parse_time_to_hours(ref_sunrise_raw)
    if our_h is not None and ref_h is not None:
        sr_match = abs(our_h - ref_h) * 60 <= _SUNRISE_TOL_MIN
    else:
        sr_match = False
    details["sunrise"] = {"ours": sunrise, "reference": ref_sunrise_raw, "match": sr_match}

    # Determine overall status
    critical_matches = [tithi_match, nak_match]
    if all(critical_matches) and sr_match:
        status = "verified"
    elif all(critical_matches):
        status = "partial"
    else:
        status = "mismatch"

    return {**base, "status": status, "details": details}
```

- [ ] **Step 3: Spot-check the module loads cleanly**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -c "from compute.panchangam_validator import validate_muhurtam_date; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add panchang-api/compute/panchangam_validator.py
git commit -m "feat: add panchangam_validator module

Fetches Prokerala Panchangam for a given date+location, parses tithi/
nakshatra/sunrise, compares against our engine output, returns:
  status: 'verified' | 'partial' | 'mismatch' | 'unavailable'

Results cached in S3 (prefix panchang-ref/) for 30 days.
Never raises — degrades gracefully to status='unavailable'.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 7: Integration Test for panchangam_validator

**Files:**
- Create: `panchang-api/tests/test_panchangam_validator.py`

- [ ] **Step 1: Create the test file**

Create `panchang-api/tests/test_panchangam_validator.py`:

```python
"""Tests for panchangam_validator — uses mocks for HTTP and S3."""
import sys
import datetime
import json
from unittest.mock import patch, MagicMock
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_prokerala_html(tithi: str, nakshatra: str, sunrise: str) -> str:
    """Build minimal Prokerala-like HTML with panchang elements in a table."""
    return f"""
    <html><body>
    <table>
      <tr><td>Tithi</td><td>{tithi}</td></tr>
      <tr><td>Nakshatra</td><td>{nakshatra}</td></tr>
      <tr><td>Sunrise</td><td>{sunrise}</td></tr>
      <tr><td>Yoga</td><td>Vriddhi</td></tr>
    </table>
    </body></html>
    """


def _import_validator():
    """Import with boto3 mocked so it works without AWS credentials."""
    for mod in list(sys.modules):
        if "panchangam_validator" in mod:
            del sys.modules[mod]
    sys.modules.setdefault("boto3", MagicMock())
    import importlib
    import compute.panchangam_validator as v
    importlib.reload(v)
    return v


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestValidateMuhurtamDate:

    def test_verified_when_tithi_nakshatra_sunrise_all_match(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Rohini", "05:43 AM")
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "verified"
        assert result["source"] == "Prokerala Panchangam"
        assert result["details"]["tithi"]["match"] is True
        assert result["details"]["nakshatra"]["match"] is True
        assert result["details"]["sunrise"]["match"] is True

    def test_partial_when_tithi_nakshatra_match_but_sunrise_off(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Rohini", "06:10 AM")  # 27 min off
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "partial"
        assert result["details"]["tithi"]["match"] is True
        assert result["details"]["sunrise"]["match"] is False

    def test_mismatch_when_nakshatra_differs(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Mrigashira", "05:43 AM")
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "mismatch"
        assert result["details"]["nakshatra"]["match"] is False

    def test_unavailable_when_fetch_fails(self):
        v = _import_validator()
        with patch("urllib.request.urlopen", side_effect=Exception("Network error")), \
             patch.object(v, "_read_s3", return_value=None):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "unavailable"

    def test_uses_s3_cache_when_available(self):
        v = _import_validator()
        cached = {
            "tithi":    "Dashami",
            "nakshatra": "Rohini",
            "sunrise":  "05:43 AM",
        }
        with patch.object(v, "_read_s3", return_value=cached), \
             patch("urllib.request.urlopen") as mock_url:
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        mock_url.assert_not_called()   # should NOT hit network when cache hits
        assert result["status"] == "verified"
```

- [ ] **Step 2: Run the new tests**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_panchangam_validator.py -v
```

Expected:
```
test_verified_when_tithi_nakshatra_sunrise_all_match PASSED
test_partial_when_tithi_nakshatra_match_but_sunrise_off PASSED
test_mismatch_when_nakshatra_differs PASSED
test_unavailable_when_fetch_fails PASSED
test_uses_s3_cache_when_available PASSED
5 passed
```

- [ ] **Step 3: Run full suite**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py tests/test_panchangam_validator.py -q
```

Expected: 86 passed (81 + 5 new).

- [ ] **Step 4: Commit**

```bash
git add panchang-api/tests/test_panchangam_validator.py
git commit -m "test: add integration tests for panchangam_validator

5 tests covering verified/partial/mismatch/unavailable/cache-hit paths.
All HTTP and S3 calls are mocked.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 8: Wire Validator into handler_muhoortam.py

**Files:**
- Modify: `panchang-api/handler_muhoortam.py`

- [ ] **Step 1: Add imports**

At the top of `handler_muhoortam.py`, add after the existing imports:

```python
import datetime

from compute.panchangam_validator import validate_muhurtam_date
from compute.panchang import TITHI_EN, NAKSHATRA_EN
```

- [ ] **Step 2: Call validator after results are computed**

In `_handle_find()`, immediately after the line `results = find_muhurtas_for_month(...)` and the `except Exception` block, and before `if month_cache is None:`, insert:

```python
    # Cross-validate each result date against Prokerala Panchangam.
    # Runs only for the final result set (not every day in the scan range).
    # Failures are silently caught — validation never blocks the response.
    for r in results:
        try:
            day_str, month_str, year_str = r["date_raw"].split("/")
            result_date = datetime.date(int(year_str), int(month_str), int(day_str))
            tithi_en    = TITHI_EN[r["tithi_idx"]]
            nakshatra_en = NAKSHATRA_EN[r["nak_idx"]]
            r["validation"] = validate_muhurtam_date(
                date=result_date,
                lat=geo["lat"],
                lon=geo["lon"],
                tz_name=geo["tz_name"],
                tithi_en=tithi_en,
                nakshatra_en=nakshatra_en,
                sunrise=r["sunrise"],
            )
        except Exception:
            r["validation"] = {"status": "unavailable", "source": "Prokerala Panchangam"}
```

- [ ] **Step 3: Verify the handler still imports cleanly**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -c "
import sys, types
# Stub swisseph and boto3 so we can test import only
sys.modules['swisseph'] = types.ModuleType('swisseph')
sys.modules['boto3'] = types.ModuleType('boto3')
import handler_muhoortam
print('Handler import OK')
"
```

Expected: `Handler import OK`

- [ ] **Step 4: Run full test suite**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py tests/test_panchangam_validator.py -q
```

Expected: 86 passed.

- [ ] **Step 5: Commit**

```bash
git add panchang-api/handler_muhoortam.py
git commit -m "feat: attach panchangam validation to each muhurtam result

After find_muhurtas_for_month() returns, call validate_muhurtam_date()
for each result date. Attaches 'validation' dict:
  {status, source, source_url, checked_at, details}
Validation errors never block the response (fallback to 'unavailable').

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 9: Frontend Validation Badge and Detail Section

**Files:**
- Modify: `docs/muhoortam/index.html`

### Background

Each result day card should show a badge below the date, driven by `r.validation.status`.
The detail overlay should show a cross-check table when `validation.status !== "unavailable"`.

Badge display rules:
- `"verified"` or `"partial"` → green badge: `✓ Verified · <source>`
- `"mismatch"` → amber badge: `⚠ Verify with local pandit`
- `"unavailable"` → no badge

- [ ] **Step 1: Add CSS for the validation badge**

In the `<style>` block (before `</style>`), add:

```css
.validation-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.62rem;
  font-weight: 600;
  border-radius: 10px;
  padding: 2px 8px;
  margin-top: 3px;
}
.validation-badge.verified  { background: #E8F5E9; color: #2E7D32; }
.validation-badge.partial   { background: #E8F5E9; color: #2E7D32; }
.validation-badge.mismatch  { background: #FFF8E1; color: #F57F17; }
```

- [ ] **Step 2: Add `_validationBadgeHtml()` helper function**

In the JavaScript section, after the `_scoreHtml` function, add:

```js
function _validationBadgeHtml(validation) {
  if (!validation) return '';
  const st = validation.status;
  if (st === 'verified' || st === 'partial') {
    const src = validation.source || 'Prokerala Panchangam';
    return `<span class="validation-badge ${st}">✓ ${t('పరీక్షించబడింది','Verified')} · ${src}</span>`;
  }
  if (st === 'mismatch') {
    return `<span class="validation-badge mismatch">⚠ ${t('స్థానిక పంచాంగంతో తనిఖీ చేయండి','Verify with local pandit')}</span>`;
  }
  return '';
}
```

- [ ] **Step 3: Add badge to day result cards**

In the day result card rendering (around where `result-badge` appears, line ~1996), find the code that renders each result `r`:

```js
<div class="result-badge">${tNakshatra(r.nakshatra_te)}<br>${tTithi(r.tithi_te)}</div>
```

And after this line (within the same card HTML block), add:

```js
${_validationBadgeHtml(r.validation)}
```

(Place it directly after the `result-badge` div, on the same level.)

- [ ] **Step 4: Add cross-check table to detail overlay**

In the "More Details" overlay body (the section that shows hard_blocks, warnings, benefits), find the closing `</div>` of the score section and add a new section after it:

```js
// Add inside the detail overlay HTML, after the score section:
${(() => {
  const val = bestDay.validation;
  if (!val || val.status === 'unavailable') return '';
  const details = val.details || {};
  const rows = Object.entries(details).map(([key, d]) => `
    <tr>
      <td style="text-transform:capitalize">${key}</td>
      <td>${d.ours || '—'}</td>
      <td>${d.reference || '—'}</td>
      <td>${d.match ? '✓' : '✗'}</td>
    </tr>`).join('');
  const srcUrl = val.source_url ? `<a href="${val.source_url}" target="_blank" rel="noopener" style="font-size:0.6rem;color:#1565C0">${val.source}</a>` : val.source;
  return `
    <div style="margin-top:16px">
      <div style="font-weight:700;font-size:0.75rem;color:#37474F;margin-bottom:6px">
        ${t('పంచాంగ పరీక్ష','Panchangam Cross-Check')} — ${srcUrl}
      </div>
      <table class="score-details-table">
        <tr style="font-size:0.6rem;color:#888">
          <th>${t('అంశం','Element')}</th>
          <th>${t('మన విలువ','Ours')}</th>
          <th>${t('మూలం','Reference')}</th>
          <th>${t('సరిపోలిక','Match')}</th>
        </tr>
        ${rows}
      </table>
    </div>`;
})()}
```

- [ ] **Step 5: Test in browser**

Load `http://localhost:8080/muhoortam/`, run a muhurtam search. Confirm:
- Results show the green ✓ badge if validation data is present
- Clicking "More Details" shows the cross-check table
- Switching to EN mode shows "Verified" not the Telugu text

Note: In local dev, the API server does not have `PANCHANG_CACHE_BUCKET` set and there is no live S3, so the validator will return `"unavailable"`. To test the badge display without live API, temporarily hardcode a fixture in the JS:

```js
// TEMP DEV ONLY — add to the test fetch response to simulate validation:
// r.validation = {status:"verified", source:"Prokerala Panchangam", source_url:"https://prokerala.com", details:{}};
```

Remove this temp code before committing.

- [ ] **Step 6: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: add panchangam validation badge and cross-check table to UI

- New .validation-badge CSS classes (verified/partial/mismatch)
- _validationBadgeHtml() renders badge from r.validation.status
- Badge appears on each day result card
- 'More Details' overlay shows element-by-element cross-check table
- All labels have data-te/data-en equivalents via t() calls

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 10: Deploy and Smoke-Test

- [ ] **Step 1: Push to origin**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang
git push origin master
```

GitHub Pages auto-deploys from `docs/`. The Lambda backend deploys separately — if `sam deploy` is available, run it; otherwise the backend changes are staged for the next Lambda deployment.

- [ ] **Step 2: Smoke-test the live site**

Open `https://muhoortam.sanathanadharmas.com`, search for a month with some muhurtam results. Verify:
- Language toggle works — EN shows English lagna names and choghadiya
- Score breakdown shows English text when EN mode is active
- Validation badge appears on result cards (initially may show nothing if Lambda isn't redeployed)

- [ ] **Step 3: Final test run**

```bash
cd /Users/schinta/MyDrive/MyCode/telugu-panchang/panchang-api
python3 -m pytest tests/test_muhoortam.py tests/test_precompute.py tests/test_panchangam_validator.py -q
```

Expected: 86 passed, 0 failed.
