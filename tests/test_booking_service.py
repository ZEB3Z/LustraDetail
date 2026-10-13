"""Scheduling rules: conflicts, buffer, pipeline, and inventory fail-safes."""
import pytest
from datetime import timedelta

from app import config
from app.exceptions import BookingError, InventoryError, ValidationError
from app.utils import datetime_utils as dtu


def test_create_booking_sets_duration_and_total(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    assert appt.status == config.STATUS_BOOKED
    assert appt.scheduled_end == dtu.fmt(dtu.add_minutes(tomorrow_at(9), 45))
    assert appt.price_breakdown["total"] == 350.0


def test_past_time_rejected(stack):
    with pytest.raises(BookingError):
        stack.bookings.create_booking(1, 1, ["SVC001"],
                                     start_dt=dtu.now() - timedelta(hours=2))


def test_overlapping_booking_rejected(stack, tomorrow_at):
    stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    with pytest.raises(BookingError):
        stack.bookings.create_booking(2, 2, ["SVC001"], start_dt=tomorrow_at(9, 30))


def test_buffer_enforced_between_jobs(stack, tomorrow_at):
    stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    # first job ends 09:45; booking at 09:59 violates the 15-minute buffer
    with pytest.raises(BookingError):
        stack.bookings.create_booking(2, 2, ["SVC001"], start_dt=tomorrow_at(9, 59))
    # exactly 15 minutes after the end is allowed
    appt = stack.bookings.create_booking(2, 2, ["SVC001"], start_dt=tomorrow_at(10, 0))
    assert appt.status == config.STATUS_BOOKED


def test_cancelled_slot_is_freed(stack, tomorrow_at):
    first = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    stack.bookings.cancel(first.id)
    second = stack.bookings.create_booking(2, 2, ["SVC001"], start_dt=tomorrow_at(9))
    assert second.status == config.STATUS_BOOKED


def test_reschedule_only_when_booked(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    moved = stack.bookings.reschedule(appt.id, tomorrow_at(14))
    assert moved.scheduled_start == dtu.fmt(tomorrow_at(14))

    stack.bookings.start_job(appt.id)
    with pytest.raises(BookingError):
        stack.bookings.reschedule(appt.id, tomorrow_at(16))


def test_reschedule_conflicts_with_other_bookings(stack, tomorrow_at):
    first = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    stack.bookings.create_booking(2, 2, ["SVC001"], start_dt=tomorrow_at(11))
    with pytest.raises(BookingError):
        stack.bookings.reschedule(first.id, tomorrow_at(11, 15))


def test_no_show_requires_time_passed(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    with pytest.raises(BookingError):
        stack.bookings.mark_no_show(appt.id)      # still in the future


def test_deposit_cannot_exceed_total(stack, tomorrow_at):
    with pytest.raises(ValidationError):
        stack.bookings.create_booking(1, 1, ["SVC001"],
                                      start_dt=tomorrow_at(9), deposit=99999)


def test_walk_in_starts_now(stack):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=dtu.now())
    assert appt.status == config.STATUS_BOOKED


def test_full_pipeline_writes_history(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    stack.bookings.start_job(appt.id)
    assert appt.status == config.STATUS_IN_PROGRESS or True   # reload below
    started = stack.bookings.get(appt.id)
    assert started.status == config.STATUS_IN_PROGRESS

    stack.bookings.complete_job(appt.id)
    done = stack.bookings.get(appt.id)
    assert done.status == config.STATUS_DONE
    entry = None
    from app.storage.repositories import HistoryRepository
    for h in HistoryRepository().all():
        if h.appointment_id == appt.id:
            entry = h
    assert entry is not None and entry.paid is False


def test_starting_twice_rejected(stack, tomorrow_at):
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    stack.bookings.start_job(appt.id)
    with pytest.raises(BookingError):
        stack.bookings.start_job(appt.id)


def test_insufficient_stock_blocks_booking(stack, tomorrow_at):
    # drain the ceramic coating kits (SVC006 needs 1 kit each)
    stack.inventory.consume([{"item_id": "CERM01", "qty": 3}])
    with pytest.raises(InventoryError):
        stack.bookings.create_booking(1, 1, ["SVC006"], start_dt=tomorrow_at(9))


def test_start_job_deducts_inventory(stack, tomorrow_at):
    before = stack.inventory.get("SHMP01").stock
    appt = stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    stack.bookings.start_job(appt.id)
    after = stack.inventory.get("SHMP01").stock
    assert after == pytest.approx(before - 0.2)


def test_next_slots_skip_busy_times(stack, tomorrow_at):
    stack.bookings.create_booking(1, 1, ["SVC001"], start_dt=tomorrow_at(9))
    slots = stack.bookings.next_slots(45, count=6)
    assert slots, "expected at least one free slot"
    for slot in slots:
        assert slot >= dtu.now()
        # no suggested slot may sit on top of the existing 09:00 booking
        assert not (slot < tomorrow_at(9, 45) and tomorrow_at(9) < dtu.add_minutes(slot, 45))
