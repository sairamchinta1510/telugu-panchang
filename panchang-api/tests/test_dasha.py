"""Tests for Vimshottari dasha computation."""
import sys
from datetime import datetime, timezone


def _load_dasha():
    """Load dasha module without swisseph dependency."""
    for mod in list(sys.modules):
        if "dasha" in mod:
            del sys.modules[mod]
    import importlib
    import compute.dasha as d

    importlib.reload(d)
    return d


def _birth_dt(year, month, day, hour=0, minute=0):
    """UTC-aware datetime for tests."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_dasha_sequence_sums_to_120_years():
    d = _load_dasha()
    assert sum(d.DASHA_YEARS.values()) == 120


def test_nakshatra_lord_rohini():
    """Rohini is nakshatra 3; lord_idx = 3 % 9 = 3 → 'chandra'."""
    d = _load_dasha()
    moon_lon = 44.0
    nak_idx = int(moon_lon / (360 / 27))
    assert nak_idx == 3
    assert d.DASHA_SEQUENCE[nak_idx % 9] == "chandra"


def test_balance_at_start_of_nakshatra():
    """Moon exactly at nakshatra start → full dasha years remaining."""
    d = _load_dasha()
    moon_lon = 40.0
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(moon_lon, birth_dt)
    assert dashas[0]["lord"] == "chandra"
    assert abs(dashas[0]["years"] - 10.0) < 0.01


def test_balance_at_midpoint_of_nakshatra():
    """Moon at nakshatra midpoint → half the dasha years remaining."""
    d = _load_dasha()
    moon_lon = 40.0 + (360 / 27) / 2
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(moon_lon, birth_dt)
    assert dashas[0]["lord"] == "chandra"
    assert abs(dashas[0]["years"] - 5.0) < 0.05


def test_returns_nine_mahadashas():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    assert len(dashas) == 9


def test_each_mahadasha_has_nine_antardashas():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    for maha in dashas:
        assert len(maha["antardashas"]) == 9, f"{maha['lord']} has {len(maha['antardashas'])} antardashas"


def test_antardasha_dates_are_contiguous():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    maha = dashas[1]
    ads = maha["antardashas"]
    for i in range(len(ads) - 1):
        assert ads[i]["end"] == ads[i + 1]["start"], f"Gap between antardasha {i} and {i+1}"


def test_mahadasha_dates_are_contiguous():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    for i in range(len(dashas) - 1):
        assert dashas[i]["end_date"] == dashas[i + 1]["start_date"]


def test_antardasha_years_sum_to_mahadasha_years():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    maha = dashas[1]
    ad_days = sum(
        (datetime.fromisoformat(a["end"]) - datetime.fromisoformat(a["start"])).days
        for a in maha["antardashas"]
    )
    maha_days = (
        datetime.fromisoformat(maha["end_date"])
        - datetime.fromisoformat(maha["start_date"])
    ).days
    assert abs(ad_days - maha_days) <= 1


def test_first_mahadasha_starts_at_birth():
    d = _load_dasha()
    birth_dt = _birth_dt(1990, 8, 15)
    dashas = d.compute_vimshottari_dasha(44.0, birth_dt)
    assert dashas[0]["start_date"] == "1990-08-15"


def test_response_includes_telugu_name_and_emoji():
    d = _load_dasha()
    dashas = d.compute_vimshottari_dasha(44.0, _birth_dt(1990, 8, 15))
    chandra = dashas[0]
    assert chandra["lord_te"] == "చంద్ర"
    assert chandra["lord_emoji"] == "🌙"
    assert chandra["antardashas"][0]["lord_te"] == "చంద్ర"
