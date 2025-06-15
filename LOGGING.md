# LOGGING.md

## Logging-Strategie

### Zentrale Logger
- ID: wincasa_unified_logger.py
  Module: unified_logger
  Level: INFO
  Format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  Features: Query-Path-Tracking, Session-Correlation

- ID: wincasa_query_logger.py
  Module: query_logger  
  Storage: SQLite (wincasa_data/query_logs.db)
  Features: Persistente Query-Historie, Performance-Metriken

### Log-Dateien
- ID: logs/layer2.log
  Size: 783KB
  Rotation: Daily
  Content: Hauptanwendung, Query-Ausführung

- ID: logs/layer2_api.log  
  Size: 13MB
  Rotation: Size-based (10MB)
  Content: API-Calls, LLM-Interaktionen

- ID: logs/layer2_performance.log
  Size: 811KB
  Rotation: Daily
  Content: Performance-Metriken, Response-Times

- ID: logs/query_paths.log
  Size: 6KB
  Rotation: Weekly
  Content: Query-Routing-Entscheidungen

### Module-spezifische Logger

#### Intelligence Layer
- llm_handler: logger.getLogger('llm_handler')
  Level: INFO
  Content: LLM-Requests, Token-Usage, Errors

- wincasa_query_engine: logger.getLogger(__name__)
  Level: INFO  
  Content: Routing-Entscheidungen, Mode-Selection

#### Data Layer  
- layer4_json_loader: logger.getLogger(__name__)
  Level: INFO
  Content: JSON-Loading, Cache-Hits

- sql_executor: logger.getLogger(__name__)
  Level: WARNING
  Content: SQL-Errors, Query-Timeouts

#### Infrastructure
- streamlit_app: logger.getLogger(__name__)
  Level: INFO
  Content: Session-Events, UI-Interactions

### Query-Path-Tracking
```python
query_path_logger.start_query(query, modes, user_id, session_id)
query_path_logger.log_event(query_id, component, event, metadata)
query_path_logger.log_layer_transition(query_id, from_layer, to_layer, data)
query_path_logger.complete_query(query_id, results)
```

### Performance-Logging
- Response-Time: Millisekunden-genau
- Result-Count: Anzahl gefundener Datensätze
- Confidence-Score: 0.0-1.0
- Cost-Estimate: USD pro Query

### Error-Handling
- Exception-Details: Full Traceback bei ERROR
- User-Context: session_id, user_id
- Recovery-Actions: Fallback-Mechanismen dokumentiert

### Log-Analyse-Tools
- wincasa_analytics_system.py: Business-Metriken
- wincasa_monitoring_dashboard.py: Real-time Monitoring
- SQLite-Queries: Direkte Analyse der query_logs.db