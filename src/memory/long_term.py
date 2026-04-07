"""
Tier 2: Long-Term Memory - Qdrant Vector Store (RAG)
=====================================================
Stores the Kapruka product catalog as dense vectors in Qdrant Cloud.
Uses sentence-transformers (all-MiniLM-L6-v2, 384d) - fully local, no API cost.

Key methods:
  create_collection()                  - create the Qdrant collection
  ingest_catalog(path)                 - embed and upsert all products
  search(query, top_k, filters)        - natural language semantic search
  search_excluding_allergens(...)      - search with allergen payload filter
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
import torch
from sentence_transformers import SentenceTransformer


class CatalogVectorStore:
    """Qdrant-backed RAG store for the Kapruka product catalog."""

    def __init__(self, settings):
        self.settings = settings
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION

        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        # Load the SentenceTransformer model (downloads once, cached locally)
        # PyTorch 2.6+ fix: force float32 + CPU to avoid meta tensor copy error
        print(f"📦 Loading embedding model: {settings.EMBEDDING_MODEL}…")
        self.encoder = self._load_encoder(settings.EMBEDDING_MODEL)
        print("✅ Embedding model ready")

    # ── Encoder loader (PyTorch 2.6+ compatible) ──────────

    @staticmethod
    def _load_encoder(model_name: str) -> SentenceTransformer:
        """
        Load SentenceTransformer safely.
        Forces float32 + CPU to avoid PyTorch meta tensor and CUDA assert errors.
        """
        import os
        
        # Aggressively prevent this layer from ever touching the GPU to avoid 
        # CUDA device-side assertion failures on uninitialized/meta embeddings.
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

        try:
            # Try loading normally on CPU
            return SentenceTransformer(model_name, device="cpu")
        except Exception as e:
            # Fallback for PyTorch 2.6+ meta tensor restriction
            import torch
            try:
                return SentenceTransformer(
                    model_name, 
                    device="cpu", 
                    model_kwargs={"torch_dtype": torch.float32}
                )
            except Exception as e2:
                # Absolute last resort
                return SentenceTransformer(model_name)

    # ── Safe CPU encode helper ────────────────────────────

    def _encode(self, text: str):
        """Always encode on CPU regardless of system GPU availability."""
        return self.encoder.encode(
            text,
            device="cpu",
            convert_to_numpy=True,
        )

    # ── Collection management ──────────────────────────────

    def create_collection(self, recreate: bool = False):
        """Create the Qdrant collection. Optionally recreate (drops existing)."""
        existing = [c.name for c in self.qdrant.get_collections().collections]

        if self.collection_name in existing:
            if recreate:
                print(f"🗑️  Deleting existing collection: {self.collection_name}")
                self.qdrant.delete_collection(self.collection_name)
            else:
                print(f"ℹ️  Collection '{self.collection_name}' already exists - skipping create")
                return

        print(f"🏗️  Creating collection: {self.collection_name} (dim={self.dimension})")
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.dimension,
                distance=Distance.COSINE,
            ),
        )
        print(f"✅ Collection created")

    def collection_exists(self) -> bool:
        existing = [c.name for c in self.qdrant.get_collections().collections]
        return self.collection_name in existing

    # ── Ingestion ─────────────────────────────────────────

    def ingest_catalog(self, catalog_path: Path, batch_size: int = 100):
        """
        Load catalog.json and upsert all products into Qdrant.
        Builds a rich text string for each product to embed.
        """
        print(f"📂 Loading catalog from {catalog_path}…")
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = data.get("products", [])
        print(f"   {len(products)} products to ingest")

        points: list[PointStruct] = []
        texts: list[str] = []

        for product in products:
            # Build rich text for embedding
            allergen_str = ", ".join(product.get("contains_allergens", [])) or "none"
            tag_str = ", ".join(product.get("tags", [])) or "none"
            text = (
                f"{product['product_name']}. "
                f"{product.get('description', '')}. "
                f"Category: {product['category']}. "
                f"Price: {product['price_lkr']} LKR. "
                f"Tags: {tag_str}. "
                f"Allergens: {allergen_str}. "
                f"Delivery: {product.get('delivery_type', 'standard')}."
            )
            texts.append(text)
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=[],  # will be filled after batch encode
                    payload=product,
                )
            )

        # Batch encode
        print(f"🔢 Encoding {len(texts)} product embeddings…")
        vectors = self.encoder.encode(texts, batch_size=64, show_progress_bar=True)

        for i, point in enumerate(points):
            point.vector = vectors[i].tolist()

        # Batch upsert
        print(f"⬆️  Upserting {len(points)} points in batches of {batch_size}…")
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
            print(f"   Upserted {min(i + batch_size, len(points))}/{len(points)}")

        print(f"✅ Ingestion complete - {len(points)} products in Qdrant")

    # ── Search ────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Semantic search over the catalog.

        Args:
            query:   Natural language (e.g. "birthday cake nut-free")
            top_k:   Number of results
            filters: Optional Qdrant filter dict (category, price range, etc.)

        Returns:
            List of {"product": payload_dict, "score": float}
        """
        query_vector = self._encode(query).tolist()

        qdrant_filter = self._build_filter(filters) if filters else None

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [{"product": hit.payload, "score": hit.score} for hit in response.points]

    def search_excluding_allergens(
        self,
        query: str,
        allergens: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search the catalog but EXCLUDE products containing any of the given allergens.
        This is the critical allergen-safety method used by the CatalogSpecialist.

        Uses Qdrant payload filters to exclude matching allergens at the DB level.
        """
        query_vector = self._encode(query).tolist()

        # Build must_not conditions: for each allergen, exclude if contains_allergens value matches
        must_not_conditions = [
            FieldCondition(
                key="contains_allergens",
                match=MatchValue(value=allergen),
            )
            for allergen in allergens
        ]

        qdrant_filter = Filter(must_not=must_not_conditions) if must_not_conditions else None

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [{"product": hit.payload, "score": hit.score} for hit in response.points]

    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 5,
        exclude_allergens: Optional[list[str]] = None,
    ) -> list[dict]:
        """Search within a specific product category."""
        query_vector = self._encode(query).tolist()

        must_conditions = [
            FieldCondition(key="category", match=MatchValue(value=category))
        ]
        must_not_conditions = []
        if exclude_allergens:
            must_not_conditions = [
                FieldCondition(
                    key="contains_allergens",
                    match=MatchValue(value=a),
                )
                for a in exclude_allergens
            ]

        qdrant_filter = Filter(
            must=must_conditions,
            must_not=must_not_conditions if must_not_conditions else None,
        )

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [{"product": hit.payload, "score": hit.score} for hit in response.points]

    # ── Info ──────────────────────────────────────────────

    def get_collection_info(self) -> dict:
        """Return collection stats."""
        info = self.qdrant.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "status": str(info.status),
        }

    # ── Helpers ───────────────────────────────────────────

    def _build_filter(self, filters: dict) -> Optional[Filter]:
        """Convert a simple filter dict to a Qdrant Filter object."""
        conditions = []
        if "category" in filters:
            conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=filters["category"]),
                )
            )
        if "delivery_type" in filters:
            conditions.append(
                FieldCondition(
                    key="delivery_type",
                    match=MatchValue(value=filters["delivery_type"]),
                )
            )
        return Filter(must=conditions) if conditions else None
