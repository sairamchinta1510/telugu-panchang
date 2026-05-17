import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import AbstractExceptionHandler, AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PANCHANG_API_URL = "https://api.sanatanadharmas.com/panchang"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_LAT = 17.38
DEFAULT_LON = 78.48
DEFAULT_CITY = "Hyderabad"
REPROMPT_TEXT = "You can ask about tithi, nakshatra, rahu kalam, or today's full panchang."


def today_in_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def spoken_term(value):
    if not isinstance(value, dict):
        return "unknown"

    english = (value.get("en") or "").strip()
    telugu = (value.get("te") or "").strip()

    if english and telugu and english != telugu:
        return f"{english} ({telugu})"
    return english or telugu or "unknown"


def until_phrase(value):
    if not isinstance(value, dict):
        return ""

    end_time = (value.get("end_time") or "").strip()
    if not end_time:
        return ""

    suffix = " next day" if value.get("next_day") else ""
    return f", until {end_time}{suffix}"


def safe_time(value):
    return value or "not available"


def safe_range(window):
    if not isinstance(window, dict):
        return ("not available", "not available")
    return safe_time(window.get("start")), safe_time(window.get("end"))


def get_geolocation_coordinates(handler_input):
    context = handler_input.request_envelope.context
    geolocation = getattr(context, "geolocation", None)
    coordinate = getattr(geolocation, "coordinate", None)
    latitude = getattr(coordinate, "latitude_in_degrees", None)
    longitude = getattr(coordinate, "longitude_in_degrees", None)

    if latitude is None or longitude is None:
        return None

    return float(latitude), float(longitude), "Alexa geolocation"


def get_postal_code(handler_input):
    service_client_factory = getattr(handler_input, "service_client_factory", None)
    system = handler_input.request_envelope.context.system
    device = getattr(system, "device", None)
    device_id = getattr(device, "device_id", None)

    if service_client_factory is None or not device_id:
        return None

    try:
        address_service = service_client_factory.get_device_address_service()
        address = address_service.get_full_address(device_id)
        postal_code = getattr(address, "postal_code", None)
        return postal_code.strip() if postal_code else None
    except Exception as exc:  # Alexa service exceptions vary by runtime package version.
        logger.warning("Unable to fetch device address: %s", exc)
        return None


def geocode_postal_code(postal_code):
    if not postal_code:
        return None

    response = requests.get(
        NOMINATIM_URL,
        params={
            "postalcode": postal_code,
            "countrycodes": "in",
            "format": "jsonv2",
            "limit": 1,
        },
        headers={"User-Agent": "telugu-panchang-alexa/1.0"},
        timeout=5,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    top_result = results[0]
    return float(top_result["lat"]), float(top_result["lon"]), f"postal code {postal_code}"


def resolve_coordinates(handler_input):
    geo_coordinates = get_geolocation_coordinates(handler_input)
    if geo_coordinates:
        return geo_coordinates

    postal_code = get_postal_code(handler_input)
    if postal_code:
        try:
            postal_coordinates = geocode_postal_code(postal_code)
            if postal_coordinates:
                return postal_coordinates
        except Exception as exc:
            logger.warning("Postal code geocoding failed for %s: %s", postal_code, exc)

    return DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY


def fetch_panchang(lat, lon, date_str):
    response = requests.get(
        PANCHANG_API_URL,
        params={"lat": lat, "lon": lon, "date": date_str},
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    panchang = payload.get("panchang")
    if not isinstance(panchang, dict):
        raise ValueError("Panchang API response missing panchang block")
    return payload, panchang


def load_panchang_for_request(handler_input):
    lat, lon, source = resolve_coordinates(handler_input)
    request_date = today_in_ist()
    logger.info("Fetching panchang for lat=%s lon=%s source=%s date=%s", lat, lon, source, request_date.isoformat())
    return fetch_panchang(lat, lon, request_date.isoformat())


def build_daily_briefing_speech(panchang, request_date):
    tithi = spoken_term(panchang.get("tithi"))
    nakshatra = spoken_term(panchang.get("nakshatra"))
    yoga = spoken_term(panchang.get("yoga"))
    vaaram = spoken_term(panchang.get("vaaram"))
    masam = spoken_term(panchang.get("masam"))
    paksham = spoken_term(panchang.get("paksham"))
    rutu = spoken_term(panchang.get("rutu"))
    samvatsara = spoken_term(panchang.get("samvatsara"))
    ayanam = spoken_term(panchang.get("ayanam"))
    sunrise = safe_time(panchang.get("sunrise"))
    sunset = safe_time(panchang.get("sunset"))
    rahu_start, rahu_end = safe_range(panchang.get("rahu_kalam"))
    yama_start, yama_end = safe_range(panchang.get("yamagandam"))
    abhijit_start, abhijit_end = safe_range(panchang.get("abhijit"))
    date_str = f"{request_date.strftime('%B')} {request_date.day}, {request_date.year}"

    return (
        f"Namaskaram! Today is {vaaram}, {date_str}. "
        f"{masam} Masam, {paksham} Paksham, {rutu} Ritu. "
        f"Tithi is {tithi}{until_phrase(panchang.get('tithi'))}. "
        f"Nakshatra is {nakshatra}{until_phrase(panchang.get('nakshatra'))}. "
        f"Yoga is {yoga}. "
        f"Sunrise at {sunrise}, sunset at {sunset}. "
        f"Rahu Kalam is from {rahu_start} to {rahu_end}. "
        f"Yamagandam from {yama_start} to {yama_end}. "
        f"Abhijit Muhurta, the most auspicious time, is from {abhijit_start} to {abhijit_end}. "
        f"Samvatsaram is {samvatsara}, {ayanam}. "
        "What else would you like to know?"
    )


def continue_response(handler_input, speech_text):
    return handler_input.response_builder.speak(speech_text).ask(REPROMPT_TEXT).response


def end_response(handler_input, speech_text):
    return handler_input.response_builder.speak(speech_text).response


def get_panchang(handler_input):
    _, panchang = load_panchang_for_request(handler_input)
    return panchang


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        _, panchang = load_panchang_for_request(handler_input)
        speech_text = build_daily_briefing_speech(panchang, today_in_ist())
        return continue_response(handler_input, speech_text)


class DailyBriefingIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DailyBriefingIntent")(handler_input)

    def handle(self, handler_input):
        _, panchang = load_panchang_for_request(handler_input)
        speech_text = build_daily_briefing_speech(panchang, today_in_ist())
        return continue_response(handler_input, speech_text)


class TithiIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("TithiIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        speech_text = f"Today's Tithi is {spoken_term(panchang.get('tithi'))}{until_phrase(panchang.get('tithi'))}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class NakshatraIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NakshatraIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        speech_text = f"Today's Nakshatra is {spoken_term(panchang.get('nakshatra'))}{until_phrase(panchang.get('nakshatra'))}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class YogaIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("YogaIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        speech_text = f"Today's Yoga is {spoken_term(panchang.get('yoga'))}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class RahuKalamIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RahuKalamIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        rahu_start, rahu_end = safe_range(panchang.get("rahu_kalam"))
        speech_text = f"Today's Rahu Kalam is from {rahu_start} to {rahu_end}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class YamagandamIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("YamagandamIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        yama_start, yama_end = safe_range(panchang.get("yamagandam"))
        speech_text = f"Today's Yamagandam is from {yama_start} to {yama_end}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class GulikaiIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GulikaiIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        gulikai_start, gulikai_end = safe_range(panchang.get("gulikai"))
        speech_text = f"Today's Gulikai is from {gulikai_start} to {gulikai_end}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class AbhijitIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AbhijitIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        abhijit_start, abhijit_end = safe_range(panchang.get("abhijit"))
        speech_text = f"Today's Abhijit Muhurta is from {abhijit_start} to {abhijit_end}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class SunTimingsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SunTimingsIntent")(handler_input)

    def handle(self, handler_input):
        panchang = get_panchang(handler_input)
        sunrise = safe_time(panchang.get("sunrise"))
        sunset = safe_time(panchang.get("sunset"))
        speech_text = f"Today's sunrise is at {sunrise}, and sunset is at {sunset}. What else would you like to know?"
        return continue_response(handler_input, speech_text)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = (
            "You can ask for today's full panchang, tithi, nakshatra, yoga, rahu kalam, "
            "yamagandam, gulikai, abhijit muhurta, or sunrise and sunset timings. "
            "What would you like to know?"
        )
        return continue_response(handler_input, speech_text)


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        return end_response(handler_input, "Sare, goodbye!")


class FallbackExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.exception("Unhandled exception: %s", exception)
        speech_text = (
            "Sorry, I could not fetch today's panchang right now. "
            "Please try again in a little while."
        )
        return continue_response(handler_input, speech_text)


sb = CustomSkillBuilder(api_client=DefaultApiClient())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(DailyBriefingIntentHandler())
sb.add_request_handler(TithiIntentHandler())
sb.add_request_handler(NakshatraIntentHandler())
sb.add_request_handler(YogaIntentHandler())
sb.add_request_handler(RahuKalamIntentHandler())
sb.add_request_handler(YamagandamIntentHandler())
sb.add_request_handler(GulikaiIntentHandler())
sb.add_request_handler(AbhijitIntentHandler())
sb.add_request_handler(SunTimingsIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(FallbackExceptionHandler())

lambda_handler = sb.lambda_handler()
