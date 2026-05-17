from compute.sankalpam import get_geographic, build_sankalpam

def test_india_vizag():
    g = get_geographic(17.69, 83.81)
    assert g["dweepa_en"] == "Jambu Dweepae"
    assert g["varsha_en"] == "Bharata Varshe"
    assert "Ishaanya" in g["locality_en"]
    assert "Godavari" in g["locality_en"]

def test_india_hyderabad():
    g = get_geographic(17.38, 78.49)
    assert g["dweepa_en"] == "Jambu Dweepae"
    assert "Vayavya" in g["locality_en"]

def test_india_chennai():
    g = get_geographic(13.08, 80.27)
    assert "Agneya" in g["locality_en"]
    assert "Kaveri" in g["locality_en"]

def test_india_bangalore():
    g = get_geographic(12.97, 77.59)
    assert "Nairutya" in g["locality_en"]

def test_india_mumbai():
    g = get_geographic(19.07, 72.87)
    assert "Sahayadri" in g["locality_en"]

def test_india_delhi():
    g = get_geographic(28.61, 77.20)
    assert "Yamuna" in g["locality_en"]

def test_usa():
    g = get_geographic(37.77, -122.41)  # San Francisco
    assert g["dweepa_en"] == "Krauncha Dweepae"
    assert g["varsha_en"] == "Ramanaka Varshe"

def test_uk():
    g = get_geographic(51.50, -0.12)  # London
    assert g["dweepa_en"] == "Shalmali Dweepae"
    assert "Airopa" in g["khanda_en"]

def test_australia():
    g = get_geographic(-33.86, 151.20)  # Sydney
    assert g["dweepa_en"] == "Shalmali Dweepae"
    assert g["varsha_en"] == "Aila Varshe"

def test_singapore():
    g = get_geographic(1.35, 103.82)
    assert g["dweepa_en"] == "Malaya Dweepasya dakshina bhage"
    assert "Serangoon" in g["khanda_en"]

def test_default_fallback():
    g = get_geographic(0.0, 180.0)
    for key in ("dweepa_en", "dweepa_te", "varsha_en", "varsha_te",
                "khanda_en", "khanda_te", "locality_en", "locality_te"):
        assert key in g
    assert g["dweepa_en"] != ""


    # Uses a pre-built panchang dict matching the compute_panchang output shape
    panchang = {
        "samvatsara": {"en": "Parabhava", "te": "పరాభవ"},
        "ayanam":     {"en": "Uttarayanam", "te": "ఉత్తరాయణం"},
        "rutu":       {"en": "Grishma", "te": "గ్రీష్మ"},
        "masam":      {"en": "Jyeshtha", "te": "జ్యేష్ఠ", "adhika": True},
        "paksham":    {"en": "Shukla Paksham", "te": "శుక్ల పక్షం"},
        "tithi":      {"en": "Panchami", "te": "పంచమి"},
        "vaaram":     {"en": "Sunday", "te": "ఆదివారం"},
        "nakshatra":  {"en": "Rohini", "te": "రోహిణి"},
        "yoga":       {"en": "Vishkambha", "te": "విష్కంభ"},
        "karana":     {"en": "Bava", "te": "బవ"},
        "sunrise": "06:14", "sunset": "18:42",
    }
    geo = get_geographic(17.38, 78.49)
    s = build_sankalpam(panchang, geo)
    assert "full_en" in s
    assert "full_te" in s
    assert "Parabhava" in s["full_en"]
    assert "Grishma" in s["full_en"]
    assert "Adhika" in s["full_en"]
    assert "Jambu" in s["full_en"]
    assert "geographic" in s
    assert "geographic_te" in s
