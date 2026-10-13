"""The welcome screen: staff login, customer portal, and system info."""
from app import config
from app.exceptions import AppError
from app.ui import terminal as t


def run(stack):
    while True:
        print(t.main_banner_text())
        print(f"  {config.SHOP_NAME}  |  version {config.APP_VERSION}")
        print("\n  [1] Staff login")
        print("  [2] Customer portal")
        print("  [3] About this system")
        print("  [0] Exit")
        choice = t.ask_int("Choose", 0, 3)
        if choice == 0:
            print(f"\n  Thank you for visiting {config.APP_NAME}. Goodbye!")
            return
        if choice == 1:
            staff_login(stack)
        elif choice == 2:
            customer_portal(stack)
        else:
            about()


def staff_login(stack):
    for attempts_left in (3, 2, 1):
        print(f"\n  STAFF LOGIN  ({attempts_left} attempt(s) left)")
        try:
            username = t.ask("Username")
            password = t.ask("Password")
            staff = stack.auth.staff_login(username, password)
        except AppError as exc:
            t.error(str(exc))
            continue
        t.success(f"Welcome back, {staff.name} ({staff.role}).")
        from app.ui.staff_ui import run as run_staff
        run_staff(stack, staff)
        return
    t.warn("Too many failed attempts. Returning to the main menu.")


def customer_portal(stack):
    print("\n  CUSTOMER PORTAL - log in with the phone number you registered.")
    phone = t.ask("Phone number")
    try:
        customer = stack.auth.customer_login(phone)
    except AppError as exc:
        t.error(str(exc))
        if not t.confirm("Would you like to register as a new customer?"):
            return
        from app.ui.booking_ui import register_customer
        try:
            customer = register_customer(stack, phone_hint=phone)
        except AppError as second:
            t.error(str(second))
            return
        t.success(f"Welcome, {customer.name}! Your account has been created.")
    from app.ui.customer_ui import run as run_customer
    run_customer(stack, customer)


def about():
    t.header("ABOUT THIS SYSTEM")
    print(f"""
  {config.SHOP_NAME}
  "{config.SHOP_TAGLINE}"

  A terminal-based management system for a one-bay auto detailing shop:
  services priced per vehicle type, scheduling with conflict detection,
  job tracking, inventory, receipts, and reports.

  Built with : Python {config.APP_VERSION and '3'} standard library only (no
               third-party packages), JSON file storage, and a layered
               architecture ready for a Tkinter GUI upgrade.
  Version    : {config.APP_VERSION}
  Authors    : Ericksson Brutas and Alwin Benitez

  DEMO ACCOUNTS
  ------------- ---------------------------------
  Staff       : admin / admin123      (admin)
                alwin / detail123    (detailer)
                cashier / cash123    (cashier)
  Customer    : any registered phone, e.g. 09171234567
  ------------- ---------------------------------
""")
    t.pause()
