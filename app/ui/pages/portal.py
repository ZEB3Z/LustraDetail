"""Customer portal pages: home, vehicles and history, profile."""
import tkinter as tk

from app import config
from app.ui import common, dialogs
from app.ui.pages.base import Page
from app.ui.pages.customers import HistoryPanel
from app.ui.theme import C, px
from app.ui.widgets import Button, Card, Divider, EmptyState, IconTile, Label, StatCard, StatusBadge
from app.utils import datetime_utils as dtu
from app.utils.formatting import money


class HomePage(Page):
    def build(self):
        self.title = f"{common.greeting()}, {self.user.name.split()[0]}"
        self.subtitle = "Your car deserves the shine. Book your next visit in a minute."
        mine = self.stack.bookings.for_customer(self.user.id)
        upcoming = [a for a in mine if a.status == config.STATUS_BOOKED and a.start_dt >= dtu.now()]
        finished = [a for a in mine if a.status in (config.STATUS_DONE, config.STATUS_PAID)]
        vehicles = self.stack.customers.vehicles_of(self.user.id)
        row = tk.Frame(self, bg=C.bg)
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="h")
        for i, (title, val, icon, tone, sub) in enumerate((
                ("Upcoming visits", len(upcoming), "calendar", "primary", "booked and waiting"),
                ("Completed jobs", len(finished), "flag", "success", "all time"),
                ("My vehicles", len(vehicles), "car", "info", "on your account"))):
            StatCard(row, title, val, icon=icon, tone=tone, sub=sub).grid(
                row=0, column=i, sticky="nsew", padx=(0 if i == 0 else px(8), 0 if i == 2 else px(8)))
        main = tk.Frame(self, bg=C.bg)
        main.pack(fill="both", expand=True, pady=(px(18), 0))
        main.grid_columnconfigure(0, weight=3, uniform="m")
        main.grid_columnconfigure(1, weight=2, uniform="m")
        nxt = Card(main, pad=24)
        nxt.grid(row=0, column=0, sticky="nsew", padx=(0, px(10)))
        Label(nxt.body, "Next appointment", "h3", bg=C.surface).pack(anchor="w")
        if upcoming:
            a = upcoming[0]
            veh = self.stack.customers.vehicle(a.vehicle_id)
            top = tk.Frame(nxt.body, bg=C.surface)
            top.pack(fill="x", pady=(px(14), px(4)))
            Label(top, common.pretty_dt(a.scheduled_start), "kpi_s", "primary", bg=C.surface).pack(side="left")
            StatusBadge(top, a.status, bg=C.surface).pack(side="right")
            Label(nxt.body, f"{veh.describe()}  -  {common.services_short(a)}", "body", "text_muted",
                  bg=C.surface, wrap=px(480)).pack(anchor="w")
            Label(nxt.body, f"Total {money(a.price_breakdown.get('total', 0))}  -  about "
                  f"{a.price_breakdown.get('duration_minutes', 0)} minutes", "bodyb", bg=C.surface).pack(
                anchor="w", pady=(px(10), px(16)))
            Button(nxt.body, "Manage appointments", lambda: self.shell.navigate("my_appointments"),
                   "secondary", bg=C.surface).pack(anchor="w")
        else:
            EmptyState(nxt.body, "calendar", "No visits booked", "Pick a service and a time that suits you.",
                       bg=C.surface).pack(pady=px(20))
            Button(nxt.body, "Book a service", self.shell.book, icon="plus", bg=C.surface).pack()
        side = Card(main, pad=24)
        side.grid(row=0, column=1, sticky="nsew", padx=(px(10), 0))
        Label(side.body, "Quick actions", "h3", bg=C.surface).pack(anchor="w", pady=(0, px(12)))
        for text, icon, fn, variant in (("Book a service", "plus", self.shell.book, "primary"),
                                        ("See services and prices", "tag", lambda: self.shell.navigate("services"), "secondary"),
                                        ("My vehicles and history", "car", lambda: self.shell.navigate("vehicles"), "secondary")):
            Button(side.body, text, fn, variant, icon=icon, width=300, bg=C.surface).pack(fill="x", pady=px(5))


class VehiclesPage(Page):
    def build(self):
        self.title = "My vehicles"
        self.subtitle = "Your cars and everything we have done to them."
        self.card = Card(self, pad=24)
        self.card.pack(fill="both", expand=True)
        self.refresh()

    def actions(self):
        return [("Add vehicle", self._add, "primary", "plus")]

    def refresh(self):
        body = self.card.body
        for child in body.winfo_children():
            child.destroy()
        HistoryPanel(body, self.stack, self.user).pack(fill="both", expand=True)

    def _add(self):
        vehicle = dialogs.add_vehicle(self.app, self.stack, self.user)
        if vehicle:
            self.refresh()
            self.toast(f"Vehicle {vehicle.plate} added.")


class ProfilePage(Page):
    def build(self):
        self.title = "My profile"
        self.subtitle = "The details we have on file for you."
        card = Card(self, pad=28)
        card.pack(anchor="nw", fill="x")
        top = tk.Frame(card.body, bg=C.surface)
        top.pack(fill="x", pady=(0, px(14)))
        IconTile(top, "user", "primary", size=56).pack(side="left")
        Label(top, self.user.name, "h2", bg=C.surface).pack(side="left", padx=px(16))
        for label, value in (("Phone", self.user.phone), ("Email", self.user.email or "-"),
                             ("Member since", self.user.created_at[:10] or "-"),
                             ("Notes", self.user.notes or "-")):
            Divider(card.body).pack(fill="x")
            row = tk.Frame(card.body, bg=C.surface)
            row.pack(fill="x", pady=px(12))
            Label(row, label, "body", "text_muted", bg=C.surface).pack(side="left")
            Label(row, value, "bodyb", bg=C.surface).pack(side="right")
        Label(card.body, "Need to update your details? Just ask our staff at the shop.", "small",
              "text_faint", bg=C.surface).pack(anchor="w", pady=(px(8), 0))
