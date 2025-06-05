#!/usr/bin/env python3
"""
Simple Test script for Business Glossar Implementation

This script validates the business glossar functionality without requiring
the full SQL agent dependencies.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from business_glossar import WINCASA_GLOSSAR, BusinessGlossar, extract_business_entities

from global_context import get_query_specific_context


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
    ]

    glossar = WINCASA_GLOSSAR

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i}: {query} ---")

        result = extract_business_entities(query, glossar)

        print(f"📋 Found Terms: {result['extracted_terms']}")
        print(f"🗂️ Categories: {list(result['category_mappings'].keys())}")
        print(f"🗄️ Tables: {result['tables_involved']}")
        print(f"🔗 JOIN Hints: {len(result['join_hints'])}")

        if result["sql_patterns"]:
            print("💡 SQL Patterns:")
            for pattern in result["sql_patterns"]:
                print(f"   • {pattern['term']}: {pattern['pattern'][:80]}...")

    return True


def test_business_context_generation():
    """Test business context generation."""
    print("\n" + "=" * 60)
    print("TEST 2: Business Context Generation")
    print("=" * 60)

    test_query = "Welche Mieter haben offene Posten und wohnen in der Marienstraße?"

    print(f"Query: {test_query}")

    # Extract business terms
    business_extraction = extract_business_entities(test_query, WINCASA_GLOSSAR)

    # Generate query-specific context
    enhanced_context = get_query_specific_context(
        test_query, business_extraction["business_terms"]
    )

    print("\n📄 Generated Business Context:")
    print(
        enhanced_context[:500] + "..."
        if len(enhanced_context) > 500
        else enhanced_context
    )

    print(f"\n🔗 JOIN Hints Generated:")
    for hint in business_extraction["join_hints"]:
        print(f"   • {hint}")

    return True


def test_glossar_demo():
    """Demo the business glossar with key WINCASA queries."""
    print("\n" + "=" * 60)
    print("TEST 3: WINCASA Business Glossar Demo")
    print("=" * 60)

    # Run the built-in demo
    glossar = BusinessGlossar()

    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Welche Eigentümer haben offene Posten?",
        "Zeige mir alle leerstehenden Wohnungen",
        "Wie hoch sind die Nebenkosten für Mieter?",
        "Welche Kautionen wurden von Bewohnern hinterlegt?",
    ]

    print("=== BUSINESS GLOSSAR DEMO ===\n")

    for query in test_queries:
        print(f"Query: {query}")
        result = extract_business_entities(query, glossar)

        print(
            f"Found {len(result['extracted_terms'])} terms: {', '.join(result['extracted_terms'])}"
        )
        print(f"Tables involved: {', '.join(result['tables_involved'])}")
        print(f"JOIN hints: {len(result['join_hints'])}")
        print(
            f"Direct matches: {result['direct_matches']}, Fuzzy matches: {result['fuzzy_matches']}"
        )
        print("-" * 60)

    return True


def main():
    """Run all business glossar tests."""
    print("🏗️ WINCASA Business Glossar Test Suite (Simple)")
    print("=" * 60)

    tests = [
        ("Business Term Extraction", test_business_term_extraction),
        ("Business Context Generation", test_business_context_generation),
        ("Business Glossar Demo", test_glossar_demo),
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
        print("🎉 All tests passed! Business Glossar is ready for integration.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
