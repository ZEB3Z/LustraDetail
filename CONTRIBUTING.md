# Contributing to LustraDetail

Thanks for helping polish the shop! This is a class project, but we still
keep the code disciplined so the interface stays a thin, replaceable layer.

## Getting set up

```bash
git clone <your-fork>
cd lustradetail
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m pytest                 # everything should pass before you start
```

## The layer rules (the important part)

| Layer | May do | Must NOT do |
|---|---|---|
| `app/ui` | draw Tkinter windows, read input, call services | contain business rules or touch JSON directly |
| `app/services` | all business rules, raise `AppError` subclasses | print, call `input()`, import `tkinter` or `app.ui` |
| `app/storage` | read/write JSON, recover from `.bak` | know anything about screens or money rules |
| `app/models` | hold data, (de)serialize | anything else |

If a reviewer can find a `print()` inside `app/services`, the PR goes back. 🙂

## Workflow

1. Open an issue describing the bug/idea (use the templates).
2. Fork, create a branch: `git checkout -b feature/short-name`.
3. Make your change; add or update tests for any behavior change.
4. Run `python -m pytest` — the full suite must pass.
5. Open a pull request against `main` and fill in the PR template.

## Code style

- Standard library only at runtime; formatting follows PEP 8 (4-space indent,
  snake_case, docstrings on modules and public functions).
- UI code uses Tkinter/ttk only (no third-party GUI packages). Take colors and
  fonts from `app/ui/theme.py` (`C`, `F`, `px()`) instead of hard-coding them, and
  check new screens in both the light and dark theme.
- Receipts are plain-text files, so keep their content ASCII-safe.
- Never name a widget attribute or method `_w`, `_h`, `_name`, `_root` or similar —
  Tkinter uses those internally.
- Plain-text staff passwords are a known, deliberate limitation of this
  class project; do not "fix" them without opening an issue first.

## Reporting bugs

Use the Bug Report issue template and include your OS, Python version
(`python --version`), a screenshot, and the exact steps to reproduce.
