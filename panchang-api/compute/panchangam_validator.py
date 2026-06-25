"""Cross-validates a muhurtam date's panchang elements against Prokerala Panchangam.

Never raises — returns status="unavailable" on any error.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request

# All standard tithi and nakshatra names as Prokerala renders them.
_TITHIS = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Amavasya",
]
_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishaka",
    "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanistha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]
# Aliases that our engine may produce vs. what Prokerala returns
_NAK_ALIASES: dict[str, str] = {
    "jyeshta": "jyeshtha",
    "jyeshtha": "jyeshtha",
    "dhanishtha": "dhanistha",
    "shravana": "shravana",
}

_PROKERALA_BASE = "https://www.prokerala.com/astrology/panchangam/"
_SUNRISE_TOL_MIN = 3   # sunrise match tolerance in minutes

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def _tz_offset(tz_name: str) -> float:
    """Return UTC offset in decimal hours for a timezone name string."""
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
        offset = datetime.datetime.now(tz).utcoffset()
        return offset.total_seconds() / 3600 if offset else 5.5
    except Exception:
        return 5.5


def _build_url(date: datetime.date, lat: float, lon: float, tz_name: str) -> str:
    tz_off = _tz_offset(tz_name)
    date_str = date.strftime("%Y-%m-%d")
    return (
        f"{_PROKERALA_BASE}"
        f"?panchangam-date={date_str}"
        f"&la={lat:.4f}&lo={lon:.4f}"
        f"&tz={tz_off:.1f}&ayanamsa=1"
    )


def _cache_key(date: datetime.date, lat: float, lon: float) -> str:
    return f"panchang-ref/{date.year}/{date.month:02d}/{date.day:02d}/{lat:.2f}_{lon:.2f}.json"


def _read_s3(key: str) -> dict | None:
    bucket = os.environ.get("PANCHANG_CACHE_BUCKET")
    if not bucket:
        return None
    try:
        import boto3
        resp = boto3.client("s3").get_object(Bucket=bucket, Key=key)
        return json.loads(resp["Body"].read())
    except Exception:
        return None


def _write_s3(key: str, data: dict) -> None:
    bucket = os.environ.get("PANCHANG_CACHE_BUCKET")
    if not bucket:
        return
    try:
        import boto3
        boto3.client("s3").put_object(
            Bucket=bucket, Key=key,
            Body=json.dumps(data).encode(),
            ContentType="application/json",
        )
    except Exception:
        pass


def _extract_prokerala(html: str) -> dict[str, str]:
    """Parse Prokerala HTML and return {tithi, nakshatra, sunrise}."""
    result: dict[str, str] = {}

    # Tithi: first matching name inside panchang-data-tithi div
    m = re.search(r'class="[^"]*panchang-data-tithi[^"]*">(.*?)</div>\s*</div>', html, re.DOTALL)
    if m:
        block = m.group(1).lower()
        for name in _TITHIS:
            if name.lower() in block:
                result["tithi"] = name
                break

    # Nakshatra: first matching name inside panchang-data-nakshatra div
    m2 = re.search(r'class="[^"]*panchang-data-nakshatra[^"]*">(.*?)</div>\s*</div>', html, re.DOTALL)
    if m2:
        block = m2.group(1).lower()
        for name in _NAKSHATRAS:
            if name.lower() in block:
                result["nakshatra"] = name
                break

    # Sunrise: look for the sunrise icon label then grab the time
    m3 = re.search(r't-sm[^>]*>\s*Sunrise\s*</span>.*?(\d{1,2}:\d{2}\s*[AP]M)', html, re.DOTALL)
    if m3:
        result["sunrise"] = m3.group(1).strip()

    return result


def _fetch_prokerala(url: str) -> dict[str, str]:
    req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return _extract_prokerala(html)


def _parse_time_to_hours(s: str) -> float | None:
    import time as _time
    s = s.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            t = _time.strptime(s, fmt)
            return t.tm_hour + t.tm_min / 60.0
        except ValueError:
            continue
    return None


def _norm_nak(name: str) -> str:
    return _NAK_ALIASES.get(name.lower(), name.lower())


def validate_muhurtam_date(
    date: datetime.date,
    lat: float,
    lon: float,
    tz_name: str,
    tithi_en: str,
    nakshatra_en: str,
    sunrise: str,
) -> dict:
    """Cross-check our panchang elements against Prokerala for the given date/location.

    Returns dict with keys:
        status: "verified" | "partial" | "mismatch" | "unavailable"
        source: display name of the reference source
        source_url: URL that was checked (also usable as a manual link)
        checked_at: ISO UTC timestamp
        details: {element: {"ours": str, "reference": str, "match": bool}}
    """
    source_url = _build_url(date, lat, lon, tz_name)
    checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    base = {
        "source": "Prokerala Panchangam",
        "source_url": source_url,
        "checked_at": checked_at,
        "details": {},
    }

    cache_key = _cache_key(date, lat, lon)
    raw = _read_s3(cache_key)
    if raw is None:
        try:
            raw = _fetch_prokerala(source_url)
            if raw:
                _write_s3(cache_key, raw)
        except Exception:
            return {**base, "status": "unavailable"}

    if not raw:
        return {**base, "status": "unavailable"}

    details: dict[str, dict] = {}

    # Tithi comparison
    ref_tithi = raw.get("tithi", "")
    tithi_match = bool(
        tithi_en and ref_tithi and tithi_en.lower() == ref_tithi.lower()
    )
    details["tithi"] = {"ours": tithi_en, "reference": ref_tithi, "match": tithi_match}

    # Nakshatra comparison (with alias normalisation)
    ref_nak = raw.get("nakshatra", "")
    nak_match = bool(
        nakshatra_en and ref_nak and _norm_nak(nakshatra_en) == _norm_nak(ref_nak)
    )
    details["nakshatra"] = {"ours": nakshatra_en, "reference": ref_nak, "match": nak_match}

    # Sunrise comparison (within ±3 min)
    ref_sunrise_raw = raw.get("sunrise", "")
    our_h = _parse_time_to_hours(sunrise)
    ref_h = _parse_time_to_hours(ref_sunrise_raw)
    if our_h is not None and ref_h is not None:
        sr_match = abs(our_h - ref_h) * 60 <= _SUNRISE_TOL_MIN
    else:
        sr_match = False
    details["sunrise"] = {"ours": sunrise, "reference": ref_sunrise_raw, "match": sr_match}

    critical_matches = [tithi_match, nak_match]
    if all(critical_matches) and sr_match:
        status = "verified"
    elif all(critical_matches):
        status = "partial"
    else:
        status = "mismatch"

    return {**base, "status": status, "details": details}
