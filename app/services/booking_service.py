"""The heart of the system: scheduling, conflicts, and the job pipeline.

Scheduling rules (single detailing bay):
- any date/time is allowed (the shop schedules around the clock)
- a booking may never start in the past
- two jobs can never overlap, and must be separated by at least
  BOOKING_BUFFER_MINUTES for setup/cleanup

Job pipeline (with fail-safes on every transition):
    BOOKED -> IN_PROGRESS -> DONE -> PAID
    BOOKED -> CANCELLED
    BOOKED -> NO_SHOW (only once the scheduled time has passed)
"""
from datetime import timedelta

from app import config
from app.exceptions import BookingError, ValidationError
from app.models import Appointment, HistoryEntry
from app.utils import datetime_utils as dtu
from app.utils.validation import to_float

ACTIVE_STATUSES = (config.STATUS_BOOKED, config.STATUS_IN_PROGRESS)


class BookingService:
    def __init__(self, appointment_repo, catalog_service, customer_repo,
                 vehicle_repo, inventory_service, history_repo):
        self.appointments = appointment_repo
        self.catalog = catalog_service
        self.customers = customer_repo
        self.vehicles = vehicle_repo
        self.inventory = inventory_service
        self.history = history_repo

    # ------------------------------------------------------------ lookups ---
    def get(self, appointment_id):
        return self.appointments.get(appointment_id)

    def schedule_for(self, date_str):
        """All appointments that start on the given 'YYYY-MM-DD', earliest first."""
        appts = [a for a in self.appointments.all()
                 if a.scheduled_start.startswith(date_str)]
        return sorted(appts, key=lambda a: a.scheduled_start)

    def upcoming(self):
        horizon = dtu.now() + timedelta(days=config.MAX_SEARCH_DAYS)
        appts = [a for a in self.appointments.all()
                 if a.status in ACTIVE_STATUSES
                 and a.start_dt >= dtu.now()
                 and a.start_dt <= horizon]
        return sorted(appts, key=lambda a: a.scheduled_start)

    def for_customer(self, customer_id):
        appts = [a for a in self.appointments.all() if a.customer_id == customer_id]
        return sorted(appts, key=lambda a: a.scheduled_start)

    def with_status(self, status):
        appts = [a for a in self.appointments.all() if a.status == status]
        return sorted(appts, key=lambda a: a.scheduled_start)

    def unpaid_completed(self):
        """Jobs finished but not yet paid (awaiting checkout)."""
        return self.with_status(config.STATUS_DONE)

    # --------------------------------------------------------- slot logic ---
    def _slot_is_free(self, start, end, exclude_id=None):
        for appt in self.appointments.all():
            if appt.id == exclude_id or appt.status not in ACTIVE_STATUSES:
                continue
            buffer = timedelta(minutes=config.BOOKING_BUFFER_MINUTES)
            if (start < appt.end_dt + buffer
                    and appt.start_dt < end + buffer):
                return False
        return True

    def _require_free_slot(self, start, end, exclude_id=None):
        if not self._slot_is_free(start, end, exclude_id):
            for appt in self.appointments.all():
                if appt.id == exclude_id or appt.status not in ACTIVE_STATUSES:
                    continue
                buffer = timedelta(minutes=config.BOOKING_BUFFER_MINUTES)
                if start < appt.end_dt + buffer and appt.start_dt < end + buffer:
                    raise BookingError(
                        f"The detailing bay is busy at that time (conflicts with "
                        f"appointment #{appt.id} on {appt.scheduled_start}). "
                        f"Leave at least {config.BOOKING_BUFFER_MINUTES} minutes "
                        f"between jobs."
                    )

    def next_slots(self, duration_minutes, count=6, from_dt=None):
        """The next `count` free start times for a job of this duration."""
        step = timedelta(minutes=30)
        cursor = dtu.ceil_to(from_dt or dtu.now(), 15)
        limit = dtu.now() + timedelta(days=config.MAX_SEARCH_DAYS)
        slots = []
        while len(slots) < count and cursor <= limit:
            end = dtu.add_minutes(cursor, duration_minutes)
            if cursor >= dtu.now() and self._slot_is_free(cursor, end):
                slots.append(cursor)
            cursor += step
        return slots

    # ------------------------------------------------------------ booking ---
    def create_booking(self, customer_id, vehicle_id, service_ids=None,
                       add_on_ids=None, package_id="", promo_code="",
                       start_dt=None, deposit=0.0, notes="", walk_in=False):
        customer = self.customers.get(customer_id)
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle.customer_id != customer.id:
            raise ValidationError("That vehicle does not belong to the selected customer.")

        if start_dt is None:
            start_dt = dtu.now()          # walk-in: start immediately
        # 1-minute grace so a walk-in booked "right now" is not rejected
        if start_dt < dtu.now() - timedelta(minutes=1):
            raise BookingError("That date and time is already in the past.")

        quote = self.catalog.build_quote(
            vehicle.type, service_ids, add_on_ids, package_id, promo_code,
        )
        end_dt = dtu.add_minutes(start_dt, quote["duration_minutes"])
        self._require_free_slot(start_dt, end_dt)
        self.inventory.check_materials(quote["materials"])

        deposit = to_float(deposit, "Deposit", minimum=0.0)
        if deposit > quote["total"]:
            raise ValidationError("The deposit cannot be greater than the total price.")

        return self.appointments.add(Appointment(
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            service_ids=[i["id"] for i in quote["items"] if i["kind"] == "service"],
            add_on_ids=[i["id"] for i in quote["items"] if i["kind"] == "add_on"],
            package_id=quote["package_id"],
            scheduled_start=dtu.fmt(start_dt),
            scheduled_end=dtu.fmt(end_dt),
            status=config.STATUS_BOOKED,
            price_breakdown=quote,
            promo_code=quote["promo_code"],
            deposit=deposit,
            notes=notes if walk_in is False else notes,
            created_at=dtu.now_str(),
        ))

    # ---------------------------------------------------- status changes ----
    def reschedule(self, appointment_id, new_start):
        appt = self.get(appointment_id)
        if appt.status != config.STATUS_BOOKED:
            raise BookingError("Only appointments that are still BOOKED can be rescheduled.")
        if new_start < dtu.now():
            raise BookingError("The new date and time is in the past.")
        duration = appt.price_breakdown.get("duration_minutes", 60)
        new_end = dtu.add_minutes(new_start, duration)
        self._require_free_slot(new_start, new_end, exclude_id=appt.id)
        appt.scheduled_start = dtu.fmt(new_start)
        appt.scheduled_end = dtu.fmt(new_end)
        return self.appointments.update(appt)

    def cancel(self, appointment_id):
        appt = self.get(appointment_id)
        if appt.status != config.STATUS_BOOKED:
            raise BookingError("Only appointments that are still BOOKED can be cancelled.")
        appt.status = config.STATUS_CANCELLED
        return self.appointments.update(appt)

    def mark_no_show(self, appointment_id):
        appt = self.get(appointment_id)
        if appt.status != config.STATUS_BOOKED:
            raise BookingError("Only appointments that are still BOOKED can be marked as a no-show.")
        if appt.start_dt >= dtu.now():
            raise BookingError("You can only mark a no-show once the scheduled time has passed.")
        appt.status = config.STATUS_NO_SHOW
        return self.appointments.update(appt)

    def start_job(self, appointment_id):
        """BOOKED -> IN_PROGRESS. Materials are deducted from stock here."""
        appt = self.get(appointment_id)
        if appt.status != config.STATUS_BOOKED:
            raise BookingError("Only BOOKED jobs can be started.")
        self.inventory.consume(appt.price_breakdown.get("materials", []))
        appt.status = config.STATUS_IN_PROGRESS
        return self.appointments.update(appt)

    def complete_job(self, appointment_id):
        """IN_PROGRESS -> DONE. Writes the vehicle's service history entry."""
        appt = self.get(appointment_id)
        if appt.status != config.STATUS_IN_PROGRESS:
            raise BookingError("Only jobs that are IN PROGRESS can be completed.")
        appt.status = config.STATUS_DONE
        appt.completed_at = dtu.now_str()
        self.appointments.update(appt)

        breakdown = appt.price_breakdown
        self.history.add(HistoryEntry(
            vehicle_id=appt.vehicle_id,
            appointment_id=appt.id,
            completed_at=appt.completed_at,
            services=[{"id": i["id"], "name": i["name"], "price": i["price"]}
                      for i in breakdown.get("items", [])],
            total_price=breakdown.get("total", 0.0),
            paid=False,
        ))
        return appt
