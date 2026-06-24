# Muhurta Time-Aware Evaluation & Telugu Sampradaya Night Exception

**Date:** 2026-06-24  
**Scope:** `panchang-api/compute/muhurta_finder.py`, `panchang-api/compute/muhurta_rules.py`  
**Status:** Approved

---

## Problem

Two bugs and one missing Telugu tradition rule in `check_muhurta_day`:

1. **Nakshatra, tithi, and lagna are always computed at sunrise**, even when a specific time (e.g. 23:44) is requested. This causes wrong factor evaluations for any time other than sunrise.

2. **Night muhurta windows are never surfaced.** `_find_good_windows` hard-blocks any segment where the vara is bad, so Saturday night windows are never returned — even though Amrita Choghadiya at night can legitimately override vara dosha per Telugu tradition.

3. **Vedic day boundary is approximated** as `rise_jd + 1.0` (24 fixed hours) instead of `rise_jd → next_rise_jd` (actual next sunrise).

---

## Vedic Day Model

The Vedic day (**dina**) runs from **today's sunrise to the next day's sunrise**, not midnight to midnight.

- Civil 23:44 on March 6 → Vedic March 6 (same vara, same panchang day)
- Civil 02:00 on March 7 → still Vedic March 6 (before March 7 sunrise)
- Civil 06:31 on March 7 (after March 7 sunrise) → Vedic March 7

All transition scans and day-boundary checks must use `next_rise_jd` (computed via `get_sunrise_sunset` on the next calendar day), not `rise_jd + 1.0`.

---

## Section 1 — Intraday Transition Tracking

### What changes

**`check_muhurta_day`** currently reads `naks_idx`, `tithi_idx`, `lagna_idx` once at `rise_jd` and never updates them. Fix:

1. Compute `next_rise_jd` (actual next day sunrise).
2. Scan the full Vedic day (`rise_jd → next_rise_jd`) for nakshatra, tithi, and lagna transition breakpoints — reusing the same binary-search approach already used in `_find_good_windows`.
3. Build a **segments list**: each segment has its own `naks_idx`, `tithi_idx`, `lagna_idx`.
4. When `check_hour >= 0`, convert the civil time to a JD within the Vedic day:
   - Times ≥ sunrise hour on the requested date → normal offset from `rise_jd`
   - Early-morning civil times before sunrise on the **next calendar day** (e.g. 02:00 civil Mar 7 for a Vedic Mar 6 request) → also valid, computed as offset from `rise_jd` spanning midnight
5. Find which segment the requested JD falls in; use **that segment's** nakshatra, tithi, lagna for **all factor checks** (nakshatra good/bad, tithi good/bad, Tara Balam, Panchaka, Rashi Shuddhi).
6. Day-level factors (vara, masa, ayanam) remain sunrise-anchored — they don't change intraday.

**`_find_good_windows`** already scans 24 hours but uses `rise_jd + 1.0`. Change `end_jd` to `next_rise_jd` throughout (both the live path and the cached path).

### Transition events in response

The response always includes a `transitions` list covering the full Vedic day:

```json
"transitions": [
  { "type": "nakshatra", "from_te": "చిత్ర",    "to_te": "స్వాతి",   "time": "11:52" },
  { "type": "tithi",     "from_te": "చతుర్థి", "to_te": "పంచమి",    "time": "17:48" }
]
```

Empty list if no transitions occur within the Vedic day.

---

## Section 2 — Telugu Sampradaya Night Vara Exception

### Traditional rule

> When a samskara is performed **at night** (after sunset, before next sunrise) during **Amrita Choghadiya** (rank 6), the vara dosha (Saturday / Sunday / Tuesday) is **mitigated** for all major samskaras. The ceremony may proceed with a **Vara Dosha Shanti puja**.

Source: VTP Rajahmundry panchangam + Muhurta Chintamani tradition. Amrita ("nectar") is the only Choghadiya tier cited in classical sources as sufficient for vara dosha override; Shubha (rank 5) is not.

### Code changes

**`is_auspicious()`** gains two new parameters:
- `is_night: bool = False`
- `choghadiya_rank: int = -1`

Vara check logic:

```python
if sun_idx in _BAD_VAARAS.get(ceremony_type, set()):
    if is_night and choghadiya_rank == 6:
        pass   # Amrita Choghadiya at night — soft warning, not hard block
    else:
        return False
```

This applies to all ceremony types that have vara restrictions (vivaha, gruha_pravesam, upanayanam, anna_prasana, namakaranam, chelamu, vidyarambham, etc.).

**`check_muhurta_day`** — when `check_hour >= 0`:
1. Determine `is_night = check_jd > set_jd` (after today's sunset, within the same Vedic day).
2. Find the Choghadiya slot overlapping `check_jd` from the 16-slot table; read its `quality_rank`.
3. Pass `is_night` and `choghadiya_rank` to all `is_auspicious` calls and to the factor-check block.
4. If vara was overridden by Amrita night exception, add to `bad_factors`:
   > *"వారం: శనివారం — రాత్రి అమృత చోఘడియాలో శాంతి పూజతో నివర్తించవచ్చు ⚠"*

**`_find_good_windows`** (both live and cached paths):
- Per segment, compute `is_night = seg_start > set_jd`.
- Best Choghadiya rank for the segment is already computed; pass it to `is_auspicious`.
- Night segments where vara dosha is overridden by Amrita are included in good windows with `vara_shanti_required: true`.

---

## Section 3 — API Response Shape

### Changed fields

| Field | Before | After |
|---|---|---|
| `nakshatra_te` | Always sunrise nakshatra | Nakshatra at requested time (or sunrise if no time given) |
| `tithi_te` | Always sunrise tithi | Tithi at requested time (or sunrise if no time given) |

### New fields

| Field | Type | Description |
|---|---|---|
| `nakshatra_at_sunrise_te` | string | Nakshatra at sunrise (always present for reference) |
| `tithi_at_sunrise_te` | string | Tithi at sunrise (always present for reference) |
| `transitions` | list | Nakshatra/tithi changes with times during the Vedic day |
| `night_good_windows` | list | Good muhurta windows after sunset (same schema as `good_windows`) |
| `vara_shanti_required` | bool | `true` when vara dosha overridden by Amrita night exception |

`night_good_windows` entries share the same schema as `good_windows` entries, plus an extra `vara_shanti: true` field on entries where the vara exception applies.

Day-level display fields (`vaaram_te`, `masam_te`, `yoga_te`, `sudhi_name_te`) remain sunrise-anchored.

---

## Files Changed

| File | Nature of change |
|---|---|
| `compute/muhurta_rules.py` | Add `is_night`, `choghadiya_rank` params to `is_auspicious()`; add night vara exception logic |
| `compute/muhurta_finder.py` | Fix `check_muhurta_day` transition scan, time-aware segment lookup, night check; fix `_find_good_windows` to use `next_rise_jd`; expose `night_good_windows` in response |

---

## Testing

Existing tests: `tests/test_muhoortam.py`, `tests/test_precompute.py` — must still pass.

Key manual validation:
- March 6 1999 vivaha: nakshatra at 11:44 PM should be **స్వాతి**, tithi **పంచమి**
- March 6 1999 vivaha night: `night_good_windows` should include the 21:25–22:56 Amrita slot
- `vara_shanti_required: true` for that window
- A date with no intraday transitions: `transitions` should be `[]`
- A time before sunrise (e.g. 05:00 input on same civil date) should be treated as belonging to the **previous** Vedic day
