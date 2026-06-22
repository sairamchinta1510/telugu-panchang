# Performance Optimization Design — Muhurtam Scan Speed

**Date:** 2025-07-15  
**Goal:** Reduce `/muhoortam/find` response time from >30 s (timeout) to 3–8 s  
**Approach:** Three targeted changes, no new infrastructure  

---

## Context

The `/muhoortam/find` endpoint scans a calendar month day-by-day using swisseph.
For each "non-obvious" day it calls `_find_good_windows()`, which does:
- `compute_lagna()` + three `find_next_index_change()` bisections per window segment
- `compute_planet_rashis()` — 9 swisseph calls per **good** window

A 30-day scan with 10 good days × 3 windows each produces **~600–900 swisseph calls**,
easily hitting the Lambda 30-second timeout.

The Lambda runs at 256 MB (≈14% of one vCPU). Cold start adds 2–3 s.

---

## Change 1 — Lazy Planet Rashis (biggest win)

### Problem
`compute_planet_rashis(jd)` is called inside `_find_good_windows()` for **every good window**
during the month scan (9 swisseph calls × N good windows). These are never needed until
the user expands a result card to view the horoscope.

### Design

**Backend (`muhurta_finder.py`)**
- Add `skip_planet_rashis: bool = False` parameter to `_find_good_windows()`.
- When `True`, skip the `compute_planet_rashis()` call and omit `planet_rashis` from
  the returned window dict.
- `find_muhurtas_for_month()` always passes `skip_planet_rashis=True`.
- `check_muhurta_day()` keeps `skip_planet_rashis=False` (single-day check — fast).

**Backend (`handler_muhoortam.py`)**
- Add new route: `POST /muhoortam/window-detail`
- Request body: `{ceremony_place, date}` where `date` is `"DD/MM/YYYY"`.
- Planet positions (rashis) change over days, not hours, so computing at local noon
  is accurate enough for the horoscope display.
- Handler geocodes place, computes Julian day at local noon on `date`, calls
  `compute_planet_rashis(jd)` for that moment, returns `{planet_rashis}`.
- Also register the route in `template.yaml` SAM events.

**Frontend (`index.html`)**
- On result card expand/tap: if `planet_rashis` is absent in the window, call
  `POST /muhoortam/window-detail` with `{ceremony_place, date}` and render
  horoscope on response.
- Show a loading spinner inside the horoscope cell until the response arrives.
- Cache result on the day object — all windows for the same day share the same
  planet rashis (planets don't move significantly within one day), so one fetch
  per day suffices even if multiple windows are expanded.

### Savings
9 swisseph calls × N good windows eliminated from the month scan hot path.
For a typical month (10 good days × 3 windows): **270 calls saved**.

---

## Change 2 — Lambda Memory Increase

### Design
- `template.yaml`: Change global `MemorySize: 256` to `MemorySize: 512`.
- `MuhoortamFunction` inherits the global; no per-function override needed.

### Effect
Lambda CPU is proportional to memory allocation (1769 MB = 1 vCPU).
- 256 MB ≈ 14.5% vCPU → 512 MB ≈ 29% vCPU
- All swisseph arithmetic runs ~2× faster
- No code change; cold-start time also halves for pyswisseph import

### Cost
Lambda charges per GB-second. 2× memory with 2× faster execution = roughly the same
monthly cost. Acceptable trade-off for interactive use.

---

## Change 3 — Same-Nakshatra Pre-filter

### Problem
`_find_good_windows()` runs the full 24-hour lagna-transition scan even on days where
the nakshatra is bad for the ceremony AND does not change all day. It will always return
an empty list on such days, wasting ~30–50 swisseph calls.

### Design
In `find_muhurtas_for_month()`, add a check immediately before calling
`_find_good_windows()`:

```python
# Already computed: naks_idx at rise_jd
naks_idx_end = int(moon_longitude(rise_jd + 1.0) / (360.0 / 27)) % 27
good_naks = _GOOD_NAKSHATRAS.get(ceremony_type, set())
if naks_idx not in good_naks and naks_idx_end not in good_naks and naks_idx == naks_idx_end:
    continue  # single bad nakshatra spans full 24 hours — skip
```

The three-condition guard (`naks_idx == naks_idx_end`) ensures we only skip when **no
nakshatra transition** occurred, so no good transition window is missed. Cost: one extra
`moon_longitude()` call per day (negligible vs. the ~50 calls saved on match).

### Savings
Eliminates `_find_good_windows()` calls on days where the same bad nakshatra persists
for the full 24-hour window. Empirically ~25–35% of all days across ceremonies.

---

## Data Flow After Changes

```
POST /muhoortam/find
  └─ find_muhurtas_for_month()
       └─ per day:
            ├─ get_sunrise_sunset()               (2 swisseph)
            ├─ moon_longitude() × 2               (sunrise + rise+24h for pre-filter)
            ├─ [SKIP if same bad nakshatra]        ← Change 3
            ├─ compute_lagna(rise_jd)             (1 swisseph)
            ├─ compute_panchang()
            └─ _find_good_windows(skip_planet_rashis=True)  ← Change 1
                 └─ per window segment:
                      ├─ moon_longitude() + elongation
                      ├─ compute_lagna()
                      ├─ find_next_index_change() × 3
                      └─ [NO compute_planet_rashis]   ← Change 1

POST /muhoortam/window-detail  (on user tap)     ← Change 1 (new endpoint)
  └─ compute_planet_rashis(noon_jd)              (9 swisseph, lazy, per day)
```

---

## Testing Strategy

- Update `test_muhoortam.py` mock: `fake_windows` in `/find` results must NOT include
  `planet_rashis` key; assert it is absent.
- Add one new test for the `/window-detail` endpoint: POST `{ceremony_place, date}`,
  assert it returns `planet_rashis` dict with keys for all 9 grahas.
- Run existing 48 tests to confirm no regressions.
- Manual timing test: scan July 2026 vivaha with one birth chart; target < 8 s.

---

## Files Changed

| File | Change |
|------|--------|
| `panchang-api/compute/muhurta_finder.py` | `skip_planet_rashis` param; same-nakshatra pre-filter |
| `panchang-api/handler_muhoortam.py` | New `_handle_window_detail()` handler + route dispatch |
| `panchang-api/template.yaml` | `MemorySize: 256 → 512`; new SAM event for `/window-detail` |
| `panchang-api/tests/test_muhoortam.py` | Update assertions + add window-detail test |
| `docs/muhoortam/index.html` | Lazy horoscope fetch on card expand |
