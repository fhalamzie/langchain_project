#!/usr/bin/env python3
"""
Complete retrieval mode test with all 11 queries.
Optimized version with pre-initialized agents.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/envs/openrouter.env")
load_dotenv("/home/envs/openai.env")

# Import the main agent
from firebird_sql_agent_direct import FirebirdDirectSQLAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# All 11 test queries
TEST_QUERIES = [
    "Wer wohnt in der Marienstr. 26, 45307 Essen",
    "Wer wohnt in der Marienstraße 26",
    "Wer wohnt in der Bäuminghausstr. 41, Essen",
    "Wer wohnt in der Schmiedestr. 8, 47055 Duisburg",
    "Alle Mieter der MARIE26",
    "Alle Eigentümer vom Haager Weg bitte",
    "Liste aller Eigentümer",
    "Liste aller Eigentümer aus Köln",
    "Liste aller Mieter in Essen",
    "Durchschnittliche Miete in Essen",
    "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg",
]

RETRIEVAL_MODES = ["faiss", "enhanced", "none"]


def initialize_all_agents():
    """Initialize all agents once at the beginning."""
    agents = {}
    db_connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"

    for mode in RETRIEVAL_MODES:
        logger.info(f"Initializing agent for mode: {mode}")
        try:
            agents[mode] = FirebirdDirectSQLAgent(
                db_connection_string=db_connection_string,
                llm="gpt-4o-mini",
                retrieval_mode=mode,
                use_enhanced_knowledge=True,
            )
            logger.info(f"✓ Successfully initialized {mode} agent")
        except Exception as e:
            logger.error(f"✗ Failed to initialize {mode} agent: {e}")
            agents[mode] = None

    return agents


def test_query_with_agent(
    agent, query: str, mode: str, timeout: int = 120
) -> Dict[str, Any]:
    """Test a single query with a specific agent."""
    result = {
        "query": query,
        "mode": mode,
        "success": False,
        "sql_query": None,
        "answer": None,
        "execution_time": None,
        "error": None,
        "row_count": 0,
    }

    if agent is None:
        result["error"] = f"Agent not initialized for mode {mode}"
        return result

    start_time = time.time()

    try:
        # Execute query with timeout handling
        response = agent.query(query)

        # Parse response
        if isinstance(response, dict):
            result["answer"] = response.get("agent_final_answer", "No answer")
            result["sql_query"] = response.get("generated_sql", "No SQL")

            # Try to extract row count
            if "query_results" in response and response["query_results"]:
                result["row_count"] = len(response["query_results"])
        else:
            result["answer"] = str(response)

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error in {mode} mode for query '{query[:30]}...': {e}")

    finally:
        result["execution_time"] = time.time() - start_time

    return result


def run_complete_test():
    """Run complete test with all queries and modes."""
    logger.info("Starting complete retrieval mode test")

    # Initialize all agents first
    logger.info("Initializing all agents...")
    agents = initialize_all_agents()

    if not any(agents.values()):
        logger.error("No agents could be initialized. Aborting test.")
        return

    # Run tests
    all_results = []
    total_tests = len(TEST_QUERIES) * len(RETRIEVAL_MODES)
    completed = 0

    for i, query in enumerate(TEST_QUERIES, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Query {i}/{len(TEST_QUERIES)}: {query}")
        logger.info(f"{'='*80}")

        query_results = []

        for mode in RETRIEVAL_MODES:
            completed += 1
            logger.info(f"\nProgress: {completed}/{total_tests} - Testing {mode} mode")

            result = test_query_with_agent(agents[mode], query, mode)
            query_results.append(result)
            all_results.append(result)

            # Log result
            if result["success"]:
                logger.info(
                    f"✓ {mode}: {result['execution_time']:.1f}s, Rows: {result['row_count']}"
                )
                # Check for expected residents in address queries
                if "Marienstr" in query and "Petra Nabakowski" in str(result["answer"]):
                    logger.info(f"  ✓ Found expected resident: Petra Nabakowski")
            else:
                logger.info(f"✗ {mode}: Failed - {result['error']}")

        # Quick comparison for this query
        successful = [r for r in query_results if r["success"]]
        if len(successful) > 1:
            sql_queries = {r["mode"]: r["sql_query"] for r in successful}
            unique_sqls = set(sql_queries.values())
            if len(unique_sqls) == 1:
                logger.info("  ✓ All modes generated identical SQL")
            else:
                logger.info("  ⚠ Different SQL queries generated")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"complete_retrieval_test_{timestamp}.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    logger.info(f"\nResults saved to: {results_file}")

    # Generate summary
    generate_summary(all_results)

    return all_results


def generate_summary(results: List[Dict]):
    """Generate test summary."""
    print("\n" + "=" * 80)
    print("COMPLETE RETRIEVAL TEST SUMMARY")
    print("=" * 80)

    # Overall statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])

    print(f"Total Tests: {total_tests}")
    print(
        f"Successful: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)"
    )

    # Per-mode statistics
    print(f"\nPER-MODE RESULTS:")
    print("-" * 50)

    for mode in RETRIEVAL_MODES:
        mode_results = [r for r in results if r["mode"] == mode]
        successful = sum(1 for r in mode_results if r["success"])
        total_time = sum(r["execution_time"] for r in mode_results if r["success"])
        avg_time = total_time / max(successful, 1)

        print(f"\n{mode.upper()} Mode:")
        print(
            f"  Success Rate: {successful}/{len(mode_results)} ({successful/len(mode_results)*100:.1f}%)"
        )
        print(f"  Avg Execution Time: {avg_time:.2f}s")
        print(f"  Total Time: {total_time:.1f}s")

    # Query-specific analysis
    print(f"\nQUERY-SPECIFIC ANALYSIS:")
    print("-" * 50)

    for query in TEST_QUERIES:
        query_results = [r for r in results if r["query"] == query]
        successful = [r for r in query_results if r["success"]]

        print(f"\n'{query[:40]}...'")
        if successful:
            # Check for address queries
            if any("Marienstr" in query for query in [query]):
                correct_answers = [
                    r
                    for r in successful
                    if "Petra Nabakowski" in str(r.get("answer", ""))
                ]
                print(
                    f"  Correct answers: {len(correct_answers)}/{len(successful)} modes"
                )

            # Performance comparison
            times = [(r["mode"], r["execution_time"]) for r in successful]
            times.sort(key=lambda x: x[1])
            print(f"  Fastest: {times[0][0]} ({times[0][1]:.1f}s)")
        else:
            print(f"  ✗ No successful results")


if __name__ == "__main__":
    try:
        run_complete_test()
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
