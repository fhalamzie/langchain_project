#!/usr/bin/env python3
"""
Automated test script for WINCASA system with different retrieval modes.
Tests predefined queries across faiss, enhanced, and none modes.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from concurrent.futures import TimeoutError
import signal
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

# Import the main agent
from firebird_sql_agent_direct import FirebirdDirectSQLAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'retrieval_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test queries
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
    "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg"
]

RETRIEVAL_MODES = ['faiss', 'enhanced', 'none']

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Query execution timed out")

class RetrievalTestRunner:
    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.results = []
        self.agents = {}
        
    def initialize_agents(self):
        """Initialize agents for each retrieval mode."""
        for mode in RETRIEVAL_MODES:
            try:
                logger.info(f"Initializing agent with mode: {mode}")
                db_connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
                self.agents[mode] = FirebirdDirectSQLAgent(
                    db_connection_string=db_connection_string,
                    llm="gpt-4o-mini",
                    retrieval_mode=mode,
                    use_enhanced_knowledge=True
                )
                logger.info(f"Successfully initialized agent for mode: {mode}")
            except Exception as e:
                logger.error(f"Failed to initialize agent for mode {mode}: {e}")
                self.agents[mode] = None
    
    def execute_query_with_timeout(self, agent, query: str, mode: str) -> Dict[str, Any]:
        """Execute a query with timeout protection."""
        result = {
            'query': query,
            'mode': mode,
            'success': False,
            'sql_query': None,
            'answer': None,
            'execution_time': None,
            'error': None,
            'row_count': 0
        }
        
        if agent is None:
            result['error'] = f"Agent not initialized for mode {mode}"
            return result
        
        # Set signal alarm for timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)
        
        start_time = time.time()
        
        try:
            # Execute query
            response = agent.query(query)
            
            # Parse response
            if isinstance(response, dict):
                result['answer'] = response.get('agent_final_answer', response.get('output', str(response)))
                result['sql_query'] = response.get('generated_sql', response.get('sql_query', 'N/A'))
                
                # Try to extract row count from query results
                if 'query_results' in response and response['query_results']:
                    result['row_count'] = len(response['query_results'])
                
                # Also check intermediate steps if available
                if 'intermediate_steps' in response:
                    for step in response['intermediate_steps']:
                        if isinstance(step, tuple) and len(step) > 1:
                            step_output = str(step[1])
                            if 'rows' in step_output.lower():
                                # Try to extract row count
                                import re
                                match = re.search(r'(\d+)\s*rows?', step_output.lower())
                                if match:
                                    result['row_count'] = int(match.group(1))
            else:
                result['answer'] = str(response)
                result['sql_query'] = 'N/A'
            
            result['success'] = True
            
        except TimeoutException:
            result['error'] = f"Query timed out after {self.timeout_seconds} seconds"
            logger.warning(f"Timeout for query '{query}' in mode {mode}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error executing query '{query}' in mode {mode}: {e}")
            
        finally:
            # Cancel alarm
            signal.alarm(0)
            result['execution_time'] = time.time() - start_time
            
        return result
    
    def run_all_tests(self):
        """Run all test queries across all modes."""
        logger.info("Starting retrieval mode comparison tests")
        
        # Initialize agents
        self.initialize_agents()
        
        total_tests = len(TEST_QUERIES) * len(RETRIEVAL_MODES)
        completed = 0
        
        for query in TEST_QUERIES:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing query: {query}")
            logger.info(f"{'='*80}")
            
            query_results = []
            
            for mode in RETRIEVAL_MODES:
                completed += 1
                logger.info(f"\nProgress: {completed}/{total_tests} - Testing with mode: {mode}")
                
                agent = self.agents.get(mode)
                result = self.execute_query_with_timeout(agent, query, mode)
                
                query_results.append(result)
                self.results.append(result)
                
                # Log result summary
                if result['success']:
                    logger.info(f"✓ Success - Time: {result['execution_time']:.2f}s, Rows: {result['row_count']}")
                    if result['sql_query'] != 'N/A':
                        logger.info(f"  SQL: {result['sql_query'][:100]}...")
                else:
                    logger.error(f"✗ Failed - {result['error']}")
                
                # Small delay between queries
                time.sleep(2)
            
            # Compare results for this query
            self._compare_query_results(query, query_results)
            
    def _compare_query_results(self, query: str, results: List[Dict]):
        """Compare results across different modes for a single query."""
        logger.info(f"\nComparison for: {query}")
        
        # Check if all succeeded
        successful_modes = [r['mode'] for r in results if r['success']]
        failed_modes = [r['mode'] for r in results if not r['success']]
        
        if failed_modes:
            logger.warning(f"Failed modes: {', '.join(failed_modes)}")
        
        if len(successful_modes) > 1:
            # Compare SQL queries
            sql_queries = {r['mode']: r['sql_query'] for r in results if r['success']}
            unique_sqls = set(sql_queries.values())
            
            if len(unique_sqls) == 1:
                logger.info("✓ All modes generated identical SQL")
            else:
                logger.warning("⚠ Different SQL queries generated:")
                for mode, sql in sql_queries.items():
                    logger.info(f"  {mode}: {sql[:100]}...")
            
            # Compare execution times
            times = {r['mode']: r['execution_time'] for r in results if r['success']}
            fastest = min(times.items(), key=lambda x: x[1])
            logger.info(f"Fastest mode: {fastest[0]} ({fastest[1]:.2f}s)")
            
            # Compare row counts
            row_counts = {r['mode']: r['row_count'] for r in results if r['success']}
            if len(set(row_counts.values())) == 1:
                logger.info(f"✓ All modes returned same row count: {list(row_counts.values())[0]}")
            else:
                logger.warning(f"⚠ Different row counts: {row_counts}")
    
    def generate_report(self):
        """Generate comprehensive test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create summary statistics
        summary = {
            'test_date': datetime.now().isoformat(),
            'total_queries': len(TEST_QUERIES),
            'total_tests': len(self.results),
            'modes_tested': RETRIEVAL_MODES,
            'overall_success_rate': sum(1 for r in self.results if r['success']) / len(self.results) * 100,
            'mode_statistics': {}
        }
        
        # Calculate per-mode statistics
        for mode in RETRIEVAL_MODES:
            mode_results = [r for r in self.results if r['mode'] == mode]
            successful = sum(1 for r in mode_results if r['success'])
            
            avg_time = sum(r['execution_time'] for r in mode_results if r['success']) / max(successful, 1)
            
            summary['mode_statistics'][mode] = {
                'success_rate': successful / len(mode_results) * 100 if mode_results else 0,
                'average_execution_time': avg_time,
                'successful_queries': successful,
                'failed_queries': len(mode_results) - successful
            }
        
        # Save detailed results
        results_file = f'retrieval_test_results_{timestamp}.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
                'detailed_results': self.results,
                'test_queries': TEST_QUERIES
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nResults saved to: {results_file}")
        
        # Generate pandas DataFrame for analysis
        df = pd.DataFrame(self.results)
        csv_file = f'retrieval_test_results_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        logger.info(f"CSV results saved to: {csv_file}")
        
        # Print summary
        self._print_summary(summary)
        
        return summary, results_file
    
    def _print_summary(self, summary: Dict):
        """Print formatted summary of test results."""
        print("\n" + "="*80)
        print("RETRIEVAL MODE TEST SUMMARY")
        print("="*80)
        print(f"Test Date: {summary['test_date']}")
        print(f"Total Queries Tested: {summary['total_queries']}")
        print(f"Total Test Runs: {summary['total_tests']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print("\nPER-MODE STATISTICS:")
        print("-"*50)
        
        for mode, stats in summary['mode_statistics'].items():
            print(f"\n{mode.upper()} Mode:")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Avg Execution Time: {stats['average_execution_time']:.2f}s")
            print(f"  Successful: {stats['successful_queries']}/{summary['total_queries']}")
        
        # Find best performing mode
        best_mode = max(summary['mode_statistics'].items(), 
                       key=lambda x: (x[1]['success_rate'], -x[1]['average_execution_time']))
        
        print("\n" + "="*80)
        print(f"BEST PERFORMING MODE: {best_mode[0].upper()}")
        print("="*80)


def main():
    """Main execution function."""
    print("Starting WINCASA Retrieval Mode Comparison Test")
    print("="*80)
    
    # Create test runner
    runner = RetrievalTestRunner(timeout_seconds=60)
    
    try:
        # Run all tests
        runner.run_all_tests()
        
        # Generate report
        summary, results_file = runner.generate_report()
        
        print(f"\n✓ Test completed successfully!")
        print(f"  Results saved to: {results_file}")
        print(f"  Log file: retrieval_test_*.log")
        
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
        print("\n⚠ Test interrupted. Partial results may have been saved.")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()