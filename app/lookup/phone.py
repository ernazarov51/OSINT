import phonenumbers
from phonenumbers import geocoder, carrier
from phonenumbers import timezone as ph_tz
from phonenumbers import PhoneNumberFormat, PhoneNumberType

TYPE_NAMES = {
    PhoneNumberType.MOBILE: "Mobil",
    PhoneNumberType.FIXED_LINE: "Statsionar",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "Statsionar yoki Mobil",
    PhoneNumberType.TOLL_FREE: "Bepul raqam",
    PhoneNumberType.PREMIUM_RATE: "Premium",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.UNKNOWN: "Noma'lum",
}

async def lookup_phone(number: str) -> dict:
    number = number.strip()
    if not number.startswith("+"):
        number = "+" + number

    try:
        parsed = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException as e:
        return {"found": False, "error": f"Raqamni tahlil qilib bo'lmadi: {e}"}

    if not phonenumbers.is_valid_number(parsed):
        return {"found": False, "error": "Raqam yaroqsiz (noto'g'ri format yoki mavjud emas)"}

    num_type = phonenumbers.number_type(parsed)

    return {
        "found": True,
        "number_international": phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL),
        "number_e164": phonenumbers.format_number(parsed, PhoneNumberFormat.E164),
        "number_local": phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL),
        "country": geocoder.description_for_number(parsed, "en") or "Noma'lum",
        "country_uz": geocoder.description_for_number(parsed, "uz") or None,
        "carrier": carrier.name_for_number(parsed, "en") or "Noma'lum",
        "type": TYPE_NAMES.get(num_type, "Noma'lum"),
        "timezones": list(ph_tz.time_zones_for_number(parsed)),
        "is_possible": phonenumbers.is_possible_number(parsed),
        "country_code": f"+{parsed.country_code}",
    }
