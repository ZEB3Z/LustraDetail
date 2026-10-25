"""Reusable, themed building blocks: buttons, cards, fields, tables, dialogs.

Everything here is plain tkinter / ttk. Rounded shapes are drawn on Canvas,
hover and focus states are tweened, and colours come from theme.C so a
theme flip only needs a rebuild.
"""
import calendar
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from app import config
from app.ui import anim, icons
from app.ui.theme import C, F, mix, px
from app.utils.datetime_utils import ceil_to


# ------------------------------------------------------------------ basics ---
def parent_bg(widget):
    try:
        return widget.cget("bg")
    except tk.TclError:
        return C.bg


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def Label(parent, text="", font="body", color="text", bg=None, anchor="w",
          wrap=None, justify="left", **kw):
    return tk.Label(parent, text=text, font=F[font], fg=getattr(C, color, color),
                    bg=bg or parent_bg(parent), anchor=anchor, justify=justify,
                    wraplength=wrap or 0, bd=0, highlightthickness=0, **kw)


def Spacer(parent, h=0, w=0, bg=None):
    return tk.Frame(parent, height=h, width=w, bg=bg or parent_bg(parent))


def Divider(parent, color=None, pad=0):
    return tk.Frame(parent, height=1, bg=color or C.border)


def bind_tree(widget, sequence, func):
    """Bind an event on a widget and all its descendants (for hover/click rows)."""
    widget.bind(sequence, func, add="+")
    for child in widget.winfo_children():
        bind_tree(child, sequence, func)


# ------------------------------------------------------------------ button ---
class Button(tk.Canvas):
    """Rounded button with hover/press tweening. variant: primary, secondary,
    ghost, soft, danger, danger_soft, success."""

    def __init__(self, parent, text="", command=None, variant="primary", icon=None,
                 width=None, height=40, font="btn", radius=10, bg=None, state="normal",
                 icon_size=16, padx=18, anchor="center"):
        self._bg_parent = bg or parent_bg(parent)
        self.text, self.command, self.variant = text, command, variant
        self.icon_name, self.state = icon, state
        self._font = F[font]
        self._radius, self._anchor = px(radius), anchor
        self._icon_size = px(icon_size)
        gap = px(8) if (icon and text) else 0
        content = self._font.measure(text) + (self._icon_size + gap if icon else 0)
        w = max(px(width or 0), content + px(padx) * 2) if text else px(height)
        if not text and width:
            w = px(width)
        self._bw, self._bh, self._gap = w, px(height), gap
        super().__init__(parent, width=self._bw, height=self._bh, bg=self._bg_parent,
                         highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        self._colors = self._palette()
        self._cur = self._colors["bg"]
        self._tw = None
        self._draw()
        self.bind("<Enter>", lambda e: self._to("hover"))
        self.bind("<Leave>", lambda e: self._to("bg"))
        self.bind("<ButtonPress-1>", lambda e: self._to("press"))
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Return>", lambda e: self._fire())
        self.bind("<space>", lambda e: self._fire())
        self.bind("<FocusIn>", lambda e: self._draw())
        self.bind("<FocusOut>", lambda e: self._draw())
        if state == "disabled":
            self.configure(cursor="arrow")

    def _palette(self):
        v, pbg = self.variant, self._bg_parent
        table = {
            "primary": (C.primary, C.primary_hover, C.primary_press, C.on_primary, None),
            "secondary": (C.surface, C.surface_alt, C.border, C.text, C.border_strong),
            "ghost": (pbg, mix(pbg, C.text, 0.07), mix(pbg, C.text, 0.13), C.text_muted, None),
            "soft": (C.primary_soft, mix(C.primary_soft, C.primary, 0.14),
                     mix(C.primary_soft, C.primary, 0.24), C.primary, None),
            "danger": (C.danger, mix(C.danger, "#000000", 0.12), mix(C.danger, "#000000", 0.24),
                       "#FFFFFF" if C.mode != "dark" else "#1F0A0A", None),
            "danger_soft": (C.danger_soft, mix(C.danger_soft, C.danger, 0.14),
                            mix(C.danger_soft, C.danger, 0.24), C.danger, None),
            "success": (C.success, mix(C.success, "#000000", 0.12), mix(C.success, "#000000", 0.24),
                        "#FFFFFF" if C.mode != "dark" else "#04200F", None),
        }
        bg, hover, press, fg, border = table[v]
        if self.state == "disabled":
            bg, fg, border = C.surface_alt, C.text_faint, None
        return dict(bg=bg, hover=hover, press=press, fg=fg, border=border)

    def _draw(self):
        self.delete("all")
        col = self._colors
        w, h = self._bw, self._bh
        self._shape = round_rect(self, 1, 1, w - 1, h - 1, self._radius, fill=self._cur,
                                 outline=col["border"] or self._cur, width=1)
        if self.focus_get() is self and self.state != "disabled":
            round_rect(self, 1, 1, w - 1, h - 1, self._radius, fill="", outline=C.accent, width=2)
        content = self._font.measure(self.text) + (self._icon_size + self._gap if self.icon_name else 0)
        x = (w - content) / 2 if self._anchor == "center" else px(16)
        if self.icon_name:
            icons.draw(self, self.icon_name, x, (h - self._icon_size) / 2, self._icon_size,
                       col["fg"], width=1.8 * self._icon_size / 16)
            x += self._icon_size + self._gap
        if self.text:
            self.create_text(x, h / 2, text=self.text, font=self._font, fill=col["fg"],
                             anchor="w")

    def _to(self, key):
        if self.state == "disabled":
            return
        target = self._colors[key]
        start = self._cur
        if self._tw:
            self._tw.cancel()

        def step(t):
            self._cur = mix(start, target, t)
            self.itemconfigure(self._shape, fill=self._cur,
                               outline=self._colors["border"] or self._cur)
        self._tw = anim.tween(self, 120, step, ease=anim.ease_out)

    def _release(self, event):
        inside = 0 <= event.x <= self._bw and 0 <= event.y <= self._bh
        self._to("hover" if inside else "bg")
        if inside:
            self._fire()

    def _fire(self):
        if self.state != "disabled" and self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        gap = px(8) if (self.icon_name and text) else 0
        content = self._font.measure(text) + (self._icon_size + gap if self.icon_name else 0)
        self._bw = max(self._bw if not text else 0, content + px(36))
        self._gap = gap
        self.configure(width=self._bw)
        self._draw()

    def set_state(self, state):
        self.state = state
        self._colors = self._palette()
        self._cur = self._colors["bg"]
        self.configure(cursor="hand2" if state == "normal" else "arrow")
        self._draw()


def IconButton(parent, icon, command=None, variant="ghost", size=36, **kw):
    return Button(parent, "", command, variant, icon=icon, height=size, width=size,
                  radius=10, **kw)


# -------------------------------------------------------------------- card ---
class Card(tk.Frame):
    """Rounded surface with a soft shadow. Put children inside `card.body`.

    The rounded background is a Canvas stacked behind a normal Frame, so
    the card sizes itself from its content like any other frame.
    """

    def __init__(self, parent, pad=20, radius=16, fill=None, bg=None, border=True,
                 stretch=False, shadow=True):
        self._parent_bg = bg or parent_bg(parent)
        self._fill = fill or C.surface
        self._r = px(radius)
        self._border = border
        self._shadow = shadow and C.mode != "dark"
        super().__init__(parent, bg=self._parent_bg)
        self._canvas = tk.Canvas(self, bg=self._parent_bg, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=self._fill)
        self.body.pack(fill="both", expand=True, padx=px(pad),
                       pady=(px(pad), px(pad) + (px(3) if self._shadow else 0)))
        self._canvas.bind("<Configure>", self._paint)

    def _paint(self, event):
        c, w, h = self._canvas, event.width, event.height
        c.delete("all")
        bottom = h - 4 if self._shadow else h - 1
        if self._shadow:
            for i, amt in enumerate((0.05, 0.035, 0.02)):
                round_rect(c, 2 - i, 3 + i - 1, w - 2 + i, bottom + i, self._r + i,
                           fill=mix(self._parent_bg, C.shadow, amt), outline="")
        round_rect(c, 1, 1, w - 2, bottom, self._r, fill=self._fill,
                   outline=C.border if self._border else self._fill, width=1)


# ------------------------------------------------------------------- badge ---
BADGE_KINDS = {
    "success": ("success_soft", "success"), "warning": ("warning_soft", "warning"),
    "danger": ("danger_soft", "danger"), "info": ("info_soft", "info"),
    "primary": ("primary_soft", "primary"), "neutral": ("surface_alt", "text_muted"),
}
STATUS_KIND = {
    config.STATUS_BOOKED: "info", config.STATUS_IN_PROGRESS: "warning",
    config.STATUS_DONE: "primary", config.STATUS_PAID: "success",
    config.STATUS_CANCELLED: "neutral", config.STATUS_NO_SHOW: "danger",
}
STATUS_LABEL = {
    config.STATUS_BOOKED: "Booked", config.STATUS_IN_PROGRESS: "In progress",
    config.STATUS_DONE: "Done", config.STATUS_PAID: "Paid",
    config.STATUS_CANCELLED: "Cancelled", config.STATUS_NO_SHOW: "No-show",
}


def status_color(status):
    soft, strong = BADGE_KINDS[STATUS_KIND.get(status, "neutral")]
    return getattr(C, strong)


class Badge(tk.Canvas):
    def __init__(self, parent, text, kind="neutral", dot=True, bg=None, font="smallb"):
        soft, strong = BADGE_KINDS[kind]
        fill, fg = getattr(C, soft), getattr(C, strong)
        fnt = F[font]
        pad = px(10)
        dot_w = px(14) if dot else 0
        w = fnt.measure(text) + pad * 2 + dot_w
        h = px(26)
        super().__init__(parent, width=w, height=h, bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0)
        round_rect(self, 0, 0, w - 1, h - 1, h / 2, fill=fill, outline="")
        x = pad
        if dot:
            r = px(3.5)
            self.create_oval(x, h / 2 - r, x + 2 * r, h / 2 + r, fill=fg, outline="")
            x += dot_w
        self.create_text(x, h / 2, text=text, font=fnt, fill=fg, anchor="w")


def StatusBadge(parent, status, **kw):
    return Badge(parent, STATUS_LABEL.get(status, status), STATUS_KIND.get(status, "neutral"), **kw)


# ------------------------------------------------------------------- field ---
class Field(tk.Frame):
    """Labelled text entry with focus ring, placeholder and inline error."""

    def __init__(self, parent, label="", value="", placeholder="", show=None, width=None,
                 icon=None, hint="", bg=None, justify="left", on_change=None):
        super().__init__(parent, bg=bg or parent_bg(parent))
        self._placeholder, self._show, self._showing_ph = placeholder, show, False
        self._on_change = on_change
        if label:
            Label(self, label, "smallb", "text_muted").pack(anchor="w", pady=(0, px(6)))
        self.box = tk.Frame(self, bg=C.surface, highlightthickness=1,
                            highlightbackground=C.border_strong, highlightcolor=C.primary)
        self.box.pack(fill="x")
        if icon:
            ic = tk.Canvas(self.box, width=px(18), height=px(18), bg=C.surface,
                           highlightthickness=0)
            icons.draw(ic, icon, 0, 0, px(18), C.text_faint, width=1.6)
            ic.pack(side="left", padx=(px(12), 0))
        self.entry = tk.Entry(self.box, relief="flat", bd=0, font=F["body"], bg=C.surface,
                              fg=C.text, insertbackground=C.text, highlightthickness=0,
                              selectbackground=C.primary, selectforeground=C.on_primary,
                              justify=justify, width=int(width) if width else 20)
        self.entry.pack(side="left", fill="x", expand=True, padx=px(12), pady=px(10))
        self.hint = Label(self, hint, "small", "text_faint") if hint else None
        if self.hint:
            self.hint.pack(anchor="w", pady=(px(4), 0))
        self.err = Label(self, "", "small", "danger", wrap=px(320))
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.box.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<KeyRelease>", lambda e: self._changed())
        if value:
            self.set(value)
        else:
            self._focus_out(None)

    # ---- placeholder handling
    def _focus_in(self, _e):
        self.box.configure(highlightbackground=C.primary)
        if self._showing_ph:
            self.entry.delete(0, "end")
            self.entry.configure(fg=C.text, show=self._show or "")
            self._showing_ph = False

    def _focus_out(self, _e):
        self.box.configure(highlightbackground=C.danger if self.err.winfo_ismapped()
                           else C.border_strong)
        if not self.entry.get() and self._placeholder:
            self.entry.configure(fg=C.text_faint, show="")
            self.entry.insert(0, self._placeholder)
            self._showing_ph = True

    def _changed(self):
        if self.err.winfo_ismapped():
            self.set_error(None)
        if self._on_change:
            self._on_change(self.get())

    def get(self):
        return "" if self._showing_ph else self.entry.get().strip()

    def set(self, value):
        self._focus_in(None)
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        if not self.entry.focus_get() is self.entry:
            self._focus_out(None)

    def focus(self):
        self.entry.focus_set()

    def set_error(self, message):
        if message:
            self.err.configure(text=message)
            self.err.pack(anchor="w", pady=(px(4), 0))
            self.box.configure(highlightbackground=C.danger)
        else:
            self.err.pack_forget()
            self.box.configure(highlightbackground=C.primary
                               if self.entry.focus_get() is self.entry else C.border_strong)

    def on_return(self, func):
        self.entry.bind("<Return>", lambda e: func())


class Select(tk.Frame):
    """Labelled read-only dropdown. options: list of str or (label, value)."""

    def __init__(self, parent, label="", options=(), value=None, width=18, command=None, bg=None):
        super().__init__(parent, bg=bg or parent_bg(parent))
        if label:
            Label(self, label, "smallb", "text_muted").pack(anchor="w", pady=(0, px(6)))
        self._pairs = [(o, o) if not isinstance(o, tuple) else o for o in options]
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var, state="readonly",
                                  style="Lustra.TCombobox", width=width, font=F["body"],
                                  values=[p[0] for p in self._pairs])
        self.combo.pack(fill="x")
        self._command = command
        self.combo.bind("<<ComboboxSelected>>", self._chosen)
        self.combo.bind("<MouseWheel>", lambda e: "break")
        if value is not None:
            self.set(value)
        elif self._pairs:
            self.combo.current(0)

    def _chosen(self, _e):
        self.combo.selection_clear()
        if self._command:
            self._command(self.get())

    def get(self):
        label = self.var.get()
        for lab, val in self._pairs:
            if lab == label:
                return val
        return None

    def set(self, value):
        for lab, val in self._pairs:
            if val == value or lab == value:
                self.var.set(lab)
                return

    def set_options(self, options, value=None):
        self._pairs = [(o, o) if not isinstance(o, tuple) else o for o in options]
        self.combo.configure(values=[p[0] for p in self._pairs])
        if value is not None:
            self.set(value)
        elif self._pairs:
            self.combo.current(0)


class TextArea(tk.Frame):
    def __init__(self, parent, label="", height=3, value="", bg=None):
        super().__init__(parent, bg=bg or parent_bg(parent))
        if label:
            Label(self, label, "smallb", "text_muted").pack(anchor="w", pady=(0, px(6)))
        self.box = tk.Frame(self, bg=C.surface, highlightthickness=1,
                            highlightbackground=C.border_strong, highlightcolor=C.primary)
        self.box.pack(fill="x")
        self.text = tk.Text(self.box, height=height, relief="flat", bd=0, font=F["body"],
                            bg=C.surface, fg=C.text, insertbackground=C.text, wrap="word",
                            highlightthickness=0, padx=px(12), pady=px(10))
        self.text.pack(fill="x")
        self.text.insert("1.0", value)
        self.text.bind("<FocusIn>", lambda e: self.box.configure(highlightbackground=C.primary))
        self.text.bind("<FocusOut>", lambda e: self.box.configure(highlightbackground=C.border_strong))

    def get(self):
        return self.text.get("1.0", "end").strip()


# --------------------------------------------------------------- segmented ---
class Segmented(tk.Canvas):
    """Pill-shaped tab switcher with an animated thumb."""

    def __init__(self, parent, options, value=None, command=None, bg=None, height=40,
                 font="bodyb", min_seg=0):
        self.options = list(options)
        self.command = command
        fnt = F[font]
        pad = px(18)
        self._seg = [max(fnt.measure(lab) + pad * 2, px(min_seg)) for _, lab in self.options]
        self._h = px(height)
        self._font = fnt
        w = sum(self._seg) + px(8)
        super().__init__(parent, width=w, height=self._h, bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value = value if value is not None else self.options[0][0]
        self._x = self._target_x()
        self._tw = None
        self._draw()
        self.bind("<Button-1>", self._click)

    def _starts(self):
        x, out = px(4), []
        for s in self._seg:
            out.append(x)
            x += s
        return out

    def _index(self):
        return [k for k, _ in self.options].index(self.value)

    def _target_x(self):
        return self._starts()[self._index()]

    def _draw(self):
        self.delete("all")
        w, h = int(self.cget("width")), self._h
        round_rect(self, 0, 0, w - 1, h - 1, h / 2, fill=C.surface_alt, outline=C.border)
        i = self._index()
        round_rect(self, self._x, px(4), self._x + self._seg[i], h - px(4), (h - px(8)) / 2,
                   fill=C.surface, outline=C.border_strong, tags="thumb")
        for (key, lab), x, s in zip(self.options, self._starts(), self._seg):
            self.create_text(x + s / 2, h / 2, text=lab, font=self._font,
                             fill=C.text if key == self.value else C.text_muted)

    def _click(self, event):
        for (key, _), x, s in zip(self.options, self._starts(), self._seg):
            if x <= event.x <= x + s and key != self.value:
                self.select(key)
                break

    def select(self, key, fire=True):
        start = self._x
        self.value = key
        target = self._target_x()
        if self._tw:
            self._tw.cancel()

        def step(t):
            self._x = start + (target - start) * t
            self._draw()
        self._tw = anim.tween(self, 220, step, ease=anim.ease_in_out)
        if fire and self.command:
            self.command(key)


# ------------------------------------------------------------------ switch ---
class Switch(tk.Canvas):
    def __init__(self, parent, value=False, command=None, bg=None, on_color=None):
        self.w, self.h = px(46), px(26)
        super().__init__(parent, width=self.w, height=self.h, bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value, self.command = value, command
        self._t = 1.0 if value else 0.0
        self._on = on_color or C.primary
        self._off = C.sidebar_line
        self._draw()
        self.bind("<Button-1>", lambda e: self.toggle())

    def _draw(self):
        self.delete("all")
        round_rect(self, 0, 0, self.w - 1, self.h - 1, self.h / 2,
                   fill=mix(self._off, self._on, self._t), outline="")
        pad = px(3)
        d = self.h - 2 * pad
        x = pad + (self.w - 2 * pad - d) * self._t
        self.create_oval(x, pad, x + d, pad + d, fill="#FFFFFF", outline="")

    def toggle(self):
        self.value = not self.value
        start, end = self._t, 1.0 if self.value else 0.0

        def step(t):
            self._t = start + (end - start) * t
            self._draw()
        anim.tween(self, 200, step, ease=anim.ease_in_out)
        if self.command:
            self.command(self.value)


# ------------------------------------------------------------- scroll area ---
class SlimScrollbar(tk.Canvas):
    """Thin rounded scrollbar (ttk scrollbars ignore custom widths on clam)."""

    def __init__(self, parent, command, bg=None, width=10):
        super().__init__(parent, width=px(width), bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0)
        self.command = command
        self.lo, self.hi = 0.0, 1.0
        self._drag, self._hover = None, False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag", None))
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))

    def set(self, lo, hi):
        self.lo, self.hi = float(lo), float(hi)
        self.draw()

    def _set_hover(self, value):
        self._hover = value
        self.draw()

    def _thumb(self):
        h = max(self.winfo_height(), 1)
        top = self.lo * h
        bottom = max(self.hi * h, top + px(36))
        return top, min(bottom, h)

    def draw(self):
        self.delete("all")
        w = self.winfo_width()
        top, bottom = self._thumb()
        round_rect(self, px(2), top + 1, w - px(2), bottom - 1, (w - px(4)) / 2,
                   fill=C.text_faint if (self._hover or self._drag is not None) else C.border_strong,
                   outline="")

    def _press(self, event):
        top, bottom = self._thumb()
        if top <= event.y <= bottom:
            self._drag = event.y - top
        else:
            h = max(self.winfo_height(), 1)
            self.command("moveto", event.y / h - (self.hi - self.lo) / 2)

    def _motion(self, event):
        if self._drag is not None:
            h = max(self.winfo_height(), 1)
            self.command("moveto", (event.y - self._drag) / h)


class ScrollFrame(tk.Frame):
    """Vertically scrolling container; add children to `.body`."""

    def __init__(self, parent, bg=None, scrollbar="Page"):
        bg = bg or parent_bg(parent)
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.bar = SlimScrollbar(self, self.canvas.yview, bg=bg)
        self.canvas.configure(yscrollcommand=self._set_bar)
        self.bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        for w in (self, self.canvas, self.body):
            w.bind("<Enter>", self._bind_wheel)
            w.bind("<Leave>", self._unbind_wheel)

    def _set_bar(self, lo, hi):
        self.bar.set(lo, hi)
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.bar.pack_forget()
        elif not self.bar.winfo_ismapped():
            self.bar.pack(side="right", fill="y", before=self.canvas)

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _bind_wheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self._scroll(-3))
        self.canvas.bind_all("<Button-5>", lambda e: self._scroll(3))

    def _unbind_wheel(self, _e):
        # only unbind if the pointer truly left the whole scroll area
        x, y = self.winfo_pointerxy()
        w = self.winfo_containing(x, y)
        while w is not None:
            if w is self:
                return
            w = getattr(w, "master", None)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _wheel(self, event):
        delta = -1 * (event.delta // 120 if abs(event.delta) >= 120 else event.delta)
        self._scroll(delta * 3 if abs(event.delta) >= 120 else delta)

    def _scroll(self, units):
        if self.bar.winfo_ismapped():
            self.canvas.yview_scroll(units, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)


# ------------------------------------------------------------------- table ---
def _fit(font, text, width):
    text = str(text)
    if font.measure(text) <= width:
        return text
    while text and font.measure(text + "...") > width:
        text = text[:-1]
    return text + "..."


class Table(tk.Frame):
    """Canvas data grid with pill badges, hover and selection.

    columns: list of (key, title, width, anchor, stretch).
    rows:    list of (iid, cells, tags). A cell is plain text or one of
             ("badge", text, kind) / ("status", STATUS) / ("bold", text) /
             ("muted", text). Tag "muted" or "danger" tints the row's text.
    """

    def __init__(self, parent, columns, height=8, on_select=None, on_double=None,
                 empty="Nothing to show yet.", bg=None, row_h=52, scrollbar="Lustra"):
        super().__init__(parent, bg=bg or parent_bg(parent))
        self.columns, self.on_select, self.on_double = columns, on_select, on_double
        self._empty, self._row_h = empty, px(row_h)
        self._head_h = px(40)
        self.rows, self._selected, self._hover = [], None, None
        self._widths = [px(c[2]) for c in columns]
        self.head = tk.Canvas(self, height=self._head_h, bg=C.surface_alt, highlightthickness=0,
                              bd=0)
        self.head.pack(fill="x")
        holder = tk.Frame(self, bg=C.surface)
        holder.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(holder, bg=C.surface, highlightthickness=0, bd=0,
                                height=self._row_h * height)
        self.bar = SlimScrollbar(holder, self.canvas.yview, bg=C.surface)
        self.canvas.configure(yscrollcommand=self._set_bar)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.empty_lbl = Label(holder, empty, "body", "text_faint", bg=C.surface, anchor="center")
        self.canvas.bind("<Configure>", lambda e: self._relayout())
        self.canvas.bind("<Motion>", self._motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Double-Button-1>", self._double)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))

    # ---- layout
    def _relayout(self):
        total = self.canvas.winfo_width()
        base = [px(c[2]) for c in self.columns]
        extra = max(0, total - sum(base) - (self.bar.winfo_width() if self.bar.winfo_ismapped() else 0))
        weights = {i: (c[4] if c[4] is not True else 1) for i, c in enumerate(self.columns)
                   if len(c) > 4 and c[4]}
        self._widths = list(base)
        if weights:
            wsum = sum(weights.values())
            avail = total - (self.bar.winfo_width() if self.bar.winfo_ismapped() else 0)
            diff = avail - sum(base)                 # + spare room, - shortage
            for i, wt in weights.items():
                self._widths[i] = max(px(64), int(base[i] + diff * wt / wsum))
        self._draw_head()
        self._draw_rows()

    def _x_positions(self):
        xs, x = [], 0
        for w in self._widths:
            xs.append(x)
            x += w
        return xs

    def _draw_head(self):
        self.head.delete("all")
        for col, x, w in zip(self.columns, self._x_positions(), self._widths):
            anchor = col[3] if len(col) > 3 else "w"
            tx = {"w": x + px(12), "e": x + w - px(12), "center": x + w / 2}[anchor]
            self.head.create_text(tx, self._head_h / 2, text=col[1], font=F["smallb"],
                                  fill=C.text_muted, anchor={"w": "w", "e": "e", "center": "center"}[anchor])

    def _draw_rows(self):
        c = self.canvas
        c.delete("all")
        width = max(c.winfo_width(), sum(self._widths))
        xs = self._x_positions()
        for i, (iid, cells, tags) in enumerate(self.rows):
            y = i * self._row_h
            fill = C.surface
            if iid == self._selected:
                fill = C.select
            elif iid == self._hover:
                fill = mix(C.surface, C.primary, 0.05)
            c.create_rectangle(0, y, width, y + self._row_h, fill=fill, outline="",
                               tags=("row", f"row{i}"))
            c.create_line(0, y + self._row_h - 1, width, y + self._row_h - 1, fill=C.border)
            if iid == self._selected:
                c.create_rectangle(0, y, px(4), y + self._row_h, fill=C.primary, outline="")
            for col, cell, x, w in zip(self.columns, cells, xs, self._widths):
                self._draw_cell(c, cell, col, x, w, y, tags)
        c.configure(scrollregion=(0, 0, width, max(len(self.rows) * self._row_h, 1)))

    def _draw_cell(self, c, cell, col, x, w, y, tags):
        anchor = col[3] if len(col) > 3 else "w"
        mid = y + self._row_h / 2
        pad = px(12)
        kind, text = "text", cell
        if isinstance(cell, tuple):
            kind, text = cell[0], cell[1]
        if kind == "status":
            text, kd = STATUS_LABEL.get(cell[1], cell[1]), STATUS_KIND.get(cell[1], "neutral")
            cell = ("badge", text, kd)
            kind = "badge"
        if kind == "badge":
            soft, strong = BADGE_KINDS[cell[2]]
            fnt = F["smallb"]
            bw = fnt.measure(cell[1]) + px(34)
            bh = px(26)
            bx = x + pad if anchor == "w" else x + w - pad - bw
            round_rect(c, bx, mid - bh / 2, bx + bw, mid + bh / 2, bh / 2,
                       fill=getattr(C, soft), outline="")
            r = px(3.5)
            c.create_oval(bx + px(10), mid - r, bx + px(10) + 2 * r, mid + r,
                          fill=getattr(C, strong), outline="")
            c.create_text(bx + px(24), mid, text=cell[1], font=fnt, fill=getattr(C, strong),
                          anchor="w")
            return
        font = {"bold": F["bodyb"], "muted": F["small"]}.get(kind, F["body"])
        color = {"muted": C.text_muted}.get(kind, C.text)
        if "muted" in tags:
            color = C.text_faint
        if "danger" in tags:
            color = C.danger
        text = _fit(font, text, w - 2 * pad)
        tx = {"w": x + pad, "e": x + w - pad, "center": x + w / 2}[anchor]
        c.create_text(tx, mid, text=text, font=font, fill=color,
                      anchor={"w": "w", "e": "e", "center": "center"}[anchor])

    def _set_bar(self, lo, hi):
        self.bar.set(lo, hi)
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.bar.pack_forget()
        elif not self.bar.winfo_ismapped():
            self.bar.pack(side="right", fill="y")

    # ---- interaction
    def _row_at(self, event):
        y = self.canvas.canvasy(event.y)
        i = int(y // self._row_h)
        return self.rows[i][0] if 0 <= i < len(self.rows) else None

    def _motion(self, event):
        self._set_hover(self._row_at(event))

    def _set_hover(self, iid):
        if iid != self._hover:
            self._hover = iid
            self.canvas.configure(cursor="hand2" if iid is not None and self.on_select else "")
            self._draw_rows()

    def _click(self, event):
        iid = self._row_at(event)
        if iid is not None:
            self.select(iid)

    def _double(self, event):
        iid = self._row_at(event)
        if iid is not None and self.on_double:
            self.on_double(iid)

    def _wheel(self, event):
        step = -1 * (event.delta // 120 if abs(event.delta) >= 120 else event.delta)
        self.canvas.yview_scroll(step * 2, "units")

    # ---- public API
    def set_rows(self, rows, keep_selection=True):
        previous = self._selected if keep_selection else None
        self.rows = [(str(iid), cells, tags or ()) for iid, cells, tags in rows]
        ids = [r[0] for r in self.rows]
        self._selected = previous if previous in ids else None
        if self.rows:
            self.empty_lbl.place_forget()
        else:
            self.empty_lbl.place(relx=0.5, rely=0.45, anchor="center")
            self.empty_lbl.lift()
        self._draw_rows()
        if previous is not None and self._selected is None and self.on_select:
            self.on_select(None)

    def selected_id(self):
        return self._selected

    def select(self, iid):
        iid = None if iid is None else str(iid)
        if iid == self._selected:
            return
        self._selected = iid
        self._draw_rows()
        if iid is not None:
            idx = [r[0] for r in self.rows].index(iid)
            top, bottom = idx * self._row_h, (idx + 1) * self._row_h
            region = max(len(self.rows) * self._row_h, 1)
            view_top = self.canvas.canvasy(0)
            view_bottom = view_top + self.canvas.winfo_height()
            if top < view_top:
                self.canvas.yview_moveto(top / region)
            elif bottom > view_bottom:
                self.canvas.yview_moveto((bottom - self.canvas.winfo_height()) / region)
        if self.on_select:
            self.on_select(iid)

    def clear_selection(self):
        if self._selected is not None:
            self._selected = None
            self._draw_rows()
            if self.on_select:
                self.on_select(None)


# ------------------------------------------------------------ small blocks ---
def EmptyState(parent, icon, title, text="", bg=None, wrap=340):
    bg = bg or parent_bg(parent)
    box = tk.Frame(parent, bg=bg)
    cv = tk.Canvas(box, width=px(64), height=px(64), bg=bg, highlightthickness=0)
    round_rect(cv, 0, 0, px(63), px(63), px(20), fill=C.primary_soft, outline="")
    icons.draw(cv, icon, px(18), px(18), px(28), C.primary, width=2)
    cv.pack()
    Label(box, title, "h3", bg=bg, anchor="center").pack(pady=(px(14), px(4)))
    if text:
        Label(box, text, "body", "text_muted", bg=bg, anchor="center", justify="center",
              wrap=px(wrap)).pack()
    return box


class IconTile(tk.Canvas):
    """Rounded square holding an icon, tinted with a theme colour name."""

    def __init__(self, parent, icon, tone="primary", size=44, bg=None, radius=14):
        s = px(size)
        super().__init__(parent, width=s, height=s, bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0)
        soft = {"primary": C.primary_soft, "success": C.success_soft, "warning": C.warning_soft,
                "danger": C.danger_soft, "info": C.info_soft}[tone]
        strong = getattr(C, tone)
        round_rect(self, 0, 0, s - 1, s - 1, px(radius), fill=soft, outline="")
        inner = int(s * 0.5)
        icons.draw(self, icon, (s - inner) / 2, (s - inner) / 2, inner, strong, width=2)


class StatCard(Card):
    """KPI tile: icon, caption, big animated number, small footnote."""

    def __init__(self, parent, title, value, fmt=None, sub="", icon="chart", tone="primary",
                 sub_tone="text_muted"):
        super().__init__(parent, pad=18, radius=16)
        self.fmt = fmt or (lambda v: f"{v:,.0f}")
        top = tk.Frame(self.body, bg=C.surface)
        top.pack(fill="x")
        IconTile(top, icon, tone, size=42).pack(side="left")
        Label(top, title, "smallb", "text_muted", bg=C.surface).pack(side="left", padx=px(12))
        self.value_lbl = Label(self.body, self.fmt(0), "kpi", bg=C.surface)
        self.value_lbl.pack(anchor="w", pady=(px(14), 0))
        self.sub_lbl = Label(self.body, sub, "small", sub_tone, bg=C.surface)
        self.sub_lbl.pack(anchor="w", pady=(px(2), 0))
        self._value = value
        anim.tween(self, 800, lambda t: self.value_lbl.configure(text=self.fmt(value * t)),
                   done=lambda: self.value_lbl.configure(text=self.fmt(value)),
                   ease=anim.ease_out, delay=60)


# ------------------------------------------------------------------ toasts ---
_toasts = []


def toast(window, message, kind="success"):
    """Slide-in notification at the bottom-right of `window`."""
    tone = {"success": C.success, "error": C.danger, "warning": C.warning,
            "info": C.info}.get(kind, C.primary)
    icon = {"success": "check", "error": "x", "warning": "alert", "info": "info"}.get(kind, "info")
    frame = tk.Frame(window, bg=C.surface, highlightthickness=1,
                     highlightbackground=C.border_strong)
    tk.Frame(frame, bg=tone, width=px(5)).pack(side="left", fill="y")
    cv = tk.Canvas(frame, width=px(22), height=px(22), bg=C.surface, highlightthickness=0)
    icons.draw(cv, icon, px(2), px(2), px(18), tone, width=2)
    cv.pack(side="left", padx=(px(14), px(8)), pady=px(14))
    Label(frame, message, "bodyb", bg=C.surface, wrap=px(360)).pack(
        side="left", padx=(0, px(18)), pady=px(14))
    frame.update_idletasks()
    _toasts.append(frame)
    slot = len(_toasts) - 1
    base_y = -px(28) - slot * (frame.winfo_reqheight() + px(10))

    def step(t):
        frame.place(relx=1.0, rely=1.0, x=-px(28), y=base_y + px(40) * (1 - t), anchor="se")
        frame.lift()
    anim.tween(frame, 320, step, ease=anim.ease_out)

    def dismiss():
        if frame in _toasts:
            _toasts.remove(frame)
        try:
            frame.destroy()
        except tk.TclError:
            pass
    window.after(3600 if kind != "error" else 5200, dismiss)
    frame.bind("<Button-1>", lambda e: dismiss())


# ------------------------------------------------------------------ dialog ---
class Dialog(tk.Toplevel):
    """Modal window with a themed header, body and right-aligned footer."""

    def __init__(self, master, title, subtitle="", icon=None, width=520, tone="primary"):
        super().__init__(master)
        self.master_win = master.winfo_toplevel()
        self.result = None
        self.title(title)
        self.configure(bg=C.surface)
        self.resizable(False, False)
        self.transient(self.master_win)
        self._width = px(width)
        head = tk.Frame(self, bg=C.surface)
        head.pack(fill="x", padx=px(28), pady=(px(24), px(6)))
        if icon:
            IconTile(head, icon, tone, size=46, bg=C.surface).pack(side="left", padx=(0, px(14)))
        titles = tk.Frame(head, bg=C.surface)
        titles.pack(side="left", fill="x", expand=True)
        Label(titles, title, "h2", bg=C.surface).pack(anchor="w")
        if subtitle:
            Label(titles, subtitle, "body", "text_muted", bg=C.surface,
                  wrap=self._width - px(150)).pack(anchor="w", pady=(px(2), 0))
        self.banner = None
        self.body = tk.Frame(self, bg=C.surface)
        self.body.pack(fill="both", expand=True, padx=px(28), pady=(px(14), px(8)))
        Divider(self).pack(fill="x", pady=(px(8), 0))
        self.footer = tk.Frame(self, bg=C.surface_alt)
        self.footer.pack(fill="x")
        self.footer_inner = tk.Frame(self.footer, bg=C.surface_alt)
        self.footer_inner.pack(side="right", padx=px(22), pady=px(14))
        self.bind("<Escape>", lambda e: self.close(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self.close(None))

    def add_button(self, text, command, variant="primary", icon=None):
        btn = Button(self.footer_inner, text, command, variant, icon=icon,
                     bg=C.surface_alt, height=40)
        btn.pack(side="right", padx=(px(10), 0))
        return btn

    def show_error(self, message):
        if self.banner is not None:
            self.banner.destroy()
        self.banner = tk.Frame(self.body, bg=C.danger_soft)
        Label(self.banner, message, "bodyb", "danger", bg=C.danger_soft, wrap=self._width - px(110)
              ).pack(anchor="w", padx=px(14), pady=px(10))
        self.banner.pack(fill="x", pady=(0, px(12)), before=self.body.winfo_children()[0])

    def clear_error(self):
        if self.banner is not None:
            self.banner.destroy()
            self.banner = None

    def close(self, result=None):
        self.result = result
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def show(self):
        self.update_idletasks()
        w = max(self._width, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        m = self.master_win
        x = m.winfo_rootx() + (m.winfo_width() - w) // 2
        y = m.winfo_rooty() + max(px(20), (m.winfo_height() - h) // 2)
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_set()
        self.wait_window(self)
        return self.result


def confirm(master, title, message, ok="Confirm", danger=False, icon="alert"):
    dlg = Dialog(master, title, icon=icon, width=460, tone="danger" if danger else "primary")
    Label(dlg.body, message, "body", "text_muted", bg=C.surface, wrap=px(390)).pack(anchor="w")
    dlg.add_button(ok, lambda: dlg.close(True), "danger" if danger else "primary")
    dlg.add_button("Cancel", lambda: dlg.close(False), "secondary")
    return bool(dlg.show())


def alert(master, title, message, kind="error"):
    icon = {"error": "alert", "info": "info", "success": "check"}.get(kind, "info")
    tone = {"error": "danger", "success": "success"}.get(kind, "primary")
    dlg = Dialog(master, title, icon=icon, width=480, tone=tone)
    Label(dlg.body, message, "body", "text_muted", bg=C.surface, wrap=px(410)).pack(anchor="w")
    dlg.add_button("OK", lambda: dlg.close(True), "primary")
    dlg.show()


# ------------------------------------------------------------- date picker ---
class CalendarPopup(tk.Toplevel):
    """Month grid shown under a DateField."""

    def __init__(self, anchor, current, on_pick):
        super().__init__(anchor)
        self.overrideredirect(True)
        self.configure(bg=C.border_strong)
        self.on_pick = on_pick
        self.selected = current
        self.view = date(current.year, current.month, 1)
        self.inner = tk.Frame(self, bg=C.surface)
        self.inner.pack(padx=1, pady=1)
        self._build()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + px(6)
        self.geometry(f"+{x}+{y}")
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(50, self._grab_focus)

    def _grab_focus(self):
        try:
            self.focus_force()
            self.bind("<FocusOut>", self._maybe_close)
        except tk.TclError:
            pass

    def _maybe_close(self, _e):
        self.after(120, self._check_focus)

    def _check_focus(self):
        try:
            f = self.focus_get()
            if f is None or f.winfo_toplevel() is not self:
                self.destroy()
        except (tk.TclError, KeyError):
            try:
                self.destroy()
            except tk.TclError:
                pass

    def _build(self):
        for child in self.inner.winfo_children():
            child.destroy()
        head = tk.Frame(self.inner, bg=C.surface)
        head.pack(fill="x", padx=px(10), pady=(px(10), px(4)))
        IconButton(head, "chevron_left", lambda: self._shift(-1), size=30,
                   bg=C.surface).pack(side="left")
        IconButton(head, "chevron_right", lambda: self._shift(1), size=30,
                   bg=C.surface).pack(side="right")
        Label(head, self.view.strftime("%B %Y"), "bodyb", bg=C.surface, anchor="center"
              ).pack(side="left", expand=True)
        grid = tk.Frame(self.inner, bg=C.surface)
        grid.pack(padx=px(10), pady=(0, px(10)))
        for c, name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            Label(grid, name, "smallb", "text_faint", bg=C.surface, anchor="center",
                  width=4).grid(row=0, column=c, pady=(0, px(4)))
        today = date.today()
        for r, week in enumerate(calendar.Calendar(0).monthdatescalendar(
                self.view.year, self.view.month), start=1):
            for c, day in enumerate(week):
                in_month = day.month == self.view.month
                is_sel, is_today = day == self.selected, day == today
                fg = C.on_primary if is_sel else (C.text if in_month else C.text_faint)
                bgc = C.primary if is_sel else C.surface
                lbl = tk.Label(grid, text=str(day.day), font=F["smallb" if is_today else "small"],
                               fg=C.primary if (is_today and not is_sel) else fg, bg=bgc,
                               width=4, pady=px(5), cursor="hand2")
                lbl.grid(row=r, column=c, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda e, d=day: self._pick(d))
                if not is_sel:
                    lbl.bind("<Enter>", lambda e, w=lbl: w.configure(bg=C.primary_soft))
                    lbl.bind("<Leave>", lambda e, w=lbl: w.configure(bg=C.surface))

    def _shift(self, delta):
        m = self.view.month - 1 + delta
        self.view = date(self.view.year + m // 12, m % 12 + 1, 1)
        self._build()

    def _pick(self, day):
        self.on_pick(day)
        self.destroy()


class DateField(Field):
    """Text field (YYYY-MM-DD) with a calendar popup."""

    def __init__(self, parent, label="", value=None, bg=None, on_change=None):
        super().__init__(parent, label, value or date.today().strftime(config.DATE_FORMAT),
                         width=11, bg=bg, on_change=on_change)
        cal = tk.Canvas(self.box, width=px(30), height=px(30), bg=C.surface,
                        highlightthickness=0, cursor="hand2")
        icons.draw(cal, "calendar", px(5), px(5), px(20), C.primary, width=1.8)
        cal.pack(side="right", padx=(0, px(8)))
        cal.bind("<Button-1>", lambda e: self._open())
        self._popup = None

    def _open(self):
        try:
            current = datetime.strptime(self.get(), config.DATE_FORMAT).date()
        except ValueError:
            current = date.today()
        if self._popup is not None:
            try:
                self._popup.destroy()
            except tk.TclError:
                pass
        self._popup = CalendarPopup(self.box, current, self._picked)

    def _picked(self, day):
        self.set(day.strftime(config.DATE_FORMAT))
        if self._on_change:
            self._on_change(self.get())

    def date_str(self):
        """Validated 'YYYY-MM-DD' or raises ValueError."""
        datetime.strptime(self.get(), config.DATE_FORMAT)
        return self.get()


class DateTimeField(tk.Frame):
    """Date + hour + minute pickers that return a datetime."""

    def __init__(self, parent, label="Date and time", value=None, bg=None):
        super().__init__(parent, bg=bg or parent_bg(parent))
        value = ceil_to(value or datetime.now(), 5)      # never round into the past
        Label(self, label, "smallb", "text_muted").pack(anchor="w", pady=(0, px(6)))
        row = tk.Frame(self, bg=self["bg"])
        row.pack(fill="x")
        self.date = DateField(row, "", value.strftime(config.DATE_FORMAT))
        self.date.pack(side="left")
        self.hour = Select(row, "", [f"{h:02d}" for h in range(24)], f"{value.hour:02d}", width=4)
        self.hour.pack(side="left", padx=(px(10), 0))
        Label(row, ":", "h3", bg=self["bg"]).pack(side="left", padx=px(4))
        minute = f"{value.minute:02d}"
        self.minute = Select(row, "", [f"{m:02d}" for m in range(0, 60, 5)], minute, width=4)
        self.minute.pack(side="left")

    def set_datetime(self, dt):
        dt = ceil_to(dt, 5)
        self.date.set(dt.strftime(config.DATE_FORMAT))
        self.hour.set(f"{dt.hour:02d}")
        self.minute.set(f"{dt.minute:02d}")

    def get_datetime(self):
        """Raises ValueError with a friendly message on a bad date."""
        try:
            day = datetime.strptime(self.date.get(), config.DATE_FORMAT)
        except ValueError:
            raise ValueError("Use the date format YYYY-MM-DD, for example 2026-10-24.") from None
        return day.replace(hour=int(self.hour.get()), minute=int(self.minute.get()))
