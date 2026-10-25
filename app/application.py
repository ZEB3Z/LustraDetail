"""Application wiring: builds the object graph and starts the Tkinter UI.

The UI only ever receives this `stack` object, so build_stack() stays
identical no matter which front end sits on top of it.
"""
import sys
from types import SimpleNamespace

USAGE = """
LustraDetail Auto Care - a desktop auto detailing management system (Tkinter).

Usage:
    python main.py              Start the application.
    python main.py --reseed     Reset all data files to the fresh demo dataset.
    python main.py --help       Show this message.
"""


def build_stack():
    """Create repositories and services and hand them back as one bundle."""
    from app.storage.repositories import (
        AppointmentRepository, CatalogRepository, CustomerRepository,
        HistoryRepository, InventoryRepository, StaffRepository, VehicleRepository,
    )
    from app.services.auth_service import AuthService
    from app.services.booking_service import BookingService
    from app.services.catalog_service import CatalogService
    from app.services.customer_service import CustomerService
    from app.services.inventory_service import InventoryService
    from app.services.payment_service import PaymentService
    from app.services.report_service import ReportService
    from app.services.staff_service import StaffService

    customer_repo = CustomerRepository()
    vehicle_repo = VehicleRepository()
    appointment_repo = AppointmentRepository()
    history_repo = HistoryRepository()
    staff_repo = StaffRepository()
    inventory_repo = InventoryRepository()
    catalog_repo = CatalogRepository()

    inventory = InventoryService(inventory_repo)
    catalog = CatalogService(catalog_repo)
    customers = CustomerService(customer_repo, vehicle_repo, history_repo)
    bookings = BookingService(appointment_repo, catalog, customer_repo,
                              vehicle_repo, inventory, history_repo)
    payments = PaymentService(appointment_repo, customer_repo, vehicle_repo, history_repo)
    reports = ReportService(appointment_repo, customer_repo, vehicle_repo, inventory)
    auth = AuthService(staff_repo, customer_repo)
    staff = StaffService(staff_repo)

    return SimpleNamespace(
        auth=auth, customers=customers, catalog=catalog, bookings=bookings,
        inventory=inventory, payments=payments, reports=reports, staff=staff,
    )


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(USAGE)
        return

    from app import config
    from app.services.seed_service import Seeder
    Seeder().ensure_all(force="--reseed" in sys.argv)

    stack = build_stack()

    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("\n  Tkinter is not installed for this Python.\n"
              "  Windows/macOS: reinstall Python from python.org with the 'tcl/tk' option ticked.\n"
              "  Debian/Ubuntu: sudo apt install python3-tk\n"
              "  Fedora:        sudo dnf install python3-tkinter\n")
        sys.exit(1)

    from app.ui.app_ui import run
    try:
        run(stack)
    except KeyboardInterrupt:
        print("\n  Interrupted. Goodbye!")
