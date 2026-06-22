# Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce `/muhoortam/find` response time from timeout (>30 s) to 3–8 s with no new infrastructure.

**Architecture:** Three targeted changes — (1) remove `compute_planet_rashis()` from the scan hot-path and serve it lazily via a new `/window-detail` endpoint, (2) raise Lambda memory from 256 MB to 512 MB for ~2× CPU speed, (3) add a nakshatra pre-filter to skip `_find_good_windows()` on guaranteed-bad days.

**Tech Stack:** Python 3.12 (Lambda), pyswisseph, AWS SAM, vanilla JS (GitHub Pages)

---

## File Map

| File | What changes |
|---|---|
| `panchang-api/compute/muhurta_finder.py` | `skip_planet_rashis` param in `_find_good_windows()`; `date_raw` field in result; nakshatra pre-filter in `find_muhurtas_for_month()` |
| `panchang-api/handler_muhoortam.py` | New `_handle_window_detail()` + route dispatch; import `local_date_to_jd` and `compute_planet_rashis` |
| `panchang-api/template.yaml` | `MemorySize: 256 → 512`; new SAM event for `/muhoortam/window-detail` |
| `panchang-api/tests/test_muhoortam.py` | 6 new tests; assert `planet_rashis` absent from `/find` windows |
| `docs/muhoortam/index.html` | `showDetail()` uses placeholder divs; new `_loadHoroscopeForDetail()` fetches lazily |

---

## Task 1: Skip planet rashis in `_find_good_windows()` + add `date_raw` + nakshatra pre-filter

**Files:**
- Modify: `panchang-api/compute/muhurta_finder.py`

- [ ] **Step 1: Add `skip_planet_rashis` parameter to `_find_good_windows()`**

Change the function signature (line 48) and the planet-rashis call site inside the `if good:` block (around line 109). Full changes:

Signature — add `skip_planet_rashis: bool = False` as the last parameter:

```python
def _find_good_windows(
    rise_jd: float,
    set_jd: float,
    lat: float, lon: float, tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    masam_name: str,
    is_adhika: bool,
    sun_idx: int,
    lagna_idx: int,
    skip_planet_rashis: bool = False,
) -> list[dict]:
```

Inside `if good:`, replace the `planet_rashis = compute_planet_rashis(jd)` line and the `good_windows.append({...})` block with:

```python
        if good:
            from_str = jd_to_local_datetime(jd,            tz_name).strftime("%H:%M")
            to_str   = jd_to_local_datetime(window_end_jd, tz_name).strftime("%H:%M")
            h_from, m_from = map(int, from_str.split(":"))
            h_to,   m_to   = map(int, to_str.split(":"))
            total_from = h_from * 60 + m_from
            total_to   = h_to   * 60 + m_to
            if total_to <= total_from:
                total_to += 24 * 60

            # Find best Choghadiya slot overlapping this window
            best_cho_rank = -1
            best_cho_te   = ""
            best_time_str = from_str
            for slot in cho_slots:
                overlap_start = max(slot["from_jd"], jd)
                overlap_end   = min(slot["to_jd"],   window_end_jd)
                if overlap_end - overlap_start < EPSILON:
                    continue
                if slot["quality_rank"] > best_cho_rank:
                    best_cho_rank = slot["quality_rank"]
                    best_cho_te   = slot["quality_te"]
                    best_time_str = jd_to_local_datetime(
                        max(slot["from_jd"], jd), tz_name
                    ).strftime("%H:%M")

            entry = {
                "from":            from_str,
                "to":              to_str,
                "duration_mins":   total_to - total_from,
                "nakshatra_te":    NAKSHATRA_TE[naks_idx],
                "tithi_te":        TITHI_TE[tithi_idx],
                "lagna_te":        RASHI_TE[win_lagna_idx],
                "nak_idx":         naks_idx,
                "tithi_idx":       tithi_idx,
                "sun_idx":         sun_idx,
                "lagna_idx":       win_lagna_idx,
                "best_time":       best_time_str,
                "choghadiya_te":   best_cho_te,
                "choghadiya_rank": best_cho_rank,
            }
            if not skip_planet_rashis:
                entry["planet_rashis"] = compute_planet_rashis(jd)
            good_windows.append(entry)
```

- [ ] **Step 2: Add nakshatra pre-filter and `date_raw` in `find_muhurtas_for_month()`**

In `find_muhurtas_for_month()`, replace the entire `for day in range(...)` loop body with the version below. Key changes: (a) nakshatra pre-filter before `_find_good_windows`, (b) `skip_planet_rashis=True` passed to `_find_good_windows`, (c) `date_raw` added to the appended dict:

```python
    for day in range(1, days_in_month + 1):
        try:
            jd      = local_date_to_jd(year, month, day, tz_name)
            rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)

            moon_lon  = moon_longitude(rise_jd)
            elong     = moon_sun_elongation(rise_jd)
            naks_idx  = int(moon_lon / (360.0 / 27)) % 27
            tithi_idx = int(elong / 12) % 30
            day_rashi_idx = int(moon_lon / 30) % 12

            dt_rise   = jd_to_local_datetime(rise_jd, tz_name)
            sun_idx   = (dt_rise.weekday() + 1) % 7   # Sunday=0 … Saturday=6

            lagna_idx = compute_lagna(rise_jd, lat, lon)

            pan = compute_panchang(jd, lat, lon, tz_name)
            masam_name = pan["masam"]["en"]
            is_adhika  = pan["masam"]["adhika"]

            good_at_sunrise = is_auspicious(
                naks_idx, tithi_idx, sun_idx, lagna_idx,
                birth_charts, ceremony_type,
                masam_name=masam_name, is_adhika_masam=is_adhika,
                day_rashi_idx=day_rashi_idx,
            )

            good_windows: list[dict] = []
            if good_at_sunrise:
                good_windows = []   # good all day — no restriction
            else:
                # Pre-filter: if the same bad nakshatra spans the full 24 h, no
                # good window transition can exist — skip the expensive scan.
                good_naks = _GOOD_NAKSHATRAS.get(ceremony_type, set())
                if naks_idx not in good_naks:
                    naks_idx_end = int(moon_longitude(rise_jd + 1.0) / (360.0 / 27)) % 27
                    if naks_idx_end not in good_naks and naks_idx_end == naks_idx:
                        continue  # single bad nakshatra covers full 24 h — skip
                good_windows = _find_good_windows(
                    rise_jd, set_jd, lat, lon, tz_name,
                    ceremony_type, birth_charts, masam_name, is_adhika,
                    sun_idx, lagna_idx,
                    skip_planet_rashis=True,
                )
                if not good_windows:
                    continue   # truly bad all day

            dt_set    = jd_to_local_datetime(set_jd, tz_name)
            rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
            set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60

            kalams = compute_kalams(rise_mins, set_mins, sun_idx)

            results.append({
                "date_te":      f"{day} {_MONTH_TE[month - 1]} {year}",
                "date_raw":     f"{day:02d}/{month:02d}/{year}",
                "vaaram_te":    pan["vaaram"]["te"],
                "sunrise":      dt_rise.strftime("%H:%M"),
                "sunset":       dt_set.strftime("%H:%M"),
                "tithi_te":     pan["tithi"]["te"],
                "nakshatra_te": pan["nakshatra"]["te"],
                "yoga_te":      pan["yoga"]["te"],
                "rahu_kalam":   kalams["rahu_kalam"],
                "yamaganda":    kalams["yamaganda"],
                "gulika_kalam": kalams["gulika_kalam"],
                "dur_muhurtam": pan["dur_muhurtam"],
                "varjyam":      pan["varjyam"],
                "good_from":    good_windows[0]["from"] if good_windows else None,
                "good_windows": good_windows,
            })
        except Exception:
            continue   # skip days where calculation fails (polar extremes, etc.)
```

- [ ] **Step 3: Verify existing tests still pass**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py -q
```

Expected: all 48 tests pass.

- [ ] **Step 4: Commit**

```bash
git add panchang-api/compute/muhurta_finder.py
git commit -m "perf: skip planet_rashis in find scan, add date_raw, nakshatra pre-filter"
```

---

## Task 2: Tests for Task 1 changes

**Files:**
- Modify: `panchang-api/tests/test_muhoortam.py`

- [ ] **Step 1: Add three tests after `test_check_muhurta_day_bad_day_has_good_windows` (end of file)**

```python
def test_find_good_windows_skip_planet_rashis_omits_key():
    """_find_good_windows(skip_planet_rashis=True) must not call compute_planet_rashis
    and must not include planet_rashis key in returned window dicts."""
    mf = _load_finder({1})  # day 1 = Rohini nakshatra = vivaha-good
    import compute.muhurta_finder as _mf
    from unittest.mock import MagicMock
    mock_pr = MagicMock(return_value={
        "ravi": 0, "chandra": 1, "kuja": 2, "budha": 3,
        "guru": 4, "shukra": 5, "shani": 6, "rahu": 7, "ketu": 1,
    })
    _mf.compute_planet_rashis = mock_pr
    birth_charts = [{"janma_nakshatra_idx": 0}]
    windows = _mf._find_good_windows(
        1.0, 1.5, 17.38, 78.49, "Asia/Kolkata",
        "vivaha", birth_charts, "Jyeshtha", False, 4, 3,
        skip_planet_rashis=True,
    )
    mock_pr.assert_not_called()
    for w in windows:
        assert "planet_rashis" not in w, "planet_rashis must be absent when skip_planet_rashis=True"


def test_find_good_windows_includes_planet_rashis_by_default():
    """_find_good_windows() includes planet_rashis in windows when skip_planet_rashis=False."""
    mf = _load_finder({1})
    import compute.muhurta_finder as _mf
    from unittest.mock import MagicMock
    mock_pr = MagicMock(return_value={
        "ravi": 0, "chandra": 1, "kuja": 2, "budha": 3,
        "guru": 4, "shukra": 5, "shani": 6, "rahu": 7, "ketu": 1,
    })
    _mf.compute_planet_rashis = mock_pr
    birth_charts = [{"janma_nakshatra_idx": 0}]
    windows = _mf._find_good_windows(
        1.0, 1.5, 17.38, 78.49, "Asia/Kolkata",
        "vivaha", birth_charts, "Jyeshtha", False, 4, 3,
    )
    assert len(windows) > 0, "Expected at least one good window for Rohini day"
    mock_pr.assert_called()
    for w in windows:
        assert "planet_rashis" in w


def test_find_muhurtas_result_has_date_raw():
    """find_muhurtas_for_month results must include date_raw in DD/MM/YYYY format."""
    mf = _load_finder({15})
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    assert len(results) >= 1
    for r in results:
        assert "date_raw" in r, "date_raw must be present in find results"
        parts = r["date_raw"].split("/")
        assert len(parts) == 3
        day_n, month_n, year_n = int(parts[0]), int(parts[1]), int(parts[2])
        assert 1 <= day_n <= 31
        assert 1 <= month_n <= 12
        assert year_n >= 2000
```

- [ ] **Step 2: Run new tests**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py::test_find_good_windows_skip_planet_rashis_omits_key \
  tests/test_muhoortam.py::test_find_good_windows_includes_planet_rashis_by_default \
  tests/test_muhoortam.py::test_find_muhurtas_result_has_date_raw -v
```

Expected: all 3 PASS.

- [ ] **Step 3: Run full suite**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py -q
```

Expected: 51 tests pass (48 original + 3 new).

- [ ] **Step 4: Commit**

```bash
git add panchang-api/tests/test_muhoortam.py
git commit -m "test: assert skip_planet_rashis behavior and date_raw field"
```

---

## Task 3: `/window-detail` endpoint (handler + SAM template)

**Files:**
- Modify: `panchang-api/handler_muhoortam.py`
- Modify: `panchang-api/template.yaml`

- [ ] **Step 1: Add imports to `handler_muhoortam.py`**

Add below the existing compute imports (after `from compute.muhurta_finder import ...`):

```python
from compute.astro import local_date_to_jd, compute_planet_rashis
```

- [ ] **Step 2: Add `_handle_window_detail()` to `handler_muhoortam.py`**

Add this function after `_handle_check()`:

```python
def _handle_window_detail(body: dict) -> dict:
    """Compute planet rashis for a single ceremony date (at local noon).

    Planet positions change over days, not hours, so noon is accurate for
    the horoscope display.

    Request:  {ceremony_place: str, date: "DD/MM/YYYY"}
    Response: {planet_rashis: {ravi, chandra, kuja, budha, guru, shukra, shani, rahu, ketu}}
    """
    try:
        date_str       = body["date"]           # "DD/MM/YYYY"
        ceremony_place = body["ceremony_place"]
    except KeyError as e:
        return _error(400, f"Missing field: {e}")

    try:
        day, month, year = [int(x) for x in date_str.split("/")]
    except (ValueError, TypeError):
        return _error(400, "date must be DD/MM/YYYY")

    try:
        geo = _geocode(ceremony_place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        jd = local_date_to_jd(year, month, day, geo["tz_name"])  # local noon
        planet_rashis = compute_planet_rashis(jd)
    except Exception:
        traceback.print_exc()
        return _error(500, "Planet rashi calculation failed")

    return _ok({"planet_rashis": planet_rashis})
```

- [ ] **Step 3: Register the route in `lambda_handler()`**

In `lambda_handler()`, add before the final `return _error(404, ...)`:

```python
    if path.endswith("/window-detail"):
        return _handle_window_detail(body)
```

The full routing block should be:

```python
    if path.endswith("/birth-chart"):
        return _handle_birth_chart(body)
    if path.endswith("/find"):
        return _handle_find(body)
    if path.endswith("/check"):
        return _handle_check(body)
    if path.endswith("/window-detail"):
        return _handle_window_detail(body)
    return _error(404, "Unknown endpoint")
```

- [ ] **Step 4: Update `template.yaml` — memory + new SAM event**

Change global `MemorySize` from `256` to `512`:

```yaml
Globals:
  Function:
    Timeout: 10
    MemorySize: 512
    Runtime: python3.12
    Environment:
      Variables:
        PYTHONDONTWRITEBYTECODE: "1"
```

Add `MuhoortamWindowDetail` event inside `MuhoortamFunction.Properties.Events` (after `MuhoortamCheck`):

```yaml
        MuhoortamWindowDetail:
          Type: HttpApi
          Properties:
            Path: /muhoortam/window-detail
            Method: POST
            ApiId: !Ref PanchangHttpApi
```

- [ ] **Step 5: Verify handler loads without errors**

```bash
cd panchang-api
python -c "import handler_muhoortam; print('OK')"
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add panchang-api/handler_muhoortam.py panchang-api/template.yaml
git commit -m "feat: add /muhoortam/window-detail endpoint; raise Lambda memory to 512 MB"
```

---

## Task 4: Tests for `/window-detail` endpoint

**Files:**
- Modify: `panchang-api/tests/test_muhoortam.py`

- [ ] **Step 1: Add three tests after `test_handler_check_bad_time_format` (around line 591)**

```python
def test_handler_window_detail_ok():
    """POST /muhoortam/window-detail returns planet_rashis with all 9 grahas."""
    h = _fresh_handler()
    MOCK_PLANET_RASHIS = {
        "ravi": 2, "chandra": 4, "kuja": 6, "budha": 1,
        "guru": 9, "shukra": 11, "shani": 7, "rahu": 0, "ketu": 6,
    }
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "compute_planet_rashis", return_value=MOCK_PLANET_RASHIS):
        event = _make_handler_event("/muhoortam/window-detail", {
            "ceremony_place": "Hyderabad, India",
            "date": "15/07/2026",
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "planet_rashis" in body
    pr = body["planet_rashis"]
    for graha in ("ravi", "chandra", "kuja", "budha", "guru", "shukra", "shani", "rahu", "ketu"):
        assert graha in pr, f"Missing graha key: {graha!r}"


def test_handler_window_detail_missing_date():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/window-detail", {
            "ceremony_place": "Hyderabad, India",
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_window_detail_bad_date_format():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/window-detail", {
            "ceremony_place": "Hyderabad, India",
            "date": "2026-07-15",  # must be DD/MM/YYYY
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400
```

- [ ] **Step 2: Run new tests**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py::test_handler_window_detail_ok \
  tests/test_muhoortam.py::test_handler_window_detail_missing_date \
  tests/test_muhoortam.py::test_handler_window_detail_bad_date_format -v
```

Expected: all 3 PASS.

- [ ] **Step 3: Run full suite**

```bash
cd panchang-api
python -m pytest tests/test_muhoortam.py -q
```

Expected: 54 tests pass (51 from Task 2 + 3 new).

- [ ] **Step 4: Commit**

```bash
git add panchang-api/tests/test_muhoortam.py
git commit -m "test: add /window-detail endpoint tests"
```

---

## Task 5: Frontend — lazy horoscope loading in `showDetail()`

**Files:**
- Modify: `docs/muhoortam/index.html`

- [ ] **Step 1: Replace the horoscope render in `showDetail()` with placeholder divs**

In `showDetail()` around line 1878, find this line inside the `r.good_windows.map(...)` template literal:

```javascript
        ${w.planet_rashis ? renderHoroscopeChart(w.planet_rashis, w.lagna_idx) : '<div style="font-size:0.75rem;color:var(--brown-mid)">గ్రహ స్థానాల సమాచారం అందుబాటులో లేదు</div>'}
```

Replace it with:

```javascript
        <div id="horoscope-w${wi}" style="min-height:40px">
          <div style="font-size:0.75rem;color:var(--brown-mid);padding:8px 0">⏳ గ్రహ స్థానాలు లోడ్ అవుతున్నాయి...</div>
        </div>
```

- [ ] **Step 2: Add async horoscope loading call at the end of `showDetail()`**

`showDetail()` ends with these two lines before the closing `}`:

```javascript
  document.getElementById("overlay").classList.add("open");
  document.body.style.overflow = "hidden";
```

Replace those two lines with three lines (still inside `showDetail`, before the `}`):

```javascript
  document.getElementById("overlay").classList.add("open");
  document.body.style.overflow = "hidden";
  if (r.good_windows && r.good_windows.length) _loadHoroscopeForDetail(r);
```

- [ ] **Step 3: Add `_loadHoroscopeForDetail()` function after `showDetail()`**

Insert this new function directly after the closing `}` of `showDetail()` and before `function closeSheet()`:

```javascript
async function _loadHoroscopeForDetail(r) {
  if (!r._planetRashis) {
    try {
      const resp = await fetch(API_BASE + "/muhoortam/window-detail", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ceremony_place: _scanPlace, date: r.date_raw }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      r._planetRashis = data.planet_rashis;
    } catch (e) {
      (r.good_windows || []).forEach((_, wi) => {
        const el = document.getElementById("horoscope-w" + wi);
        if (el) el.innerHTML = '<div style="font-size:0.75rem;color:var(--brown-mid)">గ్రహ స్థానాల సమాచారం అందుబాటులో లేదు</div>';
      });
      return;
    }
  }
  (r.good_windows || []).forEach((w, wi) => {
    const el = document.getElementById("horoscope-w" + wi);
    if (el) el.innerHTML = renderHoroscopeChart(r._planetRashis, w.lagna_idx);
  });
}
```

- [ ] **Step 4: Verify no JS syntax errors**

```bash
node --check docs/muhoortam/index.html 2>&1 || echo "syntax ok"
grep -c "horoscope-w" docs/muhoortam/index.html
```

Expected: no syntax errors; count >= 2.

- [ ] **Step 5: Commit**

```bash
git add docs/muhoortam/index.html
git commit -m "feat: lazy-load horoscope chart in detail sheet via /window-detail"
```

---

## Task 6: Deploy and verify

- [ ] **Step 1: Push all commits to master**

```bash
git push origin master
```

Expected: GitHub Actions triggers two workflows — Pages (frontend) and SAM (backend).

- [ ] **Step 2: Confirm both workflows complete successfully**

```bash
gh run list --repo sairamchinta1510/telugu-panchang --limit 5
```

Wait for both runs to show `completed`. On failure:

```bash
gh run view <run-id> --log | tail -50
```

- [ ] **Step 3: Smoke-test the new endpoint**

```bash
curl -s -X POST https://h3dp7amvn9.execute-api.ap-south-1.amazonaws.com/muhoortam/window-detail \
  -H "Content-Type: application/json" \
  -d '{"ceremony_place":"Hyderabad, India","date":"15/07/2026"}' | python3 -m json.tool
```

Expected: JSON with `planet_rashis` containing all 9 graha keys, each an integer 0–11.

- [ ] **Step 4: Smoke-test `/muhoortam/find` for speed**

```bash
time curl -s -X POST https://h3dp7amvn9.execute-api.ap-south-1.amazonaws.com/muhoortam/find \
  -H "Content-Type: application/json" \
  -d '{"year":2026,"month":7,"ceremony_type":"vivaha","ceremony_place":"Hyderabad, India","birth_charts":[{"janma_nakshatra_idx":3,"janma_rashi_idx":1}]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
has_pr = any('planet_rashis' in w for r in d.get('results',[]) for w in r.get('good_windows',[]))
print(f'count={d[\"count\"]}, planet_rashis in windows: {has_pr}')
"
```

Expected: response time < 8 s (warm) / < 15 s (cold start); `planet_rashis in windows: False`.

- [ ] **Step 5: Test live UI**

Open `https://muhoortam.sanatanadharmas.com`, select Vivaha, enter Hyderabad, set July 2026 date range, enter one birth chart, click Find:
- Results appear within 3–8 s ✓
- Tap a result card → detail sheet opens, shows "⏳ లోడ్ అవుతున్నాయి..." then renders horoscope ✓
- Second tap on same card renders horoscope instantly (cached) ✓
