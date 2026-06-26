"""
Muhurta auspiciousness rules — South Indian Telugu tradition.
Pure logic — no astronomical calculations. All inputs are pre-computed integer indices.
Sources: Venkatrama & Co. Telugu Panchangam (Rajahmundry), Muhurta Chintamani, Dharmasindhu.
"""
from __future__ import annotations

CEREMONY_VIVAHA         = "vivaha"
CEREMONY_GRUHA_PRAVESAM = "gruha_pravesam"
CEREMONY_UPANAYANAM     = "upanayanam"
CEREMONY_POOJA          = "pooja"
CEREMONY_YUDDHAM        = "yuddham"
CEREMONY_ANNA_PRASANA   = "anna_prasana"
CEREMONY_CHELAMU        = "chelamu"
CEREMONY_KOTTA_BATTALU  = "kotta_battalu"
CEREMONY_PRAYANAM       = "prayanam"
CEREMONY_VIDYARAMBHAM   = "vidyarambham"
CEREMONY_OSHADHA_SEVA   = "oshadha_seva"
CEREMONY_NAMAKARANAM    = "namakaranam"
CEREMONY_GARBHADANAM    = "garbhadanam"
CEREMONY_SANKHU_STAPANA = "sankhu_stapana"

# ── Auspicious nakshatras per ceremony (0-indexed: 0=Ashvini … 26=Revati) ────
# Sources: Muhurta Chintamani (bidyashish/vedicpanchanga.com MC tables),
#          Balavivekini & Vajrashata Sanskrit manuscripts (JDerekLomas/source-library-texts),
#          socraticsurge/telugu-calendar-utilities (Telugu Panchangam library),
#          Venkatrama & Co. Telugu Panchangam (Rajahmundry) — primary Telugu Sampradayam source.
#
# VIVAHA: 12 stars per MC Ch.6. Shravana(21)=Vishnu's star — universally cited in South Indian
#   vivaha lists. Pushya(7) is PROHIBITED despite being excellent for other ceremonies.
#   "Three Uttaras" = UttaraPhalguni(11), UttaraAshadha(20), UttaraBhadrapada(25).
#   [Correction: Added Shravana(21) — confirmed by MC standard + Vajrashata text]
#
# GRUHA PRAVESAM: Requires Sthira (fixed/stable) nakshatras for permanence.
#   Ashlesha(8), Jyeshtha(17), Moola(18) = gandanta nakshatras — explicitly vetoed.
#   [Correction: Swati(14) included — Chara argument applies to lagna not nakshatra (MC Ch.9)]
#
# CHELAMU (Karnavedha/Ear Piercing): Uses the classical "trayam" (group of 3) formula
#   from Balavivekini text: three Shravanas(21,22,23), three Hastas(12,13,14),
#   three Uttaras(11,20,25). Also Pushya(7), Mula(18), Anuradha(16), Rohini(3),
#   Mrigashira(4), Punarvasu(6), Ashwini(0), Revati(26).
#   [Correction: Added Pushya(7) per BV §Karnavedha]
#
# ANNA PRASANA: Balavivekini + Vajrashata confirm Punarvasu(6), Chitra(13),
#   and UttaraAshadha(20).
#   [Correction: Added Chitra(13) per BV §Annaprasana + VS]
#
# NAMAKARANAM: MC standard explicitly NOT-bad list excludes Dhanishtha(22)/Shatabhisha(23).
#   [Correction: Added Dhanishtha(22), Shatabhisha(23)]
#
# OSHADHA SEVA: vedicpanchanga.com MC adds Mrigashira(4); Muhurta Chintamani Ch.12
#   also includes Punarvasu(6) for renewal/recovery. Shatabhisha(23) = "hundred
#   physicians" — most medical nakshatra, correctly kept despite absence in some lists.
#   [Correction: Added Punarvasu(6) per MC Ch.12]
#
# GARBHADANAM: Same family-founding set as vivaha. Chitra(13) allowed as Mridu nakshatra
#   per Dharmasindhu §Garbhadhana.
#   [Correction: Added Chitra(13) per DS §Garbhadhana]
#
# SANKHU STAPANA: Construction/consecration type — Shravana(21) confirmed by analogy
#   with bhoomi_pujan standard from vedicpanchanga.com MC.
#   [Correction: Added Shravana(21), Pushya(7), Chitra(13)]
#
# UPANAYANAM: Pushya(7) is excellent (Guru-Pushya Yoga prized); included. Verified correct.
_GOOD_NAKSHATRAS: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         {3, 4, 9, 11, 12, 14, 16, 18, 20, 21, 25, 26},
    #                         Rohini, Mrigashira, Magha, UttaraPhalguni, Hasta, Swati,
    #                         Anuradha, Moola*, UttaraAshadha, Shravana✓, UttaraBhadra, Revati
    CEREMONY_GRUHA_PRAVESAM: {3, 4, 7, 11, 12, 13, 14, 16, 20, 21, 23, 25, 26},
    #                         Rohini, Mrigashira, Pushya✓, UttaraPhalguni, Hasta, Chitra, Swati,
    #                         Anuradha, UttaraAshadha, Shravana, Shatabhisha, UttaraBhadra, Revati
    CEREMONY_UPANAYANAM:     {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
    CEREMONY_POOJA:          {0, 3, 4, 6, 7, 9, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
    CEREMONY_YUDDHAM:        {1, 2, 5, 8, 9, 12, 17, 18, 20, 22},
    #                         Ugra/Tikshna stars: Bharani, Krittika, Ardra, Ashlesha, Magha,
    #                         Jyeshtha, Moola — for fierce activities. UttaraAshadha(20)=invincible.
    CEREMONY_ANNA_PRASANA:   {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 25, 26},
    CEREMONY_CHELAMU:        {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 18, 20, 21, 22, 23, 25, 26},
    #                         Classical "trayam" groups per Balavivekini:
    #                         3×Shravana(21,22,23), 3×Hasta(12,13,14), 3×Uttara(11,20,25)
    #                         + Pushya(7), Moola(18), Anuradha(16), Rohini(3), Mrigashira(4),
    #                           Punarvasu(6), Ashwini(0), Revati(26)
    CEREMONY_KOTTA_BATTALU:  {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 25, 26},
    CEREMONY_PRAYANAM:       {0, 4, 6, 7, 12, 16, 18, 21, 22, 26},
    #                         Per classical shloka: "మృగాశ్వని పుష్య పునర్వసుచా హస్తానురాధ
    #                         శ్రవణాని మూల ధనిష్ఠ రేవత్ అఖిలే ప్రయాణం ఫలం లేభేట్ శీఘ్ర నివర్తి తంతే"
    #                         Mrigashira(4), Ashvini(0), Pushya(7), Punarvasu(6), Hasta(12),
    #                         Anuradha(16), Shravana(21), Moola(18), Dhanishtha(22), Revati(26).
    #                         Removed: Rohini(3), Chitra(13), Swati(14), UttaraAshadha(20)
    #                         — not in shloka, shloka is primary classical authority for Prayanam.
    CEREMONY_VIDYARAMBHAM:   {0, 3, 4, 6, 7, 12, 13, 14, 16, 20, 21, 25, 26},
    CEREMONY_OSHADHA_SEVA:   {0, 4, 6, 7, 12, 21, 22, 23, 26},
    #                         Shatabhisha(23)="hundred physicians" — kept (correct per tradition).
    CEREMONY_NAMAKARANAM:    {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26},
    #                         Added Dhanishtha(22), Shatabhisha(23) per MC bad-nakshatra exclusion list
    CEREMONY_GARBHADANAM:    {3, 4, 9, 11, 12, 13, 14, 16, 18, 20, 21, 25, 26},
    CEREMONY_SANKHU_STAPANA: {3, 4, 7, 11, 12, 13, 14, 16, 20, 21, 22, 25, 26},
    #                         Added Shravana(21), Pushya(7), Chitra(13) per bhoomi_pujan MC standard
}

# ── Bad tithis per ceremony (0-indexed: 0=Shukla Prathama … 14=Purnima … 29=Amavasya) ─
# Rikta tithis (universally inauspicious): Chaturthi(3/18), Navami(8/23), Chaturdashi(13/28)
# in BOTH pakshas. Additional exclusions vary by ceremony.
# Ashtami (Shukla idx=7, Krishna idx=22) is additionally forbidden for all samskaras
# per MC §Vivaha-tithi-nisheda: "Ashtamī sarvatra varjyā". Rikta already covers
# Chaturthi/Navami/Chaturdashi in both pakshas.
_RIKTA: set[int] = {3, 8, 13, 18, 23, 28}

_BAD_TITHIS: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         _RIKTA | {7, 14, 22, 29},
    CEREMONY_GRUHA_PRAVESAM: _RIKTA | {7, 14, 22, 29},
    CEREMONY_UPANAYANAM:     _RIKTA | {7, 14, 22, 29},
    CEREMONY_POOJA:          {29},
    CEREMONY_YUDDHAM:        _RIKTA | {14, 29},
    CEREMONY_ANNA_PRASANA:   _RIKTA | {7, 14, 22, 29},
    CEREMONY_CHELAMU:        _RIKTA | {7, 14, 22, 29},
    CEREMONY_KOTTA_BATTALU:  _RIKTA | {7, 22, 29},
    CEREMONY_PRAYANAM:       _RIKTA | {7, 14, 22, 29},
    CEREMONY_VIDYARAMBHAM:   _RIKTA | {7, 14, 22, 29},
    CEREMONY_OSHADHA_SEVA:   _RIKTA | {7, 14, 22, 29},
    CEREMONY_NAMAKARANAM:    _RIKTA | {7, 14, 22, 29},
    CEREMONY_GARBHADANAM:    _RIKTA | {7, 14, 22, 29},
    CEREMONY_SANKHU_STAPANA: _RIKTA | {7, 14, 22, 29},
}

# ── Masa Shuddhi — forbidden lunar months ────────────────────────────────────
# Chaturmas core prohibition (Dharmasindhu): Ashadha, Shravana, Bhadrapada,
# Ashvina (four months of Vishnu's sleep, ending at Kartika Shukla Ekadashi).
# Any Adhika (intercalary) masa is forbidden for all samskaras.
#
# Telugu tradition:
#   Vivaha — NO Chaturmasya restriction. Weddings are permitted in any
#     non-Adhika masa; the masa choice is governed only by preferred
#     vivaha months (Vaisakha, Jyeshtha, Magha, Phalguna etc.).
#   Upanayanam — restricted to Uttarayanam entirely (see _UTTARAYANAM_ONLY);
#     the _CHATURMAS_MASAM entry is therefore empty (no additional masa ban).
_CHATURMAS_MASAM: dict[str, set[str]] = {
    CEREMONY_VIVAHA:         set(),   # No Chaturmasya ban — Telugu tradition
    CEREMONY_GRUHA_PRAVESAM: {"Ashadha", "Shravana", "Bhadrapada", "Ashvina"},
    CEREMONY_UPANAYANAM:     set(),   # Covered fully by _UTTARAYANAM_ONLY
    CEREMONY_POOJA:          set(),
    CEREMONY_YUDDHAM:        set(),
    CEREMONY_ANNA_PRASANA:   set(),
    CEREMONY_CHELAMU:        set(),
    CEREMONY_KOTTA_BATTALU:  set(),
    CEREMONY_PRAYANAM:       set(),
    CEREMONY_VIDYARAMBHAM:   set(),
    CEREMONY_OSHADHA_SEVA:   set(),
    CEREMONY_NAMAKARANAM:    set(),
    CEREMONY_GARBHADANAM:    {"Ashadha", "Shravana", "Bhadrapada", "Ashvina"},
    CEREMONY_SANKHU_STAPANA: {"Ashadha", "Shravana", "Bhadrapada", "Ashvina"},
}

# ── Ayanam restriction — ceremonies permitted only in Uttarayanam ────────────
# Uttarayanam: Sun longitude 0°–179° (Mesha through Kanya, ~mid-Jan to mid-Jul).
# Dakshinayanam: Sun longitude 180°–359° (Tula through Meena, ~mid-Jul to mid-Jan).
#
# Source: Dharmasindhu, Muhurta Chintamani, Venkatrama & Co. Telugu Panchangam.
# Upanayanam is universally restricted to Uttarayanam in Smarta/Telugu tradition.
# Gruha Pravesam is NOT in this set — while Uttarayanam is preferred, Telugu tradition
# widely performs Gruha Pravesam in Karthika/Margashira (Dakshinayanam months), which is
# culturally accepted.
_UTTARAYANAM_ONLY: set[str] = {
    CEREMONY_UPANAYANAM,
}

# ── Vaara (weekday) restrictions ──────────────────────────────────────────────
# Source: MC Ch.1 (general Vaara Shuddhi), Ch.6 (Vivaha), Ch.8 (Upanayanam),
#         Ch.9 (Gruha Pravesam), Dharmasindhu §samskaras, VTP Rajahmundry.
# Bad vaaras for most samskaras: Sunday(0), Tuesday(2), Saturday(6).
# Upanayanam: Saturday allowed — Shani = discipline, austerity, appropriate for
#   brahmacharya vow initiation; only Sun and Tue are prohibited.
# Yuddham: inverts — gentle days (Thu/Fri) are bad; fierce days (Sun/Tue/Sat) are good.
# Prayanam, Kotta Battalu: only Saturday restricted (Saturn = obstacles/delays for travel).
_BAD_VAARAS: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         {0, 2, 6},
    CEREMONY_GRUHA_PRAVESAM: {0, 2, 6},
    CEREMONY_UPANAYANAM:     {2},             # Only Tue(2) blocked; Sun/Sat allowed per Telugu Sampradayam
    CEREMONY_ANNA_PRASANA:   {0, 2, 6},
    CEREMONY_NAMAKARANAM:    {0, 2, 6},
    CEREMONY_GARBHADANAM:    {0, 2, 6},
    CEREMONY_CHELAMU:        {0, 2, 6},
    CEREMONY_VIDYARAMBHAM:   {0, 2, 6},
    CEREMONY_KOTTA_BATTALU:  {6},
    CEREMONY_PRAYANAM:       {6},             # Only Saturday; even Sun/Tue allowed for travel
    CEREMONY_OSHADHA_SEVA:   {0, 2, 6},
    CEREMONY_SANKHU_STAPANA: {0, 6},          # Sun and Sat; Tue(2) allowed per MC §Griha-arambha
    CEREMONY_YUDDHAM:        {4, 5},          # Thu(4) and Fri(5) — saumya days bad for battle
    CEREMONY_POOJA:          set(),
}

# ── Vara-Nakshatra Vedha (for Prayanam / travel) ───────────────────────────────
# On each weekday, the 3 nakshatras ruled by that day's planet are "vedha'd"
# (inauspicious for travel) even if they are otherwise in the good-nakshatra set.
# Source: MC Ch.10 §Prayana-nakshatra-vedha; VTP travel advisory columns.
# Ketu(naks 0,9,18) and Rahu(naks 5,14,23) have no weekday — never vedha'd.
_PRAYANAM_VAARA_VEDHA: dict[int, set[int]] = {
    0: {2, 11, 20},   # Sunday   (Surya)   → Krittika, UttaraPhalguni, UttaraAshadha
    1: {3, 12, 21},   # Monday   (Chandra) → Rohini, Hasta, Shravana
    2: {4, 13, 22},   # Tuesday  (Mangala) → Mrigashira, Chitra, Dhanishtha
    3: {8, 17, 26},   # Wednesday(Budha)   → Ashlesha, Jyeshtha, Revati
    4: {6, 15, 24},   # Thursday (Guru)    → Punarvasu, Vishakha, PurvaBhadrapada
    5: {1, 10, 19},   # Friday   (Shukra)  → Bharani, PurvaPhalguni, PurvaAshadha
    6: {7, 16, 25},   # Saturday (Shani)   → Pushya, Anuradha, UttaraBhadrapada
}

# ── Prayanam: Anandadi Yoga (VTP Rajahmundry + Muhurta Chintamani §Prayana) ──────
# Title: "ప్రయాణమునకు ఆనందాది యోగముల పట్టిక" (Table of Anandadi Yogas for Travel)
#
# Classical source: Muhurta Chintamani Prayana Prakarana:
#   "Ananda-Gandharva-Gada-Matanga-Rakshasa-Mitrakapi iti ṣaḍ yogāḥ"
#   Six Anandadi yogas cycle across all 27 nakshatras × 7 weekdays.
#
# Formula: yoga_idx = (nakshatra_idx - weekday_idx × 4) % 6
# Starting nakshatra for yoga Ananda per weekday (shifts by 4):
#   Sun=Ashvini(0), Mon=Mrigashira(4), Tue=Ashlesha(8), Wed=Hasta(12),
#   Thu=Anuradha(16), Fri=UttaraAshadha(20), Sat=PurvaBhadra(24).
#
# Source: Muhurta Chintamani (MC) §Prayana; confirmed by VTP Rajahmundry panchangam
#   image and cross-referenced against multiple Telugu Panchangam publications.
_ANANDADI_YOGA_NAMES: list[str] = [
    "Ananda",    # 0 — Auspicious (joy, success)
    "Gandharva", # 1 — Auspicious (pleasant journey)
    "Gada",      # 2 — Avoid first 24 minutes
    "Matanga",   # 3 — Auspicious (power, success)
    "Rakshasa",  # 4 — AVOID completely (demonic influence)
    "Mitrakapi", # 5 — Auspicious (friendly outcome)
]

# Telugu names for display
_ANANDADI_YOGA_TE: dict[str, str] = {
    "Ananda":    "ఆనంద",
    "Gandharva": "గంధర్వ",
    "Gada":      "గడా",
    "Matanga":   "మాతంగ",
    "Rakshasa":  "రాక్షస",
    "Mitrakapi": "మిత్రకపి",
}

# Quality tiers (MC §Prayana, VTP table note)
_ANANDADI_AVOID:  frozenset[str] = frozenset({"Rakshasa"})
_ANANDADI_24MIN:  frozenset[str] = frozenset({"Gada"})


def get_anandadi_yoga(nak_idx: int, weekday_idx: int) -> tuple[str, str]:
    """Return (yoga_name, quality_tier) for Prayanam Anandadi yoga.

    Formula: yoga_idx = (nakshatra_idx - weekday_idx × 4) % 6
    weekday_idx: 0=Sunday … 6=Saturday.
    quality_tier: "avoid" | "restrict_24min" | "auspicious"
    Source: Muhurta Chintamani §Prayana + VTP Rajahmundry panchangam.
    """
    yoga_idx  = (nak_idx - weekday_idx * 4) % 6
    yoga_name = _ANANDADI_YOGA_NAMES[yoga_idx]
    if yoga_name in _ANANDADI_AVOID:
        tier = "avoid"
    elif yoga_name in _ANANDADI_24MIN:
        tier = "restrict_24min"
    else:
        tier = "auspicious"
    return yoga_name, tier


# ── Amritadi Yoga — Nakshatra × Weekday table ─────────────────────────────────
# "అమృతాది యోగముల పట్టిక" — General auspiciousness grid used for Prayanam and
# all samskaras in Telugu Panchangam tradition.
#
# Source: VTP Rajahmundry panchangam — directly transcribed from printed table.
# Cross-verified: UttaraAshadha/Sun=Amrita ✓, Dhanishtha/Sun=Mrityu ✓
#                 UttaraPhalguni/Sun=Amrita ✓ (corrected from earlier web-sourced table)
#
# Rows = nakshatra index 0 (Ashvini) … 26 (Revati)
# Cols = weekday 0 (Sun) … 6 (Sat)
# Values: 0=Amrita, 1=Siddha, 2=PrabalaArishta, 3=Mrityu
#   Amrita         — most auspicious (అమ్య) ✓
#   Siddha         — auspicious (సిద్ధ) ✓
#   PrabalaArishta — inauspicious; block (ప్రబలారిష్ట) ✗
#   Mrityu         — inauspicious; block (మృత్యు) ✗
_AMRITADI_TABLE: list[tuple[int, ...]] = [
    # Sun  Mon  Tue  Wed  Thu  Fri  Sat
    (1,   1,   1,   3,   0,   0,   1),  #  0 Ashvini
    (2,   1,   1,   1,   1,   1,   1),  #  1 Bharani
    (1,   3,   1,   0,   3,   1,   0),  #  2 Krittika
    (1,   0,   0,   1,   3,   1,   0),  #  3 Rohini
    (1,   0,   1,   1,   0,   1,   1),  #  4 Mrigashira
    (1,   1,   3,   1,   3,   1,   1),  #  5 Ardra
    (1,   0,   1,   1,   0,   1,   1),  #  6 Punarvasu
    (1,   1,   1,   1,   0,   3,   1),  #  7 Pushya
    (1,   1,   1,   1,   1,   3,   3),  #  8 Ashlesha
    (3,   3,   1,   1,   0,   0,   0),  #  9 Magha
    (1,   1,   1,   0,   1,   1,   1),  # 10 PurvaPhalguni
    (0,   1,   0,   0,   3,   1,   3),  # 11 UttaraPhalguni  ← Sun=Amrita ✓
    (0,   1,   1,   3,   1,   0,   3),  # 12 Hasta
    (1,   2,   1,   1,   1,   1,   3),  # 13 Chitra
    (1,   0,   1,   1,   0,   1,   0),  # 14 Swati
    (3,   3,   3,   1,   1,   1,   1),  # 15 Vishakha
    (3,   1,   1,   1,   1,   1,   1),  # 16 Anuradha
    (3,   1,   1,   1,   2,   3,   1),  # 17 Jyeshtha
    (0,   1,   0,   3,   1,   0,   1),  # 18 Moola
    (1,   2,   1,   0,   1,   2,   1),  # 19 PurvaAshadha
    (0,   3,   2,   0,   1,   1,   1),  # 20 UttaraAshadha   ← Sun=Amrita ✓
    (0,   0,   1,   1,   1,   3,   1),  # 21 Shravana
    (3,   1,   1,   2,   1,   1,   1),  # 22 Dhanishtha      ← Sun=Mrityu ✓
    (1,   1,   3,   1,   3,   1,   0),  # 23 Shatabhisha
    (1,   3,   3,   0,   1,   1,   3),  # 24 PurvaBhadra
    (0,   1,   0,   1,   1,   1,   1),  # 25 UttaraBhadra
    (0,   1,   1,   3,   1,   0,   2),  # 26 Revati
]

_AMRITADI_NAMES_EN: list[str] = ["Amrita", "Siddha", "PrabalaArishta", "Mrityu"]
_AMRITADI_NAMES_TE: list[str] = ["అమృత",  "సిద్ధ",  "ప్రబలారిష్ట",    "మృత్యు"]
_AMRITADI_BAD: frozenset[int] = frozenset({2, 3})   # PrabalaArishta, Mrityu


def get_amritadi_yoga(nak_idx: int, weekday_idx: int) -> tuple[str, str, str]:
    """Return (name_en, name_te, quality_tier) for Amritadi yoga.

    quality_tier: "auspicious" | "avoid"
    Source: VTP Rajahmundry panchangam — directly transcribed.
    """
    val = _AMRITADI_TABLE[nak_idx][weekday_idx]
    tier = "avoid" if val in _AMRITADI_BAD else "auspicious"
    return _AMRITADI_NAMES_EN[val], _AMRITADI_NAMES_TE[val], tier


# ── Rahu Kalam / Yamaganda / Gulika segments ─────────────────────────────────
# Day (sunrise→sunset) divided into 8 equal parts; one part per weekday is inauspicious.
# sun_idx: 0=Sunday … 6=Saturday  (matches existing panchang.py convention)
# Source: Venkatrama & Co. + bidyashish/vedicpanchanga.com verified tables.
_RAHU_KALAM_SEGMENT:  dict[int, int] = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
_YAMAGANDA_SEGMENT:   dict[int, int] = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
_GULIKA_SEGMENT:      dict[int, int] = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}


def _kalam_window(rise_mins: float, set_mins: float, segment: int) -> dict:
    """Return {start, end} for the given 1-indexed day segment (1–8)."""
    part = (set_mins - rise_mins) / 8.0
    start = rise_mins + (segment - 1) * part
    end   = start + part
    def fmt(m: float) -> str:
        m = m % (24 * 60)
        return f"{int(m // 60):02d}:{int(m % 60):02d}"
    return {"start": fmt(start), "end": fmt(end)}


def compute_kalams(rise_mins: float, set_mins: float, sun_idx: int) -> dict:
    """Return Rahu Kalam, Yamaganda, and Gulika Kalam windows for a given day.

    All three are essential South Indian muhurta exclusion periods.
    South Indian rule: any ceremony during Gulika Kalam will repeat
    (marriage → second marriage), making it as critical as Rahu Kalam.
    """
    return {
        "rahu_kalam":   _kalam_window(rise_mins, set_mins, _RAHU_KALAM_SEGMENT[sun_idx]),
        "yamaganda":    _kalam_window(rise_mins, set_mins, _YAMAGANDA_SEGMENT[sun_idx]),
        "gulika_kalam": _kalam_window(rise_mins, set_mins, _GULIKA_SEGMENT[sun_idx]),
    }


def _masam_ok(masam_name: str, is_adhika: bool, ceremony_type: str) -> bool:
    """Return False if the lunar month is forbidden for this ceremony type."""
    if is_adhika:
        return False  # Adhika (intercalary) masa forbidden for all samskaras per Dharmasindhu
    return masam_name not in _CHATURMAS_MASAM.get(ceremony_type, set())


# Lagna Shuddhi — which position (from birth rashi, 0-indexed) the muhurtha lagna
# must NOT fall in, per traditional Telugu Panchangam (Image 1 of source notes).
# Dvitiya(1)=2nd, Tritiya(2)=3rd, Chaturthi(3)=4th, Panchami(4)=5th, Shashthi(5)=6th,
# Saptami(6)=7th, Ashtami(7)=8th, Navami(8)=9th, Dashami(9)=10th,
# Ekadashi(10)=11th, Dwadashi(11)=12th.
_RASHI_SHUDDHI_FORBIDDEN: dict[str, set[int]] = {
    CEREMONY_VIVAHA:         {6},    # Saptami Sudhi — 7th from bride's janma rashi
    CEREMONY_GRUHA_PRAVESAM: {11},   # Dwadashi Sudhi — 12th
    CEREMONY_UPANAYANAM:     {7},    # Ashtami Sudhi — 8th
    CEREMONY_POOJA:          set(),
    CEREMONY_YUDDHAM:        {10},   # Ekadashi Sudhi — 11th
    CEREMONY_ANNA_PRASANA:   {9},    # Dashami Sudhi — 10th
    CEREMONY_CHELAMU:        {8},    # Navami Sudhi — 9th
    CEREMONY_KOTTA_BATTALU:  {5},    # Shashthi Sudhi — 6th
    CEREMONY_PRAYANAM:       {4},    # Panchami Sudhi — 5th
    CEREMONY_VIDYARAMBHAM:   {3},    # Chaturthi Sudhi — 4th
    CEREMONY_OSHADHA_SEVA:   {2},    # Tritiya Sudhi — 3rd
    CEREMONY_NAMAKARANAM:    {1},    # Dvitiya Sudhi — 2nd
    CEREMONY_GARBHADANAM:    set(),  # Lagna Sudhi — general lagna purity (handled by panchaka)
    CEREMONY_SANKHU_STAPANA: {3, 7}, # Chaturthi+Ashtami — 4th AND 8th
}

# Display name for the Lagna Shuddhi rule used for each ceremony (for UI page 3)
_SUDHI_NAME_TE: dict[str, str] = {
    CEREMONY_VIVAHA:         "సప్తమ సుద్ధి (7వ స్థానం)",
    CEREMONY_GRUHA_PRAVESAM: "ద్వాదశ సుద్ధి (12వ స్థానం)",
    CEREMONY_UPANAYANAM:     "అష్టమ సుద్ధి (8వ స్థానం)",
    CEREMONY_POOJA:          "",
    CEREMONY_YUDDHAM:        "ఏకాదశ సుద్ధి (11వ స్థానం)",
    CEREMONY_ANNA_PRASANA:   "దశమ సుద్ధి (10వ స్థానం)",
    CEREMONY_CHELAMU:        "నవమ సుద్ధి (9వ స్థానం)",
    CEREMONY_KOTTA_BATTALU:  "షష్ట సుద్ధి (6వ స్థానం)",
    CEREMONY_PRAYANAM:       "పంచమ సుద్ధి (5వ స్థానం)",
    CEREMONY_VIDYARAMBHAM:   "చతుర్థ సుద్ధి (4వ స్థానం)",
    CEREMONY_OSHADHA_SEVA:   "తృతీయ సుద్ధి (3వ స్థానం)",
    CEREMONY_NAMAKARANAM:    "ద్వితీయ సుద్ధి (2వ స్థానం)",
    CEREMONY_GARBHADANAM:    "లగ్న సుద్ధి",
    CEREMONY_SANKHU_STAPANA: "చతుర్థ+అష్టమ సుద్ధి (4వ,8వ స్థానాలు)",
}


def _rashi_shuddhi_ok(day_rashi: int, janma_rashi: int, ceremony_type: str) -> bool:
    """Return True if the Moon's rashi on the ceremony day is not in a forbidden position.

    Source: Image 1 (Lagna Shuddhi) from the user-uploaded handwritten Telugu notes.
    - Vivaha: Saptama Shuddhi — avoid 7th rashi from Janma Rashi (Saptama = partnerships house)
    - Upanayanam: Ashtama Shuddhi — avoid 8th rashi from Janma Rashi (8th = obstacles/longevity)
    """
    pos = (day_rashi - janma_rashi) % 12
    return pos not in _RASHI_SHUDDHI_FORBIDDEN.get(ceremony_type, set())


_TARA_NAMES_TE = ["జన్మ", "సంపత్", "విపత్", "క్షేమ", "ప్రత్యక్", "సాధన", "నైధన", "మిత్ర", "పరమ మిత్ర"]


def _tara_ok(janma_nak: int, day_nak: int) -> bool:
    """Return True if the day nakshatra is auspicious for this person's janma nakshatra.

    Computes 1-indexed Tara position (Tara Balam) cyclically (1–9, repeating
    across all 27 nakshatras) and rejects:
    1=Janma, 3=Vipat, 5=Pratyak, 7=Naidhana.
    """
    offset = (day_nak - janma_nak) % 27
    tara = (offset % 9) + 1   # 1-9, cyclical across all 27 nakshatras
    return tara not in {1, 3, 5, 7}


def _panchaka_ok(naks_idx: int, sun_idx: int, tithi_idx: int, lagna_idx: int) -> bool:
    """Return True if there is no Panchaka Dosha (South Indian formula).

    Formula (all 1-indexed, using FULL tithi 1–30):
        (vaara + tithi + nakshatra + lagna) % 9
    Safe remainders: {0, 3, 5, 7} = Panchaka Rahita.
    Dosha remainders: {1=Mrityu, 2=Agni, 4=Raja, 6=Chora, 8=Roga}.
    Source: Astro-Engine/Astro_Engine_ORGNL docs/02_SOUTH_INDIAN_TRADITIONS.md.
    """
    vaara_1 = sun_idx + 1     # Sunday=1 … Saturday=7
    tithi_1 = tithi_idx + 1   # 1–30 (Shukla Prathama=1 … Amavasya=30)
    nak_1   = naks_idx + 1    # 1–27
    lagna_1 = lagna_idx + 1   # 1–12
    result  = (vaara_1 + tithi_1 + nak_1 + lagna_1) % 9
    return result in {0, 3, 5, 7}


def is_auspicious(
    naks_idx: int,
    tithi_idx: int,
    sun_idx: int,
    lagna_idx: int,
    birth_charts: list[dict],
    ceremony_type: str,
    masam_name: str = "",
    is_adhika_masam: bool = False,
    day_rashi_idx: int = -1,
    is_uttarayanam: bool | None = None,
    is_night: bool = False,
    choghadiya_rank: int = -1,
    planet_rashis: "dict | None" = None,
) -> bool:
    """Return True if the given panchang state is auspicious for the ceremony.

    Checks in order:
    1. Ayanam restriction (Uttarayanam-only ceremonies)
    2. Vaara (weekday) Shuddhi
    3. Vara-Nakshatra Vedha (travel-specific day+nakshatra combination)
    4. Masa Shuddhi
    5. Good nakshatra
    6. Bad tithi
    7. Tara Balam
    8. Rashi Shuddhi
    9. Panchaka Dosha
    """
    if is_uttarayanam is not None and ceremony_type in _UTTARAYANAM_ONLY:
        if not is_uttarayanam:
            return False
    if sun_idx in _BAD_VAARAS.get(ceremony_type, set()):
        # Telugu Sampradaya: vara dosha is mitigated at night by either
        #   (a) Amrita Choghadiya — per Muhurta Chintamani, or
        #   (b) Guru (Jupiter) aspecting the lagna — per Jyotish Shastra
        if is_night and choghadiya_rank == 6:
            pass  # Amrita Choghadiya mitigation
        elif is_night and planet_rashis is not None and lagna_idx >= 0:
            guru_rashi = planet_rashis.get("guru", -1)
            if guru_rashi >= 0 and _guru_aspects_lagna(guru_rashi, lagna_idx):
                pass  # Guru-aspect mitigation
            else:
                return False
        else:
            return False
    if ceremony_type == CEREMONY_PRAYANAM:
        _, anandadi_tier = get_anandadi_yoga(naks_idx, sun_idx)
        if anandadi_tier == "avoid":
            return False
        _, _, amritadi_tier = get_amritadi_yoga(naks_idx, sun_idx)
        if amritadi_tier == "avoid":
            return False
    if masam_name and not _masam_ok(masam_name, is_adhika_masam, ceremony_type):
        return False
    # For Prayanam, the Amritadi table (VTP) already encodes nakshatra×weekday quality
    # and takes precedence over the standalone nakshatra shloka.
    # The nakshatra shloka is secondary when Amritadi = Amrita/Siddha (already verified above).
    if ceremony_type != CEREMONY_PRAYANAM:
        if naks_idx not in _GOOD_NAKSHATRAS.get(ceremony_type, set()):
            return False
    if tithi_idx in _BAD_TITHIS.get(ceremony_type, set()):
        return False
    for chart in birth_charts:
        if not _tara_ok(chart["janma_nakshatra_idx"], naks_idx):
            return False
    if day_rashi_idx >= 0:
        for chart in birth_charts:
            jrashi = chart.get("janma_rashi_idx", -1)
            if jrashi >= 0 and not _rashi_shuddhi_ok(day_rashi_idx, jrashi, ceremony_type):
                return False
    if not _panchaka_ok(naks_idx, sun_idx, tithi_idx, lagna_idx):
        return False
    return True


# ── Choghadiya ────────────────────────────────────────────────────────────────
# Index mapping: 0=Amrit, 1=Char, 2=Labh, 3=Shubh, 4=Udveg, 5=Kaal, 6=Rog
_CHO_TE   = ["అమృత", "చర", "లాభ", "శుభ", "ఉద్వేగ", "కాల", "రోగ"]
_CHO_RANK = [6,       3,     4,     5,      1,         1,      1    ]

# Rows = weekday (0=Sun … 6=Sat); columns = 8 day slots
_DAY_CHO = [
    [4, 1, 2, 0, 5, 3, 6, 4],  # Sun
    [0, 5, 3, 6, 4, 1, 2, 0],  # Mon
    [6, 4, 1, 2, 0, 5, 3, 6],  # Tue
    [2, 0, 5, 3, 6, 4, 1, 2],  # Wed
    [3, 6, 4, 1, 2, 0, 5, 3],  # Thu
    [1, 2, 0, 5, 3, 6, 4, 1],  # Fri
    [5, 3, 6, 4, 1, 2, 0, 5],  # Sat
]
# 8 night slots
_NIGHT_CHO = [
    [3, 0, 1, 6, 5, 4, 2, 3],  # Sun
    [1, 6, 5, 4, 2, 3, 0, 1],  # Mon
    [5, 4, 2, 3, 0, 1, 6, 5],  # Tue
    [4, 2, 3, 0, 1, 6, 5, 4],  # Wed
    [0, 1, 6, 5, 4, 2, 3, 0],  # Thu
    [6, 5, 4, 2, 3, 0, 1, 6],  # Fri
    [2, 3, 0, 1, 6, 5, 4, 2],  # Sat
]


def compute_choghadiya_slots(
    rise_jd: float,
    set_jd: float,
    next_rise_jd: float,
    weekday_idx: int,        # 0=Sun … 6=Sat
) -> list[dict]:
    """Return all 16 Choghadiya slots (8 day + 8 night) for a given date.

    Each slot dict: {from_jd, to_jd, quality_te, quality_rank}
    """
    day_slot   = (set_jd      - rise_jd)      / 8
    night_slot = (next_rise_jd - set_jd)       / 8
    slots: list[dict] = []
    for i, ci in enumerate(_DAY_CHO[weekday_idx]):
        slots.append({
            "from_jd":      rise_jd + i * day_slot,
            "to_jd":        rise_jd + (i + 1) * day_slot,
            "quality_te":   _CHO_TE[ci],
            "quality_rank": _CHO_RANK[ci],
        })
    for i, ci in enumerate(_NIGHT_CHO[weekday_idx]):
        slots.append({
            "from_jd":      set_jd + i * night_slot,
            "to_jd":        set_jd + (i + 1) * night_slot,
            "quality_te":   _CHO_TE[ci],
            "quality_rank": _CHO_RANK[ci],
        })
    return slots


# ── Lagna Graha Quality (scholar-level lagna analysis) ────────────────────────
# Sources: Muhurta Chintamani §Vivaha-Lagna, §Graha-Bala; Dharmasindhu §Samskaras;
#          Venkatrama & Co. Telugu Panchangam commentary (Rajahmundry).
#
# Key Vivaha rules from MC:
#   1. No natural malefic (Kuja/Mars, Shani/Saturn, Rahu, Ketu) in Lagna (1st house).
#   2. No natural malefic in 7th house (the house of spouse/partnership).
#   3. Guru (Jupiter) aspecting Lagna via 5th/7th/9th sight — paramount for Vivaha.
#   4. Shukra (Venus) should not be combust — Venus is the Vivaha karaka.
#   5. Chandra (Moon) should not be in 6th or 8th from Lagna.
#   6. Shukra in 2nd/5th/11th from Lagna — auspicious; 6th/8th/12th — inauspicious.

_GRAHA_SHORT_TE: dict[str, str] = {
    "ravi":    "రవి",
    "chandra": "చంద్రుడు",
    "kuja":    "కుజుడు",
    "budha":   "బుధుడు",
    "guru":    "గురువు",
    "shukra":  "శుక్రుడు",
    "shani":   "శని",
    "rahu":    "రాహువు",
    "ketu":    "కేతువు",
}

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

# Natural malefics (papa grahas)
_PAPA_GRAHAS: frozenset[str] = frozenset({"kuja", "shani", "rahu", "ketu"})

# Combustion orbs in degrees — planet is combust when within this distance of the Sun
# Source: Muhurta Chintamani / classical Jyotish standards.
_COMBUSTION_ORB: dict[str, float] = {
    "chandra": 12.0,
    "kuja":    17.0,
    "budha":   14.0,
    "guru":    11.0,
    "shukra":  10.0,
    "shani":   15.0,
}

# House ordinals in Telugu
_HOUSE_ORD_TE: dict[int, str] = {
    1: "1వ", 2: "2వ", 3: "3వ", 4: "4వ",
    5: "5వ", 6: "6వ", 7: "7వ", 8: "8వ",
    9: "9వ", 10: "10వ", 11: "11వ", 12: "12వ",
}

_HOUSE_ORD_EN: dict[int, str] = {
    1: "1st", 2: "2nd",  3: "3rd",  4: "4th",
    5: "5th", 6: "6th",  7: "7th",  8: "8th",
    9: "9th", 10: "10th", 11: "11th", 12: "12th",
}


def _is_combust(planet: str, planet_lon: float, sun_lon: float) -> bool:
    """Return True if planet is within its combustion distance of the Sun."""
    orb = _COMBUSTION_ORB.get(planet)
    if orb is None:
        return False
    diff = abs(planet_lon - sun_lon) % 360
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def _guru_aspects_lagna(guru_rashi: int, lagna_idx: int) -> bool:
    """Return True if Jupiter (Guru) aspects the given lagna rashi.

    Jupiter casts special aspects to the 5th, 7th, and 9th from its position
    (in addition to the universal 7th aspect shared by all planets).
    Source: Jyotish Shastra — Brihad Parasara Hora Shastra §Graha-drishti.
    """
    return lagna_idx in {
        (guru_rashi + 4) % 12,  # 5th house
        (guru_rashi + 6) % 12,  # 7th house
        (guru_rashi + 8) % 12,  # 9th house
    }


# Lagna classification by sign type
# Sthira (fixed/stable): best for permanent ceremonies (vivaha, gruha pravesam)
# Chara (moveable): preferred for travel; less ideal for vivaha
# Dvisva (dual/mutable): neutral
_STHIRA_LAGNAS = frozenset({1, 4, 7, 10})   # Vrishabha, Simha, Vrischika, Kumbha
_CHARA_LAGNAS  = frozenset({0, 3, 6, 9})    # Mesha, Karka, Tula, Makara
# dvisva: 2, 5, 8, 11 (Mithuna, Kanya, Dhanu, Meena)

# Per-ceremony lagna graha rules. Values:
#   "hard"    — triggers block, window is eliminated
#   "warn"    — soft warning shown to user, window kept
#   "benefit" — positive factor shown to user
#   "none"    — check is skipped entirely
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

_LAGNA_RULES_DEFAULT: dict[str, str] = {
    "guru_aspect_lagna": "benefit",
}


def check_lagna_graha_quality(
    lagna_idx: int,
    planet_rashis: dict[str, int],
    ceremony_type: str,
    planet_longitudes: "dict[str, float] | None" = None,
) -> dict:
    """Evaluate the auspiciousness of the ceremony lagna based on graha positions.

    Sources: Muhurta Chintamani §Vivaha-Lagna; Dharmasindhu §Samskaras;
             Venkatrama & Co. Telugu Panchangam; Brihad Parasara Hora Shastra.

    Args:
        lagna_idx: 0-indexed lagna rashi (0=Mesha … 11=Meena).
        planet_rashis: dict from compute_planet_rashis().
        ceremony_type: e.g. "vivaha", "gruha_pravesam".
        planet_longitudes: exact sidereal degrees from compute_planet_longitudes()
            (optional; required only for Venus combustion check).

    Returns dict with:
        score: int 0–100 (higher = better)
        blocked: bool (True when any hard-block rule fires)
        hard_blocks_te: list[str] — disqualifying Telugu messages
        warnings_te: list[str] — soft Telugu warnings
        benefits_te: list[str] — positive Telugu benefit messages
    """
    if not planet_rashis:
        return {
            "score": 50, "blocked": False,
            "hard_blocks_te": [], "warnings_te": [], "benefits_te": [],
            "score_components": [{"te": "ప్రాథమిక బేస్ స్కోర్", "delta": 50}],
        }

    rules = _LAGNA_RULES.get(ceremony_type, _LAGNA_RULES_DEFAULT)

    def _rule(key: str) -> str:
        return rules.get(key, "none")

    def _house(p_rashi: int) -> int:
        """1-indexed house from lagna (1 = lagna, 7 = 7th, etc.)."""
        return (p_rashi - lagna_idx) % 12 + 1

    hard_blocks: list[str] = []
    warnings: list[str] = []
    benefits: list[str] = []
    score_components: list[dict] = [{"te": "ప్రాథమిక బేస్ స్కోర్", "delta": 50, "en": "Base score"}]
    score = 50  # neutral baseline

    def _add(delta: int, te: str, en: str = "") -> None:
        score_components.append({"te": te, "delta": delta, "en": en})

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

    # 3.5. Guru (Jupiter) combustion — Guru Asta ──────────────────────────────
    # When Jupiter is within 11° of the Sun, it is considered "asta" (combust/hidden).
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

    # 4. Guru (Jupiter) aspects lagna ─────────────────────────────────────────
    if _rule("guru_aspect_lagna") != "none":
        guru_rashi = planet_rashis.get("guru", -1)
        if guru_rashi >= 0 and _guru_aspects_lagna(guru_rashi, lagna_idx):
            msg_te = "గురువు లగ్నాన్ని వీక్షిస్తున్నాడు — శుభ దృష్టి ✓"
            benefits.append(msg_te)
            score += 25
            _add(+25, msg_te, "Jupiter aspects Lagna — Auspicious aspect ✓")

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

    # 8. Sthira (fixed) lagna — preferred for permanent ceremonies ────────────
    # Per Muhurta Chintamani: Sthira lagnas (Vrishabha, Simha, Vrischika, Kumbha)
    # give permanence and stability; ranked above dual and moveable signs.
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

    return {
        "score":            max(0, min(150, score)),
        "blocked":          bool(hard_blocks),
        "hard_blocks_te":   hard_blocks,
        "warnings_te":      warnings,
        "benefits_te":      benefits,
        "score_components": score_components,
    }
