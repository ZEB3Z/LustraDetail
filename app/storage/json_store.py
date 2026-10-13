"""Tiny JSON persistence layer with atomic writes and .bak recovery.

- Writes go to a .tmp file first, then atomically replace the target,
  so a crash mid-write can never truncate a data file.
- Every successful save copies the previous file to .bak.
- If a file is ever corrupted, the next read silently restores from .bak.
"""
import json
import os
import shutil
from pathlib import Path

from app.exceptions import AppError


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise AppError(f"invalid JSON: {exc}") from exc
    except OSError as exc:
        raise AppError(f"could not read file: {exc}") from exc


def read_json(path, default):
    """Read a JSON file; return `default` when it does not exist.

    If the file exists but is corrupted, try to recover from its .bak
    backup. Only if both are unreadable do we give up with instructions.
    """
    path = Path(path)
    if not path.exists():
        return default
    try:
        return _load(path)
    except AppError:
        bak = path.with_name(path.name + ".bak")
        if bak.exists():
            try:
                data = _load(bak)
                shutil.copyfile(bak, path)   # silently repair the main file
                return data
            except AppError:
                pass
        raise AppError(
            f"Data file '{path.name}' is corrupted and no backup could be "
            f"recovered. Run 'python main.py --reseed' to restore the demo data."
        ) from None


def write_json(path, data):
    """Atomically write `data` to `path`, keeping a .bak of the old file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    bak = path.with_name(path.name + ".bak")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    if path.exists():
        shutil.copyfile(path, bak)
    os.replace(tmp, path)


def ensure_file(path, default):
    """Create the file with `default` content when it does not exist yet."""
    path = Path(path)
    if not path.exists():
        write_json(path, default)
