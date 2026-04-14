"""
Reset image_url fields in data/catalog.json to empty string.

Run this before re-scraping so patch_real_image_urls.py will
re-populate all products (it only patches products with no image_url).

Usage:
    python reset_image_urls.py
"""

import json
from pathlib import Path

catalog_path = Path("data/catalog.json")
with open(catalog_path, encoding="utf-8") as f:
    data = json.load(f)

is_wrapped = isinstance(data, dict) and "products" in data
products = data.get("products", data) if is_wrapped else data

TARGET_CATEGORIES = {"cakes", "flowers", "chocolates", "hampers", "gift-hampers", "gift_hampers"}

reset_count = 0
for p in products:
    if p.get("category", "").lower() in TARGET_CATEGORIES:
        p["image_url"] = ""
        reset_count += 1

if is_wrapped:
    data["products"] = products
    out = data
else:
    out = products

with open(catalog_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Reset {reset_count} image_url fields to empty string.")
print("Next: python patch_real_image_urls.py")
