"""The Tkinter application window.

The UI only ever receives the service `stack` from build_stack(), so no
business logic lives here: screens call services and show the result.
"""
import tkinter as tk

from app import config
from app.ui import theme


def _make_icon(root):
    """A 64px app icon drawn pixel by pixel (no image files needed)."""
    size = 64
    img = tk.PhotoImage(width=size, height=size, master=root)
    r = 16
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            dx = max(r - x, x - (size - 1 - r), 0)
            dy = max(r - y, y - (size - 1 - r), 0)
            if dx * dx + dy * dy > r * r:
                row.append("#000000")
                continue
            t = (x + y) / (2.0 * size)
            base = theme.mix("#22D3EE", "#0E7490", t)
            u, v = abs(x - 32) / 17.0, abs(y - 32) / 17.0
            if u ** 0.62 + v ** 0.62 <= 1.0:
                base = "#FFFFFF"
            row.append(base)
        rows.append("{" + " ".join(row) + "}")
    img.put(" ".join(rows))
    return img


class App(tk.Tk):
    def __init__(self, stack, splash=True):
        theme.enable_dpi_awareness()
        super().__init__()
        self.stack = stack
        self.withdraw()
        self.title(config.SHOP_NAME)
        theme.init_scale(self)
        theme.apply(theme.load_mode())
        theme.init_fonts(self)
        theme.style_ttk(self)
        self.configure(bg=theme.C.bg)
        try:
            self._icon = _make_icon(self)
            self.iconphoto(True, self._icon)
        except tk.TclError:
            pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(theme.px(1440), sw - theme.px(60)), min(theme.px(900), sh - theme.px(100))
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - theme.px(20))}")
        self.minsize(min(theme.px(1180), w), min(theme.px(720), h))
        self.container = tk.Frame(self, bg=theme.C.bg)
        self.container.pack(fill="both", expand=True)
        self.screen = None
        self._state = ("login", None, None)
        self.bind("<F11>", lambda e: self.attributes("-fullscreen",
                                                     not self.attributes("-fullscreen")))
        if splash:
            from app.ui.splash import Splash
            Splash(self, self._ready)
        else:
            self._ready()

    # ------------------------------------------------------------- screens ---
    def _ready(self):
        self.show_login()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _swap(self, screen):
        if self.screen is not None:
            self.screen.destroy()
        self.screen = screen
        screen.pack(fill="both", expand=True)

    def show_login(self):
        from app.ui.login import LoginScreen
        self._state = ("login", None, None)
        self._swap(LoginScreen(self, self.stack))

    def show_shell(self, kind, user, page=None):
        from app.ui.shell import CUSTOMER_MENU, STAFF_MENUS, Shell
        self._state = (kind, user, page)
        shell = Shell(self, self.stack, kind, user)
        self._swap(shell)
        menu = STAFF_MENUS[user.role] if kind == "staff" else CUSTOMER_MENU
        shell.navigate(page if page in menu else menu[0])

    def set_theme(self, mode):
        theme.apply(mode)
        theme.save_mode(mode)
        theme.style_ttk(self)
        self.configure(bg=theme.C.bg)
        self.container.configure(bg=theme.C.bg)
        kind, user, page = self._state
        if kind == "login":
            self.show_login()
        else:
            current = self.screen.page_key if self.screen is not None else page
            self.show_shell(kind, user, current)


def run(stack):
    App(stack).mainloop()
