#!/usr/bin/env python3
"""
Query Result Cache for WINCASA Database
======================================

Implements intelligent caching for frequently accessed database queries
to improve performance across all retrieval modes.

Features:
- LRU cache with TTL (Time To Live)
- Query normalization for better cache hits
- Cache invalidation strategies
- Performance metrics and monitoring
- Persistent cache storage option
"""

import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    query_hash: str
    original_query: str
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def touch(self):
        """Update last access time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    expired_hits: int = 0
    evictions: int = 0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            **asdict(self),
            'hit_rate_percent': round(self.hit_rate(), 2)
        }


class QueryNormalizer:
    """Normalizes SQL queries for better cache key generation."""
    
    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalize SQL query for caching.
        
        Args:
            query: Original SQL query
            
        Returns:
            Normalized query string
        """
        # Remove extra whitespace and convert to uppercase
        normalized = ' '.join(query.strip().split()).upper()
        
        # Remove comments
        normalized = QueryNormalizer._remove_comments(normalized)
        
        # Normalize string literals (but preserve their structure)
        normalized = QueryNormalizer._normalize_string_literals(normalized)
        
        # Sort WHERE conditions for consistent ordering
        normalized = QueryNormalizer._sort_where_conditions(normalized)
        
        return normalized
    
    @staticmethod
    def _remove_comments(query: str) -> str:
        """Remove SQL comments."""
        # Remove line comments
        query = '\n'.join(line.split('--')[0] for line in query.split('\n'))
        
        # Remove block comments (simplified)
        while '/*' in query and '*/' in query:
            start = query.find('/*')
            end = query.find('*/', start) + 2
            if start != -1 and end != 1:
                query = query[:start] + query[end:]
            else:
                break
        
        return query
    
    @staticmethod
    def _normalize_string_literals(query: str) -> str:
        """Normalize string literals while preserving their meaning."""
        # For now, keep string literals as-is since they affect query semantics
        return query
    
    @staticmethod
    def _sort_where_conditions(query: str) -> str:
        """Sort WHERE conditions for consistent cache keys."""
        # Simplified implementation - full WHERE clause parsing is complex
        return query
    
    @staticmethod
    def generate_cache_key(query: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key for query and parameters.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Hash-based cache key
        """
        normalized_query = QueryNormalizer.normalize_query(query)
        
        # Include parameters in key if present
        if params:
            param_str = json.dumps(params, sort_keys=True)
            cache_input = f"{normalized_query}|{param_str}"
        else:
            cache_input = normalized_query
        
        # Generate SHA-256 hash
        return hashlib.sha256(cache_input.encode()).hexdigest()


class QueryResultCache:
    """
    High-performance LRU cache with TTL for database query results.
    
    Supports both in-memory and persistent storage options.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 300,  # 5 minutes
        persistent_cache_file: Optional[str] = None,
        enable_persistence: bool = True
    ):
        """
        Initialize query result cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl_seconds: Default TTL for cache entries
            persistent_cache_file: Path to persistent cache file
            enable_persistence: Whether to enable persistent storage
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_persistence = enable_persistence
        
        # In-memory cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU eviction
        self._lock = threading.RLock()
        
        # Performance statistics
        self.stats = CacheStats()
        
        # Persistent storage
        self.persistent_cache_file = persistent_cache_file or "wincasa_query_cache.db"
        if enable_persistence:
            self._init_persistent_storage()
            self._load_from_persistent_storage()
        
        logger.info(f"Query cache initialized: max_size={max_size}, ttl={default_ttl_seconds}s")
    
    def _init_persistent_storage(self):
        """Initialize SQLite database for persistent cache storage."""
        try:
            with sqlite3.connect(self.persistent_cache_file) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at REAL,
                        last_accessed REAL,
                        access_count INTEGER,
                        ttl_seconds INTEGER,
                        query_hash TEXT,
                        original_query TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON query_cache(last_accessed)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON query_cache(created_at)")
                conn.commit()
                
            logger.info(f"Persistent cache storage initialized: {self.persistent_cache_file}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize persistent storage: {e}")
            self.enable_persistence = False
    
    def _load_from_persistent_storage(self):
        """Load cache entries from persistent storage."""
        if not self.enable_persistence:
            return
        
        try:
            with sqlite3.connect(self.persistent_cache_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT key, value, created_at, last_accessed, access_count, 
                           ttl_seconds, query_hash, original_query
                    FROM query_cache
                    ORDER BY last_accessed DESC
                    LIMIT ?
                """, (self.max_size,))
                
                loaded_count = 0
                for row in cursor.fetchall():
                    key, value_blob, created_at, last_accessed, access_count, ttl_seconds, query_hash, original_query = row
                    
                    try:
                        # Deserialize value
                        value = pickle.loads(value_blob)
                        
                        # Create cache entry
                        entry = CacheEntry(
                            key=key,
                            value=value,
                            created_at=datetime.fromtimestamp(created_at),
                            last_accessed=datetime.fromtimestamp(last_accessed),
                            access_count=access_count,
                            ttl_seconds=ttl_seconds,
                            query_hash=query_hash,
                            original_query=original_query
                        )
                        
                        # Check if still valid
                        if not entry.is_expired():
                            self._cache[key] = entry
                            self._access_order.append(key)
                            loaded_count += 1
                    
                    except Exception as e:
                        logger.warning(f"Failed to load cache entry {key}: {e}")
                
                logger.info(f"Loaded {loaded_count} cache entries from persistent storage")
                
        except Exception as e:
            logger.warning(f"Failed to load from persistent storage: {e}")
    
    def get(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """
        Get cached result for query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = QueryNormalizer.generate_cache_key(query, params)
        
        with self._lock:
            if cache_key not in self._cache:
                self.stats.misses += 1
                return None
            
            entry = self._cache[cache_key]
            
            # Check if expired
            if entry.is_expired():
                self._remove_entry(cache_key)
                self.stats.expired_hits += 1
                self.stats.misses += 1
                return None
            
            # Update access info
            entry.touch()
            self._update_access_order(cache_key)
            
            self.stats.hits += 1
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return entry.value
    
    def put(
        self,
        query: str,
        result: Any,
        params: Optional[Dict] = None,
        ttl_seconds: Optional[int] = None
    ):
        """
        Store result in cache.
        
        Args:
            query: SQL query
            result: Query result to cache
            params: Query parameters
            ttl_seconds: TTL for this entry (uses default if None)
        """
        cache_key = QueryNormalizer.generate_cache_key(query, params)
        ttl = ttl_seconds or self.default_ttl_seconds
        
        with self._lock:
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=result,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl,
                query_hash=cache_key[:16],  # Short hash for identification
                original_query=query[:200]  # Truncated for storage
            )
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()
            
            # Store entry
            self._cache[cache_key] = entry
            self._update_access_order(cache_key)
            
            # Persist to storage if enabled
            if self.enable_persistence:
                self._persist_entry(entry)
            
            logger.debug(f"Cached result for query: {query[:50]}...")
    
    def _update_access_order(self, cache_key: str):
        """Update LRU access order."""
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        lru_key = self._access_order[0]
        self._remove_entry(lru_key)
        self.stats.evictions += 1
        logger.debug(f"Evicted LRU entry: {lru_key[:16]}")
    
    def _remove_entry(self, cache_key: str):
        """Remove entry from cache."""
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
    
    def _persist_entry(self, entry: CacheEntry):
        """Persist cache entry to storage."""
        if not self.enable_persistence:
            return
        
        try:
            with sqlite3.connect(self.persistent_cache_file) as conn:
                # Serialize value
                value_blob = pickle.dumps(entry.value)
                
                conn.execute("""
                    INSERT OR REPLACE INTO query_cache 
                    (key, value, created_at, last_accessed, access_count, 
                     ttl_seconds, query_hash, original_query)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    value_blob,
                    entry.created_at.timestamp(),
                    entry.last_accessed.timestamp(),
                    entry.access_count,
                    entry.ttl_seconds,
                    entry.query_hash,
                    entry.original_query
                ))
                conn.commit()
                
        except Exception as e:
            logger.warning(f"Failed to persist cache entry: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self.stats = CacheStats()
            
            if self.enable_persistence:
                try:
                    with sqlite3.connect(self.persistent_cache_file) as conn:
                        conn.execute("DELETE FROM query_cache")
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to clear persistent cache: {e}")
        
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            logger.info(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            self.stats.total_entries = len(self._cache)
            
            # Estimate memory usage
            try:
                import sys
                total_size = sum(
                    sys.getsizeof(entry.value) + sys.getsizeof(entry.key)
                    for entry in self._cache.values()
                )
                self.stats.memory_usage_bytes = total_size
            except Exception:
                self.stats.memory_usage_bytes = 0
            
            return self.stats.to_dict()
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed queries."""
        with self._lock:
            sorted_entries = sorted(
                self._cache.values(),
                key=lambda e: e.access_count,
                reverse=True
            )
            
            return [
                {
                    'query': entry.original_query,
                    'access_count': entry.access_count,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat()
                }
                for entry in sorted_entries[:limit]
            ]


# Global cache instance
_query_cache: Optional[QueryResultCache] = None
_cache_lock = threading.Lock()


def get_query_cache(
    max_size: int = 1000,
    default_ttl_seconds: int = 300,
    persistent_cache_file: Optional[str] = None
) -> QueryResultCache:
    """
    Get or create global query cache instance.
    
    Args:
        max_size: Maximum cache size
        default_ttl_seconds: Default TTL
        persistent_cache_file: Persistent storage file
        
    Returns:
        QueryResultCache instance
    """
    global _query_cache
    
    with _cache_lock:
        if _query_cache is None:
            _query_cache = QueryResultCache(
                max_size=max_size,
                default_ttl_seconds=default_ttl_seconds,
                persistent_cache_file=persistent_cache_file
            )
        
        return _query_cache


def test_query_result_cache():
    """Test the query result cache functionality."""
    print("🧪 Testing Query Result Cache")
    print("=" * 60)
    
    # Create test cache
    cache = QueryResultCache(max_size=5, default_ttl_seconds=60)
    
    # Test queries
    test_queries = [
        ("SELECT COUNT(*) FROM BEWOHNER", [("count", 1500)]),
        ("SELECT COUNT(*) FROM OBJEKTE", [("count", 800)]),
        ("SELECT BNAME FROM BEWOHNER WHERE BWO = 1", [("BNAME", "Müller")]),
        ("SELECT COUNT(*) FROM BEWOHNER", [("count", 1500)]),  # Should hit cache
    ]
    
    print("Testing cache operations:")
    for i, (query, result) in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        
        # Try to get from cache
        cached_result = cache.get(query)
        if cached_result:
            print(f"   ✅ Cache hit: {cached_result}")
        else:
            print(f"   ❌ Cache miss - storing result")
            cache.put(query, result)
    
    # Display statistics
    stats = cache.get_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   Hit rate: {stats['hit_rate_percent']:.1f}%")
    print(f"   Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"   Total entries: {stats['total_entries']}")
    
    # Test top queries
    top_queries = cache.get_top_queries(3)
    print(f"\n🔥 Top Queries:")
    for i, query_info in enumerate(top_queries, 1):
        print(f"   {i}. {query_info['query']} (accessed {query_info['access_count']} times)")
    
    print(f"\n✅ Query Result Cache test completed")


if __name__ == "__main__":
    test_query_result_cache()