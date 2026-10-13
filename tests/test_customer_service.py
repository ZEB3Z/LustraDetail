"""Customer and vehicle registration rules."""
import pytest

from app.exceptions import NotFoundError, ValidationError


def test_register_customer(stack):
    customer = stack.customers.register("Test Person", "09998887776")
    assert customer.id == 5                     # seed data has 4 customers
    assert customer.name == "Test Person"


def test_duplicate_phone_rejected(stack):
    with pytest.raises(ValidationError):
        stack.customers.register("Someone Else", "09171234567")   # Juan's phone


def test_invalid_phone_rejected(stack):
    with pytest.raises(ValidationError):
        stack.customers.register("Valid Name", "not-a-phone")


def test_add_vehicle_and_duplicate_plate(stack):
    vehicle = stack.customers.add_vehicle(1, "XYZ 9999", "Honda", "City",
                                          2023, "White", "sedan")
    assert vehicle.id == 5
    with pytest.raises(ValidationError):
        stack.customers.add_vehicle(2, "xyz 9999", "Honda", "City",
                                    2023, "White", "sedan")


def test_invalid_year_rejected(stack):
    with pytest.raises(ValidationError):
        stack.customers.add_vehicle(1, "QQQ 1111", "Honda", "City",
                                    "1800", "White", "sedan")


def test_invalid_vehicle_type_rejected(stack):
    with pytest.raises(ValidationError):
        stack.customers.add_vehicle(1, "QQQ 2222", "Honda", "City",
                                    2023, "White", "truck")


def test_vehicle_must_belong_to_customer_when_booking(stack):
    with pytest.raises(ValidationError):
        stack.bookings.create_booking(1, 2, ["SVC001"])   # vehicle 2 is Maria's
