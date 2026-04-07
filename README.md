# 🎁 Kapruka Gift-Concierge Agent

> **AEE Bootcamp | Mini Project 03** - Agentic Design Patterns & Cognitive Memory Systems

A fully custom AI gift-concierge agent for [Kapruka.com](https://www.kapruka.com) - Sri Lanka's leading online gift platform. Built from scratch with raw Python + Anthropic Claude + Qdrant, with **zero agent frameworks**.

---

## Architecture

```
User Message
    ↓
GiftConciergeAgent (orchestrator.py)
    ↓
RouterAgent → classifies intent
    ↓
PRODUCT_SEARCH  → CatalogSpecialist → ReflectionLoop → Response
DELIVERY_CHECK  → LogisticsSpecialist → Response
PREFERENCE_UPDATE → RecipientMemory update → Confirmation
ORDER_HISTORY   → SemanticMemory lookup → Response
GENERAL         → Direct LLM response
```

## Memory Architecture

| Tier | Component | Storage | Purpose |
|------|-----------|---------|---------|
| Short-Term | `ConversationMemory` | In-memory list | Rolling 20-message conversation buffer |
| Long-Term | `CatalogVectorStore` | Qdrant Cloud | RAG vector search over product catalog |
| Semantic | `RecipientMemory` | JSON file | Recipient profiles, allergies, preferences |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
```

### 3. Crawl & Ingest Catalog

```bash
# Run the crawler (or use pre-curated catalog.json)
python -c "
import asyncio
from src.crawler.kapruka_scraper import KaprukaScraper
from config import settings
scraper = KaprukaScraper(settings)
asyncio.run(scraper.scrape_all_categories())
"

# Ingest catalog into Qdrant
python -c "
from config import settings
from src.memory.long_term import CatalogVectorStore
store = CatalogVectorStore(settings)
store.create_collection()
store.ingest_catalog(settings.CATALOG_PATH)
print('Ingestion complete!')
"
```

### 4. Run the Agent

```python
from src.orchestrator import GiftConciergeAgent

agent = GiftConciergeAgent()
result = agent.chat("I need a birthday cake for my wife")
print(result["response"])
```

### 5. Run the UI

```bash
streamlit run ui/streamlit_app.py
```

## Project Structure

```
kapruka-gift-concierge/
├── .env                     # API keys (NEVER commit)
├── .env.example             # Template for graders
├── requirements.txt
├── config/
│   ├── settings.py          # Central configuration
│   └── delivery_zones.json  # Sri Lankan delivery rules
├── data/
│   ├── catalog.json         # Crawled product catalog
│   ├── recipient_profiles.json  # Semantic memory
│   └── test_scenarios.json  # Evaluation test cases
├── src/
│   ├── llm/client.py        # Anthropic API wrapper
│   ├── memory/              # 3-tier memory system
│   ├── agents/              # Router + Specialists + Reflection
│   ├── orchestrator.py      # Main GiftConciergeAgent
│   └── evaluation.py        # Performance metrics
├── notebooks/               # Demo notebooks (01-05)
└── ui/streamlit_app.py      # Chat interface (Bonus)
```

## Evaluation Metrics

| Metric | Target |
|--------|--------|
| Router Accuracy | > 90% |
| Allergy Safety Rate | **100%** |
| Reflection Catch Rate | > 80% |
| Avg Latency | < 10s |

## Key Design Decisions

- **No Frameworks**: Pure Python orchestration, full control
- **Allergen Safety**: Reflection loop is the safety net - catches dangerous recommendations before they reach the user
- **Local Embeddings**: `all-MiniLM-L6-v2` (free, 384d) for zero embedding API costs
- **Sri Lankan Context**: Knows Sinhala relationship terms (amma, thaththa, akka), Sri Lankan districts, local occasions (Avurudu)
