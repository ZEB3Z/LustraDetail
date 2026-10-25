"""Reports: daily sales, top services, bay utilization, shop summary."""
import tkinter as tk

from app.ui import charts, common
from app.ui.pages.base import Page
from app.ui.theme import C, px
from app.ui.widgets import Card, DateField, Label, ScrollFrame, Segmented, StatCard, Table
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


class ReportsPage(Page):
    def build(self):
        self.title = "Reports"
        self.subtitle = "Sales, popular services and how busy the bay has been."
        self.tab = "sales"
        bar = tk.Frame(self, bg=C.bg)
        bar.pack(fill="x", pady=(0, px(14)))
        Segmented(bar, [("sales", "Daily sales"), ("top", "Top services"), ("util", "Bay utilization"),
                        ("summary", "Shop summary")], "sales", self._tab).pack(side="left")
        self.date_box = tk.Frame(bar, bg=C.bg)
        self.date_field = DateField(self.date_box, "", dtu.today_str(), on_change=self._date)
        self.date_field.pack()
        self.area = tk.Frame(self, bg=C.bg)
        self.area.pack(fill="both", expand=True)
        self._render()

    def _tab(self, key):
        self.tab = key
        self._render()

    def _date(self, _text):
        try:
            dtu.parse_date(self.date_field.get())
        except ValueError:
            return
        self._render()

    def _render(self):
        for child in self.area.winfo_children():
            child.destroy()
        if self.tab in ("sales", "util"):
            self.date_box.pack(side="right")
        else:
            self.date_box.pack_forget()
        {"sales": self._sales, "top": self._top, "util": self._util, "summary": self._summary}[self.tab]()

    def _day(self):
        try:
            return dtu.fmt_date(dtu.parse_date(self.date_field.get()))
        except ValueError:
            return dtu.today_str()

    def _sales(self):
        r = self.stack.reports.daily_sales(self._day())
        row = tk.Frame(self.area, bg=C.bg)
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="s")
        for i, (title, val, fmt, icon, tone) in enumerate((
                ("Revenue collected", r["revenue"], money, "chart", "success"),
                ("Payments received", r["paid_count"], None, "card", "primary"),
                ("Jobs completed", r["completed_count"], None, "flag", "info"))):
            StatCard(row, title, val, fmt=fmt, icon=icon, tone=tone, sub=r["date"]).grid(
                row=0, column=i, sticky="nsew", padx=(0 if i == 0 else px(8), 0 if i == 2 else px(8)))
        card = Card(self.area, pad=0)
        card.pack(fill="both", expand=True, pady=(px(18), 0))
        table = Table(card.body, [("id", "ID", 60), ("t", "Time", 90), ("c", "Customer", 200, "w", True),
                                  ("m", "Method", 140), ("a", "Amount", 140, "e")], height=6,
                      empty="No payments were collected on that date.")
        table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        rows = []
        for a in r["payments"]:
            cust = self.stack.customers.get(a.customer_id)
            rows.append((a.id, [f"#{a.id}", a.payment.get("paid_at", "")[11:16], ("bold", cust.name),
                                a.payment.get("method", "").title(),
                                ("bold", money(a.price_breakdown.get("total", 0.0)))], []))
        table.set_rows(rows)

    def _top(self):
        top = self.stack.reports.top_services(8)
        card = Card(self.area, pad=26)
        card.pack(fill="x")
        Label(card.body, "Most availed services", "h3", bg=C.surface).pack(anchor="w", pady=(0, px(14)))
        charts.HBarList(card.body, [(r["service"], r["count"], f"{r['count']} job(s)  -  {money(r['revenue'])}")
                                    for r in top], row_h=52, empty="No completed jobs yet.").pack(fill="x")

    def _util(self):
        r = self.stack.reports.utilization(self._day())
        card = Card(self.area, pad=30)
        card.pack(fill="x")
        Label(card.body, f"Bay utilization on {r['date']}", "h3", bg=C.surface).pack(anchor="w")
        charts.Gauge(card.body, r["percent"], size=360, caption="of a 9-hour reference day").pack(pady=px(10))
        Label(card.body, f"{r['minutes']} booked minutes across {r['jobs']} job(s)", "body",
              "text_muted", bg=C.surface, anchor="center").pack(fill="x")
        Label(card.body, "The shop schedules around the clock. The 9-hour day is only a reference.", "small",
              "text_faint", bg=C.surface, anchor="center").pack(fill="x", pady=(px(4), 0))

    def _summary(self):
        s = self.stack.reports.summary()
        row = tk.Frame(self.area, bg=C.bg)
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="s")
        for i, (title, val, icon, tone) in enumerate((
                ("Customers", s["customers"], "users", "primary"), ("Vehicles", s["vehicles"], "car", "info"),
                ("Upcoming jobs", s["upcoming"], "calendar", "success"),
                ("Awaiting payment", s["awaiting_payment"], "receipt", "warning"))):
            StatCard(row, title, val, icon=icon, tone=tone, sub="registered" if i < 2 else "right now").grid(
                row=0, column=i, sticky="nsew", padx=(0 if i == 0 else px(8), 0 if i == 3 else px(8)))
        card = Card(self.area, pad=22)
        card.pack(fill="x", pady=(px(18), 0))
        Label(card.body, "Inventory health", "h3", bg=C.surface).pack(anchor="w")
        if s["low_stock"]:
            for item in s["low_stock"]:
                Label(card.body, f"{item.name}: {item.stock:g} {item.unit} left", "body", "danger",
                      bg=C.surface).pack(anchor="w", pady=px(3))
        else:
            Label(card.body, "All inventory items are above their reorder levels.", "body", "success",
                  bg=C.surface).pack(anchor="w", pady=(px(6), 0))
