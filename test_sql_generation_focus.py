#!/usr/bin/env python3
"""
Focused test for SQL generation issues
"""

import sys
import os
sys.path.append('src')

from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.utils.config_loader import WincasaConfig

def test_sql_generation():
    """Test SQL generation with specific queries"""
    
    config = WincasaConfig()
    
    # Test queries that should generate SQL
    test_queries = [
        "Zeige alle Mieter",
        "Liste aller Eigentümer",
        "Summe der Kaltmiete",
        "Finde Leerstand",
        "Wer wohnt in Marienstraße 26",
        "Zeige alle Objekte in Essen"
    ]
    
    # Test with SQL mode
    llm_handler = WincasaLLMHandler()
    
    print("Testing SQL generation with SQL_SYSTEM mode:\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        try:
            result = llm_handler.query_llm(query, mode="SQL_SYSTEM")
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"Answer preview: {result.get('answer', '')[:200]}...")
                print(f"Result count: {result.get('result_count', 0)}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_sql_generation()