"""Plain-ASCII text formatting: money and tables (no unicode box drawing)."""


def money(value):
    return f"Php {float(value):,.2f}"


def _clip(text, width):
    text = str(text)
    return text if len(text) <= width else text[: width - 3] + "..."


def make_table(headers, rows, aligns=None):
    """Render an ASCII table like:

        ID  Name        Total
        --  ----        -----
        1   Juan        Php 100.00
    """
    aligns = aligns or ["<"] * len(headers)
    headers = [str(h) for h in headers]
    clipped = [[_clip(cell, 28) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in clipped:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def render(cells):
        out = []
        for cell, width, align in zip(cells, widths, aligns):
            cell = str(cell)
            out.append(cell.ljust(width) if align == "<" else cell.rjust(width))
        return "  ".join(out)

    lines = [render(headers), "  ".join("-" * w for w in widths)]
    lines.extend(render(row) for row in clipped)
    return "\n".join(lines)


def dotted(label, value_str, width=50):
    """'Basic Wash ......................... Php 350.00' style line."""
    label, value_str = str(label), str(value_str)
    dots = max(3, width - len(label) - len(value_str) - 2)
    return f"{label} {'.' * dots} {value_str}"
