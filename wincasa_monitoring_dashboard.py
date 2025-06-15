#!/usr/bin/env python3
"""
WINCASA Phase 2.4 - Monitoring Dashboard
Real-time Metrics und Performance Monitoring für Query Engine
"""

import json
import time
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque

from wincasa_query_engine import WincasaQueryEngine, QueryEngineResult
# Shadow mode removed
from wincasa_query_logger import QueryLogEntry, get_query_logger

@dataclass
class MetricSnapshot:
    """Snapshot von Metrics zu einem Zeitpunkt"""
    timestamp: datetime
    total_queries: int
    queries_per_minute: float
    avg_response_time_ms: float
    success_rate: float
    unified_percentage: float
    legacy_percentage: float
    error_rate: float
    cost_per_query: float

@dataclass
class AlertRule:
    """Alert-Regel für Monitoring"""
    name: str
    metric: str  # e.g., "avg_response_time_ms", "error_rate"
    operator: str  # "gt", "lt", "eq"
    threshold: float
    enabled: bool = True
    cooldown_minutes: int = 5

@dataclass
class Alert:
    """Active Alert"""
    rule_name: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    triggered_at: datetime
    current_value: float
    threshold: float

class WincasaMonitoringDashboard:
    """
    WINCASA Monitoring Dashboard - Phase 2.4
    
    Features:
    - Real-time Performance Metrics
    - Alerting System mit konfigurierbaren Rules
    - Historical Data Storage
    - Performance Trend Analysis
    - Cost Monitoring
    """
    
    def __init__(self, 
                 query_engine: WincasaQueryEngine,
                 storage_dir: str = "monitoring_data",
                 debug_mode: bool = False):
        
        self.query_engine = query_engine
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode
        
        # Initialize persistent query logger
        self.query_logger = get_query_logger(debug_mode=debug_mode)
        
        # Metrics Storage
        self.metric_snapshots: deque = deque(maxlen=1440)  # 24h at 1min intervals
        self.query_history: deque = deque(maxlen=10000)    # Last 10k queries
        self.error_log: deque = deque(maxlen=1000)         # Last 1k errors
        
        # Performance Tracking
        self.response_times: deque = deque(maxlen=1000)    # Rolling window
        self.hourly_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        
        # Alerting System
        self.alert_rules = self._setup_default_alert_rules()
        self.active_alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Threading
        self._lock = threading.Lock()
        self._monitoring_active = False
        self._monitoring_thread = None
        
        if self.debug_mode:
            print(f"📊 Monitoring Dashboard initialisiert:")
            print(f"   📁 Storage: {self.storage_dir}")
            print(f"   🚨 Alert Rules: {len(self.alert_rules)}")
            print(f"   📈 Metrics Retention: {self.metric_snapshots.maxlen} snapshots")
    
    def _setup_default_alert_rules(self) -> List[AlertRule]:
        """Setup Standard Alert Rules"""
        return [
            AlertRule("high_response_time", "avg_response_time_ms", "gt", 5000.0),
            AlertRule("high_error_rate", "error_rate", "gt", 0.05),  # 5%
            AlertRule("low_success_rate", "success_rate", "lt", 0.9), # 90%
            AlertRule("high_cost", "cost_per_query", "gt", 0.10),    # $0.10
            AlertRule("system_overload", "queries_per_minute", "gt", 100.0),
        ]
    
    def log_query_result(self, query: str, result: QueryEngineResult):
        """Loggt Query-Ergebnis für Monitoring"""
        
        # Log to persistent storage first
        log_entry = QueryLogEntry(
            timestamp=result.timestamp.isoformat(),
            query=query,
            mode=result.processing_mode,
            model=getattr(result, 'model', 'unknown'),
            user_id=result.user_id or 'anonymous',
            session_id=getattr(result, 'session_id', 'unknown'),
            response_time_ms=result.processing_time_ms,
            result_count=result.result_count,
            confidence=result.confidence,
            cost_estimate=result.cost_estimate,
            success=result.result_count > 0 and not result.error_details,
            error=result.error_details,
            answer_preview=getattr(result, 'answer', '')[:200] if hasattr(result, 'answer') else None,
            source_data=result.processing_mode
        )
        
        # Persist to database
        self.query_logger.log_query(log_entry)
        
        with self._lock:
            # Store in query history (in-memory for real-time)
            query_record = {
                "timestamp": result.timestamp,
                "query": query,
                "processing_mode": result.processing_mode,
                "engine_version": result.engine_version,
                "response_time_ms": result.processing_time_ms,
                "result_count": result.result_count,
                "confidence": result.confidence,
                "cost": result.cost_estimate,
                "success": result.result_count > 0,
                "user_id": result.user_id
            }
            
            self.query_history.append(query_record)
            self.response_times.append(result.processing_time_ms)
            
            # Update hourly stats
            hour_key = result.timestamp.strftime("%Y-%m-%d_%H")
            self.hourly_stats[hour_key]["count"] += 1
            self.hourly_stats[hour_key]["total_time"] += result.processing_time_ms
            
            if result.result_count == 0 or result.error_details:
                self.hourly_stats[hour_key]["errors"] += 1
                
                # Log error
                if result.error_details:
                    error_record = {
                        "timestamp": result.timestamp,
                        "query": query,
                        "error": result.error_details,
                        "processing_mode": result.processing_mode
                    }
                    self.error_log.append(error_record)
        
        if self.debug_mode:
            print(f"📝 Logged query: {result.processing_mode} - {result.processing_time_ms:.1f}ms")
    
    def log_error(self, error_message: str, context: Dict[str, Any] = None):
        """Loggt System-Fehler"""
        
        with self._lock:
            error_record = {
                "timestamp": datetime.now(),
                "error": error_message,
                "context": context or {}
            }
            self.error_log.append(error_record)
        
        if self.debug_mode:
            print(f"❌ Error logged: {error_message}")
    
    def capture_metrics_snapshot(self) -> MetricSnapshot:
        """Erstellt aktuellen Metrics Snapshot"""
        
        with self._lock:
            # Recent query stats (last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_queries = [
                q for q in self.query_history 
                if q["timestamp"] >= recent_cutoff
            ]
            
            if not recent_queries:
                return MetricSnapshot(
                    timestamp=datetime.now(),
                    total_queries=0,
                    queries_per_minute=0.0,
                    avg_response_time_ms=0.0,
                    success_rate=0.0,
                    unified_percentage=0.0,
                    legacy_percentage=0.0,
                    error_rate=0.0,
                    cost_per_query=0.0
                )
            
            # Calculate metrics
            total_queries = len(recent_queries)
            queries_per_minute = total_queries / 60.0
            
            response_times = [q["response_time_ms"] for q in recent_queries]
            avg_response_time = sum(response_times) / len(response_times)
            
            successful_queries = sum(1 for q in recent_queries if q["success"])
            success_rate = successful_queries / total_queries
            
            unified_queries = sum(1 for q in recent_queries if q["engine_version"] == "unified_v2")
            unified_percentage = unified_queries / total_queries
            legacy_percentage = 1.0 - unified_percentage
            
            error_queries = sum(1 for q in recent_queries if not q["success"])
            error_rate = error_queries / total_queries
            
            costs = [q["cost"] for q in recent_queries]
            avg_cost = sum(costs) / len(costs) if costs else 0.0
        
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            total_queries=total_queries,
            queries_per_minute=queries_per_minute,
            avg_response_time_ms=avg_response_time,
            success_rate=success_rate,
            unified_percentage=unified_percentage,
            legacy_percentage=legacy_percentage,
            error_rate=error_rate,
            cost_per_query=avg_cost
        )
        
        # Store snapshot
        with self._lock:
            self.metric_snapshots.append(snapshot)
        
        # Check alerts
        self._check_alerts(snapshot)
        
        return snapshot
    
    def _check_alerts(self, snapshot: MetricSnapshot):
        """Prüft Alert Rules gegen aktuelle Metrics"""
        
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.name in self.alert_cooldowns:
                if current_time < self.alert_cooldowns[rule.name]:
                    continue
            
            # Get metric value
            metric_value = getattr(snapshot, rule.metric, None)
            if metric_value is None:
                continue
            
            # Check condition
            triggered = False
            if rule.operator == "gt" and metric_value > rule.threshold:
                triggered = True
            elif rule.operator == "lt" and metric_value < rule.threshold:
                triggered = True
            elif rule.operator == "eq" and metric_value == rule.threshold:
                triggered = True
            
            if triggered:
                # Determine severity
                severity = self._determine_alert_severity(rule, metric_value)
                
                alert = Alert(
                    rule_name=rule.name,
                    message=f"{rule.name}: {rule.metric} {rule.operator} {rule.threshold} (current: {metric_value:.2f})",
                    severity=severity,
                    triggered_at=current_time,
                    current_value=metric_value,
                    threshold=rule.threshold
                )
                
                with self._lock:
                    self.active_alerts.append(alert)
                    self.alert_history.append(alert)
                
                # Set cooldown
                self.alert_cooldowns[rule.name] = current_time + timedelta(minutes=rule.cooldown_minutes)
                
                if self.debug_mode:
                    print(f"🚨 ALERT [{severity.upper()}]: {alert.message}")
    
    def _determine_alert_severity(self, rule: AlertRule, current_value: float) -> str:
        """Bestimmt Alert Severity basierend auf wie weit der Wert über dem Threshold liegt"""
        
        if rule.operator == "gt":
            ratio = current_value / rule.threshold
            if ratio > 3.0:
                return "critical"
            elif ratio > 2.0:
                return "high"
            elif ratio > 1.5:
                return "medium"
            else:
                return "low"
        
        elif rule.operator == "lt":
            ratio = rule.threshold / current_value if current_value > 0 else float('inf')
            if ratio > 3.0:
                return "critical"
            elif ratio > 2.0:
                return "high"
            elif ratio > 1.5:
                return "medium"
            else:
                return "low"
        
        return "medium"
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Gibt komplette Dashboard-Daten zurück"""
        
        # Current snapshot
        current_snapshot = self.capture_metrics_snapshot()
        
        # Recent performance trend (last 4 hours)
        trend_cutoff = datetime.now() - timedelta(hours=4)
        trend_snapshots = [
            s for s in self.metric_snapshots 
            if s.timestamp >= trend_cutoff
        ]
        
        # Top errors (last 24h)
        error_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = [
            e for e in self.error_log 
            if e["timestamp"] >= error_cutoff
        ]
        
        # System stats
        system_stats = self.query_engine.get_system_stats()
        
        return {
            "current_metrics": asdict(current_snapshot),
            "performance_trend": [asdict(s) for s in trend_snapshots],
            "active_alerts": [asdict(a) for a in self.active_alerts],
            "recent_errors": recent_errors[-10:],  # Last 10 errors
            "system_stats": system_stats,
            "alert_rules": [asdict(rule) for rule in self.alert_rules],
            "dashboard_meta": {
                "last_updated": datetime.now().isoformat(),
                "total_snapshots": len(self.metric_snapshots),
                "total_queries_logged": len(self.query_history),
                "monitoring_active": self._monitoring_active
            }
        }
    
    def start_background_monitoring(self, interval_seconds: int = 60):
        """Startet Background-Monitoring Thread"""
        
        if self._monitoring_active:
            print("⚠️ Monitoring already active")
            return
        
        self._monitoring_active = True
        
        def monitoring_loop():
            while self._monitoring_active:
                try:
                    snapshot = self.capture_metrics_snapshot()
                    
                    if self.debug_mode:
                        print(f"📊 Monitoring snapshot: {snapshot.queries_per_minute:.1f} QPM, "
                              f"{snapshot.avg_response_time_ms:.1f}ms avg")
                    
                    time.sleep(interval_seconds)
                
                except Exception as e:
                    if self.debug_mode:
                        print(f"❌ Monitoring error: {e}")
                    time.sleep(interval_seconds)
        
        self._monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        print(f"📊 Background monitoring started (interval: {interval_seconds}s)")
    
    def stop_background_monitoring(self):
        """Stoppt Background-Monitoring"""
        
        self._monitoring_active = False
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        print("📊 Background monitoring stopped")
    
    def clear_alerts(self, severity_filter: Optional[str] = None):
        """Löscht aktive Alerts"""
        
        with self._lock:
            if severity_filter:
                self.active_alerts = [
                    a for a in self.active_alerts 
                    if a.severity != severity_filter
                ]
            else:
                self.active_alerts.clear()
        
        print(f"🚨 Alerts cleared (filter: {severity_filter or 'all'})")
    
    def add_alert_rule(self, rule: AlertRule):
        """Fügt neue Alert Rule hinzu"""
        
        # Check if rule already exists
        for existing_rule in self.alert_rules:
            if existing_rule.name == rule.name:
                print(f"⚠️ Alert rule '{rule.name}' already exists")
                return
        
        self.alert_rules.append(rule)
        print(f"🚨 Alert rule added: {rule.name}")
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]):
        """Aktualisiert existierende Alert Rule"""
        
        for rule in self.alert_rules:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                print(f"🚨 Alert rule updated: {rule_name}")
                return
        
        print(f"⚠️ Alert rule not found: {rule_name}")
    
    def export_metrics_report(self, filename: Optional[str] = None) -> str:
        """Exportiert Metrics Report als JSON"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_report_{timestamp}.json"
        
        filepath = self.storage_dir / filename
        
        dashboard_data = self.get_dashboard_data()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Monitoring report exported: {filepath}")
        return str(filepath)
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Gibt Performance Summary für gegebenen Zeitraum zurück"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            relevant_queries = [
                q for q in self.query_history 
                if q["timestamp"] >= cutoff_time
            ]
        
        if not relevant_queries:
            return {"error": "No data available for timeframe"}
        
        # Calculate summary stats
        total_queries = len(relevant_queries)
        successful_queries = sum(1 for q in relevant_queries if q["success"])
        
        response_times = [q["response_time_ms"] for q in relevant_queries]
        costs = [q["cost"] for q in relevant_queries]
        
        # Mode distribution
        mode_counts = defaultdict(int)
        for q in relevant_queries:
            mode_counts[q["processing_mode"]] += 1
        
        return {
            "timeframe_hours": hours,
            "total_queries": total_queries,
            "success_rate": successful_queries / total_queries,
            "performance": {
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)]
            },
            "cost": {
                "total_cost": sum(costs),
                "avg_cost_per_query": sum(costs) / len(costs),
                "max_cost_per_query": max(costs)
            },
            "mode_distribution": dict(mode_counts),
            "queries_per_hour": total_queries / hours
        }

def test_monitoring_dashboard():
    """Test des Monitoring Dashboards"""
    print("🧪 Teste WINCASA Monitoring Dashboard...")
    
    # Initialize components
    query_engine = WincasaQueryEngine(debug_mode=True)
    dashboard = WincasaMonitoringDashboard(query_engine, debug_mode=True)
    
    # Simulate some queries
    test_queries = [
        "Wer wohnt in der Aachener Str. 71?",
        "Portfolio von Bona Casa GmbH",
        "Freie Wohnungen in Essen",
        "Kontaktdaten von Weber",
        "Invalid query that should fail"
    ]
    
    print(f"\n📋 Simulating Queries:")
    
    for i, query in enumerate(test_queries):
        user_id = f"test_user_{i+1}"
        result = query_engine.process_query(query, user_id)
        dashboard.log_query_result(query, result)
        
        print(f"   Query {i+1}: {result.processing_mode} - {result.processing_time_ms:.1f}ms")
        
        # Simulate some delay
        time.sleep(0.1)
    
    # Test metrics capture
    print(f"\n📊 Capturing Metrics:")
    snapshot = dashboard.capture_metrics_snapshot()
    
    print(f"   Queries/min: {snapshot.queries_per_minute:.1f}")
    print(f"   Avg Response: {snapshot.avg_response_time_ms:.1f}ms")
    print(f"   Success Rate: {snapshot.success_rate:.1%}")
    print(f"   Unified %: {snapshot.unified_percentage:.1%}")
    
    # Test dashboard data
    print(f"\n📈 Dashboard Data:")
    dashboard_data = dashboard.get_dashboard_data()
    
    print(f"   Snapshots: {len(dashboard_data['performance_trend'])}")
    print(f"   Active Alerts: {len(dashboard_data['active_alerts'])}")
    print(f"   Recent Errors: {len(dashboard_data['recent_errors'])}")
    
    # Test performance summary
    print(f"\n📊 Performance Summary:")
    summary = dashboard.get_performance_summary(hours=1)
    
    if "error" not in summary:
        print(f"   Total Queries: {summary['total_queries']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Avg Response: {summary['performance']['avg_response_time_ms']:.1f}ms")
        print(f"   Mode Distribution: {summary['mode_distribution']}")
    
    # Test alert system
    print(f"\n🚨 Testing Alerts:")
    
    # Add custom alert rule
    custom_rule = AlertRule(
        name="test_alert",
        metric="avg_response_time_ms",
        operator="gt",
        threshold=1000.0,  # 1 second
        enabled=True
    )
    dashboard.add_alert_rule(custom_rule)
    
    # Trigger alert with high response time simulation
    # This should trigger an alert since our test queries are taking >1000ms
    snapshot = dashboard.capture_metrics_snapshot()
    
    print(f"   Alert Rules: {len(dashboard.alert_rules)}")
    print(f"   Active Alerts: {len(dashboard.active_alerts)}")
    
    if dashboard.active_alerts:
        for alert in dashboard.active_alerts:
            print(f"   🚨 {alert.severity.upper()}: {alert.message}")
    
    # Export report
    print(f"\n📄 Exporting Report:")
    report_path = dashboard.export_metrics_report()
    print(f"   Report saved: {report_path}")
    
    print(f"\n✅ Monitoring Dashboard Test Complete")

if __name__ == "__main__":
    test_monitoring_dashboard()