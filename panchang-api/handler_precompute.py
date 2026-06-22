from __future__ import annotations

import gzip
import json
import logging
import os
from datetime import date, timedelta

from compute.precompute import precompute_month

MAJOR_CITIES = [
    {"name": "hyderabad", "lat": 17.385, "lon": 78.487, "tz": "Asia/Kolkata"},
    {"name": "mumbai", "lat": 19.076, "lon": 72.878, "tz": "Asia/Kolkata"},
    {"name": "delhi", "lat": 28.614, "lon": 77.209, "tz": "Asia/Kolkata"},
    {"name": "chennai", "lat": 13.083, "lon": 80.275, "tz": "Asia/Kolkata"},
    {"name": "bangalore", "lat": 12.972, "lon": 77.594, "tz": "Asia/Kolkata"},
    {"name": "kolkata", "lat": 22.573, "lon": 88.363, "tz": "Asia/Kolkata"},
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _write_cache_sync(year: int, month: int, lat: float, lon: float, data: dict) -> None:
    """Synchronous S3 write for the precompute job."""
    from compute.s3_cache import cache_s3_key, round_location

    bucket = os.environ.get("PANCHANG_CACHE_BUCKET")
    if not bucket:
        return

    import boto3

    lat_r, lon_r = round_location(lat, lon)
    key = cache_s3_key(year, month, lat_r, lon_r)
    body = gzip.compress(json.dumps(data, ensure_ascii=False).encode())
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentEncoding="gzip",
        ContentType="application/json",
    )


def lambda_handler(event: dict, context) -> dict:
    """Nightly cron: precompute next 90 days for major Indian cities."""
    today = date.today()

    month_set: set[tuple[int, int]] = set()
    for i in range(91):
        d = today + timedelta(days=i)
        month_set.add((d.year, d.month))

    months = sorted(month_set)
    results = {"success": [], "failed": []}

    for city in MAJOR_CITIES:
        for year, month in months:
            try:
                data = precompute_month(year, month, city["lat"], city["lon"], city["tz"])
                _write_cache_sync(year, month, city["lat"], city["lon"], data)
                results["success"].append(f"{city['name']}/{year}-{month:02d}")
                logger.info("Precomputed %s/%s-%02d: %d days", city["name"], year, month, len(data))
            except Exception as exc:
                key = f"{city['name']}/{year}-{month:02d}"
                results["failed"].append(key)
                logger.error("Failed %s: %s", key, exc)

    logger.info(
        "Precompute complete. Success: %d, Failed: %d",
        len(results["success"]),
        len(results["failed"]),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }
