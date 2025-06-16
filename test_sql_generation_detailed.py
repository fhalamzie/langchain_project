#!/usr/bin/env python3
"""
Detailed SQL generation test with query inspection
"""

import sys
import os
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

sys.path.append('src')

from wincasa.core.llm_handler import WincasaLLMHandler

def test_sql_generation_detailed():
    """Test SQL generation with detailed output"""
    
    # Test queries
    test_queries = [
        ("Liste alle Eigentümer", "Should use EIGADR table"),
        ("Zeige alle Mieter", "Should use BEWOHNER table"),
        ("Summe der Kaltmiete", "Should use BEWOHNER.Z1 field"),
        ("Finde Leerstand", "Should find vacant units"),
    ]
    
    llm_handler = WincasaLLMHandler()
    
    print("Testing SQL generation with SQL_SYSTEM mode:\n")
    
    for query, expected in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        print(f"{'='*60}")
        
        try:
            result = llm_handler.query_llm(query, mode="SQL_SYSTEM")
            
            print(f"\nSuccess: {result.get('success', False)}")
            
            if result.get('success'):
                answer = result.get('answer', '')
                print(f"\nFull Answer:\n{answer}")
                
                # Look for SQL in the answer
                if 'SQL' in answer or 'SELECT' in answer:
                    print("\n*** SQL FOUND IN ANSWER ***")
                
            else:
                print(f"\nError: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"\nException: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_sql_generation_detailed()