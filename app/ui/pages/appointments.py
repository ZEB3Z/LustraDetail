"""Appointments: filterable list on the left, detail + actions on the right.

Staff see the whole shop (actions depend on role); customers see only
their own bookings (MyAppointmentsPage) and may cancel or reschedule
future ones.
"""
import tkinter as tk
from datetime import datetime, timedelta

from app import config
from app.ui import common, dialogs
from app.ui.pages.base import BAY, FRONT, Page
from app.ui.theme import C, px
from app.ui.widgets import (Button, Card, DateField, Divider, EmptyState, Label, Segmented,
                            StatusBadge, Table, confirm)
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


class AppointmentsPage(Page):
    customer_mode = False
    default_mode = "day"

    def build(self):
        self.title = "Appointments"
        self.subtitle = "Every booking, from first call to final receipt."
        self.mode = self.default_mode
        self.date = dtu.today_str()
        self.shown = []
        top = tk.Frame(self, bg=C.bg)
        top.pack(fill="x", pady=(0, px(14)))
        self.seg = Segmented(top, self._modes(), self.mode, self._set_mode)
        self.seg.pack(side="left")
        self.date_box = tk.Frame(top, bg=C.bg)
        Button(self.date_box, "", lambda: self._shift(-1), "secondary", icon="chevron_left",
               width=40, height=40).pack(side="left")
        self.date_field = DateField(self.date_box, "", self.date, on_change=self._date_typed)
        self.date_field.pack(side="left", padx=px(8))
        Button(self.date_box, "", lambda: self._shift(1), "secondary", icon="chevron_right",
               width=40, height=40).pack(side="left")
        Button(self.date_box, "Today", self._today, "ghost", height=40).pack(side="left", padx=px(6))
        self.count_lbl = Label(top, "", "smallb", "text_faint")
        self.count_lbl.pack(side="right")

        main = tk.Frame(self, bg=C.bg)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)
        main.grid_rowconfigure(0, weight=1)
        card = Card(main, pad=0)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, px(16)))
        self.table = Table(card.body, [("w", "When", 146), ("c", "Customer", 110, "w", 3),
                                       ("s", "Services", 100, "w", 2), ("st", "Status", 130),
                                       ("t", "Total", 118, "e")],
                           on_select=self._selected, height=8, empty="No appointments here.")
        self.table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        if self.customer_mode:
            self.table.columns[1] = ("c", "Vehicle", 110, "w", 3)
            self.table._draw_head()
        holder = tk.Frame(main, bg=C.bg, width=px(340))
        holder.grid(row=0, column=1, sticky="nsew")
        holder.pack_propagate(False)
        self.detail = Card(holder, pad=22)
        self.detail.pack(fill="both", expand=True)
        self._set_mode(self.mode)

    # ---- modes / data
    def _modes(self):
        return [("day", "By date"), ("upcoming", "Upcoming"), ("active", "In progress"),
                ("checkout", "Checkout"), ("all", "All")]

    def _set_mode(self, key):
        self.mode = key
        if key == "day":
            self.date_box.pack(side="left", padx=(px(16), 0))
        else:
            self.date_box.pack_forget()
        self.refresh()

    def _date_typed(self, text):
        try:
            self.date = dtu.fmt_date(dtu.parse_date(text))
        except ValueError:
            return
        self.refresh()

    def _shift(self, days):
        try:
            current = dtu.parse_date(self.date_field.get())
        except ValueError:
            current = datetime.now()
        self.date = dtu.fmt_date(current + timedelta(days=days))
        self.date_field.set(self.date)
        self.refresh()

    def _today(self):
        self.date = dtu.today_str()
        self.date_field.set(self.date)
        self.refresh()

    def _load(self):
        bk = self.stack.bookings
        if self.mode == "day":
            return bk.schedule_for(self.date)
        if self.mode == "upcoming":
            return bk.upcoming()
        if self.mode == "active":
            return bk.with_status(config.STATUS_IN_PROGRESS)
        if self.mode == "checkout":
            return bk.unpaid_completed()
        return sorted(bk.appointments.all(), key=lambda a: a.scheduled_start, reverse=True)

    def refresh(self):
        self.shown = self._load()
        self.table.set_rows([(a.id, common.appt_cells(self.stack, a, self.customer_mode), []) for a in self.shown])
        n = len(self.shown)
        self.count_lbl.configure(text=f"{n} appointment{'s' if n != 1 else ''}")
        self._render_detail(self.table.selected_id())
        self.shell.refresh_badges()

    def _selected(self, iid):
        self._render_detail(iid)

    # ---- detail panel
    def _get(self, iid):
        return next((a for a in self.shown if str(a.id) == str(iid)), None) if iid else None

    def _render_detail(self, iid):
        body = self.detail.body
        for child in body.winfo_children():
            child.destroy()
        appt = self._get(iid)
        if appt is None:
            EmptyState(body, "calendar", "Select an appointment",
                       "Pick a row to see its details and the actions available to you.",
                       bg=C.surface, wrap=240).pack(expand=True, pady=px(40))
            return
        stack = self.stack
        customer, vehicle = stack.customers.get(appt.customer_id), stack.customers.vehicle(appt.vehicle_id)
        top = tk.Frame(body, bg=C.surface)
        top.pack(fill="x")
        Label(top, f"Appointment #{appt.id}", "h3", bg=C.surface).pack(side="left")
        StatusBadge(top, appt.status, bg=C.surface).pack(side="right")
        for label, value in (("Customer", customer.name), ("Vehicle", vehicle.describe()),
                             ("Starts", common.pretty_dt(appt.scheduled_start)),
                             ("Ends", common.pretty_dt(appt.scheduled_end))):
            row = tk.Frame(body, bg=C.surface)
            row.pack(fill="x", pady=px(4))
            Label(row, label, "body", "text_muted", bg=C.surface).pack(side="left")
            Label(row, value, "bodyb", bg=C.surface, wrap=px(220), justify="right",
                  anchor="e").pack(side="right")
        Divider(body).pack(fill="x", pady=px(12))
        common.bill_block(body, appt).pack(fill="x")
        if appt.notes:
            Label(body, f"Note: {appt.notes}", "small", "text_muted", bg=C.surface,
                  wrap=px(310)).pack(anchor="w", pady=(px(8), 0))
        acts = tk.Frame(body, bg=C.surface)
        acts.pack(fill="x", pady=(px(16), 0))
        for text, fn, variant, icon in self._actions_for(appt):
            Button(acts, text, lambda f=fn, a=appt: f(a), variant, icon=icon, width=280,
                   bg=C.surface).pack(fill="x", pady=px(4))

    def _actions_for(self, appt):
        out = []
        st, role = appt.status, self.role
        if self.customer_mode:
            if st == config.STATUS_BOOKED and appt.start_dt >= dtu.now():
                out.append(("Reschedule", self._reschedule, "secondary", "clock"))
                out.append(("Cancel appointment", self._cancel, "danger_soft", "ban"))
            return out
        if st == config.STATUS_BOOKED:
            if role in BAY:
                out.append(("Start job", self._start, "primary", "play"))
            if role in FRONT:
                out.append(("Reschedule", self._reschedule, "secondary", "clock"))
                if appt.start_dt < dtu.now():
                    out.append(("Mark as no-show", self._no_show, "secondary", "alert"))
                out.append(("Cancel appointment", self._cancel, "danger_soft", "ban"))
        elif st == config.STATUS_IN_PROGRESS and role in BAY:
            out.append(("Complete job", self._complete, "success", "flag"))
        elif st == config.STATUS_DONE and role in FRONT:
            out.append(("Checkout and receipt", self._checkout, "primary", "card"))
        elif st == config.STATUS_PAID and appt.payment.get("receipt_file"):
            out.append(("View receipt", self._view_receipt, "secondary", "receipt"))
        return out

    # ---- actions
    def _done(self, message):
        self.toast(message)
        self.refresh()

    def _start(self, appt):
        if confirm(self.app, "Start this job?",
                   f"Appointment #{appt.id} moves to IN PROGRESS and its materials are "
                   "deducted from inventory.", ok="Start job"):
            ok, _ = self.attempt(self.stack.bookings.start_job, appt.id)
            if ok:
                self._done(f"Job #{appt.id} started. Materials deducted from stock.")

    def _complete(self, appt):
        if confirm(self.app, "Complete this job?",
                   f"Mark appointment #{appt.id} as DONE. A service history entry will be recorded.",
                   ok="Mark as done"):
            ok, _ = self.attempt(self.stack.bookings.complete_job, appt.id)
            if ok:
                self._done(f"Job #{appt.id} is done. Ready for checkout.")

    def _cancel(self, appt):
        if confirm(self.app, "Cancel appointment?",
                   f"Appointment #{appt.id} on {common.pretty_dt(appt.scheduled_start)} will be "
                   "cancelled and the slot freed.", ok="Cancel appointment", danger=True, icon="ban"):
            ok, _ = self.attempt(self.stack.bookings.cancel, appt.id)
            if ok:
                self._done(f"Appointment #{appt.id} cancelled.")

    def _no_show(self, appt):
        if confirm(self.app, "Mark as no-show?", f"Appointment #{appt.id} will be recorded as a no-show.",
                   ok="Mark no-show", danger=True):
            ok, _ = self.attempt(self.stack.bookings.mark_no_show, appt.id)
            if ok:
                self._done(f"Appointment #{appt.id} marked as a no-show.")

    def _reschedule(self, appt):
        updated = dialogs.reschedule(self.app, self.stack, appt, allow_walk_in=not self.customer_mode)
        if updated:
            self._done(f"Moved to {common.pretty_dt(updated.scheduled_start)}.")

    def _checkout(self, appt):
        result = dialogs.checkout(self.app, self.stack, appt, self.user)
        if result:
            paid, path, change = result
            self.refresh()
            self.toast(f"Appointment #{paid.id} paid" + (f". Change due: {money(change)}" if change else ""))
            dialogs.receipt(self.app, path)

    def _view_receipt(self, appt):
        path = config.receipts_dir() / appt.payment["receipt_file"]
        if path.exists():
            dialogs.receipt(self.app, path)
        else:
            self.toast("The receipt file is no longer on disk.", "warning")

    def actions(self):
        if self.customer_mode:
            return [("Book a service", self.shell.book, "primary", "plus")]
        acts = []
        if self.role in FRONT:
            acts.append(("Walk-in", lambda: self._book(True), "secondary", "play"))
            acts.append(("New booking", lambda: self._book(False), "primary", "plus"))
        return acts

    def _book(self, walk_in):
        from app.ui.wizard import BookingWizard
        appt = BookingWizard(self.app, self.stack, staff_mode=True, walk_in=walk_in).show()
        if appt:
            self.mode = "day"
            self.seg.select("day", fire=False)
            self.date = appt.scheduled_start[:10]
            self.date_field.set(self.date)
            self._set_mode("day")
            self.table.select(appt.id)
            self.toast(f"Appointment #{appt.id} booked for {common.pretty_dt(appt.scheduled_start)}")


class MyAppointmentsPage(AppointmentsPage):
    customer_mode = True
    default_mode = "upcoming"

    def build(self):
        super().build()
        self.title = "My appointments"
        self.subtitle = "View, move or cancel your upcoming visits."

    def _modes(self):
        return [("upcoming", "Upcoming"), ("all", "All visits")]

    def _load(self):
        mine = self.stack.bookings.for_customer(self.user.id)
        if self.mode == "upcoming":
            return [a for a in mine if a.status in (config.STATUS_BOOKED, config.STATUS_IN_PROGRESS)
                    and a.start_dt >= dtu.now() - timedelta(hours=12)]
        return sorted(mine, key=lambda a: a.scheduled_start, reverse=True)
