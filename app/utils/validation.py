"""Input validation helpers with friendly error messages.

Every function either returns the cleaned value or raises ValidationError.
Used by the service layer so no business rule lives in the UI.
"""
import re
from datetime import datetime

from app.config import VEHICLE_TYPES
from app.exceptions import ValidationError


def clean(value):
    return "" if value is None else str(value).strip()


def require(value, field):
    value = clean(value)
    if not value:
        raise ValidationError(f"{field} cannot be empty.")
    return value


def valid_name(value):
    value = require(value, "Name")
    if len(value) < 2:
        raise ValidationError("Name must be at least 2 characters long.")
    if len(value) > 60:
        raise ValidationError("Name is too long (max 60 characters).")
    if not re.fullmatch(r"[A-Za-z .'\-]+", value):
        raise ValidationError("Names may only contain letters, spaces, periods, apostrophes and hyphens.")
    return value


def normalize_phone(value):
    return clean(value).replace(" ", "").replace("-", "")


def valid_phone(value):
    value = normalize_phone(value)
    if not re.fullmatch(r"\d{7,15}", value):
        raise ValidationError("Phone numbers must be 7-15 digits (e.g. 09171234567).")
    return value


def valid_email(value):
    value = clean(value)
    if not value:
        return ""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValidationError("That email address looks invalid (e.g. name@example.com).")
    return value


def normalize_plate(value):
    return clean(value).upper()


def valid_plate(value):
    value = normalize_plate(value)
    if not re.fullmatch(r"[A-Z0-9\- ]{3,10}", value):
        raise ValidationError("Plates must be 3-10 letters/digits (e.g. ABC 1234).")
    return value


def valid_year(value):
    value = require(value, "Year")
    try:
        year = int(value)
    except ValueError:
        raise ValidationError("Year must be a number (e.g. 2021).") from None
    latest = datetime.now().year + 1
    if year < 1950 or year > latest:
        raise ValidationError(f"Year must be between 1950 and {latest}.")
    return year


def valid_vehicle_type(value):
    value = clean(value).lower()
    if value not in VEHICLE_TYPES:
        raise ValidationError(f"Vehicle type must be one of: {', '.join(VEHICLE_TYPES)}.")
    return value


def to_float(value, field="Amount", minimum=None):
    try:
        number = round(float(value), 2)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} cannot be less than {minimum}.")
    return number
