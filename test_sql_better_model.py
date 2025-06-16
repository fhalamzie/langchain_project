#!/usr/bin/env python3
"""Test SQL with better model"""
import sys
import os
sys.path.append('src')

# Force SQL mode and better model
os.environ['SYSTEM_MODE'] = 'sql_standard'
os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'  # Better model

from wincasa.core.llm_handler import WincasaLLMHandler

def test_sql_generation():
    print("=== Testing SQL Generation with gpt-4o-mini ===\n")
    
    # Create handler (will use new model)
    handler = WincasaLLMHandler()
    
    test_queries = [
        "Liste alle Eigentümer mit Namen Schmidt",
        "Zeige mir alle aktiven Mieter in der Marienstraße",
        "Welche Eigentümer haben Objekte in Essen?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        try:
            result = handler.query_llm(
                user_query=query,
                mode="SQL_VANILLA"
            )
            
            if result.get('sql'):
                print(f"Generated SQL:\n{result['sql']}")
                
            if result.get('answer'):
                preview = result['answer'][:200]
                if 'Fehler' in preview:
                    print(f"\nError in execution: {preview}")
                else:
                    print(f"\nSuccess! Answer preview: {preview}...")
                    
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_sql_generation()