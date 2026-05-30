"""
South Indian Telugu Panchang computations.
All functions take a Julian Day at local solar noon for the date in question.
"""
from __future__ import annotations
from .astro import (
    sun_longitude, moon_longitude, moon_sun_elongation,
    get_sunrise_sunset, jd_to_local_datetime, find_next_index_change,
)
import swisseph as swe

# ── Name tables ──────────────────────────────────────────────────────────────

SAMVATSARA_EN = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
    "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
    "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrishabha",
    "Chitrabhanu", "Svabhanu", "Tarana", "Parthiva", "Vyaya",
    "Sarvajit", "Sarvadharin", "Virodhin", "Vikruta", "Khara",
    "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakrut", "Shobhana", "Krodhi", "Vishvavasu", "Parabhava",
    "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhakrut",
    "Paridhavi", "Pramadin", "Ananda", "Rakshasa", "Nala",
    "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati",
    "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]
SAMVATSARA_TE = [
    "ప్రభవ", "విభవ", "శుక్ల", "ప్రమోద", "ప్రజాపతి",
    "అంగిరస", "శ్రీముఖ", "భావ", "యువ", "ధాత్రి",
    "ఈశ్వర", "బహుధాన్య", "ప్రమాథి", "విక్రమ", "వృషభ",
    "చిత్రభాను", "స్వభాను", "తారణ", "పార్థివ", "వ్యయ",
    "సర్వజిత్", "సర్వధారి", "విరోధి", "వికృత", "ఖర",
    "నందన", "విజయ", "జయ", "మన్మథ", "దుర్ముఖి",
    "హేవిళంబి", "విళంబి", "వికారి", "శార్వరి", "ప్లవ",
    "శుభకృత్", "శోభన", "క్రోధి", "విశ్వావసు", "పరాభవ",
    "ప్లవంగ", "కీలక", "సౌమ్య", "సాధారణ", "విరోధకృత్",
    "పరిధావి", "ప్రమాదీ", "ఆనంద", "రాక్షస", "నల",
    "పింగళ", "కాళయుక్తి", "సిద్ధార్థి", "రౌద్ర", "దుర్మతి",
    "దుందుభి", "రుధిరోద్గారి", "రక్తాక్షి", "క్రోధన", "అక్షయ",
]

MASAM_EN = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashvina", "Kartika",
    "Margashira", "Pushya", "Magha", "Phalguna",
]
MASAM_TE = [
    "చైత్ర", "వైశాఖ", "జ్యేష్ఠ", "ఆషాఢ",
    "శ్రావణ", "భాద్రపద", "ఆశ్వయుజ", "కార్తీక",
    "మార్గశిర", "పుష్య", "మాఘ", "ఫాల్గుణ",
]

RUTU_EN = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]
RUTU_TE = ["వసంత", "గ్రీష్మ", "వర్ష", "శరత్", "హేమంత", "శిశిర"]

TITHI_EN = [
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]
TITHI_TE = [
    "ప్రథమ", "ద్వితీయ", "తృతీయ", "చతుర్థి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పౌర్ణమి",
    "ప్రథమ", "ద్వితీయ", "తృతీయ", "చతుర్థి", "పంచమి",
    "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి",
    "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "అమావాస్య",
]

NAKSHATRA_EN = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_TE = [
    "అశ్వని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర",
    "ఆర్ద్ర", "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఘ",
    "పూర్వ ఫల్గుని", "ఉత్తర ఫల్గుని", "హస్త", "చిత్ర", "స్వాతి",
    "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ",
    "ఉత్తరాషాఢ", "శ్రావణ", "ధనిష్ఠ", "శతభిష",
    "పూర్వభాద్ర", "ఉత్తరభాద్ర", "రేవతి",
]

YOGA_EN = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]
YOGA_TE = [
    "విష్కంభ", "ప్రీతి", "ఆయుష్మాన్", "సౌభాగ్య", "శోభన",
    "అతిగండ", "సుకర్మ", "ధృతి", "శూల", "గండ",
    "వృద్ధి", "ధ్రువ", "వ్యాఘాత", "హర్షణ", "వజ్ర",
    "సిద్ధి", "వ్యతీపాత", "వరీయాన్", "పరిఘ", "శివ",
    "సిద్ధ", "సాధ్య", "శుభ", "శుక్ల", "బ్రహ్మ",
    "ఇంద్ర", "వైధృతి",
]

KARANA_MOVABLE_EN = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
KARANA_MOVABLE_TE = ["బవ", "బాలవ", "కౌలవ", "తైతిల", "గరజ", "వణిజ", "విష్టి"]
KARANA_FIXED_EN = ["Kimstughna", "Shakuni", "Chatushpada", "Nagava"]
KARANA_FIXED_TE = ["కింస్తుఘ్న", "శకుని", "చతుష్పద", "నాగవ"]

VAARAM_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
VAARAM_TE = ["ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం", "గురువారం", "శుక్రవారం", "శనివారం"]

# Traditional Sanskrit/Vedic names used in Sankalpam recitation.
# These are the names of the planetary deities — different from the modern colloquial weekday names:
#   Sunday  → Bhanu  (Sun epithet)       not "Ravi-varam"
#   Monday  → Soma   (Moon)              not "Soma-varam" (same root, but no "varam" suffix)
#   Tuesday → Bhouma (son of Earth/Mars) not "Mangala-varam"
#   Wed     → Saumya (Mercury, auspicious) not "Budha-varam"
#   Thu     → Brihaspati (Jupiter/Guru)  not "Guru-varam"
#   Friday  → Bhrughu (sage Bhrigu, patron of Venus) NOT "Shukra-varam"
#   Saturday→ Sthira (Saturn, the slow/stable) not "Shani-varam"
VAARAM_SANKALPAM_EN = ["Bhanu", "Soma", "Bhouma", "Saumya", "Brihaspati", "Bhrughu", "Sthira"]
VAARAM_SANKALPAM_TE = ["భాను", "సోమ", "భౌమ", "సౌమ్య", "బృహస్పతి", "భృగు", "స్థిర"]

# Varjyam start offset (in proportional ghatikas from sunrise, where 1 ghatika = day/30)
# for each nakshatra (0=Ashvini … 26=Revati).
# Table verified against Venkatrama & Co. Telugu Panchangam (Rajahmundry edition).
# Duration is fixed at 4 ghatikas 25 palas = 106 minutes.
_VARJYAM_GHATIKAS = [
    11, 23, 17, 26, 22,  7, 18,  4, 19, 13,  # 0-9   Ashvini–Magha
    10, 20, 16,  9, 22, 11,  9,  5, 14, 22,  # 10-19 PurvaPhalguni–PurvaAshadha
    11,  6, 10, 24, 23,  9,  1,              # 20-26 UttaraAshadha–Revati
]
_VARJYAM_DURATION_MINS = 106  # 4 ghatikas 25 palas (fixed traditional value)

# Dur Muhurtam: muhurta positions (1-indexed) per weekday.
# Day muhurtas 1-30: counted from sunrise, each = (sunset-sunrise)/30.
# Night muhurtas 31-60: counted from sunset, each = (24h-day_duration)/30.
# Duration = number of muhurtas × respective muhurta size.
# Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
# Verified against Venkatrama & Co. Telugu Panchangam (Rajahmundry edition).
_DUR_MUHURTAM_TABLE = [
    [(27, 2)],           # Sunday:    27th–28th day muhurtas (evening)
    [(17, 2), (23, 2)],  # Monday:    17th–18th and 23rd–24th
    [(7,  2), (43, 2)],  # Tuesday:   7th–8th (day) and 13th–14th night (=43rd–44th)
    [(15, 2)],           # Wednesday: 15th–16th
    [(11, 2), (23, 2)],  # Thursday:  11th–12th and 23rd–24th
    [(7,  2), (17, 2)],  # Friday:    7th–8th and 17th–18th
    [(1,  4)],           # Saturday:  1st–4th (from sunrise, early morning)
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_amavasya(jd_ref: float, forward: bool = True) -> float:
    """Find nearest Amavasya (new moon) from jd_ref.
    Scans in 2h steps detecting elongation wrap 360°→0°, then binary search."""
    step = (2 / 24.0) if forward else -(2 / 24.0)
    prev_elong = moon_sun_elongation(jd_ref)
    jd = jd_ref

    for _ in range(400):
        jd += step
        curr_elong = moon_sun_elongation(jd)
        wrapped = (forward and prev_elong > 300 and curr_elong < 60) or \
                  (not forward and prev_elong < 60 and curr_elong > 300)
        if wrapped:
            lo = jd - abs(step) if forward else jd
            hi = jd if forward else jd + abs(step)
            for _ in range(40):
                mid = (lo + hi) / 2
                e = moon_sun_elongation(mid)
                if e < 180:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2
        prev_elong = curr_elong

    raise ValueError(f"Amavasya not found from jd={jd_ref}, forward={forward}")


# ── Public API ───────────────────────────────────────────────────────────────

def compute_panchang(jd: float, lat: float, lon: float, tz_name: str) -> dict:
    """Compute all panchang fields for the given Julian Day + location.

    jd is used only as a date anchor (solar noon) to locate the correct
    sunrise. All panchang elements — tithi, nakshatra, yoga, karana,
    vaaram, masam, etc. — are computed at sunrise, following the
    traditional South Indian Telugu convention.

    Returns a dict with keys: samvatsara, ayanam, rutu, masam, paksham,
    tithi, vaaram, nakshatra, yoga, karana, sunrise, sunset.
    Each value is a dict with 'en' and 'te' keys (plus 'adhika' for masam).
    """
    # ── Sunrise / Sunset — computed first; all panchang elements use rise_jd ──
    rise_jd, set_jd = get_sunrise_sunset(jd, lat, lon)
    rise_local = jd_to_local_datetime(rise_jd, tz_name)
    set_local  = jd_to_local_datetime(set_jd,  tz_name)

    # Use sunrise as the canonical reference moment for all panchang elements.
    jd_ref   = rise_jd
    dt_local = rise_local

    # ── Masam + Adhika ──
    # Must be computed before Samvatsara because the Ugadi boundary depends on masam_idx.
    # A0 = new moon that started this lunar month (search backward from yesterday)
    # A1 = next new moon that will end this month (search forward from tomorrow)
    jd_a0_cand = _find_amavasya(jd_ref - 1, forward=False)
    if jd_ref - jd_a0_cand > 29.0:
        jd_a0 = _find_amavasya(jd_a0_cand + 25, forward=True)
    else:
        jd_a0 = jd_a0_cand
    jd_a1 = _find_amavasya(jd_ref + 1, forward=True)
    rashi_a0 = int(sun_longitude(jd_a0) / 30) % 12
    rashi_a1 = int(sun_longitude(jd_a1) / 30) % 12
    if rashi_a0 == rashi_a1:
        # No sankranti between the two new moons → Adhika (leap) month
        masam_idx = (rashi_a0 + 1) % 12
        is_adhika = True
    else:
        masam_idx = rashi_a1
        is_adhika = False
    masam = {
        "en": MASAM_EN[masam_idx],
        "te": MASAM_TE[masam_idx],
        "adhika": is_adhika,
    }

    # ── Samvatsara ──
    # The samvatsara changes at Ugadi (Chaitra Shukla Pratipada), not on Jan 1.
    # masam_idx: Chaitra=0 … Margashira=8, Pushya=9, Magha=10, Phalguna=11
    # If masam_idx <= 8 (Chaitra through Margashira): Ugadi has passed → current year
    # If masam_idx >= 9 (Pushya, Magha, Phalguna): still before next Ugadi → previous year
    sam_year = dt_local.year if masam_idx <= 8 else dt_local.year - 1
    saka_year = sam_year - 78
    sam_idx = (saka_year % 60 + 11) % 60
    samvatsara = {"en": SAMVATSARA_EN[sam_idx], "te": SAMVATSARA_TE[sam_idx]}

    # ── Ayanam ──
    sun_lon = sun_longitude(jd_ref)
    ayanam = {
        "en": "Uttarayanam" if sun_lon < 180 else "Dakshinayanam",
        "te": "ఉత్తరాయణం" if sun_lon < 180 else "దక్షిణాయణం",
    }

    # ── Rutu (derived from masam index, NOT from sun longitude directly) ──
    rutu_idx = (masam_idx // 2) % 6
    rutu = {"en": RUTU_EN[rutu_idx], "te": RUTU_TE[rutu_idx]}

    # ── Elongation-based fields ──
    elong = moon_sun_elongation(jd_ref)

    # Paksham
    paksham = {
        "en": "Shukla Paksham" if elong < 180 else "Krishna Paksham",
        "te": "శుక్ల పక్షం" if elong < 180 else "కృష్ణ పక్షం",
    }

    # Tithi: each tithi = 12°. Index 0-29 → Shukla 1-15, Krishna 1-15
    tithi_idx = int(elong / 12) % 30
    tithi = {"en": TITHI_EN[tithi_idx], "te": TITHI_TE[tithi_idx]}

    # Nakshatra: 27 nakshatras, each spans 360/27 ≈ 13.333°
    moon_lon = moon_longitude(jd_ref)
    naks_idx = int(moon_lon / (360 / 27)) % 27
    nakshatra = {"en": NAKSHATRA_EN[naks_idx], "te": NAKSHATRA_TE[naks_idx]}

    # Yoga: sum of sidereal sun + moon longitudes, divided into 27 equal parts
    yoga_idx = int((sun_lon + moon_lon) / (360 / 27)) % 27
    yoga = {"en": YOGA_EN[yoga_idx], "te": YOGA_TE[yoga_idx]}

    # Karana: 60 half-tithis per lunar month (each karana = 6° elongation)
    # k_idx 0=Kimstughna (fixed), 1-56=movable (7-cycle), 57=Shakuni, 58=Chatushpada, 59=Nagava
    k_idx = int(elong / 6) % 60
    if k_idx == 0:
        karana = {"en": KARANA_FIXED_EN[0], "te": KARANA_FIXED_TE[0]}
    elif k_idx <= 56:
        mi = (k_idx - 1) % 7
        karana = {"en": KARANA_MOVABLE_EN[mi], "te": KARANA_MOVABLE_TE[mi]}
    elif k_idx == 57:
        karana = {"en": KARANA_FIXED_EN[1], "te": KARANA_FIXED_TE[1]}
    elif k_idx == 58:
        karana = {"en": KARANA_FIXED_EN[2], "te": KARANA_FIXED_TE[2]}
    else:
        karana = {"en": KARANA_FIXED_EN[3], "te": KARANA_FIXED_TE[3]}

    # ── Vaaram ──
    # Python weekday(): Monday=0 … Sunday=6
    # Hindu vaaram: Sunday=0 … Saturday=6
    weekday = dt_local.weekday()
    sun_idx = (weekday + 1) % 7
    vaaram = {
        "en": VAARAM_EN[sun_idx],
        "te": VAARAM_TE[sun_idx],
        "sankalpam_en": VAARAM_SANKALPAM_EN[sun_idx],
        "sankalpam_te": VAARAM_SANKALPAM_TE[sun_idx],
    }

    # ── End times for tithi, nakshatra, yoga, karana ──
    def _tithi_idx(j):
        return int(moon_sun_elongation(j) / 12) % 30

    def _naks_idx(j):
        return int(moon_longitude(j) / (360.0 / 27)) % 27

    def _yoga_idx(j):
        return int((sun_longitude(j) + moon_longitude(j)) / (360.0 / 27)) % 27

    def _karana_idx(j):
        return int(moon_sun_elongation(j) / 6) % 60

    def _end_time_fields(end_jd):
        if end_jd is None:
            return None, False
        end_dt = jd_to_local_datetime(end_jd, tz_name)
        return end_dt.strftime("%H:%M"), end_dt.date() > dt_local.date()

    tithi_end_time, tithi_next_day = _end_time_fields(
        find_next_index_change(jd_ref, _tithi_idx, tithi_idx))
    naks_end_time, naks_next_day = _end_time_fields(
        find_next_index_change(jd_ref, _naks_idx, naks_idx))
    yoga_end_time, yoga_next_day = _end_time_fields(
        find_next_index_change(jd_ref, _yoga_idx, yoga_idx))
    karan_end_time, karan_next_day = _end_time_fields(
        find_next_index_change(jd_ref, _karana_idx, k_idx))

    # ── Sunrise / Sunset ──

    # ── Varjyam + Dur Muhurtam ──
    # Both use PROPORTIONAL muhurtas where the day (sunrise→sunset) is divided
    # into 30 equal muhurtas and the night (sunset→next sunrise) into 30 more.
    rise_mins = rise_local.hour * 60 + rise_local.minute + rise_local.second / 60
    set_mins  = set_local.hour  * 60 + set_local.minute  + set_local.second  / 60
    day_dur   = set_mins - rise_mins
    night_dur = 24 * 60 - day_dur
    day_muh   = day_dur  / 30.0   # one daytime muhurta in minutes
    night_muh = night_dur / 30.0  # one nighttime muhurta in minutes

    def _fmt_mins(m: float) -> str:
        m = m % (24 * 60)
        return f"{int(m // 60):02d}:{int(m % 60):02d}"

    # Varjyam: offset = _VARJYAM_GHATIKAS[naks] proportional daytime ghatikas from sunrise
    # Duration: fixed 106 minutes (4 ghatikas 25 palas)
    varjyam_start_mins = rise_mins + _VARJYAM_GHATIKAS[naks_idx] * day_muh
    varjyam_end_mins   = varjyam_start_mins + _VARJYAM_DURATION_MINS
    varjyam = {
        "start": _fmt_mins(varjyam_start_mins),
        "end":   _fmt_mins(varjyam_end_mins),
    }

    # Dur Muhurtam: muhurtas 1-30 = day (from sunrise), 31-60 = night (from sunset)
    dur_periods = []
    for start_m, dur_m in _DUR_MUHURTAM_TABLE[sun_idx]:
        if start_m <= 30:
            dm_start = rise_mins + (start_m - 1) * day_muh
            dm_end   = dm_start + dur_m * day_muh
        else:  # night muhurta (31-60): position within night = start_m - 30
            night_pos = start_m - 30
            dm_start  = set_mins + (night_pos - 1) * night_muh
            dm_end    = dm_start + dur_m * night_muh
        dur_periods.append({"start": _fmt_mins(dm_start), "end": _fmt_mins(dm_end)})
    dur_muhurtam = dur_periods

    return {
        "samvatsara": samvatsara,
        "ayanam": ayanam,
        "rutu": rutu,
        "masam": masam,
        "paksham": paksham,
        "tithi": {**tithi, "end_time": tithi_end_time, "next_day": tithi_next_day},
        "vaaram": vaaram,
        "nakshatra": {**nakshatra, "end_time": naks_end_time, "next_day": naks_next_day},
        "yoga": {**yoga, "end_time": yoga_end_time, "next_day": yoga_next_day},
        "karana": {**karana, "end_time": karan_end_time, "next_day": karan_next_day},
        "varjyam": varjyam,
        "dur_muhurtam": dur_muhurtam,
        "sunrise": rise_local.strftime("%H:%M"),
        "sunset": set_local.strftime("%H:%M"),
    }
