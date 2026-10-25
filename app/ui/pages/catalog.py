"""Service catalog: price/duration matrix, add-ons, packages and promo codes."""
import tkinter as tk

from app import config
from app.ui.pages.base import Page
from app.ui.theme import C, px
from app.ui.widgets import Card, IconTile, Label, ScrollFrame, Segmented, Table
from app.utils.formatting import money


class CatalogPage(Page):
    def build(self):
        self.title = "Service catalog"
        self.subtitle = "Prices and timing for every vehicle type."
        self.tab, self.unit = "services", "price"
        bar = tk.Frame(self, bg=C.bg)
        bar.pack(fill="x", pady=(0, px(14)))
        Segmented(bar, [("services", "Services"), ("addons", "Add-ons"), ("packages", "Packages"),
                        ("promos", "Promo codes")], "services", self._tab).pack(side="left")
        self.unit_seg = Segmented(bar, [("price", "Price"), ("time", "Duration")], "price", self._unit,
                                  height=38)
        self.unit_seg.pack(side="right")
        self.area = tk.Frame(self, bg=C.bg)
        self.area.pack(fill="both", expand=True)
        self._render()

    def _tab(self, key):
        self.tab = key
        self._render()

    def _unit(self, key):
        self.unit = key
        self._render()

    def _render(self):
        for child in self.area.winfo_children():
            child.destroy()
        if self.tab == "services":
            self.unit_seg.pack(side="right")
            self._services()
        else:
            self.unit_seg.pack_forget()
            {"addons": self._addons, "packages": self._packages, "promos": self._promos}[self.tab]()

    def _services(self):
        card = Card(self.area, pad=0)
        card.pack(fill="both", expand=True)
        cols = [("n", "Service", 220, "w", True)] + [(vt, vt.title(), 125, "e") for vt in config.VEHICLE_TYPES]
        table = Table(card.body, cols, height=9, row_h=54)
        table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        rows = []
        for s in self.stack.catalog.services():
            if self.unit == "price":
                cells = [("bold", s.name)] + [f"Php {s.prices.get(v, 0):,.0f}" for v in config.VEHICLE_TYPES]
            else:
                cells = [("bold", s.name)] + [f"{s.durations.get(v, '-')} min" for v in config.VEHICLE_TYPES]
            rows.append((s.id, cells, []))
        table.set_rows(rows)

    def _grid(self, items, empty):
        scroll = ScrollFrame(self.area, bg=C.bg)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        body.grid_columnconfigure((0, 1, 2), weight=1, uniform="g")
        if not items:
            Label(body, empty, "body", "text_faint").grid(row=0, column=0, pady=px(40))
        for i, (icon, tone, title, big, desc, foot) in enumerate(items):
            card = Card(body, pad=20)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=px(8), pady=px(8))
            top = tk.Frame(card.body, bg=C.surface)
            top.pack(fill="x")
            IconTile(top, icon, tone, size=44).pack(side="left")
            Label(top, big, "kpi_s", tone, bg=C.surface).pack(side="right")
            Label(card.body, title, "h3", bg=C.surface).pack(anchor="w", pady=(px(14), px(2)))
            Label(card.body, desc, "body", "text_muted", bg=C.surface, wrap=px(250)).pack(anchor="w")
            if foot:
                Label(card.body, foot, "smallb", "text_faint", bg=C.surface, wrap=px(250)).pack(
                    anchor="w", pady=(px(10), 0))

    def _addons(self):
        items = [("plus", "primary", a.name, money(a.price), "Optional extra for any booking.",
                  f"Adds {a.duration} minutes") for a in self.stack.catalog.add_ons()]
        self._grid(items, "No add-ons in the catalog.")

    def _packages(self):
        items = []
        for p in self.stack.catalog.packages():
            names = []
            for sid in p.service_ids:
                try:
                    names.append(self.stack.catalog.get_service(sid).name)
                except Exception:
                    names.append(sid)
            items.append(("tag", "success", p.name, f"{p.discount_percent:g}% off", p.description,
                          "Includes: " + ", ".join(names)))
        self._grid(items, "No packages in the catalog.")

    def _promos(self):
        items = [("sparkle", "warning", p.code, f"{p.discount_percent:g}% off", p.description,
                  "Enter at booking") for p in self.stack.catalog.promos()]
        self._grid(items, "No active promos.")
