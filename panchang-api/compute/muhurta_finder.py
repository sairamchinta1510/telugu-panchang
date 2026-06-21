"""
Month scanner for auspicious muhurta dates — South Indian Telugu tradition.
Iterates every calendar day, computes panchang at sunrise,
and returns days that pass all auspiciousness checks including
Masa Shuddhi (Chaturmas), Tara Balam, and Panchaka Dosha.
Includes Rahu Kalam, Yamaganda, and Gulika Kalam in output (essential South Indian exclusion periods).
"""
from __future__ import annotations
import calendar

from .astro import (
    local_date_to_jd, get_sunrise_sunset,
    jd_to_local_datetime, moon_longitude, moon_sun_elongation,
    find_next_index_change,
)
from .panchang import compute_panchang, NAKSHATRA_TE, TITHI_TE
from .birth_chart import compute_lagna, RASHI_TE
from .muhurta_rules import (
    is_auspicious, compute_kalams,
    _masam_ok, _GOOD_NAKSHATRAS, _BAD_TITHIS,
    _tara_ok, _rashi_shuddhi_ok, _panchaka_ok,
    _RASHI_SHUDDHI_FORBIDDEN,
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
}


def _find_good_windows(
    rise_jd: float,
    lat: float, lon: float, tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
    masam_name: str,
    is_adhika: bool,
    sun_idx: int,
    lagna_idx: int,   # kept for API compat; actual per-window lagna is recomputed
) -> list[dict]:
    """Scan the full 24 hours from rise_jd for auspicious muhurta windows.

    Tithi, nakshatra, AND lagna change during the day; each segment between
    transitions is evaluated independently with the actual lagna at that time.

    Returns list of {"from": "HH:MM", "to": "HH:MM"} in local time.
    Each window is guaranteed to be at least 1 minute long.
    """
    def _ti(j): return int(moon_sun_elongation(j) / 12) % 30
    def _ni(j): return int(moon_longitude(j) / (360.0 / 27)) % 27
    def _li(j): return compute_lagna(j, lat, lon)

    EPSILON = 1.0 / (24 * 60)   # 1 minute in JD
    end_jd  = rise_jd + 1.0     # exactly 24 hours

    good_windows: list[dict] = []
    jd = rise_jd

    while jd < end_jd - EPSILON:
        ml    = moon_longitude(jd)
        elong = moon_sun_elongation(jd)
        naks_idx      = int(ml / (360.0 / 27)) % 27
        tithi_idx     = int(elong / 12) % 30
        day_rashi_idx = int(ml / 30) % 12
        # Recompute lagna at the start of each sub-window (changes every ~2 h)
        win_lagna_idx = compute_lagna(jd, lat, lon)

        t_change = find_next_index_change(jd, _ti, tithi_idx, step_hours=1.0, max_hours=26)
        n_change = find_next_index_change(jd, _ni, naks_idx,  step_hours=1.0, max_hours=26)
        # Lagna changes every ~2 h; use small step to catch it accurately
        l_change = find_next_index_change(jd, _li, win_lagna_idx, step_hours=0.25, max_hours=3)

        # Window ends at the earliest upcoming transition (capped at 24 h boundary)
        candidates = [c for c in [t_change, n_change, l_change] if c is not None and c < end_jd]
        window_end_jd = min(candidates) if candidates else end_jd

        good = is_auspicious(
            naks_idx, tithi_idx, sun_idx, win_lagna_idx,
            birth_charts, ceremony_type,
            masam_name=masam_name, is_adhika_masam=is_adhika,
            day_rashi_idx=day_rashi_idx,
        )

        if good:
            from_str = jd_to_local_datetime(jd,            tz_name).strftime("%H:%M")
            to_str   = jd_to_local_datetime(window_end_jd, tz_name).strftime("%H:%M")
            h_from, m_from = map(int, from_str.split(":"))
            h_to,   m_to   = map(int, to_str.split(":"))
            total_from = h_from * 60 + m_from
            total_to   = h_to   * 60 + m_to
            if total_to <= total_from:   # crosses midnight
                total_to += 24 * 60
            good_windows.append({
                "from":          from_str,
                "to":            to_str,
                "duration_mins": total_to - total_from,
                "nakshatra_te":  NAKSHATRA_TE[naks_idx],
                "tithi_te":      TITHI_TE[tithi_idx],
                "lagna_te":      RASHI_TE[win_lagna_idx],
            })

        # Always advance by at least EPSILON to prevent infinite loop
        jd = max(window_end_jd, jd + EPSILON) + EPSILON
        if jd >= end_jd:
            break

    # Sort best (longest) window first
    good_windows.sort(key=lambda w: w["duration_mins"], reverse=True)
    return good_windows


def find_muhurtas_for_month(
    year: int,
    month: int,
    lat: float,
    lon: float,
    tz_name: str,
    ceremony_type: str,
    birth_charts: list[dict],
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

            # Get panchang for Masa Shuddhi check (masam name + adhika flag) and Telugu labels
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
                good_windows = _find_good_windows(
                    rise_jd, lat, lon, tz_name,
                    ceremony_type, birth_charts, masam_name, is_adhika,
                    sun_idx, lagna_idx,
                )
                if not good_windows:
                    continue   # truly bad all day

            dt_set    = jd_to_local_datetime(set_jd, tz_name)
            rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
            set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60

            kalams = compute_kalams(rise_mins, set_mins, sun_idx)

            results.append({
                "date_te":      f"{day} {_MONTH_TE[month - 1]} {year}",
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

    rise_mins = dt_rise.hour * 60 + dt_rise.minute + dt_rise.second / 60
    set_mins  = dt_set.hour  * 60 + dt_set.minute  + dt_set.second  / 60
    kalams    = compute_kalams(rise_mins, set_mins, sun_idx)

    cer_te = _CEREMONY_TE.get(ceremony_type, ceremony_type)
    good_factors: list[str] = []
    bad_factors:  list[str] = []

    # 1. Masa Shuddhi
    if masam_name and not _masam_ok(masam_name, is_adhika, ceremony_type):
        label = "అధిక మాసం" if is_adhika else pan["masam"]["te"] + " మాసం"
        bad_factors.append(f"{label} — {cer_te}కు నిషిద్ధ మాసం (చాతుర్మాస్య నియమం)")
    else:
        good_factors.append(f"మాసం: {pan['masam']['te']} — {cer_te}కు అనుకూలం")

    # 2. Nakshatra
    if naks_idx in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
        good_factors.append(f"నక్షత్రం: {pan['nakshatra']['te']} — {cer_te}కు శుభమైన నక్షత్రం ✓")
    else:
        bad_factors.append(f"నక్షత్రం: {pan['nakshatra']['te']} — {cer_te}కు అనుకూలమైన నక్షత్రం కాదు")

    # 3. Tithi
    if tithi_idx in _BAD_TITHIS.get(ceremony_type, set()):
        bad_factors.append(f"తిథి: {pan['tithi']['te']} — నివారించాల్సిన తిథి (రిక్త/దోష తిథి)")
    else:
        good_factors.append(f"తిథి: {pan['tithi']['te']} — శుభ తిథి ✓")

    # 4. Tara Balam per person
    for i, chart in enumerate(birth_charts):
        name = chart.get("name") or f"వ్యక్తి {i + 1}"
        if _tara_ok(chart["janma_nakshatra_idx"], naks_idx):
            good_factors.append(f"{name}: తార బలం అనుకూలం ✓")
        else:
            bad_factors.append(
                f"{name}: తార బలం అననుకూలం — జన్మ నక్షత్రానికి "
                f"వ్యతిరేక తార (1, 3, 5 లేదా 7వ తార)"
            )

    # 5. Rashi Shuddhi (only ceremonies with restrictions)
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

    # 6. Panchaka Dosha
    if _panchaka_ok(naks_idx, sun_idx, tithi_idx, lagna_idx):
        good_factors.append("పంచక దోషం లేదు ✓")
    else:
        bad_factors.append("పంచక దోషం ఉంది — (వారం+తిథి+నక్షత్రం+లగ్నం) % 9 దోష సంఖ్య")

    overall_good = is_auspicious(
        naks_idx, tithi_idx, sun_idx, lagna_idx,
        birth_charts, ceremony_type,
        masam_name=masam_name, is_adhika_masam=is_adhika,
        day_rashi_idx=day_rashi_idx,
    )

    good_windows = _find_good_windows(
        rise_jd, lat, lon, tz_name,
        ceremony_type, birth_charts, masam_name, is_adhika,
        sun_idx, lagna_idx,
    )

    if not overall_good and good_windows:
        windows_str = ", ".join(f"{w['from']}–{w['to']}" for w in good_windows)
        good_factors.append(f"పగటిపూట శుభ ముహూర్త సమయాలు: {windows_str} ✓")

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
        "verdict":          verdict,
        "overall_day_good": overall_good or bool(good_windows),
        "time_verdict":     time_verdict,
        "date_te":          f"{day} {_MONTH_TE[month - 1]} {year}",
        "vaaram_te":        pan["vaaram"]["te"],
        "tithi_te":         pan["tithi"]["te"],
        "nakshatra_te":     pan["nakshatra"]["te"],
        "yoga_te":          pan["yoga"]["te"],
        "masam_te":         pan["masam"]["te"],
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

