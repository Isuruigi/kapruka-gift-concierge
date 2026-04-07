"""
MemoryManager - Coordinates All Three Memory Tiers
===================================================
This is the single entry point the orchestrator uses.
Never calls ConversationMemory, CatalogVectorStore, or RecipientMemory directly.

  Tier 1 (short_term)  - ConversationMemory  - rolling message buffer
  Tier 2 (long_term)   - CatalogVectorStore  - Qdrant RAG product search
  Tier 3 (semantic)    - RecipientMemory     - JSON recipient profiles
"""

from typing import Optional

from src.memory.short_term import ConversationMemory
from src.memory.long_term import CatalogVectorStore
from src.memory.semantic import RecipientMemory


class MemoryManager:
    """Coordinator for all three memory tiers."""

    def __init__(self, settings):
        self.settings = settings

        # Tier 1: short-term
        self.short_term = ConversationMemory(
            max_messages=settings.SHORT_TERM_MAX_MESSAGES
        )

        # Tier 2: long-term (Qdrant)
        self.long_term = CatalogVectorStore(settings)

        # Tier 3: semantic (recipient profiles)
        self.semantic = RecipientMemory(settings.PROFILES_PATH)

    # ── Short-term helpers ────────────────────────────────

    def add_user_message(self, message: str):
        self.short_term.add_message("user", message)

    def add_assistant_message(self, message: str):
        self.short_term.add_message("assistant", message)

    def get_conversation_context(self) -> list[dict]:
        """Anthropic-format conversation history."""
        return self.short_term.get_messages()

    def get_conversation_summary(self) -> str:
        """Short text summary for prompt injection."""
        return self.short_term.get_context_summary()

    def clear_session(self):
        """Reset short-term memory (new conversation)."""
        self.short_term.clear()

    # ── Product search (Tier 2 + Tier 3 integration) ──────

    def search_products(
        self,
        query: str,
        recipient_key: Optional[str] = None,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> list[dict]:
        """
        Search the product catalog.
        Automatically excludes allergens if a known recipient is provided.
        Optionally filters to a specific category.
        """
        allergens = []
        if recipient_key:
            allergens = self.semantic.get_allergies(recipient_key)

        if category:
            return self.long_term.search_by_category(
                query=query,
                category=category,
                top_k=top_k,
                exclude_allergens=allergens if allergens else None,
            )
        elif allergens:
            return self.long_term.search_excluding_allergens(
                query=query,
                allergens=allergens,
                top_k=top_k,
            )
        else:
            return self.long_term.search(query=query, top_k=top_k)

    # ── Recipient context (Tier 3) ─────────────────────────

    def get_recipient_context(
        self, user_message: str
    ) -> Optional[tuple[str, dict]]:
        """
        Try to identify a recipient from the user message.
        Returns (key, profile_dict) or None.
        """
        return self.semantic.find_recipient(user_message)

    def get_full_context(self, user_message: str) -> dict:
        """
        Build the complete agent decision context.

        Returns:
            {
                "conversation": str,          # recent conversation summary
                "recipient_key": str | None,  # matched recipient key
                "recipient_profile": str,     # formatted profile string
                "recipient_allergies": list,  # allergen list (may be empty)
                "recipient_location": str | None,
            }
        """
        context: dict = {
            "conversation": self.short_term.get_context_summary(),
            "recipient_key": None,
            "recipient_profile": "No recipient profile found.",
            "recipient_allergies": [],
            "recipient_location": None,
        }

        result = self.semantic.find_recipient(user_message)
        if not result:
            # Fallback to recent conversation memory if not mentioned in this turn
            result = self.semantic.find_recipient(context["conversation"])
            
        if result:
            key, _profile = result
            context["recipient_key"] = key
            context["recipient_profile"] = self.semantic.format_for_prompt(key)
            context["recipient_allergies"] = self.semantic.get_allergies(key)
            context["recipient_location"] = self.semantic.get_location(key)

        return context

    # ── Semantic memory writes ─────────────────────────────

    def update_recipient_info(self, recipient_key: str, updates: dict):
        """
        Update semantic memory for a recipient.

        updates dict may contain:
          - "allergies": list[str]  → merged into existing allergies
          - "preferences": list[str] → merged into existing preferences
          - "past_gift": dict       → appended to past_gifts
        """
        if "allergies" in updates:
            self.semantic.update_allergies(recipient_key, updates["allergies"])
        if "preferences" in updates:
            self.semantic.update_preferences(recipient_key, updates["preferences"])
        if "past_gift" in updates:
            self.semantic.add_past_gift(recipient_key, updates["past_gift"])

    def get_past_gifts(self, recipient_key: str) -> list[dict]:
        return self.semantic.get_past_gifts(recipient_key)

    def ensure_catalog_loaded(self) -> bool:
        """Check if the Qdrant collection exists and has data."""
        try:
            info = self.long_term.get_collection_info()
            return (info.get("points_count") or 0) > 0
        except Exception:
            return False

    def __repr__(self) -> str:
        return (
            f"MemoryManager("
            f"short_term={len(self.short_term)} msgs, "
            f"recipients={len(self.semantic.list_recipients())} profiles)"
        )
