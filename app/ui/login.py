"""Welcome screen: brand panel on the left, staff / customer sign-in on the right."""
import tkinter as tk

from app import config
from app.exceptions import AppError
from app.ui import anim, brand, dialogs, icons
from app.ui.theme import C, F, is_dark, mix, px
from app.ui.widgets import Button, Field, IconButton, Label, Segmented, toast

# The demo accounts documented in the README.
DEMO = [("Admin", "admin", "admin123"), ("Detailer", "alwin", "detail123"),
        ("Cashier", "cashier", "cash123")]
DEMO_PHONE = "09171234567"
LOCK_SECONDS = 15


class BrandPanel(tk.Canvas):
    """Gradient panel with the car, headline and a periodic light sweep."""

    TOP, BOTTOM = "#0F2A52", "#060E1D"

    def __init__(self, parent):
        super().__init__(parent, bg=self.BOTTOM, highlightthickness=0, bd=0)
        self.sweep = None
        self._shine = None
        self.bind("<Configure>", lambda e: self.paint())
        self.after(1400, self._loop)

    def paint(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 100:
            return
        steps = 90
        for i in range(steps):
            self.create_rectangle(0, h * i / steps, w, h * (i + 1) / steps + 1, outline="",
                                  fill=mix(self.TOP, self.BOTTOM, i / steps))
        for cx, cy, r, amt in ((w * 0.85, h * 0.12, 260, 0.03), (w * 0.1, h * 0.95, 320, 0.025)):
            for k in range(6):
                rr = px(r) * (1 - k * 0.12)
                self.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="",
                                 fill=mix(self.TOP, "#22D3EE", amt * (0.25 + k * 0.1)))
        pad = px(56)
        mark = tk.Canvas(self, width=px(44), height=px(44), bg=self.TOP, highlightthickness=0)
        self.create_window(pad, pad, window=mark, anchor="w")
        brand.logo_mark(mark, 0, px(2), px(40))
        self.create_text(pad + px(58), pad - px(8), text=config.APP_NAME, anchor="w",
                         font=F["h2"], fill="#FFFFFF")
        self.create_text(pad + px(58), pad + px(12), text="AUTO CARE", anchor="w",
                         font=F["tinyb"], fill="#8FB3CF")
        self.create_text(pad, h * 0.30, text="Drive in dirty.", anchor="w", font=F["huge"],
                         fill="#FFFFFF")
        self.create_text(pad, h * 0.30 + px(50), text="Drive out dazzling.", anchor="w",
                         font=F["huge"], fill="#22D3EE")
        self.create_text(pad, h * 0.30 + px(104), width=w - 2 * pad, anchor="nw", font=F["body"],
                         fill="#9FB6CC",
                         text="One bay, zero conflicts. Every job tracked from booking to receipt.")
        scale = min((w - 2 * pad) / brand.CAR_W, px(1.05))
        self._scale = scale
        self._cx = (w - brand.CAR_W * scale) / 2
        self._cy = h * 0.62
        gx, gy = w / 2, self._cy + 112 * scale
        for i in range(5):
            self.create_oval(gx - (210 - i * 22) * scale, gy - (4 - i * 0.4) * scale + i,
                             gx + (210 - i * 22) * scale, gy + (12 - i) * scale, outline="",
                             fill=mix(self.BOTTOM, "#000000", 0.12))
        brand.draw_car(self, self._cx, self._cy, scale, "#E9F4FA", "#0F3C58", "#0A1424", "#9FB6CC")
        feats = [("calendar", "Conflict-free scheduling"), ("box", "Live inventory"),
                 ("receipt", "Instant receipts")]
        x = pad
        y = h - px(54)
        for icon, text in feats:
            icons.draw(self, icon, x, y - px(10), px(20), "#22D3EE", width=1.8)
            tid = self.create_text(x + px(30), y, text=text, anchor="w", font=F["small"], fill="#C5D5E6")
            x = self.bbox(tid)[2] + px(28)

    def _loop(self):
        if not self.winfo_exists():
            return

        def step(t):
            if self._shine is not None:
                self.delete(self._shine)
                self._shine = None
            if 0 < t < 1:
                poly = brand.shine_polygon(-60 + 520 * t)
                if len(poly) >= 3:
                    flat = []
                    for x, y in poly:
                        flat += [self._cx + x * self._scale, self._cy + y * self._scale]
                    self._shine = self.create_polygon(*flat, fill="#8EE9F8", outline="")
        anim.tween(self, 1100, step, ease=anim.ease_in_out)
        self.after(6500, self._loop)


class LoginScreen(tk.Frame):
    def __init__(self, app, stack):
        super().__init__(app.container, bg=C.bg)
        self.app, self.stack = app, stack
        self.attempts = 3
        self.locked = False
        self.grid_columnconfigure(0, weight=11, uniform="c")
        self.grid_columnconfigure(1, weight=10, uniform="c")
        self.grid_rowconfigure(0, weight=1)
        BrandPanel(self).grid(row=0, column=0, sticky="nsew")
        right = tk.Frame(self, bg=C.bg)
        right.grid(row=0, column=1, sticky="nsew")
        IconButton(right, "sun" if is_dark() else "moon",
                   lambda: app.set_theme("light" if is_dark() else "dark"), size=40).place(
            relx=1.0, x=-px(28), y=px(24), anchor="ne")
        form = tk.Frame(right, bg=C.bg, width=px(420))
        form.place(relx=0.5, rely=0.5, anchor="center")
        Label(form, "Welcome back", "h1").pack(anchor="w")
        Label(form, "Sign in to run the shop or manage your bookings.", "body", "text_muted").pack(
            anchor="w", pady=(px(4), px(24)))
        self.tabs = Segmented(form, [("staff", "Staff"), ("customer", "Customer")], "staff",
                              self._switch, min_seg=150, height=42)
        self.tabs.pack(anchor="w", pady=(0, px(22)))
        self.panel = tk.Frame(form, bg=C.bg, width=px(420))
        self.panel.pack(fill="x")
        self.demo_row = tk.Frame(form, bg=C.bg)
        self.demo_row.pack(fill="x", pady=(px(26), 0))
        self._staff_form()
        self._demo_chips()

    # ---------------------------------------------------------------- tabs ---
    def _switch(self, key):
        for child in self.panel.winfo_children():
            child.destroy()
        self.msg = None
        (self._staff_form if key == "staff" else self._customer_form)()

    def _error_label(self):
        self.msg = Label(self.panel, "", "smallb", "danger", wrap=px(400))
        self.msg.pack(anchor="w", pady=(px(10), 0))

    def _staff_form(self):
        self.user_f = Field(self.panel, "Username", placeholder="e.g. admin", icon="user", width=34)
        self.user_f.pack(fill="x", pady=(0, px(14)))
        self.pass_f = Field(self.panel, "Password", placeholder="Your password", icon="lock",
                            show="*", width=34)
        self.pass_f.pack(fill="x")
        self._error_label()
        self.go_btn = Button(self.panel, "Sign in", self._staff_login, height=46, width=400, icon="key")
        self.go_btn.pack(fill="x", pady=(px(18), 0))
        self.pass_f.on_return(self._staff_login)
        self.user_f.on_return(lambda: self.pass_f.focus())
        self.user_f.focus()

    def _customer_form(self):
        self.phone_f = Field(self.panel, "Phone number", placeholder="09171234567", icon="phone",
                             width=34, hint="Use the number you registered with.")
        self.phone_f.pack(fill="x")
        self._error_label()
        self.go_btn = Button(self.panel, "Continue", self._customer_login, height=46, width=400)
        self.go_btn.pack(fill="x", pady=(px(18), 0))
        self.reg_btn = Button(self.panel, "New here? Create an account", self._register_customer, "ghost",
                              height=40, width=400)
        self.reg_btn.pack(fill="x", pady=(px(8), 0))
        self.phone_f.on_return(self._customer_login)
        self.phone_f.focus()

    def _demo_chips(self):
        Label(self.demo_row, "Demo accounts", "smallb", "text_faint").pack(anchor="w", pady=(0, px(8)))
        chips = tk.Frame(self.demo_row, bg=C.bg)
        chips.pack(anchor="w")
        for label, user, pw in DEMO:
            Button(chips, label, lambda u=user, p=pw: self._fill_staff(u, p), "secondary", height=34,
                   font="smallb", padx=14).pack(side="left", padx=(0, px(8)))
        Button(chips, "Customer", self._fill_customer, "secondary", height=34, font="smallb",
               padx=14).pack(side="left")

    def _fill_staff(self, user, pw):
        if self.tabs.value != "staff":
            self.tabs.select("staff", fire=False)
            self._switch("staff")
        self.user_f.set(user)
        self.pass_f.set(pw)
        self.pass_f.entry.configure(show="*")
        self.pass_f.focus()

    def _fill_customer(self):
        if self.tabs.value != "customer":
            self.tabs.select("customer", fire=False)
            self._switch("customer")
        self.phone_f.set(DEMO_PHONE)

    # --------------------------------------------------------------- logic ---
    def _show(self, text):
        if self.msg is not None:
            self.msg.configure(text=text)

    def _staff_login(self):
        if self.locked:
            return
        try:
            staff = self.stack.auth.staff_login(self.user_f.get(), self.pass_f.get())
        except AppError as exc:
            self.attempts -= 1
            if self.attempts <= 0:
                self._lock()
            else:
                self._show(f"{exc}  ({self.attempts} attempt{'s' if self.attempts != 1 else ''} left)")
            return
        self.attempts = 3
        self.app.show_shell("staff", staff)
        toast(self.app, f"Welcome back, {staff.name} ({staff.role})", "success")

    def _lock(self):
        self.locked = True
        self.go_btn.set_state("disabled")
        remaining = {"n": LOCK_SECONDS}

        def tick():
            if not self.winfo_exists():
                return
            if remaining["n"] <= 0:
                self.locked, self.attempts = False, 3
                self.go_btn.set_state("normal")
                self._show("")
                return
            self._show(f"Too many failed attempts. Try again in {remaining['n']}s.")
            remaining["n"] -= 1
            self.after(1000, tick)
        tick()

    def _customer_login(self):
        phone = self.phone_f.get()
        try:
            customer = self.stack.auth.customer_login(phone)
        except AppError as exc:
            self._show(str(exc))
            return
        self.app.show_shell("customer", customer)
        toast(self.app, f"Welcome, {customer.name}!", "success")

    def _register_customer(self):
        customer = dialogs.register_customer(self.app, self.stack, phone_hint=self.phone_f.get())
        if customer:
            self.app.show_shell("customer", customer)
            toast(self.app, f"Welcome, {customer.name}! Your account is ready.", "success")
