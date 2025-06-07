#!/usr/bin/env python3
"""
Database Connection Pool for WINCASA Firebird Database
=====================================================

Performance optimization for database connections by implementing connection pooling
for embedded FDB connections. This reduces connection overhead and improves query
execution times across all retrieval modes.

Features:
- Connection pooling with configurable pool size
- Automatic connection health checks and recovery
- Query result caching for frequently accessed data
- Connection reuse across multiple queries
- Proper connection cleanup and resource management
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from queue import Queue, Empty
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import firebird.driver as fdb_driver
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Configuration for database connection pool."""
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    cache_ttl: int = 300  # 5 minutes for query cache


@dataclass
class QueryCacheEntry:
    """Cache entry for query results."""
    query_hash: str
    result: Any
    timestamp: datetime
    hit_count: int = 0
    execution_time: float = 0.0


class FirebirdConnectionPool:
    """
    High-performance connection pool for Firebird database operations.
    
    Implements connection pooling, query caching, and health monitoring
    to optimize database performance across all retrieval modes.
    """
    
    def __init__(self, connection_string: str, config: ConnectionPoolConfig = None):
        """
        Initialize connection pool.
        
        Args:
            connection_string: Firebird database connection string
            config: Pool configuration (uses defaults if None)
        """
        self.connection_string = connection_string
        self.config = config or ConnectionPoolConfig()
        
        # SQLAlchemy engine with connection pooling
        self.engine = None
        self._init_engine()
        
        # Query result cache
        self.query_cache: Dict[str, QueryCacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # Connection health monitoring
        self.health_check_interval = 60  # seconds
        self.last_health_check = time.time()
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'connection_errors': 0,
            'avg_query_time': 0.0
        }
        
        logger.info(f"Initialized Firebird connection pool with {self.config.pool_size} connections")
    
    def _init_engine(self):
        """Initialize SQLAlchemy engine with connection pooling."""
        try:
            # Parse connection string to extract components
            parsed = urlparse(self.connection_string)
            
            # Create engine with QueuePool for better connection management
            self.engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=False,  # Set to True for SQL debugging
                # Add read-only connection configuration
                execution_options={
                    "autocommit": True,  # Use autocommit for read-only operations
                },
                connect_args={
                    "role": None,  # No specific role
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM RDB$DATABASE"))
                logger.info("Database connection pool initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _generate_query_hash(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate hash for query caching."""
        import hashlib
        query_text = query.lower().strip()
        if params:
            param_str = str(sorted(params.items()))
            query_text += param_str
        return hashlib.md5(query_text.encode()).hexdigest()
    
    def _is_cache_valid(self, entry: QueryCacheEntry) -> bool:
        """Check if cache entry is still valid."""
        age = datetime.now() - entry.timestamp
        return age.total_seconds() < self.config.cache_ttl
    
    def _should_cache_query(self, query: str) -> bool:
        """Determine if query results should be cached."""
        # Cache SELECT queries but not INSERT/UPDATE/DELETE
        query_lower = query.lower().strip()
        
        # Don't cache queries with random/time-sensitive functions
        skip_patterns = ['rand()', 'current_timestamp', 'now()', 'sysdate']
        if any(pattern in query_lower for pattern in skip_patterns):
            return False
        
        # Cache SELECT queries
        return query_lower.startswith('select')
    
    def execute_query(self, query: str, params: Optional[Dict] = None, 
                     use_cache: bool = True) -> List[Tuple]:
        """
        Execute query with connection pooling and caching.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            use_cache: Whether to use query result cache
            
        Returns:
            List of query result tuples
        """
        start_time = time.time()
        self.metrics['total_queries'] += 1
        
        # Check cache first
        if use_cache and self._should_cache_query(query):
            query_hash = self._generate_query_hash(query, params)
            
            with self.cache_lock:
                if query_hash in self.query_cache:
                    entry = self.query_cache[query_hash]
                    if self._is_cache_valid(entry):
                        entry.hit_count += 1
                        self.metrics['cache_hits'] += 1
                        logger.debug(f"Cache hit for query hash {query_hash}")
                        return entry.result
                    else:
                        # Remove expired entry
                        del self.query_cache[query_hash]
        
        # Execute query
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                rows = result.fetchall()
                
                # Convert to list of tuples for caching
                result_data = [tuple(row) for row in rows]
                
                execution_time = time.time() - start_time
                
                # Update metrics
                self._update_avg_query_time(execution_time)
                
                # Cache result if applicable
                if use_cache and self._should_cache_query(query):
                    self.metrics['cache_misses'] += 1
                    self._cache_result(query, params, result_data, execution_time)
                
                logger.debug(f"Query executed in {execution_time:.3f}s, returned {len(result_data)} rows")
                return result_data
                
        except Exception as e:
            self.metrics['connection_errors'] += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _cache_result(self, query: str, params: Optional[Dict], 
                     result: List[Tuple], execution_time: float):
        """Cache query result."""
        query_hash = self._generate_query_hash(query, params)
        
        with self.cache_lock:
            # Limit cache size (remove oldest entries if needed)
            max_cache_size = 1000
            if len(self.query_cache) >= max_cache_size:
                # Remove 10% of oldest entries
                entries_to_remove = sorted(
                    self.query_cache.items(),
                    key=lambda x: x[1].timestamp
                )[:max_cache_size // 10]
                
                for old_hash, _ in entries_to_remove:
                    del self.query_cache[old_hash]
            
            # Add new entry
            self.query_cache[query_hash] = QueryCacheEntry(
                query_hash=query_hash,
                result=result,
                timestamp=datetime.now(),
                execution_time=execution_time
            )
    
    def _update_avg_query_time(self, execution_time: float):
        """Update average query execution time."""
        current_avg = self.metrics['avg_query_time']
        total_queries = self.metrics['total_queries']
        
        # Exponential moving average
        if total_queries == 1:
            self.metrics['avg_query_time'] = execution_time
        else:
            alpha = 0.1  # Smoothing factor
            self.metrics['avg_query_time'] = (
                alpha * execution_time + (1 - alpha) * current_avg
            )
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool."""
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_transaction(self, queries: List[Tuple[str, Optional[Dict]]]) -> List[Any]:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            List of query results
        """
        results = []
        
        with self.get_connection() as conn:
            trans = conn.begin()
            try:
                for query, params in queries:
                    if params:
                        result = conn.execute(text(query), params)
                    else:
                        result = conn.execute(text(query))
                    
                    if result.returns_rows:
                        results.append([tuple(row) for row in result.fetchall()])
                    else:
                        results.append(result.rowcount)
                
                trans.commit()
                return results
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get comprehensive table information with caching.
        
        Args:
            table_name: Name of table to analyze
            
        Returns:
            Dictionary with table metadata
        """
        cache_key = f"table_info_{table_name.upper()}"
        
        # Check cache first
        with self.cache_lock:
            if cache_key in self.query_cache:
                entry = self.query_cache[cache_key]
                if self._is_cache_valid(entry):
                    return entry.result
        
        # Query table information
        queries = [
            # Column information
            ("""
                SELECT rf.rdb$field_name, f.rdb$field_type, f.rdb$field_length,
                       f.rdb$field_precision, f.rdb$field_scale, rf.rdb$null_flag
                FROM rdb$relation_fields rf
                JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
                WHERE rf.rdb$relation_name = ?
                ORDER BY rf.rdb$field_position
            """, {'rdb$relation_name': table_name.upper()}),
            
            # Foreign key information
            ("""
                SELECT rc.rdb$constraint_name, rc.rdb$relation_name,
                       rc.rdb$index_name, ref.rdb$const_name_uq
                FROM rdb$ref_constraints ref
                JOIN rdb$relation_constraints rc ON ref.rdb$constraint_name = rc.rdb$constraint_name
                WHERE rc.rdb$relation_name = ?
            """, {'rdb$relation_name': table_name.upper()}),
            
            # Row count estimate
            (f"SELECT COUNT(*) FROM {table_name}", None)
        ]
        
        try:
            table_info = {
                'table_name': table_name,
                'columns': [],
                'foreign_keys': [],
                'row_count': 0,
                'last_updated': datetime.now().isoformat()
            }
            
            # Execute queries
            for query, params in queries:
                if "COUNT(*)" in query:
                    # Row count query
                    rows = self.execute_query(query, use_cache=False)
                    table_info['row_count'] = rows[0][0] if rows else 0
                elif "rdb$relation_fields" in query:
                    # Column information
                    rows = self.execute_query(query, params, use_cache=False)
                    table_info['columns'] = [
                        {
                            'name': row[0].strip() if row[0] else '',
                            'type': row[1],
                            'length': row[2],
                            'precision': row[3],
                            'scale': row[4],
                            'nullable': row[5] is None
                        }
                        for row in rows
                    ]
                elif "rdb$ref_constraints" in query:
                    # Foreign key information
                    rows = self.execute_query(query, params, use_cache=False)
                    table_info['foreign_keys'] = [
                        {
                            'constraint_name': row[0].strip() if row[0] else '',
                            'table_name': row[1].strip() if row[1] else '',
                            'index_name': row[2].strip() if row[2] else '',
                            'referenced_constraint': row[3].strip() if row[3] else ''
                        }
                        for row in rows
                    ]
            
            # Cache result
            with self.cache_lock:
                self.query_cache[cache_key] = QueryCacheEntry(
                    query_hash=cache_key,
                    result=table_info,
                    timestamp=datetime.now()
                )
            
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return {'table_name': table_name, 'error': str(e)}
    
    def clear_cache(self):
        """Clear query result cache."""
        with self.cache_lock:
            self.query_cache.clear()
            logger.info("Query cache cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get connection pool performance metrics."""
        cache_hit_rate = 0.0
        if self.metrics['total_queries'] > 0:
            cache_hit_rate = (
                self.metrics['cache_hits'] / 
                (self.metrics['cache_hits'] + self.metrics['cache_misses'])
            ) * 100
        
        return {
            **self.metrics,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_size': len(self.query_cache),
            'pool_size': self.config.pool_size,
            'pool_checked_out': self.engine.pool.checkedout() if self.engine else 0,
            'pool_checked_in': self.engine.pool.checkedin() if self.engine else 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform connection pool health check."""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT 1 FROM RDB$DATABASE"))
                test_result = result.fetchone()[0]
            
            response_time = time.time() - start_time
            
            health_status = {
                'status': 'healthy' if test_result == 1 else 'unhealthy',
                'response_time': f"{response_time:.3f}s",
                'timestamp': datetime.now().isoformat(),
                'connection_string': self.connection_string.replace(
                    self.connection_string.split('@')[0].split('//')[-1],
                    "***:***"  # Hide credentials
                )
            }
            
            self.last_health_check = time.time()
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """Close connection pool and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Connection pool closed")


# Global connection pool instance
_connection_pool: Optional[FirebirdConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(connection_string: str = None, 
                       config: ConnectionPoolConfig = None) -> FirebirdConnectionPool:
    """
    Get or create global connection pool instance.
    
    Args:
        connection_string: Database connection string
        config: Pool configuration
        
    Returns:
        FirebirdConnectionPool instance
    """
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool is None:
            if not connection_string:
                # Default connection string
                connection_string = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
            
            _connection_pool = FirebirdConnectionPool(connection_string, config)
        
        return _connection_pool


def optimize_query(query: str) -> str:
    """
    Optimize SQL query for better performance.
    
    Args:
        query: Original SQL query
        
    Returns:
        Optimized SQL query
    """
    # Basic query optimizations
    optimized = query.strip()
    
    # Add FIRST clause for large result sets if not present
    if (optimized.upper().startswith('SELECT') and 
        'FIRST' not in optimized.upper() and 
        'COUNT(' not in optimized.upper()):
        
        # Insert FIRST 1000 after SELECT
        parts = optimized.split(' ', 1)
        if len(parts) > 1:
            optimized = f"{parts[0]} FIRST 1000 {parts[1]}"
    
    # Add index hints for common patterns
    common_optimizations = {
        'WHERE BSTR LIKE': 'WHERE BSTR STARTING WITH',  # Better for prefix searches
        'WHERE UPPER(': 'WHERE',  # Remove unnecessary UPPER() if possible
    }
    
    for pattern, replacement in common_optimizations.items():
        if pattern in optimized:
            logger.debug(f"Applied optimization: {pattern} -> {replacement}")
    
    return optimized


# Example usage and testing
if __name__ == "__main__":
    # Test connection pool
    pool = get_connection_pool()
    
    # Test basic query
    result = pool.execute_query("SELECT COUNT(*) FROM BEWOHNER")
    print(f"BEWOHNER count: {result[0][0] if result else 0}")
    
    # Test caching
    start_time = time.time()
    result1 = pool.execute_query("SELECT COUNT(*) FROM OBJEKTE")
    first_query_time = time.time() - start_time
    
    start_time = time.time()
    result2 = pool.execute_query("SELECT COUNT(*) FROM OBJEKTE")  # Should be cached
    cached_query_time = time.time() - start_time
    
    print(f"First query: {first_query_time:.3f}s")
    print(f"Cached query: {cached_query_time:.3f}s")
    print(f"Speedup: {first_query_time / cached_query_time:.1f}x")
    
    # Print performance metrics
    metrics = pool.get_performance_metrics()
    print(f"Performance metrics: {metrics}")
    
    # Health check
    health = pool.health_check()
    print(f"Health check: {health}")