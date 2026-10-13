"""Shared appointment rendering helpers used by staff and customer screens."""
from app.ui import terminal as t
from app.utils.formatting import money


def services_short(appt):
    names = [i["name"] for i in appt.price_breakdown.get("items", [])]
    text = ", ".join(names[:2])
    if len(names) > 2:
        text += f" (+{len(names) - 2} more)"
    return text or "-"


def row(stack, appt):
    customer = stack.customers.get(appt.customer_id)
    vehicle = stack.customers.vehicle(appt.vehicle_id)
    return [
        appt.id,
        appt.scheduled_start,
        customer.name,
        f"{vehicle.make} {vehicle.model} ({vehicle.type})",
        services_short(appt),
        appt.status,
        money(appt.price_breakdown.get("total", 0.0)),
    ]


def show(stack, appts, empty="No appointments to display."):
    return t.show_table(
        ["ID", "Scheduled", "Customer", "Vehicle", "Service(s)", "Status", "Total"],
        [row(stack, a) for a in appts],
        aligns=[">", "<", "<", "<", "<", "<", ">"],
        empty=empty,
    )


def pick(stack, appts, verb, allow_zero=False):
    """Show a list and let the user choose one appointment ID from it."""
    if not show(stack, appts, empty=f"There is nothing to {verb.lower()}."):
        return None
    appt_id = t.ask_int(f"Enter the ID of the appointment to {verb}")
    for appt in appts:
        if appt.id == appt_id:
            return appt
    t.warn("That ID is not in the list above.")
    return None


def bill(stack, appt):
    """Print the itemized bill for an appointment (used before checkout)."""
    breakdown = appt.price_breakdown
    customer = stack.customers.get(appt.customer_id)
    vehicle = stack.customers.vehicle(appt.vehicle_id)
    t.line()
    print(f"  Appointment #{appt.id} - {vehicle.describe()}")
    print(f"  Customer: {customer.name}")
    t.line()
    for item in breakdown.get("items", []):
        print("  " + _dots(item["name"], money(item["price"])))
    print("  " + _dots("Subtotal", money(breakdown.get("subtotal", 0.0))))
    if breakdown.get("package_discount_amount"):
        print("  " + _dots("Package discount", f"-{money(breakdown['package_discount_amount'])}"))
    if breakdown.get("promo_discount_amount"):
        print("  " + _dots(f"Promo ({breakdown.get('promo_code', '')})",
                          f"-{money(breakdown['promo_discount_amount'])}"))
    print("  " + _dots("TOTAL", money(breakdown.get("total", 0.0))))
    if appt.deposit:
        print("  " + _dots("Deposit already paid", f"-{money(appt.deposit)}"))
        balance = max(breakdown.get("total", 0.0) - appt.deposit, 0.0)
        print("  " + _dots("BALANCE DUE", money(balance)))
    t.line()


def _dots(label, value, width=48):
    dots = max(3, width - len(label) - len(value) - 2)
    return f"{label} {'.' * dots} {value}"
