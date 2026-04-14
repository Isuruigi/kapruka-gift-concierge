"""
Fusion Ranker — combines Text RAG results + CLIP Image results
into a single ranked list with unified confidence scores.

Why fusion?
    Text RAG is excellent at matching semantic descriptions.
    CLIP is excellent at visual similarity.
    Combined, they catch what either misses alone.

Algorithm:
    1. Normalize scores from both retrievers to [0, 1]
    2. For products appearing in BOTH results -> weighted sum
    3. For products in only one -> score x that layer's weight
    4. Sort by fused_score descending
    5. Return top_k with full metadata + score breakdown

Config (in settings.py):
    FUSION_TEXT_WEIGHT = 0.6   (text contributes 60%)
    FUSION_IMAGE_WEIGHT = 0.4  (image contributes 40%)
"""

from loguru import logger
from config.settings import Settings

settings = Settings()


class FusionRanker:
    """
    Merges and re-ranks results from text RAG and CLIP image retrieval.
    """

    def __init__(
        self,
        text_weight: float = None,
        image_weight: float = None,
    ):
        self.text_weight = text_weight or settings.FUSION_TEXT_WEIGHT
        self.image_weight = image_weight or settings.FUSION_IMAGE_WEIGHT
        # Validate weights sum to 1
        assert abs(self.text_weight + self.image_weight - 1.0) < 0.01, \
            "Fusion weights must sum to 1.0"

    def fuse(
        self,
        text_results: list[dict],
        image_results: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Fuse text RAG and CLIP image results into a single ranked list.

        Args:
            text_results: From CatalogVectorStore.search() — list of {product, score}
            image_results: From ImageVectorStore.search() — list of {product, clip_score}
            top_k: How many fused results to return

        Returns:
            List of fused result dicts sorted by fused_score descending.
            Each dict contains:
                - product: full product metadata
                - fused_score: combined score (0-1)
                - text_score: original text RAG score (0-1 or None)
                - image_score: original CLIP score (0-1 or None)
                - retrieval_source: "text_only" | "image_only" | "both"
        """
        # Build lookup: product_id -> scores from each layer
        text_lookup = {}
        for r in text_results:
            pid = r["product"].get("product_id", r["product"].get("id", ""))
            text_lookup[pid] = {
                "product": r["product"],
                "text_score": r.get("score", r.get("text_score", 0)),
            }

        image_lookup = {}
        for r in image_results:
            pid = r["product"].get("product_id", "")
            image_lookup[pid] = {
                "product": r["product"],
                "image_score": r.get("clip_score", r.get("image_score", 0)),
            }

        # Normalize scores to [0, 1] within each result set
        text_lookup = self._normalize_scores(text_lookup, "text_score")
        image_lookup = self._normalize_scores(image_lookup, "image_score")

        # Merge all unique product IDs
        all_pids = set(text_lookup.keys()) | set(image_lookup.keys())

        fused = []
        for pid in all_pids:
            in_text = pid in text_lookup
            in_image = pid in image_lookup

            text_score = text_lookup[pid]["text_score"] if in_text else 0.0
            image_score = image_lookup[pid]["image_score"] if in_image else 0.0

            # Product metadata — prefer text (richer payload), fall back to image
            product = (
                text_lookup[pid]["product"] if in_text
                else image_lookup[pid]["product"]
            )

            # Compute fused score
            if in_text and in_image:
                fused_score = (self.text_weight * text_score) + (self.image_weight * image_score)
                source = "both"
            elif in_text:
                fused_score = self.text_weight * text_score
                source = "text_only"
            else:
                fused_score = self.image_weight * image_score
                source = "image_only"

            fused.append({
                "product": product,
                "fused_score": round(fused_score, 4),
                "text_score": round(text_score, 4),
                "image_score": round(image_score, 4),
                "retrieval_source": source,
            })

        # Sort by fused score descending
        fused.sort(key=lambda x: x["fused_score"], reverse=True)

        logger.debug(f"Fusion: {len(text_results)} text + {len(image_results)} image -> {len(fused)} merged -> top {top_k}")

        return fused[:top_k]

    def _normalize_scores(self, lookup: dict, score_key: str) -> dict:
        """Min-max normalize scores within a result set to [0, 1]."""
        if not lookup:
            return lookup
        scores = [v[score_key] for v in lookup.values()]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return lookup  # All scores equal — leave as-is
        for pid in lookup:
            lookup[pid][score_key] = (lookup[pid][score_key] - min_s) / (max_s - min_s)
        return lookup
