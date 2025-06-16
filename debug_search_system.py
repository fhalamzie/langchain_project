#!/usr/bin/env python3
"""Debug search system data loading"""

import sys
sys.path.append('src')

from wincasa.core.wincasa_optimized_search import WincasaOptimizedSearch
from wincasa.core.wincasa_query_engine import WincasaQueryEngine

# Test 1: Direct search system
print("=== Testing Direct Search System ===")
search = WincasaOptimizedSearch(
    rag_data_dir="data/exports/rag_data",
    debug_mode=True
)
print(f"\nLoaded data:")
print(f"  Mieter: {len(search.mieter_data)}")
print(f"  Eigentümer: {len(search.eigentuemer_data)}")
print(f"  Objekte: {len(search.objekte_data)}")

# Test 2: Check some specific data
if search.mieter_data:
    print(f"\nFirst tenant: {search.mieter_data[0]}")

# Test 3: Try a search
print("\n=== Testing Search ===")
result = search.query("wer wohnt marienstr 26")
print(f"Search result: {result}")

# Test 4: Test through query engine
print("\n=== Testing Query Engine ===")
engine = WincasaQueryEngine(debug_mode=True)
result = engine.process_query("wer wohnt marienstr 26")
print(f"\nQuery result:")
print(f"  Answer: {result.answer}")
print(f"  Result count: {result.result_count}")
print(f"  Processing mode: {result.processing_mode}")