#!/usr/bin/env python3
"""
Fast test aller Modi mit optimiertem Phoenix SQLite Backend
"""

import os
import time

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/envs/openrouter.env")
load_dotenv("/home/envs/openai.env")

# Import optimized Phoenix config
from phoenix_sqlite_config import get_phoenix_config


def test_mode_fast(mode_name, timeout=45):
    """Fast test eines spezifischen Modus"""
    try:
        print(f"🧪 Testing {mode_name.upper()} Mode (fast)...")

        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        # Create LLM and agent
        llm = LLMInterface().llm

        # Connection string based on mode
        if mode_name == "langchain":
            connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        else:
            connection_string = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"

        agent = FirebirdDirectSQLAgent(
            db_connection_string=connection_string,
            llm=llm,
            retrieval_mode=mode_name,
            use_enhanced_knowledge=True,
        )

        # Fast test query
        start_time = time.time()
        result = agent.query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time

        # Check if result contains expected data
        success = (
            "517" in str(result)
            or "apartment" in str(result).lower()
            or "wohnung" in str(result).lower()
        )

        print(
            f"✅ {mode_name.upper()}: {duration:.2f}s - {'SUCCESS' if success else 'UNCLEAR'}"
        )
        if not success:
            print(f"   Result: {str(result)[:150]}...")

        return {"success": True, "duration": duration, "query_success": success}

    except Exception as e:
        print(f"❌ {mode_name.upper()}: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run fast test of all modes with optimized Phoenix"""
    print("🚀 Fast Mode Test - Optimized Phoenix SQLite")
    print("=" * 50)

    # Setup optimized Phoenix
    print("🔧 Configuring Phoenix SQLite backend...")
    phoenix_config = get_phoenix_config()
    if phoenix_config and phoenix_config.get("session"):
        print(f"✅ Phoenix UI: http://localhost:6006")
    else:
        print("⚠️ Phoenix UI not available")

    # Test modes in order of complexity
    modes = ["none", "enhanced", "faiss", "langchain", "sqlcoder"]

    results = {}
    total_start = time.time()

    for mode in modes:
        print(f"\n{'='*15} {mode.upper()} {'='*15}")
        results[mode] = test_mode_fast(mode, timeout=60)

        # Small delay to avoid overwhelming the system
        time.sleep(1)

    total_duration = time.time() - total_start

    print(f"\n📊 Fast Test Summary ({total_duration:.1f}s total):")
    print("=" * 50)

    working_modes = 0
    successful_queries = 0

    for mode, result in results.items():
        if result["success"]:
            working_modes += 1
            if result.get("query_success", False):
                successful_queries += 1
                status = "✅ FULLY WORKING"
                duration_info = f"({result['duration']:.1f}s)"
            else:
                status = "⚠️ PARTIAL"
                duration_info = f"({result['duration']:.1f}s)"
        else:
            status = "❌ FAILED"
            duration_info = ""

        print(f"  {mode.upper():10}: {status} {duration_info}")

    print(f"\n🎯 Performance Results:")
    print(f"  Working modes: {working_modes}/5")
    print(f"  Successful queries: {successful_queries}/5")
    print(f"  Average time per mode: {total_duration/5:.1f}s")

    if working_modes >= 4 and successful_queries >= 3:
        print("\n✅ SYSTEM IS PRODUCTION READY!")
        if phoenix_config and phoenix_config.get("session"):
            print(f"📊 Monitor at: http://localhost:6006")
    elif working_modes >= 3:
        print("\n⚠️ SYSTEM IS MOSTLY FUNCTIONAL")
    else:
        print("\n❌ SYSTEM NEEDS FIXES")


if __name__ == "__main__":
    main()
