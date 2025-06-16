#!/usr/bin/env python3
"""
Final test to verify that LLM uses correct tables and fields
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from wincasa.core.wincasa_query_engine import WincasaQueryEngine

def test_queries():
    """Test various queries to check if correct tables/fields are used"""
    
    engine = WincasaQueryEngine()
    
    test_cases = [
        {
            'query': 'Zeige alle Mieter mit Namen Müller',
            'mode': 'sql_standard',
            'description': 'Test natural language query for tenants'
        },
        {
            'query': 'Liste alle Eigentümer', 
            'mode': 'sql_standard',
            'description': 'Test owner query - should use EIGADR not OWNERS'
        },
        {
            'query': 'Summe aller Kaltmieten',
            'mode': 'sql_standard',
            'description': 'Test sum query - should use Z1 not KALTMIETE'
        },
        {
            'query': 'Mieter der Marienstr. 26',
            'mode': 'sql_standard',
            'description': 'Test address query - should use BSTR not STRASSE'
        }
    ]
    
    print("Testing SQL generation with new system prompts...")
    print("="*80 + "\n")
    
    for test in test_cases:
        print(f"Test: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Mode: {test['mode']}")
        
        try:
            # Execute query using query engine
            result = engine.process_query(test['query'], test['mode'])
            
            # QueryEngineResult object
            answer = result.answer
            print(f"Mode: {result.processing_mode}")
            print(f"Confidence: {result.confidence}")
            
            if answer:
                
                # For SQL modes, check the generated SQL
                if 'sql' in test['mode']:
                    # Look for SQL queries in the answer
                    if 'SELECT' in answer.upper():
                        print("\nGenerated SQL found:")
                        # Extract SQL part
                        sql_start = answer.upper().find('SELECT')
                        sql_end = answer.find('\n', sql_start+100) if '\n' in answer[sql_start+100:] else len(answer)
                        sql = answer[sql_start:sql_end]
                        print(f"SQL: {sql[:300]}...")
                        
                        # Check for correct/wrong tables
                        sql_upper = sql.upper()
                        
                        # Correct tables/fields
                        if 'BEWOHNER' in sql_upper:
                            print("✅ Using correct BEWOHNER table")
                        if 'BEWADR' in sql_upper:
                            print("✅ Using correct BEWADR table")
                        if 'EIGADR' in sql_upper:
                            print("✅ Using correct EIGADR table")
                        if 'Z1' in sql_upper:
                            print("✅ Using correct Z1 field for Kaltmiete")
                        if 'BSTR' in sql_upper:
                            print("✅ Using correct BSTR field for street")
                        if 'BNAME' in sql_upper:
                            print("✅ Using correct BNAME field for name")
                            
                        # Wrong tables/fields
                        if 'OWNERS' in sql_upper:
                            print("❌ ERROR: Using wrong OWNERS table!")
                        if 'STRASSE' in sql_upper and 'OSTRASSE' not in sql_upper and 'BSTR' not in sql_upper:
                            print("❌ ERROR: Using wrong STRASSE field!")
                        if 'KALTMIETE' in sql_upper:
                            print("❌ ERROR: Using wrong KALTMIETE field!")
                        if 'STADT' in sql_upper:
                            print("❌ ERROR: Using wrong STADT field!")
                        if 'BEWNAME' in sql_upper:
                            print("❌ ERROR: Using wrong BEWNAME field!")
                    else:
                        print("\nNo SQL found in answer")
                        print(f"Answer preview: {answer[:200]}...")
                else:
                    print(f"\nAnswer preview: {answer[:200]}...")
            else:
                print(f"No answer returned")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        print("-" * 80 + "\n")

if __name__ == "__main__":
    test_queries()