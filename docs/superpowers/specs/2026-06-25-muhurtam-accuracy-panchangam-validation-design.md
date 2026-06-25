# Muhurtam Accuracy — Telugu Sampradaya Rules + Panchangam Validation
**Date:** 2026-06-25  
**Scope:** Backend rule additions + post-computation validation against online Panchangam sources  
**Sources:** Muhurta Chintamani, Dharmasindhu, Venkatrama & Co. Telugu Panchangam, Prokerala Telugu Panchangam API

---

## 1. Goals

1. **Close the rule gaps** — add Guru Asta (Jupiter combust) and refine existing rules to match Telugu Sampradaya standards.  
2. **Validate computed muhurtams** — after generating results, cross-check the underlying panchang elements for each result date against an authoritative online Telugu Panchangam.  
3. **Surface validation status in the UI** — each result card shows which source was checked, and whether it passed.

---

## 2. Missing Rules to Add

### 2a. Guru Asta (Jupiter Combust) — HIGH PRIORITY

**What it is:** When Jupiter is within 11° of the Sun (ecliptic longitude), it is considered "asta" (combust/hidden). During this period, Jupiter's auspiciousness is eliminated. Per Telugu Sampradaya, this is a hard block for the three most sacred ceremonies.

**Gap:** `_COMBUSTION_ORB["guru"] = 11.0` is already defined but never used. `shukra_combust` is checked; `guru_combust` is not.

**Implementation:**
- In `check_lagna_graha_quality()` (`muhurta_rules.py`), add a `guru_combust` check parallel to the existing `shukra_combust` check.
- `planet_longitudes` dict already passed in — `planet_longitudes["guru"]` is available.
- Severity:

| Ceremony | Severity |
|---|---|
| `vivaha` | `"hard"` (block) |
| `gruha_pravesam` | `"hard"` |
| `upanayanam` | `"hard"` |
| `pooja`, `prayanam`, others | `"soft"` (penalty only) |

- Score component label: `{"te": "గురు అస్తమయం", "en": "Jupiter Combust (Guru Asta)", "delta": -30}` for hard block.

### 2b. Add English keys to all `score_components` entries

**Gap:** Every `_add()` call in `check_lagna_graha_quality()` appends only `{"te": ..., "delta": ...}`. No `"en"` key, so score breakdown always shows Telugu text even when UI is in English.

**Implementation:**
- Add `en: str = ""` param to `_add()` helper.
- Update all ~15 existing `_add()` call sites with English translations.
- Frontend score rendering already checks `comp["en"]` if `lang == "en"` — the field just needs to exist.

### 2c. Chaturmasya Period Block (review/tighten)

**Current state:** `_CHATURMAS_MASAM[CEREMONY_VIVAHA] = set()` — explicitly cleared with comment "No Chaturmasya ban — Telugu tradition." 

**Decision:** Keep as-is. The code comment correctly states that in Telugu tradition Chaturmasya is not an absolute vivaha ban (unlike North Indian tradition). Do not change this rule unless a specific Telugu authority source contradicts it.

### 2d. Lagna Lookup Mismatch (Frontend)

**Gap:** Frontend `_LAGNA_TE_LIST` has `'తుల'`, `'ధనుసు'` but backend `RASHI_TE` returns `'తులం'`, `'ధనుస్సు'`. Lookup fails silently → lagna names never translate to English.

**Implementation:** Fix `_LAGNA_TE_LIST` in `docs/muhoortam/index.html` to exactly match `panchang-api/compute/birth_chart.py:RASHI_TE`.

### 2e. Choghadiya Translation (Frontend)

**Gap:** Choghadiya is rendered with `t(choghadiya_te, choghadiya_te)` — both params identical → EN mode still shows Telugu.

**Implementation:** Add `tChoghadiya()` function in `index.html` with `_CHO_TE_LIST` / `_CHO_EN` lookup arrays; replace all raw choghadiya usages.

---

## 3. Panchangam Validation Pipeline

### 3a. When validation runs

Validation runs **after** muhurtam windows are computed — only for the final result set. It does NOT run on every day in the scan range.

Flow:
```
User submits → engine scans date range → muhurtam windows produced
→ for each result date, fetch reference panchang (once per date+location, cached)
→ compare panchang elements
→ attach verification result to each muhurtam object
→ return to frontend
```

### 3b. Reference source

**Primary:** [Prokerala Telugu Panchangam](https://www.prokerala.com/astrology/telugu-panchangam/)  
URL pattern: `https://www.prokerala.com/astrology/telugu-panchangam/date/{YYYY}/{MM}/{DD}/?location={city}&ayanamsa=1`  
Returns tithi, nakshatra, yoga, sunrise, rahu kalam, yamaganda for the requested location.  
Ayanamsa=1 = Lahiri (matching our engine).

**Fallback:** [Drikpanchang Telugu](https://www.drikpanchang.com/telugu/panchangam/telugu-panchangam.html)  
Only used if Prokerala returns an error.

### 3c. What is compared

| Element | Our field | Match criteria |
|---|---|---|
| Sunrise (local) | `sunrise_time` | Within ±2 minutes |
| Tithi at sunrise | `tithi_idx` | Same ordinal |
| Nakshatra at sunrise | `nakshatra_idx` | Same ordinal |
| Yoga at sunrise | `yoga_idx` | Same ordinal |
| Rahu Kalam start | `rahu_start` | Within ±5 minutes |

**Match result:**
- `"verified"` — all 5 elements match
- `"partial"` — sunrise + tithi + nakshatra match, minor diff in yoga or rahu
- `"mismatch"` — tithi or nakshatra differ → flag prominently, do NOT suppress result

### 3d. Caching

- Cache layer: `panchang-api/compute/s3_cache.py` (already exists)
- Cache key: `prokerala-panchang/{YYYY-MM-DD}/{lat:.2f}/{lon:.2f}`
- TTL: 30 days (panchang data for a past date never changes)
- Cache population: one fetch per unique date+location, stored as JSON

### 3e. New module: `panchang-api/compute/panchangam_validator.py`

Single public function:
```python
def validate_muhurtam_date(
    date: datetime.date,
    lat: float,
    lon: float,
    our_panchang: dict,
) -> dict:
    """
    Returns:
        {
            "status": "verified" | "partial" | "mismatch" | "unavailable",
            "source": "Prokerala Telugu Panchangam",
            "checked_at": ISO timestamp,
            "details": { element: {"ours": ..., "reference": ..., "match": bool}, ... }
        }
    """
```

Internally:
1. Check S3 cache — return if hit
2. Fetch Prokerala HTML → parse with `lxml` / `BeautifulSoup`
3. Compare against `our_panchang` dict
4. Store to S3 cache
5. Return status dict

### 3f. Integration in handler

In `handler_muhoortam.py`, after `find_muhurtam_windows()` returns results, call `validate_muhurtam_date()` for each unique date in results. Attach `"validation"` key to each muhurtam object in the response.

If external fetch fails (network error, scrape format changed): set `status = "unavailable"`, do not block the response.

---

## 4. UI Changes

### 4a. Validation badge on result cards

Each result card in the results list shows a badge below the date/time:

- `✓ Verified — Prokerala Telugu Panchangam` (green) — status = `"verified"` or `"partial"`
- `⚠ Verify with local pandit` (amber) — status = `"mismatch"`
- *(no badge)* — status = `"unavailable"`

### 4b. Detail sheet expansion

In the "More Details" overlay, add a "Panchangam Cross-Check" section showing the element-by-element comparison table. Visible only when `validation.status !== "unavailable"`.

### 4c. Translation

All new badge/label strings get `data-te`/`data-en` attributes so the existing `_applyI18n()` system handles them.

---

## 5. Testing

### 5a. Unit tests (existing test suite)

- `tests/test_muhoortam.py` — add test case: date where Jupiter is combust → vivaha blocked
- `tests/test_muhoortam.py` — add test: English `score_components` keys present in output
- `tests/test_precompute.py` — no changes needed

### 5b. Integration test (new)

New file: `tests/test_panchangam_validator.py`  
- Fixture: known panchang values for 2026-06-25 Hyderabad (from session baseline — verified matches prokerala)
- Mock `urllib` fetch to return fixture HTML
- Assert `validate_muhurtam_date()` returns `"verified"` for the fixture date
- Assert it returns `"unavailable"` when fetch fails (connection error mock)

### 5c. Reference baseline

The baseline established in this session:  
- Date: 2026-06-25, Location: Hyderabad (17.385N, 78.487E)
- Sunrise: 05:43 local (our) vs 05:44 (drikpanchang) — within 2 min tolerance ✓
- Use this as a regression anchor in the test fixture

---

## 6. Implementation Sequence

1. **Frontend translation fixes** (lagna list, choghadiya, score EN keys) — no backend dependency  
2. **Guru Asta rule** in `muhurta_rules.py` + `_add()` English keys  
3. **`panchangam_validator.py`** — new module with caching  
4. **`handler_muhoortam.py`** — wire validator into response  
5. **Frontend badge + detail section** — consume `validation` field  
6. **Tests** — unit + integration  
7. **Deploy** — push to master → GitHub Pages

---

## 7. Out of Scope (deferred)

- Automated scheduled comparison job (CI/cron) — defer to a future spec
- Shunya Masa detection — insufficient Telugu authority source to confirm rule; defer
- Muhurtam export (PDF/iCal) — different feature track
