#!/usr/bin/env python3
"""
Quick test to verify the fixes for LangChain and Guided Agent modes.
"""

import sys
import traceback
sys.path.append('.')

from gemini_llm import get_gemini_llm
from filtered_langchain_retriever import FilteredLangChainSQLRetriever

def test_fixes():
    """Test the two problematic modes."""
    print("🔧 Testing fixes for LangChain and Guided Agent modes")
    print("=" * 60)
    
    llm = get_gemini_llm()
    query = 'Wer wohnt in der Marienstraße 26?'
    
    print('\n1. Testing LangChain mode...')
    try:
        retriever = FilteredLangChainSQLRetriever(
            db_connection_string='firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB',
            llm=llm
        )
        docs = retriever.retrieve_documents(query, max_docs=4)
        print(f'✅ LangChain: SUCCESS - {len(docs)} docs retrieved')
        if docs:
            print(f"   First doc: {docs[0].page_content[:100]}...")
    except Exception as e:
        print(f'❌ LangChain: ERROR - {e}')
        print(f"   Traceback: {traceback.format_exc()}")

    print('\n2. Testing Guided Agent...')
    try:
        from guided_agent_retriever import run_guided_agent
        answer = run_guided_agent(
            query, 
            db_connection_string='firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB', 
            llm=llm
        )
        print(f'✅ Guided Agent: SUCCESS - {len(answer)} chars returned')
        print(f"   Answer preview: {answer[:100]}...")
    except Exception as e:
        print(f'❌ Guided Agent: ERROR - {e}')
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_fixes()
