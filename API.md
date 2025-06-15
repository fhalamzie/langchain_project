# API.md - WINCASA API Documentation

**System**: WINCASA Property Management API  
**Typ**: Streamlit Web Interface + Internal Module APIs  
**Status**: Production Ready  
**Letztes Update**: 2025-06-15

---

## Web Interface API

### Primary Endpoint
```
Base URL: http://localhost:8667
Protocol: HTTP/HTTPS
Framework: Streamlit
```

### Main Application Interface

#### GET /
**Beschreibung**: Hauptanwendung mit 5-Modi Query Interface  
**Modul**: `streamlit_app.py`  
**Session**: 0, 6 (UI Fixes)

**Response Interface**:
```html
┌─────────────────────────────────────────┐
│ WINCASA Property Management System      │
├─────────────────────────────────────────┤
│ ☐ JSON_VANILLA    ☐ JSON_SYSTEM        │
│ ☐ SQL_VANILLA     ☐ SQL_SYSTEM         │  
│ ☐ UNIFIED (Phase 2)                    │
├─────────────────────────────────────────┤
│ Query Input: [_________________]        │
│        [🔍 Abfrage ausführen]          │
├─────────────────────────────────────────┤
│ [Tab1] [Tab2] [Tab3] [Tab4] [Tab5]      │
│ ┌─────────────────────────────────────┐ │
│ │ 📊 Ergebnisse                       │ │
│ │ Results Container (Full-width)      │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Request Parameters**:
- `query` (string): Deutsche Abfrage (z.B. "Zeige alle Mieter")
- `modes` (array): Ausgewählte Modi ["JSON_VANILLA", "UNIFIED", etc.]
- `session_id` (string): Automatisch generierte Session-ID

**Response Format**:
```json
{
  "results": {
    "JSON_VANILLA": {
      "data": [...],
      "response_time_ms": 305.2,
      "success": true,
      "source": "json_cache"
    },
    "UNIFIED": {
      "data": [...],
      "response_time_ms": 3.1,
      "success": true,
      "source": "optimized_search"
    }
  },
  "query_metadata": {
    "original_query": "alle mieter",
    "timestamp": "2025-06-15T10:30:45Z",
    "session_id": "sess_abc123"
  }
}
```

---

## Core Engine APIs

### 1. Unified Query Engine API

#### `wincasa_query_engine.execute_query()`
**Modul**: `wincasa_query_engine.py`  
**Session**: 3, 4 (Unified Engine)

```python
def execute_query(query: str, config: QueryConfig = None) -> QueryResult:
    """
    Phase 2 Unified Engine mit 3-Pfad Routing
    
    Args:
        query (str): Deutsche Abfrage
        config (QueryConfig): Optional configuration
        
    Returns:
        QueryResult: Strukturiertes Ergebnis mit Metadaten
    """
```

**Query Routing Logic**:
```python
# 3-Pfad Routing System
if intent_router.is_simple_lookup(query):
    return optimized_search.execute(query)      # 1-5ms
elif template_engine.has_template(query):  
    return template_engine.execute(query)       # ~100ms
else:
    return legacy_fallback.execute(query)       # 500-2000ms
```

**Response Structure**:
```json
{
  "data": [...],
  "metadata": {
    "execution_path": "optimized_search|template|legacy_fallback",
    "response_time_ms": 3.1,
    "query_intent": "TENANT_SEARCH",
    "confidence": 0.95,
    "fallback_used": false
  },
  "success": true,
  "error": null
}
```

### 2. Legacy Handler API

#### `llm_handler.process_query()`
**Modul**: `llm_handler.py`  
**Session**: 0, 1 (Legacy System)

```python
def process_query(query: str, mode: str, system_prompt: str = None) -> Dict:
    """
    Legacy LLM-basierte Query-Verarbeitung für Modi 1-4
    
    Args:
        query (str): User query in German
        mode (str): "JSON_VANILLA|JSON_SYSTEM|SQL_VANILLA|SQL_SYSTEM"
        system_prompt (str): Optional system enhancement
        
    Returns:
        Dict: Query results with timing and metadata
    """
```

**Mode-spezifische Endpunkte**:
```python
# Mode 1: JSON_VANILLA (~300ms)
llm_handler.process_query(query, "JSON_VANILLA") 
→ layer4_json_loader.search()

# Mode 2: JSON_SYSTEM (~1500ms)  
llm_handler.process_query(query, "JSON_SYSTEM", system_prompt)
→ layer4_json_loader.search()

# Mode 3: SQL_VANILLA (~500ms)
llm_handler.process_query(query, "SQL_VANILLA")
→ database_connection.execute()

# Mode 4: SQL_SYSTEM (~2000ms)
llm_handler.process_query(query, "SQL_SYSTEM", system_prompt) 
→ database_connection.execute()
```

---

## Data Access APIs

### 3. Optimized Search API (Phase 2.1)

#### `wincasa_optimized_search.search()`
**Modul**: `wincasa_optimized_search.py`  
**Session**: 2 (High-Performance Search)

```python
def search(query: str, limit: int = 50) -> SearchResult:
    """
    Ultra-fast In-Memory Search für 588 indexierte Entitäten
    
    Performance: 1-5ms response time
    Success Rate: 100% für Entity Lookups
    
    Args:
        query (str): Search query
        limit (int): Max results (default 50)
        
    Returns:
        SearchResult: Fast search results
    """
```

**Search Categories**:
```python
# Entity Types
SUPPORTED_ENTITIES = {
    "owners": ["name", "address", "phone", "email"],
    "tenants": ["name", "apartment", "rent", "contract"],  
    "properties": ["address", "units", "type"],
    "apartments": ["building", "unit", "tenant", "status"]
}
```

**Response Example**:
```json
{
  "results": [
    {
      "entity_type": "tenant",
      "entity_id": "T12345",
      "name": "Max Mustermann", 
      "apartment": "Hauptstr. 1, Wohnung 3A",
      "relevance_score": 0.98
    }
  ],
  "metadata": {
    "total_found": 1,
    "response_time_ms": 2.3,
    "search_type": "exact_match",
    "index_used": "tenant_name_index"
  }
}
```

### 4. Template Engine API (Phase 2.2)

#### `sql_template_engine.execute_template()`
**Modul**: `sql_template_engine.py`  
**Session**: 3 (Template System)

```python
def execute_template(intent: str, parameters: Dict) -> TemplateResult:
    """
    Parametrisierte SQL-Templates mit Security-Validierung
    
    Args:
        intent (str): Business intent (e.g., "TENANT_SEARCH")
        parameters (Dict): Template parameters
        
    Returns:
        TemplateResult: Template execution result
    """
```

**Template Categories**:
```python
AVAILABLE_TEMPLATES = {
    "TENANT_SEARCH": "SELECT * FROM vw_mieter_komplett WHERE name LIKE ?",
    "OWNER_PORTFOLIO": "SELECT * FROM vw_eigentuemer_portfolio WHERE eignr = ?",
    "VACANCY_ANALYSIS": "SELECT * FROM vw_leerstand_korrekt WHERE building = ?",
    "RENT_QUERY": "SELECT bewohner.z1 as kaltmiete FROM bewohner WHERE ?"
}
```

### 5. Data Access Layer API

#### `data_access_layer.unified_query()`
**Modul**: `data_access_layer.py`  
**Session**: 4 (Unified Data Access)

```python
def unified_query(query: str, source: DataSource) -> UnifiedResult:
    """
    Abstrahiert verschiedene Datenquellen
    
    Args:
        query (str): Query string
        source (DataSource): FIREBIRD|JSON_CACHE|SEARCH_INDEX
        
    Returns:
        UnifiedResult: Normalized result regardless of source
    """
```

**Data Source Routing**:
```python
class DataSource(Enum):
    FIREBIRD = "firebird_database"      # Real-time, 500-2000ms
    JSON_CACHE = "json_exports"         # Cached, ~300ms  
    SEARCH_INDEX = "in_memory_index"    # Ultra-fast, 1-5ms
```

---

## Knowledge Base APIs

### 6. Knowledge Extractor API (Phase 2.4)

#### `knowledge_extractor.extract_mappings()`
**Modul**: `knowledge_extractor.py`  
**Session**: 5 (Knowledge System)

```python
def extract_mappings(sql_files_dir: str) -> ExtractionResult:
    """
    Analysiert SQL-Dateien und extrahiert Field-Mappings
    
    Args:
        sql_files_dir (str): Pfad zu SQL-Dateien
        
    Returns:
        ExtractionResult: 226 Field-Mappings + Join-Graph
    """
```

**Extraction Output**:
```json
{
  "field_mappings": {
    "kaltmiete": "BEWOHNER.Z1",  // KRITISCHE KORREKTUR!
    "warmmiete": "BEWOHNER.Z1 + BEWOHNER.Z2 + BEWOHNER.Z3",
    "mieter_name": "BEWADR.BNAME",
    "eigentuemer_name": "EIGADR.ENAME"
  },
  "join_relationships": {
    "BEWOHNER": ["BEWADR.BEWNR", "OBJEKTE.ONR"],
    "EIGENTUEMER": ["EIGADR.EIGNR", "VEREIG.EIGNR"]
  },
  "extraction_stats": {
    "sql_files_analyzed": 35,
    "total_mappings": 226,
    "critical_fixes": 1
  }
}
```

### 7. Knowledge Base Loader API

#### `knowledge_base_loader.enhance_query()`
**Modul**: `knowledge_base_loader.py`  
**Session**: 5 (Runtime Knowledge Injection)

```python
def enhance_query(query: str) -> EnhancedQuery:
    """
    Runtime Context-Injection für LLM-Prompts
    
    Args:
        query (str): Original user query
        
    Returns:
        EnhancedQuery: Query mit injiziertem Knowledge Context
    """
```

**Context Injection Examples**:
```python
# Input: "Zeige Kaltmiete für Mustermann"
# Output: "Zeige Kaltmiete für Mustermann\nWICHTIG: KALTMIETE = BEWOHNER.Z1"

# Input: "Alle Mieter in Hauptstraße"  
# Output: "Alle Mieter in Hauptstraße\nKONTEXT: BEWADR.BNAME für Namen, OBJEKTE.OSTRASSE für Adresse"
```

---

## Analytics & Logging APIs

### 8. Unified Logger API

#### `wincasa_unified_logger.log_query()`
**Modul**: `wincasa_unified_logger.py`  
**Session**: 4 (Logging Framework)

```python
def log_query(entry: QueryLogEntry) -> None:
    """
    Zentrales Query-Logging mit strukturierten Daten
    
    Args:
        entry (QueryLogEntry): Structured log entry
    """

@dataclass
class QueryLogEntry:
    query: str
    mode: str  
    execution_path: str        # "template|search|legacy_fallback"
    response_time_ms: float
    success: bool
    session_id: str
    timestamp: datetime
    error_details: Optional[str] = None
```

**Log Destinations**:
```python
LOG_FILES = {
    "main": "logs/layer2.log",              # 783KB
    "api": "logs/layer2_api.log",           # 13MB
    "errors": "logs/layer2_errors.log",     # 28KB  
    "performance": "logs/layer2_performance.log",  # 811KB
    "query_paths": "logs/query_paths.log"   # 6KB
}
```

### 9. Analytics System API

#### `wincasa_analytics_system.generate_report()`
**Modul**: `wincasa_analytics_system.py`  
**Session**: 4 (Business Analytics)

```python
def generate_report(timeframe: str = "24h") -> AnalyticsReport:
    """
    Business Analytics Report Generation
    
    Args:
        timeframe (str): "1h|24h|7d|30d"
        
    Returns:
        AnalyticsReport: Comprehensive analytics data
    """
```

**Analytics Metrics**:
```json
{
  "query_statistics": {
    "total_queries": 1247,
    "mode_distribution": {
      "UNIFIED": 67.3,
      "JSON_VANILLA": 18.2, 
      "SQL_SYSTEM": 14.5
    },
    "avg_response_time_ms": 127.8,
    "success_rate": 98.7
  },
  "performance_trends": {
    "optimized_search_usage": 45.2,
    "template_hits": 32.1,
    "legacy_fallbacks": 22.7
  },
  "business_metrics": {
    "most_queried_entities": ["tenants", "rent_info", "properties"],
    "peak_hours": ["09:00-11:00", "14:00-16:00"]
  }
}
```

---

## Testing APIs

### 10. Test Suite API

#### `test_suite_phase2.run_comprehensive_tests()`
**Modul**: `test_suite_phase2.py`  
**Session**: 1, 4 (Testing Framework)

```python
def run_comprehensive_tests() -> TestResults:
    """
    100% Test Coverage für alle Phase 2 Komponenten
    
    Returns:
        TestResults: 26/26 Tests mit Detailed Results
    """
```

**Test Categories**:
```python
TEST_SUITES = {
    "unit_tests": [
        "test_optimized_search",
        "test_template_engine", 
        "test_knowledge_extraction",
        "test_unified_logger"
    ],
    "integration_tests": [
        "test_end_to_end_query_flow",
        "test_mode_switching",
        "test_fallback_logic"
    ],
    "performance_tests": [
        "test_1ms_search_requirement",
        "test_100ms_template_requirement",
        "test_concurrent_query_handling"
    ]
}
```

### 11. Golden Set Validation API

#### `test_golden_queries_kb.validate_with_knowledge_base()`
**Modul**: `test_golden_queries_kb.py`  
**Session**: 5 (Knowledge Base Testing)

```python
def validate_with_knowledge_base() -> ValidationReport:
    """
    Golden Set Testing mit Knowledge Base Integration
    
    Returns:
        ValidationReport: 100% Success Rate auf kritische Queries
    """
```

---

## Configuration APIs

### 12. Configuration Loader API

#### `config_loader.load_config()`
**Modul**: `config_loader.py`  
**Session**: 1 (Configuration Management)

```python
def load_config(config_type: str) -> Dict:
    """
    Zentrale Konfigurationsverwaltung
    
    Args:
        config_type (str): "sql_paths|query_engine|feature_flags"
        
    Returns:
        Dict: Configuration data
    """
```

**Configuration Files**:
```python
CONFIG_MAPPING = {
    "sql_paths": "config/sql_paths.json",
    "query_engine": "config/query_engine.json", 
    "feature_flags": "config/feature_flags.json"
}
```

---

## Error Handling & HTTP Status Codes

### Standard Response Format
```json
{
  "success": true|false,
  "data": {...},
  "error": null|{
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {...}
  },
  "metadata": {
    "response_time_ms": 123.45,
    "timestamp": "2025-06-15T10:30:45Z",
    "session_id": "sess_abc123"
  }
}
```

### Error Codes
```python
ERROR_CODES = {
    "QUERY_EMPTY": "Query string cannot be empty",
    "MODE_INVALID": "Invalid query mode specified", 
    "DB_CONNECTION_FAILED": "Database connection error",
    "TEMPLATE_NOT_FOUND": "No template available for intent",
    "SEARCH_INDEX_ERROR": "Search index unavailable",
    "KNOWLEDGE_BASE_ERROR": "Knowledge base loading failed",
    "LLM_API_ERROR": "LLM service unavailable",
    "TIMEOUT_ERROR": "Query execution timeout"
}
```

---

## Performance Benchmarks

### API Response Time Targets
```python
PERFORMANCE_TARGETS = {
    "optimized_search": "1-5ms",      # Ultra-fast entity lookups
    "template_engine": "~100ms",      # Parametrized SQL  
    "json_vanilla": "~300ms",         # Cached JSON access
    "sql_vanilla": "~500ms",          # Direct SQL generation
    "json_system": "~1500ms",         # LLM-enhanced JSON
    "sql_system": "~2000ms",          # LLM-enhanced SQL
    "legacy_fallback": "500-2000ms"   # Full LLM processing
}
```

### Concurrent Performance
- **Max Concurrent Users**: 10-50 (Streamlit limitation)
- **Session Management**: Persistent session state
- **Memory Usage**: ~200MB for search index + knowledge base
- **Database Connections**: Single embedded Firebird connection

---

**API Status**: Production ready mit 100% Test Coverage und comprehensive error handling.