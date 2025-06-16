#!/usr/bin/env python3
"""Debug SQL generation to see what's happening"""
import sys
import os
import json
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'
os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'

import openai
from wincasa.utils.config_loader import WincasaConfig

def test_direct_llm_call():
    """Test LLM directly to see SQL generation"""
    print("=== Direct LLM SQL Generation Test ===\n")
    
    # Load config and prompt
    config = WincasaConfig()
    llm_config = config.get_llm_config()
    system_prompt = config.load_system_prompt()
    
    print("System Prompt Preview:")
    print("-" * 50)
    print(system_prompt[:500] + "...")
    print("-" * 50)
    
    # Test query
    user_query = "Liste alle Eigentümer mit Namen Schmidt"
    
    # Define function for SQL execution
    functions = [
        {
            "name": "execute_sql_query",
            "description": "Executes a SQL query against the WINCASA Firebird database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL SELECT query to execute"},
                    "query_type": {"type": "string", "description": "Type of query for result formatting"}
                },
                "required": ["sql"]
            }
        }
    ]
    
    # Call OpenAI
    client = openai.OpenAI(api_key=llm_config['api_key'])
    
    print(f"\nCalling LLM with query: {user_query}")
    print(f"Model: {llm_config['model']}")
    
    try:
        response = client.chat.completions.create(
            model=llm_config['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            functions=functions,
            function_call="auto",
            temperature=0.1,
            max_tokens=1000
        )
        
        message = response.choices[0].message
        
        if message.function_call:
            print(f"\nFunction called: {message.function_call.name}")
            args = json.loads(message.function_call.arguments)
            print(f"Arguments:")
            print(json.dumps(args, indent=2))
            
            if 'sql' in args:
                print(f"\nGenerated SQL:")
                print(args['sql'])
        else:
            print(f"\nText response: {message.content}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_llm_call()