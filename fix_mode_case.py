#!/usr/bin/env python3
"""Fix mode case sensitivity in LLM handler"""

from pathlib import Path

def fix_mode_case():
    handler_path = Path("src/wincasa/core/llm_handler.py")
    
    with open(handler_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the _load_system_prompt_for_mode method to handle uppercase modes
    old_line = "        if mode not in prompt_files:"
    new_line = "        mode_lower = mode.lower()\n        if mode_lower not in prompt_files:"
    
    content = content.replace(old_line, new_line)
    
    # Replace all occurrences of mode with mode_lower in that method
    content = content.replace("prompt_files[mode]", "prompt_files[mode_lower]")
    content = content.replace("layer4_fallback[mode]", "layer4_fallback[mode_lower]")
    content = content.replace("layer2_prompts[mode]", "layer2_prompts[mode_lower]")
    content = content.replace("mode in layer4_fallback", "mode_lower in layer4_fallback")
    content = content.replace("mode in layer2_prompts", "mode_lower in layer2_prompts")
    
    with open(handler_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed mode case sensitivity in {handler_path}")

if __name__ == "__main__":
    fix_mode_case()