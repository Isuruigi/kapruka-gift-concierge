"""
Tier 3: Semantic Memory - Recipient Profiles
=============================================
JSON-backed store for user-specific recipient knowledge:
preferences, allergies, past gifts, occasions, location, budget.

Supports fuzzy matching of relationship terms including Sri Lankan
relationship words (amma, thaththa, akka, aiya, malli, nangi).
"""

import json
from pathlib import Path
from typing import Optional


# Sri Lankan and English relationship synonyms → canonical key
RELATIONSHIP_SYNONYMS: dict[str, str] = {
    # Wife / Partner
    "wife": "wife", "partner": "wife", "spouse": "wife",
    "amaya": "wife",  # match by first name
    # Mother
    "mother": "mother", "mom": "mother", "amma": "mother", "ammi": "mother",
    "mum": "mother", "kamala": "mother",
    # Father
    "father": "father", "dad": "father", "thaththa": "father",
    "thaththi": "father", "tatta": "father",
    # Boss
    "boss": "boss", "rajapakse": "boss", "mr rajapakse": "boss",
    # Daughter
    "daughter": "daughter", "girl": "daughter", "nethmi": "daughter",
    # Friend Dinesh
    "friend": "friend_dinesh", "dinesh": "friend_dinesh",
    # Generic sibling terms
    "akka": "sister", "nangi": "sister", "sister": "sister",
    "aiya": "brother", "malli": "brother", "brother": "brother",
    # Generic husband
    "husband": "husband",
}


class RecipientMemory:
    """JSON-backed recipient profile store - Semantic Memory tier."""

    def __init__(self, profiles_path: Path):
        self.profiles_path = profiles_path
        self.profiles: dict = self._load_profiles()

    # ── I/O ───────────────────────────────────────────────

    def _load_profiles(self) -> dict:
        if self.profiles_path.exists():
            with open(self.profiles_path, "r", encoding="utf-8") as f:
                return json.load(f).get("profiles", {})
        return {}

    def _save_profiles(self):
        data = {"profiles": self.profiles}
        with open(self.profiles_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Retrieval ──────────────────────────────────────────

    def get_profile(self, recipient_key: str) -> Optional[dict]:
        """Get a recipient's full profile by key. Returns None if not found."""
        return self.profiles.get(recipient_key)

    def find_recipient(self, text: str) -> Optional[tuple[str, dict]]:
        """
        Fuzzy-match a recipient from free-form user text.

        Matching order:
          1. Direct key match ("wife", "mother", "boss")
          2. Name match (e.g. "Amaya" → "wife")
          3. Synonym / relationship term match
          4. Substring match in known nicknames

        Returns (key, profile_dict) or None.
        """
        text_lower = text.lower()

        # 1. Direct profile key match
        for key in self.profiles:
            if key in text_lower or key.replace("_", " ") in text_lower:
                return key, self.profiles[key]

        # 2. First-name / alias match
        for key, profile in self.profiles.items():
            name = profile.get("name", "").lower()
            if name and name in text_lower:
                return key, profile

        # 3. Synonym match
        for term, canonical in RELATIONSHIP_SYNONYMS.items():
            if term in text_lower:
                if canonical in self.profiles:
                    return canonical, self.profiles[canonical]
                # Try friends with underscore pattern
                for key in self.profiles:
                    if key.startswith(canonical + "_") or key.startswith("friend"):
                        prof = self.profiles[key]
                        if prof.get("relationship", "") == canonical.replace("friend_", "friend"):
                            return key, prof

        return None

    # ── Field accessors ───────────────────────────────────

    def get_allergies(self, recipient_key: str) -> list[str]:
        profile = self.profiles.get(recipient_key, {})
        return profile.get("allergies", [])

    def get_preferences(self, recipient_key: str) -> list[str]:
        return self.profiles.get(recipient_key, {}).get("preferences", [])

    def get_dislikes(self, recipient_key: str) -> list[str]:
        return self.profiles.get(recipient_key, {}).get("dislikes", [])

    def get_past_gifts(self, recipient_key: str) -> list[dict]:
        return self.profiles.get(recipient_key, {}).get("past_gifts", [])

    def get_occasion_date(self, recipient_key: str, occasion: str) -> Optional[str]:
        occasions = self.profiles.get(recipient_key, {}).get("occasions", {})
        return occasions.get(occasion)

    def get_budget_range(self, recipient_key: str) -> Optional[dict]:
        return self.profiles.get(recipient_key, {}).get("budget_range_lkr")

    def get_location(self, recipient_key: str) -> Optional[str]:
        return self.profiles.get(recipient_key, {}).get("location")

    def list_recipients(self) -> list[str]:
        return list(self.profiles.keys())

    # ── Write ──────────────────────────────────────────────

    def update_allergies(self, recipient_key: str, new_allergies: list[str]):
        """Merge new_allergies into the existing list for a recipient."""
        if recipient_key not in self.profiles:
            self.profiles[recipient_key] = {"allergies": []}
        current = self.profiles[recipient_key].get("allergies", [])
        merged = list(set(current + new_allergies))
        self.profiles[recipient_key]["allergies"] = merged
        self._save_profiles()

    def update_preferences(self, recipient_key: str, preferences: list[str]):
        """Merge preferences into the existing list."""
        if recipient_key not in self.profiles:
            self.profiles[recipient_key] = {"preferences": []}
        current = self.profiles[recipient_key].get("preferences", [])
        merged = list(set(current + preferences))
        self.profiles[recipient_key]["preferences"] = merged
        self._save_profiles()

    def add_past_gift(self, recipient_key: str, gift_record: dict):
        """Append a gift to the past_gifts history."""
        if recipient_key not in self.profiles:
            self.profiles[recipient_key] = {"past_gifts": []}
        self.profiles[recipient_key].setdefault("past_gifts", []).append(gift_record)
        self._save_profiles()

    def create_profile(self, recipient_key: str, profile_data: dict):
        """Create a new recipient profile."""
        self.profiles[recipient_key] = profile_data
        self._save_profiles()

    def update_profile_field(self, recipient_key: str, field: str, value):
        """Update any single field in a profile."""
        if recipient_key not in self.profiles:
            self.profiles[recipient_key] = {}
        self.profiles[recipient_key][field] = value
        self._save_profiles()

    # ── Formatting for LLM prompts ─────────────────────────

    def format_for_prompt(self, recipient_key: str) -> str:
        """
        Format a recipient profile as a readable block for LLM prompts.

        Example output:
        Recipient: Amaya (wife)
        Preferences: dark chocolate, red roses, spa gift sets
        Allergies: nuts, peanuts  ⚠️ CRITICAL - filter these from recommendations
        Dietary: no-nuts, pescatarian
        Location: Colombo
        Budget: LKR 3,000 – 15,000
        Past gifts: Nut-Free Chocolate Cake (birthday 2024), Red Rose Bouquet (valentines 2024)
        Notes: Prefers elegant packaging. Loves surprises at her office.
        """
        profile = self.profiles.get(recipient_key)
        if not profile:
            return f"No profile found for '{recipient_key}'."

        name = profile.get("name", recipient_key.replace("_", " ").title())
        relationship = profile.get("relationship", "unknown")
        prefs = ", ".join(profile.get("preferences", [])) or "None listed"
        dislikes = ", ".join(profile.get("dislikes", [])) or "None"
        allergies = profile.get("allergies", [])
        allergy_str = ", ".join(allergies) if allergies else "None known"
        allergy_note = "  ⚠️ CRITICAL - these MUST be filtered from all recommendations" if allergies else ""
        dietary = ", ".join(profile.get("dietary", [])) or "None"
        location = profile.get("location", "Unknown")
        budget = profile.get("budget_range_lkr", {})
        budget_str = (
            f"LKR {budget.get('min', '?'):,} – {budget.get('max', '?'):,}"
            if budget else "Not specified"
        )
        past = profile.get("past_gifts", [])
        past_str = (
            ", ".join(
                f"{g['item']} ({g.get('occasion', '?')} {g.get('date', '')[:4]})"
                for g in past[-3:]  # last 3 gifts
            )
            or "None on record"
        )
        notes = profile.get("notes", "")

        return (
            f"Recipient: {name} ({relationship})\n"
            f"Preferences: {prefs}\n"
            f"Dislikes: {dislikes}\n"
            f"Allergies: {allergy_str}{allergy_note}\n"
            f"Dietary: {dietary}\n"
            f"Location: {location}\n"
            f"Budget: {budget_str}\n"
            f"Past gifts: {past_str}\n"
            f"Notes: {notes}"
        )
