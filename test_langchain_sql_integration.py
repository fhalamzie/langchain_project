#!/usr/bin/env python3
"""
Test LangChain SQL Database Agent Integration

This test validates the implementation of the LangChain SQL Database Agent
as the 5th retrieval mode in the WINCASA system.
"""

import time
import json
import traceback
from pathlib import Path
from datetime import datetime

# Test the LangChain SQL Agent directly first
def test_langchain_retriever_direct():
    """Test the LangChain SQL retriever directly"""
    print("🧪 Testing LangChain SQL Retriever directly...")
    
    try:
        from langchain_sql_agent import LangChainSQLRetriever
        from llm_interface import LLMInterface
        
        # Get LLM instance
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        
        # Initialize retriever
        retriever = LangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=True
        )
        
        # Test simple query
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        print(f"\n📋 Testing query: {test_query}")
        
        start_time = time.time()
        docs = retriever.retrieve_documents(test_query, max_docs=5)
        duration = time.time() - start_time
        
        print(f"⏱️ Query completed in {duration:.2f}s")
        print(f"📄 Retrieved {len(docs)} documents")
        
        for i, doc in enumerate(docs):
            print(f"\n--- Document {i+1} ---")
            print(f"Source: {doc.metadata.get('source', 'unknown')}")
            print(f"Success: {doc.metadata.get('success', 'unknown')}")
            print(f"Content: {doc.page_content[:200]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ Direct retriever test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_langchain_integration():
    """Test LangChain SQL Agent integration in main agent"""
    print("\n🧪 Testing LangChain SQL Agent integration in FirebirdDirectSQLAgent...")
    
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        # Use string LLM identifier as expected by the agent
        llm = "gpt-4"
        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        
        # Initialize agent with LangChain mode
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection,
            llm=llm,
            retrieval_mode='langchain',  # Use LangChain SQL Agent mode
            use_enhanced_knowledge=True
        )
        
        print("✅ Agent initialized successfully with LangChain mode")
        
        # Test queries
        test_queries = [
            "Wie viele Wohnungen gibt es insgesamt?",
            "Zeige die ersten 2 Bewohner",
            "Welche Eigentümer gibt es?"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 Testing query: {query}")
            print("="*60)
            
            start_time = time.time()
            try:
                result = agent.query(query)
                duration = time.time() - start_time
                
                print(f"⏱️ Query completed in {duration:.2f}s")
                print(f"✅ Success: {result.get('success', False)}")
                print(f"📄 Documents: {result.get('documents_retrieved', 0)}")
                print(f"💬 Answer: {result.get('answer', 'No answer')[:200]}...")
                
                results.append({
                    "query": query,
                    "success": result.get('success', False),
                    "duration": duration,
                    "answer": result.get('answer', 'No answer'),
                    "documents_retrieved": result.get('documents_retrieved', 0)
                })
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ Query failed after {duration:.2f}s: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "duration": duration,
                    "error": str(e),
                    "documents_retrieved": 0
                })
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("="*60)
        
        successful_queries = [r for r in results if r.get('success', False)]
        success_rate = len(successful_queries) / len(results) if results else 0
        avg_duration = sum(r['duration'] for r in results) / len(results) if results else 0
        
        print(f"Total Queries: {len(results)}")
        print(f"Successful: {len(successful_queries)}")
        print(f"Success Rate: {success_rate*100:.1f}%")
        print(f"Average Duration: {avg_duration:.2f}s")
        
        for result in results:
            status = "✅" if result.get('success', False) else "❌"
            print(f"{status} {result['query']} ({result['duration']:.1f}s)")
        
        return success_rate > 0  # At least one query should succeed
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_retrieval_mode_comparison():
    """Compare LangChain mode with other modes"""
    print("\n🧪 Testing retrieval mode comparison...")
    
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        llm = "gpt-4"
        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        modes_to_test = ['langchain', 'enhanced', 'none']
        
        results = {}
        
        for mode in modes_to_test:
            print(f"\n🔄 Testing mode: {mode}")
            
            try:
                agent = FirebirdDirectSQLAgent(
                    db_connection_string=db_connection,
                    llm=llm,
                    retrieval_mode=mode,
                    use_enhanced_knowledge=True
                )
                
                start_time = time.time()
                result = agent.query(test_query)
                duration = time.time() - start_time
                
                results[mode] = {
                    "success": result.get('success', False),
                    "duration": duration,
                    "answer": result.get('answer', 'No answer'),
                    "documents_retrieved": result.get('documents_retrieved', 0)
                }
                
                print(f"✅ {mode}: {duration:.2f}s, Success: {result.get('success', False)}")
                
            except Exception as e:
                print(f"❌ {mode} failed: {e}")
                results[mode] = {
                    "success": False,
                    "duration": 0,
                    "error": str(e),
                    "documents_retrieved": 0
                }
        
        print(f"\n{'='*60}")
        print("📊 MODE COMPARISON")
        print("="*60)
        
        for mode, result in results.items():
            status = "✅" if result.get('success', False) else "❌"
            duration = result.get('duration', 0)
            docs = result.get('documents_retrieved', 0)
            print(f"{status} {mode:12} | {duration:6.2f}s | {docs:3d} docs")
        
        return any(r.get('success', False) for r in results.values())
        
    except Exception as e:
        print(f"❌ Mode comparison test failed: {e}")
        return False


def main():
    """Run all LangChain SQL Agent tests"""
    print("🚀 Starting LangChain SQL Database Agent Integration Tests")
    print("="*60)
    
    tests = [
        ("Direct Retriever Test", test_langchain_retriever_direct),
        ("Integration Test", test_langchain_integration),
        ("Mode Comparison Test", test_retrieval_mode_comparison)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print("="*60)
        
        try:
            success = test_func()
            results[test_name] = success
            print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Final summary
    print(f"\n{'='*60}")
    print("🏁 FINAL TEST RESULTS")
    print("="*60)
    
    passed_tests = [name for name, success in results.items() if success]
    total_tests = len(results)
    
    print(f"Tests Passed: {len(passed_tests)}/{total_tests}")
    print(f"Success Rate: {len(passed_tests)/total_tests*100:.1f}%")
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    if len(passed_tests) == total_tests:
        print("\n🎉 All tests passed! LangChain SQL Agent integration is working.")
    elif len(passed_tests) > 0:
        print(f"\n⚠️ Partial success. {len(passed_tests)} out of {total_tests} tests passed.")
    else:
        print("\n💥 All tests failed. Check the implementation and dependencies.")
    
    return len(passed_tests) > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)