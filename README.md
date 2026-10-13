<div align="center">

```
+============================================================+
|                                                            |
|        L  U  S  T  R  A  D  E  T  A  I  L                  |
|                A U T O    C A R E                          |
|                                                            |
|                     ______                                 |
|                    /|_||_\`.____                           |
|                   (   _    _  _ \                          |
|                   =`-(_)--(_)-'                             |
|                                                            |
|          "Drive in dirty. Drive out dazzling."             |
|                                                            |
+============================================================+
```

# LustraDetail Auto Care

### A complete terminal-based management system for a one-bay auto detailing shop

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-success)
![Tests](https://img.shields.io/badge/tests-pytest-brightgreen)
![UI](https://img.shields.io/badge/UI-terminal%20%2F%20ASCII-artistic)

**Services priced per vehicle type • conflict-free scheduling • job tracking •
inventory with auto-deduction • official receipts • sales reports • staff roles •
customer self-service portal**

*Built as a finals class project by Ericksson Brutas and Alwin Benitez.*

</div>

---

## Table of Contents

1. [What is LustraDetail?](#-what-is-lustradetail)
2. [Feature Tour](#-feature-tour)
3. [Quick Start](#-quick-start)
4. [Demo Accounts](#-demo-accounts)
5. [A Peek Inside](#-a-peek-inside)
6. [How It Works](#-how-it-works)
7. [Project Structure](#-project-structure)
8. [Scheduling Rules](#-scheduling-rules)
9. [Data Files](#-data-files)
10. [Running the Tests](#-running-the-tests)
11. [Roadmap: Tkinter GUI](#-roadmap-tkinter-gui)
12. [Contributing](#-contributing)
13. [Authors](#-authors)

---

## 📖 What is LustraDetail?

**LustraDetail Auto Care** is a fictional one-bay detailing shop in Quezon City.
This project is the shop's entire back office, squeezed into a clean, menu-driven
terminal application written in **pure Python — zero third-party packages**.

Staff log in to run the shop; customers log in with just their phone number to
book their own appointments. Every business rule — pricing, conflicts, stock,
payments — is guarded by fail-safes, and every completed job produces an
ASCII-styled official receipt saved to disk.

> *Drive in dirty. Drive out dazzling.*

---

## ✨ Feature Tour

| Area | What you get |
|---|---|
| **Service catalog** | 9 detailing services with a **price & duration matrix across 5 vehicle types**, 5 add-ons, 3 discounted packages, and promo codes |
| **Scheduling** | Book any date & time, auto-computed job duration, **overlap detection with a 15-minute bay buffer**, suggested next-free-slot browsing, walk-ins, rescheduling, cancellations, no-show tracking |
| **Job pipeline** | `BOOKED → IN PROGRESS → DONE → PAID` with guarded transitions — every step validated |
| **Customers & vehicles** | Full registry (contact, plate, make/model/year/color, notes), duplicate-phone/plate protection, per-vehicle **service history** |
| **Inventory** | Chemicals, towels, coatings and film; **stock auto-deducted when a job starts**, booking blocked when stock is insufficient, low-stock alerts, restocking |
| **Payments** | Deposits at booking, balance checkout, cash change computation, GCash / bank / card support, **itemized ASCII receipt per order** |
| **Reports** | Daily sales, top services, bay utilization (with ASCII progress bar), shop summary |
| **Staff** | Three roles (**admin / detailer / cashier**) with menu gating, staff management (add, activate/deactivate) |
| **Customer portal** | Self-service: browse prices, book, reschedule, cancel, view vehicle history |
| **Storage** | JSON files with **atomic writes and automatic `.bak` corruption recovery** |

---

## 🚀 Quick Start

### Requirements

- **Python 3.10 or newer** (3.13 recommended) — tkinter ships with it, so the future GUI upgrade needs nothing extra
- No `pip install` needed — the app uses **only the standard library**

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/ZEB3Z/lustradetail.git
cd lustradetail

# 2. (optional but recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Run it!
python main.py
```

That's it. On first launch the system seeds itself with a demo dataset
(customers, vehicles, staff, catalog, and a week of demo bookings whose dates
are relative to *today*, so dashboards and reports always have something to show).

### Command-line flags

| Command | What it does |
|---|---|
| `python main.py` | Starts the application (auto-seeds demo data on first run) |
| `python main.py --reseed` | Wipes and rebuilds all data files fresh — handy before a demo/defense |
| `python main.py --help` | Shows usage |

---

## 🔑 Demo Accounts

| Who | Login | Notes |
|---|---|---|
| Admin | `admin` / `admin123` | Full access: everything + staff management |
| Detailer | `alwin` / `detail123` | Dashboard, start/complete jobs, catalog, inventory |
| Cashier | `cashier` / `cash123` | Bookings, checkout & receipts, customers, sales reports |
| Customer | phone `09171234567` (Juan Dela Cruz) | Or register a new account from the portal |

> ℹ️ Passwords are stored in plain text in `data/staff.json` — a deliberate,
> documented decision for this class project (see `CONTRIBUTING.md`).

---

## 👀 A Peek Inside

```
+============================================================+
|                                                            |
|        L  U  S  T  R  A  D  E  T  A  I  L                  |
|                A U T O    C A R E                          |
|                                                            |
|          "Drive in dirty. Drive out dazzling."              |
|                                                            |
+============================================================+
  LustraDetail Auto Care  |  version 1.0.0

  [1] Staff login
  [2] Customer portal
  [3] About this system
  [0] Exit
  Choose: 1

  STAFF LOGIN  (3 attempt(s) left)
  Username: admin
  Password: admin123
  [+] Welcome back, Ericksson Brutas (admin).

== [ DASHBOARD - TODAY ]======================================
ID  Scheduled            Customer        Vehicle                    Service(s)                 Status    Total
--  -------------------  --------------  -------------------------  --------------------------  --------  ---------
3   2025-06-05 10:00     Carlo Reyes     Honda Click 125i (m...)    Basic Wash                 DONE      Php 250.00
4   2025-06-05 13:00     Ana Lim         Mitsubishi Montero...      Exterior Detailing (+...  BOOKED    Php 4,950.00

  Today: 2 booked, 0 in progress, 1 done, 0 paid.
  [!] 1 finished job(s) awaiting checkout.
  [+] Inventory levels look healthy.
```

And the receipt a customer walks away with (`receipts/receipt_0003.txt`):

```
======================================================
                 LustraDetail Auto Care
             "Drive in dirty. Drive out dazzling."
            123 Shine Avenue, Quezon City, Philippines
                  Tel: 0917 000 1234
======================================================
OFFICIAL RECEIPT                             No. 00003
--------------------------------------------------
Customer : Juan Dela Cruz
Phone    : 09171234567
Vehicle  : Toyota Vios 2019 (Silver) [ABC 1234]
Paid at  : 2025-06-05 16:02
Cashier  : Mara Santos
--------------------------------------------------
SERVICES
  Basic Wash ..................... Php 350.00
  Interior Detailing ............. Php 1,500.00
--------------------------------------------------
  Subtotal ....................... Php 1,850.00
  TOTAL .......................... Php 1,850.00
--------------------------------------------------
Payment method : gcash
--------------------------------------------------
          Thank you for trusting LustraDetail!
       This serves as your official receipt.
======================================================
```

---

## 🧠 How It Works

LustraDetail uses a **strict layered architecture**. Each layer may only talk to
the one below it — which is exactly why the terminal UI can be swapped for a
Tkinter GUI later **without touching a single business rule**:

```
+-----------------------------------------------------+
|  UI LAYER (app/ui)                                  |
|  menus, ASCII art, prompts  -- the ONLY layer       |
|  that prints or reads input                          |
+------------------------+----------------------------+
                         v
+-----------------------------------------------------+
|  SERVICE LAYER (app/services)                        |
|  ALL business rules: quotes, conflicts, payments,   |
|  inventory, reports. Never prints; raises typed      |
|  exceptions (AppError family) instead                |
+------------------------+----------------------------+
                         v
+-----------------------------------------------------+
|  STORAGE LAYER (app/storage)                        |
|  repositories + atomic JSON writes with .bak        |
|  corruption recovery                                |
+------------------------+----------------------------+
                         v
+-----------------------------------------------------+
|  MODELS (app/models)          |  DATA (data/*.json) |
|  plain dataclasses             |  receipts/*.txt     |
+-----------------------------------------------------+
```

### The job pipeline

```
                 +--------+     +-------------+     +------+     +------+
  book job ----> | BOOKED | --> | IN PROGRESS | --> | DONE | --> | PAID |
                 +---+----+     +-------------+     +------+     +------+
                     |                (start deducts     (checkout writes
                     |                 inventory)        receipt + history)
                     +--> CANCELLED
                     +--> NO_SHOW   (only after the scheduled time passed)
```

Every arrow is a fail-safe: you can't start a job twice, reschedule a job
that's already in the bay, pay an unfinished job, or mark a no-show for an
appointment that hasn't even happened yet.

---

## 📁 Project Structure

```
lustradetail/
├── main.py                  # entry point (run me!)
├── app/
│   ├── application.py       # wires repos + services into one "stack"
│   ├── config.py            # branding, paths, business rules
│   ├── defaults.py          # seed content for all data files
│   ├── exceptions.py        # AppError family
│   ├── models/              # dataclasses: Customer, Vehicle, Appointment, ...
│   ├── storage/             # JSON store (atomic + .bak) and repositories
│   ├── services/            # auth, catalog, customers, bookings, inventory,
│   │                        # payments, reports, staff, demo seeding
│   ├── ui/                  # terminal screens (swap target for Tkinter)
│   └── utils/               # dates, validation, ASCII-safe formatting
├── data/                    # JSON "database" (7 files, auto-created)
├── receipts/                # generated official receipts (.txt)
├── tests/                   # pytest suite (business rules + storage)
└── .github/                 # CI workflow + issue/PR templates
```

---

## 📅 Scheduling Rules

The shop has **one detailing bay** and schedules **around the clock** (no fixed
operating hours — customers pick their own time). To keep the bay sane:

1. Bookings can never start in the past.
2. Two jobs can never overlap.
3. Consecutive jobs need at least a **15-minute buffer** (`BOOKING_BUFFER_MINUTES`
   in `app/config.py`) for setup and cleanup.
4. Only `BOOKED` and `IN PROGRESS` appointments block the bay — cancelled and
   no-show slots free up immediately.
5. The system can **suggest the next free slots** for any job duration.

---

## 🗄️ Data Files

All data lives in `data/` as readable JSON — open them in any editor.

| File | Contents |
|---|---|
| `customers.json` | Customer registry (id, name, phone, email, notes) |
| `vehicles.json` | Vehicles linked to customers (plate, make, model, year, color, type) |
| `appointments.json` | Bookings with full price breakdown, status, deposits, payments |
| `service_catalog.json` | Services (price/duration matrix), add-ons, packages, promos |
| `inventory.json` | Stock levels and reorder points for all materials |
| `staff.json` | Staff accounts and roles |
| `service_history.json` | Per-vehicle completed-job history |

> Want to tweak prices or add a service? Edit `service_catalog.json` and restart —
> existing bookings keep their original quoted prices (snapshots are stored per
> appointment), which is exactly how a real shop should behave.

---

## 🧪 Running the Tests

The repo ships with a **pytest suite** covering quotes, scheduling conflicts,
inventory fail-safes, payments, storage recovery, and reports:

```bash
python -m pip install -r requirements-dev.txt   # installs pytest
python -m pytest                                # runs the whole suite
```

The test suite runs automatically on every push via **GitHub Actions**
(`.github/workflows/ci.yml`) on Python 3.10 and 3.12.

---

## 🖥️ Roadmap: Tkinter GUI

The terminal UI was built as a **deliberately replaceable layer**. Because:

- every screen receives the same injected `stack` of services,
- services never print or prompt (they raise typed exceptions),
- models serialize themselves to plain dicts,

...swapping in a Tkinter front end means rewriting **only `app/ui/`** —
`build_stack()` in `app/application.py` stays byte-for-byte identical. The
JSON storage can later be traded for SQLite behind the same repository
interfaces without touching the services either.

---

## 🤝 Contributing

Pull requests are welcome! Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for
the layer rules (UI never contains logic, services never print) and the test
requirements, and open an issue first for big changes.

---

## 👥 Authors

- **Ericksson Brutas** — [GitHub](https://github.com/ZEB3Z)
- **Alwin Benitez** — [GitHub](https://github.com/alwincroissant)

Made with soap, microfiber, and a lot of `print()` statements for our
programming finals project. 🚗✨
