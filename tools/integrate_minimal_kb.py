#!/usr/bin/env python3
"""
Update knowledge base loader to use minimal KB.
"""

import json
from pathlib import Path

def update_knowledge_base_loader():
    """Update the knowledge base loader configuration"""
    
    kb_loader_path = Path("src/wincasa/knowledge/knowledge_base_loader.py")
    
    # Read current loader
    content = kb_loader_path.read_text()
    
    # Update path to minimal KB
    old_path = 'alias_map.json'
    new_path = 'minimal_knowledge_base.json'
    
    if old_path in content:
        content = content.replace(old_path, new_path)
        kb_loader_path.write_text(content)
        print(f"Updated {kb_loader_path} to use minimal KB")
    else:
        print("Knowledge base loader already updated or has different structure")

if __name__ == "__main__":
    update_knowledge_base_loader()
