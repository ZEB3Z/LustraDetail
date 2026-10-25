"""Booking wizard: customer > vehicle > services > schedule > review.

One wizard serves staff (customer picker, deposits, notes, walk-ins) and
the customer portal (customer fixed, no deposit). A live quote panel on
the right updates as choices change.
"""
import tkinter as tk
from datetime import datetime

from app import config
from app.exceptions import AppError, BookingError, InventoryError
from app.ui import common, dialogs
from app.ui.theme import C, F, mix, px
from app.ui.widgets import (Button, Card, DateTimeField, Divider, EmptyState, Field, Label,
                            ScrollFrame, Segmented, Table, TextArea, round_rect, icons, toast)
from app.utils.formatting import money


class ChoiceTile(tk.Canvas):
    """Selectable card (checkbox or radio look)."""

    def __init__(self, parent, title, desc="", right="", sub="", selected=False, radio=False,
                 command=None, height=76):
        super().__init__(parent, height=px(height), bg=parent["bg"], highlightthickness=0, bd=0,
                         cursor="hand2")
        self.title, self.desc, self.right, self.sub = title, desc, right, sub
        self.selected, self.radio, self.command = selected, radio, command
        self._hover = False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self.command and self.command())

    def _set_hover(self, value):
        self._hover = value
        self.draw()

    def set_selected(self, value):
        self.selected = value
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        fill = C.primary_soft if self.selected else (C.surface_alt if self._hover else C.surface)
        outline = C.primary if self.selected else C.border_strong
        round_rect(self, 1, 1, w - 2, h - 2, px(12), fill=fill, outline=outline,
                   width=2 if self.selected else 1)
        cx, cy, r = px(26), h / 2, px(10)
        if self.selected:
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=C.primary, outline="")
            icons.draw(self, "check", cx - px(6), cy - px(6), px(12), C.on_primary, width=2)
        else:
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C.border_strong, width=2)
        tx = px(50)
        right_w = max(F["bodyb"].measure(self.right), F["small"].measure(self.sub)) + px(24)
        avail = w - tx - right_w
        title = _clip(F["bodyb"], self.title, avail)
        if self.desc:
            self.create_text(tx, h / 2 - px(10), text=title, font=F["bodyb"], fill=C.text, anchor="w")
            self.create_text(tx, h / 2 + px(11), text=_clip(F["small"], self.desc, avail),
                             font=F["small"], fill=C.text_muted, anchor="w")
        else:
            self.create_text(tx, h / 2, text=title, font=F["bodyb"], fill=C.text, anchor="w")
        self.create_text(w - px(18), h / 2 - (px(9) if self.sub else 0), text=self.right,
                         font=F["bodyb"], fill=C.primary if self.selected else C.text, anchor="e")
        if self.sub:
            self.create_text(w - px(18), h / 2 + px(11), text=self.sub, font=F["small"],
                             fill=C.text_muted, anchor="e")


def _clip(font, text, width):
    if width <= 0 or font.measure(text) <= width:
        return text
    while text and font.measure(text + "...") > width:
        text = text[:-1]
    return text + "..."


class BookingWizard(tk.Toplevel):
    def __init__(self, master, stack, customer=None, staff_mode=False, walk_in=False):
        super().__init__(master)
        self.stack, self.staff_mode, self.walk_in = stack, staff_mode, walk_in
        self.master_win = master.winfo_toplevel()
        self.result = None
        self.customer, self.vehicle = customer, None
        self.service_ids, self.package_id, self.add_on_ids = [], "", []
        self.promo, self.start = "", None
        self.deposit, self.notes = "0", ""
        self.quote = None
        self.title("New walk-in" if walk_in else "New booking")
        self.configure(bg=C.bg)
        self.transient(self.master_win)

        self.steps = []
        if staff_mode:
            self.steps.append(("customer", "Customer"))
        self.steps.append(("vehicle", "Vehicle"))
        self.steps.append(("services", "Services"))
        if not walk_in:
            self.steps.append(("schedule", "Schedule"))
        self.steps.append(("review", "Review"))
        self.index = 0

        self._build_chrome()
        self._go(0)
        w, h = min(px(1120), self.winfo_screenwidth() - px(60)), min(px(740), self.winfo_screenheight() - px(80))
        m = self.master_win
        x = m.winfo_rootx() + (m.winfo_width() - w) // 2
        y = m.winfo_rooty() + (m.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        self.minsize(px(980), px(640))
        self.bind("<Escape>", lambda e: self.destroy())

    # ------------------------------------------------------------- chrome ---
    def _build_chrome(self):
        head = tk.Frame(self, bg=C.surface)
        head.pack(fill="x")
        inner = tk.Frame(head, bg=C.surface)
        inner.pack(fill="x", padx=px(28), pady=px(18))
        Label(inner, "Walk-in booking" if self.walk_in else "New booking", "h2", bg=C.surface).pack(
            side="left")
        self.stepper = tk.Canvas(inner, height=px(40), bg=C.surface, highlightthickness=0)
        self.stepper.pack(side="right", fill="x", expand=True, padx=(px(40), 0))
        self.stepper.bind("<Configure>", lambda e: self._draw_stepper())
        Divider(self).pack(fill="x")

        foot = tk.Frame(self, bg=C.surface)
        foot.pack(side="bottom", fill="x")
        Divider(foot).pack(fill="x")
        bar = tk.Frame(foot, bg=C.surface)
        bar.pack(fill="x", padx=px(28), pady=px(14))
        self.next_btn = Button(bar, "Continue", self._next, icon=None, bg=C.surface)
        self.next_btn.pack(side="right")
        self.back_btn = Button(bar, "Back", self._back, "secondary", bg=C.surface)
        self.back_btn.pack(side="right", padx=(0, px(10)))
        Button(bar, "Cancel", self.destroy, "ghost", bg=C.surface).pack(side="left")

        main = tk.Frame(self, bg=C.bg)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0, minsize=px(340))
        main.grid_rowconfigure(0, weight=1)
        self.stage = tk.Frame(main, bg=C.bg)
        self.stage.grid(row=0, column=0, sticky="nsew", padx=(px(28), px(14)), pady=px(20))
        side = tk.Frame(main, bg=C.bg, width=px(340))
        side.grid(row=0, column=1, sticky="nsew", padx=(0, px(28)), pady=px(20))
        side.pack_propagate(False)
        self.quote_card = Card(side, pad=20)
        self.quote_card.pack(fill="both", expand=True)
        self._render_quote()

    def _draw_stepper(self):
        c = self.stepper
        c.delete("all")
        w = c.winfo_width()
        n = len(self.steps)
        if w < 100:
            return
        r, mid, gap = px(13), px(20), px(8)
        widths = [2 * r + gap + F["bodyb"].measure(label) for _k, label in self.steps]
        link = max(px(16), (w - sum(widths) - px(4)) / max(n - 1, 1))
        x = px(4)
        for i, (_key, label) in enumerate(self.steps):
            done, current = i < self.index, i == self.index
            cx = x + r
            fill = C.primary if (done or current) else C.surface
            c.create_oval(cx - r, mid - r, cx + r, mid + r, fill=fill,
                          outline=C.primary if (done or current) else C.border_strong, width=2)
            if done:
                icons.draw(c, "check", cx - px(7), mid - px(7), px(14), C.on_primary, width=2)
            else:
                c.create_text(cx, mid, text=str(i + 1), font=F["smallb"],
                              fill=C.on_primary if current else C.text_faint)
            c.create_text(cx + r + gap, mid, text=label, anchor="w",
                          font=F["bodyb" if current else "body"],
                          fill=C.text if (current or done) else C.text_faint)
            x += widths[i]
            if i < n - 1:
                c.create_line(x + px(10), mid, x + link - px(10), mid,
                              fill=C.primary if done else C.border_strong, width=2)
                x += link

    # --------------------------------------------------------- navigation ---
    def _key(self):
        return self.steps[self.index][0]

    def _go(self, index):
        self.index = index
        for child in self.stage.winfo_children():
            child.destroy()
        getattr(self, "_step_" + self._key())()
        last = self.index == len(self.steps) - 1
        self.next_btn.set_text("Confirm booking" if last else "Continue")
        self.back_btn.set_state("disabled" if self.index == 0 else "normal")
        self._draw_stepper()
        self._update_next()

    def _back(self):
        if self.index > 0:
            self._go(self.index - 1)

    def _next(self):
        key = self._key()
        if key == "schedule" and not self._read_schedule():
            return
        if key == "review":
            self._confirm()
            return
        self._go(self.index + 1)

    def _update_next(self):
        key = self._key()
        ok = {"customer": self.customer is not None, "vehicle": self.vehicle is not None,
              "services": self.quote is not None, "schedule": True, "review": True}[key]
        self.next_btn.set_state("normal" if ok else "disabled")

    def _title(self, text, sub=""):
        Label(self.stage, text, "h1", bg=C.bg).pack(anchor="w")
        if sub:
            Label(self.stage, sub, "body", "text_muted", bg=C.bg).pack(anchor="w", pady=(px(4), 0))
        tk.Frame(self.stage, height=px(16), bg=C.bg).pack()

    # ---------------------------------------------------------- step: customer ---
    def _step_customer(self):
        self._title("Who is this booking for?", "Search by name or phone, or register a new customer.")
        row = tk.Frame(self.stage, bg=C.bg)
        row.pack(fill="x", pady=(0, px(12)))
        self.cust_search = Field(row, "", placeholder="Search customers...", icon="search",
                                 on_change=lambda v: self._fill_customers())
        self.cust_search.pack(side="left", fill="x", expand=True)
        Button(row, "Register new", self._register_customer, "soft", icon="user_plus").pack(
            side="right", padx=(px(12), 0))
        card = Card(self.stage, pad=0)
        card.pack(fill="both", expand=True)
        self.cust_table = Table(card.body, [("n", "Customer", 190, "w", True), ("p", "Phone", 140),
                                            ("e", "Email", 190, "w", True)], height=6,
                                on_select=self._customer_picked, empty="No customers found.")
        self.cust_table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        self._fill_customers()

    def _fill_customers(self):
        query = self.cust_search.get()
        customers = self.stack.customers.search(query) if query else self.stack.customers.all()
        rows = [(c.id, [("bold", c.name), c.phone, c.email or "-"], []) for c in customers]
        self.cust_table.set_rows(rows)
        if self.customer is not None:
            self.cust_table.select(self.customer.id)

    def _customer_picked(self, iid):
        self.customer = self.stack.customers.get(int(iid)) if iid else None
        self.vehicle = None
        self._update_next()
        self._render_quote()

    def _register_customer(self):
        customer = dialogs.register_customer(self, self.stack)
        if customer:
            self.customer = customer
            self.cust_search.set("")
            self._fill_customers()
            self.cust_table.select(customer.id)

    # ---------------------------------------------------------- step: vehicle ---
    def _step_vehicle(self):
        self._title("Which vehicle is coming in?",
                    f"Prices and timing depend on the vehicle type. Owner: {self.customer.name}.")
        row = tk.Frame(self.stage, bg=C.bg)
        row.pack(fill="x", pady=(0, px(12)))
        Button(row, "Add a vehicle", self._add_vehicle, "soft", icon="plus").pack(side="left")
        card = Card(self.stage, pad=0)
        card.pack(fill="both", expand=True)
        self.veh_table = Table(card.body, [("p", "Plate", 110), ("v", "Vehicle", 200, "w", True),
                                           ("y", "Year", 70), ("c", "Color", 100),
                                           ("t", "Type", 110)], height=6,
                               on_select=self._vehicle_picked,
                               empty="No vehicles yet. Add one to continue.")
        self.veh_table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        self._fill_vehicles()

    def _fill_vehicles(self):
        vehicles = self.stack.customers.vehicles_of(self.customer.id)
        self.veh_table.set_rows([(v.id, [("bold", v.plate), f"{v.make} {v.model}", str(v.year),
                                         v.color, v.type.title()], []) for v in vehicles])
        if self.vehicle is not None:
            self.veh_table.select(self.vehicle.id)
        elif len(vehicles) == 1:
            self.veh_table.select(vehicles[0].id)

    def _vehicle_picked(self, iid):
        self.vehicle = self.stack.customers.vehicle(int(iid)) if iid else None
        self._recompute()

    def _add_vehicle(self):
        vehicle = dialogs.add_vehicle(self, self.stack, self.customer)
        if vehicle:
            self.vehicle = vehicle
            self._fill_vehicles()
            self.veh_table.select(vehicle.id)

    # --------------------------------------------------------- step: services ---
    def _step_services(self):
        self._title("Pick your services",
                    f"Pricing for a {self.vehicle.type}. Choose individual services or a bundle.")
        scroll = ScrollFrame(self.stage, bg=C.bg)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        mode = "package" if self.package_id else "services"
        self.mode_seg = Segmented(body, [("services", "Individual services"),
                                         ("package", "Packages (discounted)")], mode,
                                  self._switch_mode)
        self.mode_seg.pack(anchor="w", pady=(0, px(12)))
        self.tile_area = tk.Frame(body, bg=C.bg)
        self.tile_area.pack(fill="x")
        self._fill_tiles()

        add_ons = self.stack.catalog.add_ons()
        if add_ons:
            Label(body, "Add-ons", "h3", bg=C.bg).pack(anchor="w", pady=(px(20), px(8)))
            grid = tk.Frame(body, bg=C.bg)
            grid.pack(fill="x")
            grid.grid_columnconfigure((0, 1), weight=1, uniform="a")
            self.add_tiles = {}
            for i, a in enumerate(add_ons):
                tile = ChoiceTile(grid, a.name, "", money(a.price), f"+{a.duration} min",
                                  a.id in self.add_on_ids, command=lambda aid=a.id: self._toggle_addon(aid),
                                  height=64)
                tile.grid(row=i // 2, column=i % 2, sticky="ew", padx=px(4), pady=px(4))
                self.add_tiles[a.id] = tile

        Label(body, "Promo code", "h3", bg=C.bg).pack(anchor="w", pady=(px(20), px(8)))
        promo_row = tk.Frame(body, bg=C.bg)
        promo_row.pack(fill="x", pady=(0, px(16)))
        self.promo_field = Field(promo_row, "", value=self.promo, placeholder="Enter a code",
                                 icon="tag", width=18)
        self.promo_field.pack(side="left")
        Button(promo_row, "Apply", self._apply_promo, "soft").pack(side="left", padx=(px(12), 0))
        self.promo_msg = Label(promo_row, "", "smallb", "text_muted", bg=C.bg)
        self.promo_msg.pack(side="left", padx=px(14))
        promos = self.stack.catalog.promos()
        if promos:
            self.promo_msg.configure(
                text="Available: " + ", ".join(f"{p.code} ({p.discount_percent:g}% off)" for p in promos))

    def _fill_tiles(self):
        for child in self.tile_area.winfo_children():
            child.destroy()
        self.tiles = {}
        vt = self.vehicle.type
        self.tile_area.grid_columnconfigure((0, 1), weight=1, uniform="t")
        if self.mode_seg.value == "services":
            for i, s in enumerate(self.stack.catalog.services()):
                tile = ChoiceTile(self.tile_area, s.name, s.description,
                                  money(s.prices.get(vt, 0)), f"{s.durations.get(vt, '?')} min",
                                  s.id in self.service_ids,
                                  command=lambda sid=s.id: self._toggle_service(sid))
                tile.grid(row=i // 2, column=i % 2, sticky="ew", padx=px(4), pady=px(4))
                self.tiles[s.id] = tile
        else:
            for i, p in enumerate(self.stack.catalog.packages()):
                tile = ChoiceTile(self.tile_area, p.name, p.description, f"{p.discount_percent:g}% off",
                                  f"{len(p.service_ids)} services", p.id == self.package_id, radio=True,
                                  command=lambda pid=p.id: self._pick_package(pid))
                tile.grid(row=i // 2, column=i % 2, sticky="ew", padx=px(4), pady=px(4))
                self.tiles[p.id] = tile

    def _switch_mode(self, key):
        if key == "package":
            self.service_ids = []
        else:
            self.package_id = ""
        self._fill_tiles()
        self._recompute()

    def _toggle_service(self, sid):
        if sid in self.service_ids:
            self.service_ids.remove(sid)
        else:
            self.service_ids.append(sid)
        self.tiles[sid].set_selected(sid in self.service_ids)
        self._recompute()

    def _pick_package(self, pid):
        self.package_id = "" if self.package_id == pid else pid
        for key, tile in self.tiles.items():
            tile.set_selected(key == self.package_id)
        self._recompute()

    def _toggle_addon(self, aid):
        if aid in self.add_on_ids:
            self.add_on_ids.remove(aid)
        else:
            self.add_on_ids.append(aid)
        self.add_tiles[aid].set_selected(aid in self.add_on_ids)
        self._recompute()

    def _apply_promo(self):
        code = self.promo_field.get().upper()
        if not code:
            self.promo = ""
            self.promo_msg.configure(text="Promo removed.", fg=C.text_muted)
            self._recompute()
            return
        try:
            promo = self.stack.catalog.get_promo(code)
        except AppError as exc:
            self.promo = ""
            self.promo_msg.configure(text=str(exc), fg=C.danger)
            self._recompute()
            return
        self.promo = promo.code
        self.promo_msg.configure(text=f"{promo.code} applied: {promo.discount_percent:g}% off", fg=C.success)
        self._recompute()

    # ---------------------------------------------------------- step: schedule ---
    def _step_schedule(self):
        minutes = self.quote["duration_minutes"]
        self._title("When should we see you?",
                    f"This job needs about {minutes} minutes in the bay. We keep a "
                    f"{config.BOOKING_BUFFER_MINUTES}-minute buffer between jobs.")
        card = Card(self.stage, pad=22)
        card.pack(fill="x")
        start = self.start or datetime.now().replace(second=0, microsecond=0)
        self.picker = DateTimeField(card.body, "Date and time", start)
        self.picker.pack(anchor="w")
        self.sched_err = Label(card.body, "", "smallb", "danger", bg=C.surface)
        self.sched_err.pack(anchor="w", pady=(px(8), 0))
        Label(card.body, "Next free slots", "smallb", "text_muted", bg=C.surface).pack(
            anchor="w", pady=(px(16), px(8)))
        chips = tk.Frame(card.body, bg=C.surface)
        chips.pack(fill="x")
        slots = self.stack.bookings.next_slots(minutes, 9)
        if not slots:
            Label(chips, "No free slots found in the next two weeks. Pick a date above.", "body",
                  "text_faint", bg=C.surface).pack(anchor="w")
        for i, slot in enumerate(slots):
            when = common.pretty_dt(slot.strftime(config.DATETIME_FORMAT))
            Button(chips, when, lambda s=slot: self.picker.set_datetime(s), "soft", height=36,
                   font="smallb", padx=12).grid(row=i // 3, column=i % 3, sticky="w",
                                                padx=(0, px(8)), pady=(0, px(8)))
        if self.staff_mode:
            Button(card.body, "Walk-in: start right now", lambda: self.picker.set_datetime(datetime.now()),
                   "ghost", icon="play", height=36, font="smallb").pack(anchor="w", pady=(px(4), 0))

    def _read_schedule(self):
        try:
            self.start = self.picker.get_datetime()
        except ValueError as exc:
            self.sched_err.configure(text=str(exc))
            return False
        if self.start < datetime.now().replace(second=0, microsecond=0):
            self.sched_err.configure(text="That date and time is already in the past.")
            return False
        self.sched_err.configure(text="")
        return True

    # ----------------------------------------------------------- step: review ---
    def _step_review(self):
        self._title("Review and confirm", "Check the details below. You can still go back and change anything.")
        scroll = ScrollFrame(self.stage, bg=C.bg)
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        card = Card(body, pad=22)
        card.pack(fill="x")
        when = "Right now (walk-in)" if self.walk_in else common.pretty_dt(self.start.strftime(config.DATETIME_FORMAT))
        for label, value in (("Customer", self.customer.name), ("Vehicle", self.vehicle.describe()),
                             ("Starts", when),
                             ("Estimated time", f"{self.quote['duration_minutes']} minutes")):
            row = tk.Frame(card.body, bg=C.surface)
            row.pack(fill="x", pady=px(5))
            Label(row, label, "body", "text_muted", bg=C.surface).pack(side="left")
            Label(row, value, "bodyb", bg=C.surface).pack(side="right")
        self.review_err = None
        if self.staff_mode:
            extra = Card(body, pad=22)
            extra.pack(fill="x", pady=(px(14), 0))
            total = self.quote["total"]
            self.deposit_field = Field(extra.body, f"Deposit to collect now (max {money(total)})",
                                       value=self.deposit, icon="card", width=14)
            self.deposit_field.pack(anchor="w")
            self.notes_area = TextArea(extra.body, "Booking notes (optional)", height=3, value=self.notes)
            self.notes_area.pack(fill="x", pady=(px(14), 0))
        else:
            Label(body, "Payment happens in person at the shop, so please arrive on time.", "body",
                  "text_muted", bg=C.bg).pack(anchor="w", pady=(px(14), 0))

    def _confirm(self):
        deposit = 0.0
        notes = ""
        if self.staff_mode:
            raw = self.deposit_field.get() or "0"
            try:
                deposit = float(raw)
            except ValueError:
                self.deposit_field.set_error("Enter the deposit as a number.")
                return
            self.deposit, notes = raw, self.notes_area.get()
        start = datetime.now() if self.walk_in else self.start
        try:
            appt = self.stack.bookings.create_booking(
                self.customer.id, self.vehicle.id, self.service_ids, self.add_on_ids,
                self.package_id, self.promo, start, deposit, notes)
        except (BookingError, InventoryError) as exc:
            if not self.walk_in and isinstance(exc, BookingError) and "schedule" in [k for k, _ in self.steps]:
                self._go([k for k, _ in self.steps].index("schedule"))
                self.sched_err.configure(text=str(exc))
            else:
                from app.ui.widgets import alert
                alert(self, "Could not book", str(exc))
            return
        except AppError as exc:
            from app.ui.widgets import alert
            alert(self, "Could not book", str(exc))
            return
        self.result = appt
        self.destroy()

    # ------------------------------------------------------------- quote ---
    def _recompute(self):
        self.quote = None
        if self.vehicle is not None and (self.service_ids or self.package_id):
            try:
                self.quote = self.stack.catalog.build_quote(
                    self.vehicle.type, self.service_ids, self.add_on_ids, self.package_id, self.promo)
            except AppError:
                self.quote = None
        self._update_next()
        self._render_quote()

    def _render_quote(self):
        body = self.quote_card.body
        for child in body.winfo_children():
            child.destroy()
        Label(body, "Your quote", "h3", bg=C.surface).pack(anchor="w")
        if self.customer:
            Label(body, self.customer.name, "body", "text_muted", bg=C.surface).pack(anchor="w", pady=(px(2), 0))
        if self.vehicle:
            Label(body, self.vehicle.describe(), "small", "text_muted", bg=C.surface).pack(anchor="w")
        Divider(body).pack(fill="x", pady=px(14))
        q = self.quote
        if not q:
            body_empty = EmptyState(body, "receipt", "Nothing selected yet",
                                    "Choose a vehicle and services to see the price build up here.",
                                    bg=C.surface)
            body_empty.pack(pady=px(30))
            return
        for item in q["items"]:
            row = tk.Frame(body, bg=C.surface)
            row.pack(fill="x", pady=px(3))
            Label(row, item["name"], "body", bg=C.surface, wrap=px(190)).pack(side="left")
            Label(row, money(item["price"]), "body", bg=C.surface).pack(side="right")
        Divider(body).pack(fill="x", pady=px(10))

        def line(label, value, tone="text_muted"):
            row = tk.Frame(body, bg=C.surface)
            row.pack(fill="x", pady=px(2))
            Label(row, label, "body", tone, bg=C.surface).pack(side="left")
            Label(row, value, "body", tone, bg=C.surface).pack(side="right")
        line("Subtotal", money(q["subtotal"]))
        if q["package_discount_amount"]:
            line("Package discount", "-" + money(q["package_discount_amount"]), "success")
        if q["promo_discount_amount"]:
            line(f"Promo {q['promo_code']}", "-" + money(q["promo_discount_amount"]), "success")
        total = tk.Frame(body, bg=C.surface)
        total.pack(fill="x", pady=(px(14), 0))
        Label(total, "Total", "h3", bg=C.surface).pack(side="left")
        Label(total, money(q["total"]), "kpi_s", "primary", bg=C.surface).pack(side="right")
        chip = tk.Frame(body, bg=C.primary_soft)
        chip.pack(fill="x", pady=(px(16), 0))
        Label(chip, f"About {q['duration_minutes']} minutes in the bay", "smallb", "primary",
              bg=C.primary_soft).pack(padx=px(12), pady=px(8), anchor="w")

    # -------------------------------------------------------------- show ---
    def show(self):
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.wait_window(self)
        return self.result
