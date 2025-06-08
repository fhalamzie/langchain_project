#!/usr/bin/env python3
"""
Test Database Connection Pool Optimization
==========================================

Test the performance improvements from implementing connection pooling
for embedded FDB connections in the WINCASA retrieval system.

Tests:
1. Connection pool initialization and basic functionality
2. Query caching performance improvements
3. Connection reuse vs new connections
4. Performance metrics collection
5. Health monitoring
"""

import time
import statistics
from typing import List, Dict, Any
from database_connection_pool import (
    get_connection_pool, 
    ConnectionPoolConfig, 
    FirebirdConnectionPool
)
from filtered_langchain_retriever import FilteredLangChainSQLRetriever
from gemini_llm import get_gemini_llm

def test_connection_pool_basic_functionality():
    """Test basic connection pool functionality."""
    print("🧪 Testing Connection Pool Basic Functionality")
    print("=" * 60)
    
    # Test with default configuration
    pool = get_connection_pool()
    
    # Test basic query
    start_time = time.time()
    result = pool.execute_query("SELECT COUNT(*) FROM BEWOHNER")
    execution_time = time.time() - start_time
    
    print(f"✅ Basic query executed in {execution_time:.3f}s")
    print(f"📊 BEWOHNER count: {result[0][0] if result else 0}")
    
    # Test health check
    health = pool.health_check()
    print(f"💚 Health check: {health['status']}")
    
    return True

def test_query_caching_performance():
    """Test query caching performance improvements."""
    print("\n🧪 Testing Query Caching Performance")
    print("=" * 60)
    
    pool = get_connection_pool()
    
    # Test queries that should be cached
    test_queries = [
        "SELECT COUNT(*) FROM OBJEKTE",
        "SELECT COUNT(*) FROM BEWOHNER",
        "SELECT COUNT(*) FROM EIGENTUEMER",
        "SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0"
    ]
    
    # First execution (cache miss)
    first_run_times = []
    for query in test_queries:
        start_time = time.time()
        result = pool.execute_query(query)
        execution_time = time.time() - start_time
        first_run_times.append(execution_time)
        print(f"⏱️  First run: {query[:30]}... - {execution_time:.3f}s")
    
    print(f"\n📊 Average first run time: {statistics.mean(first_run_times):.3f}s")
    
    # Second execution (cache hit)
    second_run_times = []
    for query in test_queries:
        start_time = time.time()
        result = pool.execute_query(query)
        execution_time = time.time() - start_time
        second_run_times.append(execution_time)
        print(f"🚀 Cached run: {query[:30]}... - {execution_time:.3f}s")
    
    print(f"📊 Average cached run time: {statistics.mean(second_run_times):.3f}s")
    
    # Calculate performance improvement
    avg_first = statistics.mean(first_run_times)
    avg_cached = statistics.mean(second_run_times)
    speedup = avg_first / avg_cached if avg_cached > 0 else 1
    
    print(f"🎯 Cache speedup: {speedup:.1f}x")
    
    # Get cache metrics
    metrics = pool.get_performance_metrics()
    print(f"📈 Cache hit rate: {metrics.get('cache_hit_rate', 'N/A')}")
    
    return speedup > 1.5  # Expect at least 1.5x speedup from caching

def test_connection_reuse_vs_new():
    """Test performance of connection reuse vs creating new connections."""
    print("\n🧪 Testing Connection Reuse vs New Connections")
    print("=" * 60)
    
    # Test with connection pool (reuse)
    pool = get_connection_pool()
    
    start_time = time.time()
    for i in range(10):
        result = pool.execute_query("SELECT 1 FROM RDB$DATABASE")
    pooled_time = time.time() - start_time
    
    print(f"⚡ 10 queries with connection pool: {pooled_time:.3f}s")
    print(f"📊 Average per query: {pooled_time/10:.3f}s")
    
    # Test direct connections (new each time)
    import firebird.driver as fdb_driver
    
    start_time = time.time()
    for i in range(10):
        with fdb_driver.connect(
            database="/home/projects/langchain_project/WINCASA2022.FDB",
            user="sysdba",
            password="masterkey"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM RDB$DATABASE")
                result = cur.fetchone()
    direct_time = time.time() - start_time
    
    print(f"🐌 10 queries with new connections: {direct_time:.3f}s")
    print(f"📊 Average per query: {direct_time/10:.3f}s")
    
    # Calculate improvement
    improvement = direct_time / pooled_time if pooled_time > 0 else 1
    print(f"🎯 Connection pooling speedup: {improvement:.1f}x")
    
    return improvement > 1.2  # Expect at least 1.2x speedup from pooling

def test_filtered_langchain_with_pool():
    """Test FilteredLangChainSQLRetriever with connection pooling."""
    print("\n🧪 Testing Filtered LangChain with Connection Pool")
    print("=" * 60)
    
    db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
    
    try:
        llm = get_gemini_llm()
        
        retriever = FilteredLangChainSQLRetriever(
            db_connection_string=db_connection,
            llm=llm,
            enable_monitoring=False
        )
        
        # Test query that should use connection pool
        test_query = "Wie viele Wohnungen gibt es insgesamt?"
        
        start_time = time.time()
        documents = retriever.retrieve_documents(test_query, max_docs=3)
        execution_time = time.time() - start_time
        
        print(f"✅ Query executed in {execution_time:.3f}s")
        print(f"📄 Retrieved {len(documents)} documents")
        
        # Get performance metrics
        metrics = retriever.get_performance_metrics()
        print(f"📊 Schema reduction: {metrics.get('schema_reduction_percentage', 0)}%")
        
        if 'connection_pool' in metrics:
            pool_metrics = metrics['connection_pool']
            print(f"🔗 Pool queries: {pool_metrics.get('total_queries', 0)}")
            print(f"💾 Cache hit rate: {pool_metrics.get('cache_hit_rate', '0%')}")
        
        return len(documents) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance metrics collection."""
    print("\n🧪 Testing Performance Monitoring")
    print("=" * 60)
    
    pool = get_connection_pool()
    
    # Execute several queries to generate metrics
    for i in range(5):
        pool.execute_query("SELECT COUNT(*) FROM BEWOHNER")
        pool.execute_query("SELECT COUNT(*) FROM OBJEKTE")
    
    # Get metrics
    metrics = pool.get_performance_metrics()
    
    print(f"📊 Total queries: {metrics.get('total_queries', 0)}")
    print(f"💾 Cache hits: {metrics.get('cache_hits', 0)}")
    print(f"❌ Cache misses: {metrics.get('cache_misses', 0)}")
    print(f"🎯 Cache hit rate: {metrics.get('cache_hit_rate', '0%')}")
    print(f"⏱️  Average query time: {metrics.get('avg_query_time', 0):.3f}s")
    print(f"🔗 Pool size: {metrics.get('pool_size', 0)}")
    print(f"📦 Cache size: {metrics.get('cache_size', 0)}")
    
    # Test health check
    health = pool.health_check()
    print(f"💚 Database health: {health.get('status', 'unknown')}")
    print(f"⏱️  Health check time: {health.get('response_time', 'N/A')}")
    
    return metrics.get('total_queries', 0) >= 10

def run_comprehensive_connection_pool_test():
    """Run comprehensive connection pool optimization test."""
    print("🎯 COMPREHENSIVE CONNECTION POOL OPTIMIZATION TEST")
    print("=" * 80)
    print("Goal: Verify performance improvements from connection pooling")
    print("Focus: Query caching, connection reuse, performance monitoring")
    print()
    
    test_results = {}
    
    # Run all tests
    test_results['basic_functionality'] = test_connection_pool_basic_functionality()
    test_results['query_caching'] = test_query_caching_performance()
    test_results['connection_reuse'] = test_connection_reuse_vs_new()
    test_results['filtered_langchain'] = test_filtered_langchain_with_pool()
    test_results['performance_monitoring'] = test_performance_monitoring()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 CONNECTION POOL OPTIMIZATION TEST RESULTS")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title():30s} {status}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 SUCCESS! Connection pool optimization working effectively")
        print("✅ Ready for production use with improved database performance")
    else:
        print("⚠️  PARTIAL SUCCESS: Some optimizations need refinement")
        print("🔧 Review failed tests and optimize connection pool configuration")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = run_comprehensive_connection_pool_test()
    exit(0 if success else 1)