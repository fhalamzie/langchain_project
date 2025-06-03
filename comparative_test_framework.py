#!/usr/bin/env python3
"""
Comparative Test Framework for SQLAlchemy vs Direct FDB Approaches

This module provides a comprehensive testing framework to compare the performance,
reliability, and functionality of the SQLAlchemy-based approach versus the direct
FDB interface approach for the WINCASA database system.
"""

import time
import traceback
import statistics
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from contextlib import contextmanager

# Import both approaches
try:
    from firebird_sql_agent import FirebirdDocumentedSQLAgent as SQLAlchemyAgent
except ImportError:
    SQLAlchemyAgent = None
    
from firebird_sql_agent_direct import FirebirdDirectSQLAgent as DirectFDBAgent
from fdb_direct_interface import FDBDirectInterface


@dataclass
class TestResult:
    """Container for individual test results"""
    test_name: str
    approach: str
    success: bool
    execution_time: float
    error: Optional[str] = None
    result_data: Optional[Any] = None
    memory_usage: Optional[float] = None
    
    
@dataclass 
class TestSuite:
    """Collection of test results with summary statistics"""
    name: str
    results: List[TestResult] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for the test suite"""
        if not self.results:
            return {"error": "No test results"}
            
        sqlalchemy_results = [r for r in self.results if r.approach == "SQLAlchemy"]
        direct_results = [r for r in self.results if r.approach == "DirectFDB"]
        
        def calc_stats(results: List[TestResult]) -> Dict[str, Any]:
            if not results:
                return {"count": 0}
                
            success_count = sum(1 for r in results if r.success)
            times = [r.execution_time for r in results if r.success]
            
            return {
                "count": len(results),
                "success_count": success_count,
                "success_rate": success_count / len(results) * 100,
                "avg_time": statistics.mean(times) if times else 0,
                "median_time": statistics.median(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0
            }
            
        return {
            "suite_name": self.name,
            "total_tests": len(self.results),
            "sqlalchemy": calc_stats(sqlalchemy_results),
            "direct_fdb": calc_stats(direct_results),
            "timestamp": datetime.now().isoformat()
        }


class ComparativeTestFramework:
    """Main test framework for comparing database access approaches"""
    
    def __init__(self, db_path: str = "WINCASA2022.FDB"):
        self.db_path = db_path
        # Use the same format as expected by the agents
        self.connection_string = f"firebird+fdb://sysdba:masterkey@localhost/{os.path.abspath(db_path)}"
        self.test_suites: List[TestSuite] = []
        
        # Initialize agents
        self.direct_agent = None
        self.sqlalchemy_agent = None
        self.llm = None
        
    def _setup_llm(self):
        """Setup LLM for agents"""
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        
        # Load OpenAI API key
        load_dotenv('/home/envs/openai.env')
        
        # Try OpenRouter first, then fall back to direct OpenAI
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        
        if os.getenv('OPENROUTER_API_KEY'):
            self.llm = ChatOpenAI(
                model="openai/gpt-4o",
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0
            )
            print("✓ Using OpenRouter API")
        else:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                api_key=api_key,
                temperature=0
            )
            print("✓ Using direct OpenAI API")
        
    def setup(self):
        """Initialize both agents"""
        print("Setting up test agents...")
        
        # Setup LLM first
        self._setup_llm()
        
        if not self.llm:
            print("✗ Failed to initialize LLM")
            return
        
        # Setup Direct FDB Agent
        try:
            self.direct_agent = DirectFDBAgent(
                db_connection_string=self.connection_string,
                llm=self.llm,
                retrieval_mode='faiss'
            )
            print("✓ Direct FDB Agent initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Direct FDB Agent: {e}")
            self.direct_agent = None
            
        # Setup SQLAlchemy Agent (if available)
        if SQLAlchemyAgent:
            try:
                self.sqlalchemy_agent = SQLAlchemyAgent(
                    db_connection_string=self.connection_string,
                    llm=self.llm,
                    retrieval_mode='faiss'
                )
                print("✓ SQLAlchemy Agent initialized successfully")
            except Exception as e:
                print(f"✗ Failed to initialize SQLAlchemy Agent: {e}")
                self.sqlalchemy_agent = None
        else:
            print("✗ SQLAlchemy Agent not available (import failed)")
            
    @contextmanager
    def timer(self) -> float:
        """Context manager for timing operations"""
        start = time.time()
        yield lambda: time.time() - start
        
    def run_test(self, test_name: str, test_func, agent, approach: str) -> TestResult:
        """Run a single test and capture results"""
        if agent is None:
            return TestResult(
                test_name=test_name,
                approach=approach,
                success=False,
                execution_time=0,
                error="Agent not initialized"
            )
            
        try:
            with self.timer() as get_time:
                result = test_func(agent)
                
            return TestResult(
                test_name=test_name,
                approach=approach,
                success=True,
                execution_time=get_time(),
                result_data=result
            )
        except Exception as e:
            return TestResult(
                test_name=test_name,
                approach=approach,
                success=False,
                execution_time=get_time() if 'get_time' in locals() else 0,
                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            
    def run_comparison_test(self, test_name: str, test_func) -> Tuple[TestResult, TestResult]:
        """Run the same test on both approaches"""
        direct_result = self.run_test(test_name, test_func, self.direct_agent, "DirectFDB")
        sqlalchemy_result = self.run_test(test_name, test_func, self.sqlalchemy_agent, "SQLAlchemy")
        
        return direct_result, sqlalchemy_result
        
    # Test Cases
    
    def test_simple_query(self, agent) -> Dict[str, Any]:
        """Test a simple SELECT query"""
        query = "Zeige mir alle Bewohner"
        result = agent.query(query)
        return {
            "query": query,
            "sql": result.get("sql", ""),
            "row_count": len(result.get("result", [])) if result.get("result") else 0
        }
        
    def test_join_query(self, agent) -> Dict[str, Any]:
        """Test a query with JOIN operations"""
        query = "Welche Bewohner leben in der Marienstraße?"
        result = agent.query(query)
        return {
            "query": query,
            "sql": result.get("sql", ""),
            "row_count": len(result.get("result", [])) if result.get("result") else 0
        }
        
    def test_aggregation_query(self, agent) -> Dict[str, Any]:
        """Test a query with aggregation"""
        query = "Wie viele Wohnungen gibt es pro Gebäude?"
        result = agent.query(query)
        return {
            "query": query,
            "sql": result.get("sql", ""),
            "row_count": len(result.get("result", [])) if result.get("result") else 0
        }
        
    def test_complex_query(self, agent) -> Dict[str, Any]:
        """Test a complex query with multiple conditions"""
        query = "Zeige mir alle Eigentümer mit ihren Bankverbindungen, die in Berlin wohnen"
        result = agent.query(query)
        return {
            "query": query,
            "sql": result.get("sql", ""),
            "row_count": len(result.get("result", [])) if result.get("result") else 0
        }
        
    def test_schema_info(self, agent) -> Dict[str, Any]:
        """Test schema information retrieval"""
        if hasattr(agent, 'db_interface') and hasattr(agent.db_interface, 'get_table_names'):
            # Direct FDB approach
            tables = agent.db_interface.get_table_names()
        else:
            # SQLAlchemy approach - would need different method
            tables = []
            
        return {
            "table_count": len(tables),
            "sample_tables": tables[:5] if tables else []
        }
        
    def test_concurrent_queries(self, agent, num_queries: int = 5) -> Dict[str, Any]:
        """Test multiple queries in sequence"""
        queries = [
            "Zeige mir alle Bewohner",
            "Liste alle Gebäude auf",
            "Welche Wohnungen sind verfügbar?",
            "Zeige alle Eigentümer",
            "Liste alle Bankverbindungen"
        ]
        
        results = []
        total_time = 0
        
        for query in queries[:num_queries]:
            start = time.time()
            try:
                result = agent.query(query)
                success = True
            except Exception as e:
                success = False
                result = {"error": str(e)}
                
            elapsed = time.time() - start
            total_time += elapsed
            results.append({
                "query": query,
                "success": success,
                "time": elapsed
            })
            
        return {
            "total_queries": num_queries,
            "total_time": total_time,
            "avg_time": total_time / num_queries,
            "results": results
        }
        
    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*60)
        print("Running Comparative Tests: SQLAlchemy vs Direct FDB")
        print("="*60 + "\n")
        
        # Basic functionality tests
        basic_suite = TestSuite("Basic Functionality")
        
        tests = [
            ("Simple Query", self.test_simple_query),
            ("Join Query", self.test_join_query),
            ("Aggregation Query", self.test_aggregation_query),
            ("Complex Query", self.test_complex_query),
            ("Schema Information", self.test_schema_info)
        ]
        
        for test_name, test_func in tests:
            print(f"\nRunning: {test_name}")
            direct_result, sqlalchemy_result = self.run_comparison_test(test_name, test_func)
            
            basic_suite.add_result(direct_result)
            basic_suite.add_result(sqlalchemy_result)
            
            # Print immediate results
            print(f"  Direct FDB: {'✓' if direct_result.success else '✗'} ({direct_result.execution_time:.3f}s)")
            print(f"  SQLAlchemy: {'✓' if sqlalchemy_result.success else '✗'} ({sqlalchemy_result.execution_time:.3f}s)")
            
            if not direct_result.success:
                print(f"    Direct Error: {direct_result.error.split(chr(10))[0]}")
            if not sqlalchemy_result.success:
                print(f"    SQLAlchemy Error: {sqlalchemy_result.error.split(chr(10))[0]}")
                
        self.test_suites.append(basic_suite)
        
        # Performance tests
        perf_suite = TestSuite("Performance Tests")
        
        print(f"\nRunning: Concurrent Queries Test")
        direct_result, sqlalchemy_result = self.run_comparison_test(
            "Concurrent Queries", 
            lambda agent: self.test_concurrent_queries(agent, 5)
        )
        
        perf_suite.add_result(direct_result)
        perf_suite.add_result(sqlalchemy_result)
        
        self.test_suites.append(perf_suite)
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60 + "\n")
        
        for suite in self.test_suites:
            summary = suite.get_summary()
            print(f"\n{summary['suite_name']}:")
            print("-" * 40)
            
            print("\nDirect FDB Approach:")
            stats = summary['direct_fdb']
            if stats['count'] > 0:
                print(f"  Success Rate: {stats['success_rate']:.1f}% ({stats['success_count']}/{stats['count']})")
                print(f"  Avg Time: {stats['avg_time']:.3f}s")
                print(f"  Median Time: {stats['median_time']:.3f}s")
                print(f"  Min/Max Time: {stats['min_time']:.3f}s / {stats['max_time']:.3f}s")
            else:
                print("  No tests run")
                
            print("\nSQLAlchemy Approach:")
            stats = summary['sqlalchemy']
            if stats['count'] > 0:
                print(f"  Success Rate: {stats['success_rate']:.1f}% ({stats['success_count']}/{stats['count']})")
                print(f"  Avg Time: {stats['avg_time']:.3f}s")
                print(f"  Median Time: {stats['median_time']:.3f}s")
                print(f"  Min/Max Time: {stats['min_time']:.3f}s / {stats['max_time']:.3f}s")
            else:
                print("  No tests run")
                
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to JSON file"""
        results = {
            "test_run": datetime.now().isoformat(),
            "suites": [suite.get_summary() for suite in self.test_suites],
            "detailed_results": []
        }
        
        for suite in self.test_suites:
            for result in suite.results:
                results["detailed_results"].append({
                    "suite": suite.name,
                    "test": result.test_name,
                    "approach": result.approach,
                    "success": result.success,
                    "time": result.execution_time,
                    "error": result.error,
                    "data": result.result_data
                })
                
        os.makedirs("output/test_results", exist_ok=True)
        filepath = f"output/test_results/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"\nResults saved to: {filepath}")


def main():
    """Main entry point"""
    framework = ComparativeTestFramework()
    
    # Setup agents
    framework.setup()
    
    # Run all tests
    framework.run_all_tests()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    framework.save_results(f"comparative_test_{timestamp}.json")


if __name__ == "__main__":
    main()