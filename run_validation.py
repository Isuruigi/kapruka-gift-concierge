"""
Full validation script extracted from VALIDATE.md
Run from inside: kapruka-gift-concierge/
"""
import os, sys, re, json
from pathlib import Path

ROOT = Path(".")
PASS = 0
FAIL = 0
WARN = 0

def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

def ok(msg):   global PASS; PASS += 1; print(f"  ✅ {msg}")
def fail(msg): global FAIL; FAIL += 1; print(f"  ❌ {msg}")
def warn(msg): global WARN; WARN += 1; print(f"  ⚠️  {msg}")

# ── PHASE 0.1 Project Structure ───────────────────────────────
section("PHASE 0.1: PROJECT STRUCTURE")
REQUIRED = [
    ".env",".env.example",".gitignore","requirements.txt","README.md",
    "config/__init__.py","config/settings.py","config/delivery_zones.json",
    "data/catalog.json","data/recipient_profiles.json","data/test_scenarios.json",
    "src/__init__.py","src/crawler/__init__.py","src/crawler/kapruka_scraper.py",
    "src/memory/__init__.py","src/memory/short_term.py","src/memory/long_term.py",
    "src/memory/semantic.py","src/memory/manager.py",
    "src/agents/__init__.py","src/agents/router.py","src/agents/catalog_specialist.py",
    "src/agents/logistics_specialist.py","src/agents/reflection.py",
    "src/llm/__init__.py","src/llm/client.py",
    "src/orchestrator.py","src/evaluation.py",
    "notebooks/01_crawler.ipynb","notebooks/02_memory_lab.ipynb",
    "notebooks/03_orchestration.ipynb","notebooks/04_reflection.ipynb",
    "notebooks/05_evaluation.ipynb",
]
for f in REQUIRED:
    if (ROOT / f).exists(): ok(f)
    else: fail(f"MISSING: {f}")
for f in ["ui/streamlit_app.py"]:
    if (ROOT / f).exists(): ok(f"{f} (bonus)")
    else: warn(f"{f} (optional)")
for f in ["report/technical_proposal.pdf"]:
    if (ROOT / f).exists(): ok(f"{f}")
    else: warn(f"MISSING: {f} - needed for submission")

# ── PHASE 0.2 Env Vars ────────────────────────────────────────
section("PHASE 0.2: ENVIRONMENT VARIABLES")
from dotenv import load_dotenv
load_dotenv()
for var in ["ANTHROPIC_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]:
    val = os.getenv(var, "")
    if val and len(val) > 5:
        ok(f"{var} = {val[:8]}...****")
    else:
        fail(f"{var} - NOT SET or empty")

# ── PHASE 0.3 Hardcoded Keys ──────────────────────────────────
section("PHASE 0.3: HARDCODED KEY SCAN")
PATTERNS = [r'sk-ant-[a-zA-Z0-9\-_]{20,}', r'ANTHROPIC_API_KEY\s*=\s*["\'][^"\']+["\']']
violations = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", ".venv"]]
    for fname in files:
        if fname.endswith(".py") and fname != ".env":
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath, "r", encoding="utf-8", errors="ignore").read()
                for p in PATTERNS:
                    for m in re.findall(p, content):
                        violations.append((fpath, m[:30]))
            except: pass
if violations:
    for f, s in violations: fail(f"Hardcoded key in {f}: {s}")
else:
    ok("No hardcoded API keys detected")

# ── PHASE 0.4 Banned Frameworks ───────────────────────────────
section("PHASE 0.4: BANNED FRAMEWORK SCAN (50% PENALTY CHECK)")
BANNED = ["langgraph","crewai","autogen","langchain.agents","AgentExecutor","CrewBase","StateGraph"]
bviolations = []
# Files excluded from scan: validator itself (contains banned strings as literals) and pdf generator
SCAN_EXCLUDE = {"run_validation.py", "generate_pdf.py"}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv"]]
    for fname in files:
        if fname.endswith((".py", ".ipynb")) and fname not in SCAN_EXCLUDE:
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath, "r", encoding="utf-8", errors="ignore").read()
                for b in BANNED:
                    if b.lower() in content.lower():
                        bviolations.append((fpath, b))
            except: pass
if bviolations:
    for f, b in bviolations: fail(f"BANNED FRAMEWORK '{b}' in {f}")
else:
    ok("No banned frameworks found")

# ── PHASE 0.5 Dependencies ────────────────────────────────────
section("PHASE 0.5: DEPENDENCY IMPORT CHECK")
for mod in ["anthropic","qdrant_client","sentence_transformers","pydantic","dotenv","httpx","bs4","rich"]:
    try: __import__(mod); ok(mod)
    except ImportError: fail(f"{mod} - not installed")
for mod in ["playwright","streamlit"]:
    try: __import__(mod); ok(f"{mod} (optional)")
    except ImportError: warn(f"{mod} - optional, not installed")

# ── PHASE 1.1 catalog.json ────────────────────────────────────
section("PHASE 1.1: CATALOG.JSON VALIDATION")
catalog_path = Path("data/catalog.json")
if not catalog_path.exists():
    fail("data/catalog.json missing")
else:
    data = json.loads(catalog_path.read_text("utf-8"))
    products = data["products"] if isinstance(data, dict) and "products" in data else (data if isinstance(data, list) else [])
    n = len(products)
    if n >= 50: ok(f"Product count: {n}")
    elif n >= 30: warn(f"Only {n} products (aim for 50+)")
    else: fail(f"Only {n} products (need 30+)")
    REQUIRED_FIELDS = ["product_name","price_lkr","category","url"]
    for f in REQUIRED_FIELDS:
        count = sum(1 for p in products if p.get(f) not in [None, "", []])
        pct = count/n*100 if n else 0
        if pct >= 95: ok(f"{f}: {count}/{n} ({pct:.0f}%)")
        else: fail(f"{f}: only {count}/{n} ({pct:.0f}%) — needs 95%+")
    cats = set(p.get("category","?") for p in products)
    if len(cats) >= 3: ok(f"Categories ({len(cats)}): {', '.join(sorted(cats))}")
    else: warn(f"Only {len(cats)} categories found")
    with_allergens = sum(1 for p in products if p.get("contains_allergens"))
    if with_allergens >= n * 0.3: ok(f"Allergen coverage: {with_allergens}/{n}")
    else: warn(f"Low allergen coverage: {with_allergens}/{n}")

# ── PHASE 1.2 Crawler Code ────────────────────────────────────
section("PHASE 1.2: CRAWLER CODE")
try:
    from src.crawler.kapruka_scraper import KaprukaScraper
    ok("KaprukaScraper imported")
    for m in ["scrape_all_categories","_scrape_category","_extract_product","save_catalog"]:
        if hasattr(KaprukaScraper, m): ok(f"method: {m}()")
        else: fail(f"MISSING method: {m}()")
except Exception as e:
    fail(f"Cannot import KaprukaScraper: {e}")

# ── PHASE 2.1 Short-Term Memory ───────────────────────────────
section("PHASE 2.1: SHORT-TERM MEMORY")
try:
    from src.memory.short_term import ConversationMemory
    mem = ConversationMemory(max_messages=5)
    mem.add_message("user","Hello"); mem.add_message("assistant","Hi")
    assert len(mem) == 2; ok("add_message works")
    msgs = mem.get_messages()
    assert isinstance(msgs, list) and all("role" in m and "content" in m for m in msgs)
    ok("get_messages returns Anthropic-compatible format")
    for i in range(10): mem.add_message("user", f"msg {i}")
    assert len(mem) <= 5; ok(f"Sliding window correct (len={len(mem)})")
    mem.clear(); assert len(mem) == 0; ok("clear() works")
    mem.add_message("user","gift for wife")
    s = mem.get_context_summary()
    assert isinstance(s, str) and len(s) > 0; ok(f"get_context_summary: '{s[:50]}...'")
except Exception as e:
    fail(f"Short-term memory: {e}")

# ── PHASE 2.2 Long-Term Memory (Qdrant) ──────────────────────
section("PHASE 2.2: LONG-TERM MEMORY (QDRANT)")
try:
    from config.settings import Settings
    from src.memory.long_term import CatalogVectorStore
    settings = Settings()
    store = CatalogVectorStore(settings)
    info = store.get_collection_info()
    ok(f"Connected to Qdrant | Collection: {settings.QDRANT_COLLECTION_NAME}")
    pts = info.get("points_count", 0)
    if pts >= 30: ok(f"{pts} products in vector store")
    else: warn(f"Only {pts} products — run setup_ingest.py first")
    results = store.search("birthday cake", top_k=3)
    assert len(results) > 0; ok(f"search('birthday cake') returned {len(results)} results")
    if hasattr(store, "search_excluding_allergens"):
        safe = store.search_excluding_allergens("chocolate gift", allergens=["nuts"], top_k=3)
        ok(f"search_excluding_allergens returned {len(safe)} nut-free results")
    else: fail("Missing method: search_excluding_allergens")
except Exception as e:
    fail(f"Long-term memory: {e}")

# ── PHASE 2.3 Semantic Memory ─────────────────────────────────
section("PHASE 2.3: SEMANTIC MEMORY (RECIPIENT PROFILES)")
try:
    from src.memory.semantic import RecipientMemory
    mem = RecipientMemory(Path("data/recipient_profiles.json"))
    recipients = mem.list_recipients()
    if len(recipients) >= 3: ok(f"Loaded {len(recipients)} profiles: {', '.join(recipients)}")
    else: warn(f"Only {len(recipients)} profiles (need 3+)")
    wife = mem.get_profile("wife")
    assert wife and wife.get("name"); ok(f"get_profile('wife') -> {wife.get('name')}")
    allergies = mem.get_allergies("wife")
    assert isinstance(allergies, list) and len(allergies) > 0; ok(f"get_allergies('wife') -> {allergies}")
    if hasattr(mem, "find_recipient"):
        r = mem.find_recipient("gift for my wife")
        assert r is not None; key, _ = r; ok(f"find_recipient('...my wife...') -> {key}")
        r2 = mem.find_recipient("gift for amma")
        if r2: ok(f"find_recipient('...amma...') -> {r2[0]}")
        else: warn("'amma' not matched (Sri Lankan term — consider adding)")
    else: fail("Missing method: find_recipient")
    if hasattr(mem, "format_for_prompt"):
        fmt = mem.format_for_prompt("wife")
        assert isinstance(fmt, str) and len(fmt) > 0; ok(f"format_for_prompt works ({len(fmt)} chars)")
    else: fail("Missing method: format_for_prompt")
    unknown = mem.get_profile("uncle_nobody")
    assert unknown is None; ok("Unknown recipient returns None")
except Exception as e:
    fail(f"Semantic memory: {e}")

# ── PHASE 2.4 MemoryManager ───────────────────────────────────
section("PHASE 2.4: MEMORY MANAGER")
try:
    from src.memory.manager import MemoryManager
    mgr = MemoryManager(settings)
    mgr.add_user_message("I need a cake for my wife")
    ctx = mgr.get_conversation_context()
    assert len(ctx) >= 1; ok("add_user_message + get_conversation_context works")
    full = mgr.get_full_context("I need a cake for my wife")
    for key in ["conversation","recipient_key","recipient_profile","recipient_allergies"]:
        if key in full: ok(f"get_full_context has '{key}'")
        else: fail(f"get_full_context missing '{key}'")
    results = mgr.search_products("chocolate cake", recipient_key="wife")
    assert isinstance(results, list); ok(f"search_products -> {len(results)} results")
    mgr.clear_session()
    assert len(mgr.get_conversation_context()) == 0; ok("clear_session works")
except Exception as e:
    fail(f"MemoryManager: {e}")

# ── PHASE 3.1 Router ──────────────────────────────────────────
section("PHASE 3.1: ROUTER AGENT")
try:
    from src.llm.client import LLMClient
    from src.agents.router import RouterAgent
    llm = LLMClient(settings); router = RouterAgent(llm)
    cases = [
        ("I need a birthday cake for my wife","PRODUCT_SEARCH"),
        ("My wife is allergic to nuts","PREFERENCE_UPDATE"),
        ("Can you deliver to Kandy by Friday?","DELIVERY_CHECK"),
        ("Same as last year for Valentine's","ORDER_HISTORY"),
        ("Hello, how are you?","GENERAL"),
    ]
    correct = 0
    for msg, expected in cases:
        result = router.classify(msg)
        actual = result.get("intent","UNKNOWN")
        if actual == expected: correct += 1; ok(f"'{msg[:40]}' -> {actual}")
        else: fail(f"'{msg[:40]}' -> {actual} (expected {expected})")
    acc = correct/len(cases)*100
    if acc >= 75: ok(f"Router accuracy: {correct}/{len(cases)} ({acc:.0f}%)")
    else: fail(f"Router accuracy too low: {acc:.0f}% (need 75%+)")
except Exception as e:
    fail(f"Router: {e}")

# ── PHASE 3.2 Catalog Specialist ──────────────────────────────
section("PHASE 3.2: CATALOG SPECIALIST")
try:
    from src.agents.catalog_specialist import CatalogSpecialist
    from src.memory.manager import MemoryManager
    memory = MemoryManager(settings)
    catalog = CatalogSpecialist(LLMClient(settings), memory)
    r = catalog.search_and_recommend(query="birthday cake")
    assert "products_found" in r and "recommendation_text" in r
    assert len(r["products_found"]) > 0; ok(f"Basic search: {len(r['products_found'])} products")
    assert len(r["recommendation_text"]) > 50; ok(f"Recommendation: {len(r['recommendation_text'])} chars")
except Exception as e:
    fail(f"Catalog Specialist: {e}")

# ── PHASE 3.3 Logistics Specialist ────────────────────────────
section("PHASE 3.3: LOGISTICS SPECIALIST")
try:
    from src.agents.logistics_specialist import LogisticsSpecialist
    logistics = LogisticsSpecialist(LLMClient(settings), settings)
    for dest, ptype, note in [("Colombo","standard","same-day"),("Kandy","standard","2-day"),("Jaffna","standard","3-day")]:
        r = logistics.check_delivery(destination=dest, product_type=ptype)
        deliverable = r.get("deliverable")
        ok(f"{dest} ({ptype}) -> deliverable={deliverable} | {note}")
except Exception as e:
    fail(f"Logistics Specialist: {e}")

# ── PHASE 3.4 Full Orchestrator ───────────────────────────────
section("PHASE 3.4: FULL ORCHESTRATOR PIPELINE")
try:
    from src.orchestrator import GiftConciergeAgent
    agent = GiftConciergeAgent()
    r1 = agent.chat("I need a birthday cake for my wife")
    assert "response" in r1 and "intent" in r1 and len(r1["response"]) > 50
    ok(f"Product search: intent={r1['intent']}, {len(r1['response'])} chars, {r1['metadata']['latency_ms']:.0f}ms")
    r2 = agent.chat("Can you deliver to Kandy?")
    ok(f"Delivery check: intent={r2['intent']}")
    assert "metadata" in r1 and "latency_ms" in r1["metadata"]
    ok("Metadata structure correct")
except Exception as e:
    fail(f"Orchestrator: {e}")

# ── PHASE 4.1 Reflection Loop ─────────────────────────────────
section("PHASE 4.1: REFLECTION LOOP - ALLERGEN TRAP TEST")
try:
    agent = GiftConciergeAgent()
    agent.reset_session()
    r = agent.chat("Get me a nice chocolate gift box for my wife")
    has_refl = r.get("reflection_log") is not None
    if has_refl:
        log = r["reflection_log"]
        ok(f"Reflection triggered ({len(log)} iteration(s))")
        final = r["response"].lower()
        nut_kw = ["almond","cashew","walnut","pistachio","peanut","hazelnut"]
        found = [k for k in nut_kw if k in final and "free" not in final]
        if not found: ok("Final response appears nut-safe")
        else: fail(f"Final response may still mention: {found}")
    else:
        fail("Reflection loop NOT triggered for allergen trap")
except Exception as e:
    fail(f"Reflection loop: {e}")

# ── PHASE 4.2 Reflection Structure ────────────────────────────
section("PHASE 4.2: REFLECTION LOOP STRUCTURE")
try:
    from src.agents.reflection import ReflectionLoop
    for m in ["run","_reflect","_revise"]:
        if hasattr(ReflectionLoop, m): ok(f"method: {m}()")
        else: fail(f"MISSING method: {m}()")
except Exception as e:
    fail(f"ReflectionLoop import: {e}")

# ── PHASE 5.1 Evaluation ──────────────────────────────────────
section("PHASE 5.1: EVALUATION FRAMEWORK")
try:
    from src.evaluation import AgentEvaluator
    evaluator = AgentEvaluator(agent, Path("data/test_scenarios.json"))
    ok(f"Evaluator loaded {len(evaluator.scenarios)} scenarios")
    r = evaluator._run_scenario(evaluator.scenarios[0])
    sc = evaluator.scenarios[0]
    ok(f"Scenario {sc['id']}: intent={r['actual_intent']} | safe={r['allergy_safe']} | {r['latency_ms']:.0f}ms")
except Exception as e:
    fail(f"Evaluation: {e}")

# ── PHASE 5.2 Metrics Structure ───────────────────────────────
section("PHASE 5.2: METRICS STRUCTURE")
try:
    from src.evaluation import AgentEvaluator
    for m in ["_calculate_metrics","_estimate_costs","generate_report_data"]:
        if hasattr(AgentEvaluator, m): ok(f"method: {m}()")
        else: fail(f"MISSING method: {m}()")
except Exception as e:
    fail(f"Metrics: {e}")

# ── PHASE 6 UI ────────────────────────────────────────────────
section("PHASE 6: BONUS UI VALIDATION")
ui_path = Path("ui/streamlit_app.py")
if not ui_path.exists():
    warn("ui/streamlit_app.py not found (bonus feature)")
else:
    content = ui_path.read_text(encoding="utf-8")
    for label, check in [
        ("streamlit import", "import streamlit" in content),
        ("chat_message", "chat_message" in content),
        ("chat_input", "chat_input" in content),
        ("session_state", "session_state" in content),
        ("sidebar", "sidebar" in content),
        ("expander", "expander" in content),
        ("spinner", "spinner" in content),
        ("GiftConciergeAgent", "GiftConciergeAgent" in content or "orchestrator" in content),
    ]:
        if check: ok(label)
        else: fail(label)

# ── PHASE 7 Notebooks ─────────────────────────────────────────
section("PHASE 7: NOTEBOOKS")
for nb_path, label in [
    ("notebooks/01_crawler.ipynb","Crawler"),
    ("notebooks/02_memory_lab.ipynb","Memory Lab"),
    ("notebooks/03_orchestration.ipynb","Orchestration"),
    ("notebooks/04_reflection.ipynb","Reflection"),
    ("notebooks/05_evaluation.ipynb","Evaluation"),
]:
    p = Path(nb_path)
    if not p.exists(): fail(f"MISSING: {nb_path}"); continue
    nb = json.loads(p.read_text(encoding="utf-8"))
    code_cells = [c for c in nb.get("cells",[]) if c.get("cell_type")=="code"]
    executed = [c for c in code_cells if c.get("execution_count") is not None]
    if executed: ok(f"{nb_path} — {len(executed)}/{len(code_cells)} cells executed")
    else: warn(f"{nb_path} — 0 cells executed! Run before submission.")

# ── PHASE 8 Report ────────────────────────────────────────────
section("PHASE 8: PDF REPORT")
rp = Path("report/technical_proposal.pdf")
if rp.exists():
    kb = rp.stat().st_size / 1024
    ok(f"report/technical_proposal.pdf exists ({kb:.0f} KB)")
else:
    fail("MISSING: report/technical_proposal.pdf — required for submission")

# ── FINAL SUMMARY ─────────────────────────────────────────────
print()
print("=" * 60)
print("🏁 FINAL VALIDATION SUMMARY")
print("=" * 60)
print(f"  ✅ PASS : {PASS}")
print(f"  ❌ FAIL : {FAIL}")
print(f"  ⚠️  WARN : {WARN}")
print()
if FAIL == 0:
    print("🎉 ALL CHECKS PASSED — Ready for submission!")
else:
    print(f"⛔ {FAIL} checks failed — fix before submitting.")
