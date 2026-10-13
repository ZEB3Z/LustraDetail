"""Customer and vehicle management."""
from app.exceptions import ValidationError
from app.models import Customer, Vehicle
from app.utils import datetime_utils as dtu
from app.utils.validation import (
    clean, require, valid_email, valid_name, valid_phone,
    valid_plate, valid_vehicle_type, valid_year,
)


class CustomerService:
    def __init__(self, customer_repo, vehicle_repo, history_repo=None):
        self.customers = customer_repo
        self.vehicles = vehicle_repo
        self.history = history_repo

    # ---------------------------------------------------------- customers ---
    def all(self):
        return self.customers.all()

    def get(self, customer_id):
        return self.customers.get(customer_id)

    def register(self, name, phone, email=""):
        name = valid_name(name)
        phone = valid_phone(phone)
        email = valid_email(email)
        if self.customers.find_by_phone(phone):
            raise ValidationError("A customer with this phone number is already registered.")
        return self.customers.add(Customer(
            name=name, phone=phone, email=email, created_at=dtu.now_str(),
        ))

    def search(self, query):
        query = clean(query).lower()
        if not query:
            return []
        return [c for c in self.all()
                if query in c.name.lower() or query in c.phone]

    # ----------------------------------------------------------- vehicles ---
    def vehicle(self, vehicle_id):
        return self.vehicles.get(vehicle_id)

    def vehicles_of(self, customer_id):
        return self.vehicles.for_customer(customer_id)

    def add_vehicle(self, customer_id, plate, make, model, year, color,
                    vehicle_type, notes=""):
        self.get(customer_id)
        vehicle = Vehicle(
            customer_id=customer_id,
            plate=valid_plate(plate),
            make=require(make, "Make"),
            model=require(model, "Model"),
            year=valid_year(year),
            color=require(color, "Color"),
            type=valid_vehicle_type(vehicle_type),
            notes=clean(notes),
        )
        if self.vehicles.find_by_plate(vehicle.plate):
            raise ValidationError(f"A vehicle with plate {vehicle.plate} is already registered.")
        return self.vehicles.add(vehicle)

    # ------------------------------------------------------------ history ---
    def vehicle_history(self, vehicle_id):
        entries = self.history.for_vehicle(vehicle_id) if self.history else []
        return sorted(entries, key=lambda e: e.completed_at, reverse=True)
