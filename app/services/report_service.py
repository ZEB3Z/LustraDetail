"""Reports: daily sales, top services, bay utilization, shop summary."""
from app import config
from app.utils import datetime_utils as dtu


class ReportService:
    def __init__(self, appointment_repo, customer_repo, vehicle_repo, inventory_service):
        self.appointments = appointment_repo
        self.customers = customer_repo
        self.vehicles = vehicle_repo
        self.inventory = inventory_service

    def daily_sales(self, date_str):
        """Payments collected on a given 'YYYY-MM-DD'."""
        date = dtu.fmt_date(dtu.parse_date(date_str))
        payments = []
        revenue = 0.0
        for appt in self.appointments.all():
            if (appt.status == config.STATUS_PAID
                    and appt.payment.get("paid_at", "").startswith(date)):
                payments.append(appt)
                revenue += float(appt.price_breakdown.get("total", 0.0))
        completed = [a for a in self.appointments.all()
                     if a.completed_at.startswith(date)
                     and a.status in (config.STATUS_DONE, config.STATUS_PAID)]
        payments.sort(key=lambda a: a.payment.get("paid_at", ""))
        return {
            "date": date,
            "revenue": round(revenue, 2),
            "paid_count": len(payments),
            "completed_count": len(completed),
            "payments": payments,
        }

    def top_services(self, limit=5):
        counts, revenue = {}, {}
        for appt in self.appointments.all():
            if appt.status not in (config.STATUS_DONE, config.STATUS_PAID):
                continue
            for item in appt.price_breakdown.get("items", []):
                if item.get("kind") != "service":
                    continue
                counts[item["name"]] = counts.get(item["name"], 0) + 1
                revenue[item["name"]] = revenue.get(item["name"], 0.0) + float(item["price"])
        rows = [{"service": name, "count": counts[name], "revenue": round(revenue[name], 2)}
                for name in sorted(counts, key=counts.get, reverse=True)]
        return rows[:limit]

    def utilization(self, date_str):
        """How busy the single bay was on a given day.

        Assumes a 9-hour workday (config.WORKDAY_MINUTES) purely as a
        reference point - the shop itself schedules around the clock.
        """
        date = dtu.fmt_date(dtu.parse_date(date_str))
        minutes, jobs = 0, 0
        for appt in self.appointments.all():
            if (appt.scheduled_start.startswith(date)
                    and appt.status not in (config.STATUS_CANCELLED, config.STATUS_NO_SHOW)):
                minutes += int(appt.price_breakdown.get("duration_minutes", 0))
                jobs += 1
        percent = round(minutes / config.WORKDAY_MINUTES * 100, 1)
        return {"date": date, "minutes": minutes, "jobs": jobs, "percent": percent}

    def summary(self):
        upcoming = [a for a in self.appointments.all()
                    if a.status in (config.STATUS_BOOKED, config.STATUS_IN_PROGRESS)]
        return {
            "customers": len(self.customers.all()),
            "vehicles": len(self.vehicles.all()),
            "upcoming": len(upcoming),
            "awaiting_payment": len([a for a in self.appointments.all()
                                    if a.status == config.STATUS_DONE]),
            "low_stock": self.inventory.low_stock(),
        }
