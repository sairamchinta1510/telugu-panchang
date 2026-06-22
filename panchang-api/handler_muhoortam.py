"""
Lambda entry point for the Muhoortam API.
  POST /muhoortam/birth-chart    — compute janma nakshatra / rashi / lagna
  POST /muhoortam/find           — find auspicious dates for a given month
  POST /muhoortam/check          — check a specific date/time
  POST /muhoortam/window-detail  — planet rashis for a single ceremony date
"""
from __future__ import annotations
import json
import traceback
import urllib.request
import urllib.parse

from timezonefinder import TimezoneFinder

from compute.birth_chart import compute_birth_chart
from compute.muhurta_finder import find_muhurtas_for_month, check_muhurta_day
from compute.astro import local_date_to_jd, compute_planet_rashis

_tf = TimezoneFinder()


def _error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def _ok(data: dict) -> dict:
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, ensure_ascii=False),
    }


def _geocode(place: str) -> dict:
    """Resolve a place name to lat, lon, and IANA timezone using Nominatim."""
    params = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "muhoortam-api/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        results = json.loads(resp.read())
    if not results:
        raise ValueError(f"Place not found: {place!r}")
    r = results[0]
    lat, lon = float(r["lat"]), float(r["lon"])
    tz_name = _tf.timezone_at(lng=lon, lat=lat) or "UTC"
    return {"lat": lat, "lon": lon, "tz_name": tz_name}


def lambda_handler(event: dict, context) -> dict:
    path = event.get("rawPath") or event.get("path") or ""

    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _error(400, "Request body must be valid JSON")

    if path.endswith("/birth-chart"):
        return _handle_birth_chart(body)
    if path.endswith("/find"):
        return _handle_find(body)
    if path.endswith("/check"):
        return _handle_check(body)
    if path.endswith("/window-detail"):
        return _handle_window_detail(body)
    return _error(404, "Unknown endpoint")


def _handle_birth_chart(body: dict) -> dict:
    try:
        dob      = body["dob"]    # "DD/MM/YYYY"
        time_str = body["time"]   # "HH:MM"
        place    = body["place"]
    except KeyError as e:
        return _error(400, f"Missing field: {e}")

    try:
        day, month, year = [int(x) for x in dob.split("/")]
        hour, minute     = [int(x) for x in time_str.split(":")]
    except (ValueError, TypeError):
        return _error(400, "dob must be DD/MM/YYYY and time must be HH:MM")

    try:
        geo = _geocode(place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        chart = compute_birth_chart(
            year, month, day, hour, minute,
            geo["lat"], geo["lon"], geo["tz_name"],
        )
    except Exception:
        traceback.print_exc()
        return _error(500, "Birth chart calculation failed")

    return _ok(chart)


def _handle_find(body: dict) -> dict:
    try:
        year           = int(body["year"])
        month          = int(body["month"])
        ceremony_type  = body["ceremony_type"]
        ceremony_place = body["ceremony_place"]
        birth_charts   = body["birth_charts"]
    except (KeyError, TypeError, ValueError) as e:
        return _error(400, f"Invalid or missing field: {e}")

    if not (1 <= month <= 12):
        return _error(400, "month must be 1–12")
    if not birth_charts:
        return _error(400, "At least one birth_chart is required")

    try:
        geo = _geocode(ceremony_place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        results = find_muhurtas_for_month(
            year, month,
            geo["lat"], geo["lon"], geo["tz_name"],
            ceremony_type, birth_charts,
        )
    except Exception:
        traceback.print_exc()
        return _error(500, "Muhurta calculation failed")

    return _ok({"results": results, "count": len(results)})


def _handle_check(body: dict) -> dict:
    try:
        date_str       = body["date"]          # "DD/MM/YYYY"
        ceremony_type  = body["ceremony_type"]
        ceremony_place = body["ceremony_place"]
        birth_charts   = body.get("birth_charts", [])
    except KeyError as e:
        return _error(400, f"Missing field: {e}")

    time_str = body.get("time", "")  # "HH:MM" or empty
    check_hour = check_minute = -1
    if time_str:
        try:
            check_hour, check_minute = [int(x) for x in time_str.split(":")]
        except (ValueError, TypeError):
            return _error(400, "time must be HH:MM")

    try:
        day, month, year = [int(x) for x in date_str.split("/")]
    except (ValueError, TypeError):
        return _error(400, "date must be DD/MM/YYYY")

    try:
        geo = _geocode(ceremony_place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        result = check_muhurta_day(
            year, month, day,
            geo["lat"], geo["lon"], geo["tz_name"],
            ceremony_type, birth_charts,
            check_hour=check_hour, check_minute=check_minute,
        )
    except Exception:
        traceback.print_exc()
        return _error(500, "Muhurta check calculation failed")

    return _ok(result)


def _handle_window_detail(body: dict) -> dict:
    """Compute planet rashis for a single ceremony date (at local noon).

    Planet positions change over days, not hours, so noon is accurate for
    the horoscope display.

    Request:  {ceremony_place: str, date: "DD/MM/YYYY"}
    Response: {planet_rashis: {ravi, chandra, kuja, budha, guru, shukra, shani, rahu, ketu}}
    """
    try:
        date_str       = body["date"]           # "DD/MM/YYYY"
        ceremony_place = body["ceremony_place"]
    except KeyError as e:
        return _error(400, f"Missing field: {e}")

    try:
        day, month, year = [int(x) for x in date_str.split("/")]
    except (ValueError, TypeError):
        return _error(400, "date must be DD/MM/YYYY")

    try:
        geo = _geocode(ceremony_place)
    except ValueError as e:
        return _error(400, str(e))
    except Exception:
        return _error(502, "Geocoding service unavailable")

    try:
        jd = local_date_to_jd(year, month, day, geo["tz_name"])  # local noon
        planet_rashis = compute_planet_rashis(jd)
    except Exception:
        traceback.print_exc()
        return _error(500, "Planet rashi calculation failed")

    return _ok({"planet_rashis": planet_rashis})
