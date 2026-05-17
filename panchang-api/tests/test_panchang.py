import pytest
from compute.astro import local_date_to_jd
from compute.panchang import compute_panchang

LAT, LON = 17.38, 78.49
TZ = "Asia/Kolkata"


def pan(year, month, day):
    jd = local_date_to_jd(year, month, day, TZ)
    return compute_panchang(jd, LAT, LON, TZ)


def test_samvatsara_2026():
    p = pan(2026, 5, 17)
    assert p["samvatsara"]["en"] == "Parabhava"


def test_samvatsara_2025():
    p = pan(2025, 6, 1)
    assert p["samvatsara"]["en"] == "Vishvavasu"


def test_samvatsara_before_ugadi_2025():
    # requires pyswisseph — verified by algorithm trace:
    # Feb 1 2025 → masam_idx=9 (Pushya) → sam_year=2024 → saka=1946 → idx=37 → "Krodhi"
    # (NOT "Vishvavasu", which would be wrong if we naively used year 2025)
    p = pan(2025, 2, 1)
    assert p["samvatsara"]["en"] == "Krodhi"


def test_samvatsara_2024():
    p = pan(2024, 6, 1)
    assert p["samvatsara"]["en"] == "Krodhi"


def test_adhika_jyeshtha_may_2026():
    p = pan(2026, 5, 17)
    assert p["masam"]["en"] == "Jyeshtha"
    assert p["masam"]["adhika"] is True


def test_rutu_grishma_may_2026():
    p = pan(2026, 5, 17)
    assert p["rutu"]["en"] == "Grishma"


def test_ayanam_uttarayanam_may_2026():
    p = pan(2026, 5, 17)
    assert p["ayanam"]["en"] == "Uttarayanam"


def test_paksham_shukla():
    # 2026-05-17 is Shukla paksham
    p = pan(2026, 5, 17)
    assert p["paksham"]["en"] == "Shukla Paksham"


def test_tithi_panchami():
    p = pan(2026, 5, 17)
    assert p["tithi"]["en"] == "Panchami"


def test_vaaram_sunday():
    # 2026-05-17 is a Sunday
    p = pan(2026, 5, 17)
    assert p["vaaram"]["en"] == "Sunday"


def test_nakshatra_range():
    p = pan(2026, 5, 17)
    assert p["nakshatra"]["en"] in [
        "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati",
        "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    ]


def test_sunrise_sunset_format():
    p = pan(2026, 5, 17)
    import re
    assert re.match(r"\d{2}:\d{2}", p["sunrise"])
    assert re.match(r"\d{2}:\d{2}", p["sunset"])
