# ARCHITECTURE.md - WINCASA System Architecture

**System**: WINCASA Property Management  
**Architekturtyp**: Multi-layered Query Engine mit Knowledge-Based SQL  
**Status**: Production Ready  
**Letztes Update**: 2025-06-15

## System-Übersicht

WINCASA implementiert eine Dual-Engine Architecture mit intelligentem Query-Routing:

```
┌─────────────────────────────────────────────────────────────────┐
│                     WINCASA QUERY SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│  User Query → Streamlit UI (5 Modi) → Dual Engine Routing      │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              │                         │                        │
│         Unified Engine            Legacy Handler                │
│         (Modus 5)                (Modi 1-4)                    │
│              │                         │                        │
│    ┌─────────┴──────────┐             │                        │
│    │ Intent Router      │             │                        │
│    │ • Regex Patterns   │             │                        │
│    │ • LLM Classifier   │             │                        │
│    │ • Smart Fallback   │             │                        │
│    └─────────┬──────────┘             │                        │
│              │                         │                        │
│    ┌─────────▼──────────┐    ┌────────▼────────┐              │
│    │ 3-Path Execution:  │    │ Direct LLM:     │              │
│    │ 1. Template Engine │    │ • JSON Sources  │              │
│    │ 2. Search Index    │    │ • SQL Database  │              │
│    │ 3. Legacy Fallback │    │ • System Prompts│              │
│    └────────────────────┘    └─────────────────┘              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              KNOWLEDGE-BASED SQL SYSTEM                  │  │
│  │  • 226 Field Mappings (automatisch extrahiert)          │  │
│  │  • Join Graph (30 Tabellen)                             │  │
│  │  • Business Vocabulary (Deutsch → SQL)                  │  │
│  │  • KRITISCH: KALTMIETE = BEWOHNER.Z1                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    DATA LAYER                            │  │
│  │  • Firebird DB (126 Tabellen, Embedded Mode)           │  │
│  │  • JSON Exports (35 Dateien, 229k Zeilen)              │  │
│  │  • In-Memory Index (588 Entities, 1-5ms)               │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Detaillierte Komponentenarchitektur

### 1. Presentation Layer

**streamlit_app.py**
- Session State Management mit unique button keys
- Full-width Container Layout für Ergebnisse
- 5-Modi Checkbox System
- Tab-basierte Ergebnisanzeige

### 2. Intelligence Layer

#### Unified Engine (Modus 5)
```python
# wincasa_query_engine.py
def route_query(query: str) -> ExecutionPath:
    """Intelligente 3-Pfad Routing Logic"""
    if simple_lookup_pattern(query):
        return OptimizedSearchPath()  # 1-5ms
    elif templatable_query(query):
        return TemplateEnginePath()   # ~100ms
    else:
        return LegacyFallbackPath()   # 500-2000ms
```

**Intent Classification (3-Level)**
1. **Regex Patterns** (95% Confidence)
   - "alle mieter" → TENANT_SEARCH
   - "portfolio" → OWNER_PORTFOLIO
   - "leerstand" → VACANCY_ANALYSIS
   
2. **LLM Classification** (GPT-4o-mini)
   - Business Context Understanding
   - Entity Extraction
   
3. **Intelligent Fallback**
   - Structured Search für Lookups
   - Legacy SQL für Complex Queries

#### Legacy Handler (Modi 1-4)
```
Mode 1: JSON_VANILLA → llm_handler → layer4_json (~300ms)
Mode 2: JSON_SYSTEM  → llm_handler → layer4_json (~1500ms)
Mode 3: SQL_VANILLA  → llm_handler → database   (~500ms)
Mode 4: SQL_SYSTEM   → llm_handler → database   (~2000ms)
```

### 3. Knowledge Base Architecture

**Zero-Hardcoding System**
- **knowledge_extractor.py**: Parst 35 SQL-Dateien
- **knowledge_base_loader.py**: Runtime Context Injection

```
knowledge_base/
├── alias_map.json              # 226 field mappings
├── join_graph.json             # Table relationships
├── business_vocabulary.json    # German → SQL mappings
└── extraction_report.txt       # Analysis summary
```

**Kritische Mappings**:
- KALTMIETE = BEWOHNER.Z1 (nicht KBETRAG!)
- EIGNR = -1 (Leerstand)
- ONR >= 890 (Eigentümer-Filter)

### 4. Data Access Layer

```python
class DataAccessLayer:
    def execute_query(self, query: str, source: DataSource):
        if source == DataSource.OPTIMIZED_SEARCH:
            return self.search_engine.query(query)  # 1-5ms
        elif source == DataSource.JSON_CACHE:
            return self.json_loader.query(query)    # ~300ms
        else:
            return self.database.execute(query)     # 500-2000ms
```

### 5. Performance Architecture

```
Tier 1: Optimized Search (1-5ms)
├── In-Memory Multi-Index
├── 588 Entities indexed
└── Fuzzy Search Support

Tier 2: Template Engine (~100ms)
├── Parametrisierte SQL
├── Security Validation
└── 80% Business Coverage

Tier 3: Legacy Fallback (500-2000ms)
├── LLM SQL Generation
├── Full DB Access
└── 100% Coverage Guarantee
```

### 6. Logging & Analytics

**Multi-Layer Logging**
- **wincasa_unified_logger.py**: Zentrales Framework
- **wincasa_query_logger.py**: SQLite-basierte Historie
- **Query Path Tracking**: Template/Search/Legacy Decision

### 7. Documentation Infrastructure

**Sphinx Documentation System**
- **docs/**: Professional HTML documentation with RTD theme
- **sync-project.sh**: Complete system synchronization including docs
- **update-docs.sh**: Centralized documentation pipeline
- **docs-live.sh**: Live documentation server (localhost:8000)

```python
# Structured Logging Format
{
    "timestamp": "2025-06-15T10:30:45Z",
    "query_id": "q_abc123",
    "component": "unified_engine",
    "event": "route_decision",
    "path": "optimized_search",
    "confidence": 0.95,
    "response_time_ms": 3.1
}
```

**Self-Updating Stack (SAD.md)**
- **Schema → Code → Tests → Docs** Pipeline
- **Automatic synchronization** of all layers
- **Zero-drift architecture** with validation

## Security & Deployment

### Security Layer
- API Keys in separaten ENV-Dateien (/home/envs/openai.env)
- Firebird Embedded Mode (kein Server-Prozess)
- SQL Injection Prevention via Parameter-Substitution
- 100k Row Limit für Query Protection

### Feature Flag System
```python
def should_use_unified_engine(user_id: str) -> bool:
    """Hash-based consistent assignment"""
    if not config["unified_system_enabled"]:
        return False
    
    if user_id in config["override_users"]:
        return True
    
    # Graduelle Rollout-Kontrolle
    hash_value = md5(f"{user_id}{salt}").hexdigest()
    percentage = int(hash_value[:2], 16) / 255 * 100
    return percentage < config["rollout_percentage"]
```

## Evolution & Metrics

### Performance Evolution
```
Legacy System: 300-2000ms
    ↓ (1000x improvement)
Optimized Search: 1-5ms
Template System: ~100ms
Unified Engine: Best of all paths
```

### Key Metrics
- **Performance**: 1-5ms (Search), ~100ms (Templates)
- **Test Coverage**: 100% (26/26 tests)
- **Field Mappings**: 226 automatisch extrahiert
- **Success Rate**: >98% für Business Queries
- **Code Reduction**: 70% durch Cleanup

### Business Impact
- 311 Eigentümer verwaltet
- 189 Mieter indexiert
- 77 Liegenschaften
- 35 Business-Queries optimiert

Diese Architektur ermöglicht **risikofreie Migration**, **Enterprise-Grade Performance** und **100% Fallback-Garantie** für ein production-ready AI-powered Property Management System.