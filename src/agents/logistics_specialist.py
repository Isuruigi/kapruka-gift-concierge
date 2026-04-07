"""
LogisticsSpecialist - Delivery Feasibility Agent (Agent 3 of 3)
===============================================================
Pure rules-engine over delivery_zones.json - no LLM needed for the check.
LLM is only used to generate the natural-language response.

Checks:
  1. Is the destination deliverable?
  2. Perishable restriction (cakes/flowers only to Colombo, Gampaha, Kalutara)
  3. Is the requested date feasible given standard delivery days?
  4. Delivery fee calculation
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.llm.client import LLMClient


class LogisticsSpecialist:
    """Checks delivery feasibility based on Sri Lankan district rules."""

    PERISHABLE_ZONES = {"colombo", "gampaha", "kalutara"}

    # Alias normalisation map for district names
    DISTRICT_ALIASES: dict[str, str] = {
        "colombo": "colombo", "col": "colombo", "col 7": "colombo",
        "gampaha": "gampaha", "negombo": "gampaha", "ja-ela": "gampaha",
        "kalutara": "kalutara", "panadura": "kalutara",
        "kandy": "kandy", "peradeniya": "kandy",
        "galle": "galle", "unawatuna": "galle",
        "matara": "matara", "weligama": "matara",
        "jaffna": "jaffna", "point pedro": "jaffna",
        "kurunegala": "kurunegala",
        "ratnapura": "ratnapura",
        "anuradhapura": "anuradhapura",
        "trincomalee": "trincomalee", "trinco": "trincomalee",
        "batticaloa": "batticaloa", "batti": "batticaloa",
        "nuwara eliya": "nuwara_eliya", "nuwara": "nuwara_eliya", "nuwaraeliya": "nuwara_eliya",
        "badulla": "badulla",
        "kilinochchi": "kilinochchi", "kili": "kilinochchi",
    }

    def __init__(self, llm_client: LLMClient, settings):
        self.llm = llm_client
        self.settings = settings
        self._zones_data = self._load_zones()

    def _load_zones(self) -> dict:
        path: Path = self.settings.DELIVERY_ZONES_PATH
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── Main public method ────────────────────────────────

    def check_delivery(
        self,
        destination: str,
        product_type: str = "standard",
        requested_date: str = None,
    ) -> dict:
        """
        Check delivery feasibility to a destination.

        Args:
            destination  : District name (any spelling - normalised internally)
            product_type : "standard" | "perishable" | "fragile"
            requested_date: Raw date string from the user ("Saturday", "2025-03-29", etc.)

        Returns:
            {
                "deliverable": bool,
                "zone_info": dict | None,
                "estimated_delivery": str,
                "delivery_fee": float | None,
                "warnings": list[str],
                "response_text": str,   # Natural language response
            }
        """
        warnings: list[str] = []
        zone_key = self._normalize_district(destination)
        zones = self._zones_data.get("zones", {})
        policies = self._zones_data.get("policies", {})
        zone = zones.get(zone_key)

        # ── Zone not found ─────────────────────────────
        if not zone:
            resp = self._generate_response(
                deliverable=False,
                destination=destination,
                zone=None,
                product_type=product_type,
                warnings=[f"District '{destination}' not found in delivery zones."],
                policies=policies,
            )
            return {
                "deliverable": False,
                "zone_info": None,
                "estimated_delivery": "Unknown",
                "delivery_fee": None,
                "warnings": [f"Unknown district: {destination}"],
                "response_text": resp,
            }

        # ── Delivery not available ─────────────────────
        if not zone.get("delivery_available", False):
            warnings.append(f"Delivery is NOT currently available to {zone['district']}.")
            resp = self._generate_response(
                deliverable=False,
                destination=zone["district"],
                zone=zone,
                product_type=product_type,
                warnings=warnings,
                policies=policies,
            )
            return {
                "deliverable": False,
                "zone_info": zone,
                "estimated_delivery": "Not available",
                "delivery_fee": None,
                "warnings": warnings,
                "response_text": resp,
            }

        # ── Perishable restriction ─────────────────────
        perishable_warning = self._check_perishable_restriction(zone_key, product_type)
        if perishable_warning:
            warnings.append(perishable_warning)

        # ── Date feasibility ───────────────────────────
        delivery_days = zone.get("standard_delivery_days", 1)
        estimated_date = datetime.now() + timedelta(days=delivery_days)
        estimated_str = (
            "Same day" if delivery_days == 0
            else f"{delivery_days} day(s) - approximately {estimated_date.strftime('%A, %B %d')}"
        )

        if requested_date:
            date_warning = self._check_date_feasibility(requested_date, delivery_days)
            if date_warning:
                warnings.append(date_warning)

        # ── Fee ────────────────────────────────────────
        delivery_fee = zone.get("delivery_fee_lkr")
        order_threshold = policies.get("free_delivery_threshold_lkr", 10000)
        if delivery_fee:
            warnings.append(
                f"Delivery fee: LKR {delivery_fee:,}. "
                f"Free delivery on orders over LKR {order_threshold:,}."
            )

        # ── Generate natural language response ─────────
        resp = self._generate_response(
            deliverable=True,
            destination=zone["district"],
            zone=zone,
            product_type=product_type,
            warnings=warnings,
            policies=policies,
            requested_date=requested_date,
            estimated_delivery=estimated_str,
        )

        return {
            "deliverable": True,
            "zone_info": zone,
            "estimated_delivery": estimated_str,
            "delivery_fee": delivery_fee,
            "warnings": warnings,
            "response_text": resp,
        }

    def get_all_zones_summary(self) -> str:
        """Return a formatted summary of all delivery zones."""
        zones = self._zones_data.get("zones", {})
        lines = ["**Sri Lanka Delivery Zones:**\n"]
        for key, z in zones.items():
            status = "✅" if z.get("delivery_available") else "❌"
            same_day = " (same-day available)" if z.get("same_day_available") else ""
            days = z.get("standard_delivery_days")
            fee = z.get("delivery_fee_lkr")
            lines.append(
                f"{status} **{z['district']}** - {days} day(s){same_day} | "
                f"LKR {fee:,}" if fee else f"{status} **{z['district']}** - Not available"
            )
        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────

    def _normalize_district(self, text: str) -> str:
        """Normalise a district name to the zones.json key."""
        lower = text.lower().strip()
        # Direct match
        if lower in self.DISTRICT_ALIASES:
            return self.DISTRICT_ALIASES[lower]
        # Partial match
        for alias, canonical in self.DISTRICT_ALIASES.items():
            if alias in lower or lower in alias:
                return canonical
        return lower.replace(" ", "_")

    def _check_perishable_restriction(
        self, zone_key: str, product_type: str
    ) -> Optional[str]:
        """Return warning string if perishable item can't reach this zone."""
        if product_type == "perishable" and zone_key not in self.PERISHABLE_ZONES:
            district = zone_key.replace("_", " ").title()
            return (
                f"⚠️ Perishable items (cakes, fresh flowers) can only be delivered to "
                f"Colombo, Gampaha, and Kalutara districts for freshness. "
                f"{district} is currently outside this zone."
            )
        return None

    def _check_date_feasibility(
        self, requested_date: str, delivery_days: int
    ) -> Optional[str]:
        """Check if a requested delivery date is achievable."""
        today = datetime.now()
        earliest_possible = today + timedelta(days=delivery_days)

        # Try to parse weekday names (e.g. "Saturday", "Monday")
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        lower = requested_date.lower().strip()
        for day_name, day_num in weekdays.items():
            if day_name in lower:
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                requested_dt = today + timedelta(days=days_ahead)
                if requested_dt < earliest_possible:
                    return (
                        f"⚠️ Requested delivery on {requested_date} may not be feasible - "
                        f"standard delivery to this zone takes {delivery_days} day(s). "
                        f"Earliest possible: {earliest_possible.strftime('%A, %B %d')}."
                    )
                return None
        return None

    def _generate_response(
        self,
        deliverable: bool,
        destination: str,
        zone: Optional[dict],
        product_type: str,
        warnings: list[str],
        policies: dict,
        requested_date: str = None,
        estimated_delivery: str = None,
    ) -> str:
        """Use LLM to generate a natural language response."""
        system_prompt = (
            "You are the Logistics Specialist for Kapruka Gift-Concierge, Sri Lanka's leading gift platform. "
            "Provide clear, helpful delivery information in a warm, friendly tone. "
            "Always mention the delivery fee and timeframe. Be empathetic if delivery isn't available."
        )

        zone_info_str = json.dumps(zone, indent=2) if zone else "Zone not found in database."
        warnings_str = "\n".join(f"- {w}" for w in warnings) or "No warnings."

        user_prompt = (
            f"Destination requested: {destination}\n"
            f"Product type: {product_type}\n"
            f"Requested date: {requested_date or 'Not specified'}\n"
            f"Deliverable: {'Yes' if deliverable else 'No'}\n"
            f"Estimated delivery: {estimated_delivery or 'N/A'}\n\n"
            f"Zone data:\n{zone_info_str}\n\n"
            f"Warnings / notes:\n{warnings_str}\n\n"
            f"Policies:\n{json.dumps(policies, indent=2)}\n\n"
            "Generate a friendly, informative delivery status response."
        )

        return self.llm.call(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.2,
            max_tokens=600,
        )
