"""Inventory: stock checks, per-job deductions, restocking, low-stock alerts."""
from app.exceptions import InventoryError, ValidationError
from app.utils.validation import to_float


class InventoryService:
    def __init__(self, inventory_repo):
        self.inventory = inventory_repo

    def all(self):
        return self.inventory.all()

    def get(self, item_id):
        return self.inventory.get(item_id)

    def low_stock(self):
        return [i for i in self.all() if i.is_low]

    def check_materials(self, materials):
        """Raise InventoryError if the shop cannot cover `materials`."""
        materials = materials or []
        shortages = []
        for entry in materials:
            item = self.inventory.get(entry["item_id"])
            needed = float(entry["qty"])
            if item.stock + 1e-9 < needed:
                shortages.append(
                    f"{item.name}: need {needed:g} {item.unit}, only {item.stock:g} {item.unit} left"
                )
        if shortages:
            raise InventoryError(
                "Not enough stock for this job:\n  - " + "\n  - ".join(shortages)
            )

    def consume(self, materials):
        """Deduct materials from stock (called when a job starts)."""
        materials = materials or []
        self.check_materials(materials)
        for entry in materials:
            item = self.inventory.get(entry["item_id"])
            item.stock = round(item.stock - float(entry["qty"]), 4)
            self.inventory.update(item)

    def restock(self, item_id, quantity):
        quantity = to_float(quantity, "Restock quantity", minimum=0.01)
        item = self.inventory.get(item_id)
        item.stock = round(item.stock + quantity, 4)
        return self.inventory.update(item)
