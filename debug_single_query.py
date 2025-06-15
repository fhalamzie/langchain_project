#!/usr/bin/env python3
"""
WINCASA Single Query Debugger

Interactive tool for debugging specific queries across all modes.
Usage: python debug_single_query.py "Your query" --mode=UNIFIED --trace
"""

import sys
import argparse
import time
import logging
from typing import Dict, Any

def setup_debug_logging():
    """Setup detailed logging for debugging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def debug_query(query: str, mode: str = "UNIFIED", trace: bool = False, compare: bool = False) -> Dict[str, Any]:
    """
    Debug a single query with detailed tracing
    
    Args:
        query: The query to test
        mode: Mode to test (UNIFIED, JSON_VANILLA, JSON_SYSTEM, SQL_VANILLA, SQL_SYSTEM)
        trace: Enable detailed tracing
        compare: Compare across all modes
    """
    print(f"🔍 Debugging Query: '{query}'")
    print(f"📋 Mode: {mode}")
    print("=" * 50)
    
    if trace:
        setup_debug_logging()
        print("🐛 Trace mode enabled - detailed logs will follow")
        print("💡 Set breakpoints with: import pdb; pdb.set_trace()")
        print("")
    
    results = {}
    modes_to_test = ["JSON_VANILLA", "JSON_SYSTEM", "SQL_VANILLA", "SQL_SYSTEM", "UNIFIED"] if compare else [mode]
    
    for test_mode in modes_to_test:
        print(f"\n🧪 Testing Mode: {test_mode}")
        start_time = time.time()
        
        try:
            if test_mode == "UNIFIED":
                # Test Mode 5 (Unified Engine)
                from wincasa_query_engine import WincasaQueryEngine
                
                if trace:
                    print("📍 Breakpoint suggestion: Set in wincasa_query_engine.py line 45")
                    import pdb; pdb.set_trace()
                
                engine = WincasaQueryEngine()
                result = engine.execute_query(query)
                
                # Extract key metrics
                response_time = (time.time() - start_time) * 1000
                execution_path = getattr(result, 'execution_path', 'unknown')
                success = getattr(result, 'success', True)
                data_count = len(getattr(result, 'data', [])) if hasattr(result, 'data') else 0
                
                results[test_mode] = {
                    'success': success,
                    'response_time_ms': response_time,
                    'execution_path': execution_path,
                    'data_count': data_count,
                    'result': result
                }
                
                print(f"   ✅ Success: {success}")
                print(f"   ⚡ Response Time: {response_time:.1f}ms")
                print(f"   🛤️  Execution Path: {execution_path}")
                print(f"   📊 Data Count: {data_count}")
                
            else:
                # Test Legacy Modes (1-4)
                from llm_handler import process_query
                
                if trace:
                    print("📍 Breakpoint suggestion: Set in llm_handler.py line 34")
                    import pdb; pdb.set_trace()
                
                result = process_query(query, test_mode)
                
                response_time = (time.time() - start_time) * 1000
                success = result.get('success', True) if isinstance(result, dict) else True
                data_count = len(result.get('data', [])) if isinstance(result, dict) and 'data' in result else 0
                
                results[test_mode] = {
                    'success': success,
                    'response_time_ms': response_time,
                    'execution_path': 'legacy',
                    'data_count': data_count,
                    'result': result
                }
                
                print(f"   ✅ Success: {success}")
                print(f"   ⚡ Response Time: {response_time:.1f}ms")
                print(f"   📊 Data Count: {data_count}")
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            results[test_mode] = {
                'success': False,
                'error': str(e),
                'response_time_ms': response_time
            }
            print(f"   ❌ Error: {e}")
            print(f"   ⚡ Time to error: {response_time:.1f}ms")
            
            if trace:
                import traceback
                print("🔍 Full traceback:")
                traceback.print_exc()
    
    # Summary
    if compare:
        print("\n" + "=" * 50)
        print("📊 COMPARISON SUMMARY")
        print("=" * 50)
        
        for mode_name, result_data in results.items():
            if result_data.get('success', False):
                print(f"{mode_name:12} | ✅ {result_data['response_time_ms']:6.1f}ms | {result_data.get('execution_path', 'legacy'):15} | {result_data.get('data_count', 0):3} results")
            else:
                print(f"{mode_name:12} | ❌ {result_data['response_time_ms']:6.1f}ms | ERROR: {result_data.get('error', 'Unknown')[:30]}")
        
        # Find fastest successful mode
        successful_modes = {k: v for k, v in results.items() if v.get('success', False)}
        if successful_modes:
            fastest = min(successful_modes.items(), key=lambda x: x[1]['response_time_ms'])
            print(f"\n🏆 Fastest: {fastest[0]} ({fastest[1]['response_time_ms']:.1f}ms)")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Debug WINCASA queries interactively')
    parser.add_argument('query', help='Query to test')
    parser.add_argument('--mode', default='UNIFIED', 
                       choices=['UNIFIED', 'JSON_VANILLA', 'JSON_SYSTEM', 'SQL_VANILLA', 'SQL_SYSTEM'],
                       help='Mode to test (default: UNIFIED)')
    parser.add_argument('--trace', action='store_true', help='Enable detailed tracing')
    parser.add_argument('--compare', action='store_true', help='Compare across all modes')
    
    args = parser.parse_args()
    
    print("🏠 WINCASA Query Debugger")
    print("🎯 Perfect for testing single queries interactively")
    print("")
    
    try:
        results = debug_query(args.query, args.mode, args.trace, args.compare)
        print("\n✅ Debug session completed")
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Debug session interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Debug session failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())