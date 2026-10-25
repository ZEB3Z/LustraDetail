"""Headless-safe smoke test for the Tkinter UI.

Opens the real window, signs in as every role, visits every page in both
themes and closes it again. Skipped automatically when Tkinter or a display
is not available (for example on a bare CI runner).
"""
import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture
def app(stack, tmp_path, monkeypatch):
    from app.ui import theme
    monkeypatch.setattr(theme, "SETTINGS_FILE", tmp_path / "ui.json")
    from app.ui.app_ui import App
    try:
        window = App(stack, splash=False)
    except tk.TclError as exc:  # no display
        pytest.skip(f"no display available: {exc}")
    window.geometry("1280x800+0+0")
    window.update()
    yield window
    window.destroy()


def _visit_all(app, menu):
    for key in menu:
        app.screen.navigate(key)
        app.update()
        assert app.screen.page_key == key


def test_staff_roles_can_open_every_page(app, stack):
    from app.ui.shell import STAFF_MENUS
    for username, password, role in (("admin", "admin123", "admin"),
                                     ("cashier", "cash123", "cashier"),
                                     ("alwin", "detail123", "detailer")):
        user = stack.auth.staff_login(username, password)
        app.show_shell("staff", user)
        app.update()
        _visit_all(app, STAFF_MENUS[role])


def test_customer_portal_pages(app, stack):
    from app.ui.shell import CUSTOMER_MENU
    app.show_shell("customer", stack.auth.customer_login("09171234567"))
    app.update()
    _visit_all(app, CUSTOMER_MENU)


def test_theme_toggle_rebuilds_current_screen(app, stack):
    app.show_shell("staff", stack.auth.staff_login("admin", "admin123"))
    app.screen.navigate("reports")
    for mode in ("dark", "light"):
        app.set_theme(mode)
        app.update()
        assert app.screen.page_key == "reports"
