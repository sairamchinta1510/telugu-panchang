"""Tests for panchangam_validator — uses mocks for HTTP and S3."""
import sys
import datetime
import json
from unittest.mock import patch, MagicMock
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_prokerala_html(tithi: str, nakshatra: str, sunrise: str) -> str:
    """Build minimal Prokerala-like HTML matching the real div class structure."""
    return f"""
    <html><body>
    <div class="panchang-box-data-block panchang-data-tithi ">
      <span class="d-block b">Tithi</span>
      <div>{tithi} - Jun 25 08:09 PM</div>
    </div>
    <div class="panchang-box-data-block panchang-data-nakshatra ">
      <span class="d-block b">Nakshatra</span>
      <div>{nakshatra} - Jun 25 04:29 PM</div>
    </div>
    <span class="d-block t-sm">Sunrise</span>
    <span>{sunrise}</span>
    </body></html>
    """


def _import_validator():
    """Import with boto3 mocked so it works without AWS credentials."""
    for mod in list(sys.modules):
        if "panchangam_validator" in mod:
            del sys.modules[mod]
    sys.modules.setdefault("boto3", MagicMock())
    import importlib
    import compute.panchangam_validator as v
    importlib.reload(v)
    return v


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestValidateMuhurtamDate:

    def test_verified_when_tithi_nakshatra_sunrise_all_match(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Rohini", "05:43 AM")
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "verified"
        assert result["source"] == "Prokerala Panchangam"
        assert result["details"]["tithi"]["match"] is True
        assert result["details"]["nakshatra"]["match"] is True
        assert result["details"]["sunrise"]["match"] is True

    def test_partial_when_tithi_nakshatra_match_but_sunrise_off(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Rohini", "06:10 AM")  # 27 min off
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "partial"
        assert result["details"]["tithi"]["match"] is True
        assert result["details"]["sunrise"]["match"] is False

    def test_mismatch_when_nakshatra_differs(self):
        v = _import_validator()
        html = _make_prokerala_html("Dashami", "Mrigashira", "05:43 AM")
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch.object(v, "_read_s3", return_value=None), \
             patch.object(v, "_write_s3"):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "mismatch"
        assert result["details"]["nakshatra"]["match"] is False

    def test_unavailable_when_fetch_fails(self):
        v = _import_validator()
        with patch("urllib.request.urlopen", side_effect=Exception("Network error")), \
             patch.object(v, "_read_s3", return_value=None):
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        assert result["status"] == "unavailable"

    def test_uses_s3_cache_when_available(self):
        v = _import_validator()
        cached = {
            "tithi":     "Dashami",
            "nakshatra": "Rohini",
            "sunrise":   "05:43 AM",
        }
        with patch.object(v, "_read_s3", return_value=cached), \
             patch("urllib.request.urlopen") as mock_url:
            result = v.validate_muhurtam_date(
                date=datetime.date(2026, 6, 25),
                lat=17.385, lon=78.487,
                tz_name="Asia/Kolkata",
                tithi_en="Dashami",
                nakshatra_en="Rohini",
                sunrise="05:43",
            )

        mock_url.assert_not_called()   # should NOT hit network when cache hits
        assert result["status"] == "verified"
