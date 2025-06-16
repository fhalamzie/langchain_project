#!/usr/bin/env python3
"""Trace the actual system prompt sent to LLM - fixed version"""
import sys
import os
import json
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'
os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'

# Intercept at a different level
import logging

# Create a custom handler to capture API calls
class CaptureHandler(logging.Handler):
    def emit(self, record):
        if "Sende Anfrage an OpenAI API" in record.getMessage():
            # Next call will have the details
            pass
        elif "User Query Length:" in record.getMessage():
            # This is where we can see the query
            pass

# Add debug logging
logging.basicConfig(level=logging.DEBUG)

from wincasa.core.llm_handler import WincasaLLMHandler

# Monkey patch to see the system prompt
original_load = WincasaLLMHandler._load_system_prompt_for_mode

def patched_load(self, mode):
    prompt = original_load(self, mode)
    print("\n=== LOADED SYSTEM PROMPT ===")
    print(f"Mode: {mode}")
    print(f"Length: {len(prompt)} chars")
    print("Content preview:")
    print("-" * 50)
    print(prompt[:1000])
    if len(prompt) > 1000:
        print(f"... (truncated)")
    print("-" * 50)
    return prompt

WincasaLLMHandler._load_system_prompt_for_mode = patched_load

def test_trace():
    handler = WincasaLLMHandler()
    
    query = "Liste alle Eigentümer mit Namen Schmidt"
    
    try:
        result = handler.query_llm(
            user_query=query,
            mode="SQL_VANILLA"
        )
        
        print("\n=== RESULT ===")
        if result.get('sql'):
            print(f"Generated SQL: {result['sql']}")
        if result.get('answer'):
            print(f"Answer: {result['answer'][:200]}...")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trace()