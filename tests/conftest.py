"""Shared pytest fixture: a full app stack pointed at a temp data folder."""
import pytest

from app import config


@pytest.fixture
def stack(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "RECEIPTS_DIR", tmp_path / "receipts")

    from app.application import build_stack
    from app.services.seed_service import Seeder
    Seeder().ensure_all()
    return build_stack()


@pytest.fixture
def tomorrow_at():
    """Helper: a datetime a few days ahead at a given hour.

    It lands beyond the demo bookings (which occupy today..+2 days), so the
    tests behave the same no matter what time of day they run.
    """
    from datetime import datetime
    import pytest as _pytest

    def _make(hour, minute=0):
        base = datetime.now().replace(hour=hour, minute=minute,
                                      second=0, microsecond=0)
        from datetime import timedelta
        return base + timedelta(days=5)
    return _make
