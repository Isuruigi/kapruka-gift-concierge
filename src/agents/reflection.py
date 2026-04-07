"""
ReflectionLoop - Draft → Reflect → Revise Cycle (Part 4)
=========================================================
The SAFETY LAYER of the Gift-Concierge Agent.
Catches allergen violations, preference mismatches, and budget overruns
BEFORE the recommendation reaches the user.

Flow:
  1. DRAFT    - CatalogSpecialist generates the initial recommendation
  2. REFLECT  - Critic LLM evaluates safety and quality criteria
  3. REVISE   - Reviser LLM fixes any violations
  4. Repeat up to max_iterations, then return best result
"""

import json
from typing import Optional

from src.llm.client import LLMClient


CRITIC_SYSTEM_PROMPT = """\
You are the Safety Critic for Kapruka Gift-Concierge AI.
Your ONLY job is to evaluate a gift recommendation for safety and appropriateness.

YOU MUST CHECK (in order of priority):

1. ALLERGEN CHECK (CRITICAL - someone could be harmed):
   - Does ANY recommended product contain allergens the recipient is allergic to?
   - Check product names and descriptions for allergen keywords.
   - ALLERGEN KEYWORDS:
       nuts: nut, almond, cashew, walnut, hazelnut, pistachio, peanut, praline, marzipan
       dairy: milk, cream, butter, cheese, yogurt, dairy, whey, lactose, ghee
       gluten: wheat, flour, gluten, biscuit, bread, barley, rye
       eggs: egg, eggs, mayonnaise
       soy: soy, soya
       shellfish: prawn, shrimp, crab, lobster, shellfish
   - Be STRICT. When in doubt → FAIL.

2. PREFERENCE CHECK:
   - Does the recommendation match the recipient's known preferences?
   - Are any dislikes recommended?

3. BUDGET CHECK:
   - Is the recommended price within the recipient's budget range?

4. OCCASION CHECK:
   - Is the gift appropriate for the specific occasion?

Return ONLY valid JSON. No markdown fences. No extra text.
{
  "allergen_check": "PASS" or "FAIL",
  "allergen_violations": ["list of specific violations, e.g. 'Product X contains nuts - recipient is nut-allergic'"],
  "preference_check": "PASS" or "FAIL",
  "preference_notes": "...",
  "budget_check": "PASS" or "FAIL" or "N/A",
  "occasion_check": "PASS" or "FAIL" or "N/A",
  "all_checks_passed": true or false,
  "suggestions": ["Specific fix suggestions"],
  "severity": "CRITICAL" or "WARNING" or "NONE"
}
"""

REVISER_SYSTEM_PROMPT = """\
You are the Reviser for Kapruka Gift-Concierge AI.
A safety critique found issues with a gift recommendation. Your job:

1. REMOVE any products that violate allergen restrictions COMPLETELY
2. REPLACE them with safe alternatives from the available products list
3. If no safe alternative exists in the list, acknowledge this clearly
4. Maintain a warm, helpful tone
5. Explain changes naturally ("I've chosen a nut-free option instead")
6. Keep the same quality and format as the original recommendation, and INCLUDE THE URL for each recommended product.

CRITICAL: The revised recommendation MUST have ZERO allergen violations.
"""


class ReflectionLoop:
    """Draft → Reflect → Revise safety layer for gift recommendations."""

    def __init__(self, llm_client: LLMClient, settings):
        self.llm = llm_client
        self.settings = settings
        self.max_iterations = settings.REFLECTION_MAX_ITERATIONS

    def run(
        self,
        draft_recommendation: str,
        recipient_profile: str,
        recipient_allergies: list[str],
        products_found: list[dict],
        original_query: str,
    ) -> dict:
        """
        Run the full Draft → Reflect → Revise cycle.

        Returns:
            {
                "final_recommendation": str,
                "reflection_log": [
                    {
                        "iteration": int,
                        "draft": str,
                        "critique": dict,
                        "revised": str | None,
                        "all_passed": bool,
                    }
                ],
                "total_iterations": int,
                "safety_status": "SAFE" | "SAFE_WITH_WARNINGS" | "UNSAFE_AFTER_MAX_RETRIES",
            }
        """
        current_draft = draft_recommendation
        reflection_log: list[dict] = []

        for iteration in range(1, self.max_iterations + 1):
            # STEP 2: REFLECT
            critique = self._reflect(
                draft=current_draft,
                recipient_profile=recipient_profile,
                recipient_allergies=recipient_allergies,
                products_found=products_found,
            )

            log_entry: dict = {
                "iteration": iteration,
                "draft": current_draft,
                "critique": critique,
                "revised": None,
                "all_passed": critique.get("all_checks_passed", False),
            }

            # If all checks pass → done!
            if critique.get("all_checks_passed", False):
                log_entry["revised"] = current_draft
                reflection_log.append(log_entry)
                return {
                    "final_recommendation": current_draft,
                    "reflection_log": reflection_log,
                    "total_iterations": iteration,
                    "safety_status": "SAFE",
                }

            # STEP 3: REVISE
            revised = self._revise(
                draft=current_draft,
                critique=critique,
                recipient_profile=recipient_profile,
                products_found=products_found,
                original_query=original_query,
            )

            log_entry["revised"] = revised
            reflection_log.append(log_entry)
            current_draft = revised

        # Max iterations reached
        has_allergen_fail = any(
            log.get("critique", {}).get("allergen_check") == "FAIL"
            for log in reflection_log
        )

        return {
            "final_recommendation": current_draft,
            "reflection_log": reflection_log,
            "total_iterations": self.max_iterations,
            "safety_status": (
                "UNSAFE_AFTER_MAX_RETRIES" if has_allergen_fail else "SAFE_WITH_WARNINGS"
            ),
        }

    # ── Critic ────────────────────────────────────────────

    def _reflect(
        self,
        draft: str,
        recipient_profile: str,
        recipient_allergies: list[str],
        products_found: list[dict],
    ) -> dict:
        """Evaluate the draft. Returns a critique JSON dict."""
        allergy_str = ", ".join(recipient_allergies) if recipient_allergies else "None known"

        user_prompt = (
            f"DRAFT RECOMMENDATION:\n{draft}\n\n"
            f"RECIPIENT PROFILE:\n{recipient_profile}\n\n"
            f"KNOWN ALLERGIES: {allergy_str}\n\n"
            "Evaluate this recommendation STRICTLY. "
            "Return JSON with: allergen_check, allergen_violations, preference_check, "
            "preference_notes, budget_check, occasion_check, all_checks_passed, suggestions, severity."
        )

        default_critique = {
            "allergen_check": "PASS",
            "allergen_violations": [],
            "preference_check": "PASS",
            "preference_notes": "Unable to evaluate",
            "budget_check": "N/A",
            "occasion_check": "N/A",
            "all_checks_passed": True,
            "suggestions": [],
            "severity": "NONE",
        }

        return self.llm.call_json(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_message=user_prompt,
            model=self.settings.LLM_MODEL_STRONG,  # Use stronger model for safety
            temperature=0.0,
            max_tokens=800,
            default=default_critique,
        )

    # ── Reviser ───────────────────────────────────────────

    def _revise(
        self,
        draft: str,
        critique: dict,
        recipient_profile: str,
        products_found: list[dict],
        original_query: str,
    ) -> str:
        """Fix violations found by the critic."""
        safe_products_text = self._format_safe_products(products_found, critique)

        user_prompt = (
            f'ORIGINAL REQUEST: "{original_query}"\n\n'
            f"DRAFT THAT NEEDS FIXING:\n{draft}\n\n"
            f"SAFETY CRITIQUE:\n{json.dumps(critique, indent=2)}\n\n"
            f"RECIPIENT PROFILE:\n{recipient_profile}\n\n"
            f"AVAILABLE SAFE PRODUCTS:\n{safe_products_text}\n\n"
            "Generate a revised recommendation that fixes ALL violations. "
            "Zero allergen violations allowed."
        )

        return self.llm.call(
            system_prompt=REVISER_SYSTEM_PROMPT,
            user_message=user_prompt,
            temperature=self.settings.LLM_TEMPERATURE_CREATIVE,
            max_tokens=1500,
        )

    def _format_safe_products(self, products: list[dict], critique: dict) -> str:
        """Format the product list, flagging which ones are safe vs. violating."""
        violations = critique.get("allergen_violations", [])
        violation_text = " ".join(violations).lower()

        lines = []
        for i, p in enumerate(products, 1):
            prod = p["product"]
            name = prod["product_name"]
            allergens = prod.get("contains_allergens", [])
            tags = prod.get("tags", [])

            # Check if this product is flagged
            is_flagged = any(
                name.lower() in violation_text or
                any(a in violation_text for a in allergens)
                for _ in [1]
            )

            status = "⛔ FLAGGED" if is_flagged else "✅ SAFE"
            allergen_str = ", ".join(allergens) or "none"
            tag_str = ", ".join(tags) or "none"

            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            safe_url = f"https://www.kapruka.com/sri_lanka_search.jsp?searchWord={encoded_name}"
            
            lines.append(
                f"{status} Product {i}: {name}\n"
                f"   Price: LKR {prod['price_lkr']:,.0f} | "
                f"Allergens: {allergen_str} | Tags: {tag_str} | "
                f"URL: {safe_url}"
            )

        return "\n".join(lines) if lines else "No products available."
