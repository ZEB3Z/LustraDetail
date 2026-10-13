"""Checkout, payment recording, and official receipt generation."""
from app import config
from app.exceptions import NotFoundError, PaymentError, ValidationError
from app.utils import datetime_utils as dtu
from app.utils.formatting import dotted, money
from app.utils.validation import clean, to_float

RECEIPT_WIDTH = 54


class PaymentService:
    def __init__(self, appointment_repo, customer_repo, vehicle_repo, history_repo):
        self.appointments = appointment_repo
        self.customers = customer_repo
        self.vehicles = vehicle_repo
        self.history = history_repo

    def checkout(self, appointment_id, method, amount_received=None, cashier_name=""):
        """DONE -> PAID. Records the payment, updates history, writes the receipt."""
        appt = self.appointments.get(appointment_id)
        if appt.status != config.STATUS_DONE:
            raise PaymentError("Only completed (DONE) jobs can be checked out.")

        method = clean(method).lower()
        if method not in config.PAYMENT_METHODS:
            raise ValidationError(
                f"Payment method must be one of: {', '.join(config.PAYMENT_METHODS)}."
            )

        breakdown = appt.price_breakdown
        total = float(breakdown.get("total", 0.0))
        balance = round(max(total - float(appt.deposit), 0.0), 2)

        amount, change = balance, 0.0
        if method == "cash":
            if amount_received is None:
                raise ValidationError("Amount received is required for cash payments.")
            received = to_float(amount_received, "Amount received", minimum=0.0)
            if received + 1e-9 < balance:
                raise PaymentError(
                    f"Amount received is less than the balance of {money(balance)}."
                )
            amount, change = received, round(received - balance, 2)

        receipt_file = f"receipt_{appt.id:04d}.txt"
        appt.payment = {
            "method": method,
            "amount": amount,
            "balance": balance,
            "deposit": appt.deposit,
            "paid_at": dtu.now_str(),
            "cashier": clean(cashier_name),
            "receipt_file": receipt_file,
        }
        appt.status = config.STATUS_PAID
        self.appointments.update(appt)

        entry = self.history.for_appointment(appt.id)
        if entry is not None:
            entry.paid = True
            self.history.update(entry)

        receipt_path = config.receipts_dir() / receipt_file
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(self._build_receipt(appt, change), encoding="utf-8")
        return appt, receipt_path, change

    # ------------------------------------------------------------- receipt ---
    def _build_receipt(self, appt, change):
        customer = self.customers.get(appt.customer_id)
        vehicle = self.vehicles.get(appt.vehicle_id)
        breakdown = appt.price_breakdown
        payment = appt.payment
        edge = "=" * RECEIPT_WIDTH
        thin = "-" * RECEIPT_WIDTH

        lines = [
            edge,
            config.SHOP_NAME.center(RECEIPT_WIDTH),
            f'"{config.SHOP_TAGLINE}"'.center(RECEIPT_WIDTH),
            config.SHOP_ADDRESS.center(RECEIPT_WIDTH),
            f"Tel: {config.SHOP_PHONE}".center(RECEIPT_WIDTH),
            edge,
            f"OFFICIAL RECEIPT".ljust(RECEIPT_WIDTH - 18) + f"No. {appt.id:05d}",
            thin,
            f"Customer : {customer.name}",
            f"Phone    : {customer.phone}",
            f"Vehicle  : {vehicle.describe()}",
            f"Paid at  : {payment['paid_at']}",
            f"Cashier  : {payment['cashier'] or '-'}",
            thin,
            "SERVICES",
        ]
        for item in breakdown.get("items", []):
            lines.append("  " + dotted(item["name"], money(item["price"]), RECEIPT_WIDTH - 2))
        lines.append(thin)
        lines.append("  " + dotted("Subtotal", money(breakdown.get("subtotal", 0.0)), RECEIPT_WIDTH - 2))
        if breakdown.get("package_discount_amount"):
            lines.append("  " + dotted("Package discount", f"-{money(breakdown['package_discount_amount'])}", RECEIPT_WIDTH - 2))
        if breakdown.get("promo_discount_amount"):
            label = f"Promo ({breakdown.get('promo_code', '')})"
            lines.append("  " + dotted(label, f"-{money(breakdown['promo_discount_amount'])}", RECEIPT_WIDTH - 2))
        lines.append("  " + dotted("TOTAL", money(breakdown.get("total", 0.0)), RECEIPT_WIDTH - 2))
        if appt.deposit:
            lines.append("  " + dotted("Deposit already paid", f"-{money(appt.deposit)}", RECEIPT_WIDTH - 2))
            lines.append("  " + dotted("Amount due", money(payment["balance"]), RECEIPT_WIDTH - 2))
        lines.append(thin)
        lines.append(f"Payment method : {payment['method']}")
        if payment["method"] == "cash":
            lines.append(f"Amount received: {money(payment['amount'])}")
            lines.append(f"Change         : {money(change)}")
        lines.append(thin)
        lines.append("Thank you for trusting LustraDetail!".center(RECEIPT_WIDTH))
        lines.append("This serves as your official receipt.".center(RECEIPT_WIDTH))
        lines.append(edge)
        return "\n".join(lines) + "\n"
