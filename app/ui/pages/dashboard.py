"""Staff home: KPIs, today's schedule, utilization, pipeline, revenue, alerts."""
import tkinter as tk
from datetime import datetime, timedelta

from app import config
from app.ui import charts, common
from app.ui.pages.base import FRONT, Page
from app.ui.theme import C, px
from app.ui.widgets import (Button, Card, EmptyState, Label, ScrollFrame, StatCard, Table,
                            Divider, STATUS_LABEL, status_color)
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


class DashboardPage(Page):
    def build(self):
        self.title = f"{common.greeting()}, {self.user.name.split()[0]}"
        self.subtitle = "Here is how the bay looks today."
        today = dtu.today_str()
        bk, reports = self.stack.bookings, self.stack.reports
        todays = bk.schedule_for(today)
        counts = {s: 0 for s in config.ALL_STATUSES}
        for a in todays:
            counts[a.status] += 1
        unpaid = bk.unpaid_completed()
        low = self.stack.inventory.low_stock()
        sales = reports.daily_sales(today)
        show_money = self.role in FRONT
        owed = sum(max(a.price_breakdown.get("total", 0) - a.deposit, 0) for a in unpaid)

        scroll = ScrollFrame(self, bg=C.bg)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        body.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="k")
        active = counts[config.STATUS_BOOKED] + counts[config.STATUS_IN_PROGRESS]
        cards = [
            StatCard(body, "Today's jobs", len(todays),
                     sub=f"{counts[config.STATUS_IN_PROGRESS]} in progress, {counts[config.STATUS_DONE] + counts[config.STATUS_PAID]} finished",
                     icon="calendar", tone="primary"),
            StatCard(body, "Awaiting checkout", len(unpaid),
                     sub=(f"{money(owed)} to collect" if unpaid else "Everything is settled"),
                     icon="receipt", tone="warning"),
        ]
        if show_money:
            cards.append(StatCard(body, "Revenue today", sales["revenue"], fmt=lambda v: money(v),
                                  sub=f"{sales['paid_count']} payment(s) received", icon="chart",
                                  tone="success"))
        else:
            cards.append(StatCard(body, "Still to start", counts[config.STATUS_BOOKED],
                                  sub=f"{active} active on today's board", icon="wrench", tone="success"))
        cards.append(StatCard(body, "Low stock", len(low),
                              sub=(", ".join(i.name for i in low[:2]) if low else "All items healthy"),
                              icon="box", tone="danger" if low else "info",
                              sub_tone="danger" if low else "text_muted"))
        for i, card in enumerate(cards):
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else px(8), 0 if i == 3 else px(8)))

        # ---- schedule + utilization/pipeline
        row2 = tk.Frame(body, bg=C.bg)
        row2.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(px(18), 0))
        row2.grid_columnconfigure(0, weight=3, uniform="r2")
        row2.grid_columnconfigure(1, weight=2, uniform="r2")
        sched = Card(row2, pad=20)
        sched.grid(row=0, column=0, sticky="nsew", padx=(0, px(10)))
        head = tk.Frame(sched.body, bg=C.surface)
        head.pack(fill="x", pady=(0, px(10)))
        Label(head, "Today's schedule", "h3", bg=C.surface).pack(side="left")
        Button(head, "View all", lambda: self.shell.navigate("appointments"), "ghost", height=32,
               font="smallb", bg=C.surface).pack(side="right")
        rows = []
        for a in todays:
            cust = self.stack.customers.get(a.customer_id)
            veh = self.stack.customers.vehicle(a.vehicle_id)
            rows.append((a.id, [("bold", a.scheduled_start[11:]), cust.name,
                                f"{veh.make} {veh.model}", ("status", a.status)], []))
        table = Table(sched.body, [("t", "Time", 80), ("c", "Customer", 150, "w", True),
                                   ("v", "Vehicle", 150, "w", True), ("s", "Status", 150)],
                      height=min(max(len(rows), 3), 5), row_h=48, empty="Nothing scheduled today yet.")
        table.pack(fill="x")
        table.set_rows(rows)
        later = [a for a in bk.upcoming() if not a.scheduled_start.startswith(today)][:4]
        if later:
            Divider(sched.body).pack(fill="x", pady=(px(14), px(10)))
            Label(sched.body, "Coming up", "bodyb", bg=C.surface).pack(anchor="w", pady=(0, px(6)))
            for a in later:
                line = tk.Frame(sched.body, bg=C.surface)
                line.pack(fill="x", pady=px(4))
                Label(line, common.pretty_dt(a.scheduled_start), "smallb", "primary", bg=C.surface,
                      width=16).pack(side="left")
                Label(line, self.stack.customers.get(a.customer_id).name, "body", bg=C.surface).pack(
                    side="left", padx=(px(6), px(12)))
                Label(line, common.services_short(a), "small", "text_muted", bg=C.surface).pack(side="left")

        right = tk.Frame(row2, bg=C.bg)
        right.grid(row=0, column=1, sticky="nsew", padx=(px(10), 0))
        right.grid_rowconfigure((0, 1), weight=1)
        right.grid_columnconfigure(0, weight=1)
        util = reports.utilization(today)
        gcard = Card(right, pad=18)
        gcard.grid(row=0, column=0, sticky="nsew", pady=(0, px(10)))
        Label(gcard.body, "Bay utilization", "h3", bg=C.surface).pack(anchor="w")
        charts.Gauge(gcard.body, util["percent"], size=230, caption="of a 9-hour day").pack(pady=(px(6), 0))
        Label(gcard.body, f"{util['minutes']} booked minutes across {util['jobs']} job(s)", "small",
              "text_muted", bg=C.surface, anchor="center").pack(fill="x")
        pcard = Card(right, pad=18)
        pcard.grid(row=1, column=0, sticky="nsew")
        Label(pcard.body, "Job pipeline", "h3", bg=C.surface).pack(anchor="w")
        allc = {s: len(bk.with_status(s)) for s in config.ALL_STATUSES}
        segs = [(STATUS_LABEL[s], allc[s], status_color(s)) for s in (
            config.STATUS_BOOKED, config.STATUS_IN_PROGRESS, config.STATUS_DONE, config.STATUS_PAID)]
        wrap = tk.Frame(pcard.body, bg=C.surface)
        wrap.pack(fill="x", pady=(px(8), 0))
        charts.Donut(wrap, segs, size=140, center_label="all jobs").pack(side="left")
        legend = tk.Frame(wrap, bg=C.surface)
        legend.pack(side="left", padx=px(18))
        for name, n, color in segs:
            row = tk.Frame(legend, bg=C.surface)
            row.pack(anchor="w", pady=px(3))
            dot = tk.Canvas(row, width=px(12), height=px(12), bg=C.surface, highlightthickness=0)
            dot.create_oval(1, 1, px(11), px(11), fill=color, outline="")
            dot.pack(side="left")
            Label(row, f"{name}  {n}", "body", bg=C.surface).pack(side="left", padx=px(8))

        # ---- revenue chart + top services / low stock
        row3 = tk.Frame(body, bg=C.bg)
        row3.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(px(18), px(8)))
        row3.grid_columnconfigure(0, weight=3, uniform="r3")
        row3.grid_columnconfigure(1, weight=2, uniform="r3")
        left = Card(row3, pad=20)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, px(10)))
        if show_money:
            Label(left.body, "Revenue, last 7 days", "h3", bg=C.surface).pack(anchor="w")
            data = []
            for back in range(6, -1, -1):
                day = datetime.now() - timedelta(days=back)
                data.append((day.strftime("%a"), reports.daily_sales(day.strftime(config.DATE_FORMAT))["revenue"]))
            tk.Frame(left.body, height=px(8), bg=C.surface).pack()
            charts.BarChart(left.body, data, height=240, highlight=6).pack(fill="x")
        else:
            Label(left.body, "Needs attention", "h3", bg=C.surface).pack(anchor="w")
            self._attention(left.body, unpaid, low)
        rcard = Card(row3, pad=20)
        rcard.grid(row=0, column=1, sticky="nsew", padx=(px(10), 0))
        if show_money:
            Label(rcard.body, "Top services", "h3", bg=C.surface).pack(anchor="w")
            top = reports.top_services(4)
            tk.Frame(rcard.body, height=px(10), bg=C.surface).pack()
            charts.HBarList(rcard.body, [(r["service"], r["count"], f"{r['count']}x  {money(r['revenue'])}")
                                         for r in top], empty="No completed jobs yet.").pack(fill="x")
            if low:
                Divider(rcard.body).pack(fill="x", pady=px(14))
                Label(rcard.body, "Low stock", "bodyb", "danger", bg=C.surface).pack(anchor="w")
                for item in low:
                    Label(rcard.body, f"{item.name}: {item.stock:g} {item.unit} left", "small",
                          "text_muted", bg=C.surface).pack(anchor="w", pady=px(2))
        else:
            Label(rcard.body, "Low stock", "h3", bg=C.surface).pack(anchor="w")
            tk.Frame(rcard.body, height=px(10), bg=C.surface).pack()
            if not low:
                Label(rcard.body, "Inventory levels look healthy.", "body", "success", bg=C.surface).pack(anchor="w")
            for item in low:
                Label(rcard.body, f"{item.name}: {item.stock:g} {item.unit} left", "body", "danger",
                      bg=C.surface).pack(anchor="w", pady=px(3))

    def _attention(self, parent, unpaid, low):
        tk.Frame(parent, height=px(10), bg=C.surface).pack()
        items = []
        if unpaid:
            items.append((f"{len(unpaid)} finished job(s) are waiting for checkout.", "warning"))
        items += [(f"Low stock: {i.name} ({i.stock:g} {i.unit} left)", "danger") for i in low]
        if not items:
            Label(parent, "Nothing needs attention. Nice work.", "body", "success", bg=C.surface).pack(anchor="w")
        for text, tone in items:
            Label(parent, text, "body", tone, bg=C.surface).pack(anchor="w", pady=px(4))

    def actions(self):
        acts = []
        if self.role in FRONT:
            acts.append(("New booking", self._new_booking, "primary", "plus"))
        return acts

    def _new_booking(self):
        from app.ui.wizard import BookingWizard
        appt = BookingWizard(self.app, self.stack, staff_mode=True).show()
        if appt:
            self.toast(f"Appointment #{appt.id} booked for {appt.scheduled_start}")
            self.shell.navigate("appointments")
