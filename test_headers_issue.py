#!/usr/bin/env python3
"""
Test script to reproduce the LangChain headers issue.
"""

import sys
import traceback

def test_llm_headers_issue():
    """Test to reproduce the headers issue with LLM interface"""
    print("🧪 Testing LLM Headers Issue...")
    
    try:
        from llm_interface import LLMInterface
        
        # Create LLM interface 
        print("1. Creating LLM interface...")
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        
        print(f"2. LLM created successfully: {type(llm)}")
        print(f"   Model: {llm.model_name}")
        print(f"   Model kwargs: {llm.model_kwargs}")
        
        # Test a simple invocation
        print("3. Testing simple invocation...")
        messages = [{"role": "user", "content": "Say hello"}]
        response = llm.invoke(messages)
        
        print(f"4. Response: {response.content}")
        print("✅ Headers issue NOT reproduced - test passed")
        return True
        
    except Exception as e:
        print(f"❌ Headers issue reproduced - error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_langchain_sql_agent_headers():
    """Test LangChain SQL agent to reproduce headers issue"""
    print("\n🧪 Testing LangChain SQL Agent Headers Issue...")
    
    try:
        from llm_interface import LLMInterface
        from langchain_sql_retriever_fixed import LangChainSQLRetriever
        
        # Create LLM interface
        print("1. Creating LLM interface...")
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        
        # Create fake database connection string
        db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050/fake.fdb"
        
        print("2. Creating LangChain SQL retriever...")
        retriever = LangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=False  # Disable monitoring to isolate headers issue
        )
        
        print("3. Testing document retrieval...")
        # This should trigger the headers issue if it exists
        docs = retriever.retrieve_documents("How many tables?")
        
        print(f"4. Retrieved {len(docs)} documents")
        print("✅ Headers issue NOT reproduced in LangChain agent")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ LangChain headers issue reproduced - error: {error_msg}")
        
        if "headers" in error_msg.lower():
            print("🎯 This IS the headers issue we're looking for!")
        else:
            print("🤔 This is a different error, not the headers issue")
            
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔍 WINCASA LangChain Headers Issue Reproduction Test")
    print("=" * 60)
    
    # Test 1: Basic LLM interface
    test1_passed = test_llm_headers_issue()
    
    # Test 2: LangChain SQL agent
    test2_passed = test_langchain_sql_agent_headers()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Basic LLM Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   LangChain Agent Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if not test1_passed or not test2_passed:
        print("\n🎯 Headers issue reproduced! Now we can fix it.")
        sys.exit(1)
    else:
        print("\n🤔 Headers issue NOT reproduced. May already be fixed.")
        sys.exit(0)