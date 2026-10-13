"""Low-level terminal helpers: prompts, messages, tables, menu runner."""
from app.exceptions import AppError
from app.ui import ascii_art
from app.utils import datetime_utils as dtu
from app.utils.formatting import make_table


def banner():
    print(main_banner_text())


def main_banner_text():
    return ascii_art.main_banner()


def line(char="-", width=64):
    print(char * width)


def header(title):
    print("\n" + ascii_art.section(title))


def info(msg):
    print(f"  [i] {msg}")


def success(msg):
    print(f"  [+] {msg}")


def warn(msg):
    print(f"  [!] {msg}")


def error(msg):
    print(f"  [x] {msg}")


def ask(prompt):
    return input(f"  {prompt}: ").strip()


def ask_int(prompt, lo=None, hi=None):
    while True:
        raw = ask(prompt)
        try:
            value = int(raw)
        except ValueError:
            warn("Please enter a whole number.")
            continue
        if lo is not None and value < lo:
            warn(f"Minimum is {lo}.")
            continue
        if hi is not None and value > hi:
            warn(f"Maximum is {hi}.")
            continue
        return value


def ask_float(prompt, default=None, min_value=None):
    while True:
        suffix = f" (blank = {default})" if default is not None else ""
        raw = ask(f"{prompt}{suffix}")
        if raw == "" and default is not None:
            return default
        try:
            value = float(raw)
        except ValueError:
            warn("Please enter a number.")
            continue
        if min_value is not None and value < min_value:
            warn(f"Minimum is {min_value}.")
            continue
        return value


def ask_datetime(prompt):
    while True:
        raw = ask(f"{prompt} (YYYY-MM-DD HH:MM)")
        try:
            return dtu.parse_datetime(raw)
        except ValueError:
            warn("Use the format YYYY-MM-DD HH:MM, e.g. 2025-06-14 09:30.")


def ask_date(prompt, default_today=False):
    while True:
        suffix = " (YYYY-MM-DD, blank = today)" if default_today else " (YYYY-MM-DD)"
        raw = ask(f"{prompt}{suffix}")
        if raw == "" and default_today:
            return dtu.today_str()
        try:
            return dtu.fmt_date(dtu.parse_date(raw))
        except ValueError:
            warn("Use the format YYYY-MM-DD, e.g. 2025-06-14.")


def confirm(prompt, default=False):
    suffix = "[Y/n]" if default else "[y/N]"
    raw = ask(f"{prompt} {suffix}").lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def pause():
    input("\n  Press ENTER to continue...")


def show_table(headers, rows, aligns=None, empty="No records to display."):
    if not rows:
        warn(empty)
        return False
    print(make_table(headers, rows, aligns))
    return True


def menu(title, options, footer="Back"):
    """Run a numbered menu forever; returns when the user picks 0.

    options: list of (label, handler). AppErrors raised inside a handler
    are caught and displayed nicely, then the menu redisplays.
    """
    while True:
        header(title)
        for i, (label, _) in enumerate(options, 1):
            print(f"  [{i}] {label}")
        print(f"  [0] {footer}")
        choice = ask_int("Choose", 0, len(options))
        if choice == 0:
            return
        handler = options[choice - 1][1]
        try:
            handler()
        except AppError as exc:
            error(str(exc))
            pause()
