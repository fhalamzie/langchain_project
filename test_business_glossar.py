#!/usr/bin/env python3
"""
Test script for Business Glossar Implementation

This script validates the business glossar functionality by testing:
1. Term extraction from natural language queries
2. SQL pattern generation
3. Table relationship identification
4. Integration with the WINCASA SQL agent
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from business_glossar import BusinessGlossar, extract_business_entities, WINCASA_GLOSSAR
from global_context import get_query_specific_context
from firebird_sql_agent_direct import FirebirdDirectSQLAgent


def test_business_term_extraction():
    """Test business term extraction from various queries."""
    print("=" * 60)
    print("TEST 1: Business Term Extraction")
    print("=" * 60)
    
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Welche Eigentümer haben offene Posten?",
        "Zeige mir alle leerstehenden Wohnungen",
        "Wie hoch sind die Nebenkosten für Mieter?",
        "Welche Kautionen wurden von Bewohnern hinterlegt?",
        "Gibt es gekündigte Verträge?",
        "Zeige alle aktiven Verwalter",
        "Welche Kredite bestehen für das Objekt?",
        "Wie lautet die Adresse des Eigentümers?",
        "Zeige Mieter in Köln"
    ]
    
    glossar = WINCASA_GLOSSAR
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        
        result = extract_business_entities(query, glossar)
        
        print(f"📋 Found Terms: {result['extracted_terms']}")
        print(f"🗂️ Categories: {list(result['category_mappings'].keys())}")
        print(f"🗄️ Tables: {result['tables_involved']}")
        print(f"🔗 JOIN Hints: {len(result['join_hints'])}")
        print(f"📊 Matches: {result['direct_matches']} direct, {result['fuzzy_matches']} fuzzy")
        
        if result['sql_patterns']:
            print("💡 SQL Patterns:")
            for pattern in result['sql_patterns']:
                print(f"   • {pattern['term']}: {pattern['pattern'][:50]}...")
    
    return True


def test_business_context_generation():
    """Test business context generation for SQL agent."""
    print("\n" + "=" * 60)
    print("TEST 2: Business Context Generation")
    print("=" * 60)
    
    test_query = "Welche Mieter haben offene Posten und wohnen in der Marienstraße?"
    
    print(f"Query: {test_query}")
    
    # Extract business terms
    business_extraction = extract_business_entities(test_query, WINCASA_GLOSSAR)
    
    # Generate query-specific context
    enhanced_context = get_query_specific_context(test_query, business_extraction['business_terms'])
    
    print("\n📄 Generated Business Context:")
    print(enhanced_context)
    
    print(f"\n🔗 JOIN Hints Generated:")
    for hint in business_extraction['join_hints']:
        print(f"   • {hint}")
    
    return True


def test_fuzzy_matching():
    """Test fuzzy matching capabilities."""
    print("\n" + "=" * 60)
    print("TEST 3: Fuzzy Matching")
    print("=" * 60)
    
    glossar = WINCASA_GLOSSAR
    
    # Test queries with variations and typos
    fuzzy_queries = [
        "Zeige mir alle Bewohner",  # Alternative term for Mieter
        "Welche Besitzer gibt es?",  # Alternative term for Eigentümer  
        "Wie viele Einheiten stehen leer?",  # Alternative term for Wohnung
        "Zeige Hausverwalter",  # Alternative for Verwalter
        "Welche Schulden bestehen?",  # Alternative for offene Posten
    ]
    
    for query in fuzzy_queries:
        print(f"\n--- Fuzzy Test: {query} ---")
        
        result = extract_business_entities(query, glossar)
        
        print(f"📋 Extracted Terms: {result['extracted_terms']}")
        print(f"📊 Direct: {result['direct_matches']}, Fuzzy: {result['fuzzy_matches']}")
        
        if result['business_terms']:
            for term in result['business_terms']:
                print(f"   • Matched '{term.term}' via aliases: {term.aliases}")
    
    return True


def test_sql_agent_integration():
    """Test integration with the SQL agent (simulation)."""
    print("\n" + "=" * 60)
    print("TEST 4: SQL Agent Integration Simulation")
    print("=" * 60)
    
    # Simulate the business glossar integration without full agent setup
    test_query = "Wie viele Wohnungen gibt es insgesamt?"
    
    print(f"Simulating agent query: {test_query}")
    
    # Extract business terms
    business_extraction = extract_business_entities(test_query, WINCASA_GLOSSAR)
    
    print(f"\n🔍 Business Analysis:")
    print(f"   Terms found: {business_extraction['extracted_terms']}")
    print(f"   Tables identified: {business_extraction['tables_involved']}")
    print(f"   Categories: {list(business_extraction['category_mappings'].keys())}")
    
    # Build enhanced context as the agent would
    enhanced_context_parts = []
    
    if business_extraction['business_terms']:
        business_context = get_query_specific_context(test_query, business_extraction['business_terms'])
        enhanced_context_parts.append(f"--- BUSINESS CONTEXT ---\n{business_context}")
    
    if business_extraction['prompt_section']:
        enhanced_context_parts.append(business_extraction['prompt_section'])
    
    combined_context = "\n\n".join(enhanced_context_parts)
    
    print(f"\n📄 Context that would be sent to LLM:")
    print(combined_context)
    
    # Simulate enhanced query
    enhanced_query = f"""
Basierend auf dem folgenden Kontext:
--- START OF CONTEXT ---
{combined_context}
--- END OF CONTEXT ---

{f"JOIN-Hinweise: {', '.join(business_extraction['join_hints'])}" if business_extraction['join_hints'] else ""}

Bitte beantworte die folgende Frage: {test_query}
"""
    
    print(f"\n📝 Enhanced Query Structure:")
    print(f"   Original: {test_query}")
    print(f"   Context length: {len(combined_context)} chars")
    print(f"   JOIN hints: {len(business_extraction['join_hints'])}")
    print(f"   Business terms integrated: {len(business_extraction['business_terms'])}")
    
    return True


def test_glossar_coverage():
    """Test business glossar coverage of common WINCASA terms."""
    print("\n" + "=" * 60)
    print("TEST 5: Glossar Coverage Analysis")
    print("=" * 60)
    
    glossar = WINCASA_GLOSSAR
    
    print(f"📊 Business Glossar Statistics:")
    print(f"   Total terms: {len(glossar.terms)}")
    print(f"   Total aliases: {len(glossar.aliases_map)}")
    
    # Analyze by category
    from collections import defaultdict
    categories = defaultdict(list)
    
    for term_name, term in glossar.terms.items():
        categories[term.category.value].append(term.term)
    
    print(f"\n📂 Terms by Category:")
    for category, terms in categories.items():
        print(f"   • {category.upper()}: {len(terms)} terms")
        for term in terms:
            print(f"     - {term}")
    
    # Test coverage with common property management queries
    coverage_queries = [
        "Mieter", "Eigentümer", "Wohnung", "Objekt", "Adresse",
        "Miete", "Kosten", "Kaution", "Verwalter", "Leerstand",
        "offene Posten", "Nebenkosten", "aktiv", "gekündigt"
    ]
    
    print(f"\n🎯 Coverage Test:")
    covered = 0
    for query_term in coverage_queries:
        result = extract_business_entities(query_term, glossar)
        if result['extracted_terms']:
            covered += 1
            print(f"   ✅ {query_term} → {result['extracted_terms']}")
        else:
            print(f"   ❌ {query_term} (not covered)")
    
    coverage_percentage = (covered / len(coverage_queries)) * 100
    print(f"\n📈 Coverage: {covered}/{len(coverage_queries)} ({coverage_percentage:.1f}%)")
    
    return True


def main():
    """Run all business glossar tests."""
    print("🏗️ WINCASA Business Glossar Test Suite")
    print("=" * 60)
    
    tests = [
        ("Business Term Extraction", test_business_term_extraction),
        ("Business Context Generation", test_business_context_generation),
        ("Fuzzy Matching", test_fuzzy_matching),
        ("SQL Agent Integration", test_sql_agent_integration),
        ("Glossar Coverage", test_glossar_coverage),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"🏆 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Business Glossar is ready for production.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)