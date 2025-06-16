#!/usr/bin/env python3
"""Debug mode case sensitivity"""

mode = "SQL_VANILLA"

# From llm_handler.py
prompt_files = {
    'json_standard': 'file1',
    'json_vanilla': 'file2', 
    'sql_standard': 'file3',
    'sql_vanilla': 'file4'
}

print(f"Mode: {mode}")
print(f"Mode in dict: {mode in prompt_files}")
print(f"Mode lowercase: {mode.lower()}")
print(f"Mode lowercase in dict: {mode.lower() in prompt_files}")