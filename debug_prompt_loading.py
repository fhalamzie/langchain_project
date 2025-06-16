#!/usr/bin/env python3
"""Debug prompt loading"""
import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'

from pathlib import Path

def debug_prompt_loading():
    """Debug which prompt file is loaded"""
    
    mode = 'SQL_VANILLA'
    base_path = Path('src/wincasa/utils')
    
    # Check for Enhanced Layer 4 prompts first
    prompt_files = {
        'json_standard': base_path / 'VERSION_A_JSON_LAYER4_ENHANCED.md',
        'json_vanilla': base_path / 'VERSION_A_JSON_LAYER4_VANILLA.md',
        'sql_standard': base_path / 'VERSION_B_SQL_LAYER4_ENHANCED.md',
        'sql_vanilla': base_path / 'VERSION_B_SQL_LAYER4_VANILLA.md'
    }
    
    # Fallback to standard Layer 4 prompts
    layer4_fallback = {
        'json_standard': base_path / 'VERSION_A_JSON_LAYER4.md',
        'json_vanilla': base_path / 'VERSION_A_JSON_LAYER4_VANILLA.md',
        'sql_standard': base_path / 'VERSION_B_SQL_LAYER4.md',
        'sql_vanilla': base_path / 'VERSION_B_SQL_LAYER4_VANILLA.md'
    }
    
    # Fallback to Layer 2 prompts
    layer2_prompts = {
        'json_standard': base_path / 'VERSION_A_JSON_SYSTEM.md',
        'json_vanilla': base_path / 'VERSION_A_JSON_VANILLA.md',
        'sql_standard': base_path / 'VERSION_B_SQL_SYSTEM.md',
        'sql_vanilla': base_path / 'VERSION_B_SQL_VANILLA.md'
    }
    
    # Check lowercase mode
    mode_lower = mode.lower()
    
    print(f"Mode: {mode}")
    print(f"Mode lower: {mode_lower}")
    print(f"Mode in prompt_files: {mode_lower in prompt_files}")
    print(f"Mode in layer4_fallback: {mode_lower in layer4_fallback}")
    print(f"Mode in layer2_prompts: {mode_lower in layer2_prompts}")
    
    # Try to find the file
    if mode_lower in prompt_files and prompt_files[mode_lower].exists():
        print(f"\nWould load Enhanced Layer 4: {prompt_files[mode_lower]}")
    elif mode_lower in layer4_fallback and layer4_fallback[mode_lower].exists():
        print(f"\nWould load Layer 4: {layer4_fallback[mode_lower]}")
    elif mode_lower in layer2_prompts and layer2_prompts[mode_lower].exists():
        print(f"\nWould load Layer 2: {layer2_prompts[mode_lower]}")
        # Load and preview
        with open(layer2_prompts[mode_lower], 'r') as f:
            content = f.read()
            print(f"\nContent preview:\n{content[:500]}...")
    else:
        print("\nWould use fallback prompt!")

if __name__ == "__main__":
    debug_prompt_loading()