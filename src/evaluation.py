"""
Part 5: Evaluation Framework - AgentEvaluator
==============================================
Runs all 10 test scenarios and measures:
  1. Router Accuracy       - correct intent classification %
  2. Allergy Safety Rate   - must be 100% (critical)
  3. Reflection Catch Rate - unsafe drafts caught and fixed
  4. Latency               - avg / max / min per query (ms)
  5. Cost Estimate         - monthly API cost projection
"""

import json
import time
from pathlib import Path
from typing import Optional


class AgentEvaluator:
    """Runs all test scenarios through the GiftConciergeAgent and computes metrics."""

    def __init__(self, agent, test_scenarios_path: Path):
        # Import here to avoid circular dependency at module load
        self.agent = agent
        self.scenarios = self._load_scenarios(test_scenarios_path)
        self.results: list[dict] = []

    # ── Load ──────────────────────────────────────────────

    def _load_scenarios(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("scenarios", [])

    # ── Run ───────────────────────────────────────────────

    def run_all_scenarios(self) -> dict:
        """Run every test scenario and return aggregate metrics."""
        self.results = []
        for scenario in self.scenarios:
            print(f"  🧪 Running {scenario['id']}: {scenario['name']}…", end=" ", flush=True)
            try:
                result = self._run_scenario(scenario)
                status = "✅" if result["intent_correct"] and result["allergy_safe"] else "⚠️"
                print(f"{status} intent={result['actual_intent']}, allergy_safe={result['allergy_safe']}")
            except Exception as e:
                print(f"❌ Error: {e}")
                result = self._error_result(scenario, str(e))
            self.results.append(result)

        return self._calculate_metrics()

    def _run_scenario(self, scenario: dict) -> dict:
        """Run a single scenario through the agent."""
        self.agent.reset_session()
        start = time.time()
        response = self.agent.chat(scenario["user_message"])
        latency_ms = (time.time() - start) * 1000

        return {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "user_message": scenario["user_message"],
            "expected_intent": scenario["expected_intent"],
            "actual_intent": response["intent"],
            "intent_correct": response["intent"] == scenario["expected_intent"],
            "allergy_trap": scenario.get("allergy_trap", False),
            "allergy_safe": self._check_allergy_safety(response, scenario),
            "reflection_triggered": bool(response.get("reflection_log")),
            "reflection_caught_issue": self._check_reflection_caught(response),
            "safety_status": response.get("safety_status", "N/A"),
            "latency_ms": round(latency_ms, 1),
            "response_text": response["response"][:300],  # Truncated for display
            "full_response": {
                k: v for k, v in response.items() if k != "reflection_log"
            },
            "notes": scenario.get("notes", ""),
        }

    def _error_result(self, scenario: dict, error: str) -> dict:
        return {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "user_message": scenario["user_message"],
            "expected_intent": scenario["expected_intent"],
            "actual_intent": "ERROR",
            "intent_correct": False,
            "allergy_trap": scenario.get("allergy_trap", False),
            "allergy_safe": False,
            "reflection_triggered": False,
            "reflection_caught_issue": False,
            "safety_status": "ERROR",
            "latency_ms": 0.0,
            "response_text": f"ERROR: {error}",
            "full_response": {},
            "notes": scenario.get("notes", ""),
        }

    # ── Checks ────────────────────────────────────────────

    def _check_allergy_safety(self, response: dict, scenario: dict) -> bool:
        """Check if the final response is free of allergen violations."""
        if not scenario.get("allergy_trap"):
            return True  # Not an allergy test - passes automatically

        reflection_log = response.get("reflection_log")
        if not reflection_log:
            # If no reflection ran, check the safety_status
            return response.get("safety_status") != "UNSAFE_AFTER_MAX_RETRIES"

        # Check the last reflection entry
        last_entry = reflection_log[-1]
        critique = last_entry.get("critique", {})
        return critique.get("allergen_check") == "PASS"

    def _check_reflection_caught(self, response: dict) -> bool:
        """Returns True if the reflection loop caught at least one issue."""
        reflection_log = response.get("reflection_log")
        if not reflection_log:
            return False
        return not reflection_log[0].get("all_passed", True)

    # ── Metrics ───────────────────────────────────────────

    def _calculate_metrics(self) -> dict:
        """Compute aggregate metrics across all scenarios."""
        total = len(self.results)
        if total == 0:
            return {"error": "No results to evaluate"}

        passed_intent = sum(1 for r in self.results if r["intent_correct"])
        allergy_traps = [r for r in self.results if r["allergy_trap"]]
        allergy_safe = sum(1 for r in self.results if r["allergy_safe"])
        traps_caught = sum(1 for r in allergy_traps if r["allergy_safe"])
        triggered = [r for r in self.results if r["reflection_triggered"]]
        caught = sum(1 for r in triggered if r["reflection_caught_issue"])

        latencies = [r["latency_ms"] for r in self.results if r["latency_ms"] > 0]

        return {
            "total_scenarios": total,
            "router_accuracy": round(passed_intent / total, 3),
            "router_accuracy_pct": f"{passed_intent / total * 100:.1f}%",
            "allergy_safety_rate": round(allergy_safe / total, 3),
            "allergy_safety_rate_pct": f"{allergy_safe / total * 100:.1f}%",
            "allergy_trap_scenarios": len(allergy_traps),
            "allergy_traps_caught": traps_caught,
            "reflection_triggered_count": len(triggered),
            "reflection_catch_rate": round(caught / len(triggered), 3) if triggered else 0.0,
            "reflection_catch_rate_pct": f"{caught / len(triggered) * 100:.1f}%" if triggered else "N/A",
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "per_scenario": [
                {
                    "id": r["scenario_id"],
                    "name": r["scenario_name"],
                    "intent_correct": r["intent_correct"],
                    "allergy_safe": r["allergy_safe"],
                    "latency_ms": r["latency_ms"],
                    "safety_status": r["safety_status"],
                }
                for r in self.results
            ],
        }

    def generate_report_data(self) -> dict:
        """Structured data for the PDF report."""
        metrics = self._calculate_metrics()
        return {
            "metrics_summary": metrics,
            "per_scenario_results": self.results,
            "cost_estimate": self._estimate_costs(),
        }

    def _estimate_costs(self) -> dict:
        """Estimate monthly API costs for production scale."""
        # Assumptions: 500 daily users × 10 queries = 5,000 queries/day
        # 4 LLM calls per query: router + catalog + reflect + revise
        # Claude Haiku: ~$0.80/M input tokens, ~$4.00/M output tokens (2025 pricing)
        # Catalog search uses sentinel-transformers locally - zero cost
        avg_input_tokens = 2_500   # per query (across all calls)
        avg_output_tokens = 1_200  # per query
        daily_queries = 5_000
        monthly_queries = daily_queries * 30

        # Haiku pricing (approx)
        input_cost_per_m = 0.80
        output_cost_per_m = 4.00

        input_cost = (avg_input_tokens * monthly_queries / 1_000_000) * input_cost_per_m
        output_cost = (avg_output_tokens * monthly_queries / 1_000_000) * output_cost_per_m
        qdrant_cost = 0.0  # Free tier for < 1M vectors

        return {
            "assumptions": {
                "daily_users": 500,
                "queries_per_user": 10,
                "llm_calls_per_query": 4,
                "avg_input_tokens_per_query": avg_input_tokens,
                "avg_output_tokens_per_query": avg_output_tokens,
            },
            "monthly_queries": monthly_queries,
            "input_token_cost_usd": round(input_cost, 2),
            "output_token_cost_usd": round(output_cost, 2),
            "qdrant_cost_usd": qdrant_cost,
            "total_monthly_usd": round(input_cost + output_cost, 2),
            "cost_per_query_usd": round((input_cost + output_cost) / monthly_queries, 4),
        }
