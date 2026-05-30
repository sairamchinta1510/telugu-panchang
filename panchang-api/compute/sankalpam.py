"""
Sankalpam geographic mapping and full recitation builder.
Maps lat/lon to Puranic Dweepa/Varsha/Khanda terminology (English + Telugu).
"""
from __future__ import annotations
from .sankalpam_validator import validate_sankalpam_inputs

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
    # USA / Canada — handled separately in get_geographic() via _usa_subregion()
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

def _usa_subregion(lat: float, lon: float) -> dict:
    """Return locality strings for a point within USA / Canada.

    Three sub-regions keyed by longitude:
      West  (lon < -112) — Pacific coast, west of the Rockies
      East  (lon > -88)  — Atlantic seaboard, east of the Mississippi
      Central             — between the Rockies and the Mississippi/Missouri
    """
    if lon < -112:
        return {
            "locality_en": "Rocky parvata pashchima bhage, Pratichina Mahasagara tire",
            "locality_te": "రాకీ పర్వత పశ్చిమ భాగే, ప్రశాంత మహాసాగర తీరే",
        }
    if lon > -88:
        return {
            "locality_en": "Mississippi nadi purva bhage, Atlantika Mahasagara tire",
            "locality_te": "మిస్సిసిప్పీ నదీ పూర్వ భాగే, అట్లాంటిక్ మహాసాగర తీరే",
        }
    return {
        "locality_en": "Rocky parvata madhye, Mississippi Missouri nadi madhye",
        "locality_te": "రాకీ పర్వత మధ్యే, మిస్సిసిప్పీ మిస్సోరి నదీ మధ్యే",
    }


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

    # USA / Canada — sub-regions by longitude (west of Rockies / central / east coast)
    if 25.0 <= lat <= 83.0 and -168.0 <= lon <= -52.0:
        sub = _usa_subregion(lat, lon)
        return {
            "dweepa_en": "Krauncha Dweepae",
            "dweepa_te": "క్రౌంచ ద్వీపే",
            "varsha_en": "Ramanaka Varshe",
            "varsha_te": "రమణక వర్షే",
            "khanda_en": "Aindra Khande",
            "khanda_te": "ఐన్ద్ర ఖండే",
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

    Traditional order:
      1. శుభే శోభనే ముహూర్తే (auspicious opening)
      2. Cosmic time prefix (Brahmanah dvitiya parardhe … Kali Yuge Prathama Pade)
      3. Geographic location (dweepa → varsha → khanda → locality)
      4. Samvatsara, Ayanam, Ritu, Masam, Paksham, Tithi, Vaaram, Nakshatra
      5. అస్మిన్ శుభ ముహూర్తే …

    Args:
        panchang: dict from compute_panchang()
        geo: dict from get_geographic()

    Returns dict with keys: geographic, geographic_te, full_en, full_te, validation_warnings
    """
    p = panchang

    # Validate all panchang terms against known-correct Sanskrit forms
    validation = validate_sankalpam_inputs(p)
    import logging
    for w in validation.warnings:
        logging.getLogger(__name__).warning(w)

    sam = p["samvatsara"]["en"]
    ayanam = p["ayanam"]["en"]
    rutu = p["rutu"]["en"]
    masam_name = p["masam"]["en"]
    adhika_prefix = "Adhika " if p["masam"]["adhika"] else ""
    paksham = p["paksham"]["en"]
    tithi = p["tithi"]["en"]
    # Use traditional Sanskrit deity name, not the modern colloquial weekday name
    vaaram = p["vaaram"]["sankalpam_en"]
    nakshatra = p["nakshatra"]["en"]

    g_parts_en = " ".join(filter(None, [
        geo["dweepa_en"], geo["varsha_en"], geo["khanda_en"], geo["locality_en"]
    ]))

    full_en = (
        "Sri Shubhe Shobhane Muhurthe, "
        "Sri Maha Vishnoh Ragnaya Pravarthamanasya, "
        "Adya Brahmanah dvitiya parardhe, Shveta Varaha Kalpe, "
        "Vaivasvata Manvantare, Ashtavimsatitame Kali Yuge, Prathama Pade, "
        f"{g_parts_en}, "
        f"Asmin vartamana vyavaharika chandramana {sam} nama samvatsare, "
        f"{ayanam}, {rutu} ritau, {adhika_prefix}{masam_name} mase, "
        f"{paksham}, {tithi} tithau, {vaaram} vasare, "
        f"{nakshatra} nakshatre, asmin shubha muhurte ..."
    )

    # Telugu recitation
    sam_te = p["samvatsara"]["te"]
    ayanam_te = p["ayanam"]["te"]
    rutu_te = p["rutu"]["te"]
    masam_te = p["masam"]["te"]
    adhika_te = "అధిక " if p["masam"]["adhika"] else ""
    paksham_te = p["paksham"]["te"]
    tithi_te = p["tithi"]["te"]
    # Use traditional Sanskrit deity name in Telugu script
    vaaram_te = p["vaaram"]["sankalpam_te"]
    nakshatra_te = p["nakshatra"]["te"]

    g_parts_te = " ".join(filter(None, [
        geo["dweepa_te"], geo["varsha_te"], geo["khanda_te"], geo["locality_te"]
    ]))

    full_te = (
        "శ్రీ శుభే శోభనే ముహూర్తే, "
        "శ్రీ మహావిష్ణోరాజ్ఞయా ప్రవర్తమానస్య, "
        "అద్య బ్రాహ్మణః ద్వితీయ పరార్థే, శ్వేత వరాహ కల్పే, "
        "వైవస్వత మన్వంతరే, అష్టావింశతితమే కలి యుగే, ప్రథమ పాదే, "
        f"{g_parts_te}, "
        f"అస్మిన్ వర్తమాన వ్యావహారిక చాంద్రమాన {sam_te} నామ సంవత్సరే, "
        f"{ayanam_te}, {rutu_te} ఋతౌ, {adhika_te}{masam_te} మాసే, "
        f"{paksham_te}, {tithi_te} తిథౌ, {vaaram_te} వాసరే, "
        f"{nakshatra_te} నక్షత్రే, అస్మిన్ శుభ ముహూర్తే ..."
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
        "validation_warnings": validation.warnings,
    }
