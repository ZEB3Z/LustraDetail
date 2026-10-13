"""Inventory: consumption, restocking, low-stock flags, fail-safes."""
import pytest

from app.exceptions import InventoryError, NotFoundError, ValidationError


def test_restock_adds_quantity(stack):
    item = stack.inventory.restock("SHMP01", 5)
    assert item.stock == 25.0


def test_restock_rejects_bad_quantity(stack):
    with pytest.raises(ValidationError):
        stack.inventory.restock("SHMP01", 0)
    with pytest.raises(ValidationError):
        stack.inventory.restock("SHMP01", -3)


def test_consume_deducts_stock(stack):
    stack.inventory.consume([{"item_id": "MICF01", "qty": 10}])
    assert stack.inventory.get("MICF01").stock == 40.0


def test_consume_insufficient_raises_with_details(stack):
    with pytest.raises(InventoryError) as exc:
        stack.inventory.consume([{"item_id": "CERM01", "qty": 99}])
    assert "Ceramic Coating Kit" in str(exc.value)


def test_unknown_item_raises(stack):
    with pytest.raises(NotFoundError):
        stack.inventory.get("NOPE01")


def test_low_stock_flag(stack):
    stack.inventory.consume([{"item_id": "SHMP01", "qty": 20}])   # stock -> 0
    low = stack.inventory.low_stock()
    assert any(i.id == "SHMP01" for i in low)
