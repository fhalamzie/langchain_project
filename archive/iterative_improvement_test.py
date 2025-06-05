"""
Iterative Improvement Test Framework for WINCASA Hybrid Context Strategy

This test framework implements the iterative testing approach described in implementation_plan.md
to progressively improve context quality and SQL generation accuracy.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from data_sampler import WincasaDataSampler

from global_context import get_compact_global_context, get_global_context_prompt


class IterativeImprovementTest:
    """
    Test framework for iteratively improving the hybrid context strategy.

    This implements the test-driven development approach from the implementation plan
    with feedback loops and continuous improvement tracking.
    """

    def __init__(self, output_dir: str = "output/iterative_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test queries organized by complexity
        self.test_queries = {
            "basic_lookups": [
                {
                    "query": "Wer wohnt in der Marienstraße 26?",
                    "expected_tables": ["BEWOHNER", "BEWADR"],
                    "expected_joins": ["BEWOHNER.BEWNR = BEWADR.BEWNR"],
                    "expected_fields": ["BSTR", "BVNAME", "BNAME"],
                    "description": "Basic address lookup for residents",
                },
                {
                    "query": "Wie viele Wohnungen gibt es insgesamt?",
                    "expected_tables": ["WOHNUNG"],
                    "expected_aggregation": "COUNT",
                    "description": "Simple count aggregation",
                },
                {
                    "query": "Zeige mir alle Eigentümer aus Köln",
                    "expected_tables": ["EIGENTUEMER", "EIGADR"],
                    "expected_joins": ["EIGENTUEMER.EIGNR = EIGADR.EIGNR"],
                    "expected_filters": [
                        "OPLZORT LIKE '%Köln%'",
                        "EPLZORT LIKE '%Köln%'",
                    ],
                    "description": "Filter owners by city",
                },
            ],
            "joins_required": [
                {
                    "query": "Welche Bewohner wohnen in Objekt ONR 1001?",
                    "expected_tables": ["BEWOHNER", "OBJEKTE"],
                    "expected_joins": ["BEWOHNER.ONR = OBJEKTE.ONR"],
                    "expected_filters": ["ONR = 1001"],
                    "description": "Join residents to specific property",
                },
                {
                    "query": "Zeige mir Bewohner mit ihren Adressdaten für Objekt 5",
                    "expected_tables": ["BEWOHNER", "BEWADR", "OBJEKTE"],
                    "expected_joins": [
                        "BEWOHNER.BEWNR = BEWADR.BEWNR",
                        "BEWOHNER.ONR = OBJEKTE.ONR",
                    ],
                    "expected_filters": ["OBJEKTE.ONR = 5"],
                    "description": "Multi-table join with address details",
                },
                {
                    "query": "Welche Konten gehören zu Objekt 4?",
                    "expected_tables": ["KONTEN", "OBJEKTE"],
                    "expected_joins": ["KONTEN.ONR = OBJEKTE.ONR"],
                    "expected_filters": ["OBJEKTE.ONR = 4"],
                    "description": "Account-to-property relationship",
                },
            ],
            "complex_business": [
                {
                    "query": "Welche Eigentümer haben mehr als 2 Wohnungen?",
                    "expected_tables": ["EIGENTUEMER", "VEREIG", "OBJEKTE", "WOHNUNG"],
                    "expected_joins": [
                        "EIGENTUEMER.EIGNR = VEREIG.EIGNR",
                        "VEREIG.ONR = OBJEKTE.ONR",
                    ],
                    "expected_aggregation": "COUNT(*) > 2",
                    "expected_groupby": "EIGENTUEMER.EIGNR",
                    "description": "Owner aggregation with business logic",
                },
                {
                    "query": "Zeige mir die Mieter die mehr als 1000 Euro Miete zahlen",
                    "expected_tables": ["BEWOHNER", "KONTEN", "BUCHUNG"],
                    "expected_joins": [
                        "BEWOHNER.KNR = KONTEN.KNR",
                        "KONTEN.KNR = BUCHUNG.KHABEN",
                    ],
                    "expected_filters": ["BETRAG > 1000"],
                    "description": "Financial data with amount filtering",
                },
            ],
            "aggregations": [
                {
                    "query": "Durchschnittliche Miete pro Objekt",
                    "expected_tables": ["BEWOHNER", "OBJEKTE"],
                    "expected_aggregation": "AVG(MIETE1)",
                    "expected_groupby": "OBJEKTE.ONR",
                    "description": "Average calculation grouped by property",
                },
                {
                    "query": "Gesamtanzahl der Bewohner pro Postleitzahl",
                    "expected_tables": ["BEWOHNER", "BEWADR"],
                    "expected_joins": ["BEWOHNER.BEWNR = BEWADR.BEWNR"],
                    "expected_aggregation": "COUNT(*)",
                    "expected_groupby": "BPLZORT",
                    "description": "Resident count by postal code",
                },
            ],
        }

        # Context versions to test
        self.context_versions = {
            "v1_global_only": {
                "description": "Global context only (baseline)",
                "use_global": True,
                "use_data_patterns": False,
                "use_retrieval": False,
            },
            "v2_global_plus_patterns": {
                "description": "Global context + data patterns",
                "use_global": True,
                "use_data_patterns": True,
                "use_retrieval": False,
            },
            "v3_hybrid_basic": {
                "description": "Global + patterns + basic retrieval",
                "use_global": True,
                "use_data_patterns": True,
                "use_retrieval": True,
                "retrieval_mode": "enhanced",
            },
            "v4_compact_optimized": {
                "description": "Compact global context + optimized retrieval",
                "use_global": "compact",
                "use_data_patterns": True,
                "use_retrieval": True,
                "retrieval_mode": "enhanced",
            },
        }

        self.iteration_results = []

    def load_data_patterns(self) -> str:
        """Load the data patterns summary from data sampling"""
        patterns_file = Path("output/data_context_summary.txt")
        if patterns_file.exists():
            return patterns_file.read_text(encoding="utf-8")
        return ""

    def generate_context_for_version(self, version_key: str, query: str) -> str:
        """Generate context prompt based on version configuration"""
        version_config = self.context_versions[version_key]
        context_parts = []

        # Add global context
        if version_config.get("use_global"):
            if version_config["use_global"] == "compact":
                context_parts.append(get_compact_global_context())
            else:
                context_parts.append(get_global_context_prompt())

        # Add data patterns
        if version_config.get("use_data_patterns"):
            data_patterns = self.load_data_patterns()
            if data_patterns:
                context_parts.append(data_patterns)

        # Add retrieval information (simulated for now)
        if version_config.get("use_retrieval"):
            retrieval_mode = version_config.get("retrieval_mode", "enhanced")
            context_parts.append(f"\n=== RETRIEVAL MODE: {retrieval_mode.upper()} ===")
            context_parts.append(
                "Additional context would be retrieved based on query analysis..."
            )
            context_parts.append("=== END RETRIEVAL ===")

        return "\n\n".join(context_parts)

    def evaluate_sql_quality(
        self, sql: str, expected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate generated SQL against expected criteria.
        Returns scores for different aspects (0-3 points each).
        """
        evaluation = {
            "sql_syntax": 0,
            "table_selection": 0,
            "join_logic": 0,
            "business_logic": 0,
            "result_accuracy": 0,
            "total_score": 0,
            "max_score": 15,
            "details": [],
        }

        sql_upper = sql.upper()

        # SQL Syntax (0-3 points)
        if "SELECT" in sql_upper and "FROM" in sql_upper:
            evaluation["sql_syntax"] = 2
            if not any(
                error in sql_upper for error in ["SYNTAX ERROR", "INVALID", "ERROR"]
            ):
                evaluation["sql_syntax"] = 3
        evaluation["details"].append(f"SQL Syntax: {evaluation['sql_syntax']}/3")

        # Table Selection (0-3 points)
        expected_tables = expected.get("expected_tables", [])
        if expected_tables:
            found_tables = sum(1 for table in expected_tables if table in sql_upper)
            evaluation["table_selection"] = min(
                3, (found_tables / len(expected_tables)) * 3
            )
        else:
            evaluation["table_selection"] = 3  # No specific tables expected
        evaluation["details"].append(
            f"Table Selection: {evaluation['table_selection']:.1f}/3"
        )

        # JOIN Logic (0-3 points)
        expected_joins = expected.get("expected_joins", [])
        if expected_joins:
            # Check for JOIN keywords and table relationships
            if "JOIN" in sql_upper or "WHERE" in sql_upper:
                evaluation["join_logic"] = 2
                # Check for proper relationships (simplified)
                if any("." in sql for sql in [sql]):  # Has table.column references
                    evaluation["join_logic"] = 3
            evaluation["details"].append(f"JOIN Logic: {evaluation['join_logic']}/3")
        else:
            evaluation["join_logic"] = 3  # No joins expected
            evaluation["details"].append(
                f"JOIN Logic: {evaluation['join_logic']}/3 (none required)"
            )

        # Business Logic (0-3 points)
        expected_filters = expected.get("expected_filters", [])
        expected_aggregation = expected.get("expected_aggregation", None)
        expected_groupby = expected.get("expected_groupby", None)

        business_score = 0
        if expected_filters and any(
            filter_term.split()[0] in sql_upper for filter_term in expected_filters
        ):
            business_score += 1
        if expected_aggregation and expected_aggregation.split("(")[0] in sql_upper:
            business_score += 1
        if expected_groupby and "GROUP BY" in sql_upper:
            business_score += 1
        if not expected_filters and not expected_aggregation and not expected_groupby:
            business_score = 3  # No complex business logic expected

        evaluation["business_logic"] = min(3, business_score)
        evaluation["details"].append(
            f"Business Logic: {evaluation['business_logic']}/3"
        )

        # Result Accuracy (0-3 points) - Placeholder for now
        # In a real implementation, this would execute the query and check results
        evaluation["result_accuracy"] = 2  # Assume reasonable accuracy for now
        evaluation["details"].append(
            f"Result Accuracy: {evaluation['result_accuracy']}/3 (estimated)"
        )

        # Calculate total
        evaluation["total_score"] = (
            evaluation["sql_syntax"]
            + evaluation["table_selection"]
            + evaluation["join_logic"]
            + evaluation["business_logic"]
            + evaluation["result_accuracy"]
        )

        return evaluation

    def simulate_sql_generation(self, context: str, query: str) -> str:
        """
        Simulate SQL generation (placeholder for actual LLM integration).
        In real implementation, this would call the actual SQL agent.
        """
        # This is a simplified simulation - in reality, you'd call the actual LLM
        # For now, return a reasonable SQL based on the query

        query_lower = query.lower()

        if "wer wohnt" in query_lower and "marienstraße" in query_lower:
            return """
            SELECT b.BVNAME, b.BNAME, ba.BSTR, ba.BPLZORT 
            FROM BEWOHNER b 
            JOIN BEWADR ba ON b.BEWNR = ba.BEWNR 
            WHERE ba.BSTR LIKE '%Marienstraße%'
            """

        elif "wie viele wohnungen" in query_lower:
            return "SELECT COUNT(*) FROM WOHNUNG"

        elif "eigentümer" in query_lower and "köln" in query_lower:
            return """
            SELECT e.*, ea.EPLZORT 
            FROM EIGENTUEMER e 
            JOIN EIGADR ea ON e.EIGNR = ea.EIGNR 
            WHERE ea.EPLZORT LIKE '%Köln%'
            """

        elif "bewohner" in query_lower and "objekt" in query_lower:
            return """
            SELECT b.BVNAME, b.BNAME, o.OBEZ 
            FROM BEWOHNER b 
            JOIN OBJEKTE o ON b.ONR = o.ONR 
            WHERE o.ONR = 5
            """

        elif "konten" in query_lower and "objekt" in query_lower:
            return """
            SELECT k.*, o.OBEZ 
            FROM KONTEN k 
            JOIN OBJEKTE o ON k.ONR = o.ONR 
            WHERE o.ONR = 4
            """

        elif "mehr als" in query_lower and "wohnungen" in query_lower:
            return """
            SELECT e.EIGNR, COUNT(*) as anzahl_wohnungen 
            FROM EIGENTUEMER e 
            JOIN VEREIG v ON e.EIGNR = v.EIGNR 
            JOIN WOHNUNG w ON v.ONR = w.ONR 
            GROUP BY e.EIGNR 
            HAVING COUNT(*) > 2
            """

        elif "durchschnittliche miete" in query_lower:
            return """
            SELECT o.ONR, o.OBEZ, AVG(b.MIETE1) as durchschnittsmiete 
            FROM OBJEKTE o 
            JOIN BEWOHNER b ON o.ONR = b.ONR 
            WHERE b.MIETE1 > 0 
            GROUP BY o.ONR, o.OBEZ
            """

        else:
            return f"-- Generated SQL for: {query}\nSELECT * FROM BEWOHNER LIMIT 10"

    def run_iteration(self, iteration_number: int, version_key: str) -> Dict[str, Any]:
        """Run a complete test iteration for a specific context version"""
        print(f"\n🔄 Running Iteration {iteration_number}: {version_key}")
        print(f"Description: {self.context_versions[version_key]['description']}")

        iteration_start = time.time()

        iteration_result = {
            "iteration": iteration_number,
            "version": version_key,
            "description": self.context_versions[version_key]["description"],
            "timestamp": datetime.now().isoformat(),
            "query_results": [],
            "summary": {
                "total_queries": 0,
                "total_score": 0,
                "max_possible_score": 0,
                "success_rate": 0.0,
                "average_score": 0.0,
                "category_scores": {},
            },
            "duration_seconds": 0.0,
            "improvements_needed": [],
            "best_practices_learned": [],
        }

        # Test all query categories
        for category, queries in self.test_queries.items():
            category_scores = []
            print(f"  📝 Testing {category} ({len(queries)} queries)")

            for query_data in queries:
                query = query_data["query"]
                print(f"    🔍 Testing: {query}")

                # Generate context for this version
                context = self.generate_context_for_version(version_key, query)

                # Generate SQL (simulated)
                start_time = time.time()
                generated_sql = self.simulate_sql_generation(context, query)
                generation_time = time.time() - start_time

                # Evaluate the generated SQL
                evaluation = self.evaluate_sql_quality(generated_sql, query_data)

                # Store result
                query_result = {
                    "query": query,
                    "description": query_data["description"],
                    "category": category,
                    "generated_sql": generated_sql.strip(),
                    "evaluation": evaluation,
                    "generation_time": generation_time,
                    "context_length": len(context),
                }

                iteration_result["query_results"].append(query_result)
                category_scores.append(evaluation["total_score"])

                print(
                    f"      Score: {evaluation['total_score']}/{evaluation['max_score']} points"
                )

            # Calculate category average
            if category_scores:
                avg_score = sum(category_scores) / len(category_scores)
                iteration_result["summary"]["category_scores"][category] = {
                    "average": avg_score,
                    "queries": len(category_scores),
                    "total": sum(category_scores),
                }

        # Calculate overall summary
        all_scores = [
            r["evaluation"]["total_score"] for r in iteration_result["query_results"]
        ]
        all_max_scores = [
            r["evaluation"]["max_score"] for r in iteration_result["query_results"]
        ]

        iteration_result["summary"]["total_queries"] = len(all_scores)
        iteration_result["summary"]["total_score"] = sum(all_scores)
        iteration_result["summary"]["max_possible_score"] = sum(all_max_scores)
        iteration_result["summary"]["average_score"] = (
            sum(all_scores) / len(all_scores) if all_scores else 0
        )
        iteration_result["summary"]["success_rate"] = (
            (sum(all_scores) / sum(all_max_scores)) if sum(all_max_scores) > 0 else 0
        )
        iteration_result["duration_seconds"] = time.time() - iteration_start

        # Identify improvements needed
        low_scores = [
            r
            for r in iteration_result["query_results"]
            if r["evaluation"]["total_score"] < 10
        ]
        for result in low_scores:
            iteration_result["improvements_needed"].append(
                {
                    "query": result["query"],
                    "score": result["evaluation"]["total_score"],
                    "issues": [
                        detail
                        for detail in result["evaluation"]["details"]
                        if "0" in detail or "1" in detail
                    ],
                }
            )

        # Identify best practices
        high_scores = [
            r
            for r in iteration_result["query_results"]
            if r["evaluation"]["total_score"] >= 12
        ]
        for result in high_scores:
            iteration_result["best_practices_learned"].append(
                {
                    "query": result["query"],
                    "score": result["evaluation"]["total_score"],
                    "sql_pattern": (
                        result["generated_sql"][:100] + "..."
                        if len(result["generated_sql"]) > 100
                        else result["generated_sql"]
                    ),
                }
            )

        print(f"  ✅ Iteration {iteration_number} completed:")
        print(
            f"     Success Rate: {iteration_result['summary']['success_rate']*100:.1f}%"
        )
        print(
            f"     Average Score: {iteration_result['summary']['average_score']:.1f}/15"
        )
        print(f"     Duration: {iteration_result['duration_seconds']:.1f}s")

        return iteration_result

    def run_full_test_cycle(self) -> str:
        """Run complete test cycle across all context versions"""
        print("🚀 Starting Iterative Improvement Test Cycle")
        print(f"Testing {len(self.context_versions)} context versions")
        print(
            f"Total queries: {sum(len(queries) for queries in self.test_queries.values())}"
        )

        # Run tests for each version
        for i, version_key in enumerate(self.context_versions.keys(), 1):
            iteration_result = self.run_iteration(i, version_key)
            self.iteration_results.append(iteration_result)

        # Generate comparison report
        report_path = self.generate_comparison_report()

        print(f"\n📊 Test cycle completed! Report saved to: {report_path}")
        return str(report_path)

    def generate_comparison_report(self) -> Path:
        """Generate comprehensive comparison report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"iterative_test_report_{timestamp}.json"

        # Create comparison summary
        comparison = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_versions_tested": len(self.iteration_results),
                "total_queries_per_version": sum(
                    len(queries) for queries in self.test_queries.values()
                ),
                "query_categories": list(self.test_queries.keys()),
            },
            "version_comparisons": [],
            "best_version": None,
            "recommendations": [],
            "detailed_results": self.iteration_results,
        }

        # Compare versions
        for result in self.iteration_results:
            version_summary = {
                "version": result["version"],
                "description": result["description"],
                "success_rate": result["summary"]["success_rate"],
                "average_score": result["summary"]["average_score"],
                "total_score": result["summary"]["total_score"],
                "duration": result["duration_seconds"],
                "strengths": [],
                "weaknesses": [],
            }

            # Identify strengths and weaknesses
            for category, scores in result["summary"]["category_scores"].items():
                if scores["average"] >= 12:
                    version_summary["strengths"].append(
                        f"Strong in {category} (avg: {scores['average']:.1f})"
                    )
                elif scores["average"] < 8:
                    version_summary["weaknesses"].append(
                        f"Weak in {category} (avg: {scores['average']:.1f})"
                    )

            comparison["version_comparisons"].append(version_summary)

        # Find best version
        best_result = max(
            self.iteration_results, key=lambda x: x["summary"]["success_rate"]
        )
        comparison["best_version"] = {
            "version": best_result["version"],
            "success_rate": best_result["summary"]["success_rate"],
            "reason": (
                f"Highest success rate of {best_result['summary']['success_rate']*100:.1f}%"
            ),
        }

        # Generate recommendations
        comparison["recommendations"] = self.generate_recommendations()

        # Save report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)

        # Also create a readable summary
        summary_file = self.output_dir / f"test_summary_{timestamp}.txt"
        self.create_readable_summary(comparison, summary_file)

        return report_file

    def generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on test results"""
        recommendations = []

        if not self.iteration_results:
            return ["No test results available for recommendations"]

        # Find common weak areas
        common_issues = {}
        for result in self.iteration_results:
            for improvement in result["improvements_needed"]:
                for issue in improvement["issues"]:
                    common_issues[issue] = common_issues.get(issue, 0) + 1

        # Top issues
        if common_issues:
            top_issue = max(common_issues.items(), key=lambda x: x[1])
            recommendations.append(
                f"Address recurring issue: {top_issue[0]} (appears in {top_issue[1]} test cases)"
            )

        # Performance recommendations
        avg_success_rate = sum(
            r["summary"]["success_rate"] for r in self.iteration_results
        ) / len(self.iteration_results)
        if avg_success_rate < 0.75:
            recommendations.append(
                "Overall success rate is below 75% - focus on improving basic query understanding"
            )

        # Context optimization
        best_version = max(
            self.iteration_results, key=lambda x: x["summary"]["success_rate"]
        )
        recommendations.append(
            f"Use '{best_version['version']}' as base configuration ({best_version['summary']['success_rate']*100:.1f}% success rate)"
        )

        if len(recommendations) == 0:
            recommendations.append(
                "All versions performing well - consider testing more complex scenarios"
            )

        return recommendations

    def create_readable_summary(self, comparison: Dict[str, Any], summary_file: Path):
        """Create a human-readable summary report"""
        lines = []
        lines.append("# WINCASA Iterative Improvement Test Results")
        lines.append(f"Generated: {comparison['test_metadata']['timestamp']}")
        lines.append("")

        lines.append("## Test Overview")
        lines.append(
            f"- Versions tested: {comparison['test_metadata']['total_versions_tested']}"
        )
        lines.append(
            f"- Queries per version: {comparison['test_metadata']['total_queries_per_version']}"
        )
        lines.append(
            f"- Categories: {', '.join(comparison['test_metadata']['query_categories'])}"
        )
        lines.append("")

        lines.append("## Version Comparison")
        for version in comparison["version_comparisons"]:
            lines.append(f"### {version['version']}")
            lines.append(f"**{version['description']}**")
            lines.append(f"- Success Rate: {version['success_rate']*100:.1f}%")
            lines.append(f"- Average Score: {version['average_score']:.1f}/15")
            lines.append(f"- Duration: {version['duration']:.1f}s")
            if version["strengths"]:
                lines.append(f"- Strengths: {', '.join(version['strengths'])}")
            if version["weaknesses"]:
                lines.append(f"- Weaknesses: {', '.join(version['weaknesses'])}")
            lines.append("")

        lines.append("## Best Version")
        best = comparison["best_version"]
        lines.append(f"**Winner: {best['version']}** - {best['reason']}")
        lines.append("")

        lines.append("## Recommendations")
        for i, rec in enumerate(comparison["recommendations"], 1):
            lines.append(f"{i}. {rec}")

        summary_file.write_text("\n".join(lines), encoding="utf-8")


def main():
    """Main function to run the iterative improvement test"""
    print("🧪 WINCASA Iterative Improvement Test Framework")

    tester = IterativeImprovementTest()
    report_path = tester.run_full_test_cycle()

    print(f"\n✅ Testing completed successfully!")
    print(f"📄 Full report: {report_path}")
    print(f"📁 All files in: {tester.output_dir}")


if __name__ == "__main__":
    main()
