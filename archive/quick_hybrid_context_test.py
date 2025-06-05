#!/usr/bin/env python3
"""
Quick Hybrid Context Test
Simplified version of optimized_retrieval_test for testing hybrid context strategy.
- Single model (GPT-4)
- Reduced test set (5 queries instead of 11)
- 3 workers for faster execution
- Focus on hybrid context evaluation
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


def setup_logging(concurrent_mode=False, workers=1):
    """Setup logging to both console and file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_suffix = f"concurrent_{workers}w" if concurrent_mode else "sequential"
    log_filename = f"quick_hybrid_test_{mode_suffix}_{timestamp}.log"

    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting quick hybrid context test - Log file: {log_filename}")
    return logger, log_filename


# Reduced test set - 5 representative queries
TEST_QUERIES = [
    {
        "query": "Wer wohnt in der Marienstraße 26, 45307 Essen?",
        "description": "Specific address lookup",
        "expected_tables": ["BEWOHNER", "BEWADR"],
        "complexity": "basic",
    },
    {
        "query": "Wie viele Wohnungen gibt es insgesamt?",
        "description": "Simple count query",
        "expected_tables": ["WOHNUNG"],
        "complexity": "basic",
    },
    {
        "query": "Zeige mir Bewohner mit ihren Adressdaten für Objekt 5",
        "description": "Multi-table join",
        "expected_tables": ["BEWOHNER", "BEWADR", "OBJEKTE"],
        "complexity": "medium",
    },
    {
        "query": "Welche Eigentümer haben mehr als 2 Wohnungen?",
        "description": "Complex aggregation",
        "expected_tables": ["EIGENTUEMER", "VEREIG", "WOHNUNG"],
        "complexity": "complex",
    },
    {
        "query": "Durchschnittliche Miete pro Objekt",
        "description": "Financial aggregation",
        "expected_tables": ["BEWOHNER", "OBJEKTE"],
        "complexity": "medium",
    },
]

# Single model configuration - GPT-4 for consistent testing
MODEL_CONFIG = {
    "model_name": "openai/gpt-4",
    "provider": "openai",
    "temperature": 0.1,
    "max_tokens": 2000,
}

# Retrieval modes to test
RETRIEVAL_MODES = ["enhanced", "faiss", "none"]


class QuickHybridTester:
    """Quick tester for hybrid context strategy evaluation"""

    def __init__(self, logger, timeout_per_query=45, disable_phoenix=False):
        self.logger = logger
        self.timeout_per_query = timeout_per_query
        self.db_connection_string = (
            "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        )
        self.agents = {}  # Cache for reusing agents
        self.results = []
        self.disable_phoenix = disable_phoenix

    def initialize_agent(self, retrieval_mode: str):
        """Initialize agent for specific retrieval mode"""
        if retrieval_mode in self.agents:
            return self.agents[retrieval_mode]

        try:
            self.logger.info(f"Initializing agent for mode: {retrieval_mode}")

            # Import LLM
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-4",
                temperature=MODEL_CONFIG["temperature"],
                max_tokens=MODEL_CONFIG["max_tokens"],
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )

            agent = FirebirdDirectSQLAgent(
                db_connection_string=self.db_connection_string,
                llm=llm,
                retrieval_mode=retrieval_mode,
                use_enhanced_knowledge=True,  # Enable hybrid context
            )

            self.agents[retrieval_mode] = agent
            self.logger.info(f"✓ Agent initialized for {retrieval_mode}")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to initialize agent for {retrieval_mode}: {e}")
            return None

    def run_single_query(self, query_data: Dict, retrieval_mode: str) -> Dict[str, Any]:
        """Run a single query with specified retrieval mode"""
        query = query_data["query"]

        result = {
            "query": query,
            "description": query_data["description"],
            "complexity": query_data["complexity"],
            "retrieval_mode": retrieval_mode,
            "model": MODEL_CONFIG["model_name"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "response_time": 0.0,
            "error": None,
            "sql_query": None,
            "final_answer": None,
            "context_used": False,
        }

        try:
            agent = self.initialize_agent(retrieval_mode)
            if not agent:
                result["error"] = f"Failed to initialize agent for {retrieval_mode}"
                return result

            self.logger.info(f"🔍 Testing query: '{query}' with {retrieval_mode} mode")

            start_time = time.time()

            # Run query with timeout
            try:
                response = agent.query(query)
                result["response_time"] = time.time() - start_time

                if response and isinstance(response, dict):
                    result["success"] = True
                    result["final_answer"] = response.get("agent_final_answer", "")
                    result["sql_query"] = response.get("generated_sql", "")
                    result["context_used"] = bool(response.get("retrieved_context", ""))

                    # Extract some metrics
                    if result["final_answer"]:
                        result["answer_length"] = len(result["final_answer"])
                    if result["sql_query"]:
                        result["sql_length"] = len(result["sql_query"])
                        # Check if hybrid context features are used
                        sql_upper = result["sql_query"].upper()
                        result["uses_joins"] = "JOIN" in sql_upper
                        result["uses_aggregation"] = any(
                            agg in sql_upper
                            for agg in ["COUNT", "SUM", "AVG", "MAX", "MIN"]
                        )
                        result["table_count"] = len(
                            [
                                table
                                for table in [
                                    "BEWOHNER",
                                    "OBJEKTE",
                                    "KONTEN",
                                    "BEWADR",
                                    "EIGADR",
                                ]
                                if table in sql_upper
                            ]
                        )

                    self.logger.info(
                        f"✅ Query successful in {result['response_time']:.1f}s"
                    )

                else:
                    result["error"] = "Invalid or empty response from agent"
                    self.logger.warning(f"⚠️ Invalid response for query: {query}")

            except asyncio.TimeoutError:
                result["error"] = f"Query timed out after {self.timeout_per_query}s"
                result["response_time"] = self.timeout_per_query
                self.logger.warning(f"⏰ Timeout for query: {query}")

        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = (
                time.time() - start_time if "start_time" in locals() else 0
            )
            self.logger.error(f"❌ Error processing query '{query}': {e}")

        return result

    def run_concurrent_test(self, workers=3):
        """Run tests concurrently with specified number of workers"""
        self.logger.info(f"🔥 Starting concurrent test with {workers} workers")
        self.logger.info(f"Total queries: {len(TEST_QUERIES)}")
        self.logger.info(f"Total modes: {len(RETRIEVAL_MODES)}")
        self.logger.info(f"Total tests: {len(TEST_QUERIES) * len(RETRIEVAL_MODES)}")

        # Pre-initialize all agents
        self.logger.info("Pre-initializing agents...")
        for mode in RETRIEVAL_MODES:
            self.initialize_agent(mode)

        # Prepare all test combinations
        test_tasks = []
        for query_data in TEST_QUERIES:
            for mode in RETRIEVAL_MODES:
                test_tasks.append((query_data, mode))

        # Run tests concurrently
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {
                executor.submit(self.run_single_query, query_data, mode): (
                    query_data,
                    mode,
                )
                for query_data, mode in test_tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                query_data, mode = future_to_task[future]
                try:
                    result = future.result(timeout=self.timeout_per_query + 10)
                    self.results.append(result)

                    status = "✅" if result["success"] else "❌"
                    self.logger.info(
                        f"{status} {mode}: '{query_data['query'][:50]}...' "
                        f"({result['response_time']:.1f}s)"
                    )

                except Exception as e:
                    self.logger.error(f"❌ Task failed: {e}")
                    # Add failed result
                    failed_result = {
                        "query": query_data["query"],
                        "retrieval_mode": mode,
                        "success": False,
                        "error": str(e),
                        "response_time": 0.0,
                    }
                    self.results.append(failed_result)

        total_time = time.time() - start_time
        self.logger.info(f"🏁 All tests completed in {total_time:.1f}s")

        return self.results

    def run_sequential_test(self):
        """Run tests sequentially (fallback mode)"""
        self.logger.info("📝 Starting sequential test")
        self.logger.info(f"Total queries: {len(TEST_QUERIES)}")
        self.logger.info(f"Total modes: {len(RETRIEVAL_MODES)}")
        self.logger.info(f"Total tests: {len(TEST_QUERIES) * len(RETRIEVAL_MODES)}")

        start_time = time.time()

        for i, query_data in enumerate(TEST_QUERIES, 1):
            self.logger.info(
                f"\n--- Query {i}/{len(TEST_QUERIES)}: {query_data['description']} ---"
            )

            for j, mode in enumerate(RETRIEVAL_MODES, 1):
                self.logger.info(f"Mode {j}/{len(RETRIEVAL_MODES)}: {mode}")
                result = self.run_single_query(query_data, mode)
                self.results.append(result)

                status = "✅" if result["success"] else "❌"
                self.logger.info(
                    f"{status} Completed in {result['response_time']:.1f}s"
                )

        total_time = time.time() - start_time
        self.logger.info(f"🏁 All tests completed in {total_time:.1f}s")

        return self.results

    def analyze_results(self):
        """Analyze test results and generate summary"""
        if not self.results:
            self.logger.warning("No results to analyze")
            return {}

        analysis = {
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r["success"]]),
                "failed_tests": len([r for r in self.results if not r["success"]]),
                "overall_success_rate": 0.0,
                "average_response_time": 0.0,
            },
            "by_mode": {},
            "by_complexity": {},
            "hybrid_context_impact": {},
            "best_performing": {},
        }

        # Overall metrics
        successful_results = [r for r in self.results if r["success"]]
        analysis["summary"]["overall_success_rate"] = (
            len(successful_results) / len(self.results) * 100
        )
        if successful_results:
            analysis["summary"]["average_response_time"] = sum(
                r["response_time"] for r in successful_results
            ) / len(successful_results)

        # Analysis by retrieval mode
        for mode in RETRIEVAL_MODES:
            mode_results = [r for r in self.results if r["retrieval_mode"] == mode]
            mode_successful = [r for r in mode_results if r["success"]]

            analysis["by_mode"][mode] = {
                "total_tests": len(mode_results),
                "successful": len(mode_successful),
                "success_rate": (
                    len(mode_successful) / len(mode_results) * 100
                    if mode_results
                    else 0
                ),
                "avg_response_time": (
                    sum(r["response_time"] for r in mode_successful)
                    / len(mode_successful)
                    if mode_successful
                    else 0
                ),
                "context_usage": len(
                    [r for r in mode_successful if r.get("context_used", False)]
                ),
            }

        # Analysis by complexity
        for complexity in ["basic", "medium", "complex"]:
            complexity_results = [
                r for r in self.results if r.get("complexity") == complexity
            ]
            complexity_successful = [r for r in complexity_results if r["success"]]

            if complexity_results:
                analysis["by_complexity"][complexity] = {
                    "total_tests": len(complexity_results),
                    "successful": len(complexity_successful),
                    "success_rate": (
                        len(complexity_successful) / len(complexity_results) * 100
                    ),
                    "avg_response_time": (
                        sum(r["response_time"] for r in complexity_successful)
                        / len(complexity_successful)
                        if complexity_successful
                        else 0
                    ),
                }

        # Find best performing mode
        best_mode = None
        best_score = 0
        for mode, metrics in analysis["by_mode"].items():
            # Score = success_rate - normalized_response_time
            score = metrics["success_rate"] - (
                metrics["avg_response_time"] / 10
            )  # Penalize slow responses
            if score > best_score:
                best_score = score
                best_mode = mode

        analysis["best_performing"]["mode"] = best_mode
        analysis["best_performing"]["score"] = best_score

        return analysis

    def save_results(self, results, analysis, filename_prefix="quick_hybrid_test"):
        """Save results and analysis to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed results
        results_file = f"{filename_prefix}_results_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "model": MODEL_CONFIG["model_name"],
                        "test_type": "quick_hybrid_context_test",
                        "total_queries": len(TEST_QUERIES),
                        "retrieval_modes": RETRIEVAL_MODES,
                    },
                    "results": results,
                    "analysis": analysis,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Save readable summary
        summary_file = f"{filename_prefix}_summary_{timestamp}.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("# WINCASA Quick Hybrid Context Test Results\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Model: {MODEL_CONFIG['model_name']}\n\n")

            f.write("## Overall Summary\n")
            f.write(f"- Total tests: {analysis['summary']['total_tests']}\n")
            f.write(f"- Successful: {analysis['summary']['successful_tests']}\n")
            f.write(f"- Failed: {analysis['summary']['failed_tests']}\n")
            f.write(
                f"- Success rate: {analysis['summary']['overall_success_rate']:.1f}%\n"
            )
            f.write(
                f"- Average response time: {analysis['summary']['average_response_time']:.1f}s\n\n"
            )

            f.write("## Results by Retrieval Mode\n")
            for mode, metrics in analysis["by_mode"].items():
                f.write(f"### {mode.upper()}\n")
                f.write(f"- Success rate: {metrics['success_rate']:.1f}%\n")
                f.write(
                    f"- Average response time: {metrics['avg_response_time']:.1f}s\n"
                )
                f.write(f"- Context usage: {metrics['context_usage']} queries\n\n")

            f.write("## Best Performing Mode\n")
            f.write(
                f"**{analysis['best_performing']['mode'].upper()}** (score: {analysis['best_performing']['score']:.1f})\n\n"
            )

            f.write("## Hybrid Context Impact\n")
            context_users = len([r for r in results if r.get("context_used", False)])
            f.write(f"- Queries using context: {context_users}/{len(results)}\n")

        self.logger.info(f"📊 Results saved to: {results_file}")
        self.logger.info(f"📄 Summary saved to: {summary_file}")

        return results_file, summary_file


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Quick Hybrid Context Test for WINCASA"
    )
    parser.add_argument(
        "--concurrent", action="store_true", help="Run tests concurrently"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent workers (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Timeout per query in seconds (default: 45)",
    )
    parser.add_argument(
        "--disable-phoenix",
        action="store_true",
        help="Disable Phoenix monitoring for faster testing",
    )

    args = parser.parse_args()

    # Setup logging
    logger, log_file = setup_logging(args.concurrent, args.workers)

    logger.info("=" * 80)
    logger.info("WINCASA QUICK HYBRID CONTEXT TEST STARTED")
    logger.info("=" * 80)
    logger.info(f"Model: {MODEL_CONFIG['model_name']}")
    logger.info(f"Queries: {len(TEST_QUERIES)}")
    logger.info(f"Modes: {RETRIEVAL_MODES}")
    logger.info(f"Total tests: {len(TEST_QUERIES) * len(RETRIEVAL_MODES)}")
    logger.info(f"Timeout per query: {args.timeout}s")

    if args.concurrent:
        logger.info(f"🔥 CONCURRENT MODE: {args.workers} workers")
    else:
        logger.info("📝 SEQUENTIAL MODE")

    # Initialize tester
    tester = QuickHybridTester(logger, args.timeout, args.disable_phoenix)

    try:
        # Run tests
        if args.concurrent:
            results = tester.run_concurrent_test(args.workers)
        else:
            results = tester.run_sequential_test()

        # Analyze results
        analysis = tester.analyze_results()

        # Save results
        results_file, summary_file = tester.save_results(results, analysis)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETED - SUMMARY")
        logger.info("=" * 80)
        logger.info(
            f"📊 Success rate: {analysis['summary']['overall_success_rate']:.1f}%"
        )
        logger.info(
            f"⏱️  Average time: {analysis['summary']['average_response_time']:.1f}s"
        )
        logger.info(f"🏆 Best mode: {analysis['best_performing']['mode'].upper()}")

        # Mode comparison
        logger.info("\n📈 MODE COMPARISON:")
        for mode in RETRIEVAL_MODES:
            metrics = analysis["by_mode"][mode]
            logger.info(
                f"  {mode}: {metrics['success_rate']:.1f}% success, {metrics['avg_response_time']:.1f}s avg"
            )

        logger.info(f"\n📁 Detailed results: {results_file}")
        logger.info(f"📄 Summary report: {summary_file}")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
