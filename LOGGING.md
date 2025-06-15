# LOGGING.md - WINCASA Logging Strategy

**System**: WINCASA Logging Architecture  
**Typ**: Multi-Layer Structured Logging  
**Status**: Production Ready  
**Letztes Update**: 2025-06-15

---

## Logging-Übersicht

WINCASA implementiert ein mehrstufiges Logging-System mit strukturierten Logs, Query Path Tracking und Business Analytics Integration. Das System verfolgt alle Query-Pfade durch das 5-Modi System und bietet umfassende Performance- und Error-Analyse.

---

## Log-Datei Struktur

### Hauptkomponenten
```
logs/
├── layer2.log              # Hauptanwendung (783KB)
├── layer2_api.log          # API-Interaktionen (13MB) 
├── layer2_errors.log       # Fehler-Tracking (28KB)
├── layer2_performance.log  # Performance-Metriken (811KB)
└── query_paths.log         # Query-Routing Entscheidungen (6KB)
```

### Persistent Storage
```
wincasa_data/
└── query_logs.db          # SQLite Database mit Query-Historie
```

---

## Logger-Architektur

### 1. Unified Logger (Central Framework)

#### `wincasa_unified_logger.py`
**Modul-ID**: WC103-02  
**Session**: 4 (Analytics & Monitoring)  
**Größe**: 17KB

```python
class WincasaUnifiedLogger:
    """
    Zentrales Logging Framework mit strukturierten Logs
    
    Features:
    - JSON-strukturierte Log-Entries
    - Query Path Tracking (Template/Search/Legacy)
    - Performance Metrics Collection
    - Error Categorization & Alerting
    - Cross-Session History
    """
    
    def __init__(self):
        self.logger = logging.getLogger('wincasa_unified')
        self.setup_handlers()
        
    def setup_handlers(self):
        """
        Konfiguriert verschiedene Log-Handler für verschiedene Zwecke
        """
        handlers = {
            'main': RotatingFileHandler('logs/layer2.log', maxBytes=10MB),
            'api': RotatingFileHandler('logs/layer2_api.log', maxBytes=50MB),
            'errors': FileHandler('logs/layer2_errors.log'),
            'performance': FileHandler('logs/layer2_performance.log')
        }
```

#### Log Entry Format
```json
{
  "timestamp": "2025-06-15T10:30:45.123Z",
  "session_id": "sess_abc123",
  "level": "INFO",
  "category": "QUERY_EXECUTION",
  "message": "Query executed successfully",
  "data": {
    "query": "Zeige alle Mieter",
    "execution_path": "optimized_search",
    "response_time_ms": 3.1,
    "success": true,
    "mode": "UNIFIED",
    "results_count": 189
  },
  "user_context": {
    "ip": "127.0.0.1",
    "user_agent": "streamlit"
  }
}
```

### 2. Query-Specific Logger

#### `wincasa_query_logger.py`
**Modul-ID**: WC103-03  
**Session**: 4 (Query Path Tracking)  
**Größe**: 12KB

```python
class QueryLogger:
    """
    Spezialisierter Logger für Query-Analyse
    
    Features:
    - Detailliertes Query Path Tracking
    - Performance-Metriken pro Execution Path
    - Business Logic Validation Logging
    - Singleton Pattern für Konsistenz
    """
    
    def log_query_execution(self, entry: QueryLogEntry):
        """
        Loggt Query-Ausführung mit vollständigen Metadaten
        """
        log_data = {
            "query_id": generate_query_id(),
            "original_query": entry.query,
            "normalized_query": normalize_query(entry.query),
            "intent_classification": entry.intent,
            "execution_path": entry.execution_path,
            "fallback_used": entry.fallback_used,
            "response_time_ms": entry.response_time_ms,
            "success": entry.success,
            "error_details": entry.error_details
        }
```

#### QueryLogEntry Schema
```python
@dataclass
class QueryLogEntry:
    """Strukturierte Query-Log Daten"""
    query: str                    # Original user query
    mode: str                    # "JSON_VANILLA|JSON_SYSTEM|SQL_VANILLA|SQL_SYSTEM|UNIFIED"
    execution_path: str          # "template|optimized_search|legacy_fallback"
    intent: str                  # "TENANT_SEARCH|OWNER_PORTFOLIO|VACANCY_ANALYSIS|..."
    response_time_ms: float      # Exact response time
    success: bool                # Success/failure status
    session_id: str              # Session identifier
    timestamp: datetime          # Precise timestamp
    results_count: int           # Number of results returned
    fallback_used: bool          # Whether fallback was triggered
    error_details: Optional[str] # Error message if failed
    knowledge_base_used: bool    # Whether KB enhancement was applied
    
    # Performance Metrics
    db_query_time_ms: Optional[float]     # Database query time
    llm_processing_time_ms: Optional[float]  # LLM processing time
    search_index_time_ms: Optional[float]    # Search index time
    
    # Business Context
    entities_found: List[str]    # Types of entities found
    critical_fields_used: List[str]  # Critical business fields accessed
```

---

## Logging-Integration in Komponenten

### 3. Streamlit App Logging

#### `streamlit_app.py` Integration
```python
class WincasaStreamlitApp:
    def __init__(self):
        self.logger = get_unified_logger()
        self.query_logger = get_query_logger()
        
    def execute_query(self, query: str, selected_modes: List[str]):
        """Query-Ausführung mit umfassendem Logging"""
        session_id = self.get_session_id()
        
        # Start Query Logging
        self.logger.info("Query execution started", extra={
            "session_id": session_id,
            "query": query,
            "modes": selected_modes,
            "ui_state": self.get_ui_state()
        })
        
        for mode in selected_modes:
            start_time = time.time()
            
            try:
                result = self.execute_mode(query, mode)
                response_time = (time.time() - start_time) * 1000
                
                # Log successful execution
                entry = QueryLogEntry(
                    query=query,
                    mode=mode,
                    execution_path=result.execution_path,
                    response_time_ms=response_time,
                    success=True,
                    session_id=session_id,
                    results_count=len(result.data)
                )
                self.query_logger.log_query(entry)
                
            except Exception as e:
                # Log execution error
                self.logger.error("Query execution failed", extra={
                    "session_id": session_id,
                    "query": query,
                    "mode": mode,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
```

### 4. Unified Engine Logging

#### `wincasa_query_engine.py` Integration
```python
class WincasaQueryEngine:
    def execute_query(self, query: str, config: QueryConfig = None) -> QueryResult:
        """3-Pfad Routing mit detailliertem Path Logging"""
        logger = get_query_logger()
        start_time = time.time()
        
        # Intent Classification Logging
        intent = self.intent_router.classify_intent(query)
        logger.info(f"Intent classified as: {intent}")
        
        # Path Decision Logging
        if self.should_use_optimized_search(query, intent):
            execution_path = "optimized_search"
            logger.info("Routing to optimized search", extra={
                "reason": "simple_entity_lookup",
                "expected_response_time": "1-5ms"
            })
            
        elif self.template_engine.has_template(intent):
            execution_path = "template_engine"
            logger.info("Routing to template engine", extra={
                "template": intent,
                "expected_response_time": "~100ms"
            })
            
        else:
            execution_path = "legacy_fallback"
            logger.warning("Routing to legacy fallback", extra={
                "reason": "no_template_available",
                "expected_response_time": "500-2000ms"
            })
        
        # Execution & Result Logging
        result = self.execute_path(execution_path, query, intent)
        response_time = (time.time() - start_time) * 1000
        
        # Comprehensive Result Logging
        logger.log_query_execution(QueryLogEntry(
            query=query,
            mode="UNIFIED",
            execution_path=execution_path,
            intent=intent,
            response_time_ms=response_time,
            success=result.success,
            results_count=len(result.data) if result.data else 0,
            fallback_used=execution_path == "legacy_fallback"
        ))
```

### 5. Knowledge Base Logging

#### `knowledge_base_loader.py` Integration
```python
class KnowledgeBaseLoader:
    def enhance_query(self, query: str) -> EnhancedQuery:
        """Query Enhancement mit Knowledge Injection Logging"""
        logger = get_unified_logger()
        
        original_query = query
        enhancements = []
        
        # Critical Field Mapping Checks
        if 'kaltmiete' in query.lower():
            query += "\nWICHTIG: KALTMIETE = BEWOHNER.Z1"
            enhancements.append("critical_kaltmiete_mapping")
            
        if 'mieter' in query.lower():
            query += "\nKONTEXT: BEWADR.BNAME für Namen, BEWOHNER für Verträge"
            enhancements.append("tenant_context_injection")
        
        # Log Knowledge Enhancement
        if enhancements:
            logger.info("Knowledge base enhancement applied", extra={
                "original_query": original_query,
                "enhancements": enhancements,
                "enhanced_query": query,
                "mappings_used": self.get_mappings_for_query(query)
            })
```

---

## Log-Analyse & Monitoring

### 6. Analytics Dashboard Integration

#### `wincasa_analytics_system.py` Logging
```python
class WincasaAnalyticsSystem:
    def generate_performance_report(self) -> PerformanceReport:
        """Performance-Analyse basierend auf Log-Daten"""
        
        # Log-Daten aus verschiedenen Quellen aggregieren
        query_logs = self.load_query_logs()
        performance_logs = self.load_performance_logs()
        error_logs = self.load_error_logs()
        
        report = {
            "mode_performance": {
                "optimized_search": {
                    "avg_response_time_ms": 2.8,
                    "success_rate": 100.0,
                    "usage_percentage": 45.2
                },
                "template_engine": {
                    "avg_response_time_ms": 95.3,
                    "success_rate": 98.7,
                    "usage_percentage": 32.1
                },
                "legacy_fallback": {
                    "avg_response_time_ms": 1247.6,
                    "success_rate": 89.3,
                    "usage_percentage": 22.7
                }
            },
            "error_analysis": self.analyze_error_patterns(error_logs),
            "performance_trends": self.analyze_performance_trends(performance_logs)
        }
        
        # Report Generation Logging
        self.logger.info("Performance report generated", extra={
            "report_timeframe": "24h",
            "total_queries_analyzed": len(query_logs),
            "critical_issues": report.get("critical_issues", [])
        })
```

### 7. Real-time Monitoring

#### `wincasa_monitoring_dashboard.py` 
```python
class MonitoringDashboard:
    def start_monitoring(self):
        """Real-time Log Monitoring mit Alerting"""
        
        # Tail Log Files für Real-time Updates
        self.tail_logs()
        
        # Performance Threshold Monitoring
        self.monitor_performance_thresholds()
        
        # Error Rate Monitoring
        self.monitor_error_rates()
        
    def monitor_performance_thresholds(self):
        """Performance Schwellenwert Überwachung"""
        thresholds = {
            "optimized_search_max_ms": 10,      # Alert if > 10ms
            "template_engine_max_ms": 200,      # Alert if > 200ms
            "overall_success_rate_min": 95.0    # Alert if < 95%
        }
        
        current_metrics = self.get_current_metrics()
        
        for metric, threshold in thresholds.items():
            if self.threshold_exceeded(metric, threshold, current_metrics):
                self.logger.warning(f"Performance threshold exceeded: {metric}", extra={
                    "threshold": threshold,
                    "current_value": current_metrics[metric],
                    "alert_level": "PERFORMANCE_DEGRADATION"
                })
```

---

## Log-Konfiguration

### 8. Logging Configuration

#### Standard Log Format
```python
LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "level": "%(levelname)s", 
    "logger": "%(name)s",
    "session_id": "%(session_id)s",
    "message": "%(message)s",
    "extra_data": "%(extra_data)s"
}

LOG_LEVELS = {
    "DEBUG": "Detailed diagnostic information",
    "INFO": "Normal operation logging",
    "WARNING": "Performance issues, fallbacks used",
    "ERROR": "Query execution failures",
    "CRITICAL": "System-level failures"
}
```

#### Rotation & Retention Policy
```python
LOG_ROTATION = {
    "layer2.log": {
        "max_size": "10MB",
        "backup_count": 10,
        "rotation": "size_based"
    },
    "layer2_api.log": {
        "max_size": "50MB", 
        "backup_count": 5,
        "rotation": "size_based"
    },
    "layer2_errors.log": {
        "retention_days": 90,
        "rotation": "daily"
    },
    "layer2_performance.log": {
        "retention_days": 30,
        "rotation": "daily"
    }
}
```

---

## Business Intelligence Logging

### 9. Query Pattern Analysis

#### Business Logic Validation Logging
```python
def log_business_rule_validation(query: str, result: QueryResult):
    """Business Rule Compliance Logging"""
    logger = get_unified_logger()
    
    validations = {
        "excluded_test_data": check_onr_exclusion(result),      # ONR >= 890
        "active_contracts_only": check_vende_null(result),     # VENDE IS NULL
        "weg_collective_logic": check_eignr_minus_one(result), # EIGNR = -1
        "critical_field_usage": check_critical_fields(result)  # KALTMIETE = BEWOHNER.Z1
    }
    
    violations = [rule for rule, passed in validations.items() if not passed]
    
    if violations:
        logger.warning("Business rule violations detected", extra={
            "query": query,
            "violations": violations,
            "alert_level": "BUSINESS_LOGIC_VIOLATION"
        })
```

### 10. Cost & Performance Tracking

#### LLM API Cost Logging
```python
def log_llm_usage(query: str, mode: str, tokens_used: int, cost_usd: float):
    """LLM API Kosten und Token-Usage Tracking"""
    logger = get_unified_logger()
    
    logger.info("LLM API usage", extra={
        "category": "API_COST_TRACKING",
        "query": query,
        "mode": mode,
        "tokens_input": tokens_used,
        "tokens_output": estimate_output_tokens(query),
        "cost_usd": cost_usd,
        "provider": "openai",  # or "anthropic"
        "model": "gpt-4o-mini"
    })
```

---

## Log-Analyse Tools

### 11. Query Path Analysis

#### Skript für Log-Analyse
```bash
#!/bin/bash
# analyze_query_paths.sh

echo "=== WINCASA Query Path Analysis ==="

# Performance Analysis
echo "Average Response Times by Path:"
grep "execution_path" logs/query_paths.log | \
jq -r '.execution_path + ": " + (.response_time_ms | tostring) + "ms"' | \
sort | uniq -c

# Success Rate Analysis  
echo "Success Rates by Mode:"
grep "success" logs/layer2.log | \
jq -r '.mode + ": " + (.success | tostring)' | \
sort | uniq -c

# Error Pattern Analysis
echo "Most Common Errors:"
grep "ERROR" logs/layer2_errors.log | \
jq -r '.error' | sort | uniq -c | sort -nr | head -10
```

### 12. Business Analytics Queries

#### SQL Queries für Log-Analyse
```sql
-- Query Performance Trends (SQLite: query_logs.db)
SELECT 
    date(timestamp) as date,
    execution_path,
    AVG(response_time_ms) as avg_response_time,
    COUNT(*) as query_count,
    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
FROM query_logs 
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY date, execution_path
ORDER BY date DESC, avg_response_time ASC;

-- Most Common Query Patterns
SELECT 
    intent,
    COUNT(*) as frequency,
    AVG(response_time_ms) as avg_time,
    execution_path
FROM query_logs 
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY intent, execution_path
ORDER BY frequency DESC;

-- Error Analysis
SELECT 
    mode,
    error_details,
    COUNT(*) as error_count,
    date(timestamp) as error_date
FROM query_logs 
WHERE success = 0
GROUP BY mode, error_details, date(timestamp)
ORDER BY error_count DESC;
```

---

## Alerting & Monitoring

### 13. Alert Configuration

#### Performance Alerts
```python
ALERT_THRESHOLDS = {
    "response_time": {
        "optimized_search_max_ms": 10,
        "template_engine_max_ms": 200,
        "legacy_fallback_max_ms": 5000
    },
    "success_rate": {
        "minimum_overall": 95.0,
        "minimum_per_mode": 90.0
    },
    "error_frequency": {
        "max_errors_per_hour": 50,
        "max_critical_errors_per_day": 5
    }
}
```

#### Alert Actions
```python
def trigger_alert(alert_type: str, details: Dict):
    """Alert Triggering mit verschiedenen Notification Channels"""
    
    # Log Alert
    logger.critical(f"ALERT: {alert_type}", extra={
        "alert_level": "CRITICAL",
        "details": details,
        "timestamp": datetime.now(),
        "requires_immediate_attention": True
    })
    
    # Future: Email/Slack Notifications
    # send_slack_notification(alert_type, details)
    # send_email_alert(alert_type, details)
```

---

## Logging Best Practices

### 14. Development Guidelines

#### Logging Standards
```python
# DO: Structured Logging mit Context
logger.info("Query executed successfully", extra={
    "session_id": session_id,
    "execution_path": "optimized_search", 
    "response_time_ms": 3.1,
    "results_count": 25
})

# DON'T: Unstrukturierte String-Messages
logger.info(f"Query took {response_time}ms and returned {count} results")

# DO: Error Logging mit Full Context
logger.error("Database connection failed", extra={
    "error_type": "CONNECTION_ERROR",
    "database": "WINCASA2022.FDB",
    "retry_attempt": 3,
    "traceback": traceback.format_exc()
})

# DON'T: Generic Error Messages
logger.error("Something went wrong")
```

#### Performance Logging
```python
# DO: Granular Performance Tracking
with performance_timer("query_execution") as timer:
    result = execute_query(query)
    timer.log_milestone("database_query_complete")
    processed_result = process_result(result)
    timer.log_milestone("result_processing_complete")

# DON'T: Only Total Time Logging
start = time.time()
result = execute_query(query)
logger.info(f"Total time: {time.time() - start}")
```

---

**Logging Status**: Production-ready mit umfassender Query Path Tracking, Performance Monitoring und Business Intelligence Integration.