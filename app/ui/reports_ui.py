"""Report screens: daily sales, top services, utilization, summary."""
from app.ui import appt_view, terminal as t
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


def daily_sales(stack):
    date = t.ask_date("Sales for which date", default_today=True)
    report = stack.reports.daily_sales(date)
    t.header(f"DAILY SALES - {report['date']}")
    print(f"  Revenue collected : {money(report['revenue'])}")
    print(f"  Payments received : {report['paid_count']}")
    print(f"  Jobs completed    : {report['completed_count']}")
    if report["payments"]:
        rows = []
        for appt in report["payments"]:
            customer = stack.customers.get(appt.customer_id)
            rows.append([appt.id, appt.payment.get("paid_at", "")[11:16],
                         customer.name, appt.payment.get("method", ""),
                         money(appt.price_breakdown.get("total", 0.0))])
        t.show_table(["ID", "Time", "Customer", "Method", "Amount"], rows,
                     aligns=[">", "<", "<", "<", ">"])
    else:
        t.warn("No payments were collected on that date.")
    t.pause()


def top_services(stack):
    rows = [[r["service"], r["count"], money(r["revenue"])]
            for r in stack.reports.top_services()]
    t.header("TOP SERVICES")
    t.show_table(["Service", "Times availed", "Revenue"], rows,
                 aligns=["<", ">", ">"], empty="No completed jobs yet.")
    t.pause()


def utilization(stack):
    date = t.ask_date("Utilization for which date", default_today=True)
    report = stack.reports.utilization(date)
    t.header(f"BAY UTILIZATION - {report['date']}")
    bar = "#" * min(40, max(0, round(report["percent"] / 2.5)))
    print(f"  [{bar:<40}] {report['percent']}%")
    print(f"  {report['minutes']} booked minutes across {report['jobs']} job(s).")
    t.info("Assumes a 9-hour reference workday; the shop itself schedules around the clock.")
    t.pause()


def summary(stack):
    s = stack.reports.summary()
    t.header("SHOP SUMMARY")
    print(f"  Registered customers : {s['customers']}")
    print(f"  Registered vehicles : {s['vehicles']}")
    print(f"  Upcoming jobs       : {s['upcoming']}")
    print(f"  Awaiting payment    : {s['awaiting_payment']}")
    if s["low_stock"]:
        t.warn("Low stock: " + ", ".join(
            f"{i.name} ({i.stock:g} {i.unit} left)" for i in s["low_stock"]))
    else:
        t.success("All inventory items are above their reorder levels.")
    t.pause()


def browse(stack):
    t.menu("REPORTS", [
        ("Daily sales", lambda: daily_sales(stack)),
        ("Top services", lambda: top_services(stack)),
        ("Bay utilization", lambda: utilization(stack)),
        ("Shop summary", lambda: summary(stack)),
    ])
