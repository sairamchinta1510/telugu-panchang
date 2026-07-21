"""
Astronomical primitives using pyswisseph with Lahiri ayanamsha.
All longitude functions return sidereal degrees in [0, 360).
"""
import swisseph as swe
import pytz
from datetime import datetime

# Standard atmosphere constants for sunrise/sunset refraction calculation
_STANDARD_PRESSURE_MB = 1013.25  # Standard atmospheric pressure in millibars
_STANDARD_TEMP_C = 15.0          # Standard temperature in Celsius


def _init_swe():
    """Configure Swiss Ephemeris to use built-in Moshier + Lahiri ayanamsha."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def local_date_to_jd(year: int, month: int, day: int, tz_name: str) -> float:
    """Return Julian Day for local solar noon (12:00 in local timezone) of the given date.

    Used only as a date anchor / search seed for get_sunrise_sunset().
    All panchang elements are computed at sunrise, not at noon.
    """
    tz = pytz.timezone(tz_name)
    local_noon = tz.localize(datetime(year, month, day, 12, 0, 0))
    utc_noon = local_noon.astimezone(pytz.utc)
    hour_ut = utc_noon.hour + utc_noon.minute / 60.0 + utc_noon.second / 3600.0
    return swe.julday(utc_noon.year, utc_noon.month, utc_noon.day,
                      hour_ut, swe.GREG_CAL)


def sun_longitude(jd: float) -> float:
    """Return sidereal solar longitude in degrees [0, 360)."""
    _init_swe()
    xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return xx[0] % 360


def moon_longitude(jd: float) -> float:
    """Return sidereal lunar longitude in degrees [0, 360)."""
    _init_swe()
    xx, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return xx[0] % 360


def moon_sun_elongation(jd: float) -> float:
    """Return Moon-Sun elongation (tropical) in degrees [0, 360).
    Ayanamsha cancels in the difference, so tropical is fine here."""
    xx_moon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    xx_sun, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    return (xx_moon[0] - xx_sun[0]) % 360


def get_sunrise_sunset(jd: float, lat: float, lon: float) -> tuple[float, float]:
    """Return (sunrise_jd, sunset_jd) for the given Julian Day and location.
    geopos order for Swiss Ephemeris: [longitude, latitude, altitude]."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be in [-90, 90], got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be in [-180, 180], got {lon}")
    
    geopos = (lon, lat, 0.0)  # Swiss Ephemeris: longitude FIRST, then latitude
    # jd is always local noon (from local_date_to_jd). Subtracting 0.5 days
    # gives local midnight — guaranteed to be before sunrise for any timezone.
    # Using midnight UTC instead would miss early-UTC sunrises (e.g. IST locations
    # where sunrise at ~05:30 IST = ~23:56 UTC falls before UTC midnight).
    jd_search = jd - 0.5

    ret_rise, tret_rise = swe.rise_trans(
        jd_search, swe.SUN, swe.CALC_RISE, geopos, _STANDARD_PRESSURE_MB, _STANDARD_TEMP_C)
    ret_set, tret_set = swe.rise_trans(
        jd_search, swe.SUN, swe.CALC_SET, geopos, _STANDARD_PRESSURE_MB, _STANDARD_TEMP_C)

    if ret_rise < 0 or ret_set < 0:
        raise ValueError(f"Rise/set calculation failed: rise={ret_rise}, set={ret_set}")

    return tret_rise[0], tret_set[0]


def local_datetime_to_jd(year: int, month: int, day: int,
                         hour: int, minute: int, tz_name: str) -> float:
    """Return Julian Day for a specific local date and time."""
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, 0))
    utc_dt = local_dt.astimezone(pytz.utc)
    hour_ut = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_ut, swe.GREG_CAL)


def jd_to_local_datetime(jd: float, tz_name: str) -> datetime:
    """Convert Julian Day to local datetime."""
    unix_time = (jd - 2440587.5) * 86400
    dt_utc = datetime.fromtimestamp(unix_time, tz=pytz.utc)
    return dt_utc.astimezone(pytz.timezone(tz_name))


def find_next_index_change(jd_start: float, index_fn, current_idx: int,
                           step_hours: float = 0.5, max_hours: float = 72.0):
    """Find the JD when index_fn(jd) first differs from current_idx.

    Scans forward in step_hours increments then binary-searches to ~1-minute
    precision. Returns the JD of the transition, or None if not found within
    max_hours.
    """
    step = step_hours / 24.0
    limit = int(max_hours / step_hours) + 1
    jd = jd_start

    for _ in range(limit):
        jd += step
        if index_fn(jd) != current_idx:
            lo, hi = jd - step, jd
            for _ in range(40):
                mid = (lo + hi) / 2
                if index_fn(mid) == current_idx:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2
    return None


def compute_planet_longitudes(jd: float) -> dict[str, float]:
    """Return exact sidereal longitude in degrees [0, 360) for all 9 Jyotish grahas.

    Use this when exact degrees are needed (e.g. Venus combustion check).
    For rashi-level checks use compute_planet_rashis() which is faster.
    """
    _init_swe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    bodies = {
        "ravi":    swe.SUN,
        "chandra": swe.MOON,
        "kuja":    swe.MARS,
        "budha":   swe.MERCURY,
        "guru":    swe.JUPITER,
        "shukra":  swe.VENUS,
        "shani":   swe.SATURN,
    }
    lons: dict[str, float] = {}
    for name, pid in bodies.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        lons[name] = xx[0] % 360
    xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    lons["rahu"] = xx[0] % 360
    lons["ketu"] = (lons["rahu"] + 180) % 360
    return lons


def compute_planet_rashis(jd: float) -> dict[str, int]:
    """Compute sidereal rashi index (0=Mesha … 11=Meena) for all 9 Jyotish grahas at jd.

    Returns dict with keys: ravi, chandra, kuja, budha, guru, shukra, shani, rahu, ketu.
    """
    _init_swe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    bodies = {
        "ravi":   swe.SUN,
        "chandra": swe.MOON,
        "kuja":   swe.MARS,
        "budha":  swe.MERCURY,
        "guru":   swe.JUPITER,
        "shukra": swe.VENUS,
        "shani":  swe.SATURN,
    }
    rashis: dict[str, int] = {}
    for name, pid in bodies.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        rashis[name] = int(xx[0] / 30) % 12
    xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    rashis["rahu"] = int(xx[0] / 30) % 12
    rashis["ketu"] = (rashis["rahu"] + 6) % 12
    return rashis


def compute_planet_details(jd: float) -> dict[str, dict]:
    """Return rashi_idx, deg, min, retrograde for all 9 Jyotish grahas at jd.

    deg and min are the planet's position within its rashi (0–29°, 0–59').
    retrograde is True when the planet's apparent motion is backward.
    Rahu and Ketu are always retrograde by convention.
    """
    _init_swe()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    bodies = {
        "ravi":    swe.SUN,
        "chandra": swe.MOON,
        "kuja":    swe.MARS,
        "budha":   swe.MERCURY,
        "guru":    swe.JUPITER,
        "shukra":  swe.VENUS,
        "shani":   swe.SATURN,
    }
    details: dict[str, dict] = {}
    for name, pid in bodies.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        lon = xx[0] % 360
        speed = xx[3]
        deg_in_rashi = lon % 30
        details[name] = {
            "rashi_idx":  int(lon / 30) % 12,
            "deg":        int(deg_in_rashi),
            "min":        int((deg_in_rashi % 1) * 60),
            "retrograde": speed < 0,
        }
    xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    rahu_lon = xx[0] % 360
    rahu_deg = rahu_lon % 30
    details["rahu"] = {
        "rashi_idx":  int(rahu_lon / 30) % 12,
        "deg":        int(rahu_deg),
        "min":        int((rahu_deg % 1) * 60),
        "retrograde": True,
    }
    ketu_lon = (rahu_lon + 180) % 360
    ketu_deg = ketu_lon % 30
    details["ketu"] = {
        "rashi_idx":  int(ketu_lon / 30) % 12,
        "deg":        int(ketu_deg),
        "min":        int((ketu_deg % 1) * 60),
        "retrograde": True,
    }
    return details
