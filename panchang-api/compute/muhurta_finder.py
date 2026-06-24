"""
Month scanner for auspicious muhurta dates — South Indian Telugu tradition.
Iterates every calendar day, computes panchang at sunrise,
and returns days that pass all auspiciousness checks including
Masa Shuddhi (Chaturmas), Tara Balam, and Panchaka Dosha.
Includes Rahu Kalam, Yamaganda, and Gulika Kalam in output (essential South Indian exclusion periods).
"""
from __future__ import annotations
import bisect
import calendar
import datetime as _dt

try:
    from .astro import (
        local_date_to_jd, local_datetime_to_jd, get_sunrise_sunset,
        jd_to_local_datetime, moon_longitude, moon_sun_elongation,
        find_next_index_change, compute_planet_rashis, sun_longitude,
    )
except ImportError:
    from .astro import (
        local_date_to_jd, get_sunrise_sunset,
        jd_to_local_datetime, moon_longitude, moon_sun_elongation,
        find_next_index_change, compute_planet_rashis,
    )

    def sun_longitude(jd: float) -> float:
        return 0.0

    def local_datetime_to_jd(year: int, month: int, day: int,   # type: ignore[misc]
                              hour: int, minute: int, tz_name: str) -> float:
        """Pure-Python fallback (no swisseph) used when astro is mocked in tests."""
        import pytz
        from datetime import datetime as _datetime
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(_datetime(year, month, day, hour, minute, 0))
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.timestamp() / 86400.0 + 2440587.5
from .panchang import compute_panchang, NAKSHATRA_TE, TITHI_TE
try:
    from .panchang import YOGA_TE
except ImportError:
    YOGA_TE = [""] * 27
try:
    from .panchang import VAARAM_TE as _VAARAM_TE
except ImportError:
    _VAARAM_TE = ["ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం", "గురువారం", "శుక్రవారం", "శనివారం"]
from .birth_chart import compute_lagna, RASHI_TE
from .muhurta_rules import (
    is_auspicious, compute_kalams, compute_choghadiya_slots,
    _masam_ok, _GOOD_NAKSHATRAS, _BAD_TITHIS, _BAD_VAARAS, _PRAYANAM_VAARA_VEDHA,
    _tara_ok, _rashi_shuddhi_ok, _panchaka_ok,
    _RASHI_SHUDDHI_FORBIDDEN, _SUDHI_NAME_TE,
)

_MONTH_TE = [
    "జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్",
    "జులై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్",
]

_CEREMONY_TE = {
    "vivaha":         "వివాహం",
    "gruha_pravesam": "గృహ ప్రవేశం",
    "upanayanam":     "ఉపనయనం",
    "pooja":          "పూజ",
    "yuddham":        "యుద్ధం",
    "anna_prasana":   "అన్నప్రాశన",
    "chelamu":        "చెలము",
    "kotta_battalu":  "కొత్త బట్టలు",
    "prayanam":       "ప్రయాణం",
    "vidyarambham":   "విద్యారంభం",
    "oshadha_seva":   "ఔషధ సేవ",
    "namakaranam":    "నామకరణం",
    "garbhadanam":    "గర్భాదానం",
    "sankhu_stapana": "శంకుస్థాపన",
}


def _lookup_at_jd(transitions: list[dict], jd: float) -> int:
    """Binary search for the active index at given jd in a sorted transitions list."""
    jds = [t["jd"] for t in transitions]
    pos = bisect.bisect_right(jds, jd) - 1
    return transitions[max(0, pos)]["idx"]


def _segments_from_cache(day_cache: dict, rise_jd: float, end_jd: float) -> list[tuple]:
    """Build time segments by merging all precomputed transition breakpoints."""
    breakpoints = set()
    for key in ("lagna_transitions", "nak_transitions", "tithi_transitions"):
        for t in day_cache.get(key, []):
            jd = t["jd"]
            if rise_jd < jd < end_jd:
                breakpoints.add(jd)
    sorted_pts = sorted(breakpoints)
    all_pts = [rise_jd] + sorted_pts + [end_jd]
    return [(all_pts[i], all_pts[i + 1]) for i in range(len(all_pts) - 1)]


def _find_good_windows_from_cache(
    day_cache: dict,
    rise_jd: float,
    set_jd: float,
    tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    masam_name: str,
    is_adhika: bool,
    sun_idx: int,
    is_uttarayanam: bool = True,
    skip_planet_rashis: bool = False,
) -> list[dict]:
    """Cached path: use precomputed transitions instead of live swisseph calls."""
    EPSILON = 1.0 / (24 * 60)
    end_jd = rise_jd + 1.0

    cho_slots = compute_choghadiya_slots(rise_jd, set_jd, end_jd, sun_idx)
    lagna_trans = day_cache.get("lagna_transitions", [])
    nak_trans = day_cache.get("nak_transitions", [])
    tithi_trans = day_cache.get("tithi_transitions", [])

    segments = _segments_from_cache(day_cache, rise_jd, end_jd)
    good_windows: list[dict] = []

    for seg_start, seg_end in segments:
        if seg_end - seg_start < EPSILON:
            continue

        naks_idx = _lookup_at_jd(nak_trans, seg_start)
        tithi_idx = _lookup_at_jd(tithi_trans, seg_start)
        win_lagna_idx = _lookup_at_jd(lagna_trans, seg_start)
        day_rashi_idx = day_cache.get(
            "day_rashi_idx",
            int(naks_idx * (360.0 / 27) / 30) % 12,
        )

        good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, win_lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
            is_uttarayanam=is_uttarayanam,
        )

        if good:
            from_str = jd_to_local_datetime(seg_start, tz_name).strftime("%H:%M")
            to_str = jd_to_local_datetime(seg_end, tz_name).strftime("%H:%M")
            h_from, m_from = map(int, from_str.split(":"))
            h_to, m_to = map(int, to_str.split(":"))
            total_from = h_from * 60 + m_from
            total_to = h_to * 60 + m_to
            if total_to <= total_from:
                total_to += 24 * 60

            best_cho_rank = -1
            best_cho_te = ""
            best_time_str = from_str
            for slot in cho_slots:
                overlap_start = max(slot["from_jd"], seg_start)
                overlap_end = min(slot["to_jd"], seg_end)
                if overlap_end - overlap_start < EPSILON:
                    continue
                if slot["quality_rank"] > best_cho_rank:
                    best_cho_rank = slot["quality_rank"]
                    best_cho_te = slot["quality_te"]
                    best_time_str = jd_to_local_datetime(
                        max(slot["from_jd"], seg_start), tz_name
                    ).strftime("%H:%M")

            entry = {
                "from": from_str,
                "to": to_str,
                "duration_mins": total_to - total_from,
                "nakshatra_te": NAKSHATRA_TE[naks_idx],
                "tithi_te": TITHI_TE[tithi_idx],
                "lagna_te": RASHI_TE[win_lagna_idx],
                "nak_idx": naks_idx,
                "tithi_idx": tithi_idx,
                "sun_idx": sun_idx,
                "lagna_idx": win_lagna_idx,
                "best_time": best_time_str,
                "choghadiya_te": best_cho_te,
                "choghadiya_rank": best_cho_rank,
            }
            if not skip_planet_rashis:
                entry["planet_rashis"] = day_cache.get("planet_rashis", {})
            good_windows.append(entry)

    good_windows.sort(key=lambda w: (w["choghadiya_rank"], w["duration_mins"]), reverse=True)
    return good_windows


def _find_good_windows(
    rise_jd: float,
    set_jd: float,
    lat: float, lon: float, tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    masam_name: str,
    is_adhika: bool,
    sun_idx: int,
    lagna_idx: int,   # kept for API compat; actual per-window lagna is recomputed
    is_uttarayanam: bool = True,
    skip_planet_rashis: bool = False,
    day_cache: dict | None = None,
) -> list[dict]:
    """Scan the full 24 hours from rise_jd for auspicious muhurta windows.

    Tithi, nakshatra, AND lagna change during the day; each segment between
    transitions is evaluated independently with the actual lagna at that time.
    Within each good segment the best Choghadiya slot is identified to give
    the exact recommended start time.

    Returns list of dicts sorted best-first (highest Choghadiya rank, then longest).
    Each dict: {from, to, duration_mins, nakshatra_te, tithi_te, lagna_te,
                nak_idx, tithi_idx, sun_idx, best_time, choghadiya_te,
                choghadiya_rank}
    """
    def _ti(j): return int(moon_sun_elongation(j) / 12) % 30
    def _ni(j): return int(moon_longitude(j) / (360.0 / 27)) % 27
    def _li(j): return compute_lagna(j, lat, lon)

    EPSILON = 1.0 / (24 * 60)   # 1 minute in JD
    end_jd  = rise_jd + 1.0     # exactly 24 hours

    if day_cache is not None:
        return _find_good_windows_from_cache(
            day_cache, rise_jd, set_jd, tz_name,
            ceremony_type, birth_charts, masam_name, is_adhika,
            sun_idx, is_uttarayanam, skip_planet_rashis,
        )

    # Pre-compute Choghadiya slots for the full day/night
    cho_slots = compute_choghadiya_slots(rise_jd, set_jd, end_jd, sun_idx)

    good_windows: list[dict] = []
    jd = rise_jd

    while jd < end_jd - EPSILON:
        ml    = moon_longitude(jd)
        elong = moon_sun_elongation(jd)
        naks_idx      = int(ml / (360.0 / 27)) % 27
        tithi_idx     = int(elong / 12) % 30
        day_rashi_idx = int(ml / 30) % 12
        win_lagna_idx = compute_lagna(jd, lat, lon)

        t_change = find_next_index_change(jd, _ti, tithi_idx, step_hours=1.0, max_hours=26)
        n_change = find_next_index_change(jd, _ni, naks_idx,  step_hours=1.0, max_hours=26)
        l_change = find_next_index_change(jd, _li, win_lagna_idx, step_hours=0.25, max_hours=3)

        candidates = [c for c in [t_change, n_change, l_change] if c is not None and c < end_jd]
        window_end_jd = min(candidates) if candidates else end_jd

        good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, win_lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
            is_uttarayanam=is_uttarayanam,
        )

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

        jd = max(window_end_jd, jd + EPSILON) + EPSILON
        if jd >= end_jd:
            break

    # Sort: best Choghadiya first, then longest window
    good_windows.sort(key=lambda w: (w["choghadiya_rank"], w["duration_mins"]), reverse=True)
    return good_windows


def find_muhurtas_for_month(
    year: int,
    month: int,
    lat: float,
    lon: float,
    tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    month_cache: dict | None = None,
) -> list[dict]:
    """Scan every day of the month and return auspicious muhurta days.

    Each result dict contains:
    - Telugu-formatted date, vaaram, tithi, nakshatra, yoga
    - sunrise, sunset times
    - rahu_kalam, yamaganda, gulika_kalam windows (must be avoided during ceremony)
    - dur_muhurtam and varjyam windows (from existing panchang compute)
    """
    results = []
    _, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        try:
            date_key = f"{year}-{month:02d}-{day:02d}"
            dc = month_cache.get(date_key) if month_cache is not None else None

            if dc is not None:
                rise_jd = dc["sunrise_jd"]
                set_jd = dc["sunset_jd"]
                naks_idx = dc["nak_idx"]
                tithi_idx = dc["tithi_idx"]
                sun_idx = dc["sun_idx"]
                lagna_idx = dc["lagna_transitions"][0]["idx"]
                masam_name = dc["masam"]
                is_adhika = dc["is_adhika"]
                day_rashi_idx = dc["day_rashi_idx"]
                is_uttarayanam = dc.get("is_uttarayanam", True)
                dt_rise = jd_to_local_datetime(rise_jd, tz_name)
            else:
                jd = local_date_to_jd(year, month, day, tz_name)
                rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)

                moon_lon = moon_longitude(rise_jd)
                elong = moon_sun_elongation(rise_jd)
                naks_idx = int(moon_lon / (360.0 / 27)) % 27
                tithi_idx = int(elong / 12) % 30
                day_rashi_idx = int(moon_lon / 30) % 12

                dt_rise = jd_to_local_datetime(rise_jd, tz_name)
                sun_idx = (dt_rise.weekday() + 1) % 7   # Sunday=0 … Saturday=6
                lagna_idx = compute_lagna(rise_jd, lat, lon)
                is_uttarayanam = sun_longitude(rise_jd) < 180

                pan = compute_panchang(jd, lat, lon, tz_name)
                masam_name = pan["masam"]["en"]
                is_adhika = pan["masam"]["adhika"]

            good_at_sunrise = is_auspicious(
                naks_idx, tithi_idx, sun_idx, lagna_idx,
                birth_charts, ceremony_type,
                masam_name=masam_name, is_adhika_masam=is_adhika,
                day_rashi_idx=day_rashi_idx,
                is_uttarayanam=is_uttarayanam,
            )

            # Always compute specific muhurtam windows so the UI can show a best
            # time (Choghadiya rank). The nakshatra pre-filter only applies when
            # the day already failed the sunrise check — good-at-sunrise days
            # proceed directly to window scanning.
            if not good_at_sunrise:
                # Pre-filter: if the same bad nakshatra spans the full 24 h, no
                # good window transition can exist — skip the expensive scan.
                good_naks = _GOOD_NAKSHATRAS.get(ceremony_type, set())
                if naks_idx not in good_naks:
                    if dc is not None:
                        nak_transitions = dc.get("nak_transitions", [])
                        if len(nak_transitions) == 1 and nak_transitions[0]["idx"] == naks_idx:
                            continue  # single bad nakshatra covers full 24 h — skip
                    else:
                        naks_idx_end = int(moon_longitude(rise_jd + 1.0) / (360.0 / 27)) % 27
                        if naks_idx_end not in good_naks and naks_idx_end == naks_idx:
                            continue  # single bad nakshatra covers full 24 h — skip

            good_windows = _find_good_windows(
                rise_jd, set_jd, lat, lon, tz_name,
                ceremony_type, birth_charts, masam_name, is_adhika,
                sun_idx, lagna_idx,
                is_uttarayanam=is_uttarayanam,
                skip_planet_rashis=True,
                day_cache=dc,
            )
            if not good_at_sunrise and not good_windows:
                continue   # truly bad all day

            if dc is not None:
                sunrise = dc["sunrise"]
                sunset = dc["sunset"]
                rise_h, rise_m = map(int, sunrise.split(":"))
                set_h, set_m = map(int, sunset.split(":"))
                rise_mins = rise_h * 60 + rise_m
                set_mins = set_h * 60 + set_m
                kalams = {
                    "rahu_kalam": dc["rahu_kalam"],
                    "yamaganda": dc["yamaganda"],
                    "gulika_kalam": dc["gulika_kalam"],
                }
                vaaram_te = _VAARAM_TE[sun_idx]
                tithi_te = TITHI_TE[tithi_idx]
                nakshatra_te = NAKSHATRA_TE[naks_idx]
                yoga_te = YOGA_TE[dc["yoga_idx"]]
                dur_muhurtam = dc["dur_muhurtam"]
                varjyam = dc["varjyam"]
            else:
                dt_set = jd_to_local_datetime(set_jd, tz_name)
                sunrise = dt_rise.strftime("%H:%M")
                sunset = dt_set.strftime("%H:%M")
                rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
                set_mins = dt_set.hour * 60 + dt_set.minute + dt_set.second / 60
                kalams = compute_kalams(rise_mins, set_mins, sun_idx)
                vaaram_te = pan["vaaram"]["te"]
                tithi_te = pan["tithi"]["te"]
                nakshatra_te = pan["nakshatra"]["te"]
                yoga_te = pan["yoga"]["te"]
                dur_muhurtam = pan["dur_muhurtam"]
                varjyam = pan["varjyam"]

            results.append({
                "date_te":             f"{day} {_MONTH_TE[month - 1]} {year}",
                "date_raw":            f"{day:02d}/{month:02d}/{year}",
                "vaaram_te":           vaaram_te,
                "gregorian_vaaram_te": _VAARAM_TE[(_dt.date(year, month, day).weekday() + 1) % 7],
                "sunrise":             sunrise,
                "sunset":       sunset,
                "tithi_te":     tithi_te,
                "nakshatra_te": nakshatra_te,
                "yoga_te":      yoga_te,
                "rahu_kalam":   kalams["rahu_kalam"],
                "yamaganda":    kalams["yamaganda"],
                "gulika_kalam": kalams["gulika_kalam"],
                "dur_muhurtam": dur_muhurtam,
                "varjyam":      varjyam,
                "good_from":    good_windows[0]["from"] if good_windows else None,
                "good_windows": good_windows,
            })
        except Exception:
            continue   # skip days where calculation fails (polar extremes, etc.)

    return results


def check_muhurta_day(
    year: int, month: int, day: int,
    lat: float, lon: float, tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    check_hour: int = -1,
    check_minute: int = 0,
) -> dict:
    """Check a specific date (and optional time) for muhurta auspiciousness.

    Returns a detailed breakdown of good/bad factors, panchang info,
    and an overall verdict of 'good', 'mixed', or 'bad'.

    check_hour=-1 means no specific time was requested (day-level check only).
    """
    jd = local_date_to_jd(year, month, day, tz_name)
    rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)

    moon_lon      = moon_longitude(rise_jd)
    elong         = moon_sun_elongation(rise_jd)
    naks_idx      = int(moon_lon / (360.0 / 27)) % 27
    tithi_idx     = int(elong / 12) % 30
    day_rashi_idx = int(moon_lon / 30) % 12

    dt_rise   = jd_to_local_datetime(rise_jd, tz_name)
    dt_set    = jd_to_local_datetime(set_jd, tz_name)
    sun_idx   = (dt_rise.weekday() + 1) % 7

    lagna_idx = compute_lagna(rise_jd, lat, lon)
    pan       = compute_panchang(jd, lat, lon, tz_name)
    masam_name = pan["masam"]["en"]
    is_adhika  = pan["masam"]["adhika"]
    is_uttarayanam = sun_longitude(rise_jd) < 180

    # When a specific time is requested, recompute all astro values at that
    # exact moment so that nakshatra/tithi/yoga/lagna reflect the actual sky
    # at the ceremony time (not at sunrise, which may differ after transitions).
    check_jd: float | None = None
    if check_hour >= 0:
        check_jd      = local_datetime_to_jd(year, month, day, check_hour, check_minute, tz_name)
        moon_lon      = moon_longitude(check_jd)
        elong         = moon_sun_elongation(check_jd)
        naks_idx      = int(moon_lon / (360.0 / 27)) % 27
        tithi_idx     = int(elong / 12) % 30
        day_rashi_idx = int(moon_lon / 30) % 12
        lagna_idx     = compute_lagna(check_jd, lat, lon)

    # Yoga at the evaluation time (sunrise when no time given, check time otherwise)
    _eval_jd = check_jd if check_jd is not None else rise_jd
    _sun_lon_eval = sun_longitude(_eval_jd)
    _moon_lon_eval = moon_longitude(_eval_jd) if check_jd is not None else moon_lon
    yoga_idx  = int((_sun_lon_eval + _moon_lon_eval) / (360.0 / 27)) % 27
    yoga_te   = YOGA_TE[yoga_idx] if yoga_idx < len(YOGA_TE) else pan["yoga"]["te"]

    # Display names: use check-time values when a time is given
    nakshatra_te_display = NAKSHATRA_TE[naks_idx]
    tithi_te_display     = TITHI_TE[tithi_idx]

    rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
    set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60
    kalams    = compute_kalams(rise_mins, set_mins, sun_idx)

    cer_te = _CEREMONY_TE.get(ceremony_type, ceremony_type)
    good_factors: list[dict] = []
    bad_factors:  list[dict] = []

    def _good(te: str, rule_en: str, source_en: str) -> dict:
        return {"te": te, "rule_en": rule_en, "source_en": source_en}

    def _bad(te: str, rule_en: str, source_en: str) -> dict:
        return {"te": te, "rule_en": rule_en, "source_en": source_en}

    # 0. Ayanam check (only for Uttarayanam-only ceremonies)
    if ceremony_type in ("upanayanam",):
        ayanam_name = pan["ayanam"]["te"]
        _ayanam_src = (
            "Muhurta Chintamani, Samskara Prakarana (Upanayana section): "
            "'दक्षिणायने व्रतवन्धनिषेधात् उत्तरायणे ... प्रशस्तम्' "
            "(Since thread-ceremony is forbidden in Dakshinayana, Uttarayana is commendable). "
            "Verified: Archive.org muhurta-chintamani-kedar-datt-joshi_202501"
        )
        if is_uttarayanam:
            good_factors.append(_good(
                f"అయనం: {ayanam_name} — {cer_te}కు శుభ అయనం ✓",
                "Ayanam Shuddhi",
                _ayanam_src,
            ))
        else:
            bad_factors.append(_bad(
                f"అయనం: {ayanam_name} — {cer_te}కు కేవలం ఉత్తరాయణంలో మాత్రమే చేయాలి",
                "Ayanam Shuddhi",
                _ayanam_src,
            ))

    # 1. Masa Shuddhi
    _masa_src = (
        "Dharmasindhu (Kashinath Upadhyaya, 1790) §Chaturmasya — "
        "Ashadha–Ashvina forbidden for major samskaras during Vishnu's sleep. "
        "Adhika masa forbidden for all samskaras. "
        "Note: Exact shloka not yet verified from digitised text"
    )
    if masam_name and not _masam_ok(masam_name, is_adhika, ceremony_type):
        label = "అధిక మాసం" if is_adhika else pan["masam"]["te"] + " మాసం"
        bad_factors.append(_bad(
            f"{label} — {cer_te}కు నిషిద్ధ మాసం (చాతుర్మాస్య నియమం)",
            "Masa Shuddhi — Chaturmasya prohibition",
            _masa_src,
        ))
    else:
        good_factors.append(_good(
            f"మాసం: {pan['masam']['te']} — {cer_te}కు అనుకూలం",
            "Masa Shuddhi",
            _masa_src,
        ))

    # 2. Vaara Shuddhi
    vaara_te = pan["vaaram"]["te"]
    _vaara_src = (
        "Muhurta Chintamani, Samskara Prakarana (Upanayana section): "
        "'हित्वा शनिकुजवारौ' (Avoiding Saturday and Tuesday) — Shaangadhari quote in commentary. "
        "Verified: Archive.org muhurta-chintamani-kedar-datt-joshi_202501. "
        "Rules for other ceremonies not yet verified from primary text"
    )
    if sun_idx in _BAD_VAARAS.get(ceremony_type, set()):
        bad_factors.append(_bad(
            f"వారం: {vaara_te} — {cer_te}కు నిషిద్ధ వారం (సూర్య/మంగళ/శని దోషం)",
            "Vaara Shuddhi",
            _vaara_src,
        ))
    else:
        good_factors.append(_good(
            f"వారం: {vaara_te} — {cer_te}కు అనుకూల వారం ✓",
            "Vaara Shuddhi",
            _vaara_src,
        ))

    # 2b. Vara-Nakshatra Vedha (only for Prayanam)
    if ceremony_type == "prayanam":
        vedha_naks = _PRAYANAM_VAARA_VEDHA.get(sun_idx, set())
        _vedha_src = (
            "Muhurta Chintamani, Prayana section — "
            "each weekday's ruling planet afflicts 3 specific nakshatras for travel. "
            "Note: Exact shloka not yet verified from digitised text"
        )
        if naks_idx in vedha_naks:
            bad_factors.append(_bad(
                f"వార-నక్షత్ర వేధ: {pan['nakshatra']['te']} — ఈ {vaara_te}న వేధింపబడిన నక్షత్రం",
                "Vara-Nakshatra Vedha (Prayanam)",
                _vedha_src,
            ))
        else:
            good_factors.append(_good(
                f"వార-నక్షత్ర వేధ: {pan['nakshatra']['te']} — ఈ {vaara_te}న వేధ లేదు ✓",
                "Vara-Nakshatra Vedha (Prayanam)",
                _vedha_src,
            ))

    # 3. Nakshatra
    _naks_src = (
        "Muhurta Chintamani, Samskara Prakarana (Upanayana section): "
        "'क्षिप्रध्रुवाहिचरमूलमृदुत्रिपूर्वारोद्रे ... व्रतं सत्' — "
        "22 nakshatras approved (Kshipra, Dhruva, Ahi, Chara, Mula, Mridu, Tripurva, Ardra groups); "
        "'न चापरां' (not the others — 5 forbidden: Bharani, Krittika, Magha, Jyeshtha, Vishakha). "
        "Verified: Archive.org muhurta-chintamani-kedar-datt-joshi_202501. "
        "Nakshatra lists for other ceremonies not yet verified from primary text"
    )
    if naks_idx in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
        good_factors.append(_good(
            f"నక్షత్రం: {nakshatra_te_display} — {cer_te}కు శుభమైన నక్షత్రం ✓",
            "Nakshatra Shuddhi",
            _naks_src,
        ))
    else:
        bad_factors.append(_bad(
            f"నక్షత్రం: {nakshatra_te_display} — {cer_te}కు అనుకూలమైన నక్షత్రం కాదు",
            "Nakshatra Shuddhi",
            _naks_src,
        ))

    # 4. Tithi
    _tithi_src = (
        "Muhurta Chintamani, Shubhashubha Prakarana, shloka 4: "
        "'रिक्तासु ... यन्मङ्गलं तासु कृतं च मूढैः ... नाशमायाति' "
        "(Whatever auspicious act is done in Rikta tithis comes to ruin). "
        "Commentary defines Rikta = Chaturthi(4), Navami(9), Chaturdashi(14). "
        "Verified: Archive.org muhurta-chintamani-kedar-datt-joshi_202501"
    )
    if tithi_idx in _BAD_TITHIS.get(ceremony_type, set()):
        bad_factors.append(_bad(
            f"తిథి: {tithi_te_display} — నివారించాల్సిన తిథి (రిక్త/దోష తిథి)",
            "Tithi Shuddhi",
            _tithi_src,
        ))
    else:
        good_factors.append(_good(
            f"తిథి: {tithi_te_display} — శుభ తిథి ✓",
            "Tithi Shuddhi",
            _tithi_src,
        ))

    # 5. Tara Balam per person
    _tara_src = (
        "Muhurta Chintamani, Gochar Prakarana, shloka 12: "
        "'जन्माख्यसम्पद्विपदः क्षेमप्रत्यरिसाधकाः वध-मित्र-अतिमित्र' — "
        "9 taras named; commentary: '३।५।७ तारा अनिष्ट हैं' (3rd Vipat, 5th Pratyari, 7th Vadha inauspicious). "
        "1st (Janma) tara also treated as dosha in remedies shloka 13. "
        "Verified: Archive.org muhurta-chintamani-of-daivagya-ramacharya-mahidhar-sharma"
    )
    for i, chart in enumerate(birth_charts):
        name = chart.get("name") or f"వ్యక్తి {i + 1}"
        if _tara_ok(chart["janma_nakshatra_idx"], naks_idx):
            good_factors.append(_good(
                f"{name}: తార బలం అనుకూలం ✓",
                "Tara Balam",
                _tara_src,
            ))
        else:
            bad_factors.append(_bad(
                f"{name}: తార బలం అననుకూలం — జన్మ నక్షత్రానికి వ్యతిరేక తార (1, 3, 5 లేదా 7వ తార)",
                "Tara Balam",
                _tara_src,
            ))

    # 6. Rashi Shuddhi (only ceremonies with restrictions)
    _rashi_src = (
        "Telugu Panchangam (Venkatrama & Co. VTP Rajahmundry) Lagna Shuddhi tables — "
        "Vivaha: avoid 7th rashi (Saptama Shuddhi); "
        "Upanayanam: avoid 8th rashi (Ashtama Shuddhi); "
        "Gruha Pravesam: avoid 12th rashi (Dwadasha Shuddhi). "
        "Note: Physical panchangam not digitally accessible — not yet verified from primary text"
    )
    if day_rashi_idx >= 0 and _RASHI_SHUDDHI_FORBIDDEN.get(ceremony_type):
        for i, chart in enumerate(birth_charts):
            name = chart.get("name") or f"వ్యక్తి {i + 1}"
            jrashi = chart.get("janma_rashi_idx", -1)
            if jrashi >= 0:
                if _rashi_shuddhi_ok(day_rashi_idx, jrashi, ceremony_type):
                    good_factors.append(_good(
                        f"{name}: రాశి శుద్ధి అనుకూలం ✓",
                        "Rashi Shuddhi",
                        _rashi_src,
                    ))
                else:
                    pos = (day_rashi_idx - jrashi) % 12 + 1
                    bad_factors.append(_bad(
                        f"{name}: రాశి శుద్ధి అననుకూలం — చంద్రుడు {pos}వ స్థానంలో ఉన్నాడు",
                        "Rashi Shuddhi",
                        _rashi_src,
                    ))

    # 7. Panchaka Dosha
    _panchaka_src = (
        "South Indian tradition; Venkatrama & Co. VTP daily columns — "
        "formula: (Vara + Tithi + Nakshatra + Lagna) mod 9; "
        "remainders 1,2,4,6,8 = dosha; remainders 0,3,5,7 = safe (Panchaka Rahita). "
        "WARNING: This arithmetic formula was NOT found in Muhurta Chintamani or Dharmasindhu "
        "during text verification. Source is South Indian panchangam tradition — "
        "primary Sanskrit text citation unverified"
    )
    if _panchaka_ok(naks_idx, sun_idx, tithi_idx, lagna_idx):
        good_factors.append(_good(
            "పంచక దోషం లేదు ✓",
            "Panchaka Dosha",
            _panchaka_src,
        ))
    else:
        bad_factors.append(_bad(
            "పంచక దోషం ఉంది — (వారం+తిథి+నక్షత్రం+లగ్నం) % 9 దోష సంఖ్య",
            "Panchaka Dosha",
            _panchaka_src,
        ))

    overall_good = is_auspicious(
        naks_idx, tithi_idx, sun_idx, lagna_idx,
        birth_charts, ceremony_type,
        masam_name=masam_name, is_adhika_masam=is_adhika,
        day_rashi_idx=day_rashi_idx,
        is_uttarayanam=is_uttarayanam,
    )

    good_windows = _find_good_windows(
        rise_jd, set_jd, lat, lon, tz_name,
        ceremony_type, birth_charts, masam_name, is_adhika,
        sun_idx, lagna_idx,
        is_uttarayanam=is_uttarayanam,
    )

    if not overall_good and good_windows:
        windows_str = ", ".join(f"{w['from']}–{w['to']}" for w in good_windows)
        good_factors.append(_good(
            f"పగటిపూట శుభ ముహూర్త సమయాలు: {windows_str} ✓",
            "Good Muhurta Windows",
            "Lagna transitions, Choghadiya, Rahu Kalam exclusion — "
            "Muhurta Chintamani §Choghadiya; South Indian kalam rules (VTP)",
        ))

    # ── Time analysis ────────────────────────────────────────────────────────────
    def _in_window(w: dict, mins: float) -> bool:
        if not w:
            return False
        sh, sm = map(int, w["start"].split(":"))
        eh, em = map(int, w["end"].split(":"))
        return (sh * 60 + sm) <= mins <= (eh * 60 + em)

    time_verdict: str | None = None
    time_issues: list[str] = []

    if check_hour >= 0:
        check_mins = check_hour * 60 + check_minute
        time_bad = False

        if _in_window(kalams["rahu_kalam"], check_mins):
            time_issues.append(
                f"రాహు కాలం ({kalams['rahu_kalam']['start']}–{kalams['rahu_kalam']['end']})లో ఉంది"
            )
            time_bad = True
        if _in_window(kalams["yamaganda"], check_mins):
            time_issues.append(
                f"యమగండ కాలం ({kalams['yamaganda']['start']}–{kalams['yamaganda']['end']})లో ఉంది"
            )
            time_bad = True
        if _in_window(kalams["gulika_kalam"], check_mins):
            time_issues.append(
                f"గులిక కాలం ({kalams['gulika_kalam']['start']}–{kalams['gulika_kalam']['end']})లో ఉంది"
            )
            time_bad = True
        for v in ([pan.get("varjyam")] if isinstance(pan.get("varjyam"), dict) else (pan.get("varjyam") or [])):
            if _in_window(v, check_mins):
                time_issues.append(f"వర్జ్యం ({v['start']}–{v['end']})లో ఉంది")
                time_bad = True
        for d in ([pan.get("dur_muhurtam")] if isinstance(pan.get("dur_muhurtam"), dict) else (pan.get("dur_muhurtam") or [])):
            if _in_window(d, check_mins):
                time_issues.append(f"దుర్ముహూర్తం ({d['start']}–{d['end']})లో ఉంది")
                time_bad = True

        # Check if the requested time falls within any good muhurta window
        def _in_good_window(mins: float) -> bool:
            if not good_windows:
                # No windows found: use overall_good (good all day if True)
                return overall_good
            for w in good_windows:
                sh, sm = map(int, w["from"].split(":"))
                eh, em = map(int, w["to"].split(":"))
                if (sh * 60 + sm) <= mins <= (eh * 60 + em):
                    return True
            return False

        in_good = _in_good_window(check_mins)

        if time_bad:
            time_verdict = "bad"
        elif in_good:
            time_verdict = "good"
        else:
            time_verdict = "outside"   # not in kalam but not in a good muhurta window either

    # Overall verdict
    day_has_good_window = overall_good or bool(good_windows)

    if day_has_good_window and time_verdict in (None, "good"):
        verdict = "good"
    elif day_has_good_window and time_verdict in ("bad", "outside"):
        verdict = "mixed"
    else:
        verdict = "bad"

    return {
        "verdict":              verdict,
        "overall_day_good":     overall_good or bool(good_windows),
        "time_verdict":         time_verdict,
        "date_te":              f"{day} {_MONTH_TE[month - 1]} {year}",
        "vaaram_te":            pan["vaaram"]["te"],
        "gregorian_vaaram_te":  _VAARAM_TE[(_dt.date(year, month, day).weekday() + 1) % 7],
        "tithi_te":         tithi_te_display,
        "nakshatra_te":     nakshatra_te_display,
        "yoga_te":          yoga_te,
        "masam_te":         pan["masam"]["te"],
        "sudhi_name_te":    _SUDHI_NAME_TE.get(ceremony_type, ""),
        "sunrise":          dt_rise.strftime("%H:%M"),
        "sunset":           dt_set.strftime("%H:%M"),
        "good_factors":     good_factors,
        "bad_factors":      bad_factors,
        "time_issues":      time_issues,
        "rahu_kalam":       kalams["rahu_kalam"],
        "yamaganda":        kalams["yamaganda"],
        "gulika_kalam":     kalams["gulika_kalam"],
        "dur_muhurtam":     pan["dur_muhurtam"],
        "varjyam":          pan["varjyam"],
        "good_windows":     good_windows,
    }
