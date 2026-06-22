from __future__ import annotations

import json
import gzip
import os


def _cache_bucket() -> str | None:
    return os.environ.get("PANCHANG_CACHE_BUCKET") or None


def round_location(lat: float, lon: float) -> tuple[float, float]:
    return float(round(lat)), float(round(lon))


def cache_s3_key(year: int, month: int, lat_r: float, lon_r: float) -> str:
    return f"panchang-cache/{lat_r:+.0f}_{lon_r:+.0f}/{year}-{month:02d}.json"


def read_month_cache(year: int, month: int, lat: float, lon: float) -> dict | None:
    bucket = _cache_bucket()
    if not bucket:
        return None

    try:
        import boto3

        s3 = boto3.client("s3")
        lat_r, lon_r = round_location(lat, lon)
        key = cache_s3_key(year, month, lat_r, lon_r)
        response = s3.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()

        if response.get("ContentEncoding") == "gzip":
            payload = gzip.decompress(body).decode("utf-8")
        else:
            payload = body.decode("utf-8")

        data = json.loads(payload)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_month_cache(year: int, month: int, lat: float, lon: float, data: dict) -> None:
    bucket = _cache_bucket()
    if not bucket:
        return

    try:
        import boto3
        import threading
        import gzip
        import json
    except ImportError:
        return

    try:
        lat_r, lon_r = round_location(lat, lon)
        key = cache_s3_key(year, month, lat_r, lon_r)
        payload = json.dumps(data).encode("utf-8")
        compressed = gzip.compress(payload)
    except Exception:
        return

    def _writer() -> None:
        try:
            s3 = boto3.client("s3")
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=compressed,
                ContentEncoding="gzip",
                ContentType="application/json",
            )
        except Exception:
            pass

    try:
        thread = threading.Thread(target=_writer, daemon=True)
        thread.start()
    except Exception:
        return
