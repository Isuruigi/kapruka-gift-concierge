"""
Qdrant Image Vector Store — manages the CLIP image collection.

This is a SEPARATE Qdrant collection from the text collection.
Collection name: kapruka_clip_images
Vector size: 512 (CLIP embedding dimension)
Distance: Cosine

Each point in this collection represents ONE product image.
Payload includes: product_id, product_name, category, price_lkr,
                  image_url, local_image_path, url (product page)

Usage:
    store = ImageVectorStore()
    store.create_collection()
    store.ingest_images()                     # Run once
    results = store.search("red velvet cake") # Text -> image retrieval
"""

import json
from pathlib import Path
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from config.settings import Settings
from src.multimodal.clip_encoder import CLIPEncoder


settings = Settings()


class ImageVectorStore:
    """
    Manages the CLIP image embeddings collection in Qdrant.
    Provides ingest and search functionality.
    """

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self.encoder = CLIPEncoder()
        self.collection_name = settings.QDRANT_CLIP_COLLECTION
        self.vector_size = settings.CLIP_EMBEDDING_DIM

    def create_collection(self, recreate: bool = False):
        """
        Create the CLIP image collection in Qdrant.

        Args:
            recreate: If True, delete and recreate (use for fresh ingest)
        """
        existing = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in existing:
            if recreate:
                self.client.delete_collection(self.collection_name)
                logger.info(f"  Deleted existing collection: {self.collection_name}")
            else:
                logger.info(f"  Collection already exists: {self.collection_name}")
                return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"  Created collection: {self.collection_name} (dim={self.vector_size})")

    def ingest_images(self, batch_size: int = 50):
        """
        Main ingestion pipeline:
        1. Load data/image_manifest.json (product_id -> local_path mapping)
        2. Load data/catalog.json (product metadata)
        3. Encode all images with CLIP
        4. Upsert into Qdrant with product metadata as payload

        Run this ONCE after downloading images.
        """
        # Load manifest
        manifest_path = Path("data/image_manifest.json")
        if not manifest_path.exists():
            raise FileNotFoundError(
                "data/image_manifest.json not found. "
                "Run src/crawler/image_downloader.py first."
            )
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Load catalog for metadata enrichment
        catalog_path = Path("data/catalog.json")
        with open(catalog_path) as f:
            catalog_raw = json.load(f)
        products = catalog_raw.get("products", catalog_raw) if isinstance(catalog_raw, dict) else catalog_raw
        product_map = {p["product_id"]: p for p in products}

        logger.info(f"Starting CLIP image ingestion")
        logger.info(f"   Images in manifest: {len(manifest)}")
        logger.info(f"   Products in catalog: {len(product_map)}")

        # Build (path, product_data) pairs
        valid_pairs = []
        for entry in manifest:
            pid = entry["product_id"]
            local_path = Path(entry["local_path"])
            if local_path.exists() and pid in product_map:
                valid_pairs.append((local_path, product_map[pid]))
            else:
                logger.debug(f"  Skipping {pid}: image missing or not in catalog")

        logger.info(f"   Valid pairs for encoding: {len(valid_pairs)}")

        # Encode images in batches
        image_paths = [p for p, _ in valid_pairs]
        encoded = self.encoder.encode_images_batch(image_paths, batch_size=32)

        # Build a path -> embedding lookup
        path_to_embedding = {str(path): emb for path, emb in encoded}

        # Build Qdrant points
        points = []
        for idx, (path, product) in enumerate(valid_pairs):
            emb = path_to_embedding.get(str(path))
            if emb is None:
                continue

            payload = {
                "product_id": product["product_id"],
                "product_name": product.get("product_name", ""),
                "category": product.get("category", ""),
                "price_lkr": float(product.get("price_lkr", 0)),
                "image_url": product.get("image_url", ""),
                "local_image_path": str(path),
                "product_url": product.get("url", ""),
                "tags": product.get("tags", []),
                "contains_allergens": product.get("contains_allergens", []),
                "description": product.get("description", "")[:300],  # Truncate for payload size
            }
            points.append(PointStruct(id=idx, vector=emb, payload=payload))

        # Upsert in batches
        total_upserted = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
            total_upserted += len(batch)
            logger.info(f"  Upserted {total_upserted} / {len(points)} vectors")

        logger.info(f"CLIP ingestion complete | {total_upserted} image vectors in Qdrant")

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
    ) -> list[dict]:
        """
        Cross-modal search: text query -> image results.

        The query text is encoded with CLIP's TEXT encoder.
        Results come from the IMAGE collection.
        This works because CLIP aligns both modalities in the same vector space.

        Args:
            query: Natural language query (e.g. "chocolate birthday cake")
            top_k: Number of results to return
            category_filter: Optional category to filter (e.g. "cakes")

        Returns:
            List of dicts with product metadata + similarity score
        """
        # Encode text query with CLIP text encoder
        query_vector = self.encoder.encode_text(query)

        # Build optional category filter
        qdrant_filter = None
        if category_filter:
            qdrant_filter = Filter(
                must=[FieldCondition(
                    key="category",
                    match=MatchValue(value=category_filter)
                )]
            )

        # Fetch more candidates than top_k so we can deduplicate by image_url
        # and still return top_k *unique* visual matches.
        fetch_limit = top_k * 5
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=fetch_limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        # Deduplicate by image_url — multiple products can share the same
        # image (round-robin assignment) and therefore the same CLIP embedding.
        # Keep only the highest-scoring product per unique image.
        seen_images: set[str] = set()
        unique_results = []
        for result in results.points:
            img_url = result.payload.get("image_url", result.payload.get("local_image_path", ""))
            if img_url not in seen_images:
                seen_images.add(img_url)
                unique_results.append({
                    "product": result.payload,
                    "clip_score": result.score,
                    "retrieval_mode": "clip_image",
                })
            if len(unique_results) >= top_k:
                break

        return unique_results

    def get_collection_info(self) -> dict:
        """Return collection stats."""
        info = self.client.get_collection(self.collection_name)
        # qdrant-client >=1.7 uses points_count; older used vectors_count
        count = getattr(info, "points_count", None) or getattr(info, "vectors_count", 0)
        return {
            "name": self.collection_name,
            "vectors_count": count,
            "vector_size": self.vector_size,
            "distance": "Cosine",
        }
