"""
Sankalpam Sanskrit grammar validator.

Validates each panchang term against a whitelist of known-correct Sanskrit forms
before the sankalpam recitation is assembled. This catches naming bugs early
(e.g., modern Telugu weekday names used instead of traditional Sanskrit deity names).

All whitelists are sourced from traditional Vedic panchang recitation conventions
as used in South Indian (Andhra/Telangana) Sanskrit sankalpam.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ── Valid forms for each position in the recitation ─────────────────────────

# Weekday: traditional planetary deity names (locative context: "X vasare")
_VALID_VAARAM_SANKALPAM = {
    "Bhanu", "Soma", "Bhouma", "Saumya", "Brihaspati", "Bhrughu", "Sthira",
}
_VALID_VAARAM_SANKALPAM_TE = {
    "భాను", "సోమ", "భౌమ", "సౌమ్య", "బృహస్పతి", "భృగు", "స్థిర",
}

# Tithi stems (the suffix "tithau" is added by the recitation template)
_VALID_TITHI = {
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi",
    "Purnima", "Amavasya",
}

# Nakshatra stems (the suffix "nakshatre" is added by the template)
_VALID_NAKSHATRA = {
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Svati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
}

# Masa stems (the suffix "mase" is added by the template)
_VALID_MASAM = {
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
    "Shravana", "Bhadrapada", "Ashvina", "Kartika",
    "Margashira", "Pushya", "Magha", "Phalguna",
}

# Ritu stems (the suffix "ritau" is added by the template)
_VALID_RUTU = {"Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"}

# Paksham (display form — build_sankalpam converts to locative "Pakshe")
_VALID_PAKSHAM = {"Shukla Paksham", "Krishna Paksham"}

# Ayanam (display form — build_sankalpam converts to locative "Uttarayane"/"Dakshinayane")
_VALID_AYANAM = {"Uttarayanam", "Dakshinayanam"}


@dataclass
class ValidationResult:
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.warnings) == 0

    def warn(self, field_name: str, value: str, valid_set: set[str]) -> None:
        sorted_valid = sorted(valid_set)
        self.warnings.append(
            f"[sankalpam] Unexpected {field_name} '{value}'. "
            f"Expected one of: {sorted_valid}"
        )


def validate_sankalpam_inputs(panchang: dict) -> ValidationResult:
    """
    Validate panchang fields against known-correct Sanskrit sankalpam forms.

    Returns a ValidationResult whose .warnings list describes any issues found.
    An empty warnings list means all checked fields are valid.

    Args:
        panchang: dict returned by compute_panchang()
    """
    result = ValidationResult()

    vaaram_sk = panchang["vaaram"].get("sankalpam_en", "")
    if vaaram_sk not in _VALID_VAARAM_SANKALPAM:
        result.warn("vaaram (sankalpam)", vaaram_sk, _VALID_VAARAM_SANKALPAM)

    tithi = panchang["tithi"]["en"]
    if tithi not in _VALID_TITHI:
        result.warn("tithi", tithi, _VALID_TITHI)

    nakshatra = panchang["nakshatra"]["en"]
    if nakshatra not in _VALID_NAKSHATRA:
        result.warn("nakshatra", nakshatra, _VALID_NAKSHATRA)

    masam = panchang["masam"]["en"]
    if masam not in _VALID_MASAM:
        result.warn("masam", masam, _VALID_MASAM)

    rutu = panchang["rutu"]["en"]
    if rutu not in _VALID_RUTU:
        result.warn("rutu", rutu, _VALID_RUTU)

    paksham = panchang["paksham"]["en"]
    if paksham not in _VALID_PAKSHAM:
        result.warn("paksham", paksham, _VALID_PAKSHAM)

    ayanam = panchang["ayanam"]["en"]
    if ayanam not in _VALID_AYANAM:
        result.warn("ayanam", ayanam, _VALID_AYANAM)

    return result
