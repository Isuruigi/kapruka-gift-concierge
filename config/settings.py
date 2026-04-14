"""Central configuration for the Kapruka Gift-Concierge Agent."""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 output to prevent Windows cp1252 emoji crash
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


class Settings:
    """All project settings in one place."""

    # === Paths ===
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    CONFIG_DIR = PROJECT_ROOT / "config"

    CATALOG_PATH = DATA_DIR / "catalog.json"
    PROFILES_PATH = DATA_DIR / "recipient_profiles.json"
    DELIVERY_ZONES_PATH = CONFIG_DIR / "delivery_zones.json"
    TEST_SCENARIOS_PATH = DATA_DIR / "test_scenarios.json"

    # === API Keys ===
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    # === LLM Settings ===
    LLM_MODEL_FAST   = "claude-3-haiku-20240307"      # Router, Catalog, Logistics
    LLM_MODEL_STRONG = "claude-3-haiku-20240307"      # Reflection critique (stronger reasoning)
    LLM_MAX_TOKENS   = 2048                            # Enough for full reflection responses
    LLM_TEMPERATURE_DETERMINISTIC = 0.0
    LLM_TEMPERATURE_CREATIVE = 0.3


    # === Embedding Settings ===
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local, free, 384 dimensions
    EMBEDDING_DIMENSION = 384

    # === Qdrant Settings ===
    QDRANT_COLLECTION_NAME = "kapruka_catalog"

    # === Crawler Settings ===
    KAPRUKA_BASE_URL = "https://www.kapruka.com"
    CRAWLER_CATEGORIES = [
        "cakes",
        "flowers",
        "chocolates",
        "gift-hampers",
        "fruit-baskets",
        "soft-toys",
        "greeting-cards",
        "electronics",
    ]
    CRAWLER_MAX_PAGES_PER_CATEGORY = 50  # Up to 50 pages per category for 10k+ items
    CRAWLER_DELAY_SECONDS = (2, 5)  # Random delay range

    # === Memory Settings ===
    SHORT_TERM_MAX_MESSAGES = 20
    LONG_TERM_SEARCH_TOP_K = 5

    # === Agent Settings ===
    REFLECTION_MAX_ITERATIONS = 2

    # ─── CLIP / Multimodal Settings ───────────────────────────────────────────────

    # CLIP model (runs on CPU, no GPU needed)
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"

    # Qdrant collection for image embeddings
    QDRANT_CLIP_COLLECTION: str = "kapruka_clip_images"

    # CLIP embedding dimension (fixed for clip-vit-base-patch32)
    CLIP_EMBEDDING_DIM: int = 512

    # Local directory to store downloaded product images
    IMAGE_DIR: Path = Path("data/images")

    # Fusion weights — how much each retrieval layer contributes to final score
    FUSION_TEXT_WEIGHT: float = 0.6    # Text RAG contributes 60%
    FUSION_IMAGE_WEIGHT: float = 0.4   # CLIP image retrieval contributes 40%

    # Target categories for image crawl (highest visual impact)
    IMAGE_CRAWL_CATEGORIES: list = ["cakes", "flowers", "hampers", "chocolates"]

    # Max products to download images for
    IMAGE_CRAWL_LIMIT: int = 400

    def validate(self) -> list[str]:
        """Check all required env vars are set. Return list of missing ones."""
        missing = []
        if not self.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not self.QDRANT_URL:
            missing.append("QDRANT_URL")
        if not self.QDRANT_API_KEY:
            missing.append("QDRANT_API_KEY")
        return missing
