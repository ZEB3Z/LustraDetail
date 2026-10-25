"""Vector icons drawn with Canvas primitives (no image files, no fonts).

Every icon lives on a 24x24 grid and is drawn as strokes so it scales and
recolours cleanly in both themes.
"""
import math


def _circle(cx, cy, r):
    return ("oval", cx - r, cy - r, cx + r, cy + r)


def _moon_points():
    """Crescent = outer circle minus an offset inner circle."""
    c1, r1 = (12.0, 12.0), 9.0
    c2, r2 = (17.0, 8.0), 7.2
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dy)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0))
    mx, my = c1[0] + a * dx / d, c1[1] + a * dy / d
    p1 = (mx + h * dy / d, my - h * dx / d)
    p2 = (mx - h * dy / d, my + h * dx / d)
    ang = lambda p, c: math.atan2(p[1] - c[1], p[0] - c[0])
    a1, a2 = ang(p1, c1), ang(p2, c1)
    if a2 < a1:
        a2 += 2 * math.pi
    pts = []
    n = 18
    for i in range(n + 1):                    # outer arc the long way round
        t = a1 + (a2 - a1 - 2 * math.pi) * i / n if False else a2 + (a1 + 2 * math.pi - a2) * i / n
        pts.append((c1[0] + r1 * math.cos(t), c1[1] + r1 * math.sin(t)))
    b1, b2 = ang(p1, c2), ang(p2, c2)
    if b1 < b2:
        b1 += 2 * math.pi
    for i in range(n + 1):                    # inner arc back
        t = b1 + (b2 - b1) * i / n
        pts.append((c2[0] + r2 * math.cos(t), c2[1] + r2 * math.sin(t)))
    return pts


def _sun_rays():
    rays = []
    for deg in range(0, 360, 45):
        a = math.radians(deg)
        rays.append(("line", [(12 + 7.5 * math.cos(a), 12 + 7.5 * math.sin(a)),
                              (12 + 10 * math.cos(a), 12 + 10 * math.sin(a))]))
    return rays


ICONS = {
    "dashboard": [("rect", 3, 3, 10, 11), ("rect", 14, 3, 21, 8), ("rect", 3, 15, 10, 21),
                  ("rect", 14, 12, 21, 21)],
    "calendar": [("rect", 3, 5, 21, 21), ("line", [(3, 10), (21, 10)]),
                 ("line", [(8, 3), (8, 7)]), ("line", [(16, 3), (16, 7)])],
    "user": [_circle(12, 8, 4), ("line", [(4, 21), (5, 17), (9, 14.5), (15, 14.5),
                                          (19, 17), (20, 21)], True)],
    "users": [_circle(9, 8, 3.6), ("line", [(2.5, 20), (3.5, 16.5), (7, 14.5), (11, 14.5),
                                            (14.5, 16.5), (15.5, 20)], True),
              ("line", [(15.5, 4.8), (18.5, 6), (18.5, 10), (15.5, 11.2)], True),
              ("line", [(17.5, 14.5), (20, 15.5), (21.5, 19)], True)],
    "tag": [("line", [(3, 12.5), (12.5, 3), (21, 3), (21, 11.5), (11.5, 21), (3, 12.5)]),
            _circle(16, 8, 1.4)],
    "box": [("line", [(12, 3), (21, 7.5), (21, 16.5), (12, 21), (3, 16.5), (3, 7.5), (12, 3)]),
            ("line", [(3, 7.5), (12, 12), (21, 7.5)]), ("line", [(12, 12), (12, 21)])],
    "chart": [("line", [(3, 3), (3, 21), (21, 21)]), ("rect", 7, 12, 10, 18),
              ("rect", 12.5, 8, 15.5, 18), ("rect", 18, 4, 21, 18)],
    "shield": [("line", [(12, 3), (20, 6), (20, 12), (12, 21), (4, 12), (4, 6), (12, 3)]),
               ("line", [(8.5, 12), (11, 14.5), (15.5, 9.5)])],
    "car": [("line", [(3, 16), (4, 11), (7, 7), (17, 7), (20, 11), (21, 16), (21, 18),
                      (3, 18), (3, 16)]), ("line", [(4, 11), (20, 11)]),
            _circle(7.5, 18, 2), _circle(16.5, 18, 2)],
    "plus": [("line", [(12, 5), (12, 19)]), ("line", [(5, 12), (19, 12)])],
    "check": [("line", [(5, 12.5), (10, 17.5), (19, 7)])],
    "x": [("line", [(6, 6), (18, 18)]), ("line", [(18, 6), (6, 18)])],
    "search": [_circle(10.5, 10.5, 6.5), ("line", [(15.5, 15.5), (21, 21)])],
    "logout": [("line", [(10, 4), (4, 4), (4, 20), (10, 20)]), ("line", [(9, 12), (20, 12)]),
               ("line", [(16, 8), (20, 12), (16, 16)])],
    "sun": [_circle(12, 12, 4.2)] + _sun_rays(),
    "moon": [("poly", _moon_points())],
    "play": [("poly", [(8, 5), (19, 12), (8, 19)])],
    "flag": [("line", [(5, 21), (5, 3)]), ("line", [(5, 4), (19, 4), (16, 8.5), (19, 13),
                                                    (5, 13)])],
    "clock": [_circle(12, 12, 9), ("line", [(12, 7), (12, 12), (15.5, 14)])],
    "alert": [("line", [(12, 3), (22, 20), (2, 20), (12, 3)]), ("line", [(12, 9.5), (12, 14)]),
              ("line", [(12, 16.8), (12, 17.2)])],
    "info": [_circle(12, 12, 9), ("line", [(12, 11), (12, 17)]), ("line", [(12, 7.3), (12, 7.7)])],
    "receipt": [("line", [(5, 3), (5, 21), (8, 19), (10.5, 21), (13, 19), (15.5, 21), (19, 19),
                          (19, 3), (5, 3)]), ("line", [(8.5, 8), (15.5, 8)]),
                ("line", [(8.5, 12), (15.5, 12)])],
    "card": [("rect", 3, 6, 21, 18), ("line", [(3, 10.5), (21, 10.5)]),
             ("line", [(6.5, 15), (10, 15)])],
    "home": [("line", [(4, 11), (12, 4), (20, 11), (20, 20), (4, 20), (4, 11)]),
             ("line", [(10, 20), (10, 14), (14, 14), (14, 20)])],
    "ban": [_circle(12, 12, 9), ("line", [(5.6, 5.6), (18.4, 18.4)])],
    "chevron_left": [("line", [(15, 5), (8, 12), (15, 19)])],
    "chevron_right": [("line", [(9, 5), (16, 12), (9, 19)])],
    "user_plus": [_circle(9.5, 8, 3.8), ("line", [(2.5, 20.5), (3.5, 17), (7, 14.8), (12, 14.8),
                                                   (15, 16.5)], True),
                  ("line", [(18, 9), (18, 15)]), ("line", [(15, 12), (21, 12)])],
    "refresh": [("line", [(20, 7), (20, 3)]), ("line", [(20, 7), (16, 7)]),
                ("line", [(19.5, 7.5), (17.5, 5), (14, 3.5), (10, 4), (6, 7), (4, 11.5),
                          (4.5, 15.5), (7, 19), (11, 20.5), (15, 20), (18.5, 17.5)], True)],
    "wrench": [("line", [(14.5, 3.5), (18, 3.5), (15.5, 7), (17, 8.5), (20.5, 5.5), (20.5, 9.5),
                         (17.5, 13), (13.5, 12.5), (6, 20), (4, 18), (11.5, 10.5), (11, 6.5),
                         (14.5, 3.5)])],
    "sparkle": [("poly", [(12, 2), (14, 9.5), (21.5, 12), (14, 14.5), (12, 22), (10, 14.5),
                          (2.5, 12), (10, 9.5)])],
    "phone": [("rect", 7, 2.5, 17, 21.5), ("line", [(11, 18.5), (13, 18.5)])],
    "edit": [("line", [(4, 20), (4.5, 16), (16, 4.5), (19.5, 8), (8, 19.5), (4, 20)]),
             ("line", [(13.5, 7), (17, 10.5)])],
    "mail": [("rect", 3, 5, 21, 19), ("line", [(3, 7), (12, 13.5), (21, 7)])],
    "key": [_circle(8, 15, 4.2), ("line", [(11, 12), (20, 3.5)]), ("line", [(16.5, 7), (19, 9.5)])],
    "lock": [("rect", 5, 11, 19, 21), ("line", [(8, 11), (8, 7.5), (10, 4.8), (14, 4.8),
                                                 (16, 7.5), (16, 11)])],
    "drop": [("line", [(12, 3), (18, 11), (18.6, 15), (16, 19.3), (12, 21), (8, 19.3),
                       (5.4, 15), (6, 11), (12, 3)], True)],
}


def draw(canvas, name, x, y, size, color, width=None, tag="icon"):
    """Draw icon `name` with its top-left corner at (x, y), `size` px square."""
    scale = size / 24.0
    width = width or max(1.5, size / 11.0)

    def pt(p):
        return (x + p[0] * scale, y + p[1] * scale)

    ids = []
    for prim in ICONS[name]:
        kind = prim[0]
        if kind == "line":
            flat = [c for p in prim[1] for c in pt(p)]
            smooth = len(prim) > 2 and prim[2]
            ids.append(canvas.create_line(*flat, fill=color, width=width, smooth=smooth,
                                          capstyle="round", joinstyle="round", tags=tag))
        elif kind == "poly":
            flat = [c for p in prim[1] for c in pt(p)]
            ids.append(canvas.create_polygon(*flat, outline=color, fill="", width=width,
                                             joinstyle="round", tags=tag))
        elif kind == "rect":
            x1, y1 = pt((prim[1], prim[2]))
            x2, y2 = pt((prim[3], prim[4]))
            ids.append(canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=width,
                                               tags=tag))
        elif kind == "oval":
            x1, y1 = pt((prim[1], prim[2]))
            x2, y2 = pt((prim[3], prim[4]))
            ids.append(canvas.create_oval(x1, y1, x2, y2, outline=color, width=width, tags=tag))
    return ids
