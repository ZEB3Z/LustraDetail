"""Checkout: balances, deposits, change, receipts, and history updates."""
import pytest

from app import config
from app.exceptions import PaymentError


def _make_done(stack, tomorrow_at, deposit=0.0):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"],
                                        start_dt=tomorrow_at(9),
                                        deposit=deposit)
    stack.bookings.start_job(appt.id)
    return stack.bookings.complete_job(appt.id)


def test_checkout_cash_with_change(stack, tomorrow_at):
    done = _make_done(stack, tomorrow_at)
    appt, receipt_path, change = stack.payments.checkout(
        done.id, "cash", 500.0, "Mara Santos")
    assert appt.status == config.STATUS_PAID
    assert change == 150.0                       # 500 - 350
    assert receipt_path.exists()
    assert "Basic Wash" in receipt_path.read_text(encoding="utf-8")


def test_checkout_short_cash_rejected(stack, tomorrow_at):
    done = _make_done(stack, tomorrow_at)
    with pytest.raises(PaymentError):
        stack.payments.checkout(done.id, "cash", 100.0)


def test_checkout_only_when_done(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    with pytest.raises(PaymentError):
        stack.payments.checkout(appt.id, "cash", 350.0)


def test_non_cash_methods_record_balance(stack, tomorrow_at):
    done = _make_done(stack, tomorrow_at)
    appt, receipt_path, change = stack.payments.checkout(done.id, "gcash")
    assert appt.payment["amount"] == 350.0
    assert change == 0.0


def test_deposit_reduces_balance(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"],
                                        start_dt=tomorrow_at(9), deposit=100.0)
    stack.bookings.start_job(appt.id)
    stack.bookings.complete_job(appt.id)

    paid, receipt_path, change = stack.payments.checkout(appt.id, "cash", 300.0)
    assert paid.payment["balance"] == 250.0       # 350 - 100 deposit
    assert change == 50.0
    assert "Amount due" in receipt_path.read_text(encoding="utf-8")


def test_checkout_marks_history_paid(stack, tomorrow_at):
    from app.storage.repositories import HistoryRepository
    done = _make_done(stack, tomorrow_at)
    stack.payments.checkout(done.id, "gcash")
    entry = HistoryRepository().for_appointment(done.id)
    assert entry is not None and entry.paid is True


def test_double_checkout_rejected(stack, tomorrow_at):
    done = _make_done(stack, tomorrow_at)
    stack.payments.checkout(done.id, "gcash")
    with pytest.raises(PaymentError):
        stack.payments.checkout(done.id, "gcash")


def test_invalid_method_rejected(stack, tomorrow_at):
    from app.exceptions import ValidationError
    done = _make_done(stack, tomorrow_at)
    with pytest.raises(ValidationError):
        stack.payments.checkout(done.id, "monopoly money")
