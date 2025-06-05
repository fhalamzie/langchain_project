#!/usr/bin/env python3
"""
Test script for the 'none' retrieval mode
"""

import os
import sys

from firebird_sql_agent_direct import FirebirdDirectSQLAgent


def test_none_mode():
    """Test the None retrieval mode implementation"""
    print("🧪 Testing None Retrieval Mode...")

    # Database connection
    db_connection = "/home/projects/langchain_project/WINCASA2022.FDB"

    try:
        # Initialize agent with None mode
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection,
            llm="gpt-4",
            retrieval_mode="none",  # Test the none mode
            use_enhanced_knowledge=True,
        )

        if not agent or not agent.sql_agent:
            print("❌ Failed to initialize agent with None mode")
            return False

        print("✅ Agent initialized successfully with None mode")

        # Test query
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        print(f"\n🔍 Testing query: '{test_query}'")

        response = agent.query(test_query)

        print("\n📊 Response:")
        print(f"  Mode: {response.get('retrieval_mode')}")
        print(f"  Documents Retrieved: {response.get('documents_retrieved', 0)}")
        print(f"  Answer: {response.get('answer', 'No answer')[:200]}...")
        print(f"  SQL: {response.get('sql_query', 'No SQL')}")
        print(f"  Success: {response.get('success', False)}")

        # Verify it's actually using none mode
        if response.get("retrieval_mode") == "none":
            print("✅ None mode working correctly")
            if response.get("documents_retrieved", 0) == 0:
                print("✅ No documents retrieved as expected")
            else:
                print("⚠️ Warning: Documents were retrieved in None mode")
            return True
        else:
            print(f"❌ Expected 'none' mode, got '{response.get('retrieval_mode')}'")
            return False

    except Exception as e:
        print(f"❌ Error testing None mode: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_none_mode()
    print(f"\n🎯 None mode test: {'PASSED' if success else 'FAILED'}")
