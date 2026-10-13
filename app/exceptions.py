"""Typed exceptions. Services raise these; the UI catches AppError and prints it."""


class AppError(Exception):
    """Base class for every expected, user-facing error."""


class ValidationError(AppError):
    """Input failed validation."""


class NotFoundError(AppError):
    """A requested record does not exist."""


class BookingError(AppError):
    """A scheduling / job-pipeline rule was violated."""


class InventoryError(AppError):
    """Not enough stock, or a bad inventory operation."""


class PaymentError(AppError):
    """A checkout / payment rule was violated."""


class AuthError(AppError):
    """Login failed."""
