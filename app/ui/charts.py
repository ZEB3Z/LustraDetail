"""Canvas charts with grow-in animation: bars, ranked bars, gauge, donut."""
import tkinter as tk

from app.ui import anim
from app.ui.theme import C, F, mix, px
from app.ui.widgets import parent_bg, round_rect


def _short(value):
    if value >= 1000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return f"{value:,.0f}"


class _Animated(tk.Canvas):
    """Canvas that redraws itself with a 0..1 progress value."""

    def __init__(self, parent, width, height, bg=None, ms=800, delay=120):
        super().__init__(parent, width=width, height=height, bg=bg or parent_bg(parent),
                         highlightthickness=0, bd=0)
        self.progress = 0.0
        self._ms, self._delay = ms, delay
        self._started = False
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Map>", self._start)

    def _start(self, _e):
        if self._started:
            return
        self._started = True

        def step(t):
            self.progress = t
            self.redraw()
        anim.tween(self, self._ms, step, ease=anim.ease_out, delay=self._delay)

    def redraw(self):          # pragma: no cover - overridden
        pass


class BarChart(_Animated):
    """Vertical bars. data: list of (label, value). highlight: index to accent."""

    def __init__(self, parent, data, height=230, highlight=None, fmt=_short, bg=None):
        super().__init__(parent, px(400), px(height), bg)
        self.data, self.highlight, self.fmt = data, highlight, fmt

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or not self.data:
            return
        left, right, top, bottom = px(44), px(8), px(26), px(30)
        peak = max([v for _, v in self.data] + [1])
        step = 10 ** (len(str(int(peak))) - 1)
        top_val = ((peak // step) + 1) * step if peak % step else peak
        top_val = max(top_val, 1)
        plot_h = h - top - bottom
        for i in range(5):
            y = top + plot_h * i / 4
            val = top_val * (1 - i / 4)
            self.create_line(left, y, w - right, y, fill=C.border, dash=(2, 4) if 0 < i < 4 else ())
            self.create_text(left - px(8), y, text=_short(val), font=F["tiny"], fill=C.text_faint,
                             anchor="e")
        n = len(self.data)
        slot = (w - left - right) / n
        bar_w = min(px(46), slot * 0.56)
        for i, (label, value) in enumerate(self.data):
            cx = left + slot * (i + 0.5)
            full = plot_h * value / top_val
            bh = full * self.progress
            is_hi = (i == self.highlight)
            color = C.primary if is_hi else mix(C.primary, C.surface, 0.62)
            if bh > 1:
                round_rect(self, cx - bar_w / 2, top + plot_h - bh, cx + bar_w / 2,
                           top + plot_h, min(px(8), bar_w / 2), fill=color, outline="")
            if self.progress > 0.92:
                txt = self.fmt(value) if value else "-"
                self.create_text(cx, top + plot_h - bh - px(10), text=txt, font=F["smallb"],
                                 fill=C.text if value else C.text_faint)
            self.create_text(cx, h - bottom / 2 + px(2), text=label, font=F["small"],
                             fill=C.text if is_hi else C.text_muted)


class HBarList(_Animated):
    """Ranked horizontal bars. data: list of (label, value, value_text)."""

    def __init__(self, parent, data, row_h=44, bg=None, empty="No data yet."):
        self.data, self.row_h, self.empty = data, px(row_h), empty
        super().__init__(parent, px(300), max(self.row_h * max(len(data), 1), px(60)), bg)

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        if w < 50:
            return
        if not self.data:
            self.create_text(w / 2, px(30), text=self.empty, font=F["body"], fill=C.text_faint)
            return
        peak = max(v for _, v, _ in self.data) or 1
        for i, (label, value, text) in enumerate(self.data):
            y = i * self.row_h
            self.create_text(0, y + px(11), text=label, font=F["bodyb"], fill=C.text, anchor="w")
            self.create_text(w, y + px(11), text=text, font=F["smallb"], fill=C.text_muted,
                             anchor="e")
            bar_y, bar_h = y + px(24), px(10)
            round_rect(self, 0, bar_y, w, bar_y + bar_h, bar_h / 2, fill=C.surface_alt, outline="")
            fill_w = (w * value / peak) * self.progress
            if fill_w > bar_h:
                shade = mix(C.primary, C.accent, 0.35 if i == 0 else 0.0)
                round_rect(self, 0, bar_y, fill_w, bar_y + bar_h, bar_h / 2,
                           fill=shade if i == 0 else mix(C.primary, C.surface, 0.3 * i / 2.5),
                           outline="")


class Gauge(_Animated):
    """Semi-circular gauge, 0-100%."""

    def __init__(self, parent, percent, size=210, caption="", bg=None):
        super().__init__(parent, px(size), int(px(size) * 0.66), bg)
        self.percent, self.caption = max(0.0, min(percent, 100.0)), caption

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 40:
            return
        thick = px(16)
        pad = thick / 2 + px(4)
        d = min(w - 2 * pad, 2 * (h - pad))
        cx = w / 2
        box = (cx - d / 2, pad, cx + d / 2, pad + d)
        self.create_arc(*box, start=0, extent=180, style="arc", width=thick, outline=C.surface_alt)
        extent = 180 * self.percent / 100 * self.progress
        if extent > 0.5:
            tone = C.primary if self.percent < 85 else C.warning
            self.create_arc(*box, start=180, extent=-extent, style="arc", width=thick, outline=tone)
        shown = self.percent * self.progress
        self.create_text(cx, pad + d / 2 - px(14), text=f"{shown:.0f}%", font=F["kpi"], fill=C.text)
        if self.caption:
            self.create_text(cx, pad + d / 2 + px(14), text=self.caption, font=F["small"],
                             fill=C.text_muted)


class Donut(_Animated):
    """Donut with legend. segments: list of (label, value, colour)."""

    def __init__(self, parent, segments, size=170, center_label="jobs", bg=None):
        self.segments = [s for s in segments]
        self.center_label = center_label
        super().__init__(parent, px(size), px(size), bg)

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 40:
            return
        total = sum(v for _, v, _ in self.segments)
        thick = px(20)
        pad = thick / 2 + px(3)
        d = min(w, h) - 2 * pad
        box = (w / 2 - d / 2, h / 2 - d / 2, w / 2 + d / 2, h / 2 + d / 2)
        if total <= 0:
            self.create_oval(*box, outline=C.surface_alt, width=thick)
        else:
            start = 90.0
            for _, value, color in self.segments:
                if value <= 0:
                    continue
                extent = -360.0 * value / total * self.progress
                self.create_arc(*box, start=start, extent=extent - (0 if len(
                    [s for s in self.segments if s[1] > 0]) == 1 else 0.0), style="arc",
                    width=thick, outline=color)
                start += extent
        self.create_text(w / 2, h / 2 - px(8), text=f"{total * self.progress:.0f}", font=F["kpi_s"],
                         fill=C.text)
        self.create_text(w / 2, h / 2 + px(14), text=self.center_label, font=F["small"],
                         fill=C.text_muted)
