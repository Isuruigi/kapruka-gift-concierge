"""
setup_ingest.py - One-time Catalog Ingestion Script
====================================================
Run this ONCE after installing requirements to:
  1. Generate the catalog (via crawler or fallback)
  2. Create the Qdrant collection
  3. Embed and upsert all products

Usage:
    python setup_ingest.py
    python setup_ingest.py --force-fallback   # skip live crawl
    python setup_ingest.py --recreate         # recreate collection
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from src.crawler.kapruka_scraper import KaprukaScraper
from src.memory.long_term import CatalogVectorStore


def main():
    parser = argparse.ArgumentParser(description="Kapruka catalog ingestion script")
    parser.add_argument("--force-fallback", action="store_true",
                        help="Skip live crawl and use programmatic fallback catalog")
    parser.add_argument("--recreate", action="store_true",
                        help="Recreate (drop and re-create) the Qdrant collection")
    parser.add_argument("--skip-crawl", action="store_true",
                        help="Skip crawl if catalog.json already exists")
    args = parser.parse_args()

    settings = Settings()
    missing = settings.validate()
    if missing:
        print(f"❌ Missing env vars: {missing}")
        print("Please fill in .env with your API keys.")
        sys.exit(1)

    print("\n" + "═" * 60)
    print("  Kapruka Gift-Concierge - Catalog Ingestion")
    print("═" * 60 + "\n")

    # ── Step 1: Build catalog ──────────────────────────────
    catalog_path = settings.CATALOG_PATH

    if args.skip_crawl and catalog_path.exists():
        print(f"⏭️  Skipping crawl - {catalog_path} already exists ({catalog_path.stat().st_size // 1024}KB)")
    else:
        crawl_mode = "fallback" if args.force_fallback else "live + fallback"
        print(f"🕷️  Phase 1: Crawling catalog ({crawl_mode})…")

        scraper = KaprukaScraper(settings)

        if args.force_fallback:
            scraper._use_fallback_catalog()
            catalog = scraper._build_catalog()
        else:
            catalog = asyncio.run(scraper.scrape_all_categories())

        scraper.save_catalog(catalog, catalog_path)
        print(f"   ✅ {catalog.total_products} products saved\n")

    # ── Step 2: Create Qdrant collection ───────────────────
    print("🗄️  Phase 2: Setting up Qdrant collection…")
    store = CatalogVectorStore(settings)
    store.create_collection(recreate=args.recreate)

    # Check if already ingested and not recreating
    info = store.get_collection_info()
    if info.get("points_count", 0) > 0 and not args.recreate:
        print(f"ℹ️  Collection already has {info['points_count']} points - skipping ingest")
        print("   Use --recreate to force re-ingest.\n")
    else:
        # ── Step 3: Ingest ─────────────────────────────────
        print(f"\n📡 Phase 3: Ingesting catalog into Qdrant…")
        store.ingest_catalog(catalog_path)
        final_info = store.get_collection_info()
        print(f"   ✅ {final_info['points_count']} vectors stored\n")

    print("═" * 60)
    print("✅ Setup complete! You can now run:")
    print("   • streamlit run ui/streamlit_app.py")
    print("   • python -m pytest tests/")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
