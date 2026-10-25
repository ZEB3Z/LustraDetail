"""Shared helpers for screens: formatting, appointment rows, bill block."""
import tkinter as tk
from datetime import datetime

from app import config
from app.ui.theme import C, px
from app.ui.widgets import Label, Divider
from app.utils.formatting import money

__all__ = ["money", "pretty_dt", "services_short", "appt_cells", "bill_block", "greeting"]


def pretty_dt(text):
    """'2026-10-24 13:00' -> 'Oct 24, 1:00 PM'."""
    try:
        dt = datetime.strptime(text, config.DATETIME_FORMAT)
    except (ValueError, TypeError):
        return text or "-"
    hour = dt.hour % 12 or 12
    return f"{dt.strftime('%b')} {dt.day}, {hour}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def greeting():
    hour = datetime.now().hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"


def services_short(appt):
    names = [i["name"] for i in appt.price_breakdown.get("items", [])]
    text = ", ".join(names[:2])
    if len(names) > 2:
        text += f" +{len(names) - 2}"
    return text or "-"


def appt_cells(stack, appt, customer_mode=False):
    if customer_mode:
        v = stack.customers.vehicle(appt.vehicle_id)
        who = f"{v.make} {v.model}"
    else:
        who = stack.customers.get(appt.customer_id).name
    return [
        ("bold", pretty_dt(appt.scheduled_start)),
        who,
        services_short(appt),
        ("status", appt.status),
        ("bold", money(appt.price_breakdown.get("total", 0.0))),
    ]


def bill_block(parent, appt, bg=None):
    """Itemised price lines for an appointment (used in dialogs and panels)."""
    bg = bg or C.surface
    box = tk.Frame(parent, bg=bg)
    b = appt.price_breakdown

    def line(label, value, bold=False, tone="text", muted=False):
        row = tk.Frame(box, bg=bg)
        row.pack(fill="x", pady=px(3))
        Label(row, label, "bodyb" if bold else "body", "text_muted" if muted else tone,
              bg=bg).pack(side="left")
        Label(row, value, "bodyb" if bold else "body", tone, bg=bg).pack(side="right")

    for item in b.get("items", []):
        line(item["name"], money(item["price"]))
    Divider(box).pack(fill="x", pady=px(6))
    line("Subtotal", money(b.get("subtotal", 0.0)), muted=True)
    if b.get("package_discount_amount"):
        line("Package discount", "-" + money(b["package_discount_amount"]), tone="success")
    if b.get("promo_discount_amount"):
        line(f"Promo {b.get('promo_code', '')}", "-" + money(b["promo_discount_amount"]),
             tone="success")
    line("Total", money(b.get("total", 0.0)), bold=True)
    if appt.deposit:
        line("Deposit paid", "-" + money(appt.deposit), tone="success")
        line("Balance due", money(max(b.get("total", 0.0) - appt.deposit, 0.0)), bold=True,
             tone="primary")
    return box
