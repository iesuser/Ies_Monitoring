from string import ascii_lowercase, ascii_uppercase, digits, punctuation
import re

from flask import has_request_context, request


def _resolve_lang(lang=None):
    """Resolve UI language for validation messages (en|ka). Default: en."""
    if lang in {"en", "ka"}:
        return lang

    if has_request_context():
        header_lang = (request.headers.get("X-App-Lang") or "").strip().lower()
        if header_lang in {"en", "ka"}:
            return header_lang

        cookie_lang = (request.cookies.get("lang") or "").strip().lower()
        if cookie_lang in {"en", "ka"}:
            return cookie_lang

        accept = (request.headers.get("Accept-Language") or "").lower()
        if accept.startswith("ka"):
            return "ka"

    return "en"


_PASSWORD_MESSAGES = {
    "en": {
        "required": "Password is required.",
        "min_length": "Password must be at least 6 characters.",
        "allowed_chars": (
            "Password may only contain English letters, digits, and symbols !@#$%^&*"
        ),
        "uppercase": "Password must contain at least one uppercase letter.",
        "lowercase": "Password must contain at least one lowercase letter.",
        "digit": "Password must contain at least one digit.",
        "special": "Password must contain at least one special character.",
    },
    "ka": {
        "required": "პაროლი სავალდებულოა.",
        "min_length": "პაროლი უნდა იყოს მინიმუმ 6 სიმბოლო.",
        "allowed_chars": (
            "პაროლი შეიძლება შეიცავდეს მხოლოდ ინგლისურ ასოებს, ციფრებს და სიმბოლოებს !@#$%^&*"
        ),
        "uppercase": "პაროლი უნდა შეიცავდეს მინიმუმ ერთ დიდ ასოს.",
        "lowercase": "პაროლი უნდა შეიცავდეს მინიმუმ ერთ პატარა ასოს.",
        "digit": "პაროლი უნდა შეიცავდეს მინიმუმ ერთ ციფრს.",
        "special": "პაროლი უნდა შეიცავდეს მინიმუმ ერთ სპეციალურ სიმბოლოს.",
    },
}


def validate_password(password: str, lang=None) -> None:
    """Validate password policy and raise ValueError on invalid input.

    Policy (docs/05): min 6 chars, at least 1 upper, 1 lower, 1 digit, 1 special.
    Messages follow the active UI language (en/ka).
    """
    messages = _PASSWORD_MESSAGES[_resolve_lang(lang)]

    if not isinstance(password, str) or not password:
        raise ValueError(messages["required"])

    if len(password) < 6:
        raise ValueError(messages["min_length"])

    contains_uppercase = False
    contains_lowercase = False
    contains_digits = False
    contains_special = False
    allowed_characters = set(ascii_lowercase + ascii_uppercase + digits + punctuation)

    for character in password:
        if character not in allowed_characters:
            raise ValueError(messages["allowed_chars"])
        if character in ascii_uppercase:
            contains_uppercase = True
        elif character in ascii_lowercase:
            contains_lowercase = True
        elif character in digits:
            contains_digits = True
        elif character in punctuation:
            contains_special = True

    if not contains_uppercase:
        raise ValueError(messages["uppercase"])
    if not contains_lowercase:
        raise ValueError(messages["lowercase"])
    if not contains_digits:
        raise ValueError(messages["digit"])
    if not contains_special:
        raise ValueError(messages["special"])


def normalize_ge_phone(phone: str) -> str:
    """
    Validate and normalize Georgian phone number to E.164: +9955XXXXXXXX.
    - Must start with +995
    - Remaining part must be digits only
    """
    if not isinstance(phone, str) or not phone.strip():
        raise ValueError("ტელეფონის ნომერი სავალდებულოა.")

    # Basic cleanup for user input convenience.
    normalized = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not normalized.startswith("+995"):
        raise ValueError("ტელეფონის ნომერი უნდა იწყებოდეს +995-ით.")

    local = normalized[4:]
    if not local.isdigit():
        raise ValueError("ტელეფონის ნომრის +995-ის შემდეგ ნაწილი უნდა იყოს მხოლოდ ციფრები.")

    if len(local) != 9 or not local.startswith("5"):
        raise ValueError("ტელეფონის ნომერი უნდა იყოს ფორმატში: +9955XXXXXXXX.")

    return f"+995{local}"


def normalize_email(email: str) -> str:
    """Validate and normalize email value."""
    if not isinstance(email, str) or not email.strip():
        raise ValueError("ელ.ფოსტა სავალდებულოა.")

    normalized = email.strip().lower()
    email_pattern = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    if not re.fullmatch(email_pattern, normalized):
        raise ValueError("ელ.ფოსტის ფორმატი არასწორია.")

    return normalized


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_polygon_geometry(geometry) -> dict:
    """
    Validate a GeoJSON Polygon and return a normalized copy.
    - type must be "Polygon"
    - each ring needs at least 3 distinct points; unclosed rings are closed automatically
    - points are [lon, lat] within valid ranges (extra dimensions are dropped)
    """
    if not isinstance(geometry, dict):
        raise ValueError("geometry სავალდებულოა და უნდა იყოს GeoJSON ობიექტი.")

    if geometry.get("type") != "Polygon":
        raise ValueError('geometry.type უნდა იყოს "Polygon".')

    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise ValueError("geometry.coordinates არ უნდა იყოს ცარიელი.")

    normalized_rings = []
    for ring in rings:
        if not isinstance(ring, list):
            raise ValueError("geometry.coordinates-ის ყოველი რგოლი უნდა იყოს წერტილების სია.")

        points = []
        for point in ring:
            if not isinstance(point, list) or len(point) < 2:
                raise ValueError("ყოველი წერტილი უნდა იყოს ფორმატში [lon, lat].")
            lon, lat = point[0], point[1]
            if not _is_number(lon) or not _is_number(lat):
                raise ValueError("წერტილის კოორდინატები უნდა იყოს რიცხვები.")
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError("კოორდინატები დიაპაზონს გარეთაა: lon [-180, 180], lat [-90, 90].")
            points.append([float(lon), float(lat)])

        if points and points[0] != points[-1]:
            points.append(list(points[0]))

        if len(points) < 4:
            raise ValueError("polygon-ს უნდა ჰქონდეს მინიმუმ 3 განსხვავებული წერტილი.")

        normalized_rings.append(points)

    return {"type": "Polygon", "coordinates": normalized_rings}
