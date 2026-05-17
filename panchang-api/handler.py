"""
Lambda entry point for the Panchang API.
GET /panchang?lat={float}&lon={float}&date={YYYY-MM-DD}
"""
import json
import traceback
from datetime import datetime, timedelta

import pytz

try:
    from timezonefinder import TimezoneFinder
    _tf = TimezoneFinder()
except ImportError:
    _tf = None

from compute.astro import local_date_to_jd
from compute.panchang import compute_panchang
from compute.sankalpam import get_geographic, build_sankalpam


def _error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def _get_timezone(lat: float, lon: float) -> str:
    """Get timezone name from lat/lon, fallback to UTC."""
    if _tf is None:
        return "UTC"
    try:
        tz = _tf.timezone_at(lng=lon, lat=lat)
        return tz or "UTC"
    except Exception:
        return "UTC"


def _seconds_until_midnight(tz_name: str) -> int:
    """Seconds from now until midnight in the given timezone."""
    try:
        tz = pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.utc
    now = datetime.now(tz)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((midnight - now).total_seconds()), 1)


def lambda_handler(event: dict, context) -> dict:
    params = event.get("queryStringParameters") or {}

    # ── Validate lat / lon ──
    try:
        lat = float(params["lat"])
        lon = float(params["lon"])
    except (KeyError, ValueError, TypeError):
        return _error(400, "lat and lon are required numeric query parameters")

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return _error(400, f"lat must be -90..90, lon must be -180..180 (got lat={lat}, lon={lon})")

    # ── Resolve timezone ──
    tz_name = _get_timezone(lat, lon)

    # ── Resolve date ──
    date_param = params.get("date")
    if date_param:
        try:
            parsed = datetime.strptime(date_param, "%Y-%m-%d")
            year, month, day = parsed.year, parsed.month, parsed.day
        except ValueError:
            return _error(400, f"date must be YYYY-MM-DD, got: {date_param!r}")
    else:
        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            tz = pytz.utc
        now_local = datetime.now(tz)
        year, month, day = now_local.year, now_local.month, now_local.day

    # ── Compute ──
    try:
        jd = local_date_to_jd(year, month, day, tz_name)
        pan = compute_panchang(jd, lat, lon, tz_name)
        geo = get_geographic(lat, lon)
        sankalpam = build_sankalpam(pan, geo)
    except Exception:
        traceback.print_exc()
        return _error(500, "Internal calculation error")

    # ── Build response ──
    body = {
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "location": {"lat": lat, "lon": lon, "timezone": tz_name},
        "panchang": pan,
        "sankalpam": sankalpam,
    }

    ttl = _seconds_until_midnight(tz_name)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": f"public, max-age={ttl}",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
