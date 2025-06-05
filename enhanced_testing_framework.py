"""
WINCASA Enhanced Testing Framework - Building on Existing Architecture
This module extends the existing automated_retrieval_test.py with three testing levels:
a) Quick Test - Basic functionality verification (2-3 queries, fastest modes)
b) Extensive Test - Comprehensive failure detection (all queries, all modes)  
c) Baseline Test - Performance comparison with statistical analysis
Author: WINCASA Development Team
Date: 2025-01-06
"""

import os
import sys
import json
import time
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

# Import system components
try:
    from firebird_sql_agent_direct import FirebirdDirectSQLAgent
    from llm_interface import LLMInterface
    from phoenix_monitoring import get_monitor
    from global_context import get_compact_global_context, get_global_context_prompt
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


@dataclass
class TestResult:
    """Standardized test result structure based on existing patterns"""
    query: str
    mode: str
    success: bool
    response_time: float
    response: str
    sql_generated: Optional[str] = None
    rows_returned: Optional[int] = None
    error_message: Optional[str] = None
    context_docs: Optional[int] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass 
class TestSuite:
    """Test suite configuration matching existing test patterns"""
    name: str
    queries: List[str]
    expected_modes: List[str]
    timeout: int = 30
    description: str = ""


class EnhancedWINCASTesting:
    """
    Enhanced WINCASA Testing Framework - Extends existing automated_retrieval_test.py
    
    Three testing levels building on existing architecture:
    - Quick: Basic verification (builds on quick_retrieval_test_all_modes.py)
    - Extensive: Comprehensive testing (extends automated_retrieval_test.py)
    - Baseline: Performance comparison (inspired by optimized_retrieval_test.py)
    """
    
    def __init__(self, enable_monitoring: bool = True):
        self.logger = self._setup_logging()
        self.enable_monitoring = enable_monitoring
        
        # Phoenix monitoring (matching existing pattern)
        self.monitor = None
        if enable_monitoring:
            try:
                self.monitor = get_monitor(enable_ui=False)  # Avoid UI connection issues
                self.logger.info("✅ Phoenix monitoring initialized")
            except Exception as e:
                self.logger.warning(f"⚠️ Phoenix monitoring failed: {e}")
        
        # Test suites based on existing test queries
        self._initialize_test_suites()
        
        # Database connection (from existing config)
        self.db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        self.llm_interface = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging matching existing pattern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f'enhanced_testing_{timestamp}.log'
        
        # Remove existing handlers to avoid conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"🚀 Enhanced WINCASA Testing Framework - Log: {log_filename}")
        return logger
        
    def _initialize_test_suites(self):
        """Initialize test suites based on existing test queries"""
        # Quick test - based on quick_retrieval_test_all_modes.py
        quick_queries = [
            "Wie viele Wohnungen gibt es insgesamt?",
            "Zeige die ersten 2 Eigentümer"
        ]
        
        # Extensive test - from automated_retrieval_test.py 
        extensive_queries = [
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
            "Zeige Bewohner mit Mietverträgen"
        ]
        
        # Baseline test - performance focused
        baseline_queries = [
            "Wie viele Wohnungen gibt es insgesamt?",
            "Wer wohnt in der Marienstraße 26",
            "Liste aller Eigentümer",
            "Alle Mieter in Essen",
            "Durchschnittliche Miete"
        ]
        
        # Available modes based on current system status
        all_modes = ["enhanced", "faiss", "none", "langchain"]
        quick_modes = ["enhanced", "none"]  # Fastest modes for quick testing
        
        self.test_suites = {
            'quick': TestSuite(
                name="Quick Verification",
                queries=quick_queries,
                expected_modes=quick_modes,
                timeout=30,
                description="Basic functionality verification - fastest modes only"
            ),
            'extensive': TestSuite(
                name="Comprehensive Testing", 
                queries=extensive_queries,
                expected_modes=all_modes,
                timeout=45,
                description="Comprehensive failure detection across all modes"
            ),
            'baseline': TestSuite(
                name="Performance Baseline",
                queries=baseline_queries,
                expected_modes=all_modes,
                timeout=60,
                description="Performance comparison with statistical analysis"
            )
        }
        
    def initialize_llm(self, model: str = "gpt-4") -> bool:
        """Initialize LLM interface matching existing pattern"""
        try:
            self.llm_interface = LLMInterface(model)
            self.logger.info(f"✅ LLM interface initialized: {model}")
            return True
        except Exception as e:
            self.logger.error(f"❌ LLM initialization failed: {e}")
            return False
            
    def test_single_query(self, query: str, mode: str, timeout: int = 30) -> TestResult:
        """Test single query with specified mode - matches existing agent pattern"""
        start_time = time.time()
        
        try:
            # Create agent (matches firebird_sql_agent_direct pattern)
            agent = FirebirdDirectSQLAgent(
                db_connection_string=self.db_connection,
                llm=self.llm_interface,
                retrieval_mode=mode,
                use_enhanced_knowledge=True
            )
            
            # Execute query
            response = agent.query(query)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extract results (attempt to parse response)
            sql_generated = None
            rows_returned = None
            context_docs = None
            
            # Try to extract SQL from response
            response_str = str(response)
            if "SELECT" in response_str.upper():
                # Find SQL in response
                lines = response_str.split('\n')
                for line in lines:
                    if "SELECT" in line.upper():
                        sql_generated = line.strip()
                        break
            
            # Try to extract row count
            if "row" in response_str.lower():
                import re
                row_match = re.search(r'(\d+)\s+row', response_str.lower())
                if row_match:
                    rows_returned = int(row_match.group(1))
            
            return TestResult(
                query=query,
                mode=mode,
                success=True,
                response_time=response_time,
                response=response_str[:500],  # Truncate for logging
                sql_generated=sql_generated,
                rows_returned=rows_returned,
                context_docs=context_docs
            )
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return TestResult(
                query=query,
                mode=mode,
                success=False,
                response_time=response_time,
                response="",
                error_message=str(e)
            )
    
    def run_quick_test(self) -> Dict[str, Any]:
        """Quick functionality verification - extends quick_retrieval_test_all_modes.py"""
        self.logger.info("🚀 Starting QUICK TEST - Basic Functionality Verification")
        
        if not self.initialize_llm():
            return {"error": "LLM initialization failed"}
            
        suite = self.test_suites['quick']
        results = []
        
        for query in suite.queries:
            for mode in suite.expected_modes:
                self.logger.info(f"Testing: {mode} mode - '{query}'")
                result = self.test_single_query(query, mode, suite.timeout)
                results.append(result)
                
                status = "✅" if result.success else "❌"
                self.logger.info(f"{status} {mode}: {result.response_time:.1f}s")
        
        # Generate summary
        summary = self._generate_summary(results, "quick")
        self._save_results(results, "quick")
        
        return summary
    
    def run_extensive_test(self, concurrent: bool = False, workers: int = 2) -> Dict[str, Any]:
        """Comprehensive testing - extends automated_retrieval_test.py"""
        self.logger.info(f"🚀 Starting EXTENSIVE TEST - Comprehensive Mode Analysis (concurrent={concurrent})")
        
        if not self.initialize_llm():
            return {"error": "LLM initialization failed"}
            
        suite = self.test_suites['extensive']
        
        if concurrent:
            results = self._run_concurrent_tests(suite, workers)
        else:
            results = self._run_sequential_tests(suite)
        
        # Generate comprehensive analysis
        summary = self._generate_summary(results, "extensive")
        
        # Add mode comparison analysis (from test_analysis_summary.md pattern)
        self._analyze_mode_performance(results)
        
        self._save_results(results, "extensive")
        return summary
        
    def run_baseline_test(self) -> Dict[str, Any]:
        """Performance baseline - inspired by optimized_retrieval_test.py"""
        self.logger.info("🚀 Starting BASELINE TEST - Performance & Statistical Analysis")
        
        if not self.initialize_llm():
            return {"error": "LLM initialization failed"}
            
        suite = self.test_suites['baseline']
        results = []
        
        # Run each query multiple times for statistical significance
        for query in suite.queries:
            for mode in suite.expected_modes:
                mode_results = []
                
                self.logger.info(f"📊 Baseline testing: {mode} mode - '{query}'")
                
                for run in range(3):  # 3 runs per query/mode
                    result = self.test_single_query(query, mode, suite.timeout)
                    mode_results.append(result)
                    results.append(result)
                
                # Log statistics for this mode/query combination
                self._log_baseline_stats(query, mode, mode_results)
        
        # Generate detailed performance analysis
        summary = self._generate_baseline_summary(results)
        self._save_results(results, "baseline")
        
        return summary
    
    def _run_sequential_tests(self, suite: TestSuite) -> List[TestResult]:
        """Run tests sequentially - matches existing pattern"""
        results = []
        
        for query in suite.queries:
            for mode in suite.expected_modes:
                self.logger.info(f"Testing: {mode} mode - '{query}'")
                result = self.test_single_query(query, mode, suite.timeout)
                results.append(result)
                
                status = "✅" if result.success else "❌"
                self.logger.info(f"{status} {mode}: {result.response_time:.1f}s")
        
        return results
    
    def _run_concurrent_tests(self, suite: TestSuite, workers: int) -> List[TestResult]:
        """Run tests concurrently - from optimized_retrieval_test.py pattern"""
        self.logger.info(f"Running concurrent tests with {workers} workers")
        
        # Create test tasks
        tasks = []
        for query in suite.queries:
            for mode in suite.expected_modes:
                tasks.append((query, mode, suite.timeout))
        
        # Execute with ThreadPoolExecutor
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {
                executor.submit(self.test_single_query, *task): task 
                for task in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    status = "✅" if result.success else "❌"
                    self.logger.info(f"{status} {result.mode}: {result.response_time:.1f}s - {task[0][:50]}...")
                    
                except Exception as e:
                    self.logger.error(f"❌ Task {task} failed: {e}")
        
        return results
    
    def _analyze_mode_performance(self, results: List[TestResult]):
        """Analyze mode performance - inspired by test_analysis_summary.md"""
        self.logger.info("\n📊 MODE PERFORMANCE ANALYSIS:")
        
        # Group results by mode
        mode_results = {}
        for result in results:
            if result.mode not in mode_results:
                mode_results[result.mode] = []
            mode_results[result.mode].append(result)
        
        # Analyze each mode
        for mode in sorted(mode_results.keys()):
            results_for_mode = mode_results[mode]
            successful = [r for r in results_for_mode if r.success]
            
            success_rate = len(successful) / len(results_for_mode) if results_for_mode else 0
            avg_time = statistics.mean([r.response_time for r in successful]) if successful else 0
            
            self.logger.info(f"   {mode.upper()}: {success_rate:.1%} success, {avg_time:.1f}s avg")
            
            # Log best/worst performances
            if successful:
                fastest = min(successful, key=lambda x: x.response_time)
                slowest = max(successful, key=lambda x: x.response_time)
                self.logger.info(f"     Fastest: {fastest.response_time:.1f}s - {fastest.query[:30]}...")
                self.logger.info(f"     Slowest: {slowest.response_time:.1f}s - {slowest.query[:30]}...")
    
    def _generate_summary(self, results: List[TestResult], test_type: str) -> Dict[str, Any]:
        """Generate comprehensive test summary matching existing JSON output pattern"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Mode-specific statistics
        mode_stats = {}
        for result in results:
            if result.mode not in mode_stats:
                mode_stats[result.mode] = {
                    'success': 0, 'total': 0, 'times': [], 'errors': []
                }
            
            mode_stats[result.mode]['total'] += 1
            mode_stats[result.mode]['times'].append(result.response_time)
            
            if result.success:
                mode_stats[result.mode]['success'] += 1
            else:
                mode_stats[result.mode]['errors'].append(result.error_message)
        
        # Calculate statistics
        for mode in mode_stats:
            stats = mode_stats[mode]
            stats['success_rate'] = stats['success'] / stats['total']
            
            if stats['times']:
                stats['avg_time'] = statistics.mean(stats['times'])
                stats['min_time'] = min(stats['times'])
                stats['max_time'] = max(stats['times'])
                stats['median_time'] = statistics.median(stats['times'])
            
            # Clean up for JSON serialization
            del stats['times']
            stats['error_count'] = len(stats['errors'])
            del stats['errors']  # Keep error count but remove detailed messages
        
        summary = {
            'test_type': test_type,
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'mode_statistics': mode_stats,
            'total_time': sum(r.response_time for r in results),
            'system_info': {
                'db_connection': self.db_connection,
                'monitoring_enabled': self.enable_monitoring,
                'llm_model': 'gpt-4'
            }
        }
        
        # Log summary
        self.logger.info(f"\n📊 {test_type.upper()} TEST SUMMARY:")
        self.logger.info(f"   Success Rate: {success_rate:.1%} ({successful_tests}/{total_tests})")
        self.logger.info(f"   Total Time: {summary['total_time']:.1f}s")
        
        for mode, stats in mode_stats.items():
            self.logger.info(f"   {mode}: {stats['success_rate']:.1%} success, {stats['avg_time']:.1f}s avg")
        
        return summary
    
    def _generate_baseline_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate detailed baseline performance summary with statistics"""
        summary = self._generate_summary(results, "baseline")
        
        # Add detailed performance metrics
        response_times = [r.response_time for r in results if r.success]
        if response_times:
            summary['performance_metrics'] = {
                'mean_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'std_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'min_response_time': min(response_times),
                'max_response_time': max(response_times)
            }
            
            # Add percentiles if we have enough data
            if len(response_times) >= 10:
                sorted_times = sorted(response_times)
                summary['performance_metrics']['p90_response_time'] = sorted_times[int(len(sorted_times) * 0.9)]
                summary['performance_metrics']['p95_response_time'] = sorted_times[int(len(sorted_times) * 0.95)]
        
        return summary
    
    def _log_baseline_stats(self, query: str, mode: str, results: List[TestResult]):
        """Log statistical analysis for baseline runs"""
        times = [r.response_time for r in results if r.success]
        success_count = sum(1 for r in results if r.success)
        
        if times:
            avg_time = statistics.mean(times)
            std_time = statistics.stdev(times) if len(times) > 1 else 0
            self.logger.info(f"     📈 {avg_time:.1f}s ± {std_time:.1f}s ({success_count}/3 success)")
    
    def _save_results(self, results: List[TestResult], test_type: str):
        """Save results to JSON file matching existing output pattern"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_test_results_{test_type}_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        results_data = [asdict(result) for result in results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Results saved to {filename}")


def main():
    """Main CLI interface matching existing test script patterns"""
    parser = argparse.ArgumentParser(description="Enhanced WINCASA Testing Framework")
    parser.add_argument('--test-type', choices=['quick', 'extensive', 'baseline', 'all'],
                       default='quick', help='Type of test to run')
    parser.add_argument('--concurrent', action='store_true', 
                       help='Enable concurrent testing (extensive mode only)')
    parser.add_argument('--workers', type=int, default=2,
                       help='Number of concurrent workers')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Disable Phoenix monitoring')
    
    args = parser.parse_args()
    
    # Initialize testing framework
    framework = EnhancedWINCASTesting(enable_monitoring=not args.no_monitoring)
    
    # Run tests based on type
    if args.test_type == 'quick':
        summary = framework.run_quick_test()
    elif args.test_type == 'extensive':
        summary = framework.run_extensive_test(
            concurrent=args.concurrent, 
            workers=args.workers
        )
    elif args.test_type == 'baseline':
        summary = framework.run_baseline_test()
    elif args.test_type == 'all':
        print("Running all test types...")
        quick_summary = framework.run_quick_test()
        extensive_summary = framework.run_extensive_test()
        baseline_summary = framework.run_baseline_test()
        
        # Combined summary
        summary = {
            'quick': quick_summary,
            'extensive': extensive_summary, 
            'baseline': baseline_summary
        }
    
    # Print final summary
    print("\n" + "="*60)
    print("🎯 ENHANCED WINCASA TESTING COMPLETE")
    print("="*60)
    
    if args.test_type != 'all':
        print(f"Test Type: {summary['test_type']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Time: {summary['total_time']:.1f}s")
        
        # Show mode ranking
        mode_stats = summary.get('mode_statistics', {})
        if mode_stats:
            print("\nMode Performance Ranking:")
            sorted_modes = sorted(mode_stats.items(), 
                                key=lambda x: (x[1]['success_rate'], -x[1]['avg_time']), 
                                reverse=True)
            for i, (mode, stats) in enumerate(sorted_modes, 1):
                print(f"  {i}. {mode}: {stats['success_rate']:.1%} success, {stats['avg_time']:.1f}s avg")
    else:
        print("All test types completed. See individual result files.")


if __name__ == "__main__":
    main()