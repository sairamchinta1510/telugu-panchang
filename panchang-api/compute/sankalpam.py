"""
Sankalpam geographic mapping and full recitation builder.
Maps lat/lon to Puranic Dweepa/Varsha/Khanda terminology (English + Telugu).
"""
from __future__ import annotations

# ── Global region table ───────────────────────────────────────────────────────
# Each tuple: (lat_min, lat_max, lon_min, lon_max,
#              dweepa_en, dweepa_te, varsha_en, varsha_te, khanda_en, khanda_te)
# Checked in order; first match wins. India handled separately.

_GLOBAL_REGIONS = [
    # Singapore (checked before SE Asia — tighter bbox)
    (1.0, 2.0, 103.0, 104.5,
     "Malaya Dweepasya dakshina bhage", "మలయ ద్వీపస్య దక్షిణ భాగే",
     "", "", "Purva Samudra tire, Serangoon nadi parivahaka pradeshe",
     "పూర్వ సముద్ర తీరే, సెరంగూన్ నదీ పరివాహక ప్రదేశే"),
    # South/East Asia (ex-India, ex-Singapore)
    (-10.0, 55.0, 97.0, 145.0,
     "Jambu Dweepae", "జంబూ ద్వీపే",
     "Akhanda Bharata Varshe", "అఖండ భరత వర్షే",
     "Mero purva digbhage, Haridra Sagara tate", "మేరో: పూర్వ దిగ్భాగే, హరిద్రా సాగర తటే"),
    # Middle East
    (12.0, 38.0, 34.0, 60.0,
     "Jambu Dweepae", "జంబూ ద్వీపే",
     "Bharata Varshe", "భరత వర్షే",
     "Bharata Khande, Vindhyasya pashchima digbhage, Arabia Mahasagara pashchima tate",
     "భరత ఖండే, వింధ్యస్య పశ్చిమ దిగ్భాగే, అరబీ మహాసాగర పశ్చిమ తటే"),
    # USA / Canada
    (25.0, 83.0, -168.0, -52.0,
     "Krauncha Dweepae", "క్రౌంచ ద్వీపే",
     "Ramanaka Varshe", "రమణక వర్షే",
     "Aindra Khande, Rocky parvata madhye, Mississippi Missouri nadi madhye",
     "ఐన్ద్ర ఖండే, రాకీ పర్వత మధ్యే, మిస్సిసిప్పీ మిస్సోరి నదీ మధ్యే"),
    # Europe
    (35.0, 71.0, -25.0, 40.0,
     "Shalmali Dweepae", "శాల్మలీ ద్వీపే",
     "", "",
     "Airopa Khande", "ఐరోపా ఖండే"),
    # Australia / NZ
    (-47.0, -10.0, 112.0, 178.0,
     "Shalmali Dweepae", "శాల్మాలి ద్వీపే",
     "Aila Varshe", "ఐల వర్షే",
     "Nava Khande, Hindu Mahasagara tire", "నవ ఖండే, హిందూ మహా సముద్ర తీరే"),
    # Africa
    (-35.0, 37.0, -18.0, 52.0,
     "Plaksha Dweepae", "ప్లక్ష ద్వీపే",
     "", "",
     "Tamra Khande", "తామ్ర ఖండే"),
]

_SRISHAILA_LAT = 16.07
_SRISHAILA_LON = 78.87
_VINDHYA_LAT = 23.0
_WEST_COAST_LON = 77.5


def _india_subregion(lat: float, lon: float) -> dict:
    """Return locality strings for a point within India."""
    # Special case: Varanasi region
    if 24.5 <= lat <= 26.5 and 82.0 <= lon <= 84.5:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Asi Varuna madhye, Anandavane, Avimukta Varanasi Kshetra",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, అశీ వరుణయోర్ మధ్యే, ఆనందవనే, అవిముక్త వారణాసీ క్షేత్రే",
        }
    # North of Vindhya (Delhi, north India)
    if lat >= _VINDHYA_LAT:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Aryavarta pradeshe, Yamuna Ganga nadi madhye",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, ఆర్య వర్తైక ప్రదేశే, యమునా గంగా నదీ మధ్యే",
        }
    # West coast (Mumbai / Goa)
    if lon < _WEST_COAST_LON:
        return {
            "locality_en": "Vindhyasya pashchima digbhage, Sahayadri parvata prante, Arabia Mahasagara tire",
            "locality_te": "వింధ్యస్య పశ్చిమ దిగ్భాగే, సహయాద్రి పర్వత ప్రాంతే, అరబీ మహా సాగర తీరే",
        }
    # South of Srishaila
    if lat < _SRISHAILA_LAT:
        if lon >= _SRISHAILA_LON:
            # SE: Chennai / Tamil Nadu
            return {
                "locality_en": "Srishaila Agneya pradeshe, Krishna Kaveri nadi madhya pradeshe",
                "locality_te": "శ్రీశైలస్య ఆగ్నేయ ప్రదేశే, కృష్ణ కావేరి మధ్య ప్రదేశే",
            }
        else:
            # SW: Bangalore / Karnataka
            return {
                "locality_en": "Srishaila Nairutya pradeshe, Tungabhadra Kaveri nadi madhya pradeshe",
                "locality_te": "శ్రీశైలస్య నైరుతి ప్రదేశే, తుంగభద్ర కావేరి మధ్య ప్రదేశే",
            }
    # NE of Srishaila: Hyderabad / Vizag / AP / Telangana
    if lon >= _SRISHAILA_LON:
        return {
            "locality_en": "Srishaila Ishaanya pradeshe, Ganga Godavari nadi madhya pradeshe",
            "locality_te": "శ్రీశైలస్య ఈశాన్య ప్రదేశే, గంగా గోదావరి మధ్య ప్రదేశే",
        }
    # NW of Srishaila: rest of Deccan
    return {
        "locality_en": "Srishaila Vayavya pradeshe, Krishna Godavari nadi madhya pradeshe",
        "locality_te": "శ్రీశైలస్య వాయవ్య ప్రదేశే, కృష్ణ గోదావరి మధ్య ప్రదేశే",
    }


def get_geographic(lat: float, lon: float) -> dict:
    """Return Puranic geographic terms for the given lat/lon.
    
    Returns a dict with keys: dweepa_en, dweepa_te, varsha_en, varsha_te,
    khanda_en, khanda_te, locality_en, locality_te.
    """
    # India check first (takes priority over global table)
    if 6.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0:
        sub = _india_subregion(lat, lon)
        return {
            "dweepa_en": "Jambu Dweepae",
            "dweepa_te": "జంబూ ద్వీపే",
            "varsha_en": "Bharata Varshe",
            "varsha_te": "భరత వర్షే",
            "khanda_en": "Bharata Khande",
            "khanda_te": "భరత ఖండే",
            **sub,
        }

    for (lat_min, lat_max, lon_min, lon_max,
         dweepa_en, dweepa_te, varsha_en, varsha_te,
         khanda_en, khanda_te) in _GLOBAL_REGIONS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return {
                "dweepa_en": dweepa_en,
                "dweepa_te": dweepa_te,
                "varsha_en": varsha_en,
                "varsha_te": varsha_te,
                "khanda_en": khanda_en,
                "khanda_te": khanda_te,
                "locality_en": "",
                "locality_te": "",
            }

    # Default (open ocean, polar regions, etc.)
    return {
        "dweepa_en": "Jambu Dweepae",
        "dweepa_te": "జంబూ ద్వీపే",
        "varsha_en": "Akhanda Bharata Varshe",
        "varsha_te": "అఖండ భరత వర్షే",
        "khanda_en": "",
        "khanda_te": "",
        "locality_en": "",
        "locality_te": "",
    }


def build_sankalpam(panchang: dict, geo: dict) -> dict:
    """Build full sankalpam recitation strings from panchang + geographic data.
    
    Args:
        panchang: dict from compute_panchang()
        geo: dict from get_geographic()
    
    Returns dict with keys: geographic, geographic_te, full_en, full_te
    """
    p = panchang
    sam = p["samvatsara"]["en"]
    ayanam = p["ayanam"]["en"]
    rutu = p["rutu"]["en"]
    masam_name = p["masam"]["en"]
    adhika_prefix = "Adhika " if p["masam"]["adhika"] else ""
    paksham = p["paksham"]["en"]
    tithi = p["tithi"]["en"]
    vaaram = p["vaaram"]["en"]
    nakshatra = p["nakshatra"]["en"]
    yoga = p["yoga"]["en"]
    karana = p["karana"]["en"]

    g_parts_en = " ".join(filter(None, [
        geo["dweepa_en"], geo["varsha_en"], geo["khanda_en"], geo["locality_en"]
    ]))

    full_en = (
        f"Asmin vartamana vyavaharika chandramana {sam} nama samvatsare, "
        f"{ayanam}, {rutu} ritau, {adhika_prefix}{masam_name} mase, "
        f"{paksham}, {tithi} tithau, {vaaram} vasara yukte, "
        f"{nakshatra} nakshatre, {yoga} yoge, {karana} karane, "
        f"{g_parts_en}, asmin shubha muhurte ..."
    )

    # Telugu recitation
    sam_te = p["samvatsara"]["te"]
    ayanam_te = p["ayanam"]["te"]
    rutu_te = p["rutu"]["te"]
    masam_te = p["masam"]["te"]
    adhika_te = "అధిక " if p["masam"]["adhika"] else ""
    paksham_te = p["paksham"]["te"]
    tithi_te = p["tithi"]["te"]
    vaaram_te = p["vaaram"]["te"]
    nakshatra_te = p["nakshatra"]["te"]
    yoga_te = p["yoga"]["te"]
    karana_te = p["karana"]["te"]

    g_parts_te = " ".join(filter(None, [
        geo["dweepa_te"], geo["varsha_te"], geo["khanda_te"], geo["locality_te"]
    ]))

    full_te = (
        f"అస్మిన్ వర్తమాన వ్యావహారిక చాంద్రమాన {sam_te} నామ సంవత్సరే, "
        f"{ayanam_te}, {rutu_te} ఋతౌ, {adhika_te}{masam_te} మాసే, "
        f"{paksham_te}, {tithi_te} తిథౌ, {vaaram_te} వాసర యుక్తే, "
        f"{nakshatra_te} నక్షత్రే, {yoga_te} యోగే, {karana_te} కరణే, "
        f"{g_parts_te}, అస్మిన్ శుభ ముహూర్తే ..."
    )

    return {
        "geographic": {
            "dweepa": geo["dweepa_en"],
            "varsha": geo["varsha_en"],
            "khanda": geo["khanda_en"],
            "locality": geo["locality_en"],
        },
        "geographic_te": {
            "dweepa": geo["dweepa_te"],
            "varsha": geo["varsha_te"],
            "khanda": geo["khanda_te"],
            "locality": geo["locality_te"],
        },
        "full_en": full_en,
        "full_te": full_te,
    }
