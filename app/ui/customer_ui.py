"""Customer portal: self-service booking, viewing, rescheduling, history."""
from app import config
from app.ui import appt_view, booking_ui, catalog_ui, terminal as t
from app.utils import datetime_utils as dtu


def run(stack, customer):
    t.success(f"Welcome, {customer.name}!")
    t.menu(f"CUSTOMER PORTAL - {customer.name}", [
        ("View services & prices", lambda: catalog_ui.browse(stack)),
        ("Book an appointment", lambda: booking_ui.book_flow(stack, customer=customer)),
        ("My appointments (view / cancel)", lambda: my_appointments(stack, customer)),
        ("Reschedule an appointment", lambda: reschedule(stack, customer)),
        ("My vehicles & service history", lambda: my_vehicles(stack, customer)),
        ("My profile", lambda: profile(stack, customer)),
    ], footer="Log out")


def my_appointments(stack, customer):
    appts = stack.bookings.for_customer(customer.id)
    if not appt_view.show(stack, appts, empty="You have no appointments yet."):
        return
    booked = [a for a in appts
              if a.status == config.STATUS_BOOKED and a.start_dt >= dtu.now()]
    if not booked:
        t.info("Nothing here can be cancelled (only future BOOKED appointments).")
        return
    if t.confirm("Cancel one of your booked appointments?"):
        appt = appt_view.pick(stack, booked, "cancel")
        if appt and t.confirm(f"Cancel appointment #{appt.id} ({appt.scheduled_start})?"):
            stack.bookings.cancel(appt.id)
            t.success("Cancelled. We hope to see you another time!")
    t.pause()


def reschedule(stack, customer):
    booked = [a for a in stack.bookings.for_customer(customer.id)
              if a.status == config.STATUS_BOOKED and a.start_dt >= dtu.now()]
    appt = appt_view.pick(stack, booked, "reschedule")
    if appt is None:
        return
    duration = appt.price_breakdown.get("duration_minutes", 60)
    new_start = booking_ui.choose_start(stack, duration, allow_walk_in=False)
    updated = stack.bookings.reschedule(appt.id, new_start)
    t.success(f"Moved to {updated.scheduled_start} (until {updated.scheduled_end}).")
    t.pause()


def my_vehicles(stack, customer):
    vehicles = stack.customers.vehicles_of(customer.id)
    rows = [[v.id, v.plate, f"{v.make} {v.model}", v.year, v.color, v.type, v.notes or "-"]
            for v in vehicles]
    if not t.show_table(["ID", "Plate", "Vehicle", "Year", "Color", "Type", "Notes"],
                        rows, empty="No vehicles registered to your account yet."):
        return
    if t.confirm("Add another vehicle?"):
        booking_ui.add_vehicle_flow(stack, customer)
        return
    vehicle_id = t.ask_int("Vehicle ID to view its service history (0 = skip)", 0)
    for v in vehicles:
        if v.id == vehicle_id:
            appt_view_header = f"SERVICE HISTORY - {v.plate}"
            t.header(appt_view_header)
            entries = stack.customers.vehicle_history(v.id)
            from app.utils.formatting import money
            rows = [[e.completed_at, ", ".join(s["name"] for s in e.services),
                     money(e.total_price), "PAID" if e.paid else "UNPAID"]
                    for e in entries]
            t.show_table(["Completed at", "Services", "Total", "Status"], rows,
                         empty="No service history for this vehicle yet.")
            t.pause()
            return
    if vehicle_id != 0:
        t.warn("That ID is not in the list above.")


def profile(stack, customer):
    t.header("MY PROFILE")
    print(f"  Name  : {customer.name}")
    print(f"  Phone : {customer.phone}")
    print(f"  Email : {customer.email or '-'}")
    print(f"  Notes : {customer.notes or '-'}")
    t.info("Need to update your details? Just ask our staff at the shop.")
    t.pause()
