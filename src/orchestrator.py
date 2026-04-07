"""
GiftConciergeAgent - Main Orchestrator (src/orchestrator.py)
=============================================================
The single class external code interacts with.
NO FRAMEWORKS - pure Python orchestration.

Flow:
  User message
  → Add to Short-Term Memory
  → RouterAgent classifies intent
  → Dispatch to specialist:
      PRODUCT_SEARCH    → CatalogSpecialist → ReflectionLoop → Response
      PREFERENCE_UPDATE → RecipientMemory update → Confirmation
      DELIVERY_CHECK    → LogisticsSpecialist → Response
      ORDER_HISTORY     → SemanticMemory lookup → Response
      GENERAL           → Direct LLM response
  → Add response to Short-Term Memory
  → Return response + metadata
"""

import json
import time
from typing import Optional

from config.settings import Settings
from src.llm.client import LLMClient
from src.memory.manager import MemoryManager
from src.agents.router import RouterAgent
from src.agents.catalog_specialist import CatalogSpecialist
from src.agents.logistics_specialist import LogisticsSpecialist
from src.agents.reflection import ReflectionLoop


class GiftConciergeAgent:
    """
    The Kapruka Gift-Concierge - main agent class.
    Instantiate once and call .chat(user_message) for every turn.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

        # Validate config
        missing = self.settings.validate()
        if missing:
            raise ValueError(
                f"Missing required environment variables: {missing}\n"
                "Please copy .env.example to .env and fill in your API keys."
            )

        # Shared components
        self.llm = LLMClient(self.settings)
        self.memory = MemoryManager(self.settings)

        # Specialist agents
        self.router = RouterAgent(self.llm)
        self.catalog = CatalogSpecialist(self.llm, self.memory)
        self.logistics = LogisticsSpecialist(self.llm, self.settings)
        self.reflection = ReflectionLoop(self.llm, self.settings)

    # ──────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────

    def chat(self, user_message: str) -> dict:
        """
        Process a user message and return a full response dict.

        Returns:
            {
                "response"           : str   - the final response to display
                "intent"             : str   - classified intent
                "recipient"          : str | None
                "products_recommended": list
                "reflection_log"     : list | None
                "memory_updated"     : bool
                "metadata": {
                    "router_output"  : dict,
                    "latency_ms"     : float,
                    "model_used"     : str,
                }
            }
        """
        start = time.time()

        # 1. Store user turn in short-term memory
        self.memory.add_user_message(user_message)

        # 2. Get full context (conversation + recipient profile)
        context = self.memory.get_full_context(user_message)

        # 3. Route - classify intent
        router_output = self.router.classify(
            user_message=user_message,
            conversation_context=context["conversation"],
        )
        intent = router_output.get("intent", "GENERAL")

        # 4. Dispatch to specialist
        result = self._dispatch(intent, user_message, router_output, context)

        # 5. Store assistant response in short-term memory
        self.memory.add_assistant_message(result["response"])

        # 6. Attach metadata
        latency_ms = (time.time() - start) * 1000
        result.update(
            {
                "intent": intent,
                "metadata": {
                    "router_output": router_output,
                    "latency_ms": round(latency_ms, 1),
                    "model_used": self.settings.LLM_MODEL_FAST,
                },
            }
        )
        return result

    # ──────────────────────────────────────────────────────
    # Dispatcher
    # ──────────────────────────────────────────────────────

    def _dispatch(
        self,
        intent: str,
        user_message: str,
        router_output: dict,
        context: dict,
    ) -> dict:
        """Route to the appropriate handler based on classified intent."""
        handlers = {
            "PRODUCT_SEARCH":    self._handle_product_search,
            "PREFERENCE_UPDATE": self._handle_preference_update,
            "DELIVERY_CHECK":    self._handle_delivery_check,
            "ORDER_HISTORY":     self._handle_order_history,
        }
        handler = handlers.get(intent, self._handle_general)
        return handler(user_message, router_output, context)

    # ──────────────────────────────────────────────────────
    # Intent handlers
    # ──────────────────────────────────────────────────────

    def _handle_product_search(
        self, user_message: str, router_output: dict, context: dict
    ) -> dict:
        """
        Full pipeline:
          Catalog RAG → Draft recommendation → Reflection Loop → Final response
        """
        recipient_key = context.get("recipient_key")
        occasion = router_output.get("occasion")
        budget = router_output.get("budget_mentioned")
        query = router_output.get("product_query") or user_message

        # 1. Catalog Specialist - generates draft recommendation
        catalog_result = self.catalog.search_and_recommend(
            query=query,
            recipient_key=recipient_key,
            occasion=occasion,
            budget_max=float(budget) if budget else None,
        )

        # 2. Reflection Loop - safety check + revise if needed
        reflection_result = self.reflection.run(
            draft_recommendation=catalog_result["recommendation_text"],
            recipient_profile=context.get("recipient_profile", ""),
            recipient_allergies=context.get("recipient_allergies", []),
            products_found=catalog_result["products_found"],
            original_query=user_message,
        )

        return {
            "response": reflection_result["final_recommendation"],
            "recipient": recipient_key,
            "products_recommended": catalog_result["products_found"],
            "reflection_log": reflection_result["reflection_log"],
            "memory_updated": False,
            "safety_status": reflection_result.get("safety_status", "SAFE"),
        }

    def _handle_preference_update(
        self, user_message: str, router_output: dict, context: dict
    ) -> dict:
        """Extract what info to update and write to semantic memory."""
        recipient_key = context.get("recipient_key") or router_output.get("recipient_mentioned")

        # Use LLM to extract the specific update from the user's message
        extract_prompt = f"""The user said: "{user_message}"

They are updating information about their recipient: {recipient_key or 'unknown'}.

Extract what should be updated. Return JSON:
{{
  "recipient_key": "wife" | "mother" | etc,
  "allergies_to_add": ["shellfish", ...] or [],
  "preferences_to_add": ["..."] or [],
  "notes": "any other info to note"
}}
Return only JSON."""

        extracted = self.llm.call_json(
            system_prompt="You extract recipient update information from user messages. Return JSON only.",
            user_message=extract_prompt,
            temperature=0.0,
            default={"recipient_key": recipient_key, "allergies_to_add": [], "preferences_to_add": []},
        )

        key = extracted.get("recipient_key") or recipient_key
        memory_updated = False

        if key:
            updates = {}
            if extracted.get("allergies_to_add"):
                updates["allergies"] = extracted["allergies_to_add"]
            if extracted.get("preferences_to_add"):
                updates["preferences"] = extracted["preferences_to_add"]
            if updates:
                self.memory.update_recipient_info(key, updates)
                memory_updated = True

        # Generate confirmation response
        if memory_updated and key:
            profile_text = self.memory.semantic.format_for_prompt(key)
            response = self.llm.call(
                system_prompt=(
                    "You are the Kapruka Gift-Concierge. Confirm that you've updated "
                    "the recipient's information. Be warm and reassuring."
                ),
                user_message=(
                    f"User said: \"{user_message}\"\n"
                    f"Updated profile:\n{profile_text}\n"
                    "Generate a brief, friendly confirmation."
                ),
                temperature=0.3,
                max_tokens=300,
            )
        else:
            response = (
                "I've noted that, but I wasn't able to identify which recipient to update. "
                "Could you clarify who this is for? (e.g., 'My wife is now also allergic to shellfish')"
            )

        return {
            "response": response,
            "recipient": key,
            "products_recommended": [],
            "reflection_log": None,
            "memory_updated": memory_updated,
        }

    def _handle_delivery_check(
        self, user_message: str, router_output: dict, context: dict
    ) -> dict:
        """Check delivery feasibility for a location."""
        destination = router_output.get("location_mentioned", "")
        date = router_output.get("date_mentioned")

        if not destination:
            # Ask user for destination
            response = (
                "I'd be happy to check delivery for you! "
                "Could you tell me which city or district in Sri Lanka you'd like to deliver to?"
            )
            return {
                "response": response,
                "recipient": None,
                "products_recommended": [],
                "reflection_log": None,
                "memory_updated": False,
            }

        # Detect if product is perishable from context
        product_type = "standard"
        msg_lower = user_message.lower()
        if any(k in msg_lower for k in ["cake", "flower", "bouquet", "fresh"]):
            product_type = "perishable"

        result = self.logistics.check_delivery(
            destination=destination,
            product_type=product_type,
            requested_date=date,
        )

        return {
            "response": result["response_text"],
            "recipient": None,
            "products_recommended": [],
            "reflection_log": None,
            "memory_updated": False,
            "delivery_info": result,
        }

    def _handle_order_history(
        self, user_message: str, router_output: dict, context: dict
    ) -> dict:
        """Look up past gifts and suggest repeating or alternatives."""
        recipient_key = context.get("recipient_key") or router_output.get("recipient_mentioned")

        past_gifts = []
        profile_text = "No profile found."
        if recipient_key:
            past_gifts = self.memory.get_past_gifts(recipient_key)
            profile_text = self.memory.semantic.format_for_prompt(recipient_key)

        if not past_gifts:
            response = (
                f"I don't have any past gift history for "
                f"{recipient_key or 'that recipient'} yet. "
                "Once you place an order, I'll remember it for future reference! "
                "Would you like me to suggest something new instead?"
            )
        else:
            # Use LLM to reference past gifts
            past_text = json.dumps(past_gifts, indent=2)
            response = self.llm.call(
                system_prompt=(
                    "You are the Kapruka Gift-Concierge with access to the customer's gift history. "
                    "Reference their past gifts and help them decide what to send next."
                ),
                user_message=(
                    f'User said: "{user_message}"\n'
                    f"Recipient profile:\n{profile_text}\n\n"
                    f"Past gift history:\n{past_text}\n\n"
                    "Help the user choose - reference the past gift they mentioned, confirm if they "
                    "want to repeat it, or suggest a complementary option."
                ),
                temperature=0.3,
                max_tokens=600,
            )

        return {
            "response": response,
            "recipient": recipient_key,
            "products_recommended": [],
            "reflection_log": None,
            "memory_updated": False,
        }

    def _handle_general(
        self, user_message: str, router_output: dict, context: dict
    ) -> dict:
        """Handle general chitchat with the Kapruka brand voice."""
        response = self.llm.call(
            system_prompt=(
                "You are the Kapruka Gift-Concierge - a friendly AI assistant for "
                "Sri Lanka's leading online gift delivery platform.\n"
                "Be warm, culturally aware, and knowledgeable about Sri Lankan gifting traditions.\n"
                "If the user seems to want to buy a gift, gently guide them to tell you who it's for "
                "and what the occasion is.\n"
                "You know about Sri Lankan festivals: Avurudu (New Year), Vesak, Deepavali, Eid, Christmas.\n"
                "Keep responses concise and helpful."
            ),
            user_message=user_message,
            temperature=0.5,
            max_tokens=500,
        )

        return {
            "response": response,
            "recipient": None,
            "products_recommended": [],
            "reflection_log": None,
            "memory_updated": False,
        }

    # ──────────────────────────────────────────────────────
    # Session management
    # ──────────────────────────────────────────────────────

    def reset_session(self):
        """Clear short-term memory for a fresh conversation."""
        self.memory.clear_session()

    def get_session_summary(self) -> dict:
        """Return a summary of the current session state."""
        return {
            "messages_in_context": len(self.memory.short_term),
            "recipients_known": self.memory.semantic.list_recipients(),
            "catalog_loaded": self.memory.ensure_catalog_loaded(),
        }
