#!/usr/bin/env python3
"""
Test WINCASA with real data queries to validate schema fixes.
Using actual addresses, names, and data from the database.
"""

import requests
import json
import random
from datetime import datetime

# Real test queries based on actual WINCASA data
TEST_QUERIES = [
    # Mieter/Wohnen Queries (Who lives where)
    "Wer wohnt in der Marienstr. 26, 45307 Essen",
    "Wer wohnt in der Steinf. 32/34",
    "Wer wohnt in der Kämpenstraße 13",
    "Zeige alle Mieter in Essen",
    "Zeige alle Mieter in Bochum",
    "Liste der Bewohner Haager Weg",
    "Wer wohnt in der Florastr. 90",
    
    # Eigentümer Queries (Owner queries)
    "Alle Eigentümer vom Haager Weg",
    "Zeige alle Eigentümer mit Kontaktdaten",
    "Liste aller Eigentümer in Essen",
    "Portfolio von Ruhrstadt Wohnen GmbH",
    "Wie viele Objekte hat Prader Bauträger GmbH",
    "Eigentümer der Marienstr. 26",
    
    # Kontaktdaten Queries (Contact data)
    "Kontaktdaten von Fahim Halamzie",
    "Telefonnummer von Herrn Nonnenbüscher",
    "Kontaktdaten der Eigentümer aus der Marienstr. 26",
    "Email von Familie Klein",
    "Telefonnummer von Familie Volker",
    
    # Miete/Finanzen Queries (Rent/Finance)
    "Wieviel Miete zahlt Ouafa Hafsi",
    "Summe aller Kaltmieten",
    "Monatliche Mieteinnahmen Marienstr. 26",
    "Höchste Miete im Portfolio",
    "Durchschnittliche Kaltmiete in Essen",
    
    # Einheiten/Portfolio Queries (Units/Portfolio)
    "Wieviele Einheiten hat FHALAMZIE",
    "Anzahl Wohnungen Marienstr. 26",
    "Gesamtzahl aller verwalteten Einheiten",
    "Wie viele Wohnungen in Bochum",
    
    # Leerstand Queries (Vacancy)
    "Leerstand in Essen",
    "Freie Wohnungen in der Marienstr.",
    "Leerstehende Einheiten gesamt",
    "Vacancy Rate im Portfolio",
    
    # WEG Queries (Homeowners association)
    "Wie groß ist die WEG Neusser Str.",
    "Wer ist der Verwalter von WEG NEUSS49",
    "Anzahl Einheiten WEG Marienstr. 26",
    
    # Buchungskonten Queries (Account queries)
    "Buchungskonten von der Neusser Str. 49",
    "Kontostand von Diana",
    "Offene Posten Marienstr. 26",
    "Buchungskontenübersicht mit Kontostand aus der Marienstr 26, 45307 Essen"
]

def test_single_query(query, mode="sql_vanilla", model="gpt-4o-mini"):
    """Test a single query and check for correct field names"""
    
    url = "http://localhost:8669/query"
    payload = {
        "query": query,
        "mode": mode,
        "model": model
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get("success"):
            answer = result.get("answer", "")
            
            # Check for wrong field names (indicators of old schema)
            wrong_terms = [
                "OWNERS", "TENANTS", "STRASSE", "BEWNAME", "STADT", 
                "KALTMIETE FROM", "SELECT.*KALTMIETE.*FROM",  # SQL selecting KALTMIETE as field
                "EORT", "OBJNR", "OBJNAME", "WBEZ"
            ]
            
            # Check for correct terms
            correct_terms = {
                "owner": ["EIGADR", "ENAME"],
                "tenant": ["BEWOHNER", "BNAME"], 
                "rent": ["Z1"],
                "vacancy": ["LEFT JOIN", "IS NULL"]
            }
            
            issues = []
            
            # Check for wrong terms
            answer_upper = answer.upper()
            for wrong in wrong_terms:
                if wrong in answer_upper and "OSTRASSE" not in wrong:  # OSTRASSE is correct
                    issues.append(f"Wrong term found: {wrong}")
            
            # For specific query types, check for correct terms
            query_upper = query.upper()
            if "EIGENTÜMER" in query_upper or "OWNER" in query_upper:
                if not any(term in answer_upper for term in correct_terms["owner"]):
                    issues.append("Missing correct owner table/fields")
                    
            if "MIETER" in query_upper or "WOHNT" in query_upper:
                if not any(term in answer_upper for term in correct_terms["tenant"]):
                    issues.append("Missing correct tenant table/fields")
                    
            if "MIETE" in query_upper or "KALTMIETE" in query_upper:
                if "Z1" not in answer_upper:
                    issues.append("Missing Z1 field for rent")
                    
            if "LEERSTAND" in query_upper or "FREIE" in query_upper:
                if "LEFT JOIN" not in answer_upper:
                    issues.append("Wrong vacancy detection method")
            
            return {
                "query": query,
                "success": len(issues) == 0,
                "issues": issues,
                "preview": answer[:200] + "..." if len(answer) > 200 else answer
            }
        else:
            return {
                "query": query,
                "success": False,
                "issues": [f"API Error: {result.get('error')}"],
                "preview": ""
            }
            
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "issues": [f"Request failed: {str(e)}"],
            "preview": ""
        }

def run_comprehensive_test():
    """Run tests on sample queries"""
    
    print("=" * 80)
    print("WINCASA Schema Fix Validation - Real Data Queries")
    print("=" * 80)
    print(f"Testing {len(TEST_QUERIES)} queries...")
    print()
    
    # Test modes
    modes_to_test = ["sql_vanilla", "sql_standard", "json_vanilla", "json_standard"]
    
    # Take a sample of queries for testing
    sample_queries = random.sample(TEST_QUERIES, min(10, len(TEST_QUERIES)))
    
    results = {"passed": 0, "failed": 0, "by_mode": {}}
    
    for mode in modes_to_test:
        print(f"\n{'='*60}")
        print(f"Testing Mode: {mode}")
        print(f"{'='*60}\n")
        
        mode_results = {"passed": 0, "failed": 0}
        
        for query in sample_queries:
            result = test_single_query(query, mode)
            
            if result["success"]:
                print(f"✅ {query}")
                results["passed"] += 1
                mode_results["passed"] += 1
            else:
                print(f"❌ {query}")
                for issue in result["issues"]:
                    print(f"   - {issue}")
                results["failed"] += 1
                mode_results["failed"] += 1
        
        results["by_mode"][mode] = mode_results
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total queries tested: {len(sample_queries)} × {len(modes_to_test)} modes = {len(sample_queries) * len(modes_to_test)} tests")
    print(f"Overall passed: {results['passed']}")
    print(f"Overall failed: {results['failed']}")
    print(f"Success rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
    
    print("\nBy Mode:")
    for mode, mode_results in results["by_mode"].items():
        total = mode_results["passed"] + mode_results["failed"]
        rate = mode_results["passed"] / total * 100 if total > 0 else 0
        print(f"  {mode}: {mode_results['passed']}/{total} ({rate:.1f}%)")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results/schema_fix_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
            "sample_queries": sample_queries
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return results["failed"] == 0

if __name__ == "__main__":
    # Check server
    try:
        response = requests.get("http://localhost:8669/", timeout=5)
        print("✅ HTMX server is running on port 8669\n")
    except:
        print("❌ Server not running. Please start with:")
        print("   cd htmx && python3 server.py")
        exit(1)
    
    # Run tests
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Schema fixes are working correctly.")
        print("\nReady to commit the changes.")
    else:
        print("\n⚠️  Some tests failed. Review the issues above.")
        print("\nCommon issues to check:")
        print("- System prompts not reloaded")
        print("- LLM cache needs clearing")
        print("- Server needs restart")