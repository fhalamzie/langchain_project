#!/usr/bin/env python3
"""
Minimal test ohne Phoenix monitoring zur schnellen Validierung
"""

import os
import sys
import time

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/envs/openrouter.env")
load_dotenv("/home/envs/openai.env")

# Disable Phoenix monitoring completely
os.environ["DISABLE_PHOENIX"] = "true"


def test_minimal_enhanced():
    """Test Enhanced mode minimal"""
    try:
        print("🧪 Testing Enhanced Mode (minimal)...")

        # Test basic imports first
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        print("✅ Enhanced Mode: Imports successful")
        return True

    except Exception as e:
        print(f"❌ Enhanced Mode failed: {e}")
        return False


def test_minimal_langchain():
    """Test LangChain mode minimal"""
    try:
        print("🧪 Testing LangChain Mode (minimal)...")

        # Test Firebird server connection
        import subprocess

        result = subprocess.run(["netstat", "-ln"], capture_output=True, text=True)
        if ":3050" in result.stdout:
            print("✅ Firebird server running on port 3050")
        else:
            print("⚠️ Firebird server not detected on port 3050")

        # Test SQLAlchemy connection
        from sqlalchemy import create_engine, text

        engine = create_engine(
            "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        )

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM WOHNUNG"))
            count = result.scalar()
            print(
                f"✅ LangChain Mode: Database connected via SQLAlchemy, {count} apartments found"
            )
            return True

    except Exception as e:
        print(f"❌ LangChain Mode failed: {e}")
        return False


def test_minimal_sqlcoder():
    """Test SQLCoder basic import"""
    try:
        print("🧪 Testing SQLCoder Mode (import only)...")

        from sqlcoder_retriever import SQLCoderRetriever

        print("✅ SQLCoder: Import successful")
        return True

    except Exception as e:
        print(f"❌ SQLCoder Mode failed: {e}")
        return False


def main():
    """Run minimal tests"""
    print("🚀 Minimal Test Suite (No Phoenix)")
    print("=" * 40)

    start_time = time.time()

    results = {
        "enhanced": test_minimal_enhanced(),
        "langchain": test_minimal_langchain(),
        "sqlcoder": test_minimal_sqlcoder(),
    }

    duration = time.time() - start_time

    print(f"\n📊 Test Summary ({duration:.1f}s):")
    print("=" * 30)
    working_modes = 0
    for mode, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"  {mode.upper()}: {status}")
        if success:
            working_modes += 1

    print(f"\n🎯 Result: {working_modes}/3 core modes functional")


if __name__ == "__main__":
    main()
