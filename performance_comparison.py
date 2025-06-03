#!/usr/bin/env python3
"""
Performance comparison between SQLAlchemy and Direct FDB approaches
"""

import time
import os
import statistics
from typing import Dict, List, Any
from datetime import datetime
import json

from fdb_direct_interface import FDBDirectInterface
from sqlalchemy import create_engine, text
import fdb


class PerformanceComparison:
    """Compare performance of different database access methods"""
    
    def __init__(self, db_path: str = "WINCASA2022.FDB"):
        self.db_path = os.path.abspath(db_path)
        self.results = []
        
    def setup_sqlalchemy(self):
        """Setup SQLAlchemy connection"""
        try:
            # Set Firebird environment
            fb_temp = os.path.join(os.path.dirname(self.db_path), "fb_temp_sqlalchemy")
            os.makedirs(fb_temp, exist_ok=True)
            os.environ['FIREBIRD_TMP'] = fb_temp
            os.environ['FIREBIRD_LOCK'] = fb_temp
            
            connection_string = f"firebird+fdb://sysdba:masterkey@localhost/{self.db_path}"
            self.sqlalchemy_engine = create_engine(connection_string)
            return True
        except Exception as e:
            print(f"SQLAlchemy setup failed: {e}")
            return False
            
    def setup_direct_fdb(self):
        """Setup direct FDB connection"""
        try:
            self.fdb_interface = FDBDirectInterface(self.db_path, "sysdba", "masterkey")
            return True
        except Exception as e:
            print(f"Direct FDB setup failed: {e}")
            return False
            
    def setup_raw_fdb(self):
        """Setup raw FDB connection for baseline comparison"""
        try:
            # Set Firebird environment
            fb_temp = os.path.join(os.path.dirname(self.db_path), "fb_temp_raw")
            os.makedirs(fb_temp, exist_ok=True)
            os.environ['FIREBIRD_TMP'] = fb_temp
            os.environ['FIREBIRD_LOCK'] = fb_temp
            
            self.raw_connection = fdb.connect(
                dsn=self.db_path,
                user='sysdba',
                password='masterkey',
                charset='UTF8'
            )
            return True
        except Exception as e:
            print(f"Raw FDB setup failed: {e}")
            return False
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            return elapsed, result, None
        except Exception as e:
            elapsed = time.time() - start
            return elapsed, None, str(e)
            
    def test_simple_query(self, method: str, query: str = "SELECT FIRST 10 * FROM BEWOHNER"):
        """Test a simple query with different methods"""
        
        if method == "sqlalchemy":
            if not hasattr(self, 'sqlalchemy_engine'):
                return None
                
            def run_query():
                with self.sqlalchemy_engine.connect() as conn:
                    result = conn.execute(text(query))
                    return list(result)
                    
        elif method == "direct_fdb":
            if not hasattr(self, 'fdb_interface'):
                return None
                
            def run_query():
                return self.fdb_interface.run_sql(query)
                
        elif method == "raw_fdb":
            if not hasattr(self, 'raw_connection'):
                return None
                
            def run_query():
                cursor = self.raw_connection.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                return result
        else:
            return None
            
        return self.measure_time(run_query)
        
    def test_schema_info(self, method: str):
        """Test schema information retrieval"""
        
        if method == "sqlalchemy":
            if not hasattr(self, 'sqlalchemy_engine'):
                return None
                
            def get_tables():
                from sqlalchemy import inspect
                inspector = inspect(self.sqlalchemy_engine)
                return inspector.get_table_names()
                
        elif method == "direct_fdb":
            if not hasattr(self, 'fdb_interface'):
                return None
                
            def get_tables():
                return self.fdb_interface.get_table_names()
                
        elif method == "raw_fdb":
            if not hasattr(self, 'raw_connection'):
                return None
                
            def get_tables():
                cursor = self.raw_connection.cursor()
                cursor.execute("""
                    SELECT DISTINCT RDB$RELATION_NAME 
                    FROM RDB$RELATIONS 
                    WHERE RDB$SYSTEM_FLAG=0 
                    ORDER BY RDB$RELATION_NAME
                """)
                tables = [row[0].strip() for row in cursor.fetchall()]
                cursor.close()
                return tables
        else:
            return None
            
        return self.measure_time(get_tables)
        
    def run_benchmark(self, test_name: str, test_func, iterations: int = 5):
        """Run a benchmark test multiple times"""
        methods = ["raw_fdb", "direct_fdb", "sqlalchemy"]
        
        print(f"\n{test_name}")
        print("-" * 60)
        
        for method in methods:
            times = []
            errors = []
            
            for i in range(iterations):
                result = test_func(method)
                if result:
                    elapsed, data, error = result
                    if error:
                        errors.append(error)
                    else:
                        times.append(elapsed)
                        
            if times:
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                min_time = min(times)
                max_time = max(times)
                
                print(f"\n{method.upper()}:")
                print(f"  Average: {avg_time:.4f}s")
                print(f"  Median: {median_time:.4f}s")
                print(f"  Min: {min_time:.4f}s")
                print(f"  Max: {max_time:.4f}s")
                
                if len(times) > 1:
                    std_dev = statistics.stdev(times)
                    print(f"  Std Dev: {std_dev:.4f}s")
                    
                self.results.append({
                    "test": test_name,
                    "method": method,
                    "iterations": len(times),
                    "avg_time": avg_time,
                    "median_time": median_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "errors": errors
                })
            else:
                print(f"\n{method.upper()}: Failed")
                if errors:
                    print(f"  Errors: {errors[0]}")
                    
    def run_all_benchmarks(self):
        """Run all benchmark tests"""
        print("="*60)
        print("Performance Comparison: SQLAlchemy vs Direct FDB vs Raw FDB")
        print("="*60)
        
        # Setup connections
        print("\nSetting up connections...")
        raw_ok = self.setup_raw_fdb()
        print(f"Raw FDB: {'✓' if raw_ok else '✗'}")
        
        direct_ok = self.setup_direct_fdb()
        print(f"Direct FDB Interface: {'✓' if direct_ok else '✗'}")
        
        sqlalchemy_ok = self.setup_sqlalchemy()
        print(f"SQLAlchemy: {'✓' if sqlalchemy_ok else '✗'}")
        
        # Run benchmarks
        self.run_benchmark("Simple SELECT Query", self.test_simple_query, iterations=10)
        self.run_benchmark("Schema Information Retrieval", self.test_schema_info, iterations=5)
        
        # Test different query complexities
        queries = [
            ("Small Result Set", "SELECT FIRST 1 * FROM BEWOHNER"),
            ("Medium Result Set", "SELECT FIRST 100 * FROM BEWOHNER"),
            ("COUNT Query", "SELECT COUNT(*) FROM BEWOHNER"),
            ("JOIN Query", """
                SELECT FIRST 10 b.*, w.* 
                FROM BEWOHNER b 
                JOIN WOHNUNG w ON b.WHGNR = w.WHGNR
            """)
        ]
        
        for query_name, query in queries:
            self.run_benchmark(
                f"Query Test: {query_name}", 
                lambda method: self.test_simple_query(method, query),
                iterations=5
            )
            
        # Save results
        self.save_results()
        
        # Cleanup
        self.cleanup()
        
    def save_results(self):
        """Save benchmark results"""
        os.makedirs("output/benchmarks", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/benchmarks/performance_comparison_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "database": self.db_path,
                "results": self.results
            }, f, indent=2)
            
        print(f"\nResults saved to: {filename}")
        
    def cleanup(self):
        """Clean up connections"""
        if hasattr(self, 'raw_connection'):
            self.raw_connection.close()
        if hasattr(self, 'fdb_interface'):
            # FDBDirectInterface doesn't have a close method, 
            # connections are managed internally
            pass
        if hasattr(self, 'sqlalchemy_engine'):
            self.sqlalchemy_engine.dispose()


def main():
    """Main entry point"""
    comparison = PerformanceComparison()
    comparison.run_all_benchmarks()


if __name__ == "__main__":
    main()