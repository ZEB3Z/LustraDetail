# Changelog

All notable changes to LustraDetail are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026

### Changed
- Replaced the terminal UI with a desktop interface built on pure
  Tkinter/ttk (still zero third-party dependencies). Services, storage,
  models and tests are untouched.

### Added
- Animated splash screen and a branded login screen with demo-account chips
  and a 15-second lockout after 3 failed attempts.
- Sidebar navigation with role-gated menus (admin / cashier / detailer and
  the customer portal), live clock and badge counts.
- Dashboard with KPI cards, today's schedule, bay-utilization gauge, job
  pipeline donut, 7-day revenue chart, top services and low-stock list.
- Light and dark themes with a sidebar toggle, remembered in
  `.lustra_ui.json`.
- Five-step booking wizard with a live quote panel, plus modal forms for
  checkout, reschedule, restock, registration and staff.
- HiDPI awareness on Windows, F11 fullscreen, and a friendly message when
  Tkinter is missing.

### Removed
- The ASCII terminal screens (`app/ui/terminal.py` and friends).

## [1.0.0] - 2025

### Added
- Terminal UI with ASCII branding, role-gated staff menus, and a
  customer self-service portal.
- Service catalog: 9 services with a price/duration matrix across 5 vehicle
  types, 5 add-ons, 3 packages, and promo codes.
- Scheduling for a single detailing bay: auto-computed durations, overlap
  detection with a 15-minute buffer, suggested free slots, walk-ins,
  rescheduling, cancellations, and no-show tracking.
- Job pipeline: BOOKED → IN PROGRESS → DONE → PAID with guarded transitions.
- Customer & vehicle registry with duplicate phone/plate protection and
  per-vehicle service history.
- Inventory with per-job material deductions, insufficient-stock blocking,
  low-stock alerts, and restocking.
- Deposits, multi-method checkout, cash change computation, and itemized
  ASCII receipts saved per order.
- Reports: daily sales, top services, bay utilization, shop summary.
- Staff management with admin/detailer/cashier roles.
- JSON storage with atomic writes and automatic `.bak` corruption recovery.
- Demo dataset (relative to "today") via `python main.py --reseed`.
- Pytest suite and GitHub Actions CI (Python 3.10 / 3.12).
