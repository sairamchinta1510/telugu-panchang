import json
import pytz
import pytest
from datetime import datetime as real_datetime
from unittest.mock import patch, MagicMock


MOCK_PANCHANG = {
    "samvatsara": {"en": "Parabhava", "te": "పరాభవ"},
    "ayanam": {"en": "Uttarayanam", "te": "ఉత్తరాయణం"},
    "rutu": {"en": "Grishma", "te": "గ్రీష్మ"},
    "masam": {"en": "Jyeshtha", "te": "జ్యేష్ఠ", "adhika": True},
    "paksham": {"en": "Shukla Paksham", "te": "శుక్ల పక్షం"},
    "tithi": {"en": "Panchami", "te": "పంచమి"},
    "vaaram": {"en": "Sunday", "te": "ఆదివారం"},
    "nakshatra": {"en": "Rohini", "te": "రోహిణి"},
    "yoga": {"en": "Vriddhi", "te": "వృద్ధి"},
    "karana": {"en": "Bava", "te": "బవ"},
    "sunrise": "06:05",
    "sunset": "18:42",
}

MOCK_SANKALPAM = {
    "full_en": "On this day in Parabhava samvatsara, Grishma rutu, Jyeshtha masam...",
    "full_te": "ఈ రోజున పరాభవ సంవత్సరం, గ్రీష్మ ఋతువు...",
}


def make_event(params: dict) -> dict:
    return {
        "queryStringParameters": params,
        "requestContext": {"http": {"method": "GET"}},
    }


@patch("handler.compute_panchang")
@patch("handler.local_date_to_jd")
@patch("handler.get_geographic")
@patch("handler.build_sankalpam")
@patch("handler._get_timezone")
def test_valid_request_india(mock_get_tz, mock_build_sankalpam, mock_get_geographic, mock_local_date_to_jd, mock_compute_panchang):
    mock_get_tz.return_value = "Asia/Kolkata"
    mock_local_date_to_jd.return_value = 2460777.5
    mock_compute_panchang.return_value = MOCK_PANCHANG
    mock_get_geographic.return_value = {"region": "Telangana"}
    mock_build_sankalpam.return_value = MOCK_SANKALPAM

    from handler import lambda_handler
    
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "2026-05-17"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["panchang"]["samvatsara"]["en"] == "Parabhava"
    assert body["sankalpam"]["full_en"] != ""
    assert "Cache-Control" in resp["headers"]


@patch("handler.compute_panchang")
@patch("handler.local_date_to_jd")
@patch("handler.get_geographic")
@patch("handler.build_sankalpam")
@patch("handler._get_timezone")
def test_default_date_used_when_omitted(mock_get_tz, mock_build_sankalpam, mock_get_geographic, mock_local_date_to_jd, mock_compute_panchang):
    mock_get_tz.return_value = "Asia/Kolkata"
    mock_local_date_to_jd.return_value = 2460777.5
    mock_compute_panchang.return_value = MOCK_PANCHANG
    mock_get_geographic.return_value = {"region": "Telangana"}
    mock_build_sankalpam.return_value = MOCK_SANKALPAM

    from handler import lambda_handler

    with patch("handler.datetime") as mock_dt:
        tz = pytz.timezone("Asia/Kolkata")
        frozen = tz.localize(real_datetime(2026, 5, 17, 14, 0, 0))
        mock_dt.now.return_value = frozen
        mock_dt.strptime.side_effect = real_datetime.strptime
        event = make_event({"lat": "17.38", "lon": "78.49"})
        resp = lambda_handler(event, {})

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["date"] == "2026-05-17"


def test_missing_lat_returns_400():
    from handler import lambda_handler
    
    event = make_event({"lon": "78.49"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_missing_lon_returns_400():
    from handler import lambda_handler
    
    event = make_event({"lat": "17.38"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_invalid_lat_returns_400():
    from handler import lambda_handler
    
    event = make_event({"lat": "999", "lon": "78.49"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


def test_invalid_date_format_returns_400():
    from handler import lambda_handler
    
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "not-a-date"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 400


@patch("handler._get_timezone")
@patch("handler.compute_panchang")
@patch("handler.local_date_to_jd")
@patch("handler.get_geographic")
@patch("handler.build_sankalpam")
def test_cors_header_present(mock_build_sankalpam, mock_get_geographic, mock_local_date_to_jd, mock_compute_panchang, mock_get_tz):
    mock_get_tz.return_value = "Asia/Kolkata"
    mock_local_date_to_jd.return_value = 2460777.5
    mock_compute_panchang.return_value = MOCK_PANCHANG
    mock_get_geographic.return_value = {"region": "Telangana"}
    mock_build_sankalpam.return_value = MOCK_SANKALPAM

    from handler import lambda_handler
    
    event = make_event({"lat": "17.38", "lon": "78.49", "date": "2026-05-17"})
    
    resp = lambda_handler(event, {})
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


@patch("handler._get_timezone")
@patch("handler.compute_panchang")
@patch("handler.local_date_to_jd")
def test_compute_error_returns_500(mock_local_date_to_jd, mock_compute_panchang, mock_get_tz):
    mock_get_tz.return_value = "Asia/Kolkata"
    mock_local_date_to_jd.return_value = 2460777.5
    mock_compute_panchang.side_effect = RuntimeError("ephemeris error")

    from handler import lambda_handler

    event = make_event({"lat": "17.38", "lon": "78.49", "date": "2026-05-17"})
    resp = lambda_handler(event, {})
    assert resp["statusCode"] == 500
