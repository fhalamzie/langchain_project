#!/usr/bin/env python3
"""
WINCASA Central Query Logger
Persistent storage and analytics for all system queries
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
from collections import defaultdict

@dataclass
class QueryLogEntry:
    """Structure for query log entries"""
    timestamp: str
    query: str
    mode: str
    model: str
    user_id: str
    session_id: str
    response_time_ms: float
    result_count: int
    confidence: float
    cost_estimate: float
    success: bool
    error: Optional[str] = None
    answer_preview: Optional[str] = None
    source_data: Optional[str] = None
    
class WincasaQueryLogger:
    """
    Central Query Logger with SQLite persistence
    
    Features:
    - Persistent storage in SQLite database
    - Thread-safe operations
    - Query analytics and patterns
    - Cross-session history
    - Performance metrics
    """
    
    def __init__(self, db_path: str = "wincasa_data/query_logs.db", debug_mode: bool = False):
        self.db_path = Path(db_path)
        self.debug_mode = debug_mode
        self.lock = threading.Lock()
        
        # Ensure directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        if self.debug_mode:
            print(f"📝 Query Logger initialized: {self.db_path}")
            stats = self.get_statistics()
            print(f"   📊 Total queries logged: {stats['total_queries']:,}")
    
    def _init_database(self):
        """Initialize SQLite database with schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main query log table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                model TEXT,
                user_id TEXT,
                session_id TEXT,
                response_time_ms REAL,
                result_count INTEGER,
                confidence REAL,
                cost_estimate REAL,
                success INTEGER,
                error TEXT,
                answer_preview TEXT,
                source_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON query_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mode ON query_logs(mode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON query_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON query_logs(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_success ON query_logs(success)")
            
            # Analytics summary table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_analytics (
                date TEXT PRIMARY KEY,
                total_queries INTEGER,
                unique_users INTEGER,
                unique_sessions INTEGER,
                avg_response_time_ms REAL,
                success_rate REAL,
                total_cost REAL,
                mode_distribution TEXT,
                popular_queries TEXT,
                error_count INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
    
    def log_query(self, entry: QueryLogEntry) -> int:
        """Log a query to persistent storage"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                    INSERT INTO query_logs (
                        timestamp, query, mode, model, user_id, session_id,
                        response_time_ms, result_count, confidence, cost_estimate,
                        success, error, answer_preview, source_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.timestamp, entry.query, entry.mode, entry.model,
                        entry.user_id, entry.session_id, entry.response_time_ms,
                        entry.result_count, entry.confidence, entry.cost_estimate,
                        1 if entry.success else 0, entry.error, entry.answer_preview,
                        entry.source_data
                    ))
                    
                    query_id = cursor.lastrowid
                    conn.commit()
                    
                    if self.debug_mode:
                        print(f"✅ Query logged with ID: {query_id}")
                    
                    return query_id
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error logging query: {e}")
                return -1
    
    def get_history(self, 
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   limit: int = 100,
                   offset: int = 0,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get query history with filtering options"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM query_logs WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get query statistics for the last N days"""
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute(
                "SELECT COUNT(*) FROM query_logs WHERE timestamp >= ?",
                (cutoff_date,)
            )
            total_queries = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute(
                "SELECT AVG(CAST(success AS REAL)) FROM query_logs WHERE timestamp >= ?",
                (cutoff_date,)
            )
            success_rate = cursor.fetchone()[0] or 0.0
            
            # Average response time
            cursor.execute(
                "SELECT AVG(response_time_ms) FROM query_logs WHERE timestamp >= ?",
                (cutoff_date,)
            )
            avg_response_time = cursor.fetchone()[0] or 0.0
            
            # Unique users and sessions
            cursor.execute(
                "SELECT COUNT(DISTINCT user_id), COUNT(DISTINCT session_id) FROM query_logs WHERE timestamp >= ?",
                (cutoff_date,)
            )
            unique_users, unique_sessions = cursor.fetchone()
            
            # Mode distribution
            cursor.execute(
                "SELECT mode, COUNT(*) as count FROM query_logs WHERE timestamp >= ? GROUP BY mode",
                (cutoff_date,)
            )
            mode_distribution = dict(cursor.fetchall())
            
            # Error count
            cursor.execute(
                "SELECT COUNT(*) FROM query_logs WHERE timestamp >= ? AND error IS NOT NULL",
                (cutoff_date,)
            )
            error_count = cursor.fetchone()[0]
            
            # Total cost
            cursor.execute(
                "SELECT SUM(cost_estimate) FROM query_logs WHERE timestamp >= ?",
                (cutoff_date,)
            )
            total_cost = cursor.fetchone()[0] or 0.0
            
            return {
                "total_queries": total_queries,
                "success_rate": round(success_rate, 3),
                "avg_response_time_ms": round(avg_response_time, 2),
                "unique_users": unique_users,
                "unique_sessions": unique_sessions,
                "mode_distribution": mode_distribution,
                "error_count": error_count,
                "total_cost": round(total_cost, 2),
                "period_days": days
            }
    
    def get_popular_queries(self, days: int = 7, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular queries in the last N days"""
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Normalize queries by removing numbers and lowercase
            cursor.execute("""
            SELECT 
                LOWER(TRIM(query)) as normalized_query,
                COUNT(*) as count
            FROM query_logs
            WHERE timestamp >= ?
            GROUP BY normalized_query
            ORDER BY count DESC
            LIMIT ?
            """, (cutoff_date, limit))
            
            return cursor.fetchall()
    
    def get_error_patterns(self, days: int = 7) -> Dict[str, int]:
        """Analyze error patterns"""
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT error, COUNT(*) as count
            FROM query_logs
            WHERE timestamp >= ? AND error IS NOT NULL
            GROUP BY error
            ORDER BY count DESC
            """, (cutoff_date,))
            
            return dict(cursor.fetchall())
    
    def get_performance_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily performance trends"""
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as query_count,
                AVG(response_time_ms) as avg_response_time,
                AVG(CAST(success AS REAL)) as success_rate,
                SUM(cost_estimate) as daily_cost
            FROM query_logs
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
            """, (cutoff_date,))
            
            trends = []
            for row in cursor.fetchall():
                trends.append({
                    "date": row[0],
                    "query_count": row[1],
                    "avg_response_time_ms": round(row[2], 2),
                    "success_rate": round(row[3], 3),
                    "daily_cost": round(row[4] or 0, 2)
                })
            
            return trends
    
    def update_daily_analytics(self, date: Optional[str] = None):
        """Update daily analytics summary table"""
        
        if not date:
            date = datetime.now().date().isoformat()
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate daily statistics
                stats = {
                    "date": date,
                    "start": f"{date}T00:00:00",
                    "end": f"{date}T23:59:59"
                }
                
                # Get all metrics for the day
                cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(response_time_ms) as avg_response_time,
                    AVG(CAST(success AS REAL)) as success_rate,
                    SUM(cost_estimate) as total_cost,
                    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count
                FROM query_logs
                WHERE timestamp >= ? AND timestamp <= ?
                """, (stats["start"], stats["end"]))
                
                row = cursor.fetchone()
                if row and row[0] > 0:  # Has data
                    # Get mode distribution
                    cursor.execute("""
                    SELECT mode, COUNT(*) as count
                    FROM query_logs
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY mode
                    """, (stats["start"], stats["end"]))
                    mode_dist = dict(cursor.fetchall())
                    
                    # Get popular queries
                    cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM query_logs
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY LOWER(TRIM(query))
                    ORDER BY count DESC
                    LIMIT 10
                    """, (stats["start"], stats["end"]))
                    popular = [{"query": q, "count": c} for q, c in cursor.fetchall()]
                    
                    # Update or insert daily analytics
                    cursor.execute("""
                    INSERT OR REPLACE INTO daily_analytics (
                        date, total_queries, unique_users, unique_sessions,
                        avg_response_time_ms, success_rate, total_cost,
                        mode_distribution, popular_queries, error_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date, row[0], row[1], row[2],
                        round(row[3] or 0, 2), round(row[4] or 0, 3), round(row[5] or 0, 2),
                        json.dumps(mode_dist), json.dumps(popular), row[6]
                    ))
                    
                    conn.commit()
                    
                    if self.debug_mode:
                        print(f"📊 Daily analytics updated for {date}: {row[0]} queries")
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """Clean up logs older than specified days"""
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count logs to be deleted
                cursor.execute(
                    "SELECT COUNT(*) FROM query_logs WHERE timestamp < ?",
                    (cutoff_date,)
                )
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Delete old logs
                    cursor.execute(
                        "DELETE FROM query_logs WHERE timestamp < ?",
                        (cutoff_date,)
                    )
                    conn.commit()
                    
                    if self.debug_mode:
                        print(f"🗑️  Cleaned up {count} old query logs")
                
                # Vacuum to reclaim space
                cursor.execute("VACUUM")

# Singleton instance
_query_logger_instance = None

def get_query_logger(debug_mode: bool = False) -> WincasaQueryLogger:
    """Get singleton instance of query logger"""
    global _query_logger_instance
    if _query_logger_instance is None:
        _query_logger_instance = WincasaQueryLogger(debug_mode=debug_mode)
    return _query_logger_instance

def test_query_logger():
    """Test the query logger"""
    print("🧪 Testing WINCASA Query Logger...")
    
    logger = get_query_logger(debug_mode=True)
    
    # Test logging
    print("\n1. Logging test queries...")
    
    test_queries = [
        QueryLogEntry(
            timestamp=datetime.now().isoformat(),
            query="Zeige alle Mieter in der Bergstraße",
            mode="optimized_search",
            model="gpt-4",
            user_id="test_user",
            session_id="test_session_001",
            response_time_ms=125.5,
            result_count=5,
            confidence=0.95,
            cost_estimate=0.02,
            success=True,
            answer_preview="5 Mieter gefunden in Bergstraße..."
        ),
        QueryLogEntry(
            timestamp=datetime.now().isoformat(),
            query="Portfolio von Bona Casa GmbH",
            mode="sql_template",
            model="gpt-3.5-turbo",
            user_id="test_user",
            session_id="test_session_001",
            response_time_ms=450.2,
            result_count=12,
            confidence=0.88,
            cost_estimate=0.01,
            success=True,
            answer_preview="Bona Casa GmbH besitzt 12 Einheiten..."
        ),
        QueryLogEntry(
            timestamp=datetime.now().isoformat(),
            query="Ungültige SQL Abfrage",
            mode="legacy_sql",
            model="gpt-3.5-turbo",
            user_id="test_user",
            session_id="test_session_001",
            response_time_ms=50.0,
            result_count=0,
            confidence=0.0,
            cost_estimate=0.005,
            success=False,
            error="SQL syntax error near 'Ungültige'"
        )
    ]
    
    for entry in test_queries:
        query_id = logger.log_query(entry)
        print(f"   Logged query {query_id}: {entry.query[:50]}...")
    
    # Test retrieval
    print("\n2. Retrieving history...")
    history = logger.get_history(limit=5)
    print(f"   Found {len(history)} recent queries")
    for h in history[:3]:
        print(f"   - {h['timestamp']}: {h['query'][:40]}... ({h['mode']})")
    
    # Test statistics
    print("\n3. Query statistics...")
    stats = logger.get_statistics(days=30)
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Success rate: {stats['success_rate']*100:.1f}%")
    print(f"   Avg response time: {stats['avg_response_time_ms']:.1f}ms")
    print(f"   Mode distribution: {stats['mode_distribution']}")
    
    # Test popular queries
    print("\n4. Popular queries...")
    popular = logger.get_popular_queries(days=7, limit=5)
    for query, count in popular[:3]:
        print(f"   - '{query[:50]}...' ({count} times)")
    
    # Test performance trends
    print("\n5. Performance trends...")
    trends = logger.get_performance_trends(days=7)
    for trend in trends[-3:]:
        print(f"   {trend['date']}: {trend['query_count']} queries, "
              f"{trend['avg_response_time_ms']:.1f}ms avg, "
              f"{trend['success_rate']*100:.1f}% success")
    
    # Update daily analytics
    print("\n6. Updating daily analytics...")
    logger.update_daily_analytics()
    
    print("\n✅ Query logger test completed!")

if __name__ == "__main__":
    test_query_logger()