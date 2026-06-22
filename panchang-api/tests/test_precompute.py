import sys
import io
import gzip
import json
import types
import time
import importlib
from unittest.mock import MagicMock, patch


def test_compute_day_cache_data_smoke():
    for mod in [
        "compute.precompute",
        "compute.astro",
        "compute.birth_chart",
        "compute.muhurta_rules",
        "compute.panchang",
        "swisseph",
    ]:
        sys.modules.pop(mod, None)

    from compute.precompute import compute_day_cache_data

    data = compute_day_cache_data(2026, 6, 22, 17.385, 78.487, "Asia/Kolkata")

    required_keys = {
        "nak_idx",
        "tithi_idx",
        "yoga_idx",
        "masam",
        "is_adhika",
        "sun_idx",
        "day_rashi_idx",
        "sunrise",
        "sunset",
        "sunrise_jd",
        "sunset_jd",
        "lagna_transitions",
        "nak_transitions",
        "tithi_transitions",
        "planet_rashis",
        "dur_muhurtam",
        "varjyam",
        "rahu_kalam",
        "yamaganda",
        "gulika_kalam",
    }

    assert required_keys <= data.keys()


def test_s3_cache_write_and_read():
    from compute.s3_cache import read_month_cache, write_month_cache

    mock_s3 = MagicMock()
    fake_boto3 = types.SimpleNamespace(client=MagicMock(return_value=mock_s3))
    payload = {"2026-06-22": {"sunrise": "05:43"}}

    with patch.dict(sys.modules, {"boto3": fake_boto3}):
        with patch.dict("os.environ", {"PANCHANG_CACHE_BUCKET": "test-bucket"}, clear=False):
            write_month_cache(2026, 6, 17.385, 78.487, payload)
            time.sleep(0.1)

            mock_s3.put_object.assert_called_once()
            put_kwargs = mock_s3.put_object.call_args.kwargs
            assert put_kwargs["Bucket"] == "test-bucket"
            assert put_kwargs["Key"] == "panchang-cache/+17_+78/2026-06.json"
            assert put_kwargs["ContentEncoding"] == "gzip"
            assert put_kwargs["ContentType"] == "application/json"
            assert json.loads(gzip.decompress(put_kwargs["Body"]).decode("utf-8")) == payload

            mock_s3.get_object.return_value = {
                "Body": io.BytesIO(gzip.compress(json.dumps(payload).encode("utf-8"))),
                "ContentEncoding": "gzip",
            }
            assert read_month_cache(2026, 6, 17.385, 78.487) == payload


def test_s3_cache_read_without_bucket_returns_none():
    from compute.s3_cache import read_month_cache

    with patch.dict("os.environ", {}, clear=True):
        assert read_month_cache(2026, 6, 17.385, 78.487) is None


def test_find_good_windows_cached_path():
    """Ensure _find_good_windows accepts day_cache without crashing."""
    from compute.muhurta_finder import _find_good_windows
    from compute.precompute import compute_day_cache_data

    day_cache = compute_day_cache_data(2026, 6, 22, 17.385, 78.487, "Asia/Kolkata")
    result = _find_good_windows(
        day_cache["sunrise_jd"], day_cache["sunset_jd"],
        17.385, 78.487, "Asia/Kolkata",
        "vivaha", [], day_cache["masam"], day_cache["is_adhika"],
        day_cache["sun_idx"], day_cache["lagna_transitions"][0]["idx"],
        skip_planet_rashis=True,
        day_cache=day_cache,
    )
    assert isinstance(result, list)


def test_find_muhurtas_cached_vs_live():
    """Cached path must return same days as live path."""
    for mod in [
        "compute.muhurta_finder",
        "compute.precompute",
        "compute.astro",
        "compute.birth_chart",
        "compute.muhurta_rules",
        "compute.panchang",
        "swisseph",
    ]:
        sys.modules.pop(mod, None)

    import compute.muhurta_finder as muhurta_finder
    import compute.precompute as precompute

    importlib.reload(muhurta_finder)
    importlib.reload(precompute)

    year, month = 2026, 7
    lat, lon, tz = 17.385, 78.487, "Asia/Kolkata"
    birth_charts = []

    month_cache = precompute.precompute_month(year, month, lat, lon, tz)

    live_results = muhurta_finder.find_muhurtas_for_month(
        year, month, lat, lon, tz, "vivaha", birth_charts
    )
    cached_results = muhurta_finder.find_muhurtas_for_month(
        year, month, lat, lon, tz, "vivaha", birth_charts, month_cache=month_cache
    )

    assert len(live_results) == len(cached_results), (
        f"Live: {len(live_results)} days, Cached: {len(cached_results)} days"
    )

    live_dates = {r["date_raw"] for r in live_results}
    cached_dates = {r["date_raw"] for r in cached_results}
    assert live_dates == cached_dates, (
        f"Date mismatch: {live_dates.symmetric_difference(cached_dates)}"
    )
