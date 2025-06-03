#!/usr/bin/env python3
"""
Fast complete test of all 11 queries with optimized execution.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/envs/openrouter.env')
load_dotenv('/home/envs/openai.env')

# Import the main agent
from firebird_sql_agent_direct import FirebirdDirectSQLAgent

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Reduced logging for speed
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
    "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg"
]

RETRIEVAL_MODES = ['enhanced', 'faiss', 'none']  # Enhanced first for priority

def test_single_mode_all_queries(mode: str) -> List[Dict]:
    """Test all queries with a single mode."""
    print(f"\n{'='*80}")
    print(f"TESTING MODE: {mode.upper()}")
    print(f"{'='*80}")
    
    # Initialize agent once for this mode
    try:
        db_connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_connection_string,
            llm="gpt-4o-mini",
            retrieval_mode=mode,
            use_enhanced_knowledge=True
        )
        print(f"✓ Agent initialized for {mode} mode")
    except Exception as e:
        print(f"✗ Failed to initialize {mode} agent: {e}")
        return []
    
    results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'-'*60}")
        print(f"Query {i}/11: {query}")
        print(f"{'-'*60}")
        
        result = {
            'query_number': i,
            'query': query,
            'mode': mode,
            'success': False,
            'sql_query': None,
            'answer': None,
            'execution_time': None,
            'error': None,
            'found_expected': False
        }
        
        start_time = time.time()
        
        try:
            response = agent.query(query)
            
            if isinstance(response, dict):
                result['answer'] = response.get('agent_final_answer', 'No answer')
                result['sql_query'] = response.get('generated_sql', 'No SQL')
                result['success'] = True
                
                # Check for expected results in address queries
                answer_text = str(result['answer']).lower()
                if "marienstr" in query.lower() and "petra nabakowski" in answer_text:
                    result['found_expected'] = True
                    print(f"  ✓ Found expected resident: Petra Nabakowski")
                elif "bäuminghausstr" in query.lower() and any(name in answer_text for name in ["bewohner", "mieter", "name"]):
                    result['found_expected'] = True
                    print(f"  ✓ Found residents in Bäuminghausstr")
                elif "schmiedestr" in query.lower() and any(name in answer_text for name in ["bewohner", "mieter", "name"]):
                    result['found_expected'] = True
                    print(f"  ✓ Found residents in Schmiedestr")
                elif "eigentümer" in query.lower() and "eigentümer" in answer_text:
                    result['found_expected'] = True
                    print(f"  ✓ Found property owners")
                elif "miete" in query.lower() and ("€" in answer_text or "euro" in answer_text or any(c.isdigit() for c in answer_text)):
                    result['found_expected'] = True
                    print(f"  ✓ Found rent information")
            else:
                result['answer'] = str(response)
                result['success'] = True
            
            print(f"  Status: ✓ Success")
            print(f"  Time: {time.time() - start_time:.1f}s")
            if result['sql_query'] and result['sql_query'] != 'No SQL':
                print(f"  SQL: {result['sql_query'][:80]}...")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"  Status: ✗ Failed - {e}")
        
        finally:
            result['execution_time'] = time.time() - start_time
            results.append(result)
            
            # Small delay between queries
            time.sleep(1)
    
    return results

def run_fast_complete_test():
    """Run complete test optimized for speed."""
    print("FAST COMPLETE RETRIEVAL MODE TEST")
    print("="*80)
    print("Testing all 11 queries across 3 modes")
    print("="*80)
    
    all_results = []
    mode_summaries = {}
    
    # Test each mode separately to avoid re-initialization
    for mode in RETRIEVAL_MODES:
        mode_results = test_single_mode_all_queries(mode)
        all_results.extend(mode_results)
        
        # Calculate mode summary
        successful = [r for r in mode_results if r['success']]
        expected_found = [r for r in mode_results if r['found_expected']]
        total_time = sum(r['execution_time'] for r in mode_results if r['execution_time'])
        avg_time = total_time / len(mode_results) if mode_results else 0
        
        mode_summaries[mode] = {
            'total_queries': len(mode_results),
            'successful': len(successful),
            'expected_found': len(expected_found),
            'total_time': total_time,
            'avg_time': avg_time,
            'success_rate': len(successful) / len(mode_results) * 100 if mode_results else 0,
            'accuracy_rate': len(expected_found) / len(mode_results) * 100 if mode_results else 0
        }
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'fast_complete_test_{timestamp}.json'
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'mode_summaries': mode_summaries,
            'detailed_results': all_results,
            'test_queries': TEST_QUERIES
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("COMPLETE TEST RESULTS")
    print(f"{'='*80}")
    
    # Print comprehensive summary
    print(f"\nOVERALL SUMMARY:")
    print(f"  Total Tests: {len(all_results)}")
    print(f"  Results saved to: {results_file}")
    
    print(f"\nMODE COMPARISON:")
    print(f"{'Mode':<10} {'Success':<8} {'Accuracy':<10} {'Avg Time':<10} {'Total Time':<12}")
    print("-" * 60)
    
    for mode, summary in mode_summaries.items():
        print(f"{mode:<10} {summary['success_rate']:>6.1f}%  {summary['accuracy_rate']:>8.1f}%  {summary['avg_time']:>8.1f}s  {summary['total_time']:>10.1f}s")
    
    # Find best mode
    best_mode = max(mode_summaries.items(), key=lambda x: (x[1]['accuracy_rate'], -x[1]['avg_time']))
    print(f"\n🏆 BEST PERFORMING MODE: {best_mode[0].upper()}")
    print(f"   Accuracy: {best_mode[1]['accuracy_rate']:.1f}%")
    print(f"   Avg Time: {best_mode[1]['avg_time']:.1f}s")
    
    print(f"\nDETAILED RESULTS BY QUERY:")
    print("-" * 80)
    
    # Group results by query for comparison
    for i, query in enumerate(TEST_QUERIES, 1):
        query_results = [r for r in all_results if r['query'] == query]
        print(f"\nQuery {i}: {query}")
        
        for result in query_results:
            status = "✓" if result['success'] else "✗"
            accuracy = "✓" if result['found_expected'] else "⚠"
            time_str = f"{result['execution_time']:.1f}s" if result['execution_time'] else "N/A"
            
            print(f"  {result['mode']:<10} {status} {accuracy} {time_str:<8}")
            
            if result['success'] and result['sql_query'] and result['sql_query'] != 'No SQL':
                print(f"    SQL: {result['sql_query'][:60]}...")
    
    return all_results, mode_summaries

if __name__ == "__main__":
    try:
        run_fast_complete_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        raise