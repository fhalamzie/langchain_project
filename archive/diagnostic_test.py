#!/usr/bin/env python3
"""
Diagnostic test to understand SQL generation problems across all retrieval modes
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_single_query_all_modes():
    """Test one query across all retrieval modes to diagnose SQL generation issues"""

    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        # Simple test query
        test_query = "Wer wohnt in der Marienstr. 26, 45307 Essen"
        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"

        print(f"🧪 DIAGNOSTIC TEST: {test_query}")
        print("=" * 80)

        # Initialize LLM once
        llm_interface = LLMInterface("gpt-4o-mini")
        llm = llm_interface.llm  # Direct access to the ChatOpenAI instance

        # Test all 5 modes
        modes = ["enhanced", "faiss", "none", "langchain", "langgraph"]
        results = {}

        for mode in modes:
            print(f"\n### {mode.upper()} MODE ###")
            try:
                # Create agent for this mode
                agent = FirebirdDirectSQLAgent(
                    db_connection_string=db_connection,
                    llm=llm,
                    retrieval_mode=mode,
                    use_enhanced_knowledge=True,
                )

                print(f"✅ Agent initialized successfully")

                # Process query
                result = agent.query(test_query)

                # Extract key information
                sql_query = result.get("sql_query", "N/A")
                answer = result.get("answer", "N/A")
                success = result.get("success", False)
                execution_time = result.get("execution_time", 0)

                print(f"Success: {success}")
                print(f"SQL: {sql_query}")
                print(f"Answer: {answer[:200]}...")
                print(f"Time: {execution_time:.2f}s")

                results[mode] = {
                    "success": success,
                    "sql": sql_query,
                    "answer": answer,
                    "time": execution_time,
                }

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                results[mode] = {"error": str(e)}

        # Summary analysis
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)

        for mode, result in results.items():
            if "error" in result:
                print(f"{mode.upper()}: ERROR - {result['error']}")
            else:
                success_icon = "✅" if result["success"] else "❌"
                print(f"{mode.upper()}: {success_icon} {result['time']:.1f}s")
                print(f"  SQL: {result['sql']}")
                print(f"  Answer: {result['answer'][:100]}...")
                print()

        return results

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_single_query_all_modes()
