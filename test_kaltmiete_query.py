#!/usr/bin/env python3
"""
Test specific KALTMIETE query with Knowledge Base
"""

import logging
from llm_handler import WincasaLLMHandler

logging.basicConfig(level=logging.INFO)

def test_kaltmiete_query():
    handler = WincasaLLMHandler()
    
    queries = [
        "Wieviel Kaltmieten erzielt der Eigentümer FHALAMZIE monatlich?",
        "Was ist die monatliche Kaltmiete von FHALAMZIE?",
        "Zeige mir die Summe aller Kaltmieten für Eigentümer FHALAMZIE"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        # Test in SQL mode
        result = handler.query_llm(query, mode='sql_vanilla')
        
        if result.get('success'):
            response = result.get('answer', result.get('response', ''))
            print(f"\nResponse Preview:")
            print(response[:500] + '...' if len(response) > 500 else response)
            
            # Check for specific errors
            if 'KBETRAG' in response:
                print("\n⚠️  WARNING: Still using KBETRAG field!")
            elif 'Column unknown' in response:
                print("\n❌ ERROR: Column unknown error detected!")
            elif 'BEWOHNER.Z1' in response or 'B.Z1' in response:
                print("\n✅ SUCCESS: Using correct field BEWOHNER.Z1!")
            else:
                print("\n❓ UNCLEAR: Could not determine field usage")
        else:
            print(f"\n❌ Query failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_kaltmiete_query()