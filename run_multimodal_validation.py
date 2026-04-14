"""
Multimodal Validation Script — equivalent to running notebooks/06_multimodal_demo.ipynb
Runs all 5 validation checks + demo queries without Jupyter kernel overhead.

Usage:
    python run_multimodal_validation.py

Exit code 0 = all checks pass.
Exit code 1 = one or more checks failed.
"""
import sys
import gc
import json
from pathlib import Path

import torch
torch.set_num_threads(2)  # Limit CPU parallelism to reduce peak RAM

sys.path.insert(0, str(Path(__file__).parent))

# ──────────────────────────────────────────────────────────────────────────────
print("=" * 64)
print("Kapruka Multimodal Validation (Phase 8)")
print("=" * 64)

# ── Cell 1: Load components ───────────────────────────────────────────────────
print("\n[1/5] Loading components...")
from config.settings import Settings
from src.multimodal.clip_encoder import CLIPEncoder
from src.multimodal.image_store import ImageVectorStore
from src.multimodal.fusion_ranker import FusionRanker
from src.memory.long_term import CatalogVectorStore

settings  = Settings()
encoder   = CLIPEncoder()       # Loads CLIP once (singleton)
img_store = ImageVectorStore()
txt_store = CatalogVectorStore(settings)
fusion    = FusionRanker()

info = img_store.get_collection_info()
print(f"  CLIP collection : {info['name']}")
print(f"  Image vectors   : {info['vectors_count']}")
print(f"  Vector dim      : {info['vector_size']} (CLIP shared space)")
print(f"  Distance metric : {info['distance']}")

# ── Cell 2: Pure CLIP retrieval ───────────────────────────────────────────────
print("\n[2/5] Pure CLIP retrieval test...")
query = "red velvet birthday cake"
results = img_store.search(query, top_k=5)
print(f"  Query: \"{query}\"")
print(f"  {'#':<4} {'Product':<40} {'Category':<14} {'Price LKR':>10} {'CLIP Score':>11}")
print(f"  {'-'*82}")
for i, r in enumerate(results, 1):
    p = r["product"]
    name = p.get("product_name", "?")[:38]
    print(f"  {i:<4} {name:<40} {p.get('category','?'):<14} {p.get('price_lkr',0):>10,.0f} {r['clip_score']:>11.4f}")

gc.collect()  # Free memory between heavy operations

# ── Cell 4: Fusion demo ───────────────────────────────────────────────────────
print("\n[3/5] Fusion ranking test...")
fq = "birthday gift for mother"
text_results  = txt_store.search(fq, top_k=5)
image_results = img_store.search(fq, top_k=5)
fused         = fusion.fuse(text_results, image_results, top_k=5)

print(f"  Query: \"{fq}\"")
print(f"  Text RAG: {len(text_results)} | CLIP: {len(image_results)} | Fused: {len(fused)}")
print(f"  {'#':<3} {'Product':<38} {'Fused':>6} {'Text':>6} {'Image':>6} {'Source':<12}")
print(f"  {'-'*78}")
for i, r in enumerate(fused, 1):
    name = r["product"].get("product_name", "?")[:36]
    print(f"  {i:<3} {name:<38} {r['fused_score']:>6.3f} {r['text_score']:>6.3f} {r['image_score']:>6.3f} {r['retrieval_source']:<12}")

image_only = [r for r in fused if r["retrieval_source"] == "image_only"]
both       = [r for r in fused if r["retrieval_source"] == "both"]
text_only  = [r for r in fused if r["retrieval_source"] == "text_only"]
print(f"\n  BOTH: {len(both)} | TEXT only: {len(text_only)} | IMAGE (CLIP) only: {len(image_only)}")

gc.collect()

# ── Cell 6: 5 diverse queries ─────────────────────────────────────────────────
print("\n[4/5] Multi-category CLIP queries...")
QUERIES = [
    "chocolate birthday cake with candles",
    "elegant flower bouquet for anniversary",
    "luxury gift hamper with multiple items",
    "something colourful and festive",
    "traditional Sri Lankan sweet treat",
]
print(f"  {'Query':<45} {'Top CLIP Match':<38} {'Cat':<12} {'Score':>6}")
print(f"  {'-'*106}")
for q in QUERIES:
    res = img_store.search(q, top_k=1)
    if res:
        p = res[0]["product"]
        print(f"  {q[:43]:<45} {p.get('product_name','?')[:36]:<38} "
              f"{p.get('category','?')[:10]:<12} {res[0]['clip_score']:>6.3f}")

gc.collect()

# ── Cell 8: Validation checklist ──────────────────────────────────────────────
print("\n[5/5] Validation checklist...")
print("=" * 64)
all_pass = True

# Check 1: images on disk
image_dir   = Path("data/images")
image_count = len(list(image_dir.glob("*"))) if image_dir.exists() else 0
ok = image_count >= 100
status = "OK  " if ok else "FAIL"
print(f"  [{status}] Images on disk          : {image_count}  (need >= 100)")
if not ok: all_pass = False

# Check 2: manifest
manifest = Path("data/image_manifest.json")
ok = manifest.exists()
status = "OK  " if ok else "FAIL"
print(f"  [{status}] image_manifest.json     : {'exists' if ok else 'MISSING'}")
if not ok: all_pass = False

# Check 3: Qdrant CLIP collection
clip_info = img_store.get_collection_info()
n = clip_info["vectors_count"]
ok = n >= 100
status = "OK  " if ok else "FAIL"
print(f"  [{status}] CLIP vectors in Qdrant  : {n}  (need >= 100)")
if not ok: all_pass = False

# Check 4: cross-modal search
hits = img_store.search("birthday cake", top_k=3)
ok = len(hits) > 0
status = "OK  " if ok else "FAIL"
print(f"  [{status}] Cross-modal search       : {len(hits)} results for 'birthday cake'")
for r in hits:
    print(f"           -> {r['product'].get('product_name','?')[:45]}  CLIP={r['clip_score']:.4f}")
if not ok: all_pass = False

# Check 5: fusion
t_res = txt_store.search("birthday cake", top_k=5)
i_res = img_store.search("birthday cake", top_k=5)
f_res = fusion.fuse(t_res, i_res, top_k=5)
ok = len(f_res) > 0
status = "OK  " if ok else "FAIL"
print(f"  [{status}] Fusion ranker            : {len(f_res)} fused results")
if f_res:
    top = f_res[0]
    print(f"           Top: {top['product'].get('product_name','?')[:40]}  "
          f"score={top['fused_score']:.4f}  src={top['retrieval_source']}")
if not ok: all_pass = False

print("=" * 64)
if all_pass:
    print("\n[ALL PASS] Phase 8 multimodal validation complete.")
    print("  Text RAG + CLIP Image + Fusion Ranking: FULLY OPERATIONAL")
else:
    print("\n[FAIL] One or more checks failed. See above.")
    sys.exit(1)
