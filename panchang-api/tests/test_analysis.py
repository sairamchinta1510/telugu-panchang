"""Tests for compute.analysis module."""
import pytest


def _load():
    import importlib, compute.analysis as m
    importlib.reload(m)
    return m


# ── enrich_planet_details ──────────────────────────────────────────────────────

def test_enrich_adds_nakshatra():
    m = _load()
    details = {"ravi": {"rashi_idx": 0, "deg": 10, "min": 0, "retrograde": False}}
    enriched = m.enrich_planet_details(details)
    assert "nakshatra_idx" in enriched["ravi"]
    assert "nakshatra_te" in enriched["ravi"]
    assert "nakshatra_lord" in enriched["ravi"]


def test_enrich_adds_navamsa():
    m = _load()
    details = {"ravi": {"rashi_idx": 0, "deg": 5, "min": 0, "retrograde": False}}
    enriched = m.enrich_planet_details(details)
    assert "navamsa_rashi_idx" in enriched["ravi"]
    assert 0 <= enriched["ravi"]["navamsa_rashi_idx"] <= 11


def test_exalted_sun():
    m = _load()
    # Sun exalted in Mesha (0)
    details = {"ravi": {"rashi_idx": 0, "deg": 10, "min": 0, "retrograde": False}}
    enriched = m.enrich_planet_details(details)
    assert enriched["ravi"]["strength"] == "exalted"


def test_debilitated_sun():
    m = _load()
    # Sun debilitated in Tula (6)
    details = {"ravi": {"rashi_idx": 6, "deg": 10, "min": 0, "retrograde": False}}
    enriched = m.enrich_planet_details(details)
    assert enriched["ravi"]["strength"] == "debilitated"


def test_own_sign_moon():
    m = _load()
    # Moon owns Karkataka (3)
    details = {
        "ravi": {"rashi_idx": 4, "deg": 15, "min": 0, "retrograde": False},
        "chandra": {"rashi_idx": 3, "deg": 10, "min": 0, "retrograde": False},
    }
    enriched = m.enrich_planet_details(details)
    assert enriched["chandra"]["strength"] == "own"


def test_combust_mars():
    m = _load()
    # Mars combust: within 17° of Sun
    # Sun at Mesha 10° (lon=10), Mars at Mesha 20° (lon=20) → diff=10 < 17
    details = {
        "ravi": {"rashi_idx": 0, "deg": 10, "min": 0, "retrograde": False},
        "kuja": {"rashi_idx": 0, "deg": 20, "min": 0, "retrograde": False},
    }
    enriched = m.enrich_planet_details(details)
    assert enriched["kuja"]["strength"] == "combust"


# ── Graha Drishti ─────────────────────────────────────────────────────────────

def test_seventh_aspect_all_planets():
    m = _load()
    # Sun in Mesha (0), Moon in Tula (6) → Sun aspects Moon via 7th
    rashis = {"ravi": 0, "chandra": 6}
    aspects = m.compute_graha_drishti(rashis)
    sun_to_moon = [a for a in aspects if a["from"] == "ravi" and a["to"] == "chandra"]
    assert len(sun_to_moon) == 1
    assert sun_to_moon[0]["aspect_house"] == 7


def test_jupiter_fifth_aspect():
    m = _load()
    # Guru in Mesha (0), target 5th = Simha (4)
    rashis = {"guru": 0, "ravi": 4}
    aspects = m.compute_graha_drishti(rashis)
    guru_5th = [a for a in aspects if a["from"] == "guru" and a["aspect_house"] == 5]
    assert len(guru_5th) == 1


def test_saturn_third_aspect():
    m = _load()
    # Shani in Mesha (0), 3rd = Mithuna (2)
    rashis = {"shani": 0, "budha": 2}
    aspects = m.compute_graha_drishti(rashis)
    shani_3rd = [a for a in aspects if a["from"] == "shani" and a["aspect_house"] == 3]
    assert len(shani_3rd) == 1


# ── Parivartana Yoga ─────────────────────────────────────────────────────────

def test_parivartana_detected():
    m = _load()
    # Sun in Dhanus (8=Guru's sign), Guru in Simha (4=Sun's sign)
    rashis = {"ravi": 8, "guru": 4, "chandra": 1, "kuja": 0,
              "budha": 5, "shukra": 6, "shani": 9}
    yogas = m.compute_parivartana_yogas(rashis, lagna_idx=0)
    pairs = {(y["planet_a"], y["planet_b"]) for y in yogas}
    assert ("ravi", "guru") in pairs or ("guru", "ravi") in pairs


def test_no_parivartana_when_absent():
    m = _load()
    # All planets in own signs — no exchange possible
    rashis = {"ravi": 4, "chandra": 3, "kuja": 0, "budha": 5,
              "guru": 8, "shukra": 1, "shani": 9}
    yogas = m.compute_parivartana_yogas(rashis, lagna_idx=0)
    assert yogas == []


# ── Mangala Dosha ─────────────────────────────────────────────────────────────

def test_mangala_dosha_from_lagna():
    m = _load()
    # Mars in 7th house from lagna (lagna=0, Mars in rashi 6 → house 7)
    rashis = {"kuja": 6, "chandra": 3, "shukra": 1}
    result = m.compute_mangala_dosha(rashis, lagna_idx=0)
    assert result["present"] is True
    assert result["from_lagna"] is True


def test_no_mangala_dosha():
    m = _load()
    # Mars in 3rd house (not a dosha house)
    rashis = {"kuja": 2, "chandra": 5, "shukra": 8}
    result = m.compute_mangala_dosha(rashis, lagna_idx=0)
    # 3rd is not a dosha house; check from moon (kuja in rashi 2, moon in 5 → house = (2-5)%12+1=10) and venus
    assert result["from_lagna"] is False


def test_mangala_dosha_cancelled_own_sign():
    m = _load()
    # Kuja in Mesha (own sign, rashi 0) — dosha cancelled regardless of house
    rashis = {"kuja": 0, "chandra": 3, "shukra": 1}
    result = m.compute_mangala_dosha(rashis, lagna_idx=6)  # Kuja in 7th house from Tula lagna
    assert result["present"] is False
    assert result.get("cancelled") is True


def test_mangala_dosha_cancelled_vrischika():
    m = _load()
    # Kuja in Vrischika (own sign, rashi 7) — dosha cancelled
    rashis = {"kuja": 7, "chandra": 3, "shukra": 1}
    result = m.compute_mangala_dosha(rashis, lagna_idx=0)
    assert result["present"] is False
    assert result.get("cancelled") is True


def test_mangala_dosha_cancelled_exalted():
    m = _load()
    # Kuja in Makara (exaltation, rashi 9) — dosha cancelled
    rashis = {"kuja": 9, "chandra": 3, "shukra": 1}
    result = m.compute_mangala_dosha(rashis, lagna_idx=2)
    assert result["present"] is False
    assert result.get("cancelled") is True


# ── Kala Sarpa Dosha ─────────────────────────────────────────────────────────

def test_kala_sarpa_detected():
    m = _load()
    # Rahu at 1 (Vrshabha), Ketu at 7 (Vrischika)
    # All classical planets between 1 and 7 (rashis 2,3,4,5,6)
    rashis = {
        "rahu": 1, "ketu": 7,
        "ravi": 2, "chandra": 3, "kuja": 4,
        "budha": 5, "guru": 6, "shukra": 5, "shani": 3,
    }
    result = m.compute_kala_sarpa_dosha(rashis)
    assert result["present"] is True
    assert result["type"] == "kalasarpa"


def test_no_kala_sarpa():
    m = _load()
    # Saturn outside the arc
    rashis = {
        "rahu": 1, "ketu": 7,
        "ravi": 2, "chandra": 3, "kuja": 4,
        "budha": 5, "guru": 6, "shukra": 5, "shani": 9,
    }
    result = m.compute_kala_sarpa_dosha(rashis)
    assert result["present"] is False
