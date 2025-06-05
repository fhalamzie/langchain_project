#!/usr/bin/env python3
"""
Quick validation test for all available retrieval modes
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

# Import the main agent
try:
    from firebird_sql_agent_direct import FirebirdDirectSQLAgent
    print("✅ Successfully imported FirebirdDirectSQLAgent")
except Exception as e:
    print(f"❌ Failed to import FirebirdDirectSQLAgent: {e}")
    sys.exit(1)

def test_mode(mode_name, query="Wie viele Wohnungen gibt es insgesamt?"):
    """Test a specific retrieval mode with a simple query"""
    print(f"\n{'='*50}")
    print(f"🧪 Testing mode: {mode_name}")
    print(f"📝 Query: {query}")
    print(f"{'='*50}")
    
    try:
        start_time = time.time()
        
        # Initialize agent with correct parameters
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm=llm,
            retrieval_mode=mode_name
        )
        
        init_time = time.time() - start_time
        print(f"⏱️ Agent initialization: {init_time:.2f}s")
        
        # Execute query
        query_start = time.time()
        result = agent.query(query)
        query_time = time.time() - query_start
        
        print(f"⏱️ Query execution: {query_time:.2f}s")
        print(f"✅ Mode '{mode_name}' - SUCCESS")
        print(f"📊 Result preview: {str(result)[:200]}...")
        
        return True, query_time, str(result)[:500]
        
    except Exception as e:
        print(f"❌ Mode '{mode_name}' - FAILED: {e}")
        return False, None, str(e)

def main():
    """Test all available retrieval modes"""
    print("🚀 WINCASA Quick Mode Validation")
    print("=" * 60)
    
    # Test modes - available retrieval modes
    test_modes = ["enhanced", "faiss", "none", "langchain"]
    
    results = {}
    
    for mode in test_modes:
        success, execution_time, result = test_mode(mode)
        results[mode] = {
            "success": success,
            "execution_time": execution_time,
            "result": result
        }
        
        # Small delay between tests
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for mode, data in results.items():
        status = "✅ PASS" if data["success"] else "❌ FAIL"
        time_str = f"{data['execution_time']:.2f}s" if data["execution_time"] else "N/A"
        print(f"{mode:>10}: {status} ({time_str})")
    
    success_count = sum(1 for r in results.values() if r["success"])
    print(f"\nOverall: {success_count}/{len(test_modes)} modes working")
    
    return results

if __name__ == "__main__":
    main()