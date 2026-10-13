"""Creates/refreshes the JSON data files, including a demo dataset.

Demo bookings use dates relative to *today*, so reports and dashboards
always have something to show no matter when the project is graded.
Run `python main.py --reseed` at any time to regenerate them.
"""
from datetime import timedelta

from app import config, defaults
from app.models import Appointment, HistoryEntry
from app.storage.json_store import ensure_file, write_json
from app.storage.repositories import (
    AppointmentRepository, CatalogRepository, HistoryRepository,
    VehicleRepository,
)
from app.services.catalog_service import CatalogService
from app.utils import datetime_utils as dtu


class Seeder:
    def ensure_all(self, force=False):
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if force:
            for key in config.FILES:
                path = config.file_path(key)
                for suffix in ("", ".bak", ".tmp"):
                    candidate = path.with_name(path.name + suffix)
                    if candidate.exists():
                        candidate.unlink()

        ensure_file(config.file_path("service_catalog"), defaults.CATALOG)
        ensure_file(config.file_path("inventory"), defaults.INVENTORY)
        ensure_file(config.file_path("staff"), {"next_id": 4, "records": defaults.STAFF})
        ensure_file(config.file_path("customers"), {"next_id": 5, "records": defaults.CUSTOMERS})
        ensure_file(config.file_path("vehicles"), {"next_id": 5, "records": defaults.VEHICLES})

        if force or not config.file_path("appointments").exists():
            write_json(config.file_path("appointments"), {"next_id": 1, "records": []})
            write_json(config.file_path("service_history"), {"next_id": 1, "records": []})
            self._demo_bookings()

    # ------------------------------------------------------------- helpers ---
    def _at(self, day_offset, hour, minute=0):
        base = dtu.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        return base + timedelta(days=day_offset)

    def _demo_bookings(self):
        appointments = AppointmentRepository()
        history = HistoryRepository()
        vehicles = VehicleRepository()
        catalog = CatalogService(CatalogRepository())

        demo = [
            # two finished & paid jobs yesterday -> sales history
            dict(day=-1, hour=9, customer=1, vehicle=1,
                 services=["SVC001", "SVC002"], add_ons=[], package="", promo="",
                 deposit=0, status=config.STATUS_PAID),
            dict(day=-1, hour=14, customer=2, vehicle=2,
                 services=["SVC003"], add_ons=[], package="", promo="",
                 deposit=0, status=config.STATUS_PAID),
            # finished today, still awaiting checkout -> demo the cashier flow
            dict(day=0, hour=10, customer=3, vehicle=3,
                 services=["SVC001"], add_ons=[], package="", promo="",
                 deposit=0, status=config.STATUS_DONE),
            # today & next days: live schedule for the dashboard
            dict(day=0, hour=13, customer=4, vehicle=4,
                 services=[], add_ons=[], package="PKG002", promo="",
                 deposit=1000, status=config.STATUS_BOOKED),
            dict(day=1, hour=9, customer=1, vehicle=1,
                 services=["SVC006"], add_ons=[], package="", promo="",
                 deposit=1000, status=config.STATUS_BOOKED),
            dict(day=1, hour=15, customer=2, vehicle=2,
                 services=["SVC009"], add_ons=["ADD003"], package="", promo="LUSTRA10",
                 deposit=0, status=config.STATUS_BOOKED),
            dict(day=2, hour=11, customer=4, vehicle=4,
                 services=["SVC004", "SVC005"], add_ons=[], package="", promo="",
                 deposit=0, status=config.STATUS_BOOKED),
        ]

        for spec in demo:
            vehicle = vehicles.get(spec["vehicle"])
            quote = catalog.build_quote(
                vehicle.type, spec["services"], spec["add_ons"],
                spec["package"], spec["promo"],
            )
            start = self._at(spec["day"], spec["hour"])
            end = dtu.add_minutes(start, quote["duration_minutes"])
            completed_at = dtu.fmt(end)

            appt = appointments.add(Appointment(
                customer_id=spec["customer"],
                vehicle_id=spec["vehicle"],
                service_ids=[i["id"] for i in quote["items"] if i["kind"] == "service"],
                add_on_ids=[i["id"] for i in quote["items"] if i["kind"] == "add_on"],
                package_id=quote["package_id"],
                scheduled_start=dtu.fmt(start),
                scheduled_end=completed_at,
                status=config.STATUS_BOOKED,
                price_breakdown=quote,
                promo_code=quote["promo_code"],
                deposit=float(spec["deposit"]),
                notes="",
                created_at=dtu.fmt(start - timedelta(days=1)),
            ))

            entry = None
            if spec["status"] in (config.STATUS_DONE, config.STATUS_PAID):
                appt.status = config.STATUS_DONE
                appt.completed_at = completed_at
                entry = history.add(HistoryEntry(
                    vehicle_id=appt.vehicle_id,
                    appointment_id=appt.id,
                    completed_at=completed_at,
                    services=[{"id": i["id"], "name": i["name"], "price": i["price"]}
                              for i in quote["items"]],
                    total_price=quote["total"],
                    paid=False,
                ))

            if spec["status"] == config.STATUS_PAID:
                appt.status = config.STATUS_PAID
                appt.payment = {
                    "method": "gcash",
                    "amount": quote["total"],
                    "balance": quote["total"],
                    "deposit": 0.0,
                    "paid_at": completed_at,
                    "cashier": "Mara Santos",
                    "receipt_file": "",
                }
                entry.paid = True
                history.update(entry)

            appointments.update(appt)
