#!/usr/bin/env python3
"""
Quick Retrieval Test for All Available Modes

Tests all functioning retrieval modes with simple queries to verify current status.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_all_modes():
    """Test all available retrieval modes"""
    try:
        # Import within function to handle failures gracefully
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        from llm_interface import LLMInterface

        logger.info("✅ System imports successful")

        # Setup
        db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        llm_interface = LLMInterface("gpt-4")

        # Test queries
        test_queries = [
            "Wie viele Wohnungen gibt es insgesamt?",
            "Zeige die ersten 2 Eigentümer",
        ]

        # Available modes
        modes = ["enhanced", "faiss", "none", "langchain"]

        results = {}

        for mode in modes:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {mode} mode...")
            logger.info("=" * 60)

            mode_results = []

            try:
                # Create agent for this mode
                if mode == "langchain":
                    # Special handling for LangChain mode
                    try:
                        from langchain_sql_retriever_fixed import LangChainSQLRetriever

                        agent = LangChainSQLRetriever(
                            db_connection_string=db_connection,
                            llm=llm_interface.llm,
                            enable_monitoring=False,
                        )
                        logger.info(f"✅ {mode} agent created")

                        # Test queries
                        for query in test_queries:
                            start_time = time.time()
                            try:
                                docs = agent.retrieve_documents(query, max_docs=3)
                                execution_time = time.time() - start_time

                                if docs and len(docs) > 0:
                                    result = {
                                        "query": query,
                                        "success": True,
                                        "response": docs[0].page_content[:200],
                                        "execution_time": execution_time,
                                        "doc_count": len(docs),
                                    }
                                    logger.info(
                                        f"✅ Query succeeded in {execution_time:.2f}s"
                                    )
                                else:
                                    result = {
                                        "query": query,
                                        "success": False,
                                        "error": "No documents returned",
                                        "execution_time": execution_time,
                                    }
                                    logger.warning(f"⚠️ No documents returned")

                            except Exception as e:
                                execution_time = time.time() - start_time
                                result = {
                                    "query": query,
                                    "success": False,
                                    "error": str(e),
                                    "execution_time": execution_time,
                                }
                                logger.error(f"❌ Query failed: {e}")

                            mode_results.append(result)

                    except Exception as e:
                        logger.error(f"❌ LangChain mode initialization failed: {e}")
                        mode_results.append(
                            {
                                "error": f"Mode initialization failed: {e}",
                                "success": False,
                            }
                        )

                else:
                    # Standard modes (enhanced, faiss, none)
                    agent = FirebirdDirectSQLAgent(
                        db_connection_string=db_connection,
                        llm=llm_interface.llm,
                        retrieval_mode=mode,
                        use_enhanced_knowledge=True,
                    )
                    logger.info(f"✅ {mode} agent created")

                    # Test queries
                    for query in test_queries:
                        start_time = time.time()
                        try:
                            response = agent.query(query)
                            execution_time = time.time() - start_time

                            result = {
                                "query": query,
                                "success": response.get("success", False),
                                "response": response.get("answer", "No answer"),
                                "sql": response.get("sql_query", "No SQL"),
                                "execution_time": execution_time,
                            }

                            if result["success"]:
                                logger.info(
                                    f"✅ Query succeeded in {execution_time:.2f}s"
                                )
                                logger.info(f"SQL: {result['sql']}")
                            else:
                                logger.warning(
                                    f"⚠️ Query failed: {response.get('error', 'Unknown error')}"
                                )

                        except Exception as e:
                            execution_time = time.time() - start_time
                            result = {
                                "query": query,
                                "success": False,
                                "error": str(e),
                                "execution_time": execution_time,
                            }
                            logger.error(f"❌ Query failed: {e}")

                        mode_results.append(result)

            except Exception as e:
                logger.error(f"❌ {mode} mode failed completely: {e}")
                mode_results.append({"error": f"Mode failed: {e}", "success": False})

            results[mode] = mode_results

        # Print summary
        print(f"\n{'='*80}")
        print("📊 TEST SUMMARY")
        print("=" * 80)

        for mode, mode_results in results.items():
            successful = sum(1 for r in mode_results if r.get("success", False))
            total = len(mode_results)
            success_rate = (successful / total * 100) if total > 0 else 0

            status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            print(
                f"{status} {mode}: {successful}/{total} queries succeeded ({success_rate:.0f}%)"
            )

            if mode_results and "execution_time" in mode_results[0]:
                avg_time = sum(r.get("execution_time", 0) for r in mode_results) / len(
                    mode_results
                )
                print(f"   Average execution time: {avg_time:.2f}s")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_test_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Results saved to: {filename}")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 WINCASA Quick Retrieval Test - All Modes")
    print("=" * 80)
    test_all_modes()
