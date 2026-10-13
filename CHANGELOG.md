# Changelog

All notable changes to LustraDetail are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
