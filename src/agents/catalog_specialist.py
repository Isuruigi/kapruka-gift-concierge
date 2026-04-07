"""
CatalogSpecialist - RAG Product Search Agent (Agent 2 of 3)
===========================================================
Combines Qdrant vector search + recipient profile context
to generate personalised gift recommendations.

Pipeline:
  1. Build enriched search query
  2. Search Qdrant (auto-filters allergens via MemoryManager)
  3. Format products + recipient context
  4. LLM generates a warm, tailored recommendation
"""

from src.llm.client import LLMClient
from src.memory.manager import MemoryManager


SYSTEM_PROMPT = """\
You are the Catalog Specialist for Kapruka.com's Gift-Concierge - Sri Lanka's leading online gift store.
Your job is to recommend the BEST gift(s) from the search results based on:
1. The user's original request
2. The recipient's full profile (preferences, allergies, budget, past gifts)
3. The occasion

CRITICAL SAFETY RULES:
- NEVER recommend products containing allergens the recipient is allergic to
- If allergen information is unclear for a product, FLAG it clearly
- Always state the price in LKR
- Be warm and helpful - like a knowledgeable Sri Lankan gift shop assistant
- Suggest 2–3 ranked options; explain WHY each fits this specific recipient
- Mention relevant tags (nut-free, dairy-free, etc.) to reassure the user
- Explicitly include the official buying link (URL) for each recommended product so the user can easily purchase it

Sri Lankan cultural sensitivity:
- For Avurudu (New Year) → traditional sweets, fruits, religious items
- Perishable items (cakes, flowers) → remind about delivery zone restrictions
- Formal relationships (boss) → keep recommendations professional
- Children → age-appropriate, always flag allergies prominently

Format your response in a friendly, conversational tone.
"""


class CatalogSpecialist:
    """RAG-powered product search and recommendation agent."""

    def __init__(self, llm_client: LLMClient, memory_manager: MemoryManager):
        self.llm = llm_client
        self.memory = memory_manager

    def search_and_recommend(
        self,
        query: str,
        recipient_key: str = None,
        occasion: str = None,
        budget_max: float = None,
        top_k: int = None,
    ) -> dict:
        """
        Main entry: search catalog and generate a personalised recommendation.

        Returns:
            {
                "products_found": [...],
                "recommendation_text": "...",
                "recipient_context_used": "...",
                "search_query_used": "...",
            }
        """
        top_k = top_k or self.memory.settings.LONG_TERM_SEARCH_TOP_K

        # 1. Build enriched search query
        search_query = self._build_search_query(query, occasion, budget_max, recipient_key)

        # 2. Search - MemoryManager auto-filters allergens if recipient_key known
        products = self.memory.search_products(
            query=search_query,
            recipient_key=recipient_key,
            top_k=top_k,
        )

        # 3. Get recipient context
        recipient_context = "No recipient profile available."
        if recipient_key:
            profile_text = self.memory.semantic.format_for_prompt(recipient_key)
            if profile_text:
                recipient_context = profile_text

        # 4. Apply budget filter (client-side, after RAG)
        if budget_max:
            products = [
                p for p in products
                if p["product"]["price_lkr"] <= budget_max
            ] or products  # fall back to all if nothing in budget

        # 5. LLM recommendation
        recommendation = self._generate_recommendation(
            products=products,
            recipient_context=recipient_context,
            original_query=query,
            occasion=occasion,
            budget_max=budget_max,
        )

        return {
            "products_found": products,
            "recommendation_text": recommendation,
            "recipient_context_used": recipient_context,
            "search_query_used": search_query,
        }

    # ── Internal ──────────────────────────────────────────

    def _build_search_query(
        self,
        query: str,
        occasion: str = None,
        budget: float = None,
        recipient_key: str = None,
    ) -> str:
        """Enrich the raw user query for better vector search."""
        parts = [query]
        if occasion:
            parts.append(f"for {occasion}")
        # Note: Do NOT append all historical preferences to the vector query. 
        # It pollutes the embedding (e.g., retrieving 'red roses' when user strictly asked for 'chocolate').
        # The LLM prompt already receives the full profile to rank/filter results.
        return " ".join(parts)

    def _generate_recommendation(
        self,
        products: list[dict],
        recipient_context: str,
        original_query: str,
        occasion: str = None,
        budget_max: float = None,
    ) -> str:
        """Use LLM to generate a warm, personalised recommendation."""
        if not products:
            return (
                "I'm sorry, I couldn't find suitable products matching your request "
                "in our catalog right now. Could you try a different category or budget range?"
            )

        # Format products for the prompt
        import urllib.parse
        products_text = ""
        for i, p in enumerate(products, 1):
            prod = p["product"]
            allergens = ", ".join(prod.get("contains_allergens", [])) or "None listed"
            tags = ", ".join(prod.get("tags", [])) or "No special tags"
            
            # Since some URLs are mock data, use Kapruka's search URL to ensure no 404s
            encoded_name = urllib.parse.quote(prod['product_name'])
            safe_url = f"https://www.kapruka.com/sri_lanka_search.jsp?searchWord={encoded_name}"
            
            products_text += (
                f"\nProduct {i}: {prod['product_name']}\n"
                f"  Price    : LKR {prod['price_lkr']:,.0f}\n"
                f"  Category : {prod['category']}\n"
                f"  Desc     : {prod.get('description', 'N/A')[:150]}\n"
                f"  Allergens: {allergens}\n"
                f"  Tags     : {tags}\n"
                f"  URL      : {safe_url}\n"
                f"  Score    : {p['score']:.3f}\n"
            )

        user_prompt = (
            f'User asked: "{original_query}"\n'
            f"Occasion: {occasion or 'Not specified'}\n"
            f"Budget limit: {'LKR {:,.0f}'.format(budget_max) if budget_max else 'Not specified'}\n\n"
            f"RECIPIENT PROFILE:\n{recipient_context}\n\n"
            f"AVAILABLE PRODUCTS FROM CATALOG (allergen-filtered):\n{products_text}\n\n"
            "Generate a friendly, personalised recommendation. "
            "Rank the top 2–3 options, clearly explain why each fits this recipient, "
            "and explicitly include the exact URL (buying link) for each product."
        )

        return self.llm.call(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_prompt,
            temperature=self.llm.settings.LLM_TEMPERATURE_CREATIVE,
            max_tokens=1500,
        )
