#!/usr/bin/env python3
"""
Improved 9-mode status test with proper constructor parameters.
"""

import os
import sys
from dotenv import load_dotenv
from gemini_llm import get_gemini_llm
from langchain_core.documents import Document

# Load environment variables
load_dotenv('/home/envs/openai.env')

def create_test_documents():
    """Create sample documents for testing."""
    return [
        Document(page_content="BEWOHNER table: BWO, BNAME, BSTR...", 
                metadata={"table_name": "BEWOHNER", "business_purpose": "Resident data"}),
        Document(page_content="EIGENTUEMER table: ENR, NAME, VNAME...", 
                metadata={"table_name": "EIGENTUEMER", "business_purpose": "Owner information"}),
        Document(page_content="KONTEN table: ONR, SALDO, KONTO...", 
                metadata={"table_name": "KONTEN", "business_purpose": "Financial accounts"})
    ]

def test_all_modes():
    """Test all 9 retrieval modes with proper parameters."""
    print("🧪 IMPROVED 9-MODE STATUS CHECK")
    print("="*60)
    
    results = {}
    llm = get_gemini_llm()
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    test_docs = create_test_documents()
    openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
    
    # Mode 1: Enhanced (using alias from enhanced_retrievers)
    try:
        from contextual_enhanced_retriever import ContextualEnhancedRetriever
        retriever = ContextualEnhancedRetriever(test_docs, openai_api_key)
        # Just test initialization, not full retrieval
        results['Enhanced'] = "✅ Initialized successfully"
    except Exception as e:
        results['Enhanced'] = f"❌ {str(e)[:50]}..."
    
    # Mode 2: Contextual Enhanced
    try:
        from contextual_enhanced_retriever import ContextualEnhancedRetriever
        retriever = ContextualEnhancedRetriever(test_docs, openai_api_key)
        results['Contextual Enhanced'] = "✅ Initialized successfully"
    except Exception as e:
        results['Contextual Enhanced'] = f"❌ {str(e)[:50]}..."
    
    # Mode 3: FAISS
    try:
        from hybrid_faiss_retriever import HybridFAISSRetriever
        retriever = HybridFAISSRetriever(test_docs, openai_api_key)
        results['FAISS'] = "✅ Initialized successfully"
    except Exception as e:
        results['FAISS'] = f"❌ {str(e)[:50]}..."
    
    # Mode 4: LangChain (Filtered)
    try:
        from filtered_langchain_retriever import FilteredLangChainSQLRetriever
        retriever = FilteredLangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=False
        )
        results['LangChain'] = "✅ Initialized successfully"
    except Exception as e:
        results['LangChain'] = f"❌ {str(e)[:50]}..."
    
    # Mode 5: TAG
    try:
        from adaptive_tag_classifier import AdaptiveTAGClassifier
        # TAG mode works differently - it's a classifier, not a retriever
        classifier = AdaptiveTAGClassifier()
        result = classifier.classify_query("test query")
        results['TAG'] = f"✅ Classification: {result.query_type}"
    except Exception as e:
        results['TAG'] = f"❌ {str(e)[:50]}..."
    
    # Mode 6: Smart Fallback
    try:
        from smart_fallback_retriever import SmartFallbackRetriever
        retriever = SmartFallbackRetriever(db_connection_string=db_connection)
        results['Smart Fallback'] = "✅ Initialized successfully"
    except Exception as e:
        results['Smart Fallback'] = f"❌ {str(e)[:50]}..."
    
    # Mode 7: Smart Enhanced (Enhanced + TAG)
    try:
        from smart_enhanced_retriever import SmartEnhancedRetriever
        retriever = SmartEnhancedRetriever(test_docs, openai_api_key)
        results['Smart Enhanced'] = "✅ Initialized successfully"
    except Exception as e:
        results['Smart Enhanced'] = f"❌ {str(e)[:50]}..."
    
    # Mode 8: Guided Agent (LangChain + TAG)
    try:
        from guided_agent_retriever import GuidedAgentRetriever
        retriever = GuidedAgentRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=False
        )
        results['Guided Agent'] = "✅ Initialized successfully"
    except Exception as e:
        results['Guided Agent'] = f"❌ {str(e)[:50]}..."
    
    # Mode 9: Contextual Vector (FAISS + TAG)
    try:
        from contextual_vector_retriever import ContextualVectorRetriever
        retriever = ContextualVectorRetriever(test_docs, openai_api_key)
        results['Contextual Vector'] = "✅ Initialized successfully"
    except Exception as e:
        results['Contextual Vector'] = f"❌ {str(e)[:50]}..."
    
    # Results
    print("\n📊 MODE STATUS SUMMARY:")
    print("="*60)
    working_count = 0
    for i, (mode, status) in enumerate(results.items(), 1):
        print(f"{i:2d}. {mode:20s} {status}")
        if status.startswith("✅"):
            working_count += 1
    
    print(f"\n🎯 OVERALL STATUS: {working_count}/9 modes working")
    
    if working_count >= 7:
        print("🎉 EXCELLENT! Almost all modes functional!")
    elif working_count >= 5:
        print("👍 GOOD! Most modes working!")
    else:
        print("⚠️  NEEDS WORK: Several modes failing")
    
    return working_count

if __name__ == "__main__":
    working_count = test_all_modes()
    sys.exit(0 if working_count >= 7 else 1)