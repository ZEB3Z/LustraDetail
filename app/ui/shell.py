"""The signed-in frame: navy sidebar, page header, and the active page."""
import importlib
import tkinter as tk
from datetime import datetime

from app import config
from app.ui import anim, brand, icons
from app.ui.theme import C, F, is_dark, mix, px
from app.ui.widgets import Button, IconButton, Label, Switch, round_rect, confirm

# key -> (label, icon, "module:Class")
PAGES = {
    "dashboard": ("Dashboard", "dashboard", "dashboard:DashboardPage"),
    "appointments": ("Appointments", "calendar", "appointments:AppointmentsPage"),
    "customers": ("Customers", "users", "customers:CustomersPage"),
    "catalog": ("Service catalog", "tag", "catalog:CatalogPage"),
    "inventory": ("Inventory", "box", "inventory:InventoryPage"),
    "reports": ("Reports", "chart", "reports:ReportsPage"),
    "staff": ("Staff", "shield", "staff_admin:StaffPage"),
    "home": ("Home", "home", "portal:HomePage"),
    "my_appointments": ("My appointments", "calendar", "appointments:MyAppointmentsPage"),
    "services": ("Services & prices", "tag", "catalog:CatalogPage"),
    "vehicles": ("My vehicles", "car", "portal:VehiclesPage"),
    "profile": ("My profile", "user", "portal:ProfilePage"),
}
STAFF_MENUS = {
    "admin": ["dashboard", "appointments", "customers", "catalog", "inventory", "reports", "staff"],
    "cashier": ["dashboard", "appointments", "customers", "catalog", "reports"],
    "detailer": ["dashboard", "appointments", "catalog", "inventory"],
}
CUSTOMER_MENU = ["home", "my_appointments", "services", "vehicles", "profile"]


class NavItem(tk.Canvas):
    def __init__(self, parent, label, icon, command, badge=0):
        super().__init__(parent, height=px(46), bg=C.sidebar, highlightthickness=0, bd=0,
                         cursor="hand2")
        self.label, self.icon, self.command, self.badge = label, icon, command, badge
        self.active, self._hover = False, 0.0
        self._tw = None
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._tween(1.0))
        self.bind("<Leave>", lambda e: self._tween(0.0))
        self.bind("<Button-1>", lambda e: self.command())

    def _tween(self, target):
        start = self._hover
        if self._tw:
            self._tw.cancel()

        def step(t):
            self._hover = start + (target - start) * t
            self.draw()
        self._tw = anim.tween(self, 140, step)

    def set_active(self, value):
        self.active = value
        self.draw()

    def set_badge(self, count):
        self.badge = count
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        if self.active:
            round_rect(self, 0, px(2), w, h - px(2), px(12), fill=C.sidebar_active, outline="")
            self.create_rectangle(0, px(12), px(4), h - px(12), fill=C.accent, outline="")
        elif self._hover > 0.01:
            round_rect(self, 0, px(2), w, h - px(2), px(12),
                       fill=mix(C.sidebar, C.sidebar_hover, self._hover), outline="")
        color = C.sidebar_text_active if self.active else mix(C.sidebar_text, "#FFFFFF", self._hover * 0.7)
        icons.draw(self, self.icon, px(18), (h - px(20)) / 2, px(20),
                   C.accent if self.active else color, width=1.8)
        self.create_text(px(52), h / 2, text=self.label, anchor="w", fill=color,
                         font=F["bodyb"] if self.active else F["body"])
        if self.badge:
            r = px(10)
            cx = w - px(22)
            round_rect(self, cx - r - px(2), h / 2 - r, cx + r + px(2), h / 2 + r, r,
                       fill=C.accent, outline="")
            self.create_text(cx, h / 2, text=str(self.badge), font=F["tinyb"], fill="#04202A")


class Shell(tk.Frame):
    def __init__(self, app, stack, kind, user):
        super().__init__(app.container, bg=C.bg)
        self.app, self.stack, self.kind, self.user = app, stack, kind, user
        self.page, self.page_key = None, None
        self.items = {}
        self.menu = STAFF_MENUS[user.role] if kind == "staff" else CUSTOMER_MENU
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._clock_job = None
        self._tick_clock()

    # ------------------------------------------------------------ sidebar ---
    def _build_sidebar(self):
        side = tk.Frame(self, bg=C.sidebar, width=px(240))
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        side.pack_propagate(False)
        logo = tk.Frame(side, bg=C.sidebar)
        logo.pack(fill="x", padx=px(22), pady=(px(26), px(22)))
        mark = tk.Canvas(logo, width=px(44), height=px(44), bg=C.sidebar, highlightthickness=0)
        brand.logo_mark(mark, 0, px(2), px(40))
        mark.pack(side="left")
        names = tk.Frame(logo, bg=C.sidebar)
        names.pack(side="left", padx=(px(12), 0))
        Label(names, config.APP_NAME, "brand", "#FFFFFF", bg=C.sidebar).pack(anchor="w")
        Label(names, "AUTO CARE", "tinyb", C.sidebar_text, bg=C.sidebar).pack(anchor="w")

        Label(side, "MENU" if self.kind == "staff" else "YOUR ACCOUNT", "tinyb", C.sidebar_text,
              bg=C.sidebar).pack(anchor="w", padx=px(26), pady=(px(6), px(8)))
        nav = tk.Frame(side, bg=C.sidebar)
        nav.pack(fill="x", padx=px(14))
        for key in self.menu:
            label, icon, _ = PAGES[key]
            item = NavItem(nav, label, icon, lambda k=key: self.navigate(k))
            item.pack(fill="x", pady=px(1))
            self.items[key] = item
        if self.kind == "customer":
            book = Button(side, "Book a service", self.book, "primary", icon="plus", bg=C.sidebar,
                          height=44)
            book.pack(fill="x", padx=px(18), pady=(px(22), 0))

        bottom = tk.Frame(side, bg=C.sidebar)
        bottom.pack(side="bottom", fill="x", padx=px(18), pady=px(20))
        user_card = tk.Frame(bottom, bg=C.sidebar_hover)
        row = tk.Frame(bottom, bg=C.sidebar)
        theme_row = tk.Frame(bottom, bg=C.sidebar)
        theme_row.pack(fill="x", pady=(0, px(14)))
        cv = tk.Canvas(theme_row, width=px(24), height=px(24), bg=C.sidebar, highlightthickness=0)
        icons.draw(cv, "moon" if not is_dark() else "sun", px(2), px(2), px(20), C.sidebar_text, width=1.8)
        cv.pack(side="left")
        Label(theme_row, "Dark mode", "body", C.sidebar_text, bg=C.sidebar).pack(side="left", padx=px(10))
        sw = Switch(theme_row, value=is_dark(), command=lambda v: self.app.set_theme("dark" if v else "light"),
                    bg=C.sidebar)
        sw.pack(side="right")
        user_card.destroy()
        row.pack(fill="x")
        name = getattr(self.user, "name", "")
        avatar = tk.Canvas(row, width=px(40), height=px(40), bg=C.sidebar, highlightthickness=0)
        avatar.create_oval(1, 1, px(39), px(39), fill=C.primary if not is_dark() else C.sidebar_active,
                           outline=C.accent if is_dark() else "")
        initials = "".join(p[0] for p in name.split()[:2]).upper() or "?"
        avatar.create_text(px(20), px(20), text=initials, font=F["smallb"],
                           fill="#FFFFFF" if not is_dark() else C.accent)
        avatar.pack(side="left")
        who = tk.Frame(row, bg=C.sidebar)
        who.pack(side="left", padx=px(10), fill="x", expand=True)
        Label(who, name, "bodyb", "#FFFFFF", bg=C.sidebar).pack(anchor="w")
        role = self.user.role.title() if self.kind == "staff" else "Customer"
        Label(who, role, "small", C.sidebar_text, bg=C.sidebar).pack(anchor="w")
        IconButton(row, "logout", self.logout, size=36, bg=C.sidebar).pack(side="right")

    # --------------------------------------------------------------- main ---
    def _build_main(self):
        main = tk.Frame(self, bg=C.bg)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        self.header = tk.Frame(main, bg=C.bg)
        self.header.grid(row=0, column=0, sticky="ew", padx=px(28), pady=(px(24), px(16)))
        self.titles = tk.Frame(self.header, bg=C.bg)
        self.titles.pack(side="left")
        self.title_lbl = Label(self.titles, "", "h1")
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = Label(self.titles, "", "body", "text_muted")
        self.sub_lbl.pack(anchor="w", pady=(px(2), 0))
        self.actions = tk.Frame(self.header, bg=C.bg)
        self.actions.pack(side="right")
        self.clock = Label(self.actions, "", "smallb", "text_faint")
        self.content = tk.Frame(main, bg=C.bg)
        self.content.grid(row=1, column=0, sticky="nsew", padx=px(28), pady=(0, px(24)))

    def _tick_clock(self):
        try:
            now = datetime.now()
            hour = now.hour % 12 or 12
            self.clock.configure(text=f"{now.strftime('%a, %b')} {now.day}  -  {hour}:{now.minute:02d} {'AM' if now.hour < 12 else 'PM'}")
            self._clock_job = self.after(20000, self._tick_clock)
        except tk.TclError:
            pass

    # --------------------------------------------------------- navigation ---
    def navigate(self, key):
        if self.page is not None:
            self.page.destroy()
        for child in self.actions.winfo_children():
            if child is not self.clock:
                child.destroy()
        label, _icon, target = PAGES[key]
        module, cls = target.split(":")
        page_cls = getattr(importlib.import_module(f"app.ui.pages.{module}"), cls)
        self.page_key = key
        for k, item in self.items.items():
            item.set_active(k == key)
        self.page = page_cls(self.content, self)
        self.page.pack(fill="both", expand=True)
        self.title_lbl.configure(text=self.page.title or label)
        self.sub_lbl.configure(text=self.page.subtitle)
        for text, command, variant, icon in self.page.actions():
            Button(self.actions, text, command, variant, icon=icon, bg=C.bg).pack(
                side="right", padx=(px(10), 0))
        self.clock.pack(side="right", padx=(px(18), px(6)))
        self.refresh_badges()

    def refresh_badges(self):
        if "appointments" in self.items and self.kind == "staff":
            if self.user.role in ("admin", "cashier"):
                self.items["appointments"].set_badge(len(self.stack.bookings.unpaid_completed()))
            else:
                self.items["appointments"].set_badge(
                    len(self.stack.bookings.with_status(config.STATUS_IN_PROGRESS)))

    def set_subtitle(self, text):
        self.sub_lbl.configure(text=text)

    def book(self):
        from app.ui.wizard import BookingWizard
        appt = BookingWizard(self.app, self.stack, customer=self.user).show()
        if appt:
            from app.ui.widgets import toast
            toast(self.app, f"Appointment #{appt.id} booked for {appt.scheduled_start}", "success")
            self.navigate("my_appointments")

    def logout(self):
        if confirm(self.app, "Log out", "Are you sure you want to sign out?", ok="Log out"):
            self.app.show_login()

    def destroy(self):
        if self._clock_job:
            try:
                self.after_cancel(self._clock_job)
            except tk.TclError:
                pass
        super().destroy()
