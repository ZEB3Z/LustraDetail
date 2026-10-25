"""Design system: palettes, fonts, DPI scaling, ttk styling, saved preference.

Widgets read colours from the shared `C` object at construction time. When
the theme flips, `apply()` rewrites `C` and the app rebuilds its current
screen, so there is never a half-light, half-dark window.
"""
import json
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from app import config

PALETTES = {
    "light": dict(
        bg="#F2F5FA", surface="#FFFFFF", surface_alt="#EEF3F9",
        border="#E1E7F0", border_strong="#C9D3E2",
        text="#0B1B33", text_muted="#51617A", text_faint="#8795AB",
        primary="#0E7490", primary_hover="#0B6279", primary_press="#094F64",
        primary_soft="#DDF2F7", on_primary="#FFFFFF", accent="#22D3EE",
        sidebar="#0B1B33", sidebar_hover="#132847", sidebar_active="#183253",
        sidebar_text="#9DB0CA", sidebar_text_active="#FFFFFF", sidebar_line="#1C3153",
        success="#15803D", success_soft="#DCFCE7",
        warning="#B45309", warning_soft="#FEF1C7",
        danger="#DC2626", danger_soft="#FEE2E2",
        info="#2563EB", info_soft="#DBE8FE",
        row_alt="#F8FAFD", select="#D9F0F6", shadow="#0B1B33",
    ),
    "dark": dict(
        bg="#0A1322", surface="#111D31", surface_alt="#172640",
        border="#223350", border_strong="#30466B",
        text="#E8EEF8", text_muted="#9BACC5", text_faint="#6C7E99",
        primary="#22D3EE", primary_hover="#5BE3F5", primary_press="#0FB5D0",
        primary_soft="#0F3A4C", on_primary="#032530", accent="#22D3EE",
        sidebar="#070F1C", sidebar_hover="#0F1D33", sidebar_active="#13264A",
        sidebar_text="#8396B3", sidebar_text_active="#FFFFFF", sidebar_line="#16253F",
        success="#4ADE80", success_soft="#12361F",
        warning="#FBBF24", warning_soft="#3B2F0E",
        danger="#F87171", danger_soft="#40191B",
        info="#7DB1FB", info_soft="#15294F",
        row_alt="#0F1A2E", select="#14405A", shadow="#000000",
    ),
}


class _Colors:
    """Mutable colour bag: `C.surface`, `C.primary`, ..."""


C = _Colors()
F = {}                 # named fonts, filled by init_fonts()
_state = {"mode": "light", "scale": 1.0}
SETTINGS_FILE = config.PROJECT_ROOT / ".lustra_ui.json"


# ---------------------------------------------------------------- colours ---
def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def mix(a, b, t):
    """Blend colour a toward colour b by t (0..1)."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex([x + (y - x) * t for x, y in zip(ra, rb)])


def apply(mode):
    mode = mode if mode in PALETTES else "light"
    _state["mode"] = mode
    C.__dict__.update(PALETTES[mode])
    C.mode = mode


def mode():
    return _state["mode"]


def is_dark():
    return _state["mode"] == "dark"


def load_mode():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data.get("theme", "light")
    except (OSError, ValueError):
        return "light"


def save_mode(value):
    try:
        SETTINGS_FILE.write_text(json.dumps({"theme": value}), encoding="utf-8")
    except OSError:
        pass            # a read-only folder must never crash the UI


# ------------------------------------------------------------ DPI / sizes ---
def enable_dpi_awareness():
    """Crisp text on Windows high-DPI screens (call BEFORE creating Tk)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def init_scale(root):
    try:
        scale = root.winfo_fpixels("1i") / 96.0
    except tk.TclError:
        scale = 1.0
    _state["scale"] = max(1.0, min(scale, 3.0))


def px(value):
    """Scale a design pixel value for the current screen density."""
    return int(round(value * _state["scale"]))


# ------------------------------------------------------------------ fonts ---
def _pick(root, preferred):
    available = {name.lower(): name for name in tkfont.families(root)}
    for name in preferred:
        if name.lower() in available:
            return available[name.lower()]
    return tkfont.nametofont("TkDefaultFont").actual("family")


def init_fonts(root):
    sans = _pick(root, ["Segoe UI Variable Display", "Segoe UI", "SF Pro Display",
                        "Helvetica Neue", "Inter", "Ubuntu", "Noto Sans",
                        "DejaVu Sans", "Helvetica", "Arial"])
    mono = _pick(root, ["Cascadia Mono", "Consolas", "SF Mono", "Menlo",
                        "DejaVu Sans Mono", "Courier New"])
    F.clear()

    def make(size, weight="normal", family=sans):
        return tkfont.Font(root=root, family=family, size=size, weight=weight)

    F.update(
        tiny=make(8), tinyb=make(8, "bold"),
        small=make(9), smallb=make(9, "bold"),
        body=make(10), bodyb=make(10, "bold"),
        btn=make(10, "bold"),
        h3=make(12, "bold"), h2=make(15, "bold"), h1=make(21, "bold"),
        kpi=make(25, "bold"), kpi_s=make(17, "bold"),
        brand=make(13, "bold"), huge=make(32, "bold"),
        mono=make(10, family=mono), monob=make(10, "bold", family=mono),
    )


# -------------------------------------------------------------- ttk style ---
def style_ttk(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    # ---- tables
    style.configure("Lustra.Treeview", background=C.surface, fieldbackground=C.surface,
                    foreground=C.text, rowheight=px(44), borderwidth=0,
                    relief="flat", font=F["body"])
    style.layout("Lustra.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Lustra.Treeview.Heading", background=C.surface_alt,
                    foreground=C.text_muted, font=F["smallb"], relief="flat",
                    borderwidth=0, padding=(px(12), px(10)))
    style.map("Lustra.Treeview.Heading", background=[("active", C.border)])
    style.map("Lustra.Treeview",
              background=[("selected", C.select)],
              foreground=[("selected", C.text)])

    # ---- scrollbars (slim, no arrows)
    for name, trough in (("Lustra", C.surface), ("Page", C.bg)):
        sname = f"{name}.Vertical.TScrollbar"
        style.layout(sname, [("Vertical.Scrollbar.trough", {
            "sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        style.configure(sname, troughcolor=trough, background=C.border_strong,
                        bordercolor=trough, lightcolor=C.border_strong,
                        darkcolor=C.border_strong, gripcount=0, width=px(9),
                        relief="flat", arrowsize=0)
        style.map(sname, background=[("active", C.text_faint), ("pressed", C.text_faint)],
                  lightcolor=[("active", C.text_faint)], darkcolor=[("active", C.text_faint)])

    # ---- combobox
    style.configure("Lustra.TCombobox", fieldbackground=C.surface, background=C.surface,
                    foreground=C.text, arrowcolor=C.text_muted, bordercolor=C.border_strong,
                    lightcolor=C.border_strong, darkcolor=C.border_strong,
                    padding=(px(10), px(8)), arrowsize=px(14), selectbackground=C.surface,
                    selectforeground=C.text)
    style.map("Lustra.TCombobox",
              fieldbackground=[("readonly", C.surface), ("disabled", C.surface_alt)],
              foreground=[("disabled", C.text_faint)],
              selectbackground=[("readonly", C.surface)],
              selectforeground=[("readonly", C.text)],
              bordercolor=[("focus", C.primary), ("active", C.primary)],
              lightcolor=[("focus", C.primary)], darkcolor=[("focus", C.primary)],
              arrowcolor=[("active", C.primary)])
    root.option_add("*TCombobox*Listbox.background", C.surface, 80)
    root.option_add("*TCombobox*Listbox.foreground", C.text, 80)
    root.option_add("*TCombobox*Listbox.selectBackground", C.primary, 80)
    root.option_add("*TCombobox*Listbox.selectForeground", C.on_primary, 80)
    root.option_add("*TCombobox*Listbox.font", F["body"], 80)
    root.option_add("*TCombobox*Listbox.borderWidth", 0, 80)
    root.option_add("*TCombobox*Listbox.relief", "flat", 80)
    root.option_add("*Font", F["body"], 20)
    return style
