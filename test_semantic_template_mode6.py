#!/usr/bin/env python3
"""
Test script for Semantic Template Engine Mode 6
Tests the specific use case: "Alle Mieter von Fahim Halamzie"
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wincasa.core.semantic_template_engine import SemanticTemplateEngine

def test_semantic_template_mode6():
    """Test Semantic Template Engine with parameterized queries"""
    
    print("🧩 Testing Semantic Template Engine Mode 6...")
    
    # Initialize engine
    engine = SemanticTemplateEngine(debug_mode=True)
    
    # Test queries from the identified gap
    test_queries = [
        "Alle Mieter von Fahim Halamzie",
        "Portfolio von Bona Casa GmbH", 
        "Leerstand von Weber",
        "Objekte in Essen",
        "Mieter seit 2023",
        "Wartung für Aachener Str. 71"
    ]
    
    print(f"\n📋 Testing {len(test_queries)} semantic queries:")
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        # Step 1: Check if engine can handle
        can_handle, confidence = engine.can_handle_query(query)
        print(f"   ✅ Can handle: {can_handle} (confidence: {confidence:.2f})")
        
        if can_handle:
            # Step 2: Process query
            result = engine.process_query(query)
            
            print(f"   🎯 Pattern: {result.pattern.pattern_id if result.pattern else 'None'}")
            print(f"   📊 Success: {result.success}")
            print(f"   ⏱️  Time: {result.processing_time_ms}ms")
            print(f"   💬 Answer: {result.answer}")
            
            if result.sql_query:
                print(f"   📝 SQL: {result.sql_query[:100]}...")
    
    # Test supported patterns
    print(f"\n📋 Supported Semantic Patterns:")
    patterns = engine.get_supported_patterns()
    
    for pattern in patterns:
        print(f"   • {pattern['name']} ({pattern['id']})")
        print(f"     Example: {pattern['example_patterns'][0]}")
        print(f"     Description: {pattern['description']}")
        print()

if __name__ == "__main__":
    test_semantic_template_mode6()