"""
Jyotish chart analysis: nakshatra enrichment, planet strength, Navamsa,
Graha Drishti, Parivartana Yoga, Mangala Dosha, Kala Sarpa Dosha.
"""
from __future__ import annotations


NAKSHATRA_TE = [
    "అశ్వని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆర్ద్ర", "పునర్వసు",
    "పుష్యమి", "ఆశ్లేష", "మఖ", "పూర్వఫల్గుని", "ఉత్తరఫల్గుని", "హస్త", "చిత్త",
    "స్వాతి", "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ",
    "శ్రవణం", "ధనిష్ఠ", "శతభిష", "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి",
]

RASHI_TE = [
    "మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య",
    "తులం", "వృశ్చికం", "ధనుస్సు", "మకరం", "కుంభం", "మీనం",
]

RASHI_OWNER = {
    0: "kuja", 1: "shukra", 2: "budha", 3: "chandra", 4: "ravi", 5: "budha",
    6: "shukra", 7: "kuja", 8: "guru", 9: "shani", 10: "shani", 11: "guru",
}

EXALTATION = {
    "ravi": (0, 10), "chandra": (1, 3), "kuja": (9, 28),
    "budha": (5, 15), "guru": (3, 5), "shukra": (11, 27),
    "shani": (6, 20), "rahu": (1, 20), "ketu": (7, 20),
}
DEBILITATION = {planet: ((rashi + 6) % 12, degree) for planet, (rashi, degree) in EXALTATION.items()}

MOOLATRIKONA = {
    "ravi": (4, 0, 20), "chandra": (1, 4, 30), "kuja": (0, 0, 12),
    "budha": (5, 16, 20), "guru": (8, 0, 10), "shukra": (6, 0, 15),
    "shani": (10, 0, 20),
}

COMBUST_ORB = {
    "chandra": 12, "kuja": 17, "budha": 14,
    "guru": 11, "shukra": 10, "shani": 15,
}

DASHA_SEQUENCE = ["ketu", "shukra", "ravi", "chandra", "kuja", "rahu", "guru", "shani", "budha"]

SPECIAL_ASPECTS = {
    "kuja": [4, 8],
    "guru": [5, 9],
    "shani": [3, 10],
}

_NAK_SPAN = 360.0 / 27


def enrich_planet_details(planet_details: dict[str, dict]) -> dict[str, dict]:
    """Add derived Jyotish metadata to each planet entry."""
    sun_lon = _approx_lon(planet_details.get("ravi", {}))
    result = {}

    fire_signs = {0, 4, 8}
    earth_signs = {1, 5, 9}
    air_signs = {2, 6, 10}

    for name, details in planet_details.items():
        lon = _approx_lon(details)
        nak_idx = int(lon / _NAK_SPAN) % 27
        nak_pada = int((lon % _NAK_SPAN) / (_NAK_SPAN / 4)) + 1

        rashi_idx = details.get("rashi_idx", int(lon / 30) % 12)
        if rashi_idx in fire_signs:
            nav_start = 0
        elif rashi_idx in earth_signs:
            nav_start = 9
        elif rashi_idx in air_signs:
            nav_start = 6
        else:
            nav_start = 3

        deg_in_rashi = lon % 30
        pada_in_sign = int(deg_in_rashi / (30.0 / 9))
        navamsa_rashi_idx = (nav_start + pada_in_sign) % 12

        entry = dict(details)
        entry.update({
            "nakshatra_idx": nak_idx,
            "nakshatra_te": NAKSHATRA_TE[nak_idx],
            "nakshatra_pada": nak_pada,
            "nakshatra_lord": DASHA_SEQUENCE[nak_idx % 9],
            "navamsa_rashi_idx": navamsa_rashi_idx,
            "navamsa_rashi_te": RASHI_TE[navamsa_rashi_idx],
            "strength": _compute_strength(
                name,
                rashi_idx,
                details.get("deg", 0),
                sun_lon,
                details.get("retrograde", False),
                lon,
            ),
        })
        result[name] = entry

    return result


def _approx_lon(details: dict) -> float:
    """Reconstruct approximate longitude from rashi_idx + deg + min."""
    return details.get("rashi_idx", 0) * 30.0 + details.get("deg", 0) + details.get("min", 0) / 60.0


def _compute_strength(
    name: str,
    rashi_idx: int,
    deg: int,
    sun_lon: float,
    retrograde: bool,
    lon: float,
) -> str:
    """Return primary strength label."""
    _ = retrograde

    if name in ("rahu", "ketu"):
        ex_r, _ = EXALTATION[name]
        deb_r, _ = DEBILITATION[name]
        if rashi_idx == ex_r:
            return "exalted"
        if rashi_idx == deb_r:
            return "debilitated"
        return "normal"

    ex_r, _ = EXALTATION[name]
    deb_r, _ = DEBILITATION[name]
    if rashi_idx == ex_r:
        return "exalted"
    if rashi_idx == deb_r:
        return "debilitated"

    if name != "ravi" and name in COMBUST_ORB:
        diff = abs(lon - sun_lon)
        if diff > 180:
            diff = 360 - diff
        if diff <= COMBUST_ORB[name]:
            return "combust"

    if name in MOOLATRIKONA:
        mt_rashi, mt_start_deg, mt_end_deg = MOOLATRIKONA[name]
        if rashi_idx == mt_rashi and mt_start_deg <= deg <= mt_end_deg:
            return "moolatrikona"

    if RASHI_OWNER.get(rashi_idx) == name:
        return "own"

    return "normal"


def compute_navamsa_rashis(planet_details: dict[str, dict]) -> dict[str, int]:
    """Return navamsa rashi index for each enriched planet."""
    return {
        planet: details["navamsa_rashi_idx"]
        for planet, details in planet_details.items()
        if "navamsa_rashi_idx" in details
    }


def compute_graha_drishti(planet_rashis: dict[str, int]) -> list[dict]:
    """Return graha aspect relations between planets."""
    aspects = []

    for from_planet, from_rashi in planet_rashis.items():
        seventh_rashi = (from_rashi + 6) % 12
        for to_planet, to_rashi in planet_rashis.items():
            if to_planet == from_planet:
                continue
            if to_rashi == seventh_rashi:
                aspects.append({
                    "from": from_planet,
                    "to": to_planet,
                    "aspect_house": 7,
                    "type": "full",
                })
            for extra_house in SPECIAL_ASPECTS.get(from_planet, []):
                special_rashi = (from_rashi + extra_house - 1) % 12
                if to_rashi == special_rashi:
                    aspects.append({
                        "from": from_planet,
                        "to": to_planet,
                        "aspect_house": extra_house,
                        "type": "special",
                    })

    return aspects


def compute_parivartana_yogas(planet_rashis: dict[str, int], lagna_idx: int) -> list[dict]:
    """Return mutual sign-exchange yogas."""
    yogas = []
    seen = set()

    for planet_a in (planet for planet in planet_rashis if planet not in ("rahu", "ketu")):
        rashi_a = planet_rashis[planet_a]
        planet_b = RASHI_OWNER.get(rashi_a)
        if planet_b is None or planet_b == planet_a or planet_b not in planet_rashis:
            continue

        rashi_b = planet_rashis[planet_b]
        if RASHI_OWNER.get(rashi_b) != planet_a:
            continue

        key = tuple(sorted((planet_a, planet_b)))
        if key in seen:
            continue
        seen.add(key)

        house_a = (rashi_a - lagna_idx) % 12 + 1
        house_b = (rashi_b - lagna_idx) % 12 + 1
        if house_a in {6, 8, 12} or house_b in {6, 8, 12}:
            yoga_type = "dainya"
        elif house_a == 3 or house_b == 3:
            yoga_type = "kahala"
        else:
            yoga_type = "maha"

        yogas.append({
            "planet_a": planet_a,
            "planet_b": planet_b,
            "rashi_a_te": RASHI_TE[rashi_a],
            "rashi_b_te": RASHI_TE[rashi_b],
            "house_a": house_a,
            "house_b": house_b,
            "type": yoga_type,
        })

    return yogas


def compute_mangala_dosha(planet_rashis: dict[str, int], lagna_idx: int) -> dict:
    """Check Mangala Dosha from lagna, moon, and venus.

    Cancellation rules (universally accepted in Telugu/South Indian tradition):
    - Kuja in own sign (Mesha=0 or Vrischika=7): dosha cancelled
    - Kuja in exaltation (Makara=9): dosha cancelled
    - Kuja in 1st house and lagna is Mesha or Vrischika (Kuja is lagna lord): cancelled
    - Kuja in 2nd house and lagna is Makara or Kumbha (Shani lagna, 2nd-house rule relaxed): cancelled
    """
    dosha_houses = {1, 2, 4, 7, 8, 12}
    kuja_rashi = planet_rashis.get("kuja")
    moon_rashi = planet_rashis.get("chandra")
    venus_rashi = planet_rashis.get("shukra")

    if kuja_rashi is None:
        return {"present": False}

    # Cancellation: own sign or exaltation nullifies dosha entirely
    if kuja_rashi in (0, 7, 9):  # Mesha, Vrischika, Makara
        return {"present": False, "cancelled": True,
                "cancel_reason": "స్వక్షేత్ర లేదా ఉచ్చ స్థానం" if kuja_rashi != 9
                else "ఉచ్చ స్థానం (మకరం)"}

    kuja_house_lagna = (kuja_rashi - lagna_idx) % 12 + 1
    kuja_house_moon = (kuja_rashi - moon_rashi) % 12 + 1 if moon_rashi is not None else None
    kuja_house_venus = (kuja_rashi - venus_rashi) % 12 + 1 if venus_rashi is not None else None

    # Cancellation: Kuja in 1st house but lagna is Mesha or Vrischika (own-sign lagna)
    if kuja_house_lagna == 1 and lagna_idx in (0, 7):
        return {"present": False, "cancelled": True,
                "cancel_reason": "కుజ లగ్నాధిపతి — లగ్నంలో స్వగ్రహం"}

    # Cancellation: Kuja in 2nd house from Makara/Kumbha lagna (Saturn lagna exception)
    if kuja_house_lagna == 2 and lagna_idx in (9, 10):
        return {"present": False, "cancelled": True,
                "cancel_reason": "మకర/కుంభ లగ్నానికి 2వ భావంలో కుజ — దోషం లేదు"}

    from_lagna = kuja_house_lagna in dosha_houses
    from_moon = kuja_house_moon in dosha_houses if kuja_house_moon else False
    from_venus = kuja_house_venus in dosha_houses if kuja_house_venus else False

    count = sum([from_lagna, from_moon, from_venus])
    return {
        "present": from_lagna or from_moon or from_venus,
        "from_lagna": from_lagna,
        "from_moon": from_moon,
        "from_venus": from_venus,
        "kuja_house_lagna": kuja_house_lagna,
        "kuja_house_moon": kuja_house_moon,
        "kuja_house_venus": kuja_house_venus,
        "severity": "తీవ్రం" if count >= 2 else ("మధ్యమం" if count == 1 else "లేదు"),
    }


def compute_kala_sarpa_dosha(planet_rashis: dict[str, int]) -> dict:
    """Check if all classical planets lie on the same nodal arc."""
    rahu_rashi = planet_rashis.get("rahu")
    ketu_rashi = planet_rashis.get("ketu")
    if rahu_rashi is None or ketu_rashi is None:
        return {"present": False}

    classical = ["ravi", "chandra", "kuja", "budha", "guru", "shukra", "shani"]
    classical_rashis = [planet_rashis[planet] for planet in classical if planet in planet_rashis]

    def _between(start: int, end: int, rashi: int) -> bool:
        if start == end:
            return False
        if start < end:
            return start < rashi < end
        return rashi > start or rashi < end

    kala_sarpa = all(_between(rahu_rashi, ketu_rashi, rashi) for rashi in classical_rashis)
    kala_amrita = all(_between(ketu_rashi, rahu_rashi, rashi) for rashi in classical_rashis)

    if not kala_sarpa and not kala_amrita:
        return {"present": False}

    return {
        "present": True,
        "type": "kalasarpa" if kala_sarpa else "kalamrita",
        "rahu_rashi_te": RASHI_TE[rahu_rashi],
        "ketu_rashi_te": RASHI_TE[ketu_rashi],
        "planets_between": classical,
    }
