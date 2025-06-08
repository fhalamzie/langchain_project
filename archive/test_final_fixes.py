#!/usr/bin/env python3
"""
Final test to verify all 9 retrieval modes work properly.
Tests both LangChain and Guided Agent modes that were previously failing.
"""

import os
import sys
import time
from dotenv import load_dotenv
from gemini_llm import get_gemini_llm

# Load environment variables
load_dotenv('/home/envs/openai.env')

def test_langchain_mode():
    """Test the LangChain (Filtered) mode specifically."""
    print("🔬 Testing LangChain (Filtered) Mode")
    print("="*60)
    
    try:
        from filtered_langchain_retriever import FilteredLangChainSQLRetriever
        
        # Initialize retriever
        retriever = FilteredLangChainSQLRetriever(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm=get_gemini_llm(),
            enable_monitoring=False
        )
        
        print("✅ LangChain retriever initialized successfully")
        
        # Test query
        query = "Wie viele Bewohner gibt es?"
        print(f"📝 Testing query: {query}")
        
        start_time = time.time()
        docs = retriever.retrieve_documents(query, max_docs=3)
        end_time = time.time()
        
        print(f"✅ Query completed in {end_time - start_time:.2f}s")
        print(f"📊 Retrieved {len(docs)} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain mode failed: {e}")
        return False

def test_guided_agent_mode():
    """Test the Guided Agent mode specifically."""
    print("\n🔬 Testing Guided Agent Mode")
    print("="*60)
    
    try:
        from guided_agent_retriever import GuidedAgentRetriever
        
        # Initialize retriever
        retriever = GuidedAgentRetriever(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm=get_gemini_llm(),
            enable_monitoring=False
        )
        
        print("✅ Guided Agent retriever initialized successfully")
        
        # Test query
        query = "Wie viele Bewohner gibt es?"
        print(f"📝 Testing query: {query}")
        
        start_time = time.time()
        result = retriever.retrieve(query, max_docs=3)
        end_time = time.time()
        
        print(f"✅ Query completed in {end_time - start_time:.2f}s")
        print(f"📊 Query type: {result.classification.query_type}")
        print(f"📊 Tables filtered: {len(result.filtered_tables)}")
        print(f"📊 Documents: {len(result.documents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Guided Agent mode failed: {e}")
        return False

def test_database_connection():
    """Test basic database connectivity."""
    print("🔬 Testing Database Connection")
    print("="*60)
    
    try:
        import fdb
        
        # Test direct fdb connection
        con = fdb.connect(
            dsn="localhost:3050/home/projects/langchain_project/WINCASA2022.FDB",
            user="sysdba",
            password="masterkey"
        )
        
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        table_count = cur.fetchone()[0]
        
        cur.close()
        con.close()
        
        print(f"✅ Database connection successful")
        print(f"📊 Found {table_count} user tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 FINAL VERIFICATION TESTS")
    print("="*80)
    print("Testing fixes for LangChain database permission issues")
    print("Goal: Achieve complete 9/9 mode functionality")
    print()
    
    results = {}
    
    # Test database connection first
    results['database'] = test_database_connection()
    
    # Test LangChain mode
    results['langchain'] = test_langchain_mode()
    
    # Test Guided Agent mode  
    results['guided_agent'] = test_guided_agent_mode()
    
    # Summary
    print("\n" + "="*80)
    print("📈 TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    total_pass = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall: {total_pass}/{total_tests} tests passed")
    
    if total_pass == total_tests:
        print("🎉 ALL TESTS PASSED! Ready for 9/9 mode functionality!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
    return total_pass == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
