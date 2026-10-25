"""Small modal forms: register customer, add vehicle, checkout, reschedule,
restock, add staff, receipt viewer."""
import tkinter as tk
from datetime import datetime

from app import config
from app.exceptions import AppError
from app.ui import common
from app.ui.theme import C, F, px
from app.ui.widgets import (Button, Card, DateTimeField, Dialog, Field, Label, Segmented,
                            Select, TextArea, toast)
from app.utils.formatting import money


def _pair(parent, make_left, make_right):
    """Two fields side by side. The factories receive the row as their parent."""
    row = tk.Frame(parent, bg=C.surface)
    row.pack(fill="x", pady=(0, px(12)))
    left, right = make_left(row), make_right(row)
    left.pack(side="left", fill="x", expand=True, padx=(0, px(8)))
    right.pack(side="left", fill="x", expand=True, padx=(px(8), 0))
    return left, right


def register_customer(master, stack, phone_hint=""):
    dlg = Dialog(master, "Register customer", "Create an account so they can book services.",
                 icon="user_plus", width=520)
    name = Field(dlg.body, "Full name", placeholder="e.g. Juan Dela Cruz", icon="user")
    name.pack(fill="x", pady=(0, px(12)))
    phone = Field(dlg.body, "Phone number", value=phone_hint, placeholder="09171234567",
                  icon="phone", hint="7-15 digits. This is how the customer logs in.")
    phone.pack(fill="x", pady=(0, px(12)))
    email = Field(dlg.body, "Email (optional)", placeholder="name@example.com", icon="mail")
    email.pack(fill="x")

    def submit():
        dlg.clear_error()
        try:
            customer = stack.customers.register(name.get(), phone.get(), email.get())
        except AppError as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(customer)

    dlg.add_button("Register", submit, icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    name.focus()
    dlg.bind("<Return>", lambda e: submit())
    return dlg.show()


def add_vehicle(master, stack, customer):
    dlg = Dialog(master, "Add a vehicle", f"Registering a vehicle for {customer.name}.",
                 icon="car", width=560)
    plate, vtype = _pair(dlg.body, lambda p: Field(p, "Plate number", placeholder="ABC 1234"),
                         lambda p: Select(p, "Vehicle type", config.VEHICLE_TYPES, "sedan"))
    make, model = _pair(dlg.body, lambda p: Field(p, "Make", placeholder="Toyota"),
                        lambda p: Field(p, "Model", placeholder="Vios"))
    year, color = _pair(dlg.body, lambda p: Field(p, "Year", placeholder=str(datetime.now().year - 3)),
                        lambda p: Field(p, "Color", placeholder="White"))
    notes = Field(dlg.body, "Notes (optional)", placeholder="Scratches on rear bumper")
    notes.pack(fill="x")

    def submit():
        dlg.clear_error()
        try:
            vehicle = stack.customers.add_vehicle(customer.id, plate.get(), make.get(), model.get(),
                                                  year.get(), color.get(), vtype.get(), notes.get())
        except AppError as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(vehicle)

    dlg.add_button("Add vehicle", submit, icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    plate.focus()
    return dlg.show()


def checkout(master, stack, appt, staff):
    """Returns (appointment, receipt_path, change) or None."""
    vehicle = stack.customers.vehicle(appt.vehicle_id)
    customer = stack.customers.get(appt.customer_id)
    dlg = Dialog(master, "Checkout", f"{customer.name}  -  {vehicle.describe()}",
                 icon="card", width=560)
    card = Card(dlg.body, pad=16, fill=C.surface_alt, bg=C.surface, border=False, shadow=False)
    card.pack(fill="x", pady=(0, px(16)))
    common.bill_block(card.body, appt, bg=C.surface_alt).pack(fill="x")

    balance = max(appt.price_breakdown.get("total", 0.0) - appt.deposit, 0.0)
    Label(dlg.body, "Payment method", "smallb", "text_muted", bg=C.surface).pack(
        anchor="w", pady=(0, px(6)))
    method = {"value": "cash"}
    cash_box = tk.Frame(dlg.body, bg=C.surface)
    received = Field(cash_box, f"Amount received (balance {money(balance)})", value=f"{balance:.2f}",
                     icon="card")
    received.pack(fill="x")
    change_lbl = Label(cash_box, "", "bodyb", "success", bg=C.surface)
    change_lbl.pack(anchor="w", pady=(px(8), 0))

    def update_change(_v=None):
        try:
            diff = float(received.get() or 0) - balance
            change_lbl.configure(text=f"Change due: {money(diff)}" if diff >= 0
                                 else f"Short by {money(-diff)}",
                                 fg=C.success if diff >= 0 else C.danger)
        except ValueError:
            change_lbl.configure(text="")
    received._on_change = update_change
    update_change()

    def pick(key):
        method["value"] = key
        if key == "cash":
            cash_box.pack(fill="x", pady=(px(14), 0))
        else:
            cash_box.pack_forget()

    labels = {"gcash": "GCash", "bank transfer": "Bank transfer"}
    seg = Segmented(dlg.body, [(m, labels.get(m, m.title())) for m in config.PAYMENT_METHODS], "cash", pick)
    seg.pack(anchor="w")
    cash_box.pack(fill="x", pady=(px(14), 0))

    def submit():
        dlg.clear_error()
        amount = None
        if method["value"] == "cash":
            try:
                amount = float(received.get())
            except ValueError:
                dlg.show_error("Enter the cash amount received as a number.")
                return
        try:
            result = stack.payments.checkout(appt.id, method["value"], amount, staff.name)
        except AppError as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(result)

    dlg.add_button("Confirm payment", submit, "success", icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    return dlg.show()


def receipt(master, path):
    text = path.read_text(encoding="utf-8") if hasattr(path, "read_text") else str(path)
    dlg = Dialog(master, "Official receipt", "Saved to the receipts folder.", icon="receipt",
                 width=620, tone="success")
    box = tk.Frame(dlg.body, bg=C.surface_alt, highlightthickness=1, highlightbackground=C.border)
    box.pack(fill="x")
    widget = tk.Text(box, font=F["mono"], bg=C.surface_alt, fg=C.text, relief="flat", bd=0,
                     height=text.count("\n") + 1, width=56, padx=px(14), pady=px(12),
                     highlightthickness=0, wrap="none")
    widget.insert("1.0", text)
    widget.configure(state="disabled")
    widget.pack()

    def copy():
        dlg.clipboard_clear()
        dlg.clipboard_append(text)
        toast(dlg, "Receipt copied to clipboard", "info")

    dlg.add_button("Close", lambda: dlg.close(True))
    dlg.add_button("Copy text", copy, "secondary")
    dlg.show()


def reschedule(master, stack, appt, allow_walk_in=True):
    """Returns the updated appointment or None."""
    duration = appt.price_breakdown.get("duration_minutes", 60)
    dlg = Dialog(master, "Reschedule", f"Appointment #{appt.id} needs about {duration} minutes in the bay.",
                 icon="clock", width=620)
    picker = DateTimeField(dlg.body, "New date and time", datetime.now())
    picker.pack(anchor="w")
    Label(dlg.body, "Next free slots", "smallb", "text_muted", bg=C.surface).pack(
        anchor="w", pady=(px(18), px(8)))
    chips = tk.Frame(dlg.body, bg=C.surface)
    chips.pack(fill="x")
    slots = stack.bookings.next_slots(duration, 6)
    if not slots:
        Label(chips, "No free slots in the next two weeks. Pick a date and time above.", "body",
              "text_faint", bg=C.surface).pack(anchor="w")
    for i, slot in enumerate(slots):
        label = slot.strftime("%a %b %d  ") + common.pretty_dt(slot.strftime(config.DATETIME_FORMAT)).split(", ")[1]
        Button(chips, label, lambda s=slot: picker.set_datetime(s), "soft", height=34, font="smallb",
               padx=12).grid(row=i // 3, column=i % 3, padx=(0, px(8)), pady=(0, px(8)), sticky="w")
    if allow_walk_in:
        Button(dlg.body, "Start right now", lambda: picker.set_datetime(datetime.now()), "ghost",
               icon="play", height=34, font="smallb").pack(anchor="w", pady=(px(4), 0))

    def submit():
        dlg.clear_error()
        try:
            start = picker.get_datetime()
            updated = stack.bookings.reschedule(appt.id, start)
        except (AppError, ValueError) as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(updated)

    dlg.add_button("Move appointment", submit, icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    return dlg.show()


def restock(master, stack, item):
    dlg = Dialog(master, f"Restock {item.name}",
                 f"Currently {item.stock:g} {item.unit} in stock (reorder at {item.reorder_level:g}).",
                 icon="box", width=460)
    qty = Field(dlg.body, f"Quantity to add ({item.unit})", placeholder="e.g. 10", icon="plus")
    qty.pack(fill="x")

    def submit():
        dlg.clear_error()
        try:
            updated = stack.inventory.restock(item.id, qty.get())
        except AppError as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(updated)

    dlg.add_button("Add stock", submit, icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    qty.focus()
    dlg.bind("<Return>", lambda e: submit())
    return dlg.show()


def add_staff(master, stack):
    dlg = Dialog(master, "Add staff member", "Create a login for a new team member.",
                 icon="user_plus", width=540)
    name, role = _pair(dlg.body, lambda p: Field(p, "Full name", placeholder="e.g. Ana Reyes", icon="user"),
                       lambda p: Select(p, "Role", config.STAFF_ROLES, "detailer"))
    username, password = _pair(dlg.body, lambda p: Field(p, "Username", placeholder="areyes", icon="user"),
                               lambda p: Field(p, "Password", show="*", placeholder="Pick a password",
                                               icon="lock"))
    phone = Field(dlg.body, "Phone number", placeholder="09170000000", icon="phone")
    phone.pack(fill="x")

    def submit():
        dlg.clear_error()
        try:
            member = stack.staff.add(name.get(), role.get(), username.get(), password.get(),
                                     phone.get())
        except AppError as exc:
            dlg.show_error(str(exc))
            return
        dlg.close(member)

    dlg.add_button("Add staff", submit, icon="check")
    dlg.add_button("Cancel", lambda: dlg.close(None), "secondary")
    name.focus()
    return dlg.show()
