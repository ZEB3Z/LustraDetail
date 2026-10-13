"""Catalog browsing screens, shared by staff and the customer portal."""
from app import config
from app.ui import terminal as t
from app.utils.formatting import make_table, money


def service_matrix(stack):
    services = stack.catalog.services()
    rows = []
    for svc in services:
        rows.append([svc.name] + [f"{svc.prices.get(vt, '-'):,.0f}" for vt in config.VEHICLE_TYPES])
    print()
    print(make_table(["Service (Php)"] + config.VEHICLE_TYPES, rows,
                     aligns=["<"] + [">"] * len(config.VEHICLE_TYPES)))
    t.info("Durations in minutes:")
    rows = []
    for svc in services:
        rows.append([svc.name] + [str(svc.durations.get(vt, "-")) for vt in config.VEHICLE_TYPES])
    print(make_table(["Service (min)"] + config.VEHICLE_TYPES, rows,
                     aligns=["<"] + [">"] * len(config.VEHICLE_TYPES)))


def add_ons(stack):
    rows = [[a.name, money(a.price), f"{a.duration} min"] for a in stack.catalog.add_ons()]
    t.show_table(["Add-on", "Price", "Extra time"], rows, aligns=["<", ">", ">"],
                 empty="No add-ons in the catalog.")


def packages(stack):
    rows = []
    for pkg in stack.catalog.packages():
        names = []
        for sid in pkg.service_ids:
            try:
                names.append(stack.catalog.get_service(sid).name)
            except Exception:
                names.append(sid)
        rows.append([pkg.name, ", ".join(names), f"{pkg.discount_percent:g}%", pkg.description])
    t.show_table(["Package", "Includes", "Discount", "Description"], rows,
                 empty="No packages in the catalog.")


def promos(stack):
    rows = [[p.code, f"{p.discount_percent:g}%", p.description] for p in stack.catalog.promos()]
    t.show_table(["Promo code", "Discount", "Description"], rows,
                 aligns=["<", ">", "<"], empty="No active promos.")


def browse(stack):
    t.menu("SERVICE CATALOG", [
        ("Services - price & duration matrix", lambda: service_matrix(stack)),
        ("Add-ons", lambda: add_ons(stack)),
        ("Packages & bundles", lambda: packages(stack)),
        ("Promo codes", lambda: promos(stack)),
    ])
