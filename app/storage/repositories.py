"""Repositories: one small class per data file.

Each repository loads/saves the whole file per operation. That keeps the
code simple (a class project does not need caching) while JsonStore
guarantees atomic writes and corruption recovery underneath.
"""
from app import config
from app.exceptions import NotFoundError
from app.models import (
    AddOn,
    Appointment,
    Customer,
    HistoryEntry,
    InventoryItem,
    Package,
    Promo,
    Service,
    Staff,
    Vehicle,
)
from app.storage.json_store import read_json, write_json


class IdRepository:
    """Base class for records with auto-increment integer ids.

    File shape: {"next_id": int, "records": [ ... ]}
    """
    model = None
    file_key = ""

    @property
    def path(self):
        return config.file_path(self.file_key)

    def _load(self):
        return read_json(self.path, {"next_id": 1, "records": []})

    def _save(self, data):
        write_json(self.path, data)

    def all(self):
        return [self.model.from_dict(r) for r in self._load()["records"]]

    def get(self, record_id):
        try:
            record_id = int(record_id)
        except (TypeError, ValueError):
            raise NotFoundError(self._missing(record_id)) from None
        for record in self.all():
            if record.id == record_id:
                return record
        raise NotFoundError(self._missing(record_id))

    def _missing(self, record_id):
        return f"{self.model.__name__} #{record_id} was not found."

    def add(self, record):
        data = self._load()
        record.id = data["next_id"]
        data["next_id"] += 1
        data["records"].append(record.to_dict())
        self._save(data)
        return record

    def update(self, record):
        data = self._load()
        for i, raw in enumerate(data["records"]):
            if int(raw.get("id", 0)) == record.id:
                data["records"][i] = record.to_dict()
                self._save(data)
                return record
        raise NotFoundError(self._missing(record.id))


class CustomerRepository(IdRepository):
    model = Customer
    file_key = "customers"

    def find_by_phone(self, phone):
        phone = str(phone).replace(" ", "").replace("-", "")
        for customer in self.all():
            if customer.phone == phone:
                return customer
        return None


class VehicleRepository(IdRepository):
    model = Vehicle
    file_key = "vehicles"

    def for_customer(self, customer_id):
        return [v for v in self.all() if v.customer_id == customer_id]

    def find_by_plate(self, plate):
        plate = str(plate).strip().upper()
        for vehicle in self.all():
            if vehicle.plate.upper() == plate:
                return vehicle
        return None


class AppointmentRepository(IdRepository):
    model = Appointment
    file_key = "appointments"


class HistoryRepository(IdRepository):
    model = HistoryEntry
    file_key = "service_history"

    def for_vehicle(self, vehicle_id):
        return [h for h in self.all() if h.vehicle_id == vehicle_id]

    def for_appointment(self, appointment_id):
        for h in self.all():
            if h.appointment_id == appointment_id:
                return h
        return None


class StaffRepository(IdRepository):
    model = Staff
    file_key = "staff"

    def find_by_username(self, username):
        username = str(username).strip().lower()
        for staff in self.all():
            if staff.username.lower() == username:
                return staff
        return None


class InventoryRepository:
    """List-shaped store; ids are strings like 'SHMP01'."""

    @property
    def path(self):
        return config.file_path("inventory")

    def all(self):
        return [InventoryItem.from_dict(r) for r in read_json(self.path, [])]

    def get(self, item_id):
        item_id = str(item_id).strip()
        for item in self.all():
            if item.id == item_id:
                return item
        raise NotFoundError(f"Inventory item '{item_id}' was not found.")

    def save_all(self, items):
        write_json(self.path, [i.to_dict() for i in items])

    def update(self, item):
        items = self.all()
        for i, current in enumerate(items):
            if current.id == item.id:
                items[i] = item
                self.save_all(items)
                return item
        raise NotFoundError(f"Inventory item '{item.id}' was not found.")


class CatalogRepository:
    """Read-only view of the service catalog (services/add-ons/packages/promos)."""

    @property
    def path(self):
        return config.file_path("service_catalog")

    def _load(self):
        from app import defaults
        return read_json(self.path, defaults.CATALOG)

    def services(self):
        return [Service.from_dict(s) for s in self._load()["services"]]

    def add_ons(self):
        return [AddOn.from_dict(a) for a in self._load()["add_ons"]]

    def packages(self):
        return [Package.from_dict(p) for p in self._load()["packages"]]

    def promos(self):
        return [Promo.from_dict(p) for p in self._load()["promos"]]
