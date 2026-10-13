"""Reports computed over the seeded demo dataset (dates relative to today)."""
from datetime import timedelta

from app.utils import datetime_utils as dtu


def _yesterday():
    return dtu.fmt_date(dtu.now() - timedelta(days=1))


def test_daily_sales_sees_yesterdays_paid_jobs(stack):
    report = stack.reports.daily_sales(_yesterday())
    # seed: SVC001+SVC002 sedan (1850) and SVC003 pickup (1500), both PAID
    assert report["revenue"] == 3350.0
    assert report["paid_count"] == 2
    assert report["completed_count"] == 2


def test_top_services_ranks_by_count(stack):
    rows = stack.reports.top_services()
    assert rows, "expected services from the demo bookings"
    counts = [r["count"] for r in rows]
    assert counts == sorted(counts, reverse=True)
    names = {r["service"] for r in rows}
    assert "Basic Wash" in names


def test_utilization_counts_booked_minutes(stack):
    tomorrow = dtu.fmt_date(dtu.now() + timedelta(days=1))
    report = stack.reports.utilization(tomorrow)
    # seed tomorrow: SVC006 sedan 240min + SVC009 pickup 75min (+15 add-on)
    assert report["minutes"] == 330
    assert report["jobs"] == 2
    assert report["percent"] > 0


def test_summary_counts(stack):
    s = stack.reports.summary()
    assert s["customers"] == 4
    assert s["vehicles"] == 4
    assert s["upcoming"] >= 3
    assert s["awaiting_payment"] == 1        # today's DONE-but-unpaid job
