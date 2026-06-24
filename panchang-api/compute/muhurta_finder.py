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

try:
    from .astro import (
        local_date_to_jd, get_sunrise_sunset,
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
    get_anandadi_yoga, _ANANDADI_YOGA_TE,
    get_amritadi_yoga,
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
    next_rise_jd: float = 0.0,
) -> list[dict]:
    """Cached path: use precomputed transitions instead of live swisseph calls."""
    EPSILON = 1.0 / (24 * 60)
    end_jd = next_rise_jd if next_rise_jd > rise_jd else rise_jd + 1.0

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

        is_night_seg = seg_start >= set_jd

        # Compute best choghadiya rank for this segment
        best_cho_rank_seg = -1
        for slot in cho_slots:
            overlap_start = max(slot["from_jd"], seg_start)
            overlap_end = min(slot["to_jd"], seg_end)
            if overlap_end - overlap_start < EPSILON:
                continue
            if slot["quality_rank"] > best_cho_rank_seg:
                best_cho_rank_seg = slot["quality_rank"]

        good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, win_lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
            is_uttarayanam=is_uttarayanam,
            is_night=is_night_seg,
            choghadiya_rank=best_cho_rank_seg,
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

            vara_shanti = (
                sun_idx in _BAD_VAARAS.get(ceremony_type, set())
                and is_night_seg
                and best_cho_rank == 6
            )

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
                "vara_shanti": vara_shanti,
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
    next_rise_jd: float = 0.0,
) -> list[dict]:
    """Scan the full Vedic day (rise_jd → next_rise_jd) for auspicious muhurta windows.

    Tithi, nakshatra, AND lagna change during the day; each segment between
    transitions is evaluated independently with the actual lagna at that time.
    Within each good segment the best Choghadiya slot is identified to give
    the exact recommended start time.

    Returns list of dicts sorted best-first (highest Choghadiya rank, then longest).
    Each dict: {from, to, duration_mins, nakshatra_te, tithi_te, lagna_te,
                nak_idx, tithi_idx, sun_idx, best_time, choghadiya_te,
                choghadiya_rank, vara_shanti}
    """
    def _ti(j): return int(moon_sun_elongation(j) / 12) % 30
    def _ni(j): return int(moon_longitude(j) / (360.0 / 27)) % 27
    def _li(j): return compute_lagna(j, lat, lon)

    EPSILON = 1.0 / (24 * 60)   # 1 minute in JD
    end_jd  = next_rise_jd if next_rise_jd > rise_jd else rise_jd + 1.0

    if day_cache is not None:
        return _find_good_windows_from_cache(
            day_cache, rise_jd, set_jd, tz_name,
            ceremony_type, birth_charts, masam_name, is_adhika,
            sun_idx, is_uttarayanam, skip_planet_rashis,
            next_rise_jd=end_jd,
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

        is_night_seg = jd >= set_jd

        # Compute best choghadiya rank for this segment
        best_cho_rank_seg = -1
        for slot in cho_slots:
            overlap_start = max(slot["from_jd"], jd)
            overlap_end   = min(slot["to_jd"], window_end_jd)
            if overlap_end - overlap_start < EPSILON:
                continue
            if slot["quality_rank"] > best_cho_rank_seg:
                best_cho_rank_seg = slot["quality_rank"]

        good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, win_lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
            is_uttarayanam=is_uttarayanam,
            is_night=is_night_seg,
            choghadiya_rank=best_cho_rank_seg,
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
                "vara_shanti":     (
                    sun_idx in _BAD_VAARAS.get(ceremony_type, set())
                    and is_night_seg
                    and best_cho_rank == 6
                ),
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
                "date_te":      f"{day} {_MONTH_TE[month - 1]} {year}",
                "date_raw":     f"{day:02d}/{month:02d}/{year}",
                "vaaram_te":    vaaram_te,
                "sunrise":      sunrise,
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
                **({"anandadi_yoga": _ANANDADI_YOGA_TE.get(
                        get_anandadi_yoga(naks_idx, sun_idx)[0],
                        get_anandadi_yoga(naks_idx, sun_idx)[0]
                   ),
                    "amritadi_yoga": get_amritadi_yoga(naks_idx, sun_idx)[1],
                   } if ceremony_type == "prayanam" else {}),
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

    Uses the Vedic day model: day runs from today's sunrise to next day's sunrise.
    When check_hour >= 0, nakshatra/tithi/lagna are evaluated at the requested time,
    not at sunrise. Night times (after sunset, before next sunrise) are valid and
    may qualify via Amrita Choghadiya vara exception per Telugu Sampradaya.

    check_hour=-1 means no specific time was requested (day-level check only).
    """
    import calendar as _cal

    jd = local_date_to_jd(year, month, day, tz_name)
    rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)

    # Compute next-day sunrise for the Vedic day boundary
    _, days_in_month = _cal.monthrange(year, month)
    if day < days_in_month:
        ny, nm, nd = year, month, day + 1
    elif month < 12:
        ny, nm, nd = year, month + 1, 1
    else:
        ny, nm, nd = year + 1, 1, 1
    next_rise_jd, _ = get_sunrise_sunset(local_date_to_jd(ny, nm, nd, tz_name), lat, lon)

    # Sunrise-anchored values (used for day-level labels — vara/masa don't change intraday)
    moon_lon_rise  = moon_longitude(rise_jd)
    elong_rise     = moon_sun_elongation(rise_jd)
    naks_idx_rise  = int(moon_lon_rise / (360.0 / 27)) % 27
    tithi_idx_rise = int(elong_rise / 12) % 30
    day_rashi_idx  = int(moon_lon_rise / 30) % 12

    dt_rise = jd_to_local_datetime(rise_jd, tz_name)
    dt_set  = jd_to_local_datetime(set_jd, tz_name)
    sun_idx = (dt_rise.weekday() + 1) % 7

    lagna_idx_rise = compute_lagna(rise_jd, lat, lon)
    pan            = compute_panchang(jd, lat, lon, tz_name)
    masam_name     = pan["masam"]["en"]
    is_adhika      = pan["masam"]["adhika"]
    is_uttarayanam = sun_longitude(rise_jd) < 180

    rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
    set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60
    kalams    = compute_kalams(rise_mins, set_mins, sun_idx)

    # Midnight JD for this civil date
    midnight_jd = rise_jd - rise_mins / (24.0 * 60)

    # Intraday transition helpers
    def _ti(j): return int(moon_sun_elongation(j) / 12) % 30
    def _ni(j): return int(moon_longitude(j) / (360.0 / 27)) % 27

    EPSILON = 1.0 / (24 * 60)

    # Build transition list for the full Vedic day (rise → next rise)
    transitions: list[dict] = []
    cur_jd    = rise_jd
    cur_naks  = naks_idx_rise
    cur_tithi = tithi_idx_rise
    while cur_jd < next_rise_jd - EPSILON:
        n_change = find_next_index_change(cur_jd, _ni, cur_naks,  step_hours=1.0, max_hours=28)
        t_change = find_next_index_change(cur_jd, _ti, cur_tithi, step_hours=1.0, max_hours=28)
        candidates = [c for c in [n_change, t_change] if c is not None and c < next_rise_jd]
        if not candidates:
            break
        chg_jd   = min(candidates)
        after_jd = chg_jd + EPSILON
        new_naks  = _ni(after_jd)
        new_tithi = _ti(after_jd)
        chg_time  = jd_to_local_datetime(chg_jd, tz_name).strftime("%H:%M")
        if new_naks != cur_naks:
            transitions.append({"type": "nakshatra", "from_te": NAKSHATRA_TE[cur_naks],
                                 "to_te": NAKSHATRA_TE[new_naks], "time": chg_time})
        if new_tithi != cur_tithi:
            transitions.append({"type": "tithi", "from_te": TITHI_TE[cur_tithi],
                                 "to_te": TITHI_TE[new_tithi], "time": chg_time})
        cur_naks  = new_naks
        cur_tithi = new_tithi
        cur_jd    = chg_jd + EPSILON

    # Determine nakshatra/tithi/lagna at the requested time (or sunrise)
    if check_hour >= 0:
        check_jd = midnight_jd + check_hour / 24.0 + check_minute / (24.0 * 60)
        naks_idx      = _ni(check_jd)
        tithi_idx     = _ti(check_jd)
        lagna_idx     = compute_lagna(check_jd, lat, lon)
        day_rashi_idx = int(moon_longitude(check_jd) / 30) % 12
        is_night      = check_jd > set_jd
    else:
        check_jd      = rise_jd
        naks_idx      = naks_idx_rise
        tithi_idx     = tithi_idx_rise
        lagna_idx     = lagna_idx_rise
        is_night      = False

    # Choghadiya at the checked time
    cho_slots = compute_choghadiya_slots(rise_jd, set_jd, next_rise_jd, sun_idx)
    choghadiya_rank_at_time = -1
    choghadiya_te_at_time   = ""
    for slot in cho_slots:
        if slot["from_jd"] <= check_jd < slot["to_jd"]:
            choghadiya_rank_at_time = slot["quality_rank"]
            choghadiya_te_at_time   = slot["quality_te"]
            break

    vara_bad = sun_idx in _BAD_VAARAS.get(ceremony_type, set())

    overall_good = is_auspicious(
        naks_idx, tithi_idx, sun_idx, lagna_idx,
        birth_charts, ceremony_type,
        masam_name=masam_name, is_adhika_masam=is_adhika,
        day_rashi_idx=day_rashi_idx,
        is_uttarayanam=is_uttarayanam,
        is_night=is_night,
        choghadiya_rank=choghadiya_rank_at_time,
    )

    # Find all good windows (day + night, full Vedic day) — computed early so
    # vara_shanti_required can be used in factor messages below
    all_windows = _find_good_windows(
        rise_jd, set_jd, lat, lon, tz_name,
        ceremony_type, birth_charts, masam_name, is_adhika,
        sun_idx, lagna_idx_rise,
        is_uttarayanam=is_uttarayanam,
        next_rise_jd=next_rise_jd,
    )

    # Split into day windows (before sunset) and night windows (after sunset)
    def _is_after_sunset(from_str: str) -> bool:
        fh, fm = map(int, from_str.split(":"))
        sh, sm = map(int, dt_set.strftime("%H:%M").split(":"))
        from_mins = fh * 60 + fm
        set_m2    = sh * 60 + sm
        if from_mins < 6 * 60:          # early morning (00-06h) is post-midnight night
            return True
        return from_mins >= set_m2

    good_windows       = [w for w in all_windows if not _is_after_sunset(w["from"])]
    night_good_windows = [w for w in all_windows if     _is_after_sunset(w["from"])]

    # vara_shanti_required: True if vara is bad but mitigated on this Vedic day
    # via night Amrita Choghadiya (at least one night window with vara_shanti=True)
    vara_shanti_required = vara_bad and any(w.get("vara_shanti") for w in all_windows)

    # When no specific time was requested, re-anchor evaluation context to the
    # best muhurta window so factors reflect the actual recommended time
    # (nakshatra/tithi at the best window, not at sunrise).
    if check_hour < 0 and all_windows:
        best = all_windows[0]
        naks_idx  = best["nak_idx"]
        tithi_idx = best["tithi_idx"]
        lagna_idx = best["lagna_idx"]
        bw_h, bw_m = map(int, best["from"].split(":"))
        _bw_jd = midnight_jd + bw_h / 24.0 + bw_m / (24.0 * 60)
        if _bw_jd < rise_jd:           # post-midnight window (e.g. 00:xx–02:xx)
            _bw_jd += 1.0
        day_rashi_idx           = int(moon_longitude(_bw_jd) / 30) % 12
        is_night                = _bw_jd > set_jd
        choghadiya_rank_at_time = best["choghadiya_rank"]
        overall_good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
            is_uttarayanam=is_uttarayanam,
            is_night=is_night,
            choghadiya_rank=choghadiya_rank_at_time,
        )

    cer_te        = _CEREMONY_TE.get(ceremony_type, ceremony_type)
    good_factors: list[str] = []
    bad_factors:  list[str] = []

    # 0. Ayanam
    if ceremony_type in ("upanayanam",):
        ayanam_name = pan["ayanam"]["te"]
        if is_uttarayanam:
            good_factors.append(f"అయనం: {ayanam_name} — {cer_te}కు శుభ అయనం ✓")
        else:
            bad_factors.append(f"అయనం: {ayanam_name} — {cer_te}కు కేవలం ఉత్తరాయణంలో మాత్రమే చేయాలి")

    # 1. Masa Shuddhi
    if masam_name and not _masam_ok(masam_name, is_adhika, ceremony_type):
        label = "అధిక మాసం" if is_adhika else pan["masam"]["te"] + " మాసం"
        bad_factors.append(f"{label} — {cer_te}కు నిషిద్ధ మాసం (చాతుర్మాస్య నియమం)")
    else:
        good_factors.append(f"మాసం: {pan['masam']['te']} — {cer_te}కు అనుకూలం")

    # 2. Vaara Shuddhi
    vaara_te = pan["vaaram"]["te"]
    if vara_bad:
        if vara_shanti_required:
            bad_factors.append(
                f"వారం: {vaara_te} — రాత్రి అమృత చోఘడియాలో శాంతి పూజతో నివర్తించవచ్చు ⚠"
            )
        else:
            bad_factors.append(f"వారం: {vaara_te} — {cer_te}కు నిషిద్ధ వారం (సూర్య/మంగళ/శని దోషం)")
    else:
        good_factors.append(f"వారం: {vaara_te} — {cer_te}కు అనుకూల వారం ✓")

    # 2c. Anandadi Yoga (Prayanam only)
    if ceremony_type == "prayanam":
        anandadi_name, anandadi_tier = get_anandadi_yoga(naks_idx, sun_idx)
        yoga_te = _ANANDADI_YOGA_TE.get(anandadi_name, anandadi_name)
        if anandadi_tier == "avoid":
            bad_factors.append(f"ఆనందాది యోగం: {yoga_te} — రాక్షస యోగం, ప్రయాణానికి నిషేధించబడింది")
        elif anandadi_tier == "restrict_24min":
            bad_factors.append(f"ఆనందాది యోగం: {yoga_te} — మొదటి 24 నిమిషాలు నివారించాలి")
        else:
            good_factors.append(f"ఆనందాది యోగం: {yoga_te} — శుభ యోగం ✓")

    # 2d. Amritadi Yoga (Prayanam only)
    if ceremony_type == "prayanam":
        am_en, am_te, am_tier = get_amritadi_yoga(naks_idx, sun_idx)
        if am_tier == "avoid":
            bad_factors.append(f"అమృతాది యోగం: {am_te} — ప్రయాణానికి అశుభ యోగం")
        else:
            good_factors.append(f"అమృతాది యోగం: {am_te} — శుభ యోగం ✓")

    # 3. Nakshatra — evaluated at requested time
    if ceremony_type == "prayanam":
        if naks_idx in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
            good_factors.append(f"నక్షత్రం: {NAKSHATRA_TE[naks_idx]} — శ్లోకంలో శుభ నక్షత్రం ✓")
        else:
            good_factors.append(f"నక్షత్రం: {NAKSHATRA_TE[naks_idx]} — అమృతాది యోగం శుభంగా ఉన్నందున శ్లోక నక్షత్రం ద్వితీయం")
    else:
        if naks_idx in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
            good_factors.append(f"నక్షత్రం: {NAKSHATRA_TE[naks_idx]} — {cer_te}కు శుభమైన నక్షత్రం ✓")
        else:
            bad_factors.append(f"నక్షత్రం: {NAKSHATRA_TE[naks_idx]} — {cer_te}కు అనుకూలమైన నక్షత్రం కాదు")

    # 4. Tithi — evaluated at requested time
    if tithi_idx in _BAD_TITHIS.get(ceremony_type, set()):
        bad_factors.append(f"తిథి: {TITHI_TE[tithi_idx]} — నివారించాల్సిన తిథి (రిక్త/దోష తిథి)")
    else:
        good_factors.append(f"తిథి: {TITHI_TE[tithi_idx]} — శుభ తిథి ✓")

    # 5. Tara Balam
    for i, chart in enumerate(birth_charts):
        name = chart.get("name") or f"వ్యక్తి {i + 1}"
        if _tara_ok(chart["janma_nakshatra_idx"], naks_idx):
            good_factors.append(f"{name}: తార బలం అనుకూలం ✓")
        else:
            bad_factors.append(
                f"{name}: తార బలం అననుకూలం — జన్మ నక్షత్రానికి "
                f"వ్యతిరేక తార (1, 3, 5 లేదా 7వ తార)"
            )

    # 6. Rashi Shuddhi
    if day_rashi_idx >= 0 and _RASHI_SHUDDHI_FORBIDDEN.get(ceremony_type):
        for i, chart in enumerate(birth_charts):
            name = chart.get("name") or f"వ్యక్తి {i + 1}"
            jrashi = chart.get("janma_rashi_idx", -1)
            if jrashi >= 0:
                if _rashi_shuddhi_ok(day_rashi_idx, jrashi, ceremony_type):
                    good_factors.append(f"{name}: రాశి శుద్ధి అనుకూలం ✓")
                else:
                    pos = (day_rashi_idx - jrashi) % 12 + 1
                    bad_factors.append(
                        f"{name}: రాశి శుద్ధి అననుకూలం — చంద్రుడు {pos}వ స్థానంలో ఉన్నాడు"
                    )

    # 7. Panchaka Dosha
    if _panchaka_ok(naks_idx, sun_idx, tithi_idx, lagna_idx):
        good_factors.append("పంచక దోషం లేదు ✓")
    else:
        good_factors.append("పంచక దోషం ఉంది — పంచక శాంతి చేయించుకోవాలి ⚠")

    if not overall_good and good_windows:
        windows_str = ", ".join(f"{w['from']}–{w['to']}" for w in good_windows)
        good_factors.append(f"పగటిపూట శుభ ముహూర్త సమయాలు: {windows_str} ✓")
    if night_good_windows:
        nw_str = ", ".join(f"{w['from']}–{w['to']}" for w in night_good_windows)
        good_factors.append(f"రాత్రి శుభ ముహూర్త సమయాలు: {nw_str} ✓")

    # Time analysis
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
        time_bad   = False

        if _in_window(kalams["rahu_kalam"], check_mins):
            time_issues.append(f"రాహు కాలం ({kalams['rahu_kalam']['start']}–{kalams['rahu_kalam']['end']})లో ఉంది")
            time_bad = True
        if _in_window(kalams["yamaganda"], check_mins):
            time_issues.append(f"యమగండ కాలం ({kalams['yamaganda']['start']}–{kalams['yamaganda']['end']})లో ఉంది")
            time_bad = True
        if _in_window(kalams["gulika_kalam"], check_mins):
            time_issues.append(f"గులిక కాలం ({kalams['gulika_kalam']['start']}–{kalams['gulika_kalam']['end']})లో ఉంది")
            time_bad = True
        for v in ([pan.get("varjyam")] if isinstance(pan.get("varjyam"), dict) else (pan.get("varjyam") or [])):
            if _in_window(v, check_mins):
                time_issues.append(f"వర్జ్యం ({v['start']}–{v['end']})లో ఉంది")
                time_bad = True
        for d in ([pan.get("dur_muhurtam")] if isinstance(pan.get("dur_muhurtam"), dict) else (pan.get("dur_muhurtam") or [])):
            if _in_window(d, check_mins):
                time_issues.append(f"దుర్ముహూర్తం ({d['start']}–{d['end']})లో ఉంది")
                time_bad = True

        def _in_good_window(mins: float) -> bool:
            all_w = good_windows + night_good_windows
            if not all_w:
                return overall_good
            for w in all_w:
                wh, wm = map(int, w["from"].split(":"))
                eh, em = map(int, w["to"].split(":"))
                wstart = wh * 60 + wm
                wend   = eh * 60 + em
                if wend < wstart:
                    wend += 24 * 60
                check_m = mins if mins >= wstart else mins + 24 * 60
                if wstart <= check_m <= wend:
                    return True
            return False

        in_good = _in_good_window(check_mins)
        if time_bad:
            time_verdict = "bad"
        elif in_good:
            time_verdict = "good"
        else:
            time_verdict = "outside"

    # Overall verdict
    day_has_good = overall_good or bool(good_windows) or bool(night_good_windows)

    if day_has_good and time_verdict in (None, "good"):
        verdict = "good"
    elif day_has_good and time_verdict in ("bad", "outside"):
        verdict = "mixed"
    else:
        verdict = "bad"

    return {
        "verdict":                verdict,
        "overall_day_good":       day_has_good,
        "time_verdict":           time_verdict,
        "vara_shanti_required":   vara_shanti_required,
        "date_te":                f"{day} {_MONTH_TE[month - 1]} {year}",
        "vaaram_te":              pan["vaaram"]["te"],
        # nakshatra/tithi at the requested time (or sunrise if no time given)
        "nakshatra_te":           NAKSHATRA_TE[naks_idx],
        "tithi_te":               TITHI_TE[tithi_idx],
        # sunrise reference values
        "nakshatra_at_sunrise_te": NAKSHATRA_TE[naks_idx_rise],
        "tithi_at_sunrise_te":     TITHI_TE[tithi_idx_rise],
        "yoga_te":                pan["yoga"]["te"],
        "masam_te":               pan["masam"]["te"],
        "sudhi_name_te":          _SUDHI_NAME_TE.get(ceremony_type, ""),
        "sunrise":                dt_rise.strftime("%H:%M"),
        "sunset":                 dt_set.strftime("%H:%M"),
        "good_factors":           good_factors,
        "bad_factors":            bad_factors,
        "time_issues":            time_issues,
        "transitions":            transitions,
        "rahu_kalam":             kalams["rahu_kalam"],
        "yamaganda":              kalams["yamaganda"],
        "gulika_kalam":           kalams["gulika_kalam"],
        "dur_muhurtam":           pan["dur_muhurtam"],
        "varjyam":                pan["varjyam"],
        "good_windows":           good_windows,
        "night_good_windows":     night_good_windows,
    }
