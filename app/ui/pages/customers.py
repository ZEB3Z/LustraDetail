"""Staff customer registry with vehicles and per-vehicle service history."""
import tkinter as tk

from app.ui import common, dialogs
from app.ui.pages.base import FRONT, Page
from app.ui.theme import C, px
from app.ui.widgets import Button, Card, Divider, EmptyState, Field, Label, Table
from app.utils.formatting import money


def history_rows(stack, vehicle):
    return [(e.id, [common.pretty_dt(e.completed_at), ", ".join(s["name"] for s in e.services),
                    ("bold", money(e.total_price)),
                    ("badge", "Paid", "success") if e.paid else ("badge", "Unpaid", "warning")], [])
            for e in stack.customers.vehicle_history(vehicle.id)]


class HistoryPanel(tk.Frame):
    """Vehicles of one customer + service history of the selected vehicle."""

    def __init__(self, parent, stack, customer, on_change=None, bg=None):
        super().__init__(parent, bg=bg or C.surface)
        self.stack, self.customer, self.on_change = stack, customer, on_change
        self.vehicles = stack.customers.vehicles_of(customer.id)
        Label(self, "Vehicles", "bodyb", bg=self["bg"]).pack(anchor="w", pady=(0, px(8)))
        self.vtable = Table(self, [("p", "Plate", 100), ("v", "Vehicle", 160, "w", True), ("y", "Year", 70),
                                   ("t", "Type", 100)], height=min(max(len(self.vehicles), 2), 4),
                            row_h=44, on_select=self._pick, empty="No vehicles registered yet.")
        self.vtable.pack(fill="x")
        self.vtable.set_rows([(v.id, [("bold", v.plate), f"{v.make} {v.model}", str(v.year), v.type.title()], [])
                              for v in self.vehicles])
        Label(self, "Service history", "bodyb", bg=self["bg"]).pack(anchor="w", pady=(px(18), px(8)))
        self.htable = Table(self, [("d", "Completed", 140), ("s", "Services", 140, "w", True),
                                   ("t", "Total", 130, "e"), ("p", "Status", 110)], height=3, row_h=44,
                            empty="Select a vehicle to see its history.")
        self.htable.pack(fill="x")
        if len(self.vehicles) == 1:
            self.vtable.select(self.vehicles[0].id)

    def _pick(self, iid):
        vehicle = next((v for v in self.vehicles if str(v.id) == str(iid)), None)
        if vehicle is None:
            self.htable.set_rows([])
            return
        rows = history_rows(self.stack, vehicle)
        self.htable.empty_lbl.configure(text="No service history for this vehicle yet.")
        self.htable.set_rows(rows)


class CustomersPage(Page):
    def build(self):
        self.title = "Customers"
        self.subtitle = "Everyone you have served, with their vehicles and history."
        self.customer = None
        main = tk.Frame(self, bg=C.bg)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=5, uniform="c")
        main.grid_columnconfigure(1, weight=6, uniform="c")
        main.grid_rowconfigure(0, weight=1)
        left = Card(main, pad=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, px(16)))
        self.search = Field(left.body, "", placeholder="Search by name or phone...", icon="search",
                            on_change=lambda v: self.refresh())
        self.search.pack(fill="x", pady=(0, px(12)))
        self.table = Table(left.body, [("n", "Customer", 120, "w", True), ("p", "Phone", 135),
                                       ("v", "Cars", 70, "center")], height=8,
                           on_select=self._pick, empty="No customers match your search.")
        self.table.pack(fill="both", expand=True)
        self.detail = Card(main, pad=22)
        self.detail.grid(row=0, column=1, sticky="nsew")
        self.refresh()

    def actions(self):
        acts = []
        if self.role in FRONT:
            acts.append(("Register customer", self._register, "primary", "user_plus"))
        return acts

    def refresh(self):
        query = self.search.get()
        customers = self.stack.customers.search(query) if query else self.stack.customers.all()
        self.table.set_rows([(c.id, [("bold", c.name), c.phone,
                                     str(len(self.stack.customers.vehicles_of(c.id)))], [])
                             for c in customers])
        self._render(self.table.selected_id())

    def _pick(self, iid):
        self._render(iid)

    def _render(self, iid):
        body = self.detail.body
        for child in body.winfo_children():
            child.destroy()
        customer = self.stack.customers.get(int(iid)) if iid else None
        self.customer = customer
        if customer is None:
            EmptyState(body, "users", "Select a customer",
                       "Their contact details, vehicles and service history appear here.",
                       bg=C.surface).pack(expand=True, pady=px(60))
            return
        top = tk.Frame(body, bg=C.surface)
        top.pack(fill="x")
        Label(top, customer.name, "h2", bg=C.surface).pack(side="left")
        if self.role in FRONT:
            Button(top, "Add vehicle", self._add_vehicle, "soft", icon="plus", height=36, font="smallb",
                   bg=C.surface).pack(side="right")
        for label, value in (("Phone", customer.phone), ("Email", customer.email or "-"),
                             ("Customer since", customer.created_at[:10] or "-")):
            row = tk.Frame(body, bg=C.surface)
            row.pack(fill="x", pady=px(3))
            Label(row, label, "body", "text_muted", bg=C.surface).pack(side="left")
            Label(row, value, "bodyb", bg=C.surface).pack(side="right")
        if customer.notes:
            Label(body, f"Note: {customer.notes}", "small", "text_muted", bg=C.surface, wrap=px(480)).pack(
                anchor="w", pady=(px(6), 0))
        Divider(body).pack(fill="x", pady=px(16))
        HistoryPanel(body, self.stack, customer).pack(fill="both", expand=True)

    def _register(self):
        customer = dialogs.register_customer(self.app, self.stack)
        if customer:
            self.search.set("")
            self.refresh()
            self.table.select(customer.id)
            self.toast(f"{customer.name} registered (ID #{customer.id}).")

    def _add_vehicle(self):
        vehicle = dialogs.add_vehicle(self.app, self.stack, self.customer)
        if vehicle:
            keep = self.customer.id
            self.refresh()
            self.table.select(keep)
            self._render(str(keep))
            self.toast(f"Vehicle {vehicle.plate} added.")
