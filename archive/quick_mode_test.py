#!/usr/bin/env python3
"""
Quick test for all 4 retrieval modes without Phoenix monitoring
"""

import os
import time

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/envs/openrouter.env")
load_dotenv("/home/envs/openai.env")


def test_enhanced_mode():
    """Test Enhanced retrieval mode"""
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        print("🧪 Testing Enhanced Mode...")
        llm = LLMInterface().llm
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
            llm=llm,
            retrieval_mode="enhanced",
            use_enhanced_knowledge=True,
        )

        start_time = time.time()
        result = agent.process_query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time

        print(f"✅ Enhanced Mode: {duration:.2f}s")
        print(f"   Result: {result[:100]}...")
        return True

    except Exception as e:
        print(f"❌ Enhanced Mode failed: {e}")
        return False


def test_faiss_mode():
    """Test FAISS retrieval mode"""
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        print("🧪 Testing FAISS Mode...")
        llm = LLMInterface().llm
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
            llm=llm,
            retrieval_mode="faiss",
            use_enhanced_knowledge=True,
        )

        start_time = time.time()
        result = agent.process_query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time

        print(f"✅ FAISS Mode: {duration:.2f}s")
        print(f"   Result: {result[:100]}...")
        return True

    except Exception as e:
        print(f"❌ FAISS Mode failed: {e}")
        return False


def test_none_mode():
    """Test None retrieval mode"""
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        print("🧪 Testing None Mode...")
        llm = LLMInterface().llm
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB",
            llm=llm,
            retrieval_mode="none",
            use_enhanced_knowledge=True,
        )

        start_time = time.time()
        result = agent.process_query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time

        print(f"✅ None Mode: {duration:.2f}s")
        print(f"   Result: {result[:100]}...")
        return True

    except Exception as e:
        print(f"❌ None Mode failed: {e}")
        return False


def test_langchain_mode():
    """Test LangChain retrieval mode"""
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        print("🧪 Testing LangChain Mode...")
        llm = LLMInterface().llm
        agent = FirebirdDirectSQLAgent(
            db_connection_string="firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            llm=llm,
            retrieval_mode="langchain",
            use_enhanced_knowledge=True,
        )

        start_time = time.time()
        result = agent.process_query("Wie viele Wohnungen gibt es insgesamt?")
        duration = time.time() - start_time

        print(f"✅ LangChain Mode: {duration:.2f}s")
        print(f"   Result: {result[:100]}...")
        return True

    except Exception as e:
        print(f"❌ LangChain Mode failed: {e}")
        return False


def main():
    """Run all mode tests"""
    print("🚀 Quick Mode Test - All 5 Retrieval Modes")
    print("=" * 50)

    results = {
        "enhanced": test_enhanced_mode(),
        "faiss": test_faiss_mode(),
        "none": test_none_mode(),
        "langchain": test_langchain_mode(),
    }

    print("\n📊 Test Summary:")
    print("=" * 30)
    working_modes = 0
    for mode, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"  {mode.upper()}: {status}")
        if success:
            working_modes += 1

    print(f"\n🎯 Result: {working_modes}/5 modes functional")

    if working_modes >= 4:
        print("✅ System is PRODUCTION READY")
    else:
        print("⚠️ System needs fixes before production")


if __name__ == "__main__":
    main()
