# Panchang API — Design Spec

**Date:** 2026-05-17  
**Status:** Approved

---

## Problem & Approach

The Telugu Panchang web page computes all astronomical data in client-side JavaScript. The upcoming Alexa Skill will need the same data. Rather than duplicating complex calculations in two runtimes, a shared REST API centralises all Panchang computation using **pyswisseph** (Python Swiss Ephemeris bindings) — the same Lahiri-ayanamsha-corrected sidereal calculations already proven correct in the web page, but now authoritative and server-side.

---

## Architecture

```
Web page (panchang.html)       Alexa Skill Lambda
         \                          /
          \                        /
           GET /panchang?lat=&lon=&date=
                       |
          API Gateway (HTTP API)
                       |
              Panchang Lambda (Python)
              ├── pyswisseph  (astronomy)
              ├── timezonefinder (offline TZ lookup)
              └── sankalpam mapper (lat/lon → geo terms)
                       |
          CloudFront (cache per date+location)
```

- **Hosting:** AWS Lambda + API Gateway (HTTP API), deployed via AWS SAM
- **Domain:** `api.sanatanadharmas.com` (CNAME → API Gateway custom domain)
- **Auth:** None — public API
- **Caching:** CloudFront in front of API Gateway; `Cache-Control: max-age=<seconds until midnight of requested date>` so each date's data is cached until it expires naturally

---

## Endpoint

```
GET /panchang?lat={float}&lon={float}&date={YYYY-MM-DD}
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `lat` | Yes | Latitude in decimal degrees (e.g. `17.38`) |
| `lon` | Yes | Longitude in decimal degrees (e.g. `78.49`) |
| `date` | No | ISO date. Defaults to today in the location's timezone |

### Success Response — 200 OK

```json
{
  "date": "2026-05-17",
  "location": {
    "lat": 17.38,
    "lon": 78.49,
    "timezone": "Asia/Kolkata"
  },
  "panchang": {
    "samvatsara":  { "en": "Parabhava",      "te": "పరాభవ" },
    "ayanam":      { "en": "Uttarayanam",    "te": "ఉత్తరాయణం" },
    "rutuvu":      { "en": "Grishma",        "te": "గ్రీష్మ ఋతువు" },
    "masam":       { "en": "Adhika Jyeshtha","te": "అధిక జ్యేష్ఠ మాసం", "adhika": true },
    "paksham":     { "en": "Shukla Paksham", "te": "శుక్ల పక్షం" },
    "tithi":       { "en": "Panchami",       "te": "పంచమి" },
    "vaaram":      { "en": "Sunday",         "te": "ఆదివారం" },
    "nakshatra":   { "en": "Rohini",         "te": "రోహిణి" },
    "yoga":        { "en": "Vishkambha",     "te": "విష్కంభ" },
    "karana":      { "en": "Bava",           "te": "బవ" },
    "sunrise":     "06:14",
    "sunset":      "18:42"
  },
  "sankalpam": {
    "geographic": {
      "dweepa":   "Jambu Dweepae",
      "varsha":   "Bharata Varshe",
      "khanda":   "Bharata Khande",
      "locality": "Srishaila Ishaanya Pradesh, Ganga Godavari Madhya Pradesh"
    },
    "geographic_te": {
      "dweepa":   "జంబూ ద్వీపే",
      "varsha":   "భరత వర్షే",
      "khanda":   "భరత ఖండే",
      "locality": "శ్రీశైలస్య ఈశాన్య ప్రదేశే గంగా గోదావరి మధ్య ప్రదేశే"
    },
    "full_en": "Asmin vartamana vyavaharika chandramana Parabhava nama samvatsare, Uttarayanam, Grishma ritau, Jyeshtha adhika mase, Shukla pakshe, Panchami tithau, Adivara vasara yukta, Rohini nakshatre, Vishkambha yoga, Bava karana, Jambu Dweepae, Bharata Varshe, Bharata Khande, Srishaila Ishaanya Pradesh, Ganga Godavari Madhya Pradesh, asmin shubha muhurte ...",
    "full_te": "అస్మిన్ వర్తమాన వ్యావహారిక చాంద్రమాన పరాభవ నామ సంవత్సరే, ఉత్తరాయణే, గ్రీష్మ ఋతౌ, జ్యేష్ఠ అధిక మాసే, శుక్ల పక్షే, పంచమి తిథౌ, ఆదివార వాసర యుక్తే, రోహిణి నక్షత్రే, విష్కంభ యోగే, బవ కరణే, జంబూ ద్వీపే, భరత వర్షే, భరత ఖండే, శ్రీశైలస్య ఈశాన్య ప్రదేశే, గంగా గోదావరి మధ్య ప్రదేశే, అస్మిన్ శుభ ముహూర్తే ..."
  }
}
```

### Error Responses

| Code | Condition |
|------|-----------|
| 400 | Missing or invalid `lat`/`lon`, invalid `date` format |
| 500 | Internal calculation error (logged to CloudWatch) |

---

## Astronomical Calculations

All calculations use **pyswisseph** with:
- **Epoch:** Julian Day computed for local solar noon at given lat/lon/date
- **Ayanamsha:** Lahiri (SE_SIDM_LAHIRI) — same formula verified in JS frontend
- **Coordinate system:** Sidereal (tropical longitude minus ayanamsha)

### Computed Values

| Field | Method |
|-------|--------|
| Samvatsara | Saka year = Gregorian year − 78; index = `(saka_year % 60 + 11) % 60` |
| Ayanam | Sun sidereal longitude: < 180° → Uttarayanam, ≥ 180° → Dakshinayanam |
| Rutu | `floor(masam_index / 2) % 6` (derived from masam, not sun longitude) |
| Masam | New moon (Amavasya) binary search; Adhika if no sankranti between consecutive Amavasyas |
| Paksham | Moon–Sun elongation: < 180° → Shukla, ≥ 180° → Krishna |
| Tithi | `floor(elongation / 12) + 1` (1–30) |
| Vaaram | Day of week in local timezone |
| Nakshatra | Moon sidereal longitude / 13.333° |
| Yoga | `(sun_sid + moon_sid) / 13.333°` |
| Karana | `floor((elongation % 180) / 6)` mapped to 11 karanas |
| Sunrise/Sunset | pyswisseph `swe_rise_trans` with refraction |

---

## Sankalpam Geographic Mapping

Mapping is resolved offline (no external geocoding API) using lat/lon ranges:

### Global Regions

| Lat/Lon Range | Dweepa | Varsha | Khanda |
|---|---|---|---|
| India (6–37°N, 68–97°E) | Jambu Dweepae | Bharata Varshe | sub-region (see below) |
| Middle East (12–38°N, 34–60°E) | Jambu Dweepae | Bharata Varshe | Bharata Khande, Vindhya pashchima, Arabia Mahasagara tata |
| South/East Asia ex-India (−10–55°N, 97–145°E) | Jambu Dweepae | Akhanda Bharata Varshe | Mero purva digbhage, Haridra Sagara tate |
| Singapore (1–2°N, 103–104°E) | Malaya Dweepasya dakshina bhage | — | Purva Samudra tire |
| Europe (35–71°N, −25–40°E) | Shalmali Dweepae | — | Airopa Khande |
| USA/Canada (25–83°N, −168–−52°E) | Krauncha Dweepae | Ramanaka Varshe | Aindra Khande, Rocky mountains madhye, Mississippi Missouri nadi madhye |
| Australia/NZ (−47–−10°S, 112–178°E) | Shalmali Dweepae | Aila Varshe | Nava Khande, Hindu Mahasagara tire |
| Africa (−35–37°N, −18–52°E) | Plaksha Dweepae | — | Tamra Khande |
| Default/other | Jambu Dweepae | Akhanda Bharata Varshe | — |

### India Sub-Regions (relative to Srishaila 16.07°N, 78.87°E and Vindhya ~23°N)

| Region | Direction | Rivers | Cities |
|---|---|---|---|
| North of Vindhya (>23°N) | Vindhya pashchima | Yamuna / Ganga | Delhi, Varanasi |
| NE of Srishaila (lat>16°N, lon>78°E) | Srishaila Ishaanya | Ganga–Godavari | Hyderabad, Vizag |
| SE of Srishaila (lat<16°N, lon>78°E) | Srishaila Agneya | Krishna–Kaveri | Chennai, Tirupati |
| SW of Srishaila (lat<16°N, lon<78°E) | Srishaila Nairutya | Tungabhadra–Kaveri | Bangalore, Mysore |
| West coast (lon<75°E) | Vindhya pashchima, Sahayadri | Arabia Mahasagara | Mumbai, Goa |

Special case — Varanasi (25.3°N, 83.0°E): `Vindhya pashchima, Asi Varuna madhye, Anandavane, Avimukta Varanasi Kshetra`

---

## Client Caching

**Web page:** cache in `localStorage` keyed `panchang:{date}:{lat_rounded}:{lon_rounded}` (rounded to 0.1°). Invalidate at midnight local time.

**Alexa Skill:** no caching — call the API fresh on each intent invocation.

---

## Deployment

| Resource | Value |
|---|---|
| Lambda runtime | Python 3.12 |
| Lambda memory | 256 MB |
| Lambda timeout | 10 seconds |
| Dependencies | pyswisseph, timezonefinder, pytz |
| SAM template | `panchang-api/template.yaml` |
| API Gateway | HTTP API (not REST API) |
| CloudFront | New distribution in front of API GW custom domain |
| Custom domain | `api.sanatanadharmas.com` |
| Certificate | ACM us-east-1 (same account) |

---

## Directory Structure

```
panchang-api/
├── template.yaml          # SAM template (Lambda + API GW + CloudFront)
├── requirements.txt       # pyswisseph, timezonefinder, pytz
├── handler.py             # Lambda entry point — parse params, call compute, return JSON
├── compute/
│   ├── __init__.py
│   ├── astro.py           # pyswisseph wrappers: JD, sunrise, sidereal positions
│   ├── panchang.py        # samvatsara, masam, tithi, nakshatra, yoga, karana, rutu
│   └── sankalpam.py       # lat/lon → Dweepa/Varsha/Khanda + full recitation strings
└── tests/
    ├── test_astro.py
    ├── test_panchang.py
    └── test_sankalpam.py
```

---

## Testing Strategy

- **Unit tests:** `tests/` using pytest; known-good dates verified against published panchangams
  - 2026-05-17 → Parabhava, Adhika Jyeshtha, Grishma, Panchami ✓
- **Integration test:** deploy to a `dev` stage; run `curl` assertions against the live endpoint
- **Regression guard:** samvatsara anchors checked: 2024=Krodhi(37), 2025=Vishvavasu(38), 2026=Parabhava(39)
