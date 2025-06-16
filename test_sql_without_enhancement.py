#!/usr/bin/env python3
"""Test SQL without knowledge base enhancement"""
import sys
import os
sys.path.append('src')

# Force SQL mode
os.environ['SYSTEM_MODE'] = 'sql_standard'
os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'

# Monkey patch to disable knowledge enhancement
import wincasa.core.llm_handler
original_query_llm = wincasa.core.llm_handler.WincasaLLMHandler.query_llm

def patched_query_llm(self, user_query, mode=None):
    # Temporarily disable knowledge enhancement
    old_enhance = None
    try:
        from wincasa.knowledge.knowledge_base_loader import KnowledgeBaseLoader
        old_enhance = KnowledgeBaseLoader.enhance_prompt_with_knowledge
        KnowledgeBaseLoader.enhance_prompt_with_knowledge = lambda self, q: ""
    except:
        pass
    
    result = original_query_llm(self, user_query, mode)
    
    # Restore
    if old_enhance:
        KnowledgeBaseLoader.enhance_prompt_with_knowledge = old_enhance
        
    return result

wincasa.core.llm_handler.WincasaLLMHandler.query_llm = patched_query_llm

from wincasa.core.llm_handler import WincasaLLMHandler

def test_sql_clean():
    print("=== Testing SQL without Knowledge Enhancement ===\n")
    
    handler = WincasaLLMHandler()
    
    query = "Liste alle Eigentümer mit Namen Schmidt"
    
    print(f"Query: {query}")
    
    try:
        result = handler.query_llm(
            user_query=query,
            mode="SQL_VANILLA"
        )
        
        if result.get('sql'):
            print(f"\nGenerated SQL:\n{result['sql']}")
            
        if result.get('answer'):
            preview = result['answer'][:300]
            print(f"\nResult: {preview}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_clean()