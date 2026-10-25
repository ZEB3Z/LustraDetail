"""Inventory: stock levels with visual bars, low-stock flags and restocking."""
import tkinter as tk

from app.ui import dialogs
from app.ui.pages.base import Page
from app.ui.theme import C, F, mix, px
from app.ui.widgets import Badge, Button, Card, Divider, Label, ScrollFrame, Segmented, round_rect


class StockBar(tk.Canvas):
    def __init__(self, parent, ratio, low, marker=0.0):
        super().__init__(parent, height=px(14), bg=C.surface, highlightthickness=0, bd=0)
        self.ratio, self.low, self.marker = max(0.0, min(ratio, 1.0)), low, marker
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        y0, y1 = px(2), h - px(2)
        round_rect(self, 0, y0, w, y1, (y1 - y0) / 2, fill=C.surface_alt, outline="")
        fill_w = max(y1 - y0, w * self.ratio)
        round_rect(self, 0, y0, fill_w, y1, (y1 - y0) / 2, fill=C.danger if self.low else C.primary, outline="")
        if self.marker:
            x = w * self.marker
            self.create_line(x, 0, x, h, fill=C.text_muted, width=2)


class InventoryPage(Page):
    def build(self):
        self.title = "Inventory"
        self.subtitle = "Materials are deducted automatically when a job starts."
        self.only_low = False
        bar = tk.Frame(self, bg=C.bg)
        bar.pack(fill="x", pady=(0, px(14)))
        Segmented(bar, [("all", "All items"), ("low", "Low stock")], "all",
                  lambda k: self._filter(k == "low")).pack(side="left")
        self.card = Card(self, pad=8)
        self.card.pack(fill="both", expand=True)
        self.scroll = ScrollFrame(self.card.body, bg=C.surface, scrollbar="Lustra")
        self.scroll.pack(fill="both", expand=True)
        self.refresh()

    def _filter(self, low):
        self.only_low = low
        self.refresh()

    def refresh(self):
        body = self.scroll.body
        for child in body.winfo_children():
            child.destroy()
        items = self.stack.inventory.low_stock() if self.only_low else self.stack.inventory.all()
        if not items:
            Label(body, "Nothing is below its reorder level.", "body", "success", bg=C.surface).pack(pady=px(40))
        for i, item in enumerate(items):
            if i:
                Divider(body).pack(fill="x", padx=px(14))
            row = tk.Frame(body, bg=C.surface)
            row.pack(fill="x", padx=px(14), pady=px(14))
            row.grid_columnconfigure(0, minsize=px(250))
            row.grid_columnconfigure(1, weight=1)
            info = tk.Frame(row, bg=C.surface, width=px(220))
            info.grid(row=0, column=0, sticky="w")
            Label(info, item.name, "bodyb", bg=C.surface).pack(anchor="w")
            Label(info, f"{item.id}  -  reorder at {item.reorder_level:g} {item.unit}", "small",
                  "text_muted", bg=C.surface).pack(anchor="w")
            mid = tk.Frame(row, bg=C.surface)
            mid.grid(row=0, column=1, sticky="ew", padx=px(24))
            ceiling = max(item.reorder_level * 8, item.stock, 1)
            StockBar(mid, item.stock / ceiling, item.is_low, item.reorder_level / ceiling).pack(
                fill="x", pady=(px(4), px(4)))
            Label(mid, f"{item.stock:g} {item.unit} in stock  (tick = reorder level)", "smallb",
                  "danger" if item.is_low else "text_muted", bg=C.surface).pack(anchor="w")
            Badge(row, "Low" if item.is_low else "OK", "danger" if item.is_low else "success",
                  bg=C.surface).grid(row=0, column=2, padx=px(16))
            if self.role == "admin":
                Button(row, "Restock", lambda it=item: self._restock(it), "soft", icon="plus", height=36,
                       font="smallb", bg=C.surface).grid(row=0, column=3)

    def _restock(self, item):
        updated = dialogs.restock(self.app, self.stack, item)
        if updated:
            self.refresh()
            self.toast(f"{updated.name} restocked to {updated.stock:g} {updated.unit}.")
