"""The shared booking wizard - used by staff AND the customer portal.

Only the flags differ: staff may take walk-ins, deposits and notes;
customers schedule themselves and pay in person at the shop.
"""
from app.exceptions import AppError, ValidationError
from app.ui import catalog_ui, terminal as t
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


def book_flow(stack, customer=None, allow_walk_in=False, allow_deposit=False,
              walk_in=False):
    t.header("NEW BOOKING")
    if customer is None:
        customer = choose_customer(stack)
    vehicle = choose_vehicle(stack, customer)

    while True:
        try:
            service_ids, package_id = choose_services(stack, vehicle.type)
            add_on_ids = choose_add_ons(stack)
            promo_code = choose_promo(stack)
            quote = stack.catalog.build_quote(
                vehicle.type, service_ids, add_on_ids, package_id, promo_code,
            )
        except AppError as exc:
            t.error(str(exc))
            if not t.confirm("Try selecting services again?"):
                return
            continue
        show_quote(stack, quote)
        if t.confirm("Proceed with this quote?"):
            break

    if walk_in:
        start = dtu.now()
    else:
        start = choose_start(stack, quote["duration_minutes"], allow_walk_in)

    deposit, notes = 0.0, ""
    if allow_deposit:
        deposit = t.ask_float("Deposit to collect now", default=0.0, min_value=0.0)
        notes = t.ask("Booking notes (optional)")

    try:
        appt = stack.bookings.create_booking(
            customer.id, vehicle.id, service_ids, add_on_ids, package_id,
            promo_code, start, deposit, notes,
        )
    except AppError as exc:
        t.error(str(exc))
        t.pause()
        return

    t.success(f"Appointment #{appt.id} booked: {appt.scheduled_start} until {appt.scheduled_end}.")
    t.info(f"Total: {money(quote['total'])}"
           + (f"  (deposit collected: {money(deposit)})" if deposit else ""))
    if not allow_deposit:
        t.info("Payment happens in person at the shop - please arrive on time.")
    t.pause()


# --------------------------------------------------------------- choices ---
def _parse_numbers(raw, count, allow_empty=False):
    numbers = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if not part.isdigit():
            raise ValidationError(f"'{part}' is not a valid number.")
        n = int(part)
        if n < 1 or n > count:
            raise ValidationError(f"Number {n} is out of range (1-{count}).")
        if n not in numbers:
            numbers.append(n)
    if not numbers and not allow_empty:
        raise ValidationError("Please pick at least one option.")
    return numbers


def choose_services(stack, vehicle_type):
    services = stack.catalog.services()
    print(f"\n  Services for a {vehicle_type.upper()}:")
    rows = [[i, s.name, money(s.prices.get(vehicle_type, 0)),
             f"{s.durations.get(vehicle_type, '?')} min"]
            for i, s in enumerate(services, 1)]
    print(_table(["#", "Service", "Price", "Duration"], rows, [">", "<", ">", ">"]))
    raw = t.ask("Service numbers (e.g. 1,3) - or 'P' for packages - blank to finish")
    if raw.lower() == "p":
        package = choose_package(stack)
        return [], package.id
    if raw == "":
        raise ValidationError("Select at least one service (or a package).")
    picks = _parse_numbers(raw, len(services))
    return [services[n - 1].id for n in picks], ""


def choose_package(stack):
    packages = stack.catalog.packages()
    rows = [[i, p.name, f"{p.discount_percent:g}%", p.description]
            for i, p in enumerate(packages, 1)]
    print(f"\n  Packages (discount applies to the included services):")
    print(_table(["#", "Package", "Discount", "Description"], rows, [">", "<", ">", "<"]))
    n = t.ask_int("Package number", 1, len(packages))
    return packages[n - 1]


def choose_add_ons(stack):
    add_ons = stack.catalog.add_ons()
    if not add_ons:
        return []
    print("\n  Optional add-ons:")
    rows = [[i, a.name, money(a.price), f"+{a.duration} min"]
            for i, a in enumerate(add_ons, 1)]
    print(_table(["#", "Add-on", "Price", "Extra time"], rows, [">", "<", ">", ">"]))
    raw = t.ask("Add-on numbers (comma-separated, blank for none)")
    if not raw:
        return []
    picks = _parse_numbers(raw, len(add_ons), allow_empty=True)
    return [add_ons[n - 1].id for n in picks]


def choose_promo(stack):
    promos = stack.catalog.promos()
    if not promos:
        return ""
    print("\n  Active promos: " + ", ".join(
        f"{p.code} ({p.discount_percent:g}% off)" for p in promos))
    return t.ask("Promo code (blank for none)").upper()


def choose_start(stack, duration_minutes, allow_walk_in):
    print(f"\n  This job needs about {duration_minutes} minutes in the bay.")
    t.info("The shop schedules around the clock - one bay, "
           f"{15}-minute buffer between jobs.")
    if allow_walk_in:
        print("  [3] Walk-in: start right now")
    choice = t.ask_int(
        "How do you want to schedule? [1] pick date & time  [2] browse next free slots",
        1, 3 if allow_walk_in else 2,
    )
    if choice == 1:
        return t.ask_datetime("Date and time")
    if choice == 3:
        return dtu.now()
    return choose_slot(stack, duration_minutes)


def choose_slot(stack, duration_minutes, count=6):
    slots = stack.bookings.next_slots(duration_minutes, count)
    if not slots:
        t.warn("No free slots found in the next two weeks. Pick a date & time instead.")
        return t.ask_datetime("Date and time")
    print()
    rows = [[i, dtu.fmt(s), dtu.fmt(dtu.add_minutes(s, duration_minutes))]
            for i, s in enumerate(slots, 1)]
    print(_table(["#", "Free start", "Would finish"], rows, [">", "<", "<"]))
    return slots[t.ask_int("Slot number", 1, len(slots)) - 1]


def choose_customer(stack):
    while True:
        query = t.ask("Search customer by name or phone (blank = list everyone)")
        matches = stack.customers.search(query) if query else stack.customers.all()
        rows = [[c.id, c.name, c.phone, c.email or "-"] for c in matches]
        if not t.show_table(["ID", "Name", "Phone", "Email"], rows,
                            empty="No customers found."):
            if t.confirm("Register a new customer instead?"):
                return register_customer(stack)
            continue
        choice = t.ask_int("Customer ID (0 = register a new customer)", 0)
        if choice == 0:
            return register_customer(stack)
        for c in matches:
            if c.id == choice:
                return c
        t.warn("That ID is not in the list above.")


def register_customer(stack, phone_hint=""):
    t.info("Registering a new customer:")
    name = t.ask("Full name")
    phone = phone_hint or t.ask("Phone number")
    email = t.ask("Email address (optional)")
    customer = stack.customers.register(name, phone, email)
    t.success(f"Customer '{customer.name}' registered (ID #{customer.id}).")
    return customer


def choose_vehicle(stack, customer):
    while True:
        vehicles = stack.customers.vehicles_of(customer.id)
        if vehicles:
            rows = [[v.id, v.plate, f"{v.make} {v.model}", v.year, v.color, v.type]
                    for v in vehicles]
            t.show_table(["ID", "Plate", "Vehicle", "Year", "Color", "Type"], rows)
            choice = t.ask_int("Vehicle ID (0 = add a new vehicle)", 0)
            if choice == 0:
                return add_vehicle_flow(stack, customer)
            for v in vehicles:
                if v.id == choice:
                    return v
            t.warn("That ID is not in the list above.")
            continue
        t.warn(f"{customer.name} has no registered vehicles yet.")
        if t.confirm("Add one now?"):
            return add_vehicle_flow(stack, customer)
        raise ValidationError("A vehicle is required to book a service.")


def add_vehicle_flow(stack, customer):
    t.info("Registering a vehicle:")
    plate = t.ask("Plate number (e.g. ABC 1234)")
    make = t.ask("Make (e.g. Toyota)")
    model = t.ask("Model (e.g. Vios)")
    year = t.ask("Year (e.g. 2021)")
    color = t.ask("Color")
    print("  Vehicle type:")
    for i, vt in enumerate(_vehicle_types(), 1):
        print(f"   [{i}] {vt}")
    vtype = _vehicle_types()[t.ask_int("Type", 1, len(_vehicle_types())) - 1]
    notes = t.ask("Notes (optional)")
    vehicle = stack.customers.add_vehicle(
        customer.id, plate, make, model, year, color, vtype, notes,
    )
    t.success(f"Vehicle {vehicle.plate} registered (ID #{vehicle.id}).")
    return vehicle


def _vehicle_types():
    from app.config import VEHICLE_TYPES
    return VEHICLE_TYPES


def _table(headers, rows, aligns):
    from app.utils.formatting import make_table
    return make_table(headers, rows, aligns)


def show_quote(stack, quote):
    t.line()
    print(f"  QUOTE - {quote['vehicle_type'].upper()}")
    for item in quote["items"]:
        print("  " + _dots(item["name"], money(item["price"])))
    print("  " + _dots("Subtotal", money(quote["subtotal"])))
    if quote["package_discount_amount"]:
        name = ""
        try:
            name = stack.catalog.get_package(quote["package_id"]).name
        except AppError:
            name = quote["package_id"]
        print("  " + _dots(f"Package discount ({name})",
                          f"-{money(quote['package_discount_amount'])}"))
    if quote["promo_discount_amount"]:
        print("  " + _dots(f"Promo ({quote['promo_code']})",
                          f"-{money(quote['promo_discount_amount'])}"))
    print("  " + _dots("TOTAL", money(quote["total"])))
    print(f"  Estimated time in the bay: {quote['duration_minutes']} minutes")
    t.line()


def _dots(label, value, width=48):
    dots = max(3, width - len(label) - len(value) - 2)
    return f"{label} {'.' * dots} {value}"
