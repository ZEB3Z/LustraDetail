"""Base class for every screen shown inside the shell."""
import tkinter as tk

from app.exceptions import AppError
from app.ui.theme import C
from app.ui.widgets import alert, toast

ALL_ROLES = ("admin", "detailer", "cashier")
FRONT = ("admin", "cashier")      # booking desk
BAY = ("admin", "detailer")       # works on cars


class Page(tk.Frame):
    title = ""
    subtitle = ""

    def __init__(self, parent, shell):
        super().__init__(parent, bg=C.bg)
        self.shell, self.stack, self.user, self.app = shell, shell.stack, shell.user, shell.app
        self.role = getattr(self.user, "role", "customer")
        self.build()

    def build(self):
        raise NotImplementedError

    def actions(self):
        """Header buttons: list of (text, command, variant, icon)."""
        return []

    def refresh(self):
        pass

    # ---- helpers
    def toast(self, message, kind="success"):
        toast(self.app, message, kind)

    def attempt(self, func, *args, **kw):
        """Run a service call; show a friendly dialog on AppError. -> (ok, result)."""
        try:
            return True, func(*args, **kw)
        except AppError as exc:
            alert(self.app, "That didn't work", str(exc))
            return False, None
