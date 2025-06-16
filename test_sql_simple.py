#!/usr/bin/env python3
"""Simple SQL mode test"""

import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'

from wincasa.core.wincasa_query_engine import WincasaQueryEngine

def test_sql_mode():
    """Test SQL mode with corrected prompt"""
    
    print("=== Testing SQL Mode with Corrected Prompt ===\n")
    
    # Create engine in SQL mode with unified system disabled
    engine = WincasaQueryEngine()
    # Force disable unified system for this test
    engine.config["feature_flags"]["unified_system_enabled"] = False
    
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Zeige alle Mieter mit Namen",
        "Welche Objekte gibt es?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        try:
            result = engine.process_query(query)
            
            print(f"   Success: {result.result_count > 0}")
            print(f"   Result count: {result.result_count}")
            print(f"   Mode: {result.processing_mode}")
            
            if result.result_count > 0:
                print(f"   Answer preview: {result.answer[:150]}...")
            else:
                print(f"   Answer: {result.answer}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    test_sql_mode()