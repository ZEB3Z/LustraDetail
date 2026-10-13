"""Quote math: base prices, package discounts, promos, and validation."""
import pytest

from app.exceptions import NotFoundError, ValidationError


def test_basic_quote(stack):
    quote = stack.catalog.build_quote("suv", ["SVC001"])
    assert quote["total"] == 450.0
    assert quote["duration_minutes"] == 60
    assert quote["items"][0]["name"] == "Basic Wash"


def test_matrix_pricing_differs_by_vehicle(stack):
    sedan = stack.catalog.build_quote("sedan", ["SVC001"])
    moto = stack.catalog.build_quote("motorcycle", ["SVC001"])
    assert sedan["total"] == 350.0
    assert moto["total"] == 250.0


def test_add_ons_add_price_and_time(stack):
    quote = stack.catalog.build_quote("sedan", ["SVC001"], ["ADD003"])
    assert quote["total"] == 350.0 + 200.0
    assert quote["duration_minutes"] == 45 + 15


def test_package_discount(stack):
    # PKG001 = SVC001 (350) + SVC002 (1500) = 1850, minus 10% = 1665
    quote = stack.catalog.build_quote("sedan", package_id="PKG001")
    assert quote["subtotal"] == 1850.0
    assert quote["package_discount_amount"] == 185.0
    assert quote["total"] == 1665.0


def test_promo_discount(stack):
    quote = stack.catalog.build_quote("sedan", ["SVC001"], promo_code="LUSTRA10")
    assert quote["total"] == 315.0


def test_promo_stacks_after_package_discount(stack):
    # PKG001 (1665 after package) then 10% promo = 1665 - 166.5
    quote = stack.catalog.build_quote("sedan", package_id="PKG001",
                                     promo_code="LUSTRA10")
    assert quote["promo_discount_amount"] == 166.5
    assert quote["total"] == 1498.5


def test_quote_includes_aggregated_materials(stack):
    quote = stack.catalog.build_quote("sedan", ["SVC001", "SVC002"])
    materials = {m["item_id"]: m["qty"] for m in quote["materials"]}
    assert materials["MICF01"] == 5      # 2 towels + 3 towels
    assert materials["SHMP01"] == pytest.approx(0.2)


def test_unknown_vehicle_type_raises(stack):
    with pytest.raises(ValidationError):
        stack.catalog.build_quote("truck", ["SVC001"])


def test_empty_selection_raises(stack):
    with pytest.raises(ValidationError):
        stack.catalog.build_quote("sedan", [])


def test_unknown_service_raises(stack):
    with pytest.raises(NotFoundError):
        stack.catalog.build_quote("sedan", ["SVC999"])


def test_invalid_promo_raises(stack):
    with pytest.raises(NotFoundError):
        stack.catalog.build_quote("sedan", ["SVC001"], promo_code="FAKE99")
