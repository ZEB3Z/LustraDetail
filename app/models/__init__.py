"""Plain dataclasses used across the app (no logic beyond tiny helpers)."""
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime

from app.config import DATETIME_FORMAT


class _Model:
    """Shared (de)serialisation helpers."""

    @classmethod
    def from_dict(cls, data):
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self):
        return asdict(self)


@dataclass
class Customer(_Model):
    name: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    created_at: str = ""
    id: int = 0


@dataclass
class Vehicle(_Model):
    customer_id: int = 0
    plate: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    color: str = ""
    type: str = "sedan"
    notes: str = ""
    id: int = 0

    def describe(self):
        return f"{self.year} {self.make} {self.model} ({self.plate})"


@dataclass
class Staff(_Model):
    name: str = ""
    role: str = "detailer"
    username: str = ""
    password: str = ""
    phone: str = ""
    active: bool = True
    id: int = 0


@dataclass
class Service(_Model):
    id: str = ""
    name: str = ""
    description: str = ""
    prices: dict = field(default_factory=dict)
    durations: dict = field(default_factory=dict)
    materials: list = field(default_factory=list)


@dataclass
class AddOn(_Model):
    id: str = ""
    name: str = ""
    price: float = 0.0
    duration: int = 0
    materials: list = field(default_factory=list)


@dataclass
class Package(_Model):
    id: str = ""
    name: str = ""
    description: str = ""
    service_ids: list = field(default_factory=list)
    discount_percent: float = 0.0


@dataclass
class Promo(_Model):
    code: str = ""
    description: str = ""
    discount_percent: float = 0.0


@dataclass
class InventoryItem(_Model):
    id: str = ""
    name: str = ""
    unit: str = ""
    stock: float = 0.0
    reorder_level: float = 0.0

    @property
    def is_low(self):
        return self.stock <= self.reorder_level


@dataclass
class Appointment(_Model):
    customer_id: int = 0
    vehicle_id: int = 0
    service_ids: list = field(default_factory=list)
    add_on_ids: list = field(default_factory=list)
    package_id: str = ""
    scheduled_start: str = ""
    scheduled_end: str = ""
    status: str = "BOOKED"
    price_breakdown: dict = field(default_factory=dict)
    promo_code: str = ""
    deposit: float = 0.0
    notes: str = ""
    created_at: str = ""
    completed_at: str = ""
    payment: dict = field(default_factory=dict)
    id: int = 0

    @property
    def start_dt(self):
        return datetime.strptime(self.scheduled_start, DATETIME_FORMAT)

    @property
    def end_dt(self):
        return datetime.strptime(self.scheduled_end, DATETIME_FORMAT)


@dataclass
class HistoryEntry(_Model):
    vehicle_id: int = 0
    appointment_id: int = 0
    completed_at: str = ""
    services: list = field(default_factory=list)
    total_price: float = 0.0
    paid: bool = False
    id: int = 0
