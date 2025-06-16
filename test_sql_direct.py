#!/usr/bin/env python3
"""Direct SQL mode test with updated prompts"""
import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'

from wincasa.core.llm_handler import WincasaLLMHandler

def test_direct_sql():
    print("=== Testing Direct SQL Mode ===\n")
    
    # Create handler
    handler = WincasaLLMHandler()
    
    # Test query
    query = "Liste alle Eigentümer mit Namen Schmidt"
    
    print(f"Query: {query}")
    print("Mode: SQL_VANILLA\n")
    
    try:
        # Call LLM with SQL mode
        result = handler.query_llm(
            user_query=query,
            mode="SQL_VANILLA"
        )
        
        print("LLM Response:")
        print("-" * 50)
        print(f"Success: {result.get('success', False)}")
        print(f"Mode: {result.get('mode', 'unknown')}")
        
        if result.get('sql'):
            print(f"\nGenerated SQL:\n{result['sql']}")
        
        if result.get('answer'):
            print(f"\nAnswer Preview: {result['answer'][:200]}...")
            
        if result.get('error'):
            print(f"\nError: {result['error']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_sql()