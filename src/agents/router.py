"""
RouterAgent - Intent Classifier (Agent 1 of 3)
==============================================
Single LLM call that classifies the user's intent and extracts
key entities (recipient, occasion, budget, location, date).

Intents:
  PRODUCT_SEARCH    - user wants to find / buy a gift
  PREFERENCE_UPDATE - user sharing recipient info (allergies, preferences)
  DELIVERY_CHECK    - questions about delivery logistics
  ORDER_HISTORY     - referencing a past order, wants to repeat
  GENERAL           - greeting, chitchat, general question
"""

import json

from src.llm.client import LLMClient


SYSTEM_PROMPT = """\
You are the Router for the Kapruka Gift-Concierge AI, Sri Lanka's leading online gift platform.
Your ONLY job is to classify the user's intent and extract key entities from their message.

INTENTS:
- PRODUCT_SEARCH    : User wants to find, browse, or purchase a gift/product
- PREFERENCE_UPDATE : User is sharing/updating recipient info (allergies, preferences, "remember that")
- DELIVERY_CHECK    : User asking about delivery options, timing, fees, or availability to a location
- ORDER_HISTORY     : User referencing a past order or wanting to repeat a past gift
- GENERAL           : Greetings, thanks, general questions, feedback, anything else

RULES:
1. If message references a past gift AND wants to buy again → ORDER_HISTORY
2. If message mentions allergies/preferences + "remember" → PREFERENCE_UPDATE
3. If message asks "can you deliver" / mentions location + date → DELIVERY_CHECK
4. If user seems to want to buy something → PRODUCT_SEARCH
5. Default to GENERAL when nothing else fits

Sri Lankan relationship terms to recognise and normalise:
- wife / partner / spouse           → "wife"
- husband                           → "husband"
- amma / amma / mom / mother / mum  → "mother"
- thaththa / tatta / dad / father   → "father"
- akka / elder sister / sister      → "sister"
- aiya / elder brother / brother    → "brother"
- malli / younger brother           → "brother"
- nangi / younger sister            → "sister"

Return ONLY valid JSON - no preamble, no markdown fences.
Output schema:
{
  "intent": "PRODUCT_SEARCH",
  "confidence": 0.95,
  "recipient_mentioned": "wife" | null,
  "occasion": "birthday" | "valentines" | "mothers_day" | "avurudu" | null,
  "product_query": "birthday cake nut-free" | null,
  "budget_mentioned": 5000 | null,
  "location_mentioned": "Kandy" | null,
  "date_mentioned": "Saturday" | null,
  "reasoning": "one line explanation"
}
"""


class RouterAgent:
    """Classifies user messages into intents and extracts entities."""

    DEFAULT_RESPONSE = {
        "intent": "GENERAL",
        "confidence": 0.5,
        "recipient_mentioned": None,
        "occasion": None,
        "product_query": None,
        "budget_mentioned": None,
        "location_mentioned": None,
        "date_mentioned": None,
        "reasoning": "Fallback - could not parse router response",
    }

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def classify(
        self,
        user_message: str,
        conversation_context: str = "",
    ) -> dict:
        """
        Classify the user's message.

        Returns a parsed dict with intent and entities.
        Never raises - returns DEFAULT_RESPONSE on failure.
        """
        user_prompt = f"""Conversation so far:
{conversation_context or "No prior conversation."}

Latest message: "{user_message}"

Classify the intent and extract entities. Return JSON only."""

        result = self.llm.call_json(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_prompt,
            temperature=0.0,  # Fully deterministic classification
            max_tokens=512,
            default=self.DEFAULT_RESPONSE,
        )

        # Validate and normalise the result
        return self._validate(result)

    def _validate(self, raw: dict) -> dict:
        """Ensure all required keys exist; fill defaults where missing."""
        defaults = self.DEFAULT_RESPONSE.copy()
        defaults.update(raw)

        # Normalise intent to uppercase
        defaults["intent"] = str(defaults.get("intent", "GENERAL")).upper()
        valid_intents = {
            "PRODUCT_SEARCH", "PREFERENCE_UPDATE",
            "DELIVERY_CHECK", "ORDER_HISTORY", "GENERAL",
        }
        if defaults["intent"] not in valid_intents:
            defaults["intent"] = "GENERAL"

        # Normalise budget to float or None
        budget = defaults.get("budget_mentioned")
        if budget is not None:
            try:
                defaults["budget_mentioned"] = float(str(budget).replace(",", ""))
            except (ValueError, TypeError):
                defaults["budget_mentioned"] = None

        return defaults
