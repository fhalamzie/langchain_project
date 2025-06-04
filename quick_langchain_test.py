#!/usr/bin/env python3
"""
Quick Test for LangChain SQL Database Agent Integration

Fast test to verify the LangChain SQL Agent integration works.
"""

import time
import traceback

def quick_langchain_test():
    """Quick test of LangChain SQL Agent mode"""
    print("🚀 Quick LangChain SQL Agent Test")
    print("="*50)
    
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        # Quick setup
        llm = "gpt-4"
        db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        
        print("🔧 Initializing agent with LangChain mode...")
        start_time = time.time()
        
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection,
            llm=llm,
            retrieval_mode='langchain',
            use_enhanced_knowledge=True
        )
        
        init_time = time.time() - start_time
        print(f"✅ Agent initialized in {init_time:.2f}s")
        
        # Quick test query
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        print(f"\n🔍 Testing query: {test_query}")
        
        query_start = time.time()
        result = agent.query(test_query)
        query_time = time.time() - query_start
        
        print(f"⏱️ Query completed in {query_time:.2f}s")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📄 Documents: {result.get('documents_retrieved', 0)}")
        
        answer = result.get('answer', 'No answer')
        print(f"💬 Answer: {answer[:100]}...")
        
        if result.get('success', False):
            print("\n🎉 LangChain SQL Agent integration is working!")
            return True
        else:
            print("\n⚠️ Query succeeded but no valid result")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_mode_availability():
    """Test if langchain mode is available"""
    print("\n🧪 Testing mode availability...")
    
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        
        # Just test initialization without query
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm="gpt-4",
            retrieval_mode='langchain',
            use_enhanced_knowledge=False  # Faster initialization
        )
        
        # Check if langchain retriever was initialized
        if hasattr(agent, 'langchain_retriever') and agent.langchain_retriever:
            print("✅ LangChain retriever initialized successfully")
            return True
        else:
            print("❌ LangChain retriever not available")
            return False
            
    except Exception as e:
        print(f"❌ Mode availability test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Quick LangChain SQL Agent Tests...\n")
    
    # Test 1: Mode availability
    mode_available = test_mode_availability()
    
    # Test 2: Quick functionality test (only if mode is available)
    if mode_available:
        functionality_works = quick_langchain_test()
    else:
        functionality_works = False
    
    # Summary
    print("\n" + "="*50)
    print("📊 QUICK TEST SUMMARY")
    print("="*50)
    print(f"Mode Available: {'✅' if mode_available else '❌'}")
    print(f"Functionality: {'✅' if functionality_works else '❌'}")
    
    if mode_available and functionality_works:
        print("\n🎉 LangChain SQL Agent integration is ready for use!")
        print("You can now use retrieval_mode='langchain' in your agents.")
    elif mode_available:
        print("\n⚠️ Mode is available but functionality test failed.")
        print("Check the specific error messages above.")
    else:
        print("\n❌ LangChain mode is not properly initialized.")
        print("Check dependencies and configuration.")
    
    exit(0 if (mode_available and functionality_works) else 1)