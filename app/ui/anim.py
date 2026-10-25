"""Tiny animation helpers built on Tk's `after` (no threads, no libraries)."""
import time
import tkinter as tk


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def ease_out_back(t):
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class Tween:
    """Calls step(eased_progress) about 60 times a second, then done()."""

    def __init__(self, widget, ms, step, done=None, ease=ease_out, delay=0):
        self.widget, self.ms, self.step = widget, max(1, ms), step
        self.done, self.ease = done, ease
        self._job = None
        self._start = None
        self._cancelled = False
        if delay:
            self._job = widget.after(delay, self._begin)
        else:
            self._begin()

    def _begin(self):
        self._start = time.perf_counter()
        self._tick()

    def _tick(self):
        if self._cancelled:
            return
        try:
            if not self.widget.winfo_exists():
                return
            t = min(1.0, (time.perf_counter() - self._start) * 1000.0 / self.ms)
            self.step(self.ease(t))
            if t >= 1.0:
                if self.done:
                    self.done()
                return
            self._job = self.widget.after(15, self._tick)
        except tk.TclError:
            pass                      # widget was destroyed mid-animation

    def cancel(self):
        self._cancelled = True
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except tk.TclError:
                pass


def tween(widget, ms, step, done=None, ease=ease_out, delay=0):
    return Tween(widget, ms, step, done, ease, delay)
