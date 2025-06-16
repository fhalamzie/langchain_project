#!/usr/bin/env python3
"""
Test script to validate schema fixes work correctly.
Tests critical queries that were failing before.
"""

import requests
import json
from pathlib import Path

# Test queries that were failing
TEST_QUERIES = [
    {
        "query": "Zeige alle Eigentümer",
        "expected_tables": ["EIGADR"],
        "expected_fields": ["EIGNR", "ENAME", "EVNAME"],
        "should_not_contain": ["OWNERS", "NAME"]
    },
    {
        "query": "Liste aller aktiven Mieter",
        "expected_tables": ["BEWOHNER"],
        "expected_fields": ["BNAME", "BVNAME", "BSTR", "BPLZORT"],
        "should_not_contain": ["TENANTS", "BEWNAME", "STRASSE", "STADT", "EIGNR"]
    },
    {
        "query": "Summe der Kaltmiete",
        "expected_tables": ["BEWOHNER"],
        "expected_fields": ["Z1"],
        "should_not_contain": ["KALTMIETE", "KBETRAG"]
    },
    {
        "query": "Finde Leerstand",
        "expected_tables": ["WOHNUNG", "BEWOHNER"],
        "expected_pattern": "LEFT JOIN",
        "should_not_contain": ["EIGNR = -1", "BEWOHNER.EIGNR"]
    },
    {
        "query": "Wer wohnt in der Marienstr. 26",
        "expected_tables": ["BEWOHNER", "OBJEKTE"],
        "expected_fields": ["BNAME", "OSTRASSE"],
        "should_not_contain": ["STRASSE"]
    }
]

def test_query(query_info, mode="sql_vanilla", model="gpt-4o-mini"):
    """Test a single query"""
    print(f"\nTesting: {query_info['query']}")
    print(f"Mode: {mode}, Model: {model}")
    
    # Call the API
    url = "http://localhost:8669/query"
    payload = {
        "query": query_info["query"],
        "mode": mode,
        "model": model
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get("success"):
            answer = result.get("answer", "")
            
            # Check for expected content
            issues = []
            
            # Check expected tables
            for table in query_info.get("expected_tables", []):
                if table not in answer.upper():
                    issues.append(f"Missing expected table: {table}")
            
            # Check expected fields
            for field in query_info.get("expected_fields", []):
                if field not in answer.upper():
                    issues.append(f"Missing expected field: {field}")
            
            # Check for wrong content
            for wrong in query_info.get("should_not_contain", []):
                if wrong in answer.upper():
                    issues.append(f"Contains wrong term: {wrong}")
            
            # Check patterns
            if "expected_pattern" in query_info:
                if query_info["expected_pattern"] not in answer.upper():
                    issues.append(f"Missing pattern: {query_info['expected_pattern']}")
            
            if issues:
                print("❌ FAILED - Issues found:")
                for issue in issues:
                    print(f"   - {issue}")
                print(f"\nGenerated SQL:\n{answer[:500]}...")
            else:
                print("✅ PASSED - Query looks correct")
                
            return len(issues) == 0
        else:
            print(f"❌ FAILED - API error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED - Request error: {e}")
        return False

def run_all_tests():
    """Run all test queries"""
    print("=" * 60)
    print("WINCASA Schema Fix Validation")
    print("=" * 60)
    
    # Test SQL modes
    sql_modes = ["sql_vanilla", "sql_standard"]
    models = ["gpt-4o-mini"]
    
    results = {"passed": 0, "failed": 0}
    
    for mode in sql_modes:
        print(f"\n{'='*60}")
        print(f"Testing mode: {mode}")
        print(f"{'='*60}")
        
        for query_info in TEST_QUERIES:
            for model in models:
                if test_query(query_info, mode, model):
                    results["passed"] += 1
                else:
                    results["failed"] += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
    
    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! Schema fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Further investigation needed.")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://localhost:8669/", timeout=5)
        print("✅ Server is running on port 8669")
    except:
        print("❌ Server not running on port 8669. Start with:")
        print("   cd htmx && python3 server.py")
        exit(1)
    
    run_all_tests()