"""The service catalog: prices, durations, quotes, packages and promos."""
from app.exceptions import NotFoundError, ValidationError
from app.utils.validation import clean, valid_vehicle_type


class CatalogService:
    def __init__(self, catalog_repo):
        self.catalog = catalog_repo

    # ------------------------------------------------------------ lists ----
    def services(self):
        return self.catalog.services()

    def add_ons(self):
        return self.catalog.add_ons()

    def packages(self):
        return self.catalog.packages()

    def promos(self):
        return self.catalog.promos()

    # ------------------------------------------------------------ lookups ---
    def get_service(self, service_id):
        for service in self.services():
            if service.id == service_id:
                return service
        raise NotFoundError(f"Service '{service_id}' was not found.")

    def get_add_on(self, add_on_id):
        for add_on in self.add_ons():
            if add_on.id == add_on_id:
                return add_on
        raise NotFoundError(f"Add-on '{add_on_id}' was not found.")

    def get_package(self, package_id):
        for package in self.packages():
            if package.id == package_id:
                return package
        raise NotFoundError(f"Package '{package_id}' was not found.")

    def get_promo(self, code):
        code = clean(code).upper()
        for promo in self.promos():
            if promo.code.upper() == code:
                return promo
        raise NotFoundError(f"Promo code '{code}' is not valid.")

    def price_of(self, service, vehicle_type):
        if vehicle_type not in service.prices:
            raise ValidationError(
                f"'{service.name}' is not offered for {vehicle_type} vehicles."
            )
        return float(service.prices[vehicle_type])

    def duration_of(self, service, vehicle_type):
        if vehicle_type not in service.durations:
            raise ValidationError(
                f"'{service.name}' has no duration set for {vehicle_type} vehicles."
            )
        return int(service.durations[vehicle_type])

    # ------------------------------------------------------------- quote ----
    def build_quote(self, vehicle_type, service_ids=None, add_on_ids=None,
                    package_id="", promo_code=""):
        """Compute the full price/duration breakdown for a booking.

        Returns a dict that is stored on the appointment, so later catalog
        edits never rewrite the price of an existing booking.
        """
        vtype = valid_vehicle_type(vehicle_type)
        service_ids = list(dict.fromkeys(service_ids or []))
        add_on_ids = list(dict.fromkeys(add_on_ids or []))
        package_id = clean(package_id).upper()

        if package_id:
            package = self.get_package(package_id)
            service_ids = list(package.service_ids)
        elif not service_ids:
            raise ValidationError("Select at least one service (or a package).")

        items, materials = [], {}
        subtotal, duration = 0.0, 0

        def add_materials(entries):
            for entry in entries:
                key = entry["item_id"]
                materials[key] = round(materials.get(key, 0.0) + float(entry["qty"]), 4)

        for sid in service_ids:
            service = self.get_service(sid)
            price = self.price_of(service, vtype)
            items.append({"kind": "service", "id": service.id, "name": service.name, "price": price})
            subtotal += price
            duration += self.duration_of(service, vtype)
            add_materials(service.materials)

        package_discount = 0.0
        if package_id:
            package_discount = round(subtotal * package.discount_percent / 100, 2)

        for aid in add_on_ids:
            add_on = self.get_add_on(aid)
            items.append({"kind": "add_on", "id": add_on.id, "name": add_on.name, "price": float(add_on.price)})
            subtotal += float(add_on.price)
            duration += int(add_on.duration)
            add_materials(add_on.materials)

        promo_discount = 0.0
        code = clean(promo_code).upper()
        if code:
            promo = self.get_promo(code)
            base = subtotal - package_discount
            promo_discount = round(base * promo.discount_percent / 100, 2)

        total = round(subtotal - package_discount - promo_discount, 2)
        if total < 0:
            total = 0.0

        return {
            "vehicle_type": vtype,
            "items": items,
            "materials": [{"item_id": k, "qty": v} for k, v in sorted(materials.items())],
            "subtotal": round(subtotal, 2),
            "package_id": package_id,
            "package_discount_amount": package_discount,
            "promo_code": code,
            "promo_discount_amount": promo_discount,
            "total": total,
            "duration_minutes": duration,
        }
