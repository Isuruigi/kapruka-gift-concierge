"""
Real Image URL Scraper for Kapruka — patches catalog.json with real image URLs.

Correct URL patterns (verified from live site):
    Cakes:      https://www.kapruka.com/online/cakes
    Flowers:    https://www.kapruka.com/online/flowers
    Chocolates: https://www.kapruka.com/online/chocolates
    Hampers:    https://www.kapruka.com/srilanka_online_search.jsp?d=hampers

Image CDN:
    https://www.kapruka.com/images/product/[category]/[filename].jpg

Product URL pattern:
    https://www.kapruka.com/buyonline/[slug]/kid/[id]

Usage:
    python patch_real_image_urls.py

Output:
    data/catalog.json          (image_url fields populated with real Kapruka URLs)
    data/image_url_cache.json  (raw scraped URLs for debugging)
"""

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ─── Correct Kapruka category URLs (verified) ────────────────────────────────
CATEGORY_URLS = {
    "cakes":       "https://www.kapruka.com/online/cakes",
    "flowers":     "https://www.kapruka.com/online/flowers",
    "chocolates":  "https://www.kapruka.com/online/chocolates",
    "hampers":     "https://www.kapruka.com/srilanka_online_search.jsp?d=hampers",
}

# Catalog category names that map to the above
CATALOG_CAT_MAP = {
    "cakes":      ["cakes"],
    "flowers":    ["flowers"],
    "chocolates": ["chocolates"],
    "hampers":    ["hampers", "gift-hampers", "gift_hampers"],
}

MAX_PER_CATEGORY = 120

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Selectors to find product listing containers on kapruka's pages
PRODUCT_LINK_SELECTORS = [
    "a[href*='/buyonline/']",
    "a[href*='/kid/']",
    ".product-item a",
    ".productListing a",
    "div.item a",
    "li.product a",
    "a[href*='/online/']",
]

IMG_SELECTORS = [
    "img[src*='/images/product/']",  # Direct kapruka CDN images
    "img[src*='kapruka.com/images']",
    "img[data-src*='/images/product/']",
    "img.lazy",
    "img[src]",
]


def _full_url(src: str) -> str:
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return "https://www.kapruka.com" + src
    return src


def _is_real_product_image(src: str) -> bool:
    """
    Return True only for real Kapruka product CDN images.
    Rejects banners, icons, and UI assets.

    Real image patterns (verified from live site):
        static2.kapruka.com/product-image/...
        partnercentral.kapruka.com/kapruka-pc/assets/images/product/...
    """
    if not src:
        return False
    return "static2.kapruka.com" in src or "partnercentral.kapruka.com" in src


async def _scroll_and_load_more(page: Page, max_rounds: int = 8) -> None:
    """
    Scroll to the bottom repeatedly and click any 'Load More' button found.
    This triggers lazy-loading and pagination on Kapruka category pages.
    Each round scrolls to the bottom, waits for new cards, and tries to
    click 'Load More' / 'View More' / 'Show More' buttons.
    """
    LOAD_MORE_SELECTORS = [
        "button:has-text('Load More')",
        "button:has-text('View More')",
        "button:has-text('Show More')",
        "a:has-text('Load More')",
        "a:has-text('View More')",
        ".load-more",
        ".loadmore",
        "[class*='loadMore']",
        "[class*='load-more']",
        "[class*='viewMore']",
        "input[value='Load More']",
    ]
    prev_count = 0
    for round_num in range(max_rounds):
        # Scroll to bottom in steps to trigger lazy loading
        for step in [0.4, 0.7, 1.0]:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {step})")
            await asyncio.sleep(0.6)

        # Try to click any "Load More" button
        clicked = False
        for sel in LOAD_MORE_SELECTORS:
            try:
                btn = await page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await asyncio.sleep(2.5)
                    clicked = True
                    print(f"      Clicked '{sel}' (round {round_num + 1})")
                    break
            except Exception:
                pass

        # Count current product cards
        cards = await page.query_selector_all("a[href*='/buyonline/']")
        current_count = len(cards)
        print(f"      Round {round_num + 1}: {current_count} product cards visible")

        # Stop if no new cards appeared after a click attempt
        if current_count == prev_count:
            break
        prev_count = current_count

        # Stop if we already have enough unique images
        if current_count >= MAX_PER_CATEGORY:
            break

        if not clicked:
            # No button found — try one more scroll and stop
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
            new_cards = await page.query_selector_all("a[href*='/buyonline/']")
            if len(new_cards) == current_count:
                break


async def scrape_category(page: Page, category: str, url: str) -> list[dict]:
    """Scrape image URLs from a Kapruka category page."""
    print(f"\n  Scraping [{category}] -> {url}")
    scraped = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(4)

        actual_url = page.url
        print(f"    Landed: {actual_url}")

        # Scroll + Load More to surface as many product cards as possible
        print(f"    Loading more products...")
        await _scroll_and_load_more(page, max_rounds=8)

        # Final scroll to ensure all lazy images are triggered
        for step in [0.25, 0.5, 0.75, 1.0]:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {step})")
            await asyncio.sleep(0.5)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1.0)

        # ── Strategy 1: product cards via a[href*='/buyonline/'] ─────────────
        # These anchor tags wrap each product card and contain the product img.
        # Real images are lazy-loaded into data-src; fall back to src.
        collected_imgs = set()
        cards = await page.query_selector_all("a[href*='/buyonline/']")
        print(f"    Product cards (a[href*='/buyonline/']): {len(cards)}")

        for card in cards[:MAX_PER_CATEGORY]:
            try:
                href = await card.get_attribute("href") or ""
                prod_url = _full_url(href)

                img_el = await card.query_selector("img")
                if img_el:
                    src = (
                        await img_el.get_attribute("data-src")
                        or await img_el.get_attribute("src")
                        or ""
                    )
                    if _is_real_product_image(src) and src not in collected_imgs:
                        collected_imgs.add(src)
                        name_el = await card.query_selector(
                            ".name, .title, .product-name, span, p"
                        )
                        name = ""
                        if name_el:
                            name = (await name_el.inner_text()).strip()
                        scraped.append({
                            "product_name": name,
                            "image_url": _full_url(src),
                            "product_url": prod_url,
                        })
            except Exception:
                pass

        print(f"    Strategy 1 (product cards): {len(scraped)} real images")

        # ── Strategy 2: a[href*='/kid/'] fallback ────────────────────────────
        if not scraped:
            print(f"    Trying a[href*='/kid/'] fallback...")
            links = await page.query_selector_all("a[href*='/kid/']")
            print(f"    Links via '/kid/': {len(links)}")
            for link in links[:MAX_PER_CATEGORY]:
                try:
                    href = await link.get_attribute("href") or ""
                    img_el = await link.query_selector("img")
                    if img_el:
                        src = (
                            await img_el.get_attribute("data-src")
                            or await img_el.get_attribute("src")
                            or ""
                        )
                        if _is_real_product_image(src) and src not in collected_imgs:
                            collected_imgs.add(src)
                            scraped.append({
                                "product_name": "",
                                "image_url": _full_url(src),
                                "product_url": _full_url(href),
                            })
                except Exception:
                    pass
            print(f"    Strategy 2 (/kid/ links): {len(scraped)} real images")

        # ── Strategy 3: regex scan of page HTML for static2 CDN URLs ─────────
        if not scraped:
            print(f"    Scanning page HTML for static2.kapruka.com URLs...")
            import re
            html = await page.content()
            # Match real product CDN images in HTML source
            matches = re.findall(
                r'(https?://static2\.kapruka\.com/product-image/[^\s"\'<>]+)',
                html,
                re.IGNORECASE,
            )
            # Also match partnercentral CDN
            matches += re.findall(
                r'(https?://partnercentral\.kapruka\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
                html,
                re.IGNORECASE,
            )
            unique = list(dict.fromkeys(matches))  # deduplicate, preserve order
            print(f"    Regex found {len(unique)} CDN image URLs in HTML")
            for img_url in unique[:MAX_PER_CATEGORY]:
                scraped.append({"product_name": "", "image_url": img_url, "product_url": ""})

    except Exception as e:
        print(f"    [ERROR] {category}: {e}")

    print(f"    Result: {len(scraped)} image URLs collected")
    return scraped


async def run_scraper() -> dict[str, list[dict]]:
    print("\n[Step 1] Launching browser and scraping Kapruka category pages...")
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
        )
        # Mask webdriver flag
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        for category, url in CATEGORY_URLS.items():
            results[category] = await scrape_category(page, category, url)
            await asyncio.sleep(2)

        await browser.close()
    return results


def patch_catalog(scraped: dict[str, list[dict]]) -> int:
    """Assign real scraped image URLs round-robin to catalog products by category."""
    catalog_path = Path("data/catalog.json")
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    is_wrapped = isinstance(data, dict) and "products" in data
    products = data.get("products", data) if is_wrapped else data

    patched = 0
    for cat_key, items in scraped.items():
        real_imgs = [i["image_url"] for i in items if i.get("image_url")]
        if not real_imgs:
            print(f"  [!] No images for '{cat_key}' — skipping")
            continue

        cat_aliases = CATALOG_CAT_MAP.get(cat_key, [cat_key])
        targets = [
            p for p in products
            if p.get("category", "").lower() in cat_aliases
            and not p.get("image_url")
        ]

        for i, product in enumerate(targets):
            product["image_url"] = real_imgs[i % len(real_imgs)]
            patched += 1

        print(f"  {cat_key}: {len(real_imgs)} real images -> {len(targets)} products patched")

    if is_wrapped:
        data["products"] = products
        out = data
    else:
        out = products

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    return patched


async def main():
    print("=" * 60)
    print("Kapruka Real Image URL Scraper")
    print("=" * 60)

    scraped = await run_scraper()

    # Save cache
    cache_path = Path("data/image_url_cache.json")
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(scraped, f, indent=2)

    total = sum(len(v) for v in scraped.values())
    print(f"\n  Total image URLs scraped: {total}")
    for cat, items in scraped.items():
        print(f"  {cat}: {len(items)}")

    if total == 0:
        print("\n[!] Zero images scraped.")
        print("    Kapruka may be blocking headless browsers or the page structure changed.")
        print("    Check data/image_url_cache.json and run inspect_kapruka.py to debug.")
        sys.exit(1)

    print("\n[Step 2] Patching catalog.json...")
    patched = patch_catalog(scraped)
    print(f"\n[OK] {patched} products now have real Kapruka image URLs.")
    print("     Next step: python -m src.crawler.image_downloader")


if __name__ == "__main__":
    asyncio.run(main())
