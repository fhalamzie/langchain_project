#!/usr/bin/env python3
"""
Quick check of all 5 retrieval modes - initialization only
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_mode_initialization():
    """Quick check that all modes can initialize without errors"""

    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        llm_interface = LLMInterface("gpt-4o-mini")
        llm = llm_interface.llm

        modes = ["enhanced", "faiss", "none", "langchain", "langgraph"]
        results = {}

        print("🧪 QUICK MODE INITIALIZATION CHECK")
        print("=" * 50)

        for mode in modes:
            print(f"\n🔍 Testing {mode.upper()} mode initialization...")
            try:
                agent = FirebirdDirectSQLAgent(
                    db_connection_string=db_connection,
                    llm=llm,
                    retrieval_mode=mode,
                    use_enhanced_knowledge=True,
                )

                print(f"✅ {mode.upper()} mode: Initialized successfully")
                results[mode] = "SUCCESS"

            except Exception as e:
                print(f"❌ {mode.upper()} mode: Failed - {str(e)}")
                results[mode] = f"ERROR: {str(e)}"

        print("\n" + "=" * 50)
        print("INITIALIZATION SUMMARY")
        print("=" * 50)

        for mode, result in results.items():
            status_icon = "✅" if result == "SUCCESS" else "❌"
            print(f"{status_icon} {mode.upper()}: {result}")

        successful_modes = sum(1 for r in results.values() if r == "SUCCESS")
        print(f"\n📊 {successful_modes}/{len(modes)} modes initialized successfully")

        return results

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    check_mode_initialization()
