#!/usr/bin/env python3
"""
Test Golden Queries with Knowledge Base Integration
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from config_loader import WincasaConfig
from llm_handler import WincasaLLMHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoldenQueryTester:
    def __init__(self):
        self.llm_handler = WincasaLLMHandler()
        self.golden_set_path = Path("realistic_golden_set.json")
        self.results = []
        
    def load_golden_set(self):
        """Load golden query set"""
        with open(self.golden_set_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def test_query(self, query_data, mode='sql_vanilla'):
        """Test a single query"""
        query = query_data['query']
        category = query_data.get('category', 'unknown')
        expected_results = query_data.get('results', {})
        
        logger.info(f"Testing: {query} (Category: {category})")
        
        start_time = time.time()
        try:
            result = self.llm_handler.query_llm(query, mode)
            response_time = time.time() - start_time
            
            success = result.get('success', False)
            response = result.get('response', '')
            
            # Analyze response
            has_error = 'Fehler' in response or 'ERROR' in response.upper()
            has_sql_error = 'Column unknown' in response or 'Table unknown' in response
            has_results = bool(response) and not has_error
            
            return {
                'query': query,
                'category': category,
                'success': success and not has_error,
                'has_results': has_results,
                'has_sql_error': has_sql_error,
                'response_time': response_time,
                'response_preview': response[:200] + '...' if len(response) > 200 else response,
                'expected_results': expected_results
            }
            
        except Exception as e:
            logger.error(f"Error testing query: {str(e)}")
            return {
                'query': query,
                'category': category,
                'success': False,
                'has_results': False,
                'has_sql_error': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
            
    def run_tests(self, limit=10):
        """Run tests on golden queries"""
        golden_set = self.load_golden_set()
        queries = golden_set.get('queries', [])
        
        logger.info(f"Starting test of {min(limit, len(queries))} queries")
        
        for i, query_data in enumerate(queries[:limit]):
            logger.info(f"\n--- Query {i+1}/{limit} ---")
            result = self.test_query(query_data)
            self.results.append(result)
            
            # Brief pause to avoid overloading
            time.sleep(0.5)
            
    def generate_report(self):
        """Generate test report"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        sql_errors = sum(1 for r in self.results if r['has_sql_error'])
        
        # Group by category
        by_category = {}
        for result in self.results:
            cat = result['category']
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'success': 0, 'sql_errors': 0}
            by_category[cat]['total'] += 1
            if result['success']:
                by_category[cat]['success'] += 1
            if result['has_sql_error']:
                by_category[cat]['sql_errors'] += 1
                
        report = {
            'summary': {
                'total_queries': total,
                'successful': successful,
                'failed': total - successful,
                'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                'sql_errors': sql_errors,
                'avg_response_time': f"{sum(r['response_time'] for r in self.results)/total:.2f}s" if total > 0 else "0s",
                'timestamp': datetime.now().isoformat()
            },
            'by_category': by_category,
            'failed_queries': [r for r in self.results if not r['success']],
            'sql_error_queries': [r for r in self.results if r['has_sql_error']]
        }
        
        # Save detailed results
        with open('golden_query_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'report': report,
                'detailed_results': self.results
            }, f, indent=2, ensure_ascii=False)
            
        return report
        
    def print_report(self, report):
        """Print test report"""
        print("\n" + "="*60)
        print("GOLDEN QUERY TEST REPORT - WITH KNOWLEDGE BASE")
        print("="*60)
        
        summary = report['summary']
        print(f"\nSummary:")
        print(f"  Total Queries: {summary['total_queries']}")
        print(f"  Successful: {summary['successful']} ({summary['success_rate']})")
        print(f"  Failed: {summary['failed']}")
        print(f"  SQL Errors: {summary['sql_errors']}")
        print(f"  Avg Response Time: {summary['avg_response_time']}")
        
        print(f"\nBy Category:")
        for cat, stats in report['by_category'].items():
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.0f}%) - SQL Errors: {stats['sql_errors']}")
            
        if report['sql_error_queries']:
            print(f"\nQueries with SQL Errors ({len(report['sql_error_queries'])}):")
            for q in report['sql_error_queries'][:5]:
                print(f"  - {q['query'][:60]}...")
                print(f"    Error: {q.get('response_preview', '')[:100]}...")
                
        print(f"\nDetailed results saved to: golden_query_test_results.json")


def main():
    tester = GoldenQueryTester()
    
    # Test first 5 queries
    tester.run_tests(limit=5)
    
    # Generate and print report
    report = tester.generate_report()
    tester.print_report(report)


if __name__ == "__main__":
    main()