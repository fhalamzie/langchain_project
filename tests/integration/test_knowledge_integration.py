#!/usr/bin/env python3
"""
Test Knowledge Base Integration
"""

import logging

from knowledge_base_loader import get_knowledge_base

logging.basicConfig(level=logging.INFO)

def test_knowledge_base():
    kb = get_knowledge_base()
    
    print("=== Knowledge Base Test ===\n")
    
    # Test 1: Check important mappings
    print("1. Important Field Mappings:")
    important_aliases = ["KALTMIETE", "EIGENTUEMERKUERZEL", "MIETER_NAME", "WARMMIETE_AKTUELL"]
    for alias in important_aliases:
        canonical = kb.get_canonical_field(alias)
        if canonical:
            print(f"   {alias} -> {canonical}")
    
    # Test 2: Business term recognition
    print("\n2. Business Term Recognition:")
    test_queries = [
        "Wieviel Kaltmieten erzielt der Eigentümer FHALAMZIE monatlich?",
        "Alle Mieter von der Marienstr. 26",
        "Zeige alle Wohnungen mit Leerstand"
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query}")
        terms = kb.find_business_term(query)
        for term in terms:
            print(f"   - Found: '{term['term']}' -> Table: {term['table']}")
    
    # Test 3: Enhanced context generation
    print("\n3. Enhanced Context Generation:")
    query = "Wieviel Kaltmieten erzielt der Eigentümer FHALAMZIE monatlich?"
    context = kb.enhance_prompt_with_knowledge(query)
    print(f"   Query: {query}")
    print(f"   Generated Context:\n{context}")
    
    # Test 4: SQL Validation
    print("\n4. SQL Field Validation:")
    bad_sql = "SELECT KBETRAG FROM KONTEN WHERE NAME = 'FHALAMZIE'"
    issues = kb.validate_sql_fields(bad_sql)
    print(f"   SQL: {bad_sql}")
    print(f"   Issues found: {issues}")

if __name__ == "__main__":
    test_knowledge_base()