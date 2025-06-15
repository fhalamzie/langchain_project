#!/usr/bin/env python3
"""
WINCASA Unified Query Logger
Kombiniert Query Logging mit Query Path Tracking
"""

import os
import json
import sqlite3
import time
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
import threading
from collections import defaultdict

# Setup logging
logger = logging.getLogger('unified_logger')
logger.setLevel(logging.INFO)

# File handler für Query Paths
log_dir = Path('./logs')
log_dir.mkdir(exist_ok=True)
handler = logging.FileHandler(log_dir / 'query_paths.log')
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
logger.addHandler(handler)

@dataclass
class QueryPathEvent:
    """Einzelnes Event im Query Path"""
    timestamp: str
    layer: str  # streamlit, query_engine, unified_template, optimized_search, llm_handler, data_access
    event_type: str  # start, decision, transform, execute, result, error
    details: Dict[str, Any]
    duration_ms: Optional[float] = None

@dataclass
class QueryLogEntry:
    """Structure for query log entries with path tracking"""
    query_id: str  # NEW: Shared ID for path tracking
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
    # NEW: Path tracking fields
    selected_modes: List[str] = field(default_factory=list)
    path_events: List[QueryPathEvent] = field(default_factory=list)
    missing_modes: List[str] = field(default_factory=list)
    total_duration_ms: Optional[float] = None

class WincasaUnifiedLogger:
    """
    Unified Query Logger with Path Tracking
    
    Combines:
    - Persistent storage in SQLite database
    - Query path tracking through layers
    - Thread-safe operations
    - Query analytics and patterns
    - Cross-session history
    - Performance metrics per layer
    """
    
    def __init__(self, db_path: str = "wincasa_data/query_logs.db", debug_mode: bool = False):
        self.db_path = Path(db_path)
        self.debug_mode = debug_mode
        self.lock = threading.Lock()
        
        # Active queries for path tracking
        self.active_queries: Dict[str, Dict[str, Any]] = {}
        
        # Ensure directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with enhanced schema"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Main query logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT UNIQUE NOT NULL,
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
                    selected_modes TEXT,
                    missing_modes TEXT,
                    total_duration_ms REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Query path events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_path_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    layer TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    duration_ms REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES query_logs(query_id)
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_mode ON query_logs(mode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_success ON query_logs(success)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_events_query ON query_path_events(query_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_events_layer ON query_path_events(layer)")
            
            conn.commit()
            conn.close()
    
    def start_query(self, query_text: str, selected_modes: List[str], 
                   user_id: str = None, session_id: str = None) -> str:
        """Start tracking a new query"""
        query_id = str(uuid.uuid4())[:8]
        
        with self.lock:
            self.active_queries[query_id] = {
                'query_text': query_text,
                'selected_modes': selected_modes,
                'user_id': user_id,
                'session_id': session_id,
                'start_time': time.time(),
                'events': [],
                'mode_results': {}
            }
        
        # Log first event
        self.log_event(query_id, 'streamlit', 'start', {
            'query': query_text,
            'modes': selected_modes,
            'user_id': user_id,
            'session_id': session_id
        })
        
        logger.info(f"Started query {query_id}: {query_text[:50]}...")
        return query_id
    
    def log_event(self, query_id: str, layer: str, event_type: str, 
                  details: Dict[str, Any], duration_ms: Optional[float] = None):
        """Add event to query path"""
        event = QueryPathEvent(
            timestamp=datetime.now().isoformat(),
            layer=layer,
            event_type=event_type,
            details=details,
            duration_ms=duration_ms
        )
        
        with self.lock:
            if query_id in self.active_queries:
                self.active_queries[query_id]['events'].append(event)
            
            # Also save to database immediately
            self._save_path_event(query_id, event)
        
        # Log to file
        log_entry = {
            'query_id': query_id,
            'event': asdict(event)
        }
        logger.info(json.dumps(log_entry))
    
    def _save_path_event(self, query_id: str, event: QueryPathEvent):
        """Save path event to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_path_events 
            (query_id, timestamp, layer, event_type, details, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            query_id,
            event.timestamp,
            event.layer,
            event.event_type,
            json.dumps(event.details),
            event.duration_ms
        ))
        
        conn.commit()
        conn.close()
    
    def log_routing_decision(self, query_id: str, decision: str, reason: str):
        """Log routing decision"""
        self.log_event(query_id, 'query_engine', 'decision', {
            'decision': decision,
            'reason': reason
        })
    
    def log_layer_transition(self, query_id: str, from_layer: str, to_layer: str, 
                           input_data: Any, transformation: Optional[str] = None):
        """Log transition between layers"""
        self.log_event(query_id, from_layer, 'transform', {
            'to_layer': to_layer,
            'input_summary': str(input_data)[:200],
            'transformation': transformation
        })
    
    def log_error(self, query_id: str, layer: str, error: Exception, context: Dict[str, Any]):
        """Log error with context"""
        self.log_event(query_id, layer, 'error', {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        })
    
    def log_mode_result(self, query_id: str, entry: QueryLogEntry):
        """Log result for a specific mode"""
        with self.lock:
            if query_id in self.active_queries:
                self.active_queries[query_id]['mode_results'][entry.mode] = entry
        
        # Save to database
        self._save_query_log(entry)
    
    def _save_query_log(self, entry: QueryLogEntry):
        """Save query log entry to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO query_logs 
            (query_id, timestamp, query, mode, model, user_id, session_id,
             response_time_ms, result_count, confidence, cost_estimate, 
             success, error, answer_preview, source_data, selected_modes,
             missing_modes, total_duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.query_id,
            entry.timestamp,
            entry.query,
            entry.mode,
            entry.model,
            entry.user_id,
            entry.session_id,
            entry.response_time_ms,
            entry.result_count,
            entry.confidence,
            entry.cost_estimate,
            int(entry.success),
            entry.error,
            entry.answer_preview,
            entry.source_data,
            json.dumps(entry.selected_modes),
            json.dumps(entry.missing_modes),
            entry.total_duration_ms
        ))
        
        conn.commit()
        conn.close()
    
    def complete_query(self, query_id: str, results: Dict[str, Any]):
        """Complete query tracking"""
        with self.lock:
            if query_id not in self.active_queries:
                logger.warning(f"Query ID {query_id} not found in active queries")
                return
            
            query_data = self.active_queries[query_id]
            total_duration_ms = (time.time() - query_data['start_time']) * 1000
            
            # Find missing modes
            executed_modes = list(results.keys())
            missing_modes = [
                mode for mode in query_data['selected_modes']
                if mode not in executed_modes
            ]
            
            # Log completion event
            self.log_event(query_id, 'streamlit', 'complete', {
                'total_duration_ms': total_duration_ms,
                'executed_modes': executed_modes,
                'missing_modes': missing_modes,
                'result_summary': f"{len(results)} modes executed"
            })
            
            # Save complete query path
            self._save_query_path_summary(query_id, query_data, total_duration_ms, missing_modes)
            
            # Clean up
            del self.active_queries[query_id]
        
        logger.info(f"Query {query_id} completed in {total_duration_ms:.0f}ms")
    
    def _save_query_path_summary(self, query_id: str, query_data: Dict, 
                                total_duration_ms: float, missing_modes: List[str]):
        """Save query path summary as JSON file"""
        path_summary = {
            'query_id': query_id,
            'query_text': query_data['query_text'],
            'selected_modes': query_data['selected_modes'],
            'missing_modes': missing_modes,
            'start_time': query_data['start_time'],
            'total_duration_ms': total_duration_ms,
            'events': [asdict(e) for e in query_data['events']],
            'mode_results': {
                mode: asdict(result) if hasattr(result, '__dict__') else result
                for mode, result in query_data['mode_results'].items()
            }
        }
        
        # Save to file
        path_file = log_dir / f'query_path_{query_id}.json'
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(path_summary, f, indent=2, ensure_ascii=False)
    
    def analyze_query_path(self, query_id: str) -> Dict[str, Any]:
        """Analyze query path for issues"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get query info
        cursor.execute("""
            SELECT * FROM query_logs WHERE query_id = ?
        """, (query_id,))
        query_info = cursor.fetchone()
        
        if not query_info:
            return {'error': 'Query not found'}
        
        # Get path events
        cursor.execute("""
            SELECT * FROM query_path_events 
            WHERE query_id = ? 
            ORDER BY timestamp
        """, (query_id,))
        events = cursor.fetchall()
        
        conn.close()
        
        # Analyze
        analysis = {
            'query_id': query_id,
            'query': query_info[2],  # query text
            'selected_modes': json.loads(query_info[15]) if query_info[15] else [],
            'missing_modes': json.loads(query_info[16]) if query_info[16] else [],
            'total_duration_ms': query_info[17],
            'events_count': len(events),
            'errors': [],
            'layer_durations': {},
            'routing_decisions': []
        }
        
        # Analyze events
        for event in events:
            event_type = event[4]
            layer = event[3]
            details = json.loads(event[5]) if event[5] else {}
            
            if event_type == 'error':
                analysis['errors'].append({
                    'layer': layer,
                    'error': details.get('error_message', 'Unknown')
                })
            elif event_type == 'decision':
                analysis['routing_decisions'].append(details)
            
            # Track layer durations
            if event[6]:  # duration_ms
                if layer not in analysis['layer_durations']:
                    analysis['layer_durations'][layer] = 0
                analysis['layer_durations'][layer] += event[6]
        
        return analysis
    
    def get_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get query statistics for dashboard"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Basic stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(response_time_ms) as avg_response_time,
                AVG(cost_estimate) as avg_cost,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
            FROM query_logs
            WHERE timestamp > ?
        """, (since,))
        
        stats = cursor.fetchone()
        
        # Mode distribution
        cursor.execute("""
            SELECT mode, COUNT(*) as count
            FROM query_logs
            WHERE timestamp > ?
            GROUP BY mode
            ORDER BY count DESC
        """, (since,))
        
        mode_dist = cursor.fetchall()
        
        # Error patterns
        cursor.execute("""
            SELECT error, COUNT(*) as count
            FROM query_logs
            WHERE timestamp > ? AND error IS NOT NULL
            GROUP BY error
            ORDER BY count DESC
            LIMIT 10
        """, (since,))
        
        errors = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_queries': stats[0] or 0,
            'unique_users': stats[1] or 0,
            'avg_response_time_ms': stats[2] or 0,
            'avg_cost': stats[3] or 0,
            'success_rate': (stats[4] / stats[0] * 100) if stats[0] > 0 else 0,
            'mode_distribution': dict(mode_dist),
            'top_errors': [{'error': e[0], 'count': e[1]} for e in errors]
        }
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Alias for get_query_stats for backward compatibility"""
        # Convert days to hours for get_query_stats
        hours = days * 24
        return self.get_query_stats(hours)

# Backward compatibility functions
def get_query_logger(debug_mode: bool = False) -> WincasaUnifiedLogger:
    """Get singleton instance of unified logger"""
    if not hasattr(get_query_logger, '_instance'):
        get_query_logger._instance = WincasaUnifiedLogger(debug_mode=debug_mode)
    return get_query_logger._instance

# Alias for old query_path_logger
query_path_logger = get_query_logger()