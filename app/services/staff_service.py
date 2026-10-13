"""Staff management (roles, accounts)."""
from app.config import STAFF_ROLES
from app.exceptions import ValidationError
from app.models import Staff
from app.utils.validation import require, valid_name, valid_phone


class StaffService:
    def __init__(self, staff_repo):
        self.staff = staff_repo

    def all(self):
        return self.staff.all()

    def add(self, name, role, username, password, phone=""):
        name = valid_name(name)
        role = require(role, "Role").lower()
        if role not in STAFF_ROLES:
            raise ValidationError(f"Role must be one of: {', '.join(STAFF_ROLES)}.")
        username = require(username, "Username")
        if self.staff.find_by_username(username):
            raise ValidationError(f"The username '{username}' is already taken.")
        password = require(password, "Password")
        return self.staff.add(Staff(
            name=name, role=role, username=username, password=password,
            phone=valid_phone(phone),
        ))

    def toggle_active(self, staff_id, acting_staff):
        """Deactivate/reactivate an account. Fail-safe: you cannot lock yourself out."""
        member = self.staff.get(staff_id)
        if member.id == acting_staff.id:
            raise ValidationError("You cannot deactivate your own account.")
        member.active = not member.active
        return self.staff.update(member)
