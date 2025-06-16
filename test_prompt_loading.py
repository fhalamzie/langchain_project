#!/usr/bin/env python3
"""Test if system prompts are loaded correctly"""
import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'

from wincasa.core.llm_handler import WincasaLLMHandler

def test_prompt_loading():
    print("=== Testing Prompt Loading ===\n")
    
    # Create handler
    handler = WincasaLLMHandler()
    
    # Check loaded prompt
    print("System Prompt Preview:")
    print("-" * 50)
    print(handler.system_prompt[:500] + "...")
    print("-" * 50)
    
    # Check if it contains critical table names
    critical_checks = [
        ("EIGADR", "EIGADR table name"),
        ("BEWOHNER", "BEWOHNER table name"),
        ("NEVER use 'Eigentümer'", "Warning about German names"),
        ("EXACT table names", "Enforcement message")
    ]
    
    print("\nCritical Content Checks:")
    for check, desc in critical_checks:
        if check in handler.system_prompt:
            print(f"✓ Found: {desc}")
        else:
            print(f"✗ Missing: {desc}")

if __name__ == "__main__":
    test_prompt_loading()