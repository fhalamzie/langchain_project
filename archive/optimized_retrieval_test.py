#!/usr/bin/env python3
"""
Optimized retrieval mode test with:
1. Agent reuse (initialize once, use for all queries)
2. Retriever caching (persistent FAISS and knowledge cache)
3. Optional concurrent testing (rate-limit aware)
4. Performance monitoring and comparison
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/envs/openrouter.env")
load_dotenv("/home/envs/openai.env")

# Import the main agent
from firebird_sql_agent_direct import FirebirdDirectSQLAgent


# Setup logging with file output
def setup_logging(concurrent_mode=False, workers=1):
    """Setup logging to both console and file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_suffix = f"concurrent_{workers}w" if concurrent_mode else "sequential"
    log_filename = f"optimized_retrieval_test_{mode_suffix}_{timestamp}.log"

    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                log_filename, mode="w", encoding="utf-8"
            ),  # Fresh file each run
            logging.StreamHandler(),  # Console output
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting optimized retrieval test - Log file: {log_filename}")
    logger.info(f"Mode: {'Concurrent' if concurrent_mode else 'Sequential'}")
    if concurrent_mode:
        logger.info(f"Workers: {workers}")

    return logger, log_filename


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

# Modelle für A/B-Tests
MODEL_NAMES = [
    "openai/gpt-4.1-nano",
    "openai/gpt-4.1",
    "deepseek/deepseek-r1-0528",
    "google/gemini-2.5-pro-preview",
    "anthropic/claude-3.5-haiku:beta",
]

RETRIEVAL_MODES = ["enhanced", "faiss", "none"]


class OptimizedRetrievalTestRunner:
    """
    Optimized test runner with agent reuse and caching.
    """

    def __init__(
        self,
        timeout_seconds: int = 120,
        enable_concurrent: bool = False,
        max_workers: int = 2,
    ):
        self.timeout_seconds = timeout_seconds
        self.enable_concurrent = enable_concurrent
        self.max_workers = max_workers  # Conservative limit for API rate limits
        self.results = []
        self.agents = {}
        self.retriever_cache = {}
        self.log_filename = None

        # Performance tracking
        self.initialization_time = 0
        self.total_test_time = 0

    def initialize_agents_with_cache(self):
        """Initialize agents for all model-mode combinations with caching."""
        start_time = time.time()
        logger.info("Initializing agents for A/B testing...")

        db_connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        total_agents = len(MODEL_NAMES) * len(RETRIEVAL_MODES)
        agent_count = 0

        for model_name in MODEL_NAMES:
            for mode in RETRIEVAL_MODES:
                agent_key = f"{model_name}_{mode}"
                agent_count += 1

                try:
                    logger.info(
                        f"Initializing agent {agent_count}/{total_agents}: {model_name} ({mode})"
                    )

                    agent = FirebirdDirectSQLAgent(
                        db_connection_string=db_connection_string,
                        llm=model_name,
                        retrieval_mode=mode,
                        use_enhanced_knowledge=True,
                    )

                    # Cache retriever
                    if hasattr(agent, "retriever") and agent.retriever:
                        try:
                            agent.retriever.similarity_search("test", k=1)
                        except Exception as e:
                            logger.warning(f"  ⚠ Retriever cache failed: {e}")

                    self.agents[agent_key] = agent
                    logger.info(f"✓ Agent initialized: {model_name} ({mode})")

                except Exception as e:
                    logger.error(f"✗ Failed to initialize {model_name} ({mode}): {e}")
                    self.agents[agent_key] = None

        self.initialization_time = time.time() - start_time
        logger.info(
            f"Agent initialization completed in {self.initialization_time:.2f}s"
        )
        logger.info(
            f"Active agents: {sum(1 for a in self.agents.values() if a)}/{total_agents}"
        )
        return any(self.agents.values())

    def test_single_query(
        self, agent, query: str, model_name: str, mode: str
    ) -> Dict[str, Any]:
        """Test a single query with an agent."""
        result = {
            "query": query,
            "model": model_name,
            "mode": mode,
            "success": False,
            "sql_query": None,
            "answer": None,
            "execution_time": None,
            "error": None,
            "row_count": 0,
        }

        if agent is None:
            result["error"] = f"Agent not available for mode {mode}"
            return result

        start_time = time.time()

        try:
            # Execute query (agent is reused, no re-initialization)
            response = agent.query(query)

            # Parse response
            if isinstance(response, dict):
                result["answer"] = response.get("agent_final_answer", "No answer")
                result["sql_query"] = response.get("generated_sql", "No SQL")

                # Extract row count
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

    def run_sequential_test(self) -> List[Dict[str, Any]]:
        """Run tests sequentially (original approach but with agent reuse)."""
        logger.info("\n" + "🔄 STARTING SEQUENTIAL TEST")
        logger.info("=" * 60)

        all_results = []
        total_queries = len(TEST_QUERIES)
        total_tests = total_queries * len(RETRIEVAL_MODES)
        completed_tests = 0

        for i, query in enumerate(TEST_QUERIES, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"📋 QUERY {i}/{total_queries}: {query}")
            logger.info(f"{'='*80}")

            for model_name in MODEL_NAMES:
                for mode in RETRIEVAL_MODES:
                    agent_key = f"{model_name}_{mode}"
                    completed_tests += 1
                    progress_pct = (completed_tests / total_tests) * 100

                    logger.info(
                        f"\n🧪 Testing {model_name} ({mode}) - {completed_tests}/{total_tests} ({progress_pct:.1f}%)"
                    )

                    start_query_time = time.time()
                    result = self.test_single_query(
                        self.agents[agent_key], query, model_name, mode
                    )

                all_results.append(result)

                # Detailed result logging
                if result["success"]:
                    logger.info(
                        f"✅ {mode.upper()}: {result['execution_time']:.1f}s, Rows: {result['row_count']}"
                    )
                    # Check for expected results
                    if "Marienstr" in query and "Petra Nabakowski" in str(
                        result["answer"]
                    ):
                        logger.info(
                            f"   🎯 CORRECT: Found expected resident Petra Nabakowski!"
                        )
                else:
                    logger.info(f"❌ {mode.upper()}: FAILED - {result['error']}")

                # Time estimate
                remaining_tests = total_tests - completed_tests
                if completed_tests > 0:
                    avg_time_per_test = sum(
                        r["execution_time"] for r in all_results if r["success"]
                    ) / max(1, len([r for r in all_results if r["success"]]))
                    estimated_remaining = remaining_tests * avg_time_per_test
                    logger.info(
                        f"⏱️  Estimated remaining time: {estimated_remaining/60:.1f} minutes"
                    )

        logger.info(f"\n🏁 SEQUENTIAL TEST COMPLETED")
        logger.info(f"📊 Total tests: {completed_tests}/{total_tests}")
        return all_results

    def run_concurrent_test(self) -> List[Dict[str, Any]]:
        """Run tests with limited concurrency (rate-limit aware)."""
        logger.info(f"Running concurrent test with max {self.max_workers} workers...")

        all_results = []

        # Create all test tasks
        test_tasks = []
        for query in TEST_QUERIES:
            for model_name in MODEL_NAMES:
                for mode in RETRIEVAL_MODES:
                    test_tasks.append((query, model_name, mode))

        logger.info(f"Total test tasks: {len(test_tasks)}")

        # Execute with limited concurrency
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all tasks
            future_to_task = {}
            for query, model_name, mode in test_tasks:
                agent_key = f"{model_name}_{mode}"
                future = executor.submit(
                    self.test_single_query,
                    self.agents[agent_key],
                    query,
                    model_name,
                    mode,
                )
                future_to_task[future] = (query, model_name, mode)

            # Collect results as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_task):
                query, model_name, mode = future_to_task[future]
                completed += 1

                try:
                    result = future.result()
                    all_results.append(result)

                    # Log progress
                    if result["success"]:
                        logger.info(
                            f"✓ [{completed}/{len(test_tasks)}] {mode}: {result['execution_time']:.1f}s"
                        )
                    else:
                        logger.info(f"✗ [{completed}/{len(test_tasks)}] {mode}: Failed")

                except Exception as e:
                    logger.error(f"Task failed for {query} ({mode}): {e}")

        # Sort results by query, model, mode
        query_order = {query: i for i, query in enumerate(TEST_QUERIES)}
        model_order = {model: i for i, model in enumerate(MODEL_NAMES)}
        mode_order = {mode: i for i, mode in enumerate(RETRIEVAL_MODES)}

        all_results.sort(
            key=lambda r: (
                query_order[r["query"]],
                model_order[r["model"]],
                mode_order[r["mode"]],
            )
        )

        return all_results

    def run_optimized_test(self):
        """Run the complete optimized test."""
        # Setup logging first
        global logger
        logger, self.log_filename = setup_logging(
            self.enable_concurrent, self.max_workers
        )

        logger.info("=" * 80)
        logger.info("WINCASA OPTIMIZED RETRIEVAL TEST STARTED")
        logger.info("=" * 80)
        logger.info(f"Total queries: {len(TEST_QUERIES)}")
        logger.info(f"Total modes: {len(RETRIEVAL_MODES)}")
        logger.info(f"Total tests: {len(TEST_QUERIES) * len(RETRIEVAL_MODES)}")
        logger.info(f"Timeout per query: {self.timeout_seconds}s")

        if self.enable_concurrent:
            logger.info(f"💾 CONCURRENT MODE: {self.max_workers} workers")
        else:
            logger.info(f"💾 SEQUENTIAL MODE: 1 worker")

        # Initialize agents with caching
        if not self.initialize_agents_with_cache():
            logger.error("No agents could be initialized. Aborting test.")
            return None

        # Run tests
        test_start = time.time()

        if self.enable_concurrent:
            all_results = self.run_concurrent_test()
        else:
            all_results = self.run_sequential_test()

        self.total_test_time = time.time() - test_start

        logger.info("\n" + "=" * 80)
        logger.info("🎉 TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"⏱️  Total initialization time: {self.initialization_time:.2f}s")
        logger.info(f"⏱️  Total test execution time: {self.total_test_time:.2f}s")
        logger.info(
            f"⏱️  Grand total time: {self.initialization_time + self.total_test_time:.2f}s"
        )

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "concurrent" if self.enable_concurrent else "sequential"
        results_file = f"optimized_retrieval_test_{mode_suffix}_{timestamp}.json"

        # Add optimization metadata
        optimization_metadata = {
            "test_mode": "concurrent" if self.enable_concurrent else "sequential",
            "max_workers": self.max_workers if self.enable_concurrent else 1,
            "agent_reuse": True,
            "retriever_caching": True,
            "initialization_time": self.initialization_time,
            "total_test_time": self.total_test_time,
            "total_queries": len(TEST_QUERIES),
            "total_modes": len(RETRIEVAL_MODES),
            "total_tests": len(all_results),
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {"metadata": optimization_metadata, "results": all_results},
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"\n📄 Results saved to: {results_file}")
        logger.info(f"📄 Log file saved to: {self.log_filename}")
        logger.info(f"\n💡 Monitor progress with: cat {self.log_filename}")

        # Generate summary
        self.generate_optimization_summary(all_results, optimization_metadata)

        return all_results

    def generate_optimization_summary(self, results: List[Dict], metadata: Dict):
        """Generate optimized test summary with performance analysis."""
        print("\n" + "=" * 80)
        print("OPTIMIZED RETRIEVAL TEST SUMMARY")
        print("=" * 80)

        # Optimization info
        print(f"Test Mode: {metadata['test_mode'].upper()}")
        print(f"Agent Reuse: ✓ Enabled")
        print(f"Retriever Caching: ✓ Enabled")
        if metadata["test_mode"] == "concurrent":
            print(f"Max Workers: {metadata['max_workers']}")

        print(f"\nTIMING ANALYSIS:")
        print(f"Initialization Time: {metadata['initialization_time']:.2f}s")
        print(f"Total Test Time: {metadata['total_test_time']:.2f}s")
        print(
            f"Average per Test: {metadata['total_test_time']/metadata['total_tests']:.2f}s"
        )

        # Test results
        successful_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)

        print(f"\nTEST RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(
            f"Successful: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)"
        )

        # Per-mode performance
        print(f"\nPER-MODE PERFORMANCE:")
        print("-" * 60)

        # Per-model performance
        print(f"\nPER-MODEL PERFORMANCE:")
        print("-" * 60)

        for model_name in MODEL_NAMES:
            model_results = [r for r in results if r["model"] == model_name]
            successful = [r for r in model_results if r["success"]]

            if successful:
                avg_time = sum(r["execution_time"] for r in successful) / len(
                    successful
                )
                success_rate = len(successful) / len(model_results) * 100

                print(f"\n{model_name}:")
                print(
                    f"  Success Rate: {len(successful)}/{len(model_results)} ({success_rate:.1f}%)"
                )
                print(f"  Avg Execution Time: {avg_time:.2f}s")

                # Per-mode breakdown
                for mode in RETRIEVAL_MODES:
                    mode_results = [r for r in model_results if r["mode"] == mode]
                    if mode_results:
                        mode_success = sum(1 for r in mode_results if r["success"])
                        mode_rate = mode_success / len(mode_results) * 100
                        print(
                            f"    {mode.upper()}: {mode_success}/{len(mode_results)} ({mode_rate:.1f}%)"
                        )

        # Performance comparison
        print(f"\nPERFORMANCE RANKING:")
        print("-" * 40)

        # Performance ranking
        print(f"\nOVERALL RANKING:")
        print("-" * 40)

        model_performance = []
        for model_name in MODEL_NAMES:
            model_results = [
                r for r in results if r["model"] == model_name and r["success"]
            ]
            if model_results:
                avg_time = sum(r["execution_time"] for r in model_results) / len(
                    model_results
                )
                success_rate = len(model_results) / len(
                    [r for r in results if r["model"] == model_name]
                )
                score = success_rate / max(
                    avg_time, 0.1
                )  # Vermeide Division durch Null
                model_performance.append((model_name, avg_time, success_rate, score))

        model_performance.sort(key=lambda x: x[3], reverse=True)

        for i, (model, avg_time, success_rate, score) in enumerate(
            model_performance, 1
        ):
            print(f"{i}. {model}: {success_rate*100:.1f}% success, {avg_time:.1f}s avg")


def main():
    """Main function with configuration options."""
    import argparse

    parser = argparse.ArgumentParser(description="Optimized Retrieval Mode Test")
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Enable concurrent testing (rate-limit aware)",
    )
    parser.add_argument(
        "--workers", type=int, default=2, help="Max concurrent workers (default: 2)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per query in seconds (default: 120)",
    )

    args = parser.parse_args()

    # Validate worker count for concurrent mode
    if args.concurrent and args.workers > 3:
        logger.warning(
            f"High worker count ({args.workers}) may hit API rate limits. Recommended: 2-3"
        )
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            logger.info("Test cancelled")
            return

    runner = OptimizedRetrievalTestRunner(
        timeout_seconds=args.timeout,
        enable_concurrent=args.concurrent,
        max_workers=args.workers,
    )

    try:
        results = runner.run_optimized_test()
        if results:
            logger.info("✓ Optimized test completed successfully")
        else:
            logger.error("✗ Test failed")
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
