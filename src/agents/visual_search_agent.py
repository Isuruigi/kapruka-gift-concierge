"""
Visual Search Agent — 6th specialist agent in the Gift-Concierge system.

This agent handles queries that benefit from visual product retrieval.
It uses the Fusion Ranker to combine text RAG + CLIP image retrieval,
then uses Claude to generate a visually-aware recommendation.

Key difference from CatalogSpecialist:
    CatalogSpecialist -> text search only
    VisualSearchAgent -> text search + image search + fusion ranking
                        Claude response includes visual context

Triggered when:
    - Router detects visual intent keywords (color, looks like, appearance, etc.)
    - OR as a parallel call alongside CatalogSpecialist for gift queries
"""

from loguru import logger
from src.llm.client import LLMClient
from src.memory.long_term import CatalogVectorStore
from src.multimodal.image_store import ImageVectorStore
from src.multimodal.fusion_ranker import FusionRanker
from config.settings import Settings

settings = Settings()

# ─── Fix: CatalogVectorStore requires settings to be passed ──────────────────


class VisualSearchAgent:
    """
    Multimodal gift recommendation agent combining text + visual retrieval.
    """

    def __init__(self, llm_client: LLMClient, settings):
        self.llm = llm_client
        self.settings = settings
        self.text_store = CatalogVectorStore(settings)   # ← FIX: requires settings arg
        self.image_store = ImageVectorStore()
        self.fusion_ranker = FusionRanker()

    def search(
        self,
        query: str,
        recipient_context: str = "",
        budget_max: float | None = None,
        occasion: str | None = None,
        top_k: int = 5,
    ) -> str:
        """
        Multimodal gift search and recommendation.

        Pipeline:
            1. Text RAG search (existing collection)
            2. CLIP image search (new image collection)
            3. Fusion ranking (weighted merge)
            4. Claude generates recommendation with visual context

        Args:
            query: Natural language gift request
            recipient_context: Formatted recipient profile (allergies, preferences)
            budget_max: Maximum price in LKR
            occasion: Occasion context
            top_k: Number of fused results to consider

        Returns:
            Formatted recommendation string
        """
        logger.info(f"VisualSearchAgent | Query: '{query}'")

        # Step 1: Text RAG retrieval
        text_results = self.text_store.search(query=query, top_k=top_k)
        logger.debug(f"  Text RAG: {len(text_results)} results")

        # Step 2: CLIP image retrieval (cross-modal)
        image_results = self.image_store.search(query=query, top_k=top_k)
        logger.debug(f"  CLIP image: {len(image_results)} results")

        # Step 3: Fusion ranking
        fused_results = self.fusion_ranker.fuse(
            text_results=text_results,
            image_results=image_results,
            top_k=top_k,
        )
        logger.debug(f"  Fused: {len(fused_results)} results")

        # Step 4: Apply budget filter post-fusion
        if budget_max:
            fused_results = [
                r for r in fused_results
                if r["product"].get("price_lkr", 0) <= budget_max
            ] or fused_results  # Fallback to all if nothing fits budget

        # Step 5: Generate recommendation with Claude
        return self._generate_recommendation(
            fused_results=fused_results,
            query=query,
            recipient_context=recipient_context,
            occasion=occasion,
            budget_max=budget_max,
        )

    def _generate_recommendation(
        self,
        fused_results: list[dict],
        query: str,
        recipient_context: str,
        occasion: str | None,
        budget_max: float | None,
    ) -> str:
        """Generate a visually-aware recommendation using Claude."""

        # Format fused results for the prompt
        products_text = ""
        for i, r in enumerate(fused_results, 1):
            p = r["product"]
            products_text += f"""
Product {i}: {p.get('product_name', 'N/A')}
  Price: LKR {p.get('price_lkr', 0):,.0f}
  Category: {p.get('category', 'N/A')}
  Description: {p.get('description', 'N/A')[:150]}
  Allergens: {', '.join(p.get('contains_allergens', [])) or 'None listed'}
  Tags: {', '.join(p.get('tags', []))}
  Retrieval: {r['retrieval_source']} (confidence: {r['fused_score']:.2f})
  Visual match score: {r['image_score']:.2f} | Text match score: {r['text_score']:.2f}
  URL: {p.get('product_url', p.get('url', 'N/A'))}
"""

        system_prompt = """You are the Visual Gift Specialist for Kapruka.com's Gift-Concierge.
You have access to BOTH text descriptions AND visual similarity scores for each product.
Products with high visual match scores were retrieved because they look similar to what was requested.

Your job:
1. Recommend the best 2-3 gifts based on text + visual match combined
2. Mention if a product is a strong VISUAL match (high image score)
3. Always check allergens — NEVER recommend products with allergens the recipient can't have
4. Keep recommendations warm and personal — like a knowledgeable Sri Lankan gift shop assistant
5. Always include the price in LKR and product URL"""

        user_prompt = f"""User request: "{query}"
Occasion: {occasion or 'Not specified'}
Budget: {f'LKR {budget_max:,.0f}' if budget_max else 'Not specified'}

RECIPIENT PROFILE:
{recipient_context or 'No profile provided'}

PRODUCTS (ranked by combined text + visual relevance):
{products_text}

Generate a personalized gift recommendation. Note any products with strong visual matches.
Highlight top 2-3 options. Explain fit for the recipient and occasion."""

        return self.llm.call(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.3,
        )
