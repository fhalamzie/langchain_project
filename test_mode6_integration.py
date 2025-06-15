#!/usr/bin/env python3
"""
Integration test for Mode 6 Semantic Template Engine
Tests complete integration with WincasaQueryEngine
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wincasa.core.wincasa_query_engine import WincasaQueryEngine

def test_mode6_integration():
    """Test Mode 6 integration with Query Engine"""
    
    print("🚀 Testing Mode 6 Integration with Query Engine...")
    
    # Initialize engine with debug mode
    engine = WincasaQueryEngine(debug_mode=True)
    
    # Set rollout to 100% to ensure unified mode
    engine.update_rollout_percentage(100)
    
    # Test queries that should trigger Mode 6
    test_queries = [
        ("Alle Mieter von Fahim Halamzie", "Should use Mode 6 - semantic template"),
        ("Portfolio von Bona Casa GmbH", "Should use Mode 6 - semantic template"),  
        ("Leerstand von Weber", "Should use Mode 6 - semantic template"),
        ("Wer wohnt in der Aachener Str. 71?", "Should use Template Engine - existing template"),
        ("Freie Wohnungen in Essen", "Should use Template Engine - existing template"),
        ("Erstelle einen Bericht über Rückstände", "Should use Legacy - complex analysis")
    ]
    
    print(f"\n📋 Testing {len(test_queries)} queries with full routing:")
    
    for query, expectation in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print(f"   🎯 Expectation: {expectation}")
        
        # Process with Query Engine
        result = engine.process_query(query, user_id="test_user", force_mode="unified")
        
        print(f"   ✅ Engine: {result.engine_version}")
        print(f"   🎯 Mode: {result.processing_mode}")
        print(f"   📊 Results: {result.result_count}")
        print(f"   ⏱️  Time: {result.processing_time_ms}ms")
        print(f"   💰 Cost: ${result.cost_estimate:.4f}")
        print(f"   🎭 Confidence: {result.confidence:.1%}")
        
        # Validate Mode 6 routing
        if "Alle Mieter von" in query or "Portfolio von" in query or "Leerstand von" in query:
            expected_mode = "semantic_template"
            if result.processing_mode == expected_mode:
                print(f"   ✅ SUCCESS: Correctly routed to {expected_mode}")
            else:
                print(f"   ❌ FAILURE: Expected {expected_mode}, got {result.processing_mode}")
        
        print(f"   💬 Answer: {result.answer[:100]}...")
    
    # Test system statistics
    print(f"\n📊 System Statistics:")
    stats = engine.get_system_stats()
    
    print(f"   Total Queries: {stats['query_statistics']['total_queries']}")
    print(f"   Unified Queries: {stats['query_statistics']['unified_queries']}")
    print(f"   Semantic Queries: {stats['query_statistics']['semantic_queries']}")
    print(f"   Avg Processing Time: {stats['query_statistics']['avg_processing_time']:.1f}ms")
    print(f"   Avg Cost per Query: ${stats['query_statistics']['avg_cost_per_query']:.4f}")
    
    print(f"\n🎯 Mode 6 Implementation:")
    semantic_queries = stats['query_statistics']['semantic_queries']
    total_queries = stats['query_statistics']['total_queries']
    
    if semantic_queries > 0:
        semantic_percentage = (semantic_queries / total_queries) * 100
        print(f"   ✅ Mode 6 Active: {semantic_queries}/{total_queries} queries ({semantic_percentage:.1f}%)")
        print(f"   ✅ Implementation: SUCCESSFUL")
    else:
        print(f"   ⚠️  Mode 6 not triggered in this test")

if __name__ == "__main__":
    test_mode6_integration()