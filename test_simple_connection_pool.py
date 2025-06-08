#!/usr/bin/env python3
"""
Simple Connection Pool Test with Embedded Database
=================================================

Test connection pooling with embedded Firebird database format
to verify the optimization works before integrating with LangChain modes.
"""

import time
import statistics
from typing import List, Dict, Any

# Test embedded connection without server format
def test_embedded_connection():
    """Test basic embedded Firebird connection."""
    print("🧪 Testing Embedded Firebird Connection")
    print("=" * 60)
    
    try:
        import firebird.driver as fdb_driver
        
        # Test direct embedded connection
        start_time = time.time()
        with fdb_driver.connect(
            database="/home/projects/langchain_project/WINCASA2022.FDB",
            user="sysdba",
            password="masterkey"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM BEWOHNER")
                result = cur.fetchone()
                bewohner_count = result[0] if result else 0
        
        execution_time = time.time() - start_time
        print(f"✅ Embedded connection successful in {execution_time:.3f}s")
        print(f"📊 BEWOHNER count: {bewohner_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedded connection failed: {e}")
        return False

def test_connection_reuse_performance():
    """Test performance of reusing vs creating new connections."""
    print("\n🧪 Testing Connection Reuse Performance")
    print("=" * 60)
    
    try:
        import firebird.driver as fdb_driver
        
        # Test multiple new connections (baseline)
        print("Testing 5 new connections...")
        start_time = time.time()
        for i in range(5):
            with fdb_driver.connect(
                database="/home/projects/langchain_project/WINCASA2022.FDB",
                user="sysdba",
                password="masterkey"
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM RDB$DATABASE")
                    result = cur.fetchone()
        new_connections_time = time.time() - start_time
        
        print(f"⏱️  5 new connections: {new_connections_time:.3f}s")
        print(f"📊 Average per connection: {new_connections_time/5:.3f}s")
        
        # Test single reused connection
        print("\nTesting 5 queries on reused connection...")
        start_time = time.time()
        with fdb_driver.connect(
            database="/home/projects/langchain_project/WINCASA2022.FDB",
            user="sysdba",
            password="masterkey"
        ) as conn:
            for i in range(5):
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM RDB$DATABASE")
                    result = cur.fetchone()
        reused_connection_time = time.time() - start_time
        
        print(f"⚡ 5 queries on reused connection: {reused_connection_time:.3f}s")
        print(f"📊 Average per query: {reused_connection_time/5:.3f}s")
        
        # Calculate improvement
        if reused_connection_time > 0:
            improvement = new_connections_time / reused_connection_time
            print(f"🎯 Connection reuse speedup: {improvement:.1f}x")
            return improvement > 1.2
        
        return False
        
    except Exception as e:
        print(f"❌ Connection reuse test failed: {e}")
        return False

def test_query_caching_manual():
    """Test manual query result caching."""
    print("\n🧪 Testing Manual Query Result Caching")
    print("=" * 60)
    
    try:
        import firebird.driver as fdb_driver
        
        # Simple in-memory cache
        query_cache = {}
        
        def cached_query(query: str):
            if query in query_cache:
                return query_cache[query], True  # Cache hit
            
            # Execute query
            with fdb_driver.connect(
                database="/home/projects/langchain_project/WINCASA2022.FDB",
                user="sysdba",
                password="masterkey"
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchall()
                    query_cache[query] = result
                    return result, False  # Cache miss
        
        # Test queries
        test_queries = [
            "SELECT COUNT(*) FROM BEWOHNER",
            "SELECT COUNT(*) FROM OBJEKTE",
            "SELECT COUNT(*) FROM EIGENTUEMER"
        ]
        
        # First run (cache misses)
        print("First run (cache misses):")
        first_run_times = []
        for query in test_queries:
            start_time = time.time()
            result, cached = cached_query(query)
            execution_time = time.time() - start_time
            first_run_times.append(execution_time)
            print(f"⏱️  {query[:30]}... - {execution_time:.3f}s (cached: {cached})")
        
        # Second run (cache hits)
        print("\nSecond run (cache hits):")
        second_run_times = []
        for query in test_queries:
            start_time = time.time()
            result, cached = cached_query(query)
            execution_time = time.time() - start_time
            second_run_times.append(execution_time)
            print(f"🚀 {query[:30]}... - {execution_time:.3f}s (cached: {cached})")
        
        # Calculate improvement
        avg_first = statistics.mean(first_run_times)
        avg_cached = statistics.mean(second_run_times)
        
        print(f"\n📊 Average first run: {avg_first:.3f}s")
        print(f"📊 Average cached run: {avg_cached:.3f}s")
        
        if avg_cached > 0:
            speedup = avg_first / avg_cached
            print(f"🎯 Caching speedup: {speedup:.1f}x")
            return speedup > 2.0  # Expect significant speedup from caching
        
        return False
        
    except Exception as e:
        print(f"❌ Query caching test failed: {e}")
        return False

def test_database_performance_metrics():
    """Test collecting database performance metrics."""
    print("\n🧪 Testing Database Performance Metrics")
    print("=" * 60)
    
    try:
        import firebird.driver as fdb_driver
        
        metrics = {
            'queries_executed': 0,
            'total_execution_time': 0.0,
            'tables_queried': set(),
            'connection_time': 0.0
        }
        
        # Time connection establishment
        start_time = time.time()
        with fdb_driver.connect(
            database="/home/projects/langchain_project/WINCASA2022.FDB",
            user="sysdba",
            password="masterkey"
        ) as conn:
            connection_time = time.time() - start_time
            metrics['connection_time'] = connection_time
            
            # Execute various queries and collect metrics
            test_queries = [
                ("SELECT COUNT(*) FROM BEWOHNER", "BEWOHNER"),
                ("SELECT COUNT(*) FROM OBJEKTE", "OBJEKTE"),
                ("SELECT COUNT(*) FROM EIGENTUEMER", "EIGENTUEMER"),
                ("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0", "SYSTEM"),
            ]
            
            for query, table in test_queries:
                start_time = time.time()
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()
                    query_time = time.time() - start_time
                    
                    metrics['queries_executed'] += 1
                    metrics['total_execution_time'] += query_time
                    metrics['tables_queried'].add(table)
                    
                    print(f"📊 {table}: {result[0] if result else 0} rows - {query_time:.3f}s")
        
        # Calculate summary metrics
        avg_query_time = metrics['total_execution_time'] / metrics['queries_executed']
        
        print(f"\n📈 Performance Summary:")
        print(f"🔗 Connection time: {metrics['connection_time']:.3f}s")
        print(f"📊 Queries executed: {metrics['queries_executed']}")
        print(f"⏱️  Total query time: {metrics['total_execution_time']:.3f}s")
        print(f"📊 Average query time: {avg_query_time:.3f}s")
        print(f"📋 Tables queried: {len(metrics['tables_queried'])}")
        
        return metrics['queries_executed'] > 0 and avg_query_time < 1.0
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        return False

def run_simple_connection_pool_test():
    """Run simplified connection pool concept test."""
    print("🎯 SIMPLE CONNECTION POOL CONCEPT TEST")
    print("=" * 80)
    print("Goal: Test basic connection optimization concepts")
    print("Focus: Connection reuse, query caching, performance metrics")
    print()
    
    test_results = {}
    
    # Run simplified tests
    test_results['embedded_connection'] = test_embedded_connection()
    test_results['connection_reuse'] = test_connection_reuse_performance()
    test_results['query_caching'] = test_query_caching_manual()
    test_results['performance_metrics'] = test_database_performance_metrics()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SIMPLE CONNECTION POOL TEST RESULTS")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title():30s} {status}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 SUCCESS! Connection optimization concepts verified")
        print("✅ Ready to implement full connection pooling")
    else:
        print("⚠️  NEEDS WORK: Basic connection optimizations failing")
        print("🔧 Review database configuration and permissions")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = run_simple_connection_pool_test()
    exit(0 if success else 1)