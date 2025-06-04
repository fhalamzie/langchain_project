#!/usr/bin/env python3
"""
Test LangChain SQL retriever with real database
"""

import sys
import traceback

def test_langchain_with_real_db():
    """Test LangChain SQL retriever with real WINCASA database"""
    print("🧪 Testing LangChain SQL Retriever with Real Database...")
    
    try:
        from llm_interface import LLMInterface
        from langchain_sql_retriever_fixed import LangChainSQLRetriever
        
        # Create LLM interface
        print("1. Creating LLM interface...")
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        
        # Real database connection string (embedded format)
        db_connection = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
        
        print("2. Creating LangChain SQL retriever with real database...")
        retriever = LangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=False  # Disable monitoring to focus on core functionality
        )
        
        print("3. Testing simple database query...")
        # Test with a simple query
        query = "Wie viele Wohnungen gibt es insgesamt?"
        docs = retriever.retrieve_documents(query, max_docs=3)
        
        print(f"4. Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs):
            print(f"   Document {i+1}:")
            print(f"     Source: {doc.metadata.get('source', 'unknown')}")
            print(f"     Success: {doc.metadata.get('success', 'unknown')}")
            print(f"     Content preview: {doc.page_content[:100]}...")
            if doc.metadata.get('error'):
                print(f"     Error: {doc.metadata.get('error')}")
        
        print("\n5. Getting retriever info...")
        info = retriever.get_retriever_info()
        print(f"   Mode: {info['mode']}")
        print(f"   Type: {info['type']}")
        print(f"   Tables available: {info['tables_available']}")
        print(f"   Status: {info.get('status', 'active')}")
        
        # Check if any document shows success
        success_docs = [doc for doc in docs if doc.metadata.get('success')]
        if success_docs:
            print("✅ LangChain SQL retriever working with real database!")
            return True
        else:
            print("⚠️ LangChain SQL retriever created but queries failed")
            return False
        
    except Exception as e:
        print(f"❌ LangChain real database test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔍 WINCASA LangChain Real Database Test")
    print("=" * 60)
    
    success = test_langchain_with_real_db()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n🎉 LangChain integration is fully functional!")
        sys.exit(0)
    else:
        print("\n🔧 LangChain integration needs more work.")
        sys.exit(1)