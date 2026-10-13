"""ASCII art for the terminal UI.

Pure ASCII characters only (no unicode box drawing) so the banners look
identical on every terminal, including legacy Windows code pages.
"""

LOGO_LINES = [
    "L  U  S  T  R  A  D  E  T  A  I  L",
    "         A U T O    C A R E",
    "",
    "             ______",
    "            /|_||_\\`.____",
    "           (   _    _  _ \\",
    "           =`-(_)--(_)-'",
]


def box(lines, width=62):
    """Center `lines` inside a plain-ASCII box (widths computed, never eyeballed)."""
    inner = width - 4
    out = ["+" + "-" * (width - 2) + "+"]
    out += ["|  " + line.center(inner) + "  |" for line in lines]
    out.append("+" + "-" * (width - 2) + "+")
    return "\n".join(out)


def main_banner():
    from app.config import SHOP_TAGLINE
    lines = [""] + LOGO_LINES + ["", f'"{SHOP_TAGLINE}"', ""]
    return box(lines, width=62)


def section(title, width=64):
    """A section header like:  == [ DASHBOARD ]=============="""
    label = f"[ {title.upper()} ]"
    return "=" * 2 + label + "=" * max(1, width - 2 - len(label))


def small_box(title):
    return box([title], width=max(20, len(title) + 8))
