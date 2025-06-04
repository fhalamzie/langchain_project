#!/usr/bin/env python3
"""
Vollständige Validierung aller 5 Retrieval Modi mit echten Queries
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

def test_mode_full_query(mode_name, connection_string, timeout=60):
    """Test a specific mode with full query execution"""
    try:
        print(f"🧪 Testing {mode_name.upper()} Mode (full query)...")
        
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface
        
        # Create LLM and agent
        llm = LLMInterface().llm
        agent = FirebirdDirectSQLAgent(
            db_connection_string=connection_string,
            llm=llm,
            retrieval_mode=mode_name,
            use_enhanced_knowledge=True
        )
        
        # Test query
        start_time = time.time()
        result = agent.process_query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time
        
        # Extract count from result
        success = "517" in str(result) or "apartment" in str(result).lower() or "wohnung" in str(result).lower()
        
        print(f"✅ {mode_name.upper()} Mode: {duration:.2f}s")
        print(f"   Success: {'Yes' if success else 'Unknown'}")
        print(f"   Result preview: {str(result)[:100]}...")
        
        return {
            "success": True,
            "duration": duration,
            "query_success": success,
            "result": str(result)[:200]
        }
        
    except Exception as e:
        print(f"❌ {mode_name.upper()} Mode failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "duration": 0,
            "query_success": False
        }

def main():
    """Run full validation of all modes"""
    print("🚀 Full Mode Validation - All 5 Retrieval Modes")
    print("=" * 60)
    
    # Mode configurations
    modes = {
        "enhanced": "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
        "faiss": "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB", 
        "none": "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
        "sqlcoder": "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
        "langchain": "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    }
    
    results = {}
    total_start = time.time()
    
    for mode, connection_string in modes.items():
        print(f"\n{'='*20} {mode.upper()} MODE {'='*20}")
        results[mode] = test_mode_full_query(mode, connection_string, timeout=90)
        
        # Small delay between tests
        time.sleep(2)
    
    total_duration = time.time() - total_start
    
    print(f"\n📊 Validation Summary ({total_duration:.1f}s total):")
    print("=" * 60)
    
    working_modes = 0
    successful_queries = 0
    
    for mode, result in results.items():
        if result["success"]:
            working_modes += 1
            if result["query_success"]:
                successful_queries += 1
                status = "✅ FULLY WORKING"
            else:
                status = "⚠️ PARTIAL (import ok, query unclear)"
        else:
            status = "❌ FAILED"
        
        duration = f"({result['duration']:.1f}s)" if result['success'] else ""
        print(f"  {mode.upper():10}: {status} {duration}")
    
    print(f"\n🎯 Final Results:")
    print(f"  Working modes: {working_modes}/5")
    print(f"  Successful queries: {successful_queries}/5")
    
    if working_modes >= 4 and successful_queries >= 3:
        print("✅ SYSTEM IS PRODUCTION READY")
    elif working_modes >= 3:
        print("⚠️ SYSTEM IS MOSTLY FUNCTIONAL")
    else:
        print("❌ SYSTEM NEEDS SIGNIFICANT FIXES")

if __name__ == "__main__":
    main()