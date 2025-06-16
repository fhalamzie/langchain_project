#!/usr/bin/env python3
"""
Test WINCASA system with realistic user queries
Uses the 150 real-world query examples from test_questions_json
"""

import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add src to Python path
sys.path.append('src')

from wincasa.core.wincasa_query_engine import WincasaQueryEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_queries() -> Dict[str, Any]:
    """Load test queries from JSON file"""
    query_file = Path("data/test_questions_json/questions.json")
    with open(query_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_query(engine: WincasaQueryEngine, query_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single query and return results"""
    query_id = query_data['id']
    query_text = query_data['query']
    category = query_data['category']
    
    logger.info(f"Testing {query_id}: {query_text}")
    
    try:
        start_time = time.time()
        result = engine.process_query(query_text)
        response_time = time.time() - start_time
        
        # Debug the result structure
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result: {result}")
        
        # Handle QueryEngineResult object
        success = result.result_count > 0  # Success if we found results
        answer = result.answer if hasattr(result, 'answer') else str(result)
        source = result.processing_mode if hasattr(result, 'processing_mode') else 'unknown'
        
        return {
            'id': query_id,
            'query': query_text,
            'category': category,
            'success': success,
            'response_time': response_time,
            'answer_preview': answer[:200] if answer else '',
            'source': source,
            'error': None
        }
    except Exception as e:
        logger.error(f"Error testing {query_id}: {str(e)}")
        return {
            'id': query_id,
            'query': query_text,
            'category': category,
            'success': False,
            'response_time': 0,
            'answer_preview': None,
            'source': None,
            'error': str(e)
        }

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze test results by category"""
    analysis = {
        'total_queries': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'avg_response_time': sum(r['response_time'] for r in results) / len(results) if results else 0,
        'by_category': {},
        'by_source': {}
    }
    
    # Group by category
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0, 'failed': 0, 'avg_time': 0}
        
        categories[cat]['total'] += 1
        if result['success']:
            categories[cat]['success'] += 1
        else:
            categories[cat]['failed'] += 1
    
    # Calculate average times
    for cat, stats in categories.items():
        cat_results = [r for r in results if r['category'] == cat and r['success']]
        if cat_results:
            stats['avg_time'] = sum(r['response_time'] for r in cat_results) / len(cat_results)
        stats['success_rate'] = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    analysis['by_category'] = categories
    
    # Group by source
    sources = {}
    for result in results:
        if result['success']:
            src = result.get('source', 'unknown')
            sources[src] = sources.get(src, 0) + 1
    
    analysis['by_source'] = sources
    
    return analysis

def main():
    """Run realistic query tests"""
    # Load queries
    test_data = load_test_queries()
    queries = test_data['queries']
    
    logger.info(f"Loaded {len(queries)} test queries")
    
    # Initialize engine
    engine = WincasaQueryEngine()
    
    # Test a subset or all queries
    test_limit = int(os.environ.get('TEST_LIMIT', '20'))  # Default to 20 queries
    queries_to_test = queries[:test_limit]
    
    logger.info(f"Testing {len(queries_to_test)} queries...")
    
    # Run tests
    results = []
    for i, query_data in enumerate(queries_to_test):
        logger.info(f"\n[{i+1}/{len(queries_to_test)}] {'-'*50}")
        result = test_query(engine, query_data)
        results.append(result)
        
        # Show result
        if result['success']:
            logger.info(f"✓ Success in {result['response_time']:.2f}s via {result['source']}")
            logger.info(f"  Answer: {result['answer_preview']}...")
        else:
            logger.error(f"✗ Failed: {result['error']}")
    
    # Analyze results
    logger.info("\n" + "="*80)
    logger.info("ANALYSIS")
    logger.info("="*80)
    
    analysis = analyze_results(results)
    
    logger.info(f"\nOverall Results:")
    logger.info(f"  Total: {analysis['total_queries']}")
    logger.info(f"  Success: {analysis['successful']} ({analysis['successful']/analysis['total_queries']*100:.1f}%)")
    logger.info(f"  Failed: {analysis['failed']}")
    logger.info(f"  Avg Response Time: {analysis['avg_response_time']:.2f}s")
    
    logger.info(f"\nBy Category:")
    for cat, stats in sorted(analysis['by_category'].items(), key=lambda x: x[1]['total'], reverse=True):
        logger.info(f"  {cat}:")
        logger.info(f"    Total: {stats['total']}")
        logger.info(f"    Success: {stats['success']} ({stats['success_rate']:.1f}%)")
        logger.info(f"    Avg Time: {stats['avg_time']:.2f}s")
    
    logger.info(f"\nBy Source:")
    for src, count in sorted(analysis['by_source'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {src}: {count}")
    
    # Save detailed results
    results_file = f"test_results/realistic_queries_{int(time.time())}.json"
    os.makedirs("test_results", exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'analysis': analysis
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    main()