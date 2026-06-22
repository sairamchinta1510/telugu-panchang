"""Tests for new Muhoortam modules: birth_chart, muhurta_rules, muhurta_finder, handler."""
import sys
import json
import types
from unittest.mock import patch, MagicMock
import pytest


# ── Birth chart tests ─────────────────────────────────────────────────────────

def _make_birth_chart_module():
    """Load birth_chart with swisseph mocked."""
    for mod in list(sys.modules):
        if "birth_chart" in mod:
            del sys.modules[mod]

    fake_swe = MagicMock()
    fake_swe.SIDM_LAHIRI = 0
    fake_swe.GREG_CAL = 1
    fake_swe.julday.return_value = 2460000.5
    fake_swe.get_ayanamsa_ut.return_value = 24.0  # ~24° Lahiri ayanamsha
    # swe.houses returns (cusps_tuple, ascmc_tuple); ascmc[0] = tropical ascendant
    fake_swe.houses.return_value = (
        (0.0,) * 13,          # cusps (unused)
        (54.0,) + (0.0,) * 9  # ascmc[0] = 54° tropical → 54-24 = 30° sidereal → Vrishabha (idx=1)
    )
    sys.modules["swisseph"] = fake_swe

    fake_astro = types.ModuleType("compute.astro")
    # moon at 54.67° sidereal → nakshatra idx = int(54.67 / 13.333) = 4 (Mrigashira)
    # rashi idx = int(54.67 / 30) = 1 (Vrishabha)
    fake_astro.moon_longitude = lambda jd: 54.67
    sys.modules["compute.astro"] = fake_astro

    # Ensure NAKSHATRA_TE on the panchang mock is a real list so birth_chart works
    _NAKSHATRA_TE = [
        "అశ్వని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర",
        "ఆర్ద్ర", "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఘ",
        "పూర్వ ఫల్గుని", "ఉత్తర ఫల్గుని", "హస్త", "చిత్ర", "స్వాతి",
        "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ",
        "ఉత్తరాషాఢ", "శ్రావణ", "ధనిష్ఠ", "శతభిష",
        "పూర్వభాద్ర", "ఉత్తరభాద్ర", "రేవతి",
    ]
    if "compute.panchang" not in sys.modules or not isinstance(
            getattr(sys.modules["compute.panchang"], "NAKSHATRA_TE", None), list):
        from unittest.mock import MagicMock as _MM
        sys.modules["compute.panchang"] = _MM()
    sys.modules["compute.panchang"].NAKSHATRA_TE = _NAKSHATRA_TE

    import importlib
    import compute.birth_chart as bc
    importlib.reload(bc)
    return bc


def test_birth_chart_nakshatra():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["janma_nakshatra_idx"] == 4
    assert result["janma_nakshatra_te"] == "మృగశిర"


def test_birth_chart_rashi():
    bc = _make_birth_chart_module()
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["janma_rashi_idx"] == 1
    assert result["janma_rashi_te"] == "వృషభం"


def test_birth_chart_lagna():
    bc = _make_birth_chart_module()
    # tropical asc=54°, ayanamsha=24° → sidereal=30° → idx=1 (Vrishabha)
    result = bc.compute_birth_chart(1990, 8, 15, 10, 30, 17.38, 78.49, "Asia/Kolkata")
    assert result["lagna_idx"] == 1
    assert result["lagna_te"] == "వృషభం"


# ── Muhurta rules tests ───────────────────────────────────────────────────────

# Clear any cached module so we get a fresh import
for mod in list(sys.modules):
    if "muhurta_rules" in mod:
        del sys.modules[mod]

from compute.muhurta_rules import is_auspicious, _tara_ok, _panchaka_ok, _rashi_shuddhi_ok


def test_tara_ok_good():
    # Janma=3 (Rohini), day=9 (Magha): tara = (9-3)%27+1 = 7 → INAUSPICIOUS
    assert _tara_ok(3, 9) is False


def test_tara_ok_bad_same():
    # Janma=5, day=5: tara=1 (Janma) → inauspicious
    assert _tara_ok(5, 5) is False


def test_tara_ok_safe():
    # Janma=3, day=5: tara=(5-3)%27+1=3 → inauspicious
    assert _tara_ok(3, 5) is False


def test_tara_ok_position_2():
    # Janma=3, day=4: tara=(4-3)%27+1=2 → auspicious
    assert _tara_ok(3, 4) is True


def test_panchaka_ok_inauspicious():
    # nak=0→1, sun=0(Sun)→1, tithi=0→1, lagna=0→1; 1+1+1+1=4 → 4%9=4 → Dosha (4 ∈ {1,2,4,6,8})
    assert _panchaka_ok(0, 0, 0, 0) is False


def test_panchaka_ok_safe():
    # nak=3→4, sun=4(Thu)→5, tithi=0→1, lagna=3→4; 4+5+1+4=14 → 14%9=5 → SAFE (5 ∈ {0,3,5,7})
    assert _panchaka_ok(3, 4, 0, 3) is True


def test_pushya_excluded_from_vivaha():
    # Pushya (idx=7) must be excluded from Vivaha in Telugu tradition
    birth_charts = [{"janma_nakshatra_idx": 0}]
    assert is_auspicious(7, 4, 4, 0, birth_charts, "vivaha") is False


def test_pushya_allowed_for_upanayanam():
    # Pushya (idx=7) is excellent for Upanayanam — must NOT be rejected
    # nak=7→8, sun=4→5, tithi=1→2, lagna=0→1; 8+5+2+1=16 → 16%9=7 → SAFE
    # tara: janma=0, day=7: (7-0)%27+1=8 → safe
    birth_charts = [{"janma_nakshatra_idx": 0}]
    assert is_auspicious(7, 1, 4, 0, birth_charts, "upanayanam") is True


def test_is_auspicious_vivaha_good_day():
    # naks=3 (Rohini - good), tithi=0 (Prathama - safe), sun=4 (Thursday), lagna=3 (Vrishchika)
    # tara: janma=0 (Ashvini), day=3: tara=(3-0)%27+1=4 → safe
    # panchaka: nak=3→4, sun=4→5, tithi=0→1, lagna=3→4; 4+5+1+4=14 → 14%9=5 → SAFE
    birth_charts = [{"janma_nakshatra_idx": 0}]
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha") is True


def test_is_auspicious_rejects_bad_nakshatra():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # naks=0 (Ashvini) - not in vivaha good list
    assert is_auspicious(0, 4, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_rikta_tithi():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # tithi=3 (Shukla Chaturthi, idx=3) — Rikta tithi, bad for vivaha
    assert is_auspicious(3, 3, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_bad_tara():
    # person janma=3 (Rohini), day naks=3 → tara=1 (Janma) → bad
    birth_charts = [{"janma_nakshatra_idx": 3}]
    assert is_auspicious(3, 4, 4, 0, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_panchaka():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # nak=3→4, sun=0(Sun)→1, tithi=0→1, lagna=3→4; 4+1+1+4=10 → 10%9=1 → Mrityu Panchaka!
    assert is_auspicious(3, 0, 0, 3, birth_charts, "vivaha") is False


def test_is_auspicious_rejects_adhika_masam():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # Adhika masa → rejected regardless of nakshatra/tithi
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha",
                         masam_name="Jyeshtha", is_adhika_masam=True) is False


def test_is_auspicious_rejects_chaturmas():
    birth_charts = [{"janma_nakshatra_idx": 0}]
    # Shravana month → rejected for vivaha (Chaturmas)
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha",
                         masam_name="Shravana", is_adhika_masam=False) is False


# ── Rashi Shuddhi tests (Image 1 — Lagna Shuddhi) ───────────────────────────

def test_rashi_shuddhi_saptama_forbidden_vivaha():
    # day_rashi=6 (Tula), janma_rashi=0 (Mesha): pos=6 → 7th = Saptama → forbidden for Vivaha
    assert _rashi_shuddhi_ok(6, 0, "vivaha") is False


def test_rashi_shuddhi_safe_position_vivaha():
    # day_rashi=3 (Kataka), janma_rashi=0: pos=3 → 4th = Kshema → allowed for Vivaha
    assert _rashi_shuddhi_ok(3, 0, "vivaha") is True


def test_rashi_shuddhi_ashtama_forbidden_upanayanam():
    # day_rashi=7 (Vrischika), janma_rashi=0 (Mesha): pos=7 → 8th = Ashtama → forbidden for Upanayanam
    assert _rashi_shuddhi_ok(7, 0, "upanayanam") is False


def test_rashi_shuddhi_saptama_allowed_upanayanam():
    # 7th (Saptama) is only forbidden for Vivaha, not Upanayanam
    assert _rashi_shuddhi_ok(6, 0, "upanayanam") is True


def test_rashi_shuddhi_wrap_around():
    # janma_rashi=10 (Kumbha), day_rashi=4 (Simha): pos=(4-10)%12=6 → 7th → forbidden for Vivaha
    assert _rashi_shuddhi_ok(4, 10, "vivaha") is False


def test_is_auspicious_vivaha_rejects_saptama_rashi():
    # Same-day values that pass all other checks, but day_rashi is 7th from janma_rashi → rejected
    birth_charts = [{"janma_nakshatra_idx": 0, "janma_rashi_idx": 0}]
    # naks=3 (Rohini ✓), tithi=0 (Prathama ✓), sun=4 (Thu), lagna=3, tara=(3-0)%27+1=4 ✓
    # panchaka would pass, but rashi shuddhi (pos=6 → Saptama) → rejected
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha", day_rashi_idx=6) is False


def test_is_auspicious_upanayanam_rejects_ashtama_rashi():
    # Pushya day (naks=7, excellent for Upanayanam) but Moon in 8th rashi → rejected
    birth_charts = [{"janma_nakshatra_idx": 0, "janma_rashi_idx": 0}]
    # naks=7 (Pushya ✓), tithi=1 ✓, sun=4, lagna=0, tara=(7-0)%27+1=8 ✓
    # rashi: pos=(7-0)%12=7 → Ashtama → rejected
    assert is_auspicious(7, 1, 4, 0, birth_charts, "upanayanam", day_rashi_idx=7) is False


def test_is_auspicious_rashi_check_skipped_when_day_rashi_missing():
    # day_rashi_idx=-1 (default) → rashi shuddhi check is skipped entirely
    birth_charts = [{"janma_nakshatra_idx": 0, "janma_rashi_idx": 0}]
    # Would fail rashi if day_rashi_idx=6, but no rashi provided → passes
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha") is True


def test_is_auspicious_rashi_check_skipped_when_no_rashi_in_chart():
    # Chart has no janma_rashi_idx → rashi shuddhi check is skipped for that person
    birth_charts = [{"janma_nakshatra_idx": 0}]
    assert is_auspicious(3, 0, 4, 3, birth_charts, "vivaha", day_rashi_idx=6) is True


# ── Muhurta finder tests ──────────────────────────────────────────────────────

import importlib
import calendar

def _load_finder(days_auspicious: set):
    """Load muhurta_finder with all astronomical functions mocked.

    days_auspicious: set of day-of-month integers that should be marked auspicious.
    All other days return nakshatra=0 (Ashvini, not in vivaha good list) → rejected.
    """
    for mod in list(sys.modules):
        if "muhurta_finder" in mod or "birth_chart" in mod:
            del sys.modules[mod]

    def fake_local_date_to_jd(year, month, day, tz):
        return float(day)  # use day as JD stand-in

    def fake_get_sunrise_sunset(jd, lat, lon):
        # rise_jd = integer JD, set_jd = integer + 0.5 (distinguishable)
        return (jd, jd + 0.5)

    def fake_moon_longitude(jd):
        # Return Rohini (idx=3) for auspicious days: 3 * (360/27) + 1 = ~41°
        day = int(jd)
        return 41.0 if day in days_auspicious else 1.0  # 1° → Ashvini (idx=0)

    def fake_moon_sun_elongation(jd):
        # tithi_idx=0 (Prathama, safe): elong < 12, say 5.0
        # with lagna=3 → panchaka: nak=3→4, sun=4→5, tithi=0→1, lagna=3→4; 14%9=5 → SAFE
        return 5.0

    from datetime import datetime as real_dt
    def fake_jd_to_local_datetime(jd, tz):
        # rise_jd is integer (float(day)), set_jd is integer+0.5
        if jd % 1 != 0:
            return real_dt(2026, 7, 16, 18, 0)   # sunset
        return real_dt(2026, 7, 16, 6, 0)         # sunrise, Thursday → sun_idx=4

    def fake_compute_lagna(jd, lat, lon):
        return 3  # Vrishchika lagna → panchaka safe (see above)

    MOCK_PAN = {
        "vaaram":    {"te": "గురువారం"},
        "tithi":     {"te": "ప్రథమ"},
        "nakshatra": {"te": "రోహిణి"},
        "yoga":      {"te": "సౌభాగ్య"},
        "masam":     {"en": "Jyeshtha", "te": "జ్యేష్ఠ", "adhika": False},
        "dur_muhurtam": [],
        "varjyam":   {"start": "09:00", "end": "10:46"},
    }

    def fake_find_next_index_change(jd_start, index_fn, current_idx, step_hours=1.0, max_hours=26):
        # Return None so _find_good_windows treats the whole 24h as one segment
        return None

    fake_astro = types.ModuleType("compute.astro")
    fake_astro.local_date_to_jd          = fake_local_date_to_jd
    fake_astro.get_sunrise_sunset         = fake_get_sunrise_sunset
    fake_astro.moon_longitude             = fake_moon_longitude
    fake_astro.moon_sun_elongation        = fake_moon_sun_elongation
    fake_astro.jd_to_local_datetime       = fake_jd_to_local_datetime
    fake_astro.find_next_index_change     = fake_find_next_index_change
    fake_astro.compute_planet_rashis      = lambda jd: {
        "ravi": 0, "chandra": 1, "kuja": 2, "budha": 3,
        "guru": 4, "shukra": 5, "shani": 6, "rahu": 7, "ketu": 1
    }
    sys.modules["compute.astro"] = fake_astro

    fake_pan_mod = types.ModuleType("compute.panchang")
    fake_pan_mod.compute_panchang = lambda jd, lat, lon, tz: MOCK_PAN
    fake_pan_mod.NAKSHATRA_TE = ["అశ్వని"] * 27
    fake_pan_mod.TITHI_TE = ["ప్రథమ"] * 30
    fake_pan_mod.VAARAM_TE = ["ఆదివారం"] * 7
    sys.modules["compute.panchang"] = fake_pan_mod

    fake_bc = types.ModuleType("compute.birth_chart")
    fake_bc.compute_lagna = fake_compute_lagna
    fake_bc.RASHI_TE = ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం",
                        "సింహం", "కన్య", "తులం", "వృశ్చికం",
                        "ధనుస్సు", "మకరం", "కుంభం", "మీనం"]
    sys.modules["compute.birth_chart"] = fake_bc

    # muhurta_rules must also be importable
    import compute.muhurta_rules  # real module (no swisseph dependency)
    from compute.muhurta_rules import _SUDHI_NAME_TE
    sys.modules["compute.muhurta_rules"] = compute.muhurta_rules

    import compute.muhurta_finder as mf
    importlib.reload(mf)
    return mf


def test_finder_returns_only_auspicious_days():
    # Days 15 and 22 will have Rohini (naks=3, good for vivaha); all others Ashvini (naks=0, bad)
    mf = _load_finder({15, 22})
    birth_charts = [{"janma_nakshatra_idx": 0}]  # Ashvini janma; tara(0,3)=(3-0)%27+1=4 → ok
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    result_dates = [r["date_te"] for r in results]
    assert "15 జులై 2026" in result_dates
    assert "22 జులై 2026" in result_dates
    assert len(results) == 2


def test_finder_result_has_telugu_fields():
    mf = _load_finder({15})
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    assert len(results) == 1
    r = results[0]
    assert r["vaaram_te"] == "గురువారం"
    assert r["tithi_te"] == "ప్రథమ"
    assert r["nakshatra_te"] == "రోహిణి"
    assert "sunrise" in r
    assert "sunset" in r
    # South Indian kalam periods must be present
    assert "rahu_kalam" in r
    assert "yamaganda" in r
    assert "gulika_kalam" in r
    assert "start" in r["rahu_kalam"]
    assert "end"   in r["rahu_kalam"]


def test_finder_rejects_chaturmas_month():
    """Days in Shravana (core Chaturmas month) must be rejected for Vivaha."""
    mf = _load_finder({15})
    import compute.muhurta_finder as _mf_mod
    _orig = _mf_mod.compute_panchang
    def _shravana_pan(jd, lat, lon, tz):
        p = dict(_orig(jd, lat, lon, tz))
        p["masam"] = {"en": "Shravana", "te": "శ్రావణ", "adhika": False}
        return p
    _mf_mod.compute_panchang = _shravana_pan
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 8, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    _mf_mod.compute_panchang = _orig
    assert len(results) == 0  # Shravana → all days rejected for Vivaha


# ── Handler tests ─────────────────────────────────────────────────────────────

MOCK_GEO = {"lat": 17.38, "lon": 78.49, "tz_name": "Asia/Kolkata"}

MOCK_BIRTH_CHART = {
    "janma_nakshatra_idx": 3,
    "janma_nakshatra_te": "రోహిణి",
    "janma_rashi_idx": 1,
    "janma_rashi_te": "వృషభం",
    "lagna_idx": 1,
    "lagna_te": "వృషభం",
}

MOCK_FIND_RESULTS = [
    {
        "date_te": "15 జులై 2026",
        "vaaram_te": "గురువారం",
        "sunrise": "06:03",
        "sunset": "18:45",
        "tithi_te": "ప్రథమ",
        "nakshatra_te": "రోహిణి",
        "yoga_te": "సౌభాగ్య",
        "rahu_kalam": {"start": "13:30", "end": "15:07"},
        "yamaganda": {"start": "06:03", "end": "07:40"},
        "gulika_kalam": {"start": "09:17", "end": "10:54"},
        "dur_muhurtam": [],
        "varjyam": {"start": "09:00", "end": "10:46"},
    }
]


def _make_handler_event(path: str, body: dict) -> dict:
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps(body),
    }


def _fresh_handler():
    """Return handler_muhoortam with clean compute module state.

    The finder tests leave fake_bc in sys.modules["compute.birth_chart"].
    We must clear it before importing the handler so birth_chart.py is
    imported fresh against the conftest MagicMock for compute.astro/panchang.
    """
    from unittest.mock import MagicMock as _MM
    import importlib
    for mod in list(sys.modules):
        if any(m in mod for m in ("handler_muhoortam", "compute.birth_chart",
                                   "compute.muhurta_finder")):
            del sys.modules[mod]
    sys.modules["compute.astro"]    = _MM()
    sys.modules["compute.panchang"] = _MM()
    import handler_muhoortam
    importlib.reload(handler_muhoortam)
    return handler_muhoortam


def test_handler_birth_chart_ok():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "compute_birth_chart", return_value=MOCK_BIRTH_CHART):
        event = _make_handler_event("/muhoortam/birth-chart", {
            "dob": "15/08/1990", "time": "10:30", "place": "Hyderabad, India"
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["janma_nakshatra_te"] == "రోహిణి"


def test_handler_birth_chart_missing_field():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "compute_birth_chart", return_value=MOCK_BIRTH_CHART):
        event = _make_handler_event("/muhoortam/birth-chart", {"dob": "15/08/1990"})
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_find_ok():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "find_muhurtas_for_month", return_value=MOCK_FIND_RESULTS):
        event = _make_handler_event("/muhoortam/find", {
            "year": 2026, "month": 7,
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
            "birth_charts": [{"janma_nakshatra_idx": 3}],
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["results"][0]["date_te"] == "15 జులై 2026"


def test_handle_find_with_month_cache():
    """_handle_find passes month_cache to find_muhurtas_for_month."""
    h = _fresh_handler()
    mock_cache = {"2026-07-01": {"sunrise_jd": 1.0, "nak_idx": 14}}

    with patch.object(h, "_geocode", return_value={"lat": 17.385, "lon": 78.487, "tz_name": "Asia/Kolkata"}), \
         patch.object(h, "read_month_cache", return_value=mock_cache) as mock_read, \
         patch.object(h, "find_muhurtas_for_month", return_value=[]) as mock_find:
        result = h._handle_find({
            "year": 2026,
            "month": 7,
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad",
            "birth_charts": [{}],
        })

    assert result["statusCode"] == 200
    mock_read.assert_called_once_with(
        2026, 7, pytest.approx(17.385, abs=1), pytest.approx(78.487, abs=1)
    )
    assert mock_find.call_args.kwargs.get("month_cache") == mock_cache


def test_handler_find_bad_month():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "find_muhurtas_for_month", return_value=MOCK_FIND_RESULTS):
        event = _make_handler_event("/muhoortam/find", {
            "year": 2026, "month": 13,
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
            "birth_charts": [{"janma_nakshatra_idx": 3}],
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_unknown_path():
    h = _fresh_handler()
    event = _make_handler_event("/muhoortam/unknown", {})
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 404


# ── check_muhurta_day tests ───────────────────────────────────────────────────

MOCK_CHECK_RESULT_GOOD = {
    "verdict": "good",
    "overall_day_good": True,
    "time_verdict": None,
    "date_te": "15 జులై 2026",
    "vaaram_te": "గురువారం",
    "tithi_te": "ప్రథమ",
    "nakshatra_te": "రోహిణి",
    "yoga_te": "సౌభాగ్య",
    "masam_te": "జ్యేష్ఠ",
    "sunrise": "06:03",
    "sunset": "18:45",
    "good_factors": ["నక్షత్రం: రోహిణి — వివాహంకు శుభమైన నక్షత్రం ✓"],
    "bad_factors": [],
    "time_issues": [],
    "rahu_kalam": {"start": "13:30", "end": "15:07"},
    "yamaganda": {"start": "06:03", "end": "07:40"},
    "gulika_kalam": {"start": "09:17", "end": "10:54"},
    "dur_muhurtam": [],
    "varjyam": [],
}

MOCK_CHECK_RESULT_BAD = dict(MOCK_CHECK_RESULT_GOOD, verdict="bad", overall_day_good=False,
    bad_factors=["నక్షత్రం: అశ్వని — వివాహంకు అనుకూలమైన నక్షత్రం కాదు"],
    good_factors=[])


def test_handler_check_ok():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "check_muhurta_day", return_value=MOCK_CHECK_RESULT_GOOD):
        event = _make_handler_event("/muhoortam/check", {
            "date": "15/07/2026",
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
            "birth_charts": [{"janma_nakshatra_idx": 3, "janma_rashi_idx": 1}],
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["verdict"] == "good"
    assert body["date_te"] == "15 జులై 2026"


def test_handler_check_with_time():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO), \
         patch.object(h, "check_muhurta_day", return_value=MOCK_CHECK_RESULT_GOOD) as mock_check:
        event = _make_handler_event("/muhoortam/check", {
            "date": "15/07/2026",
            "time": "10:30",
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
            "birth_charts": [],
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    # Verify time was parsed and passed as check_hour=10, check_minute=30
    _, kwargs = mock_check.call_args
    assert kwargs.get("check_hour") == 10
    assert kwargs.get("check_minute") == 30


def test_handler_check_missing_field():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/check", {
            "date": "15/07/2026",
            # missing ceremony_type and ceremony_place
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_check_bad_date_format():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/check", {
            "date": "2026-07-15",  # wrong format (should be DD/MM/YYYY)
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_handler_check_bad_time_format():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/check", {
            "date": "15/07/2026",
            "time": "1030",  # wrong format (should be HH:MM)
            "ceremony_type": "vivaha",
            "ceremony_place": "Hyderabad, India",
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


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


def test_handler_window_detail_missing_place():
    h = _fresh_handler()
    with patch.object(h, "_geocode", return_value=MOCK_GEO):
        event = _make_handler_event("/muhoortam/window-detail", {
            "date": "15/07/2026",
        })
        resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_check_muhurta_day_verdict_structure():
    """check_muhurta_day result must contain required keys and valid verdict."""
    mf = _load_finder({15})
    birth_charts = [{"janma_nakshatra_idx": 0, "name": "రాము"}]
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    assert result["verdict"] in ("good", "bad", "mixed")
    assert isinstance(result["good_factors"], list)
    assert isinstance(result["bad_factors"], list)
    assert isinstance(result["time_issues"], list)
    assert "nakshatra_te" in result
    assert "tithi_te" in result
    assert "sunrise" in result


def test_check_muhurta_day_good_nakshatra():
    """Day with Rohini (auspicious for Vivaha) should appear in good_factors."""
    mf = _load_finder({15})
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 0}])
    nak_factors = [f for f in result["good_factors"] if "నక్షత్రం" in f]
    assert nak_factors, "Expected nakshatra good factor"


def test_check_muhurta_day_bad_nakshatra():
    """Day with Ashvini (not in Vivaha list) should appear in bad_factors."""
    mf = _load_finder(set())  # no auspicious days → all days get naks=0 (Ashvini)
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 0}])
    nak_bad = [f for f in result["bad_factors"] if "నక్షత్రం" in f]
    assert nak_bad, "Expected nakshatra bad factor"
    assert result["overall_day_good"] is False


def test_check_muhurta_day_person_name_in_factors():
    """Person name should appear in tara balam factor reason."""
    mf = _load_finder({15})
    # Janma=3 (Rohini), day naks=3 → tara=1 (Janma) → bad tara
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 3, "name": "వేణు"}])
    tara_factors = [f for f in result["bad_factors"] if "వేణు" in f and "తార" in f]
    assert tara_factors, "Expected person name in tara balam factor"


def test_check_muhurta_day_time_in_rahu_kalam():
    """Time within rahu kalam should set time_verdict='bad'."""
    mf = _load_finder({15})
    # Sunrise ~06:00, sunset ~18:00, sun_idx=4 (Thursday) → rahu kalam segment=6
    # rahu = rise + (6-1)*part; part=(12*60)/8=90min → rahu starts at 06:00+450=13:30
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 0}],
                                   check_hour=14, check_minute=0)
    assert result["time_verdict"] == "bad"
    assert any("రాహు" in issue for issue in result["time_issues"])
    # overall_day_good reflects overall_good OR bool(good_windows)
    assert isinstance(result["overall_day_good"], bool)


def test_find_muhurtas_result_has_good_windows_key():
    """Every result from find_muhurtas_for_month must have a good_windows key."""
    mf = _load_finder({15, 22})
    birth_charts = [{"janma_nakshatra_idx": 0}]
    results = mf.find_muhurtas_for_month(2026, 7, 17.38, 78.49, "Asia/Kolkata", "vivaha", birth_charts)
    assert len(results) >= 1
    for r in results:
        assert "good_windows" in r
        assert isinstance(r["good_windows"], list)


def test_check_muhurta_day_returns_good_windows_key():
    """check_muhurta_day response must include a good_windows key."""
    mf = _load_finder({15})
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 0}])
    assert "good_windows" in result
    assert isinstance(result["good_windows"], list)


def test_check_muhurta_day_bad_day_has_good_windows():
    """A bad day (Ashvini, not vivaha-good at sunrise) may still yield good_windows
    if a transition occurs during the day.  With the mock returning a constant
    nakshatra/tithi, good_windows will be empty — but the key must still be present."""
    mf = _load_finder(set())   # all days are auspicious=False at sunrise
    result = mf.check_muhurta_day(2026, 7, 15, 17.38, 78.49, "Asia/Kolkata", "vivaha",
                                   [{"janma_nakshatra_idx": 0}])
    assert "good_windows" in result
    # overall_day_good must be False when no windows found and not good at sunrise
    assert result["overall_day_good"] is False


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
