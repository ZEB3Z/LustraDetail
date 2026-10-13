"""Central configuration: paths, branding, and business rules.

Paths are read through functions (file_path / receipts_dir) so the test
suite can point the whole app at a temporary folder via monkeypatching.
"""
from pathlib import Path

# ---------------------------------------------------------------- brand ----
APP_NAME = "LustraDetail"
APP_VERSION = "1.0.0"
SHOP_NAME = "LustraDetail Auto Care"
SHOP_TAGLINE = "Drive in dirty. Drive out dazzling."
SHOP_ADDRESS = "123 Shine Avenue, Quezon City, Philippines"
SHOP_PHONE = "0917 000 1234"
CURRENCY = "Php"

# ---------------------------------------------------------------- paths ----
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"          # tests monkeypatch these two
RECEIPTS_DIR = PROJECT_ROOT / "receipts"

FILES = {
    "customers": "customers.json",
    "vehicles": "vehicles.json",
    "appointments": "appointments.json",
    "service_catalog": "service_catalog.json",
    "inventory": "inventory.json",
    "staff": "staff.json",
    "service_history": "service_history.json",
}


def file_path(key):
    """Absolute path of a data file (resolved at call time for testability)."""
    return Path(DATA_DIR) / FILES[key]


def receipts_dir():
    return Path(RECEIPTS_DIR)

# ------------------------------------------------------- domain values ----
VEHICLE_TYPES = ["sedan", "suv", "pickup", "van", "motorcycle"]
STAFF_ROLES = ["admin", "detailer", "cashier"]
PAYMENT_METHODS = ["cash", "gcash", "bank transfer", "card"]

# Job pipeline: BOOKED -> IN_PROGRESS -> DONE -> PAID
STATUS_BOOKED = "BOOKED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_DONE = "DONE"
STATUS_PAID = "PAID"
STATUS_CANCELLED = "CANCELLED"
STATUS_NO_SHOW = "NO_SHOW"
ALL_STATUSES = [
    STATUS_BOOKED,
    STATUS_IN_PROGRESS,
    STATUS_DONE,
    STATUS_PAID,
    STATUS_CANCELLED,
    STATUS_NO_SHOW,
]

# ------------------------------------------------------- business rules ----
# The shop has ONE detailing bay. Two jobs must always be separated by at
# least this many minutes (setup / cleanup / late-arrival allowance).
BOOKING_BUFFER_MINUTES = 15

# How far ahead the "find next available slot" search may look.
MAX_SEARCH_DAYS = 14

# Assumption used ONLY by the utilization report (a 9-hour workday).
WORKDAY_MINUTES = 540

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"
