#!/usr/bin/env python3
"""Trace the actual system prompt sent to LLM"""
import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'
os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'

# Monkey patch to capture the actual prompt
import openai
original_create = None

def capture_create(**kwargs):
    """Capture and print the actual request"""
    messages = kwargs.get('messages', [])
    
    print("=== ACTUAL LLM REQUEST ===")
    print(f"Model: {kwargs.get('model')}")
    print(f"Temperature: {kwargs.get('temperature')}")
    
    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1} ({msg['role']}) ---")
        print(msg['content'][:1000])
        if len(msg['content']) > 1000:
            print(f"... (truncated, total length: {len(msg['content'])})")
    
    # Call original
    return original_create(**kwargs)

# Apply patch
if hasattr(openai.resources.chat.completions, 'Completions'):
    original_create = openai.resources.chat.completions.Completions.create
    openai.resources.chat.completions.Completions.create = capture_create

from wincasa.core.llm_handler import WincasaLLMHandler

def test_trace():
    handler = WincasaLLMHandler()
    
    query = "Liste alle Eigentümer mit Namen Schmidt"
    
    try:
        result = handler.query_llm(
            user_query=query,
            mode="SQL_VANILLA"
        )
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_trace()