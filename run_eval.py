import sys
import asyncio
import json

sys.stdout.reconfigure(encoding='utf-8')
from config.settings import Settings
from src.orchestrator import GiftConciergeAgent
from src.evaluation import AgentEvaluator

async def main():
    print("🚀 Initializing Agent and taking 10 test scenarios...")
    settings = Settings()
    agent = GiftConciergeAgent(settings)
    evaluator = AgentEvaluator(agent, settings.TEST_SCENARIOS_PATH)
    
    print("⏳ Running Evaluation... (this will print progress to terminal)")
    evaluator.run_all_scenarios()
    
    report_data = evaluator.generate_report_data()
    
    output_path = settings.OUTPUT_DIR / "evaluation_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
        
    print(f"✅ Evaluation complete. Saved report to: {output_path}")
    print("\n📊 SUMMARY METRICS:")
    print(json.dumps(report_data["metrics_summary"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
