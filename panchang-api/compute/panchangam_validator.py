"""Cross-validates a muhurtam date's panchang elements against Prokerala Panchangam.

Never raises — returns status="unavailable" on any error.
"""
from __future__ import annotations

import datetime
import json
import os
import urllib.request
from html.parser import HTMLParser


# Prokerala label aliases — the labels Prokerala uses in its HTML table.
# Key = canonical name, Value = list of labels to look for (case-insensitive).
_FIELD_ALIASES: dict[str, list[str]] = {
    "tithi":     ["tithi", "thithi"],
    "nakshatra": ["nakshatra", "star", "nakshatram"],
    "sunrise":   ["sunrise", "sun rise", "sun-rise"],
}

_PROKERALA_BASE = "https://www.prokerala.com/astrology/panchangam/date"
_SUNRISE_TOL_MIN = 2   # sunrise match tolerance in minutes


class _TdPairParser(HTMLParser):
    """Collect <td> text content as alternating label/value pairs."""

    def __init__(self) -> None:
        super().__init__()
        self._in_td = False
        self._cells: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "td":
            self._in_td = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            self._in_td = False

    def handle_data(self, data: str) -> None:
        if self._in_td:
            cleaned = data.strip()
            if cleaned:
                self._cells.append(cleaned)

    def label_value_map(self) -> dict[str, str]:
        """Return {label.lower(): value} from alternating td pairs."""
        result: dict[str, str] = {}
        cells = self._cells
        for i in range(0, len(cells) - 1, 2):
            result[cells[i].lower()] = cells[i + 1]
        return result


def _tz_offset(tz_name: str) -> float:
    """Return UTC offset in decimal hours for a timezone name string."""
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
        offset = datetime.datetime.now(tz).utcoffset()
        return offset.total_seconds() / 3600 if offset else 5.5
    except Exception:
        return 5.5  # default to IST


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


def _fetch_prokerala(date: datetime.date, lat: float, lon: float, tz_name: str) -> dict[str, str]:
    """Fetch Prokerala panchangam page and return label→value map."""
    tz_off = _tz_offset(tz_name)
    url = (
        f"{_PROKERALA_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"
        f"?la={lat:.4f}&lo={lon:.4f}&tz={tz_off:.1f}&ayanamsa=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = _TdPairParser()
    parser.feed(html)
    return parser.label_value_map()


def _lookup(raw: dict[str, str], canonical: str) -> str:
    """Look up a canonical field using any of its aliases."""
    for alias in _FIELD_ALIASES.get(canonical, [canonical]):
        val = raw.get(alias)
        if val:
            return val
    return ""


def _parse_time_to_hours(s: str) -> float | None:
    """Parse time string like '05:43 AM' or '05:43' → decimal hours."""
    import time as _time
    s = s.strip()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            t = _time.strptime(s, fmt)
            return t.tm_hour + t.tm_min / 60.0
        except ValueError:
            continue
    return None


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

    Args:
        date: calendar date of the muhurtam
        lat, lon: location coordinates (decimal degrees)
        tz_name: IANA timezone name (e.g. "Asia/Kolkata")
        tithi_en: English tithi name from our engine (e.g. "Dashami")
        nakshatra_en: English nakshatra name from our engine (e.g. "Rohini")
        sunrise: "HH:MM" sunrise time from our engine

    Returns dict with keys:
        status: "verified" | "partial" | "mismatch" | "unavailable"
        source: display name of the reference source
        source_url: URL that was checked
        checked_at: ISO UTC timestamp
        details: {element: {"ours": str, "reference": str, "match": bool}}
    """
    tz_off = _tz_offset(tz_name)
    source_url = (
        f"{_PROKERALA_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"
        f"?la={lat:.4f}&lo={lon:.4f}&tz={tz_off:.1f}&ayanamsa=1"
    )
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
            raw = _fetch_prokerala(date, lat, lon, tz_name)
            if raw:
                _write_s3(cache_key, raw)
        except Exception:
            return {**base, "status": "unavailable"}

    if not raw:
        return {**base, "status": "unavailable"}

    details: dict[str, dict] = {}

    # Tithi comparison (case-insensitive prefix match)
    ref_tithi = _lookup(raw, "tithi")
    tithi_match = bool(
        tithi_en and ref_tithi and tithi_en.lower() in ref_tithi.lower()
    )
    details["tithi"] = {"ours": tithi_en, "reference": ref_tithi, "match": tithi_match}

    # Nakshatra comparison (case-insensitive prefix match)
    ref_nak = _lookup(raw, "nakshatra")
    nak_match = bool(
        nakshatra_en and ref_nak and nakshatra_en.lower() in ref_nak.lower()
    )
    details["nakshatra"] = {"ours": nakshatra_en, "reference": ref_nak, "match": nak_match}

    # Sunrise comparison (within ±2 min)
    ref_sunrise_raw = _lookup(raw, "sunrise")
    our_h = _parse_time_to_hours(sunrise)
    ref_h = _parse_time_to_hours(ref_sunrise_raw)
    if our_h is not None and ref_h is not None:
        sr_match = abs(our_h - ref_h) * 60 <= _SUNRISE_TOL_MIN
    else:
        sr_match = False
    details["sunrise"] = {"ours": sunrise, "reference": ref_sunrise_raw, "match": sr_match}

    # Determine overall status
    critical_matches = [tithi_match, nak_match]
    if all(critical_matches) and sr_match:
        status = "verified"
    elif all(critical_matches):
        status = "partial"
    else:
        status = "mismatch"

    return {**base, "status": status, "details": details}
