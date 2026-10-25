"""Animated launch screen: the car glides in, a light sweeps over it, the
name types out, and a progress line fills before the app appears."""
import tkinter as tk

from app import config
from app.ui import anim, brand
from app.ui.theme import F, hex_to_rgb, mix, px

NAVY_TOP, NAVY_BOTTOM = "#0E2547", "#060E1D"
AQUA = "#22D3EE"
W, H = 680, 400


class Splash(tk.Toplevel):
    def __init__(self, root, on_done, ms=2900):
        super().__init__(root)
        self.root, self.on_done = root, on_done
        self.overrideredirect(True)
        self.configure(bg=NAVY_BOTTOM)
        w, h = px(W), px(H)
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2 - px(20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0, bd=0, bg=NAVY_BOTTOM)
        self.canvas.pack()
        self._sw, self._sh = w, h
        self._alpha_ok = True
        self._set_alpha(0.0)
        self._gradient()
        scale = px(1) * 0.78
        self._scale = scale
        self._car_x = (w - brand.CAR_W * scale) / 2
        self._car_y = h * 0.20
        self._shine_id = None
        self._title = config.APP_NAME.upper()
        self._title_ids = []
        self._tag_id = None
        self._bar_id = None
        self.lift()
        self.update_idletasks()
        self._run(ms)

    # ---- helpers
    def _set_alpha(self, value):
        try:
            self.attributes("-alpha", value)
        except tk.TclError:
            self._alpha_ok = False

    def _gradient(self):
        steps = 80
        band = self._sh / steps
        for i in range(steps):
            self.canvas.create_rectangle(0, i * band, self._sw, (i + 1) * band + 1, outline="",
                                         fill=mix(NAVY_TOP, NAVY_BOTTOM, i / steps))

    def _car(self, offset_x, k):
        self.canvas.delete("car")
        self.canvas.delete("ground")
        gx = self._car_x + offset_x + brand.CAR_W * self._scale / 2
        gy = self._car_y + 112 * self._scale
        for i in range(5):
            self.canvas.create_oval(gx - (210 - i * 22) * self._scale, gy - (4 - i * 0.4) * self._scale + i,
                                    gx + (210 - i * 22) * self._scale, gy + (12 - i) * self._scale,
                                    outline="", fill=mix(NAVY_BOTTOM, "#000000", 0.14 * k), tags="ground")
        shade = mix(NAVY_BOTTOM, "#E9F4FA", k)
        glass = mix(NAVY_BOTTOM, "#0F3C58", k)
        tire = mix(NAVY_BOTTOM, "#0A1424", k)
        rim = mix(NAVY_BOTTOM, "#9FB6CC", k)
        brand.draw_car(self.canvas, self._car_x + offset_x, self._car_y, self._scale,
                       shade, glass, tire, rim)

    def _shine(self, design_x):
        if self._shine_id is not None:
            self.canvas.delete(self._shine_id)
            self._shine_id = None
        poly = brand.shine_polygon(design_x)
        if len(poly) >= 3:
            flat = []
            for px_, py_ in poly:
                flat += [self._car_x + px_ * self._scale, self._car_y + py_ * self._scale]
            self._shine_id = self.canvas.create_polygon(*flat, fill=AQUA, outline="", stipple="")
            self.canvas.itemconfigure(self._shine_id, fill=mix("#E9F4FA", AQUA, 0.55))

    # ---- timeline
    def _run(self, total):
        cx = self._sw / 2
        base_y = self._sh * 0.66
        letters = len(self._title)
        track_w = self._sw * 0.34
        bar_y = self._sh - px(46)
        self.canvas.create_line(cx - track_w / 2, bar_y, cx + track_w / 2, bar_y,
                                fill=mix(NAVY_BOTTOM, "#FFFFFF", 0.1), width=px(3), capstyle="round")
        self._bar_id = self.canvas.create_line(cx - track_w / 2, bar_y, cx - track_w / 2, bar_y,
                                               fill=AQUA, width=px(3), capstyle="round")
        spacing = px(22)
        start_x = cx - (letters - 1) * spacing / 2
        for i, ch in enumerate(self._title):
            self._title_ids.append(self.canvas.create_text(
                start_x + i * spacing, base_y, text=ch, font=F["h1"], fill=NAVY_BOTTOM))
        self._tag_id = self.canvas.create_text(cx, base_y + px(38), text=config.SHOP_TAGLINE,
                                               font=F["body"], fill=NAVY_BOTTOM)

        def timeline(t):
            ms = t * total
            # window fade in
            if self._alpha_ok:
                self._set_alpha(min(1.0, ms / 380.0))
            # car glide + colour
            k = anim.ease_out(min(1.0, ms / 900.0))
            self._car(-px(120) * (1 - k), k)
            # shine sweep 1000 -> 1800ms
            if 1000 <= ms <= 1800:
                u = (ms - 1000) / 800.0
                self._shine(-60 + 520 * anim.ease_in_out(u))
            elif self._shine_id is not None:
                self.canvas.delete(self._shine_id)
                self._shine_id = None
            # letters 500 -> 1500ms
            for i, item in enumerate(self._title_ids):
                u = min(1.0, max(0.0, (ms - 500 - i * 55) / 260.0))
                self.canvas.itemconfigure(item, fill=mix(NAVY_BOTTOM, "#FFFFFF", anim.ease_out(u)))
            # tagline 1500 -> 2000ms
            u = min(1.0, max(0.0, (ms - 1500) / 500.0))
            self.canvas.itemconfigure(self._tag_id, fill=mix(NAVY_BOTTOM, "#8FB3CF", u))
            # progress
            p = min(1.0, ms / (total - 250.0))
            self.canvas.coords(self._bar_id, cx - track_w / 2, bar_y,
                               cx - track_w / 2 + track_w * p, bar_y)

        anim.tween(self, total, timeline, done=self._fade_out, ease=lambda t: t)

    def _fade_out(self):
        def step(t):
            if self._alpha_ok:
                self._set_alpha(1.0 - t)
        anim.tween(self, 260, step, done=self._finish, ease=lambda t: t)

    def _finish(self):
        self.destroy()
        self.on_done()
