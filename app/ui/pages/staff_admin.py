"""Staff management (admin only)."""
import tkinter as tk

from app.ui import dialogs
from app.ui.pages.base import Page
from app.ui.theme import C, px
from app.ui.widgets import Button, Card, Table

ROLE_KIND = {"admin": "primary", "detailer": "info", "cashier": "warning"}


class StaffPage(Page):
    def build(self):
        self.title = "Staff"
        self.subtitle = "Accounts and roles for the team."
        card = Card(self, pad=0)
        card.pack(fill="both", expand=True)
        self.table = Table(card.body, [("n", "Name", 200, "w", True), ("r", "Role", 140),
                                       ("u", "Username", 150), ("p", "Phone", 140), ("s", "Status", 140)],
                           on_select=self._pick, height=8)
        self.table.pack(fill="both", expand=True, padx=px(2), pady=px(2))
        self.toggle_btn = None
        self.refresh()

    def actions(self):
        return [("Add staff", self._add, "primary", "user_plus")]

    def refresh(self):
        self.staff = {str(m.id): m for m in self.stack.staff.all()}
        self.table.set_rows([(m.id, [("bold", m.name), ("badge", m.role.title(), ROLE_KIND.get(m.role, "neutral")),
                                     m.username, m.phone or "-",
                                     ("badge", "Active", "success") if m.active else ("badge", "Inactive", "neutral")],
                              [] if m.active else ["muted"]) for m in self.stack.staff.all()])
        self._pick(self.table.selected_id())

    def _pick(self, iid):
        if self.toggle_btn is not None:
            self.toggle_btn.destroy()
            self.toggle_btn = None
        member = self.staff.get(str(iid)) if iid else None
        if member is not None:
            label = "Deactivate account" if member.active else "Reactivate account"
            self.toggle_btn = Button(self.shell.actions, label, lambda: self._toggle(member),
                                     "danger_soft" if member.active else "soft", icon="ban" if member.active else "check",
                                     bg=C.bg)
            self.toggle_btn.pack(side="right", padx=(px(10), 0))

    def _toggle(self, member):
        ok, updated = self.attempt(self.stack.staff.toggle_active, member.id, self.user)
        if ok:
            self.refresh()
            self.toast(f"{updated.name} is now {'active' if updated.active else 'inactive'}.")

    def _add(self):
        member = dialogs.add_staff(self.app, self.stack)
        if member:
            self.refresh()
            self.table.select(member.id)
            self.toast(f"{member.name} added as {member.role}.")
