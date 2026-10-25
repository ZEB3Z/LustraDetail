## Description

What does this PR change and why? Link the related issue
("Closes #12") if there is one.

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation only

## Layer checklist

- [ ] No business logic added to `app/ui` (screens only call services)
- [ ] No `print()` / `input()` / `tkinter` imports added to `app/services`
- [ ] No direct JSON file access outside `app/storage`
- [ ] New screens look right in both light and dark themes

## Testing

- [ ] `python -m pytest` passes locally
- [ ] Added/updated tests for the new behavior
- [ ] Manually smoke-tested via `python main.py`

## Screenshots

Add a screenshot of the changed screen (light and dark if relevant).
