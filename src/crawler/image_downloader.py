"""
Image Downloader for Kapruka products.

Reads the existing data/catalog.json, downloads product images
for target categories, and saves them to data/images/.

This is a standalone script — run it ONCE after the main crawl.
It does NOT re-scrape Kapruka. It simply downloads the image_url
that the existing crawler already saved into catalog.json.

Usage:
    python -m src.crawler.image_downloader

Output:
    data/images/{product_id}.jpg    <- one file per product
    data/image_manifest.json        <- maps product_id -> local image path
"""

import json
import asyncio
import aiohttp
from pathlib import Path
from loguru import logger
from config.settings import Settings


settings = Settings()

# ─── Target categories (visual gifting items only) ────────────────────────────
TARGET_CATEGORIES = settings.IMAGE_CRAWL_CATEGORIES
MAX_IMAGES = settings.IMAGE_CRAWL_LIMIT
IMAGE_DIR = settings.IMAGE_DIR
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def download_image(
    session: aiohttp.ClientSession,
    product_id: str,
    image_url: str,
    output_dir: Path,
) -> dict | None:
    """
    Download a single product image.

    Args:
        session: aiohttp session
        product_id: Product ID (used as filename)
        image_url: URL to download from
        output_dir: Local directory to save into

    Returns:
        dict with {product_id, local_path, status} or None on failure
    """
    if not image_url or image_url == "":
        return None

    output_path = output_dir / f"{product_id}.jpg"

    # Skip if already downloaded
    if output_path.exists():
        return {"product_id": product_id, "local_path": str(output_path), "status": "cached"}

    try:
        async with session.get(image_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                content = await resp.read()
                # Validate it's actually an image.
                # Accept: JPEG, PNG, GIF, WebP (RIFF....WEBP), AVIF/generic
                # Also fall back to content-type header for CDN-served images.
                content_type = resp.headers.get("content-type", "")
                is_image_by_magic = (
                    content[:3] == b'\xff\xd8\xff'      # JPEG
                    or content[:8] == b'\x89PNG\r\n\x1a\n'  # PNG
                    or content[:3] == b'GIF'             # GIF
                    or (content[:4] == b'RIFF' and content[8:12] == b'WEBP')  # WebP
                )
                is_image_by_header = "image/" in content_type
                if is_image_by_magic or is_image_by_header:
                    with open(output_path, "wb") as f:
                        f.write(content)
                    logger.debug(f"  Downloaded: {product_id}")
                    return {"product_id": product_id, "local_path": str(output_path), "status": "downloaded"}
                else:
                    logger.warning(f"  Not an image: {product_id} (content-type: {content_type}, bytes: {content[:4]})")
                    return None
            else:
                logger.warning(f"  HTTP {resp.status}: {product_id}")
                return None
    except Exception as e:
        logger.error(f"  Failed {product_id}: {e}")
        return None


async def download_all_images() -> list[dict]:
    """
    Main function — loads catalog.json, filters target categories,
    downloads images concurrently (batch of 20 at a time).

    Returns:
        List of manifest entries [{product_id, local_path, status}]
    """
    # Load existing catalog
    catalog_path = Path("data/catalog.json")
    if not catalog_path.exists():
        raise FileNotFoundError("data/catalog.json not found. Run the main crawler first.")

    with open(catalog_path) as f:
        catalog = json.load(f)

    products = catalog.get("products", catalog) if isinstance(catalog, dict) else catalog

    # Filter to target categories with valid image URLs
    targets = [
        p for p in products
        if p.get("category", "").lower() in [c.lower() for c in TARGET_CATEGORIES]
        and p.get("image_url")
    ][:MAX_IMAGES]

    logger.info(f"Image download starting | {len(targets)} products targeted")
    logger.info(f"   Categories: {TARGET_CATEGORIES}")
    logger.info(f"   Output dir: {IMAGE_DIR}")

    manifest = []
    connector = aiohttp.TCPConnector(limit=20)  # 20 concurrent downloads
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            download_image(session, p["product_id"], p["image_url"], IMAGE_DIR)
            for p in targets
        ]
        results = await asyncio.gather(*tasks)
        manifest = [r for r in results if r is not None]

    # Save manifest
    manifest_path = Path("data/image_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    downloaded = sum(1 for r in manifest if r["status"] == "downloaded")
    cached = sum(1 for r in manifest if r["status"] == "cached")
    logger.info(f"Done | Downloaded: {downloaded} | Cached: {cached} | Total: {len(manifest)}")

    return manifest


if __name__ == "__main__":
    asyncio.run(download_all_images())
