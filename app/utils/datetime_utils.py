"""Date/time helpers. All times are naive local times (stdlib only)."""
from datetime import datetime, timedelta

from app.config import DATETIME_FORMAT, DATE_FORMAT


def now():
    return datetime.now()


def now_str():
    return datetime.now().strftime(DATETIME_FORMAT)


def today_str():
    return datetime.now().strftime(DATE_FORMAT)


def parse_datetime(text):
    """Parse 'YYYY-MM-DD HH:MM'. Raises ValueError on bad input."""
    return datetime.strptime(str(text).strip(), DATETIME_FORMAT)


def parse_date(text):
    return datetime.strptime(str(text).strip(), DATE_FORMAT)


def fmt(dt):
    return dt.strftime(DATETIME_FORMAT)


def fmt_date(dt):
    return dt.strftime(DATE_FORMAT)


def add_minutes(dt, minutes):
    return dt + timedelta(minutes=minutes)


def overlaps(a_start, a_end, b_start, b_end):
    """True if the two ranges share any time."""
    return a_start < b_end and b_start < a_end


def ceil_to(dt, step):
    """Round a datetime UP to the next multiple of `step` minutes."""
    dt = dt.replace(second=0, microsecond=0)
    remainder = dt.minute % step
    if remainder:
        dt = dt.replace(minute=dt.minute - remainder) + timedelta(minutes=step)
    return dt
