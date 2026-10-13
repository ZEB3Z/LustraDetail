"""Authentication for staff and customers.

NOTE: passwords are stored in plain text ON PURPOSE - this is a class
project and the team explicitly decided against hashing for this version.
"""
from app.exceptions import AuthError


class AuthService:
    def __init__(self, staff_repo, customer_repo):
        self.staff = staff_repo
        self.customers = customer_repo

    def staff_login(self, username, password):
        member = self.staff.find_by_username(username)
        if member is None or member.password != password:
            raise AuthError("Invalid username or password.")
        if not member.active:
            raise AuthError("This staff account is deactivated. Please contact the admin.")
        return member

    def customer_login(self, phone):
        customer = self.customers.find_by_phone(phone)
        if customer is None:
            raise AuthError("No customer is registered with that phone number.")
        return customer
