"""
catalog_generator.py - Large-Scale Programmatic Catalog (12,000+ Products)
===========================================================================
Generates a realistic Kapruka-style product catalog using 3-axis expansion:
    Template × Size/Variant × Occasion/Theme → ~1,500 items per category

Design:
    Each category has ~25 product templates.
    Each template is expanded across multiple size/variant axes (3–8 values).
    Each size variant is further expanded across occasions/themes (5–10 values).
    Allergen data is baked in per template and never changes across variants.

Total target: ~12,000–15,000 unique SKUs

Usage:
    from src.crawler.catalog_generator import generate_large_catalog
    products = generate_large_catalog()   # returns list[dict]
"""

import itertools
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Shared Helpers
# ──────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.kapruka.com"

_counter: dict[str, int] = {}


def _uid(prefix: str) -> str:
    _counter[prefix] = _counter.get(prefix, 0) + 1
    return f"KAP-{prefix}-{_counter[prefix]:05d}"


def _slug(*parts: str) -> str:
    return "-".join(
        p.lower().replace(" ", "-").replace("(", "").replace(")", "")
              .replace("/", "").replace("&", "and")[:25]
        for p in parts if p
    )[:80]


# ──────────────────────────────────────────────────────────────────────────────
# Per-Category Data Tables
# ──────────────────────────────────────────────────────────────────────────────

# ── CAKES ─────────────────────────────────────────────────────────────────────

CAKE_FLAVOURS = [
    # (label, allergens, tags, base_price, has_nut)
    ("Classic Chocolate Truffle",    ["nuts","dairy","gluten","eggs"], [],                        3500, True),
    ("Nut-Free Vanilla Sponge",      ["dairy","gluten","eggs"],        ["nut-free"],               3000, False),
    ("Strawberry Fresh Cream",       ["dairy","gluten","eggs"],        ["nut-free"],               3200, False),
    ("Black Forest",                 ["dairy","gluten","eggs"],        ["nut-free"],               3800, False),
    ("Mango Cream",                  ["dairy","gluten","eggs"],        ["nut-free"],               3400, False),
    ("Dark Choc Fudge - Nut-Free",   ["dairy","gluten","eggs"],        ["nut-free"],               3900, False),
    ("Caramel Walnut Gateau",        ["nuts","dairy","gluten","eggs"], [],                        4200, True),
    ("Almond Praline Chocolate",     ["nuts","dairy","gluten","eggs"], [],                        4500, True),
    ("Vegan Coconut Chocolate",      ["gluten"],                       ["dairy-free","egg-free","nut-free","vegan"], 4800, False),
    ("Dairy-Free Dark Chocolate",    ["gluten","eggs"],                ["dairy-free","nut-free"], 4000, False),
    ("Red Velvet",                   ["dairy","gluten","eggs"],        ["nut-free"],               3700, False),
    ("Lemon Drizzle - Nut-Free",     ["dairy","gluten","eggs"],        ["nut-free"],               3100, False),
    ("Hazelnut Crunch Chocolate",    ["nuts","dairy","gluten","eggs"], [],                        4600, True),
    ("Tiramisu",                     ["dairy","gluten","eggs"],        ["nut-free"],               4300, False),
    ("Pineapple Cream",              ["dairy","gluten","eggs"],        ["nut-free"],               3100, False),
    ("Cashew Toffee",                ["nuts","dairy","gluten","eggs"], [],                        4100, True),
    ("Tres Leches",                  ["dairy","gluten","eggs"],        ["nut-free"],               3900, False),
    ("Carrot Walnut",                ["nuts","dairy","gluten","eggs"], [],                        3700, True),
    ("Gluten-Free Almond Flourless", ["nuts","eggs"],                  ["gluten-free","dairy-free"], 5200, True),
    ("Butter Cream Sponge",          ["dairy","gluten","eggs"],        ["nut-free"],               2600, False),
    ("Pistachio Rose Cake",          ["nuts","dairy","gluten","eggs"], [],                        4800, True),
    ("Blueberry Cheesecake",         ["dairy","gluten","eggs"],        ["nut-free"],               4400, False),
    ("Matcha Green Tea Cake",        ["dairy","gluten","eggs"],        ["nut-free"],               4200, False),
    ("White Forest Cake",            ["dairy","gluten","eggs"],        ["nut-free"],               3600, False),
    ("Choco Lava Molten",            ["dairy","gluten","eggs"],        ["nut-free"],               3900, False),
]

CAKE_SIZES = [
    ("500g", 0.5, 0),
    ("1kg",    1, 500),
    ("1.5kg",  1.5, 1000),
    ("2kg",    2, 1500),
    ("3kg",    3, 2800),
]

CAKE_OCCASIONS = [
    "Birthday", "Anniversary", "Valentine's Day", "Mother's Day",
    "Father's Day", "Wedding", "Baby Shower", "Graduation",
    "Office Party", "Avurudu",
]


# ── FLOWERS ────────────────────────────────────────────────────────────────────

FLOWER_VARIETIES = [
    ("Red Rose Bouquet",        [], ["nut-free","dairy-free","gluten-free","vegan"], 220),
    ("White Rose Bouquet",      [], ["nut-free","dairy-free","gluten-free","vegan"], 200),
    ("Pink Rose Bouquet",       [], ["nut-free","dairy-free","gluten-free","vegan"], 210),
    ("Mixed Rose Bouquet",      [], ["nut-free","dairy-free","gluten-free","vegan"], 215),
    ("Yellow Sunflower",        [], ["nut-free","dairy-free","gluten-free","vegan"], 190),
    ("White Lily",              [], ["nut-free","dairy-free","gluten-free","vegan"], 240),
    ("Pink Tulip",              [], ["nut-free","dairy-free","gluten-free","vegan"], 270),
    ("Purple Lavender",         [], ["nut-free","dairy-free","gluten-free","vegan"], 200),
    ("Gerbera Daisy Mix",       [], ["nut-free","dairy-free","gluten-free","vegan"], 175),
    ("Carnation Mix",           [], ["nut-free","dairy-free","gluten-free","vegan"], 155),
    ("Purple Orchid",           [], ["nut-free","dairy-free","gluten-free","vegan"], 380),
    ("Baby's Breath",           [], ["nut-free","dairy-free","gluten-free","vegan"], 130),
    ("Red Anthurium",           [], ["nut-free","dairy-free","gluten-free","vegan"], 320),
    ("Peony Arrangement",       [], ["nut-free","dairy-free","gluten-free","vegan"], 360),
    ("Blue Hydrangea",          [], ["nut-free","dairy-free","gluten-free","vegan"], 310),
    ("Birds of Paradise",       [], ["nut-free","dairy-free","gluten-free","vegan"], 460),
    ("Lisianthus Mix",          [], ["nut-free","dairy-free","gluten-free","vegan"], 290),
    ("Snapdragon Mix",          [], ["nut-free","dairy-free","gluten-free","vegan"], 220),
    ("Alstroemeria Mix",        [], ["nut-free","dairy-free","gluten-free","vegan"], 175),
    ("Fragrant Freesia",        [], ["nut-free","dairy-free","gluten-free","vegan"], 230),
    ("Calla Lily White",        [], ["nut-free","dairy-free","gluten-free","vegan"], 350),
    ("Ranunculus Pastel Mix",   [], ["nut-free","dairy-free","gluten-free","vegan"], 340),
    ("Dahlia Colourful Mix",    [], ["nut-free","dairy-free","gluten-free","vegan"], 310),
    ("Sweet William Mix",       [], ["nut-free","dairy-free","gluten-free","vegan"], 180),
    ("Chrysanthemum Mix",       [], ["nut-free","dairy-free","gluten-free","vegan"], 170),
]

FLOWER_SIZES = [6, 12, 24, 36, 50, 100]

FLOWER_OCCASIONS = [
    "Birthday", "Anniversary", "Valentine's Day", "Mother's Day",
    "Sympathy", "Graduation", "Wedding", "Avurudu",
]

FLOWER_PRESENTATIONS = ["Hand Tied","Box Arrangement","Vase Arrangement","Gift Wrapped","Basket"]


# ── CHOCOLATES ─────────────────────────────────────────────────────────────────

CHOC_PRODUCTS = [
    ("Cadbury Dairy Milk Assorted",     ["dairy","nuts","gluten","soy"],              [],                                    28.0),
    ("Ferrero Rocher Box",              ["nuts","dairy","gluten","eggs","soy"],        [],                                    55.0),
    ("Lindt Dark Chocolate - Nut-Free", ["dairy","soy"],                              ["nut-free"],                          38.0),
    ("Kapruka Nut-Free Gift Box",       ["dairy","gluten","soy"],                     ["nut-free"],                          42.0),
    ("Toblerone Swiss Milk",            ["nuts","dairy","gluten","eggs","soy"],        [],                                    40.0),
    ("Vegan Dark Chocolate Box",        ["soy"],                                      ["dairy-free","nut-free","gluten-free","vegan"], 48.0),
    ("Bounty Coconut Pack",             ["dairy","gluten","soy"],                     ["nut-free"],                          22.0),
    ("Raffles Praline Nut Box",         ["nuts","dairy","gluten","eggs"],              [],                                    40.0),
    ("Snickers Gift Pack",              ["nuts","dairy","gluten","eggs","soy"],        [],                                    26.0),
    ("KitKat Assorted",                 ["dairy","gluten","soy"],                     ["nut-free"],                          24.0),
    ("Artisan Single-Origin Dark",      ["dairy","soy"],                              ["nut-free"],                          46.0),
    ("Cashew Raisin Milk Chocolate",    ["nuts","dairy","gluten","soy"],              [],                                    38.0),
    ("Belgian White Truffles",          ["dairy","gluten","eggs","soy"],              ["nut-free"],                          52.0),
    ("Rum Raisin Dark Chocolate",       ["dairy","gluten","soy"],                     ["nut-free"],                          40.0),
    ("Chili Sea Salt Dark",             ["dairy","soy"],                              ["nut-free","gluten-free"],            38.0),
    ("Vegan Coconut Dark Bar",          ["soy"],                                      ["dairy-free","nut-free","gluten-free","vegan"], 42.0),
    ("M&M Gift Jar",                    ["dairy","nuts","gluten","soy"],              [],                                    22.0),
    ("Godiva Luxury Truffles",          ["dairy","gluten","nuts","eggs","soy"],        [],                                    95.0),
    ("Peppermint Dark - Nut-Free",      ["dairy","gluten","soy"],                     ["nut-free"],                          32.0),
    ("Matcha White Chocolate",          ["dairy","gluten","soy"],                     ["nut-free"],                          44.0),
    ("Pistachio Milk Chocolate Bar",    ["nuts","dairy","gluten","soy"],              [],                                    36.0),
    ("Hazelnut Spread Gift Set",        ["nuts","dairy","gluten","eggs","soy"],        [],                                    58.0),
    ("Sea Salt Caramel Truffles",       ["dairy","gluten","eggs"],                    ["nut-free"],                          48.0),
    ("Orange Zest Dark Chocolate",      ["dairy","soy"],                              ["nut-free","gluten-free"],            36.0),
    ("Lavender Dark Chocolate",         ["dairy","soy"],                              ["nut-free","gluten-free"],            40.0),
]

CHOC_WEIGHTS = [50, 100, 150, 200, 300, 400, 500]  # grams

CHOC_OCCASIONS = [
    "Birthday", "Valentine's Day", "Eid", "Christmas",
    "Thank You", "Congratulations", "Diwali",
]

CHOC_PACKAGINGS = ["Box", "Tin", "Gift Bag", "Luxury Hamper Box"]


# ── GIFT HAMPERS ───────────────────────────────────────────────────────────────

HAMPER_THEMES = [
    ("Ceylon Tea Hamper",          ["gluten"],                    ["nut-free","dairy-free"],         7500),
    ("Corporate Luxury",           ["dairy","gluten","nuts"],      [],                                15000),
    ("SPA & Wellness",             [],                            ["nut-free","dairy-free","gluten-free"], 8500),
    ("Baby Arrival",               [],                            ["nut-free","dairy-free","gluten-free"], 6500),
    ("Food & Wine Gourmet",        ["nuts","dairy","gluten"],      [],                                12000),
    ("Nut-Free Sweet Hamper",      ["dairy","gluten","eggs"],      ["nut-free"],                      5500),
    ("Cricket Fan - SL Edition",   [],                            ["nut-free","dairy-free","gluten-free"], 7200),
    ("Whisky Connoisseur Set",     [],                            ["nut-free","dairy-free","gluten-free"], 18000),
    ("Ayurvedic Wellness",         [],                            ["nut-free","dairy-free","gluten-free","vegan"], 6800),
    ("Saree & Jewellery Set",      [],                            ["nut-free","dairy-free","gluten-free"], 14500),
    ("BBQ Grilling Set",           [],                            ["nut-free","dairy-free","gluten-free"], 8900),
    ("Home Decor Luxury",          [],                            ["nut-free","dairy-free","gluten-free"], 11000),
    ("Gaming Accessories",         [],                            ["nut-free","dairy-free","gluten-free"], 9500),
    ("Makeup & Beauty Set",        [],                            ["nut-free","dairy-free","gluten-free"], 8500),
    ("Book Lover Hamper",          [],                            ["nut-free","dairy-free","gluten-free"], 5500),
    ("Coffee Lover Pack",          ["gluten"],                    ["nut-free","dairy-free"],          8000),
    ("Fitness & Health Kit",       [],                            ["nut-free","dairy-free","gluten-free"], 9500),
    ("Traditional Sri Lankan",     ["gluten"],                    ["nut-free","dairy-free"],          8500),
    ("Kid's Fun Gift Set",         ["dairy","gluten"],            ["nut-free"],                       5500),
    ("Gardening Lover Set",        [],                            ["nut-free","dairy-free","gluten-free","vegan"], 6500),
    ("Artist & Craft Hamper",      [],                            ["nut-free","dairy-free","gluten-free"], 7000),
    ("Photography Lover Bundle",   [],                            ["nut-free","dairy-free","gluten-free"], 11500),
    ("Music Lover Set",            [],                            ["nut-free","dairy-free","gluten-free"], 9000),
    ("Pet Lover Gift Hamper",      [],                            ["nut-free","dairy-free","gluten-free"], 6000),
    ("New Home Hamper",            [],                            ["nut-free","dairy-free","gluten-free"], 9500),
]

HAMPER_TIERS = [
    ("Small",  0.6),
    ("Medium", 1.0),
    ("Large",  1.6),
    ("Premium", 2.2),
]

HAMPER_OCCASIONS = [
    "Birthday", "Wedding", "Corporate", "Eid", "Christmas",
    "Avurudu", "Mother's Day", "Father's Day", "Graduation", "Thank You",
]


# ── FRUIT BASKETS ──────────────────────────────────────────────────────────────

FRUIT_THEMES = [
    ("Fresh Seasonal Fruit Basket", [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1200),
    ("Tropical Exotic Basket",      [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1400),
    ("Fruit & Chocolate Basket",    ["dairy","gluten","soy"],  ["nut-free"],                                   1600),
    ("Health & Wellness Basket",    [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1100),
    ("Mother's Delight Basket",     ["gluten","eggs"],         ["nut-free","dairy-free"],                      1300),
    ("Avurudu Traditional Basket",  ["gluten","eggs"],         ["nut-free","dairy-free"],                      1400),
    ("Dry Fruit & Nut Gift Box",    ["nuts"],                  [],                                             2000),
    ("Berry Delight Basket",        [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1800),
    ("Citrus Sunshine Basket",      [],                        ["nut-free","dairy-free","gluten-free","vegan"], 900),
    ("Mango Paradise Basket",       [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1200),
    ("Banana & Jackfruit Local",    [],                        ["nut-free","dairy-free","gluten-free","vegan"], 750),
    ("Watermelon & Melon Refresh",  [],                        ["nut-free","dairy-free","gluten-free","vegan"], 950),
    ("Fruit & Herb Wellness",       [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1500),
    ("Premium Imported Fruit",      [],                        ["nut-free","dairy-free","gluten-free","vegan"], 2500),
    ("Avocado & Greens Basket",     [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1800),
    ("Dragon Fruit Exotic Box",     [],                        ["nut-free","dairy-free","gluten-free","vegan"], 2200),
    ("Pomegranate & Berry Mix",     [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1600),
    ("Kiwi & Grape Luxury Basket",  [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1700),
    ("Fig & Date Gift Box",         [],                        ["nut-free","dairy-free","gluten-free","vegan"], 2000),
    ("Rambutan & Mangosteen Box",   [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1900),
    ("Papaya & Passion Fruit",      [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1300),
    ("Mixed Melon Basket",          [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1100),
    ("Apple & Pear Orchard Basket", [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1400),
    ("Seasonal Sri Lankan Special", [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1200),
    ("Detox Green Basket",          [],                        ["nut-free","dairy-free","gluten-free","vegan"], 1600),
]

FRUIT_SIZES = [
    ("Small (~1.5kg)",  1.5, 0),
    ("Medium (~3kg)",   3.0, 600),
    ("Large (~5kg)",    5.0, 1200),
    ("XL (~8kg)",       8.0, 2000),
    ("XXL (~12kg)",    12.0, 3200),
]

FRUIT_OCCASIONS = [
    "Birthday", "Anniversary", "Get Well Soon", "Avurudu",
    "Mother's Day", "Eid", "Corporate", "Vesak", "Housewarming",
]


# ── SOFT TOYS ──────────────────────────────────────────────────────────────────

TOY_CHARACTERS = [
    "Classic White Teddy Bear", "Brown Teddy Bear", "Giant Panda Plush",
    "Princess Plush Doll", "Prince Plush Doll", "Unicorn Rainbow",
    "Sri Lanka Elephant", "Easter Bunny Rabbit", "Minion Kevin",
    "Minion Stuart", "Minion Bob", "Dinosaur T-Rex",
    "Baby Shark Plush", "Simba Lion King", "Disney Stitch",
    "Hello Kitty", "Winnie the Pooh", "Piglet Plush",
    "Tigger Plush", "Alpaca Rainbow", "Red Panda",
    "Pikachu Pokemon", "Snorlax Pokemon", "Eevee Pokemon",
    "Corgi Puppy Plush", "Labrador Puppy Plush", "Cat Plush",
    "Fox Plush", "Owl Plush", "Penguin Plush",
    "Sloth Plush", "Capybara Plush", "Dolphin Plush",
    "Dragon Plush", "Phoenix Plush",
]

TOY_SIZES = ["18cm", "25cm", "40cm", "60cm", "90cm", "120cm"]

TOY_OCCASIONS = [
    "Birthday", "Valentine's Day", "Christmas", "Baby Shower",
    "Anniversary", "Graduation", "Just Because",
]


# ── GREETING CARDS ─────────────────────────────────────────────────────────────

CARD_DESIGNS = [
    "Happy Birthday", "Happy Birthday Milestone 18",
    "Happy Birthday Milestone 21", "Happy Birthday Milestone 30",
    "Happy Birthday Milestone 40", "Happy Birthday Milestone 50",
    "Happy Birthday Milestone 60", "Happy Birthday Milestone 70",
    "Happy Birthday Milestone 80", "Wedding Anniversary",
    "Silver Anniversary 25 Years", "Golden Anniversary 50 Years",
    "Mother's Day Flowers", "Mother's Day Handmade",
    "Father's Day Proud", "Father's Day Classic",
    "Avurudu Greetings", "Vesak Greetings", "Deepavali Greetings",
    "Eid Mubarak", "Christmas Traditional", "Christmas Modern",
    "New Year Greetings", "Easter Blessings",
    "Congratulations Achievement", "Congratulations Graduation",
    "Congratulations New Baby", "Congratulations New Home",
    "Get Well Soon", "Sympathy Condolence",
    "Thank You Sincere", "Thinking of You",
    "Farewell & Good Luck", "Welcome Back",
    "Valentine's Day Love", "Valentine's Day Roses",
]

CARD_FORMATS = ["Standard A5", "Large A4", "Mini Postcard", "Luxury Handmade", "3D Pop-Up"]
CARD_LANGUAGES = ["English", "Sinhala", "Tamil", "Bilingual EN-SI"]

CARD_BASE_PRICES = {
    "Standard A5": 450,
    "Large A4": 750,
    "Mini Postcard": 350,
    "Luxury Handmade": 1200,
    "3D Pop-Up": 950,
}


# ── ELECTRONICS ────────────────────────────────────────────────────────────────

ELEC_PRODUCTS = [
    ("JBL Bluetooth Speaker",        2800,  "Compact waterproof Bluetooth speaker."),
    ("Sony Wireless Headphones",     6500,  "Premium Sony over-ear wireless headphones."),
    ("Apple AirPods",               18000,  "Apple AirPods with charging case."),
    ("Samsung Galaxy SmartWatch",   18000,  "Samsung Galaxy Watch with health tracking."),
    ("Anker Wireless Charger",       3500,  "Qi wireless charging pad set."),
    ("Realme Smartphone",           22000,  "Budget-premium Android smartphone."),
    ("Xiaomi TWS Earbuds",           5500,  "True wireless earbuds with noise isolation."),
    ("Laptop Bag & Accessories Kit", 4500,  "Laptop bag with accessories set."),
    ("Logitech Wireless Combo",      5000,  "Wireless mouse and keyboard combo."),
    ("GoPro Action Camera Bundle",  25000,  "Action camera with accessories."),
    ("Canon Instant Camera",        12000,  "Instant print camera with film pack."),
    ("Amazon Fire Tablet",          16000,  "Amazon Fire HD tablet."),
    ("Smart Doorbell",               9000,  "Smart video doorbell with app."),
    ("TP-Link Smart Plug",           2500,  "Smart WiFi plug with timer."),
    ("Kindle E-Reader",             10000,  "Amazon Kindle e-ink e-reader."),
    ("Xiaomi Robot Vacuum",         18000,  "Robot vacuum cleaner with mapping."),
    ("DJI Mini Drone",              28000,  "Compact drone with 4K camera."),
    ("Ring Light & Tripod Set",      5500,  "LED ring light for content creators."),
    ("Bose Soundbar",               35000,  "Bose smart soundbar with Alexa."),
    ("Garmin Fitness Tracker",      12000,  "Garmin activity tracker with GPS."),
    ("Fujifilm Instax Camera",       8500,  "Fujifilm Instax Mini instant camera."),
    ("Nintendo Switch Lite",        35000,  "Nintendo Switch Lite portable console."),
    ("PS5 Controller DualSense",    12000,  "PlayStation 5 DualSense controller."),
    ("Xbox Wireless Controller",    10000,  "Xbox Series wireless controller."),
    ("Portable Power Bank 20000mAh", 4500,  "High-capacity portable power bank."),
    ("USB-C Hub 7-in-1",             3500,  "7-in-1 USB-C hub for laptop/tablet."),
    ("Mechanical Keyboard RGB",      8000,  "RGB mechanical gaming keyboard."),
    ("Gaming Mouse Programmable",    4500,  "Programmable gaming mouse with DPI."),
    ("4K Webcam",                    7500,  "4K webcam for streaming/meetings."),
    ("Smart Home Starter Kit",      12000,  "Smart bulbs, plug, and hub starter kit."),
]

ELEC_VARIANTS = ["Standard", "Pro", "Elite", "Premium"]

ELEC_OCCASIONS = [
    "Birthday", "Graduation", "Corporate Gift",
    "Father's Day", "Husband's Birthday", "Tech Lover",
    "Back to School",
]


# ──────────────────────────────────────────────────────────────────────────────
# Generator Functions
# ──────────────────────────────────────────────────────────────────────────────

def _cakes() -> list[dict]:
    products = []
    for (flavour, allergens, tags, base_price, _), (size_label, size_kg, size_extra), occasion in \
            itertools.product(CAKE_FLAVOURS, CAKE_SIZES, CAKE_OCCASIONS):
        name = f"{flavour} Cake {size_label} - {occasion}"
        price = base_price + size_extra + (200 if occasion in ["Wedding", "Valentine's Day"] else 0)
        allergen_str = ", ".join(allergens) or "none"
        products.append({
            "product_id": _uid("CAKE"),
            "product_name": name,
            "price_lkr": float(price),
            "description": (
                f"{flavour} cake in {size_label} size. "
                f"Perfect for {occasion}. "
                f"Allergens: {allergen_str}."
            ),
            "availability": "In Stock",
            "category": "cakes",
            "url": f"{BASE_URL}/food/cakes/{_slug(flavour, size_label, occasion)}",
            "image_url": None,
            "tags": tags,
            "contains_allergens": allergens,
            "delivery_type": "perishable",
        })
    return products


def _flowers() -> list[dict]:
    products = []
    for (variety, allergens, tags, price_per_stem), stems, occasion, presentation in \
            itertools.product(FLOWER_VARIETIES, FLOWER_SIZES, FLOWER_OCCASIONS, FLOWER_PRESENTATIONS):
        price = round(price_per_stem * stems * (1.15 if presentation in ["Vase Arrangement", "Box Arrangement"] else 1.0))
        name = f"{variety} - {stems} Stems, {presentation} ({occasion})"
        products.append({
            "product_id": _uid("FLOW"),
            "product_name": name,
            "price_lkr": float(price),
            "description": (
                f"Fresh {variety.lower()}. {stems} stems. {presentation} style. "
                f"Ideal for {occasion}."
            ),
            "availability": "In Stock",
            "category": "flowers",
            "url": f"{BASE_URL}/food/flowers/{_slug(variety, str(stems), presentation)}",
            "image_url": None,
            "tags": tags,
            "contains_allergens": allergens,
            "delivery_type": "perishable",
        })
    return products


def _chocolates() -> list[dict]:
    products = []
    for (name_base, allergens, tags, price_per_100g), weight, occasion, packaging in \
            itertools.product(CHOC_PRODUCTS, CHOC_WEIGHTS, CHOC_OCCASIONS, CHOC_PACKAGINGS):
        price = round(price_per_100g * weight / 100 * 100)  # LKR per 100g × weight
        name = f"{name_base} {weight}g - {packaging} ({occasion})"
        allergen_str = ", ".join(allergens) or "none"
        products.append({
            "product_id": _uid("CHOC"),
            "product_name": name,
            "price_lkr": float(max(price, 850)),
            "description": (
                f"{name_base}. {weight}g. Presented in a {packaging.lower()}. "
                f"Perfect for {occasion}. Allergens: {allergen_str}."
            ),
            "availability": "In Stock",
            "category": "chocolates",
            "url": f"{BASE_URL}/food/chocolates/{_slug(name_base, str(weight), packaging)}",
            "image_url": None,
            "tags": tags,
            "contains_allergens": allergens,
            "delivery_type": "standard",
        })
    return products


def _gift_hampers() -> list[dict]:
    products = []
    for (theme, allergens, tags, base_price), (tier, multiplier), occasion in \
            itertools.product(HAMPER_THEMES, HAMPER_TIERS, HAMPER_OCCASIONS):
        price = round(base_price * multiplier)
        name = f"{theme} - {tier} ({occasion})"
        allergen_str = ", ".join(allergens) or "none"
        products.append({
            "product_id": _uid("HAMP"),
            "product_name": name,
            "price_lkr": float(price),
            "description": (
                f"{theme}. {tier} tier gift hamper. "
                f"Perfect for {occasion}. Allergens: {allergen_str}."
            ),
            "availability": "In Stock",
            "category": "gift-hampers",
            "url": f"{BASE_URL}/giftHampers/{_slug(theme, tier, occasion)}",
            "image_url": None,
            "tags": tags,
            "contains_allergens": allergens,
            "delivery_type": "standard",
        })
    return products


def _fruit_baskets() -> list[dict]:
    products = []
    for (theme, allergens, tags, price_per_kg), (size_label, weight_kg, size_extra), occasion in \
            itertools.product(FRUIT_THEMES, FRUIT_SIZES, FRUIT_OCCASIONS):
        price = round(price_per_kg * weight_kg + size_extra)
        name = f"{theme} - {size_label} ({occasion})"
        allergen_str = ", ".join(allergens) or "none"
        products.append({
            "product_id": _uid("FRUI"),
            "product_name": name,
            "price_lkr": float(price),
            "description": (
                f"{theme}. {size_label}. "
                f"Perfect as a {occasion} gift. Allergens: {allergen_str}."
            ),
            "availability": "In Stock",
            "category": "fruit-baskets",
            "url": f"{BASE_URL}/food/fruitBaskets/{_slug(theme, size_label, occasion)}",
            "image_url": None,
            "tags": tags,
            "contains_allergens": allergens,
            "delivery_type": "perishable",
        })
    return products


def _soft_toys() -> list[dict]:
    products = []
    for character, size, occasion in \
            itertools.product(TOY_CHARACTERS, TOY_SIZES, TOY_OCCASIONS):
        size_cm = int(size.replace("cm", ""))
        base = 800 + size_cm * 28
        name = f"{character} Plush - {size} ({occasion} Gift)"
        products.append({
            "product_id": _uid("SOFT"),
            "product_name": name,
            "price_lkr": float(base),
            "description": (
                f"Super-soft {character.lower()} plush toy. {size} size. "
                f"Makes a wonderful {occasion} gift."
            ),
            "availability": "In Stock",
            "category": "soft-toys",
            "url": f"{BASE_URL}/toys/softToys/{_slug(character, size)}",
            "image_url": None,
            "tags": ["nut-free", "dairy-free", "gluten-free"],
            "contains_allergens": [],
            "delivery_type": "standard",
        })
    return products


def _greeting_cards() -> list[dict]:
    products = []
    for design, fmt, language in \
            itertools.product(CARD_DESIGNS, CARD_FORMATS, CARD_LANGUAGES):
        price = CARD_BASE_PRICES[fmt]
        if language != "English":
            price = round(price * 1.05)
        name = f"{design} Card - {fmt} ({language})"
        products.append({
            "product_id": _uid("CARD"),
            "product_name": name,
            "price_lkr": float(price),
            "description": (
                f"{design} greeting card. {fmt} format. {language} language."
            ),
            "availability": "In Stock",
            "category": "greeting-cards",
            "url": f"{BASE_URL}/greeting-cards/{_slug(design, fmt, language)}",
            "image_url": None,
            "tags": ["nut-free", "dairy-free", "gluten-free"],
            "contains_allergens": [],
            "delivery_type": "standard",
        })
    return products


def _electronics() -> list[dict]:
    products = []
    for (product_name, base_price, desc), variant, occasion in \
            itertools.product(ELEC_PRODUCTS, ELEC_VARIANTS, ELEC_OCCASIONS):
        multiplier = {"Standard": 1.0, "Pro": 1.3, "Elite": 1.6, "Premium": 2.0}[variant]
        price = round(base_price * multiplier)
        name = f"{product_name} - {variant} ({occasion} Edition)"
        products.append({
            "product_id": _uid("ELEC"),
            "product_name": name,
            "price_lkr": float(price),
            "description": f"{desc} {variant} edition. Great for {occasion}.",
            "availability": "In Stock",
            "category": "electronics",
            "url": f"{BASE_URL}/products/electronics/{_slug(product_name, variant)}",
            "image_url": None,
            "tags": ["nut-free", "dairy-free", "gluten-free"],
            "contains_allergens": [],
            "delivery_type": "standard",
        })
    return products


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_large_catalog() -> list[dict]:
    """
    Generate 12,000+ products across 8 categories.

    Counts (approximate):
        Cakes          : 25 flavours × 5 sizes × 10 occasions  = 1,250
        Flowers        : 25 varieties × 6 stems × 8 occasions × 5 presentations = 6,000
        Chocolates     : 25 products × 7 weights × 7 occasions × 4 packagings  = 4,900
        Gift Hampers   : 25 themes × 4 tiers × 10 occasions    = 1,000
        Fruit Baskets  : 25 themes × 5 sizes × 9 occasions     = 1,125
        Soft Toys      : 35 characters × 6 sizes × 7 occasions = 1,470
        Greeting Cards : 36 designs × 5 formats × 4 languages  = 720
        Electronics    : 30 products × 4 variants × 7 occasions = 840
                                                   TOTAL ≈ 17,305
    In practice some products have same name collisions across axes so
    de-duplication in the scraper trims this to ~15,000+ unique SKUs.
    """
    _counter.clear()  # Reset ID counter each run

    print("  🏭 Generating large catalog...")
    all_products: list[dict] = []

    generators = [
        ("cakes",          _cakes),
        ("flowers",        _flowers),
        ("chocolates",     _chocolates),
        ("gift-hampers",   _gift_hampers),
        ("fruit-baskets",  _fruit_baskets),
        ("soft-toys",      _soft_toys),
        ("greeting-cards", _greeting_cards),
        ("electronics",    _electronics),
    ]

    for cat_name, gen_fn in generators:
        before = len(all_products)
        cat_products = gen_fn()
        all_products.extend(cat_products)
        print(f"     {cat_name:20s} +{len(cat_products):,} → total {len(all_products):,}")

    print(f"  ✅ Raw catalog: {len(all_products):,} products (before de-duplication)")
    return all_products
