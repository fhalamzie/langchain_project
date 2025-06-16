#!/usr/bin/env python3
"""
Fix LLM handler to not add confusing knowledge base context for SQL mode
"""

from pathlib import Path

def fix_llm_handler():
    """Update LLM handler to skip knowledge base context for SQL modes"""
    
    handler_path = Path("src/wincasa/core/llm_handler.py")
    
    with open(handler_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _load_system_prompt_for_mode method and modify it
    # We need to skip knowledge base context for SQL modes
    
    # Find the line that adds knowledge base context
    old_code = """                # Add knowledge base context
                knowledge_context = self._get_knowledge_base_context()
                if knowledge_context:
                    base_content += f"\\n\\n{knowledge_context}"
                
                # Schema information is now provided by knowledge base context"""
    
    new_code = """                # Add knowledge base context (skip for SQL modes to avoid confusion)
                if not mode.lower().startswith('sql_'):
                    knowledge_context = self._get_knowledge_base_context()
                    if knowledge_context:
                        base_content += f"\\n\\n{knowledge_context}"
                
                # Schema information is now provided by knowledge base context"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(handler_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {handler_path}")
        print("Knowledge base context will now be skipped for SQL modes")
    else:
        print("Could not find the code to replace. Checking current content...")
        
        # Let's search for the method
        import re
        match = re.search(r'knowledge_context = self\._get_knowledge_base_context\(\).*?Schema information', content, re.DOTALL)
        if match:
            print(f"Found at position {match.start()}-{match.end()}")
            print("Current code:")
            print(match.group(0))

if __name__ == "__main__":
    fix_llm_handler()