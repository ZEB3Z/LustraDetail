"""Staff-facing screens, gated by role (admin / detailer / cashier)."""
from app import config
from app.ui import appt_view, booking_ui, catalog_ui, reports_ui, terminal as t
from app.utils import datetime_utils as dtu
from app.utils.formatting import money

ALL_ROLES = ("admin", "detailer", "cashier")
FRONT = ("admin", "cashier")     # booking desk
BAY = ("admin", "detailer")      # works on cars

TOP_MENU = {
    "dashboard": ("Dashboard", lambda stack, staff: dashboard(stack, staff)),
    "appointments": ("Appointments", lambda stack, staff: appointments(stack, staff)),
    "customers": ("Customers & vehicles", lambda stack, staff: customers(stack)),
    "catalog": ("Service catalog", lambda stack, staff: catalog_ui.browse(stack)),
    "inventory": ("Inventory", lambda stack, staff: inventory(stack, staff)),
    "reports": ("Reports", lambda stack, staff: reports_ui.browse(stack)),
    "staff": ("Staff management (admin)", lambda stack, staff: staff_admin(stack, staff)),
}

ROLE_MENUS = {
    "admin": ["dashboard", "appointments", "customers", "catalog",
              "inventory", "reports", "staff"],
    "cashier": ["dashboard", "appointments", "customers", "catalog", "reports"],
    "detailer": ["dashboard", "appointments", "catalog", "inventory"],
}


def run(stack, staff):
    options = [(label, lambda s=stack, st=staff, fn=fn: fn(s, st))
               for key, (label, fn) in
               ((k, TOP_MENU[k]) for k in ROLE_MENUS[staff.role])]
    t.menu(f"STAFF MENU - {staff.name} ({staff.role})", options, footer="Log out")


# ------------------------------------------------------------ dashboard ----
def dashboard(stack, staff):
    t.header("DASHBOARD - TODAY")
    today = dtu.today_str()
    appts = stack.bookings.schedule_for(today)
    appt_view.show(stack, appts,
                   empty="No appointments scheduled for today (yet).")

    counts = {status: 0 for status in config.ALL_STATUSES}
    for appt in stack.bookings.schedule_for(today):
        counts[appt.status] = counts.get(appt.status, 0) + 1
    print(f"\n  Today: {counts.get(config.STATUS_BOOKED, 0)} booked, "
          f"{counts.get(config.STATUS_IN_PROGRESS, 0)} in progress, "
          f"{counts.get(config.STATUS_DONE, 0)} done, "
          f"{counts.get(config.STATUS_PAID, 0)} paid.")
    unpaid = stack.bookings.unpaid_completed()
    if unpaid:
        t.warn(f"{len(unpaid)} finished job(s) awaiting checkout.")
    low = stack.inventory.low_stock()
    if low:
        t.warn("Low stock: " + ", ".join(f"{i.name} ({i.stock:g} {i.unit})" for i in low))
    else:
        t.success("Inventory levels look healthy.")
    t.pause()


# ---------------------------------------------------------- appointments ---
def appointments(stack, staff):
    actions = [
        ("View the schedule for a date", ALL_ROLES, lambda: view_date(stack)),
        ("View upcoming appointments", ALL_ROLES, lambda: view_upcoming(stack)),
        ("New booking (scheduled)", FRONT, lambda: booking_ui.book_flow(
            stack, allow_walk_in=True, allow_deposit=True)),
        ("Walk-in: book and start right now", FRONT,
         lambda: booking_ui.book_flow(stack, allow_walk_in=True, allow_deposit=True, walk_in=True)),
        ("Start a job (BOOKED -> IN PROGRESS)", BAY, lambda: start_job(stack)),
        ("Complete a job (IN PROGRESS -> DONE)", BAY, lambda: complete_job(stack)),
        ("Reschedule an appointment", FRONT, lambda: reschedule(stack)),
        ("Cancel an appointment", FRONT, lambda: cancel(stack)),
        ("Mark a no-show", FRONT, lambda: no_show(stack)),
        ("Checkout & print receipt", FRONT, lambda: checkout(stack, staff)),
    ]
    options = [(label, fn) for label, roles, fn in actions if staff.role in roles]
    t.menu("APPOINTMENTS", options)


def view_date(stack):
    date = t.ask_date("Schedule for which date", default_today=True)
    appt_view.show(stack, stack.bookings.schedule_for(date),
                   empty=f"Nothing scheduled on {date}.")


def view_upcoming(stack):
    appt_view.show(stack, stack.bookings.upcoming(),
                   empty="No upcoming appointments in the next two weeks.")


def start_job(stack):
    candidates = stack.bookings.with_status(config.STATUS_BOOKED)
    appt = appt_view.pick(stack, candidates, "start")
    if appt is None:
        return
    if not t.confirm(f"Start appointment #{appt.id} ({appt.scheduled_start}) now? "
                    "Materials will be deducted from inventory."):
        return
    stack.bookings.start_job(appt.id)
    t.success(f"Job #{appt.id} is now IN PROGRESS. Deducted materials from stock.")
    t.pause()


def complete_job(stack):
    candidates = stack.bookings.with_status(config.STATUS_IN_PROGRESS)
    appt = appt_view.pick(stack, candidates, "complete")
    if appt is None:
        return
    if not t.confirm(f"Mark appointment #{appt.id} as DONE? "
                    "A service history entry will be recorded."):
        return
    stack.bookings.complete_job(appt.id)
    t.success(f"Job #{appt.id} is DONE. The cashier can now check it out.")
    t.pause()


def reschedule(stack):
    appt = appt_view.pick(stack, stack.bookings.with_status(config.STATUS_BOOKED),
                          "reschedule")
    if appt is None:
        return
    duration = appt.price_breakdown.get("duration_minutes", 60)
    new_start = booking_ui.choose_start(stack, duration, allow_walk_in=True)
    updated = stack.bookings.reschedule(appt.id, new_start)
    t.success(f"Appointment #{appt.id} moved to {updated.scheduled_start} "
              f"(until {updated.scheduled_end}).")
    t.pause()


def cancel(stack):
    appt = appt_view.pick(stack, stack.bookings.with_status(config.STATUS_BOOKED),
                          "cancel")
    if appt is None:
        return
    if t.confirm(f"Cancel appointment #{appt.id} ({appt.scheduled_start})?"):
        stack.bookings.cancel(appt.id)
        t.success(f"Appointment #{appt.id} cancelled. The slot is free again.")
    t.pause()


def no_show(stack):
    past = [a for a in stack.bookings.with_status(config.STATUS_BOOKED)
            if a.start_dt < dtu.now()]
    appt = appt_view.pick(stack, past, "mark as a no-show")
    if appt is None:
        return
    if t.confirm(f"Mark appointment #{appt.id} as a NO-SHOW?"):
        stack.bookings.mark_no_show(appt.id)
        t.success(f"Appointment #{appt.id} marked as a no-show.")
    t.pause()


def checkout(stack, staff):
    appt = appt_view.pick(stack, stack.bookings.unpaid_completed(), "check out")
    if appt is None:
        return
    appt_view.bill(stack, appt)
    print("  Payment method:")
    for i, method in enumerate(config.PAYMENT_METHODS, 1):
        print(f"   [{i}] {method}")
    method = config.PAYMENT_METHODS[t.ask_int("Method", 1, len(config.PAYMENT_METHODS)) - 1]
    amount = None
    if method == "cash":
        balance = max(appt.price_breakdown.get("total", 0.0) - appt.deposit, 0.0)
        amount = t.ask_float(f"Amount received (balance is {money(balance)})",
                             min_value=0.0)

    appt, receipt_path, change = stack.payments.checkout(
        appt.id, method, amount, staff.name)
    t.success(f"Appointment #{appt.id} is now PAID.")
    if method == "cash":
        t.info(f"Change due: {money(change)}")
    t.info(f"Receipt saved to: {receipt_path}")
    if t.confirm("Display the receipt on screen?"):
        print("\n" + receipt_path.read_text(encoding="utf-8"))
    t.pause()


# ------------------------------------------------------------- customers ---
def customers(stack):
    def list_all():
        rows = []
        for c in stack.customers.all():
            vehicles = stack.customers.vehicles_of(c.id)
            rows.append([c.id, c.name, c.phone, c.email or "-", len(vehicles)])
        t.show_table(["ID", "Name", "Phone", "Email", "Vehicles"], rows)

    def search():
        query = t.ask("Search by name or phone")
        matches = stack.customers.search(query)
        rows = [[c.id, c.name, c.phone, c.email or "-"] for c in matches]
        t.show_table(["ID", "Name", "Phone", "Email"], rows,
                     empty="No customers matched that search.")

    def view_customer():
        customer = booking_ui.choose_customer(stack)
        vehicles = stack.customers.vehicles_of(customer.id)
        rows = [[v.id, v.plate, f"{v.make} {v.model}", v.year, v.color, v.type]
                for v in vehicles]
        t.show_table(["ID", "Plate", "Vehicle", "Year", "Color", "Type"], rows,
                     empty="This customer has no vehicles registered.")
        if not vehicles:
            return
        vehicle_id = t.ask_int("Vehicle ID to view service history (0 = skip)", 0)
        if vehicle_id == 0:
            return
        for v in vehicles:
            if v.id == vehicle_id:
                show_history(stack, v)
                return
        t.warn("That ID is not in the list above.")

    t.menu("CUSTOMERS & VEHICLES", [
        ("List all customers", list_all),
        ("Search customers", search),
        ("Register a new customer", lambda: booking_ui.register_customer(stack)),
        ("Add a vehicle to a customer",
         lambda: _add_vehicle_to(stack)),
        ("View a customer's vehicles & history", view_customer),
    ])


def _add_vehicle_to(stack):
    customer = booking_ui.choose_customer(stack)
    booking_ui.add_vehicle_flow(stack, customer)


def show_history(stack, vehicle):
    entries = stack.customers.vehicle_history(vehicle.id)
    rows = [[e.completed_at, ", ".join(s["name"] for s in e.services),
             money(e.total_price), "PAID" if e.paid else "UNPAID"]
            for e in entries]
    t.show_table(["Completed at", "Services", "Total", "Status"], rows,
                 empty="No service history for this vehicle yet.")
    if entries:
        t.pause()


# ------------------------------------------------------------- inventory ---
def inventory(stack, staff):
    def view():
        rows = [[i.id, i.name, i.stock, i.unit, i.reorder_level,
                 "LOW" if i.is_low else "OK"] for i in stack.inventory.all()]
        t.show_table(["ID", "Item", "Stock", "Unit", "Reorder at", "Status"],
                     rows, aligns=["<", "<", ">", "<", ">", "<"])

    def low():
        rows = [[i.id, i.name, i.stock, i.unit, i.reorder_level]
                for i in stack.inventory.low_stock()]
        t.show_table(["ID", "Item", "Stock", "Unit", "Reorder at"], rows,
                     empty="Nothing is below its reorder level.")

    def restock():
        view()
        item_id = t.ask("Item ID to restock")
        qty = t.ask_float("Quantity to add", min_value=0.01)
        item = stack.inventory.restock(item_id, qty)
        t.success(f"{item.name} restocked to {item.stock:g} {item.unit}.")

    options = [("View inventory", view), ("Low stock report", low)]
    if staff.role == "admin":
        options.append(("Restock an item", restock))
    t.menu("INVENTORY", options)


# ------------------------------------------------------------------ staff ---
def staff_admin(stack, staff):
    def list_staff():
        rows = [[s.id, s.name, s.role, s.username,
                 "ACTIVE" if s.active else "INACTIVE"] for s in stack.staff.all()]
        t.show_table(["ID", "Name", "Role", "Username", "Status"], rows)

    def add_staff():
        name = t.ask("Full name")
        print("  Role:")
        for i, role in enumerate(config.STAFF_ROLES, 1):
            print(f"   [{i}] {role}")
        role = config.STAFF_ROLES[t.ask_int("Role", 1, len(config.STAFF_ROLES)) - 1]
        username = t.ask("Username")
        password = t.ask("Password")
        phone = t.ask("Phone number")
        member = stack.staff.add(name, role, username, password, phone)
        t.success(f"Staff '{member.name}' added as {member.role}.")

    def toggle():
        list_staff()
        member_id = t.ask_int("Staff ID to activate/deactivate")
        member = stack.staff.toggle_active(member_id, staff)
        state = "ACTIVE" if member.active else "INACTIVE"
        t.success(f"{member.name} is now {state}.")

    t.menu("STAFF MANAGEMENT", [
        ("List staff", list_staff),
        ("Add a staff member", add_staff),
        ("Activate / deactivate a staff member", toggle),
    ])
