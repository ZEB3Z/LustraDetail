"""Storage layer: atomic writes, defaults, and .bak corruption recovery."""
from app.storage.json_store import read_json, write_json


def test_write_and_read_roundtrip(tmp_path):
    path = tmp_path / "demo.json"
    write_json(path, {"name": "LustraDetail", "items": [1, 2, 3]})
    assert read_json(path, {}) == {"name": "LustraDetail", "items": [1, 2, 3]}


def test_missing_file_returns_default(tmp_path):
    assert read_json(tmp_path / "nope.json", {"default": True}) == {"default": True}


def test_backup_is_created_on_second_write(tmp_path):
    path = tmp_path / "demo.json"
    write_json(path, {"v": 1})
    write_json(path, {"v": 2})
    assert (tmp_path / "demo.json.bak").exists()
    assert read_json(path, {}) == {"v": 2}


def test_corrupted_file_recovers_from_backup(tmp_path):
    path = tmp_path / "demo.json"
    write_json(path, {"v": 1})
    write_json(path, {"v": 2})                       # .bak now holds {"v": 1}
    path.write_text("{ this is not json", encoding="utf-8")
    assert read_json(path, {}) == {"v": 1}           # recovered + repaired


def test_corrupted_file_without_backup_raises(tmp_path):
    from app.exceptions import AppError
    path = tmp_path / "demo.json"
    path.write_text("{ broken", encoding="utf-8")
    try:
        read_json(path, {})
    except AppError as exc:
        assert "--reseed" in str(exc)
    else:
        raise AssertionError("expected AppError for unrecoverable file")
