"""Brand artwork drawn in code: the car silhouette, shine sweep, logo mark."""
import math

from app.ui import icons
from app.ui.theme import C, mix, px
from app.ui.widgets import round_rect


def _arch(cx, base, r, steps=14):
    """Wheel-arch points from the left foot to the right foot."""
    return [(cx - r * math.cos(math.pi * i / steps), base - r * math.sin(math.pi * i / steps))
            for i in range(steps + 1)]


def _chaikin(points, rounds=2):
    """Corner-cutting: turns the polygon's hard corners into soft curves."""
    for _ in range(rounds):
        out = []
        for i, p in enumerate(points):
            q = points[(i + 1) % len(points)]
            out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        points = out
    return points


_BODY = None


def body_points():
    global _BODY
    if _BODY is None:
        base = 108
        top = [(12, base), (12, 93), (22, 84), (72, 78), (128, 70), (158, 47), (190, 35),
               (252, 33), (298, 47), (346, 64), (380, 74), (393, 89), (393, base)]
        arches = list(reversed(_arch(322, base, 29))) + list(reversed(_arch(92, base, 29)))
        _BODY = _chaikin(top, 1)[:-1] + arches
    return _BODY


GLASS = [(128, 66), (156, 47), (186, 38), (248, 37), (290, 52), (308, 64)]
WHEELS = [(92, 108), (322, 108)]
CAR_W, CAR_H = 402, 140


def draw_car(canvas, ox, oy, scale, body, glass, tire, rim, tag="car"):
    """Draw the car with its top-left at (ox, oy). Returns the body item id."""
    def tr(p):
        return (ox + p[0] * scale, oy + p[1] * scale)

    flat = [c for p in body_points() for c in tr(p)]
    body_id = canvas.create_polygon(*flat, fill=body, outline="", tags=tag)
    glass_pts = [c for p in GLASS for c in tr(p)]
    canvas.create_polygon(*glass_pts, fill=glass, outline="", tags=tag)
    x1, y1 = tr((208, 38))
    x2, y2 = tr((208, 66))
    canvas.create_line(x1, y1, x2, y2, fill=body, width=max(2, 3 * scale), tags=tag)
    # door line and accent stripe
    canvas.create_line(*tr((150, 72)), *tr((150, 104)), fill=mix(body, "#000000", 0.25),
                       width=max(1, 1.5 * scale), tags=tag)
    canvas.create_line(*tr((30, 84)), *tr((380, 82)), fill=mix(body, "#FFFFFF", 0.35),
                       width=max(1, 1.5 * scale), tags=tag)
    for wx, wy in WHEELS:
        cx, cy = tr((wx, wy))
        r = 24 * scale
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=tire, outline="", tags=tag)
        r2 = 14 * scale
        canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, fill=rim, outline="", tags=tag)
        r3 = 4.5 * scale
        canvas.create_oval(cx - r3, cy - r3, cx + r3, cy + r3, fill=tire, outline="", tags=tag)
    return body_id


# ---- shine sweep: clip the body polygon against a slanted band ------------
def _clip(subject, edge_a, edge_b):
    """Sutherland-Hodgman against one half-plane (keep the left of a->b)."""
    def inside(p):
        return (edge_b[0] - edge_a[0]) * (p[1] - edge_a[1]) - (edge_b[1] - edge_a[1]) * (p[0] - edge_a[0]) >= 0

    def cross(p, q):
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
        x3, y3, x4, y4 = edge_a[0], edge_a[1], edge_b[0], edge_b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = []
    for i, cur in enumerate(subject):
        prev = subject[i - 1]
        if inside(cur):
            if not inside(prev):
                out.append(cross(prev, cur))
            out.append(cur)
        elif inside(prev):
            out.append(cross(prev, cur))
    return out


def shine_polygon(center_x, band=46, slant=34):
    """Body polygon clipped to a slanted vertical band (design coordinates)."""
    top, bottom = 20, 120
    quad = [(center_x - band / 2 + slant, top), (center_x + band / 2 + slant, top),
            (center_x + band / 2, bottom), (center_x - band / 2, bottom)]
    poly = body_points()
    for i in range(4):
        poly = _clip(poly, quad[i], quad[(i + 1) % 4])
        if not poly:
            return []
    return poly


def logo_mark(canvas, x, y, size, bg=None):
    """Rounded aqua tile with a car and a sparkle."""
    s = size
    tile = round_rect(canvas, x, y, x + s, y + s, s * 0.28, fill=C.primary, outline="")
    icons.draw(canvas, "car", x + s * 0.2, y + s * 0.3, s * 0.6, "#FFFFFF", width=max(1.6, s / 16))
    sp = s * 0.26
    icons.draw(canvas, "sparkle", x + s * 0.62, y + s * 0.06, sp, C.accent if C.mode != "dark" else "#FFFFFF",
               width=max(1.2, s / 24))
    return tile
