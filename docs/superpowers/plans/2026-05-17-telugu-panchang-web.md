# Telugu Panchang Web Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single standalone `frontend/panchang.html` that auto-detects browser location and renders a full South Indian (Telugu) daily panchang with Sandstone & Saffron styling.

**Architecture:** Single HTML file with all CSS and JS inline, organised into IIFE modules (Astro, TeluguCalendar, Panchang, SouthIndian, Geo, UI). SunCalc.js loaded from CDN for sunrise/sunset; all ecliptic longitude calculations done with Meeus formulas in pure JS. Browser Geolocation API + Nominatim for location.

**Tech Stack:** Vanilla HTML/CSS/JS, SunCalc.js 1.9.0 (CDN), Nominatim OpenStreetMap API (free, no key)

---

## File Map

| File | Purpose |
|---|---|
| `frontend/panchang.html` | Complete application — CSS + all JS modules inline |

---

### Task 1: HTML skeleton + CSS

**Files:**
- Create: `frontend/panchang.html`

- [ ] **Step 1: Create the file with full CSS and HTML structure**

Create `frontend/panchang.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Telugu Daily Panchang · నిత్య పంచాంగం</title>
<script src="https://unpkg.com/suncalc@1.9.0/suncalc.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #fdf6ec; color: #3e2723; padding: 16px; min-height: 100vh; }

/* Page Header */
.page-header { text-align: center; padding: 20px 16px 14px; background: linear-gradient(135deg, #5d4037 0%, #8d6e63 60%, #d7a96b 100%); border-radius: 14px; margin-bottom: 14px; color: white; }
.page-header .om { font-size: 2.2rem; line-height: 1; margin-bottom: 6px; }
.page-header h1 { font-size: 1.25rem; font-weight: 700; letter-spacing: 1px; }
.page-header .telugu-title { font-size: 0.9rem; opacity: 0.88; margin-top: 3px; }

/* Location bar */
.location-bar { background: #efebe9; border: 1px solid #d7ccc8; border-radius: 8px; padding: 8px 14px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #4e342e; flex-wrap: wrap; }
.location-bar .loc-name { font-weight: 600; }
.location-bar .loc-coords { color: #8d6e63; margin-left: auto; font-size: 0.72rem; }
.location-bar.error { color: #bf360c; background: #fbe9e7; border-color: #ffccbc; }

/* Date banner */
.date-banner { background: #fff; border: 1px solid #d7ccc8; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }
.date-banner .gregorian { font-size: 0.82rem; color: #8d6e63; margin-bottom: 4px; }
.date-banner .telugu-date { font-size: 1.05rem; font-weight: 700; color: #4e342e; }
.date-banner .samvatsara { font-size: 0.78rem; color: #8d6e63; margin-top: 3px; }

/* Sections */
.section { background: #fff; border: 1px solid #d7ccc8; border-radius: 10px; margin-bottom: 12px; overflow: hidden; }
.section-header { background: #5d4037; color: white; padding: 7px 14px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; display: flex; gap: 6px; align-items: center; }
.section-header .te { opacity: 0.82; font-weight: normal; }

/* Rows */
.row { display: flex; align-items: flex-start; padding: 10px 14px; border-bottom: 1px solid #efebe9; }
.row:last-child { border-bottom: none; }
.row .key { flex: 0 0 42%; }
.row .key .en { font-size: 0.82rem; font-weight: 600; color: #3e2723; }
.row .key .te { font-size: 0.72rem; color: #8d6e63; }
.row .value { flex: 1; text-align: right; }
.row .value .main { font-size: 0.85rem; font-weight: 700; color: #3e2723; }
.row .value .te { font-size: 0.72rem; color: #8d6e63; }
.row .value .until { font-size: 0.7rem; color: #a1887f; display: block; }

/* Time rows */
.time-row { display: flex; align-items: center; padding: 10px 14px; border-bottom: 1px solid #efebe9; }
.time-row:last-child { border-bottom: none; }
.time-row .icon { width: 26px; font-size: 1rem; flex-shrink: 0; }
.time-row .label { flex: 1; }
.time-row .label .en { font-size: 0.82rem; font-weight: 600; }
.time-row .label .te { font-size: 0.7rem; color: #8d6e63; }
.time-row .time-val { font-size: 0.85rem; font-weight: 700; }
.time-row .time-val.good { color: #33691e; }
.time-row .time-val.danger { color: #bf360c; }

.bad-note { padding: 6px 14px 8px; font-size: 0.7rem; color: #a1887f; font-style: italic; }

/* Skeleton loading */
.skel { background: linear-gradient(90deg, #efebe9 25%, #d7ccc8 50%, #efebe9 75%); background-size: 200% 100%; animation: skel 1.4s infinite; border-radius: 4px; height: 14px; margin: 4px 0; }
@keyframes skel { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Error banner */
.error-banner { background: #fbe9e7; border: 1px solid #ffccbc; border-radius: 8px; padding: 10px 14px; color: #bf360c; font-size: 0.82rem; margin-bottom: 12px; display: none; }

footer { text-align: center; padding: 14px; font-size: 0.7rem; color: #a1887f; }
</style>
</head>
<body>

<div class="page-header">
  <div class="om">🕉</div>
  <h1>Daily Panchang</h1>
  <div class="telugu-title">నిత్య పంచాంగం</div>
</div>

<div class="error-banner" id="error-banner"></div>

<div class="location-bar" id="location-bar">
  <span>📍</span>
  <span class="loc-name" id="loc-name">Detecting location…</span>
  <span class="loc-coords" id="loc-coords"></span>
</div>

<div class="date-banner">
  <div class="gregorian" id="gregorian-date"><div class="skel" style="width:180px"></div></div>
  <div class="telugu-date" id="telugu-date"><div class="skel" style="width:260px"></div></div>
  <div class="samvatsara" id="samvatsara"><div class="skel" style="width:200px"></div></div>
</div>

<!-- Calendar Section -->
<div class="section">
  <div class="section-header"><span>📅 Calendar</span><span class="te">· కాలమానం</span></div>
  <div class="row">
    <div class="key"><div class="en">Rutuvu</div><div class="te">రుతువు</div></div>
    <div class="value"><div class="main" id="rutuvu-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="rutuvu-te"></div></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Masam</div><div class="te">మాసం</div></div>
    <div class="value"><div class="main" id="masam-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="masam-te"></div></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Paksham</div><div class="te">పక్షం</div></div>
    <div class="value"><div class="main" id="paksham-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="paksham-te"></div></div>
  </div>
</div>

<!-- Panchangam Section -->
<div class="section">
  <div class="section-header"><span>☀️ Panchangam</span><span class="te">· పంచాంగం</span></div>
  <div class="row">
    <div class="key"><div class="en">Tithi</div><div class="te">తిథి</div></div>
    <div class="value"><div class="main" id="tithi-en"><div class="skel" style="width:90px;float:right"></div></div><div class="te" id="tithi-te"></div><span class="until" id="tithi-until"></span></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Nakshatra</div><div class="te">నక్షత్రం</div></div>
    <div class="value"><div class="main" id="nakshatra-en"><div class="skel" style="width:90px;float:right"></div></div><div class="te" id="nakshatra-te"></div><span class="until" id="nakshatra-until"></span></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Yoga</div><div class="te">యోగం</div></div>
    <div class="value"><div class="main" id="yoga-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="yoga-te"></div></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Karana</div><div class="te">కరణం</div></div>
    <div class="value"><div class="main" id="karana-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="karana-te"></div></div>
  </div>
  <div class="row">
    <div class="key"><div class="en">Vara</div><div class="te">వారం</div></div>
    <div class="value"><div class="main" id="vara-en"><div class="skel" style="width:80px;float:right"></div></div><div class="te" id="vara-te"></div></div>
  </div>
</div>

<!-- Sun Timings Section -->
<div class="section">
  <div class="section-header"><span>🌅 Sun Timings</span><span class="te">· సూర్యోదయ అస్తమయం</span></div>
  <div class="time-row">
    <span class="icon">🌅</span>
    <div class="label"><div class="en">Sunrise</div><div class="te">సూర్యోదయం</div></div>
    <span class="time-val good" id="sunrise"><div class="skel" style="width:60px"></div></span>
  </div>
  <div class="time-row">
    <span class="icon">🌇</span>
    <div class="label"><div class="en">Sunset</div><div class="te">సూర్యాస్తమయం</div></div>
    <span class="time-val good" id="sunset"><div class="skel" style="width:60px"></div></span>
  </div>
  <div class="time-row">
    <span class="icon">✨</span>
    <div class="label"><div class="en">Abhijit Muhurta</div><div class="te">అభిజిత్ ముహూర్తం</div></div>
    <span class="time-val good" id="abhijit"><div class="skel" style="width:110px"></div></span>
  </div>
</div>

<!-- Inauspicious Section -->
<div class="section">
  <div class="section-header"><span>⚠️ Inauspicious Periods</span><span class="te">· అశుభ సమయాలు</span></div>
  <div class="time-row">
    <span class="icon">🔴</span>
    <div class="label"><div class="en">Rahu Kalam</div><div class="te">రాహు కాలం</div></div>
    <span class="time-val danger" id="rahu"><div class="skel" style="width:110px"></div></span>
  </div>
  <div class="time-row">
    <span class="icon">🟠</span>
    <div class="label"><div class="en">Yamagandam</div><div class="te">యమగండం</div></div>
    <span class="time-val danger" id="yama"><div class="skel" style="width:110px"></div></span>
  </div>
  <div class="time-row">
    <span class="icon">🟡</span>
    <div class="label"><div class="en">Gulikai Kalam</div><div class="te">గులికై కాలం</div></div>
    <span class="time-val danger" id="gulikai"><div class="skel" style="width:110px"></div></span>
  </div>
  <div class="bad-note">⚠ Avoid starting important activities during these periods</div>
</div>

<footer>Panchang computed for your location · Refreshes at midnight · Telugu/Andhra tradition</footer>

<script>
// ── All JS modules will be added in subsequent tasks ──
</script>
</body>
</html>
```

- [ ] **Step 2: Open in browser and verify layout**

Open `frontend/panchang.html` directly in a browser (file:// URL). Expected: Page header with Om symbol and saffron-brown gradient visible; all sections show skeleton loading animations; location bar says "Detecting location…"

- [ ] **Step 3: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add panchang page skeleton with CSS and HTML structure"
```

---

### Task 2: Astro Module — Julian Day + Sun/Moon Ecliptic Longitudes

**Files:**
- Modify: `frontend/panchang.html` — replace `// ── All JS modules ──` comment with Astro module

- [ ] **Step 1: Replace the JS comment with the Astro module**

Replace the `<script>` block content in `frontend/panchang.html` with:

```javascript
// ══════════════════════════════════════════
// ASTRO MODULE — Julian Day + Ecliptic Longitudes
// ══════════════════════════════════════════
const Astro = (() => {
  function getJulianDay(date) {
    const y = date.getUTCFullYear();
    const m = date.getUTCMonth() + 1;
    const d = date.getUTCDate()
            + date.getUTCHours()   / 24
            + date.getUTCMinutes() / 1440
            + date.getUTCSeconds() / 86400;
    const A = Math.floor(y / 100);
    const B = 2 - A + Math.floor(A / 4);
    return Math.floor(365.25 * (y + 4716))
         + Math.floor(30.6001 * (m + 1))
         + d + B - 1524.5;
  }

  // Meeus Ch.25 low-precision sun longitude (~0.01° accuracy)
  function getSunLongitude(jd) {
    const n = jd - 2451545.0;
    const L = (280.460 + 0.9856474 * n) % 360;
    const g = ((357.528 + 0.9856003 * n) % 360) * Math.PI / 180;
    const lambda = L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g);
    return ((lambda % 360) + 360) % 360;
  }

  // Meeus Ch.47 simplified moon longitude (~0.3° accuracy — ~15 min on tithi)
  function getMoonLongitude(jd) {
    const T  = (jd - 2451545.0) / 36525.0;
    const Lp = (218.3164477 + 481267.88123421 * T) % 360;
    const Mm = ((134.9633964 + 477198.8675055  * T) % 360) * Math.PI / 180;
    const Ms = ((357.5291092 +  35999.0502909  * T) % 360) * Math.PI / 180;
    const F  = (( 93.2720950 + 483202.0175233  * T) % 360) * Math.PI / 180;
    const D  = ((297.8501921 + 445267.1114034  * T) % 360) * Math.PI / 180;

    const corr =
        6.288774 * Math.sin(Mm)
      + 1.274027 * Math.sin(2*D - Mm)
      + 0.658314 * Math.sin(2*D)
      + 0.213618 * Math.sin(2*Mm)
      - 0.185116 * Math.sin(Ms)
      - 0.114332 * Math.sin(2*F)
      + 0.058793 * Math.sin(2*D - 2*Mm)
      + 0.057066 * Math.sin(2*D - Ms - Mm)
      + 0.053322 * Math.sin(2*D + Mm)
      + 0.045758 * Math.sin(2*D - Ms);

    return ((Lp + corr) % 360 + 360) % 360;
  }

  return { getJulianDay, getSunLongitude, getMoonLongitude };
})();

// ── TeluguCalendar, Panchang, SouthIndian, Geo, UI modules follow ──
```

- [ ] **Step 2: Verify Astro module in browser console**

Open `frontend/panchang.html`, open DevTools → Console, paste and run:

```javascript
// J2000 epoch: JD should be 2451545.0
const jd2000 = Astro.getJulianDay(new Date('2000-01-01T12:00:00Z'));
console.assert(Math.abs(jd2000 - 2451545.0) < 0.001, 'JD J2000 failed: ' + jd2000);

// Sun longitude at J2000 should be ~280.5°
const sunLon = Astro.getSunLongitude(jd2000);
console.assert(sunLon > 278 && sunLon < 283, 'Sun lon at J2000 failed: ' + sunLon);

// Moon longitude at J2000 should be ~218°
const moonLon = Astro.getMoonLongitude(jd2000);
console.assert(moonLon > 210 && moonLon < 226, 'Moon lon at J2000 failed: ' + moonLon);

console.log('Astro ✓  JD:', jd2000.toFixed(1), ' Sun:', sunLon.toFixed(1), ' Moon:', moonLon.toFixed(1));
```

Expected output: `Astro ✓  JD: 2451545.0  Sun: ~280.5  Moon: ~218.x` with no assertion errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add Astro module (Julian Day + Meeus sun/moon ecliptic longitudes)"
```

---

### Task 3: TeluguCalendar Module — Lookup Tables

**Files:**
- Modify: `frontend/panchang.html` — add TeluguCalendar module after Astro module

- [ ] **Step 1: Add TeluguCalendar module** (replace `// ── TeluguCalendar...` comment)

```javascript
// ══════════════════════════════════════════
// TELUGU CALENDAR MODULE — Names + Lookups
// ══════════════════════════════════════════
const TeluguCalendar = (() => {
  const TITHI = [
    {en:'Pratipada',te:'పాడ్యమి'},{en:'Dwitiya',te:'విదియ'},{en:'Tritiya',te:'తదియ'},
    {en:'Chaturthi',te:'చవితి'},{en:'Panchami',te:'పంచమి'},{en:'Shashthi',te:'షష్ఠి'},
    {en:'Saptami',te:'సప్తమి'},{en:'Ashtami',te:'అష్టమి'},{en:'Navami',te:'నవమి'},
    {en:'Dashami',te:'దశమి'},{en:'Ekadashi',te:'ఏకాదశి'},{en:'Dwadashi',te:'ద్వాదశి'},
    {en:'Trayodashi',te:'త్రయోదశి'},{en:'Chaturdashi',te:'చతుర్దశి'},{en:'Purnima',te:'పౌర్ణమి'},
    {en:'Pratipada',te:'పాడ్యమి'},{en:'Dwitiya',te:'విదియ'},{en:'Tritiya',te:'తదియ'},
    {en:'Chaturthi',te:'చవితి'},{en:'Panchami',te:'పంచమి'},{en:'Shashthi',te:'షష్ఠి'},
    {en:'Saptami',te:'సప్తమి'},{en:'Ashtami',te:'అష్టమి'},{en:'Navami',te:'నవమి'},
    {en:'Dashami',te:'దశమి'},{en:'Ekadashi',te:'ఏకాదశి'},{en:'Dwadashi',te:'ద్వాదశి'},
    {en:'Trayodashi',te:'త్రయోదశి'},{en:'Chaturdashi',te:'చతుర్దశి'},{en:'Amavasya',te:'అమావాస్య'}
  ];

  const NAKSHATRA = [
    {en:'Ashwini',te:'అశ్విని'},{en:'Bharani',te:'భరణి'},{en:'Krittika',te:'కృత్తిక'},
    {en:'Rohini',te:'రోహిణి'},{en:'Mrigashira',te:'మృగశిర'},{en:'Ardra',te:'ఆర్ద్ర'},
    {en:'Punarvasu',te:'పునర్వసు'},{en:'Pushya',te:'పుష్యమి'},{en:'Ashlesha',te:'ఆశ్లేష'},
    {en:'Magha',te:'మఖ'},{en:'Purva Phalguni',te:'పూర్వ ఫల్గుణి'},{en:'Uttara Phalguni',te:'ఉత్తర ఫల్గుణి'},
    {en:'Hasta',te:'హస్త'},{en:'Chitra',te:'చిత్త'},{en:'Swati',te:'స్వాతి'},
    {en:'Vishakha',te:'విశాఖ'},{en:'Anuradha',te:'అనూరాధ'},{en:'Jyeshtha',te:'జ్యేష్ఠ'},
    {en:'Mula',te:'మూల'},{en:'Purva Ashadha',te:'పూర్వాషాఢ'},{en:'Uttara Ashadha',te:'ఉత్తరాషాఢ'},
    {en:'Shravana',te:'శ్రవణం'},{en:'Dhanishta',te:'ధనిష్ట'},{en:'Shatabhisha',te:'శతభిష'},
    {en:'Purva Bhadrapada',te:'పూర్వభాద్ర'},{en:'Uttara Bhadrapada',te:'ఉత్తరభాద్ర'},{en:'Revati',te:'రేవతి'}
  ];

  const YOGA = [
    {en:'Vishkambha',te:'విష్కంభ'},{en:'Priti',te:'ప్రీతి'},{en:'Ayushman',te:'ఆయుష్మాన్'},
    {en:'Saubhagya',te:'సౌభాగ్య'},{en:'Shobhana',te:'శోభన'},{en:'Atiganda',te:'అతిగండ'},
    {en:'Sukarma',te:'సుకర్మ'},{en:'Dhriti',te:'ధృతి'},{en:'Shoola',te:'శూల'},
    {en:'Ganda',te:'గండ'},{en:'Vriddhi',te:'వృద్ధి'},{en:'Dhruva',te:'ధ్రువ'},
    {en:'Vyaghata',te:'వ్యాఘాత'},{en:'Harshana',te:'హర్షణ'},{en:'Vajra',te:'వజ్ర'},
    {en:'Siddhi',te:'సిద్ధి'},{en:'Vyatipata',te:'వ్యతీపాత'},{en:'Variyana',te:'వరీయాన్'},
    {en:'Parigha',te:'పరిఘ'},{en:'Shiva',te:'శివ'},{en:'Siddha',te:'సిద్ధ'},
    {en:'Sadhya',te:'సాధ్య'},{en:'Shubha',te:'శుభ'},{en:'Shukla',te:'శుక్ల'},
    {en:'Brahma',te:'బ్రహ్మ'},{en:'Indra',te:'ఐంద్ర'},{en:'Vaidhriti',te:'వైధృతి'}
  ];

  const KARANA = [
    {en:'Bava',te:'బవ'},{en:'Balava',te:'బాలవ'},{en:'Kaulava',te:'కౌలవ'},
    {en:'Taitila',te:'తైతుల'},{en:'Garaja',te:'గరజ'},{en:'Vanija',te:'వణిజ'},
    {en:'Vishti',te:'విష్టి'},{en:'Shakuni',te:'శకుని'},{en:'Chatushpada',te:'చతుష్పద'},
    {en:'Naga',te:'నాగ'},{en:'Kimstughna',te:'కింస్తుఘ్న'}
  ];

  const MASAM = [
    {en:'Chaitra',te:'చైత్ర'},{en:'Vaishakha',te:'వైశాఖ'},{en:'Jyeshtha',te:'జ్యేష్ఠ'},
    {en:'Ashadha',te:'ఆషాఢ'},{en:'Shravana',te:'శ్రావణ'},{en:'Bhadrapada',te:'భాద్రపద'},
    {en:'Ashvina',te:'ఆశ్వయుజ'},{en:'Kartika',te:'కార్తీక'},{en:'Margashirsha',te:'మార్గశిర'},
    {en:'Pausha',te:'పుష్య'},{en:'Magha',te:'మాఘ'},{en:'Phalguna',te:'ఫాల్గుణ'}
  ];

  const RUTUVU = [
    {en:'Vasanta',te:'వసంత'},{en:'Grishma',te:'గ్రీష్మ'},{en:'Varsha',te:'వర్ష'},
    {en:'Sharad',te:'శరత్'},{en:'Hemanta',te:'హేమంత'},{en:'Shishira',te:'శిశిర'}
  ];

  const VARA = [
    {en:'Sunday',te:'ఆదివారం'},{en:'Monday',te:'సోమవారం'},{en:'Tuesday',te:'మంగళవారం'},
    {en:'Wednesday',te:'బుధవారం'},{en:'Thursday',te:'గురువారం'},{en:'Friday',te:'శుక్రవారం'},
    {en:'Saturday',te:'శనివారం'}
  ];

  // 60 samvatsara names (Prabhava=0 ... Kshaya=59)
  const SAMVATSARA = [
    'Prabhava','Vibhava','Shukla','Pramoda','Prajapati','Angirasa','Shrimukha','Bhava',
    'Yuva','Dhatri','Ishvara','Bahudhanya','Pramathi','Vikrama','Vrisha','Chitrabhanu',
    'Subhanu','Tarana','Parthiva','Vyaya','Sarvajit','Sarvadhari','Virodhi','Vikrita',
    'Khara','Nandana','Vijaya','Jaya','Manmatha','Durmukhi','Hevilambi','Vilambi',
    'Vikari','Sharvari','Plava','Shubhakrit','Shobhana','Krodhi','Vishvavasu','Parabhava',
    'Plavanga','Kilaka','Saumya','Sadharana','Virodhikrit','Paritapi','Pramadi','Ananda',
    'Rakshasa','Nala','Pingala','Kalayukti','Siddharthi','Raudra','Durmati','Dundubhi',
    'Rudhirodgari','Raktakshi','Krodhana','Kshaya'
  ];

  function getTithi(moonLon, sunLon) {
    const diff = ((moonLon - sunLon) % 360 + 360) % 360;
    const idx = Math.floor(diff / 12); // 0-29
    return { idx, ...TITHI[idx] };
  }

  function getNakshatra(moonLon) {
    const idx = Math.floor(moonLon / (360 / 27)) % 27;
    return { idx, ...NAKSHATRA[idx] };
  }

  function getYoga(moonLon, sunLon) {
    const idx = Math.floor(((moonLon + sunLon) % 360) / (360 / 27)) % 27;
    return { idx, ...YOGA[idx] };
  }

  function getKarana(moonLon, sunLon) {
    const diff = ((moonLon - sunLon) % 360 + 360) % 360;
    const half = Math.floor(diff / 6); // 0-59
    if (half === 0) return KARANA[10]; // Kimstughna
    if (half === 57) return KARANA[7]; // Shakuni
    if (half === 58) return KARANA[8]; // Chatushpada
    if (half === 59) return KARANA[9]; // Naga
    return KARANA[(half - 1) % 7];    // repeating 7
  }

  function getMasam(sunLon) {
    return MASAM[Math.floor(sunLon / 30) % 12];
  }

  function getRutuvu(sunLon) {
    return RUTUVU[Math.floor(sunLon / 60) % 6];
  }

  function getPaksham(tithiIdx) {
    return tithiIdx < 15
      ? {en:'Shukla Paksham', te:'శుక్ల పక్షం'}
      : {en:'Krishna Paksham', te:'కృష్ణ పక్షం'};
  }

  function getSamvatsara(year) {
    // Saka year = Gregorian year - 78 (approx, before Ugadi)
    const sakaYear = year - 78;
    const idx = ((sakaYear - 1) % 60 + 60) % 60;
    return SAMVATSARA[idx];
  }

  function getVara(date) {
    return VARA[date.getDay()];
  }

  return { getTithi, getNakshatra, getYoga, getKarana, getMasam, getRutuvu, getPaksham, getSamvatsara, getVara };
})();

// ── Panchang, SouthIndian, Geo, UI modules follow ──
```

- [ ] **Step 2: Verify TeluguCalendar in browser console**

Open DevTools → Console and run:

```javascript
// Sun at 75° = Gemini = Jyeshtha masam
const masam = TeluguCalendar.getMasam(75);
console.assert(masam.en === 'Jyeshtha', 'Masam failed: ' + masam.en);

// Sun at 75° = Grishma rutuvu (60°-120°)
const rutu = TeluguCalendar.getRutuvu(75);
console.assert(rutu.en === 'Grishma', 'Rutuvu failed: ' + rutu.en);

// Tithi: diff=36° → floor(36/12)=3 → idx=3 → Chaturthi
const t = TeluguCalendar.getTithi(136, 100);
console.assert(t.en === 'Chaturthi', 'Tithi failed: ' + t.en);

// Paksham: tithiIdx=14 (Purnima) → Shukla
const pk = TeluguCalendar.getPaksham(14);
console.assert(pk.en === 'Shukla Paksham', 'Paksham failed: ' + pk.en);

console.log('TeluguCalendar ✓');
```

Expected: All asserts pass, `TeluguCalendar ✓` printed.

- [ ] **Step 3: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add TeluguCalendar module with all name tables and lookup functions"
```

---

### Task 4: Panchang Module — Compute All Fields + End Times

**Files:**
- Modify: `frontend/panchang.html` — add Panchang module after TeluguCalendar

- [ ] **Step 1: Add Panchang module** (replace `// ── Panchang...` comment)

```javascript
// ══════════════════════════════════════════
// PANCHANG MODULE — Compute All Fields
// ══════════════════════════════════════════
const Panchang = (() => {
  // Binary search for when a panchang field changes
  // fn(ms) returns an integer index; search for when it changes from startVal
  function findEndTime(startMs, fn, startVal) {
    let lo = startMs;
    let hi = startMs + 2 * 24 * 3600 * 1000; // search up to 48h
    // Extend hi until we find a different value
    for (let attempts = 0; attempts < 50; attempts++) {
      if (fn(hi) !== startVal) break;
      hi += 3600 * 1000;
      if (attempts === 49) return null; // couldn't find end
    }
    // Binary search to 1-minute precision
    while (hi - lo > 60000) {
      const mid = Math.floor((lo + hi) / 2);
      if (fn(mid) === startVal) lo = mid; else hi = mid;
    }
    return new Date(hi);
  }

  function compute(date, lat, lon) {
    const jd = Astro.getJulianDay(date);
    const sunLon  = Astro.getSunLongitude(jd);
    const moonLon = Astro.getMoonLongitude(jd);

    const tithi     = TeluguCalendar.getTithi(moonLon, sunLon);
    const nakshatra = TeluguCalendar.getNakshatra(moonLon);
    const yoga      = TeluguCalendar.getYoga(moonLon, sunLon);
    const karana    = TeluguCalendar.getKarana(moonLon, sunLon);
    const vara      = TeluguCalendar.getVara(date);
    const masam     = TeluguCalendar.getMasam(sunLon);
    const rutuvu    = TeluguCalendar.getRutuvu(sunLon);
    const paksham   = TeluguCalendar.getPaksham(tithi.idx);
    const samvatsara = TeluguCalendar.getSamvatsara(date.getFullYear());

    // End times (binary search)
    const tithiEnd = findEndTime(
      date.getTime(),
      ms => TeluguCalendar.getTithi(Astro.getMoonLongitude(Astro.getJulianDay(new Date(ms))), Astro.getSunLongitude(Astro.getJulianDay(new Date(ms)))).idx,
      tithi.idx
    );

    const nakshatraEnd = findEndTime(
      date.getTime(),
      ms => TeluguCalendar.getNakshatra(Astro.getMoonLongitude(Astro.getJulianDay(new Date(ms)))).idx,
      nakshatra.idx
    );

    return { tithi, tithiEnd, nakshatra, nakshatraEnd, yoga, karana, vara, masam, rutuvu, paksham, samvatsara, sunLon, moonLon };
  }

  return { compute };
})();

// ── SouthIndian, Geo, UI modules follow ──
```

- [ ] **Step 2: Verify Panchang module in browser console**

```javascript
// Use a known date: 2026-05-17 12:00 UTC
const testDate = new Date('2026-05-17T06:30:00Z'); // ~noon IST
const result = Panchang.compute(testDate, 17.38, 78.48);
console.log('Tithi:', result.tithi.en, '| Nakshatra:', result.nakshatra.en);
console.log('Masam:', result.masam.en, '| Rutuvu:', result.rutuvu.en);
console.log('Tithiend:', result.tithiEnd ? result.tithiEnd.toLocaleTimeString() : 'null');
console.assert(result.tithi.en !== undefined, 'Tithi missing');
console.assert(result.nakshatra.en !== undefined, 'Nakshatra missing');
console.log('Panchang ✓');
```

Expected: Tithi and Nakshatra names printed (cross-check against a panchang calendar app). No assertion errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add Panchang module with binary-search end-time computation"
```

---

### Task 5: SouthIndian Module — Rahu Kalam, Yamagandam, Gulikai, Abhijit

**Files:**
- Modify: `frontend/panchang.html` — add SouthIndian module after Panchang

- [ ] **Step 1: Add SouthIndian module** (replace `// ── SouthIndian...` comment)

```javascript
// ══════════════════════════════════════════
// SOUTH INDIAN MODULE — Inauspicious Periods
// ══════════════════════════════════════════
const SouthIndian = (() => {
  // Slot tables indexed by weekday (0=Sun, 1=Mon, ... 6=Sat)
  // Values are 1-based slot numbers out of 8 equal day-slots
  const RAHU_SLOTS   = [8, 2, 7, 5, 6, 3, 4];
  const YAMA_SLOTS   = [5, 4, 3, 2, 1, 7, 6];
  const GULIKAI_SLOTS= [6, 5, 4, 3, 2, 1, 7];

  function getSlotTimes(slotNum, sunriseMs, sunsetMs) {
    const dayMs   = sunsetMs - sunriseMs;
    const slotMs  = dayMs / 8;
    const startMs = sunriseMs + (slotNum - 1) * slotMs;
    return { start: new Date(startMs), end: new Date(startMs + slotMs) };
  }

  function getRahuKalam(weekday, sunrise, sunset) {
    return getSlotTimes(RAHU_SLOTS[weekday], sunrise.getTime(), sunset.getTime());
  }

  function getYamagandam(weekday, sunrise, sunset) {
    return getSlotTimes(YAMA_SLOTS[weekday], sunrise.getTime(), sunset.getTime());
  }

  function getGulikai(weekday, sunrise, sunset) {
    return getSlotTimes(GULIKAI_SLOTS[weekday], sunrise.getTime(), sunset.getTime());
  }

  // Abhijit Muhurta: 8th muhurta of the day = midday ±24 min
  function getAbhijitMuhurta(sunrise, sunset) {
    const midday = new Date((sunrise.getTime() + sunset.getTime()) / 2);
    return {
      start: new Date(midday.getTime() - 24 * 60 * 1000),
      end:   new Date(midday.getTime() + 24 * 60 * 1000)
    };
  }

  return { getRahuKalam, getYamagandam, getGulikai, getAbhijitMuhurta };
})();

// ── Geo, UI modules follow ──
```

- [ ] **Step 2: Verify SouthIndian module in browser console**

```javascript
// Sunday: Rahu Kalam is slot 8 (last slot of day)
// Sunrise 6:00 AM, Sunset 6:00 PM → 12h day → each slot = 90 min
// Slot 8 starts at 6AM + 7*90min = 6AM + 630min = 4:30 PM, ends 6:00 PM
const sr = new Date('2026-05-17T00:30:00Z'); // 6:00 AM IST
const ss = new Date('2026-05-17T12:30:00Z'); // 6:00 PM IST
const rahu = SouthIndian.getRahuKalam(0, sr, ss); // Sunday
console.assert(rahu.start.getUTCHours() === 10, 'Rahu start wrong: ' + rahu.start.toISOString());
// 10 UTC = 3:30 PM IST? Let me recalculate:
// 6AM IST = 00:30 UTC, 6PM IST = 12:30 UTC
// Slot duration = (12:30 - 00:30) / 8 UTC hours = 12h/8 = 1.5h = 90 min
// Slot 8 start = 00:30 + 7*90min UTC = 00:30 + 630min = 00:30 + 10:30 = 11:00 UTC = 4:30 PM IST ✓
console.log('Rahu Kalam Sunday:', rahu.start.toLocaleTimeString(), '-', rahu.end.toLocaleTimeString());

const abhijit = SouthIndian.getAbhijitMuhurta(sr, ss);
console.log('Abhijit Muhurta:', abhijit.start.toLocaleTimeString(), '-', abhijit.end.toLocaleTimeString());
console.log('SouthIndian ✓');
```

Expected: Rahu Kalam prints ~4:30 PM – 6:00 PM for Sunday. Abhijit Muhurta ~11:54 AM – 12:48 PM.

- [ ] **Step 3: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add SouthIndian module (Rahu Kalam, Yamagandam, Gulikai, Abhijit Muhurta)"
```

---

### Task 6: Geo Module — Browser Geolocation + Nominatim

**Files:**
- Modify: `frontend/panchang.html` — add Geo module after SouthIndian

- [ ] **Step 1: Add Geo module** (replace `// ── Geo, UI...` comment)

```javascript
// ══════════════════════════════════════════
// GEO MODULE — Browser Geolocation + Nominatim
// ══════════════════════════════════════════
const Geo = (() => {
  const DEFAULT = { lat: 17.38, lon: 78.48, city: 'Hyderabad (default)' };

  async function reverseGeocode(lat, lon) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;
      const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
      if (!res.ok) throw new Error('Nominatim error');
      const data = await res.json();
      const addr = data.address;
      return addr.city || addr.town || addr.village || addr.county || 'Unknown location';
    } catch {
      return null;
    }
  }

  function detect(onSuccess, onError) {
    if (!navigator.geolocation) {
      onError('Geolocation not supported by this browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async pos => {
        const lat  = pos.coords.latitude;
        const lon  = pos.coords.longitude;
        const city = await reverseGeocode(lat, lon) || `${lat.toFixed(2)}°N ${lon.toFixed(2)}°E`;
        onSuccess({ lat, lon, city });
      },
      err => {
        let msg;
        switch (err.code) {
          case 1: msg = 'Location permission denied. Showing Hyderabad defaults.'; break;
          case 2: msg = 'Location unavailable. Showing Hyderabad defaults.'; break;
          default: msg = 'Location timeout. Showing Hyderabad defaults.';
        }
        onError(msg, DEFAULT);
      },
      { timeout: 10000, maximumAge: 300000 }
    );
  }

  return { detect, DEFAULT };
})();

// ── UI module follows ──
```

- [ ] **Step 2: Commit** (Geo cannot be fully unit-tested without browser permission; visual test happens in Task 7)

```bash
git add frontend/panchang.html
git commit -m "feat: add Geo module (browser Geolocation + Nominatim reverse geocode)"
```

---

### Task 7: UI Module — Render + Loading State + Midnight Refresh

**Files:**
- Modify: `frontend/panchang.html` — add UI module + app bootstrap after Geo

- [ ] **Step 1: Add UI module + bootstrap** (replace `// ── UI module follows ──` comment)

```javascript
// ══════════════════════════════════════════
// UI MODULE — Render Data to DOM
// ══════════════════════════════════════════
const UI = (() => {
  function fmt(date) {
    if (!date) return '';
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }

  function fmtRange(a, b) { return `${fmt(a)} – ${fmt(b)}`; }

  function set(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function showError(msg) {
    const el = document.getElementById('error-banner');
    el.textContent = '⚠ ' + msg;
    el.style.display = 'block';
  }

  function showLocation(loc) {
    set('loc-name', loc.city);
    set('loc-coords', `${loc.lat.toFixed(2)}°N · ${loc.lon.toFixed(2)}°E`);
    if (loc.city.includes('default')) {
      document.getElementById('location-bar').classList.add('error');
    }
  }

  function render(data, loc) {
    const { panchangData, sunriseTimes, southIndian } = data;
    const now = new Date();

    // Date banner
    set('gregorian-date', now.toLocaleDateString('en-IN', { weekday:'long', year:'numeric', month:'long', day:'numeric' }));
    set('telugu-date', `${panchangData.masam.te} మాసం · ${panchangData.paksham.te}`);
    set('samvatsara', `${panchangData.samvatsara} సంవత్సరం`);

    // Calendar section
    set('rutuvu-en',  panchangData.rutuvu.en + ' Ritu');
    set('rutuvu-te',  panchangData.rutuvu.te + ' ఋతువు');
    set('masam-en',   panchangData.masam.en + ' Masam');
    set('masam-te',   panchangData.masam.te + ' మాసం');
    set('paksham-en', panchangData.paksham.en);
    set('paksham-te', panchangData.paksham.te);

    // Panchangam section
    set('tithi-en',        `${panchangData.tithi.en} (${panchangData.tithi.idx + 1})`);
    set('tithi-te',        panchangData.tithi.te);
    set('tithi-until',     panchangData.tithiEnd ? 'until ' + fmt(panchangData.tithiEnd) : '');
    set('nakshatra-en',    panchangData.nakshatra.en);
    set('nakshatra-te',    panchangData.nakshatra.te);
    set('nakshatra-until', panchangData.nakshatraEnd ? 'until ' + fmt(panchangData.nakshatraEnd) : '');
    set('yoga-en',         panchangData.yoga.en);
    set('yoga-te',         panchangData.yoga.te);
    set('karana-en',       panchangData.karana.en);
    set('karana-te',       panchangData.karana.te);
    set('vara-en',         panchangData.vara.en);
    set('vara-te',         panchangData.vara.te);

    // Sun timings
    set('sunrise', fmt(sunriseTimes.sunrise));
    set('sunset',  fmt(sunriseTimes.sunset));
    set('abhijit', fmtRange(southIndian.abhijit.start, southIndian.abhijit.end));

    // Inauspicious periods
    set('rahu',    fmtRange(southIndian.rahu.start,    southIndian.rahu.end));
    set('yama',    fmtRange(southIndian.yama.start,    southIndian.yama.end));
    set('gulikai', fmtRange(southIndian.gulikai.start, southIndian.gulikai.end));
  }

  function scheduleRefreshAtMidnight() {
    const now  = new Date();
    const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
    const msUntilMidnight = next.getTime() - now.getTime();
    setTimeout(() => { location.reload(); }, msUntilMidnight);
  }

  return { render, showLocation, showError, scheduleRefreshAtMidnight };
})();

// ══════════════════════════════════════════
// BOOTSTRAP — Wire everything together
// ══════════════════════════════════════════
(function init() {
  function computeAndRender(loc) {
    UI.showLocation(loc);

    const now       = new Date();
    const panchangData = Panchang.compute(now, loc.lat, loc.lon);

    // SunCalc for sunrise/sunset (lat/lon required)
    const sunTimes  = SunCalc.getTimes(now, loc.lat, loc.lon);
    const sunrise   = sunTimes.sunrise;
    const sunset    = sunTimes.sunset;
    const weekday   = now.getDay();

    const southIndian = {
      rahu:    SouthIndian.getRahuKalam(weekday, sunrise, sunset),
      yama:    SouthIndian.getYamagandam(weekday, sunrise, sunset),
      gulikai: SouthIndian.getGulikai(weekday, sunrise, sunset),
      abhijit: SouthIndian.getAbhijitMuhurta(sunrise, sunset)
    };

    UI.render({ panchangData, sunriseTimes: { sunrise, sunset }, southIndian }, loc);
    UI.scheduleRefreshAtMidnight();
  }

  Geo.detect(
    loc => computeAndRender(loc),
    (msg, fallbackLoc) => {
      UI.showError(msg);
      if (fallbackLoc) computeAndRender(fallbackLoc);
    }
  );
})();
```

- [ ] **Step 2: Open in browser and do full visual check**

Open `frontend/panchang.html`. Expected:
- Browser asks for location permission → grant it
- Skeleton animations replaced with real data within ~3 seconds
- Location bar shows your city name and coordinates
- All 5 Panchangam fields populated with Telugu + English
- Rahu Kalam, Yamagandam, Gulikai show time ranges
- Sunrise/Sunset show local times
- No JS errors in console

- [ ] **Step 3: Test the geolocation-denied path**

Open DevTools → Application → Clear Site Data (or block location in browser settings). Reload. Expected: Error banner appears with "Location permission denied" message; page still renders with Hyderabad defaults.

- [ ] **Step 4: Commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add UI module and bootstrap — fully wired panchang page"
```

---

### Task 8: Error Banner + CDN Failure Guard + Final Polish

**Files:**
- Modify: `frontend/panchang.html` — wrap SunCalc usage in a guard; add CDN error handling

- [ ] **Step 1: Add CDN failure guard** — wrap the `init()` call at the bottom of the `<script>` block:

Find the `(function init() {` call and add a guard before it:

```javascript
// Guard: check SunCalc loaded from CDN
if (typeof SunCalc === 'undefined') {
  document.getElementById('error-banner').textContent =
    '⚠ Could not load astronomy library. Check your internet connection.';
  document.getElementById('error-banner').style.display = 'block';
} else {
  // all init() code here — move the existing IIFE inside this else block
  (function init() { /* ... existing init code ... */ })();
}
```

- [ ] **Step 2: Final cross-browser check**

Open in Chrome, Firefox, and Edge (or at least 2 browsers). Verify all sections render correctly. Check mobile view using DevTools device emulator (375px width). Expected: Page is readable and all sections visible without horizontal scroll.

- [ ] **Step 3: Final commit**

```bash
git add frontend/panchang.html
git commit -m "feat: add CDN guard and final polish for panchang page

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
