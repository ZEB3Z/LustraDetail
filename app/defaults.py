"""Seed content for the JSON data files (catalog, inventory, staff, demo people)."""

ALL = ["sedan", "suv", "pickup", "van", "motorcycle"]


def _matrix(sedan, suv, pickup, van, moto):
    return {"sedan": sedan, "suv": suv, "pickup": pickup, "van": van, "motorcycle": moto}


def _mat(*pairs):
    return [{"item_id": i, "qty": q} for i, q in pairs]


CATALOG = {
    "services": [
        {"id": "SVC001", "name": "Basic Wash",
         "description": "Exterior hand wash, rinse and dry.",
         "prices": _matrix(350, 450, 500, 550, 250),
         "durations": _matrix(45, 60, 60, 75, 30),
         "materials": _mat(("SHMP01", 0.2), ("MICF01", 2))},
        {"id": "SVC002", "name": "Interior Deep Clean",
         "description": "Vacuum, shampoo upholstery, dashboard and glass.",
         "prices": _matrix(1500, 1800, 1900, 2200, 900),
         "durations": _matrix(120, 150, 150, 180, 60),
         "materials": _mat(("MICF01", 3), ("INTC01", 0.3))},
        {"id": "SVC003", "name": "Wax & Polish",
         "description": "Machine polish with a protective carnauba wax.",
         "prices": _matrix(1200, 1400, 1500, 1700, 800),
         "durations": _matrix(90, 105, 105, 120, 60),
         "materials": _mat(("WAXX01", 0.15), ("MICF01", 2))},
        {"id": "SVC004", "name": "Engine Bay Cleaning",
         "description": "Degrease and dress the engine bay.",
         "prices": _matrix(800, 900, 1000, 1100, 600),
         "durations": _matrix(60, 60, 75, 75, 45),
         "materials": _mat(("INTC01", 0.2), ("MICF01", 1))},
        {"id": "SVC005", "name": "Headlight Restoration",
         "description": "Sand, polish and seal cloudy headlights.",
         "prices": _matrix(900, 900, 1000, 1000, 500),
         "durations": _matrix(45, 45, 45, 60, 30),
         "materials": _mat(("WAXX01", 0.05), ("MICF01", 1))},
        {"id": "SVC006", "name": "Ceramic Coating",
         "description": "Multi-year ceramic paint protection.",
         "prices": _matrix(12000, 15000, 16000, 18000, 8000),
         "durations": _matrix(240, 300, 300, 360, 180),
         "materials": _mat(("CERM01", 1), ("MICF01", 4))},
        {"id": "SVC007", "name": "Paint Correction",
         "description": "Removes swirls and light scratches.",
         "prices": _matrix(5000, 6000, 6500, 7500, 3500),
         "durations": _matrix(240, 270, 270, 300, 180),
         "materials": _mat(("WAXX01", 0.2), ("MICF01", 3))},
        {"id": "SVC008", "name": "Leather Treatment",
         "description": "Deep clean and condition leather seats.",
         "prices": _matrix(1800, 2000, 2200, 2500, 1000),
         "durations": _matrix(90, 105, 105, 120, 45),
         "materials": _mat(("INTC01", 0.2), ("MICF01", 2))},
        {"id": "SVC009", "name": "Odor Removal",
         "description": "Ozone and steam treatment for stubborn smells.",
         "prices": _matrix(1000, 1200, 1300, 1500, 700),
         "durations": _matrix(60, 75, 75, 90, 45),
         "materials": _mat(("INTC01", 0.1), ("MICF01", 1))},
    ],
    "add_ons": [
        {"id": "ADD001", "name": "Air Freshener", "price": 100, "duration": 5,
         "materials": []},
        {"id": "ADD002", "name": "Wheel & Rim Detail", "price": 300, "duration": 20,
         "materials": _mat(("MICF01", 1))},
        {"id": "ADD003", "name": "Tire Shine", "price": 200, "duration": 15,
         "materials": []},
        {"id": "ADD004", "name": "Glass Water Repellent", "price": 350, "duration": 20,
         "materials": []},
        {"id": "ADD005", "name": "Pet Hair Removal", "price": 400, "duration": 30,
         "materials": []},
    ],
    "packages": [
        {"id": "PKG001", "name": "Fresh Start",
         "description": "Wash + interior deep clean.",
         "service_ids": ["SVC001", "SVC002"], "discount_percent": 10},
        {"id": "PKG002", "name": "Showroom Shine",
         "description": "Wash + wax & polish.",
         "service_ids": ["SVC001", "SVC003"], "discount_percent": 10},
        {"id": "PKG003", "name": "Full Works",
         "description": "Wash, interior, wax and leather treatment.",
         "service_ids": ["SVC001", "SVC002", "SVC003", "SVC008"], "discount_percent": 15},
    ],
    "promos": [
        {"code": "LUSTRA10", "description": "10% off your booking", "discount_percent": 10},
        {"code": "WELCOME5", "description": "5% welcome discount", "discount_percent": 5},
    ],
}

INVENTORY = [
    {"id": "SHMP01", "name": "Car Shampoo", "unit": "L", "stock": 20.0, "reorder_level": 3.0},
    {"id": "MICF01", "name": "Microfiber Towels", "unit": "pcs", "stock": 50.0, "reorder_level": 10.0},
    {"id": "WAXX01", "name": "Carnauba Wax", "unit": "kg", "stock": 5.0, "reorder_level": 1.0},
    {"id": "INTC01", "name": "Interior Cleaner", "unit": "L", "stock": 10.0, "reorder_level": 2.0},
    {"id": "CERM01", "name": "Ceramic Coating Kit", "unit": "kits", "stock": 3.0, "reorder_level": 1.0},
]

STAFF = [
    {"id": 1, "name": "Ramon Villanueva", "role": "admin", "username": "admin",
     "password": "admin123", "phone": "09170000001", "active": True},
    {"id": 2, "name": "Alwin Mercado", "role": "detailer", "username": "alwin",
     "password": "detail123", "phone": "09170000002", "active": True},
    {"id": 3, "name": "Mara Santos", "role": "cashier", "username": "cashier",
     "password": "cash123", "phone": "09170000003", "active": True},
]

CUSTOMERS = [
    {"id": 1, "name": "Juan Dela Cruz", "phone": "09171234567", "email": "juan@example.com",
     "notes": "", "created_at": "2025-01-05 10:00"},
    {"id": 2, "name": "Maria Santos", "phone": "09181234567", "email": "maria@example.com",
     "notes": "", "created_at": "2025-01-06 11:30"},
    {"id": 3, "name": "Pedro Reyes", "phone": "09191234567", "email": "",
     "notes": "Prefers morning slots", "created_at": "2025-01-08 09:15"},
    {"id": 4, "name": "Ana Lim", "phone": "09201234567", "email": "ana@example.com",
     "notes": "", "created_at": "2025-01-10 15:45"},
]

VEHICLES = [
    {"id": 1, "customer_id": 1, "plate": "ABC 1234", "make": "Toyota", "model": "Vios",
     "year": 2020, "color": "White", "type": "sedan", "notes": ""},
    {"id": 2, "customer_id": 2, "plate": "XYZ 5678", "make": "Toyota", "model": "Hilux",
     "year": 2019, "color": "Gray", "type": "pickup", "notes": ""},
    {"id": 3, "customer_id": 3, "plate": "MTR 4321", "make": "Honda", "model": "Click 160",
     "year": 2022, "color": "Red", "type": "motorcycle", "notes": ""},
    {"id": 4, "customer_id": 4, "plate": "SUV 9001", "make": "Mitsubishi", "model": "Montero",
     "year": 2021, "color": "Black", "type": "suv", "notes": "Dark paint - swirls show easily"},
]
