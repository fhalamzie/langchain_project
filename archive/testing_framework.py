"""
WINCASA Testing Framework - Comprehensive Multi-Level Testing System

This module provides three levels of testing for WINCASA retrieval modes:
a) Quick Test - Basic functionality verification
b) Extensive Test - Comprehensive failure detection
c) Baseline Test - Performance comparison with detailed reporting

Author: WINCASA Development Team
Date: 2025-01-06
"""

import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import WINCASA modules
from firebird_sql_agent_direct import FirebirdDirectSQLAgent
from llm_interface import get_llm_client


@dataclass
class TestResult:
    """Individual test result container"""

    query: str
    mode: str
    success: bool
    response: str
    sql_generated: Optional[str]
    execution_time: float
    error_message: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class TestSummary:
    """Test run summary statistics"""

    total_tests: int
    successful_tests: int
    failed_tests: int
    success_rate: float
    average_execution_time: float
    total_execution_time: float
    mode: str
    test_level: str
    timestamp: str


class WincasaTestingFramework:
    """
    Comprehensive testing framework for WINCASA retrieval modes

    Supports three testing levels:
    - Quick: Basic functionality check (5 simple queries)
    - Extensive: Comprehensive failure detection (20+ diverse queries)
    - Baseline: Performance comparison baseline (50+ queries with detailed reporting)
    """

    def __init__(
        self, db_path: str = "/home/projects/langchain_project/WINCASA2022.FDB"
    ):
        self.db_path = db_path
        self.llm = get_llm_client()
        self.results: List[TestResult] = []
        self.test_data = self._load_test_queries()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def _load_test_queries(self) -> Dict[str, List[str]]:
        """Load test queries organized by complexity level"""
        return {
            "quick": [
                "Wie viele Wohnungen gibt es insgesamt?",
                "Zeige die ersten 2 Eigentümer",
                "Wie viele Bewohner gibt es?",
                "Liste alle Objekte auf",
                "Zeige mir die ersten 3 Konten",
            ],
            "extensive": [
                # Basic queries
                "Wie viele Wohnungen gibt es insgesamt?",
                "Zeige die ersten 5 Eigentümer",
                "Wie viele Bewohner gibt es?",
                "Liste die ersten 10 Objekte auf",
                # Address-based queries
                "Wer wohnt in der Marienstraße 26?",
                "Zeige alle Bewohner in Essen",
                "Welche Eigentümer wohnen in Köln?",
                "Finde Bewohner mit Postleitzahl 45307",
                # JOIN queries
                "Zeige Bewohner mit ihren Adressdaten",
                "Welche Bewohner wohnen in Objekt ONR 1001?",
                "Zeige Eigentümer mit ihren Objekten",
                "Liste Bewohner mit Objektadressen auf",
                # Financial queries
                "Zeige alle Konten für Objekt ONR 1001",
                "Welche Sollstellungen gibt es?",
                "Zeige Buchungen für Konto KNR 1",
                "Finde alle Kreditkonten",
                # Complex business logic
                "Welche Eigentümer haben mehr als 2 Objekte?",
                "Zeige leerstehende Wohnungen",
                "Finde Bewohner ohne gültige Adresse",
                "Welche Objekte haben keine aktiven Bewohner?",
                # Aggregation queries
                "Durchschnittliche Anzahl Bewohner pro Objekt",
                "Summe aller Sollstellungen",
                "Anzahl Konten pro Objekt",
                "Höchste Buchungssumme finden",
            ],
            "baseline": [
                # All extensive queries plus additional edge cases
                # Basic functionality
                "Wie viele Wohnungen gibt es insgesamt?",
                "Zeige die ersten 5 Eigentümer mit Details",
                "Wie viele aktive Bewohner gibt es?",
                "Liste die ersten 10 Objekte mit ONR auf",
                "Zeige mir alle verfügbaren Tabellen",
                # Address and location queries
                "Wer wohnt in der Marienstraße 26, 45307 Essen?",
                "Zeige alle Bewohner in Essen mit Adresse",
                "Welche Eigentümer wohnen in Köln oder Düsseldorf?",
                "Finde alle Bewohner mit Postleitzahl zwischen 45000 und 46000",
                "Zeige Objekte in der Bahnhofstraße",
                # Relationship and JOIN queries
                "Zeige Bewohner mit ihren vollständigen Adressdaten",
                "Welche Bewohner wohnen in Objekten von Eigentümer ENR 1?",
                "Zeige alle Eigentümer mit ihren Objekten und Adressen",
                "Liste Bewohner mit Objekt- und Eigentumsadresse auf",
                "Finde alle Verwalter mit ihren verwalteten Objekten",
                # Financial and accounting queries
                "Zeige alle Konten für Objekt ONR 1001 mit Salden",
                "Welche Sollstellungen sind über 1000 Euro?",
                "Zeige alle Buchungen der letzten 6 Monate",
                "Finde alle offenen Kreditkonten mit Beträgen",
                "Welche Objekte haben negative Kontensalden?",
                # Complex business logic queries
                "Welche Eigentümer besitzen mehr als 2 Wohnungen?",
                "Zeige alle leerstehenden Wohnungen mit Objektdetails",
                "Finde Bewohner ohne registrierte Mietverträge",
                "Welche Objekte haben mehr als 5 Bewohner?",
                "Zeige Eigentümer mit mehreren Objekten in verschiedenen Städten",
                # Aggregation and calculation queries
                "Berechne die durchschnittliche Miete pro Objekt",
                "Summe aller offenen Forderungen pro Eigentümer",
                "Anzahl Wohnungen pro Objekt durchschnittlich",
                "Höchste und niedrigste Buchungsbeträge finden",
                "Durchschnittliche Bewohneranzahl pro Postleitzahl",
                # Advanced and edge case queries
                "Finde Objekte ohne zugeordnete Eigentümer",
                "Zeige Bewohner mit mehreren Wohnungen",
                "Welche Konten haben keine Buchungen?",
                "Finde Objekte mit unvollständigen Adressdaten",
                "Zeige Duplikate in Bewohnerdaten",
                # Time-based and conditional queries
                "Zeige Bewohner die vor 2020 eingezogen sind",
                "Finde Buchungen mit negativen Beträgen",
                "Welche Sollstellungen sind überfällig?",
                "Zeige neue Bewohner der letzten 12 Monate",
                "Finde alle Änderungen an Eigentümerdaten",
                # Multi-table complex queries
                "Erstelle eine Übersicht: Objekt -> Eigentümer -> Bewohner -> Konten",
                "Zeige Cashflow-Analyse pro Objekt",
                "Finde problematische Konten mit mehreren offenen Sollstellungen",
                "Erstelle Bewohner-Eigentümer-Zuordnungsreport",
                "Analysiere Leerstandsquote nach Stadtteilen",
            ],
        }

    def _create_agent(self, mode: str) -> FirebirdDirectSQLAgent:
        """Create agent instance for specific retrieval mode"""
        return FirebirdDirectSQLAgent(
            db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
            llm=self.llm,
            retrieval_mode=mode,
            use_enhanced_knowledge=True,
        )

    def _execute_single_test(
        self, query: str, mode: str, timeout: int = 45
    ) -> TestResult:
        """Execute a single test query with specified mode and timeout"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()

        try:
            agent = self._create_agent(mode)
            response = agent.run(query)

            # Extract SQL if present in response
            sql_generated = None
            if "SELECT" in response.upper():
                # Simple extraction - could be enhanced
                lines = response.split("\n")
                for line in lines:
                    if line.strip().upper().startswith("SELECT"):
                        sql_generated = line.strip()
                        break

            execution_time = time.time() - start_time

            return TestResult(
                query=query,
                mode=mode,
                success=True,
                response=response,
                sql_generated=sql_generated,
                execution_time=execution_time,
                error_message=None,
                timestamp=timestamp,
                metadata={"timeout": timeout, "agent_type": type(agent).__name__},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"

            self.logger.error(
                f"Test failed for query '{query}' in mode '{mode}': {error_msg}"
            )

            return TestResult(
                query=query,
                mode=mode,
                success=False,
                response="",
                sql_generated=None,
                execution_time=execution_time,
                error_message=error_msg,
                timestamp=timestamp,
                metadata={"timeout": timeout, "traceback": traceback.format_exc()},
            )

    def run_quick_test(self, modes: List[str] = None) -> Dict[str, TestSummary]:
        """
        Quick test - Basic functionality verification
        Tests 5 simple queries across specified modes
        """
        if modes is None:
            modes = ["enhanced", "faiss", "none"]

        self.logger.info(f"Starting QUICK test for modes: {modes}")
        results = {}
        queries = self.test_data["quick"]

        for mode in modes:
            self.logger.info(f"Testing mode: {mode}")
            mode_results = []

            for query in queries:
                result = self._execute_single_test(query, mode, timeout=30)
                mode_results.append(result)
                self.results.append(result)

            summary = self._create_summary(mode_results, mode, "quick")
            results[mode] = summary

            self.logger.info(f"Mode {mode}: {summary.success_rate:.1%} success rate")

        return results

    def run_extensive_test(
        self, modes: List[str] = None, concurrent: bool = True
    ) -> Dict[str, TestSummary]:
        """
        Extensive test - Comprehensive failure detection
        Tests 20+ diverse queries to find edge cases and failures
        """
        if modes is None:
            modes = ["enhanced", "faiss", "none", "sqlcoder", "langchain"]

        self.logger.info(f"Starting EXTENSIVE test for modes: {modes}")
        results = {}
        queries = self.test_data["extensive"]

        for mode in modes:
            self.logger.info(f"Testing mode: {mode} with {len(queries)} queries")

            if concurrent:
                mode_results = self._run_concurrent_tests(queries, mode, timeout=60)
            else:
                mode_results = []
                for i, query in enumerate(queries, 1):
                    self.logger.info(f"Query {i}/{len(queries)}: {query[:50]}...")
                    result = self._execute_single_test(query, mode, timeout=60)
                    mode_results.append(result)
                    self.results.append(result)

            summary = self._create_summary(mode_results, mode, "extensive")
            results[mode] = summary

            self.logger.info(
                f"Mode {mode}: {summary.success_rate:.1%} success rate, "
                f"avg time: {summary.average_execution_time:.1f}s"
            )

        return results

    def run_baseline_test(
        self, modes: List[str] = None, concurrent: bool = True
    ) -> Dict[str, Any]:
        """
        Baseline test - Performance comparison with detailed reporting
        Tests 50+ queries with comprehensive analysis and comparison reports
        """
        if modes is None:
            modes = ["enhanced", "faiss", "none", "sqlcoder", "langchain"]

        self.logger.info(f"Starting BASELINE test for modes: {modes}")
        results = {}
        queries = self.test_data["baseline"]

        # Detailed results for comparison report
        detailed_results = []

        for mode in modes:
            self.logger.info(f"Testing mode: {mode} with {len(queries)} queries")

            if concurrent:
                mode_results = self._run_concurrent_tests(queries, mode, timeout=90)
            else:
                mode_results = []
                for i, query in enumerate(queries, 1):
                    self.logger.info(f"Query {i}/{len(queries)}: {query[:50]}...")
                    result = self._execute_single_test(query, mode, timeout=90)
                    mode_results.append(result)
                    self.results.append(result)

            # Add to detailed results for comparison
            for result in mode_results:
                detailed_results.append(result)

            summary = self._create_summary(mode_results, mode, "baseline")
            results[mode] = summary

            self.logger.info(
                f"Mode {mode}: {summary.success_rate:.1%} success rate, "
                f"avg time: {summary.average_execution_time:.1f}s"
            )

        # Generate detailed comparison report
        comparison_report = self._generate_comparison_report(detailed_results, modes)

        return {
            "summaries": results,
            "detailed_comparison": comparison_report,
            "raw_results": detailed_results,
        }

    def _run_concurrent_tests(
        self, queries: List[str], mode: str, timeout: int
    ) -> List[TestResult]:
        """Run tests concurrently for better performance"""
        mode_results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_query = {
                executor.submit(self._execute_single_test, query, mode, timeout): query
                for query in queries
            }

            for future in as_completed(future_to_query):
                result = future.result()
                mode_results.append(result)
                self.results.append(result)

        return mode_results

    def _create_summary(
        self, results: List[TestResult], mode: str, test_level: str
    ) -> TestSummary:
        """Create summary statistics for test results"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0

        execution_times = [r.execution_time for r in results]
        average_execution_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0
        )
        total_execution_time = sum(execution_times)

        return TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            total_execution_time=total_execution_time,
            mode=mode,
            test_level=test_level,
            timestamp=datetime.now().isoformat(),
        )

    def _generate_comparison_report(
        self, results: List[TestResult], modes: List[str]
    ) -> Dict[str, Any]:
        """Generate detailed comparison report for baseline testing"""

        # Group results by query for comparison
        query_comparison = {}
        for result in results:
            if result.query not in query_comparison:
                query_comparison[result.query] = {}
            query_comparison[result.query][result.mode] = result

        # Create comparison matrix
        comparison_matrix = []
        for query, mode_results in query_comparison.items():
            row = {"query": query}
            for mode in modes:
                if mode in mode_results:
                    result = mode_results[mode]
                    row[f"{mode}_success"] = result.success
                    row[f"{mode}_time"] = round(result.execution_time, 2)
                    row[f"{mode}_response"] = (
                        result.response[:100] + "..."
                        if len(result.response) > 100
                        else result.response
                    )
                    row[f"{mode}_sql"] = result.sql_generated or "N/A"
                else:
                    row[f"{mode}_success"] = False
                    row[f"{mode}_time"] = 0
                    row[f"{mode}_response"] = "Not tested"
                    row[f"{mode}_sql"] = "N/A"
            comparison_matrix.append(row)

        # Performance statistics by mode
        mode_stats = {}
        for mode in modes:
            mode_results = [r for r in results if r.mode == mode]
            if mode_results:
                mode_stats[mode] = {
                    "success_rate": (
                        sum(1 for r in mode_results if r.success) / len(mode_results)
                    ),
                    "avg_time": (
                        sum(r.execution_time for r in mode_results) / len(mode_results)
                    ),
                    "min_time": min(r.execution_time for r in mode_results),
                    "max_time": max(r.execution_time for r in mode_results),
                    "total_queries": len(mode_results),
                    "successful_queries": sum(1 for r in mode_results if r.success),
                    "failed_queries": sum(1 for r in mode_results if not r.success),
                }

        return {
            "query_comparison_matrix": comparison_matrix,
            "mode_performance_stats": mode_stats,
            "overall_stats": {
                "total_queries_tested": len(set(r.query for r in results)),
                "total_mode_query_combinations": len(results),
                "overall_success_rate": (
                    sum(1 for r in results if r.success) / len(results)
                ),
                "test_duration": (
                    max(results, key=lambda x: x.execution_time).execution_time
                    if results
                    else 0
                ),
            },
        }

    def save_results(
        self, filename: str = None, test_level: str = "comprehensive"
    ) -> str:
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wincasa_test_results_{test_level}_{timestamp}.json"

        output_data = {
            "test_metadata": {
                "test_level": test_level,
                "timestamp": datetime.now().isoformat(),
                "total_results": len(self.results),
                "framework_version": "1.0.0",
            },
            "results": [asdict(result) for result in self.results],
        }

        output_path = Path("output") / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Results saved to: {output_path}")
        return str(output_path)

    def generate_html_report(
        self, baseline_results: Dict[str, Any], filename: str = None
    ) -> str:
        """Generate HTML report for baseline test results with comparison matrix"""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wincasa_baseline_report_{timestamp}.html"

        # Create DataFrame for easier HTML generation
        comparison_df = pd.DataFrame(
            baseline_results["detailed_comparison"]["query_comparison_matrix"]
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WINCASA Baseline Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .mode-stats {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .mode-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; min-width: 200px; }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .query-cell {{ max-width: 300px; word-wrap: break-word; }}
                .response-cell {{ max-width: 200px; word-wrap: break-word; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>WINCASA Baseline Test Report</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="summary">
                <h2>Overall Statistics</h2>
                <p><strong>Total Queries:</strong> {baseline_results["detailed_comparison"]["overall_stats"]["total_queries_tested"]}</p>
                <p><strong>Overall Success Rate:</strong> {baseline_results["detailed_comparison"]["overall_stats"]["overall_success_rate"]:.1%}</p>
            </div>
            
            <div class="mode-stats">
                <h2>Mode Performance Summary</h2>
        """

        # Add mode statistics cards
        for mode, stats in baseline_results["detailed_comparison"][
            "mode_performance_stats"
        ].items():
            html_content += f"""
                <div class="mode-card">
                    <h3>{mode.upper()}</h3>
                    <p><strong>Success Rate:</strong> <span class="{'success' if stats['success_rate'] > 0.7 else 'failure'}">{stats['success_rate']:.1%}</span></p>
                    <p><strong>Avg Time:</strong> {stats['avg_time']:.1f}s</p>
                    <p><strong>Successful:</strong> {stats['successful_queries']}/{stats['total_queries']}</p>
                </div>
            """

        html_content += """
            </div>
            
            <h2>Detailed Query Comparison</h2>
            <table>
                <thead>
                    <tr>
                        <th class="query-cell">Query</th>
        """

        # Add column headers for each mode
        modes = list(baseline_results["summaries"].keys())
        for mode in modes:
            html_content += f"""
                        <th>{mode.upper()}<br>Success</th>
                        <th>{mode.upper()}<br>Time (s)</th>
                        <th class="response-cell">{mode.upper()}<br>Response</th>
            """

        html_content += """
                    </tr>
                </thead>
                <tbody>
        """

        # Add data rows
        for row in baseline_results["detailed_comparison"]["query_comparison_matrix"]:
            html_content += f"""
                    <tr>
                        <td class="query-cell">{row['query']}</td>
            """

            for mode in modes:
                success_key = f"{mode}_success"
                time_key = f"{mode}_time"
                response_key = f"{mode}_response"

                success = row.get(success_key, False)
                time_val = row.get(time_key, 0)
                response = row.get(response_key, "N/A")

                success_class = "success" if success else "failure"
                success_text = "✓" if success else "✗"

                html_content += f"""
                        <td class="{success_class}">{success_text}</td>
                        <td>{time_val}</td>
                        <td class="response-cell">{response}</td>
                """

            html_content += "</tr>"

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """

        output_path = Path("output") / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"HTML report saved to: {output_path}")
        return str(output_path)


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="WINCASA Testing Framework")
    parser.add_argument(
        "--level",
        choices=["quick", "extensive", "baseline"],
        default="quick",
        help="Test level to run",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["enhanced", "faiss", "none"],
        help="Retrieval modes to test",
    )
    parser.add_argument(
        "--concurrent", action="store_true", help="Run tests concurrently"
    )
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument(
        "--html", action="store_true", help="Generate HTML report (baseline only)"
    )

    args = parser.parse_args()

    framework = WincasaTestingFramework()

    if args.level == "quick":
        results = framework.run_quick_test(args.modes)
        print("\n=== QUICK TEST RESULTS ===")
        for mode, summary in results.items():
            print(
                f"{mode.upper()}: {summary.success_rate:.1%} success rate, "
                f"avg time: {summary.average_execution_time:.1f}s"
            )

    elif args.level == "extensive":
        results = framework.run_extensive_test(args.modes, args.concurrent)
        print("\n=== EXTENSIVE TEST RESULTS ===")
        for mode, summary in results.items():
            print(
                f"{mode.upper()}: {summary.success_rate:.1%} success rate, "
                f"avg time: {summary.average_execution_time:.1f}s, "
                f"{summary.failed_tests} failures"
            )

    elif args.level == "baseline":
        results = framework.run_baseline_test(args.modes, args.concurrent)
        print("\n=== BASELINE TEST RESULTS ===")
        for mode, summary in results["summaries"].items():
            print(
                f"{mode.upper()}: {summary.success_rate:.1%} success rate, "
                f"avg time: {summary.average_execution_time:.1f}s"
            )

        if args.html:
            html_file = framework.generate_html_report(results, args.output)
            print(f"\nHTML report generated: {html_file}")

    # Save results
    output_file = framework.save_results(args.output, args.level)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
