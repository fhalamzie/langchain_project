# API.md

## Web-Interface

### Streamlit-Endpoint
- URL: http://localhost:8667
- Module: streamlit_app.py
- Entry: WincasaStreamlitApp.execute_query()
- SessionID: prod-20250615

### Request-Format
```python
{
  "query": "Zeige alle Mieter",
  "modes": ["JSON_VANILLA", "UNIFIED"],
  "session_id": "sess_abc123"
}
```

### Response-Format
```python
{
  "results": {
    "mode_name": {
      "data": [...],
      "response_time_ms": 3.1,
      "success": true,
      "source": "optimized_search"
    }
  },
  "query_metadata": {
    "timestamp": "2025-06-15T10:30:45Z"
  }
}
```

## Core-APIs

### Unified-Engine
- Module: wincasa_query_engine.py
- Function: execute_query(query: str) -> QueryResult
- Routing: Template(100ms) → Search(1-5ms) → Legacy(500-2000ms)
- SessionID: phase2-20250614

### Legacy-Handler
- Module: llm_handler.py
- Function: process_query(query: str, mode: str) -> Dict
- Modes: JSON_VANILLA|JSON_SYSTEM|SQL_VANILLA|SQL_SYSTEM
- SessionID: legacy-20250612

### Optimized-Search
- Module: wincasa_optimized_search.py
- Function: search(query: str, limit: int = 50) -> SearchResult
- Performance: 1-5ms
- Entities: 588 indexed (owners, tenants, properties, apartments)
- SessionID: phase2-20250614

### Template-Engine
- Module: sql_template_engine.py
- Function: execute_template(intent: str, params: Dict) -> TemplateResult
- Templates: TENANT_SEARCH, OWNER_PORTFOLIO, VACANCY_ANALYSIS, RENT_QUERY
- SessionID: phase2-20250614

### Data-Access-Layer
- Module: data_access_layer.py
- Function: unified_query(query: str, source: DataSource) -> UnifiedResult
- Sources: FIREBIRD|JSON_CACHE|SEARCH_INDEX
- SessionID: unified-20250614

## Knowledge-APIs

### Knowledge-Extractor
- Module: knowledge_extractor.py
- Function: extract_mappings(sql_dir: str) -> ExtractionResult
- Output: 226 field mappings, join graph
- Critical: KALTMIETE = BEWOHNER.Z1
- SessionID: kb-20250614

### Knowledge-Loader
- Module: knowledge_base_loader.py
- Function: enhance_query(query: str) -> EnhancedQuery
- Runtime: Context injection for LLM prompts
- SessionID: kb-20250614

## Analytics-APIs

### Unified-Logger
- Module: wincasa_unified_logger.py
- Function: log_query(entry: QueryLogEntry) -> None
- Files: layer2.log, layer2_api.log, performance.log
- SessionID: monitoring-20250614

### Analytics-System
- Module: wincasa_analytics_system.py
- Function: generate_report(timeframe: str) -> AnalyticsReport
- Metrics: Query stats, performance trends, business metrics
- SessionID: analytics-20250614

## Test-APIs

### Test-Suite
- Module: test_suite_phase2.py
- Function: run_comprehensive_tests() -> TestResults
- Coverage: 100% (26/26 tests)
- SessionID: test-20250614

### Golden-Set-Validation
- Module: test_golden_queries_kb.py
- Function: validate_with_knowledge_base() -> ValidationReport
- Queries: 100 realistic business scenarios
- SessionID: golden-20250614

## Configuration-API

### Config-Loader
- Module: config_loader.py
- Function: load_config(config_type: str) -> Dict
- Types: sql_paths|query_engine|feature_flags
- SessionID: config-20250612

## Error-Handling

### Error-Codes
```python
ERROR_CODES = {
  "QUERY_EMPTY": "Empty query",
  "MODE_INVALID": "Invalid mode",
  "DB_CONNECTION_FAILED": "DB error",
  "TEMPLATE_NOT_FOUND": "No template",
  "SEARCH_INDEX_ERROR": "Index error",
  "KNOWLEDGE_BASE_ERROR": "KB error",
  "LLM_API_ERROR": "LLM error",
  "TIMEOUT_ERROR": "Timeout"
}
```

### Response-Structure
```python
{
  "success": bool,
  "data": {...} | None,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description"
  } | None,
  "metadata": {
    "response_time_ms": float,
    "timestamp": str
  }
}
```

## Performance-Targets

### Response-Times
- optimized_search: 1-5ms
- template_engine: ~100ms
- json_vanilla: ~300ms
- sql_vanilla: ~500ms
- json_system: ~1500ms
- sql_system: ~2000ms
- legacy_fallback: 500-2000ms

### Concurrent-Limits
- Max Users: 10-50 (Streamlit)
- Memory: ~200MB (index + KB)
- DB: Single embedded Firebird