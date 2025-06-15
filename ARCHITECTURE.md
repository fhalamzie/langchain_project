# ARCHITECTURE.md - WINCASA System Architecture

**System**: WINCASA Property Management  
**Architekturtyp**: Multi-layered Query Engine mit Knowledge-Based SQL  
**Status**: Production Ready  
**Letztes Update**: 2025-06-15

---

## System-Übersicht

WINCASA implementiert eine hochmoderne, schichtweise Query-Architektur, die von einfachen Legacy-Modi zu einem intelligenten, production-ready System mit Knowledge Base und Feature Flags evolviert ist.

### Architektur-Paradigma
```
Dual-Engine Architecture:
├── Legacy System (Modi 1-4): Direkter LLM → Database/JSON Pfad
└── Unified Engine (Modus 5): Intelligentes 3-Pfad Routing System
```

---

## Gesamt-Architektur Diagramm

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            WINCASA QUERY SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐       ┌───────────────────────────────────────────────────┐  │
│  │ User Query   │──────▶│        Streamlit Web Interface                   │  │
│  │ (German)     │       │ - 5 Modi Checkbox Selection                      │  │
│  └──────────────┘       │ - Session State Management                       │  │
│                         │ - Full-width Results Display                     │  │
│                         └─────────────────────┬─────────────────────────────┘  │
│                                               │                                │
│                         ┌─────────────────────┴─────────────────────┐         │
│                         │        DUAL ENGINE ROUTING                │         │
│                         │                                           │         │
│                         │  if 'unified' in selected_modes:          │         │
│                         │      → UNIFIED ENGINE (Phase 2)           │         │
│                         │  else:                                     │         │
│                         │      → LEGACY HANDLER (Modi 1-4)          │         │
│                         └─────────────┬───────────┬─────────────────┘         │
│                                       │           │                            │
│                              ┌────────▼───────┐  │                            │
│                              │ UNIFIED ENGINE │  │                            │
│                              │ (Modus 5)      │  │                            │
│                              │ ┌────────────┐ │  │                            │
│                              │ │Hierarchical│ │  │                            │
│                              │ │Intent      │ │  │                            │
│                              │ │Router      │ │  │                            │
│                              │ │• Regex     │ │  │                            │
│                              │ │• LLM Class │ │  │                            │
│                              │ │• Fallback  │ │  │                            │
│                              │ └─────┬──────┘ │  │                            │
│                              │       │        │  │                            │
│                              │ ┌─────▼──────┐ │  │                            │
│                              │ │3 Pfade:    │ │  │                            │
│                              │ │• Template  │ │  │                            │
│                              │ │• Search    │ │  │                            │
│                              │ │• Legacy    │ │  │                            │
│                              │ └────────────┘ │  │                            │
│                              └────────────────┘  │                            │
│                                                  │                            │
│                                       ┌─────────▼─────────┐                  │
│                                       │ LEGACY HANDLER    │                  │
│                                       │ (Modi 1-4)        │                  │
│                                       │ ┌───────────────┐ │                  │
│                                       │ │ llm_handler   │ │                  │
│                                       │ │ + layer4_json │ │                  │
│                                       │ │ + db_connect  │ │                  │
│                                       │ └───────────────┘ │                  │
│                                       └───────────────────┘                  │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │                    KNOWLEDGE-BASED SQL SYSTEM                           │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ Knowledge Extractor (Analysiert 35 SQL-Dateien)                   │ │ │
│  │  │ • 226 Field Mappings: alias → canonical database columns          │ │ │
│  │  │ • Join Graph: 30 Tabellen mit Relationships                       │ │ │
│  │  │ • Business Vocabulary: Deutsche Begriffe → SQL Context            │ │ │
│  │  │ • KRITISCH: KALTMIETE = BEWOHNER.Z1 (nicht KBETRAG!)            │ │ │
│  │  └────────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │ │
│  │  │ Knowledge Base Loader (Runtime Context Injection)                 │ │ │
│  │  │ • Singleton Pattern für Performance                               │ │ │
│  │  │ • Query Enhancement mit kritischen Mappings                       │ │ │
│  │  │ • LLM Prompt Injection: "KALTMIETE = BEWOHNER.Z1"                │ │ │
│  │  │ • SQL Validierung gegen bekannte Patterns                         │ │ │
│  │  └────────────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │                             DATA LAYER                                   │ │
│  │ ┌────────────────┐ ┌──────────────────┐ ┌───────────────────────────────┐│ │
│  │ │ JSON Exports   │ │ Firebird Database│ │ In-Memory Search Index        ││ │
│  │ │ • 35 Dateien   │ │ • WINCASA2022.FDB│ │ • 588 Entitäten               ││ │
│  │ │ • 229K Zeilen  │ │ • Embedded Mode  │ │ • Multi-field Indexing        ││ │
│  │ │ • UTF-8 Support│ │ • 126 Tabellen   │ │ • 1-5ms Response Times        ││ │
│  │ └────────────────┘ └──────────────────┘ └───────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │                      LOGGING & ANALYTICS LAYER                          │ │
│  │ ┌────────────────┐ ┌──────────────────┐ ┌───────────────────────────────┐│ │
│  │ │ Unified Logger │ │ Query Logger     │ │ Analytics Dashboard           ││ │
│  │ │ • Central Log  │ │ • Query Paths    │ │ • Performance Metrics         ││ │
│  │ │ • 5 Log Files  │ │ • Timing Data    │ │ • Business Analytics          ││ │
│  │ │ • Error Track  │ │ • Success Rates  │ │ • Real-time Monitoring        ││ │
│  │ └────────────────┘ └──────────────────┘ └───────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detaillierte Komponentenarchitektur

### 1. Presentation Layer (Web Interface)

#### streamlit_app.py
```python
class WincasaStreamlitApp:
    """
    Hauptanwendung mit Session State Management
    - 5-Modi Checkbox System
    - Full-width Container Layout  
    - Session-unique Button Keys
    - Tab-basierte Ergebnisanzeige
    """
```

**Architektur-Patterns**:
- Session-basierte App-Initialisierung verhindert Ghost-Buttons
- Container-Layout für Full-width Ergebnisse
- Button-Keys mit Session-ID für Eindeutigkeit

### 2. Core Engine Layer

#### Legacy Handler (Modi 1-4)
```
Mode 1: JSON_VANILLA   → llm_handler → layer4_json_loader  (~300ms)
Mode 2: JSON_SYSTEM    → llm_handler → layer4_json_loader  (~1500ms) 
Mode 3: SQL_VANILLA    → llm_handler → database_connection (~500ms)
Mode 4: SQL_SYSTEM     → llm_handler → database_connection (~2000ms)
```

#### Unified Engine (Modus 5)
```
Query → wincasa_query_engine → 3-Pfad Routing:
├── Template Engine      → Parametrized SQL + Security     (~100ms)
├── Optimized Search     → In-Memory Multi-Index           (1-5ms)
└── Legacy Fallback      → Internal call zu Modi 1-4       (original speed)
```

### 3. Intelligence Layer (Phase 2)

#### Intent Classification (3-Level)
```python
Level 1: Regex Patterns (95% Confidence)
├── "alle mieter" → TENANT_SEARCH
├── "portfolio" → OWNER_PORTFOLIO  
├── "leerstand" → VACANCY_ANALYSIS
└── "kaltmiete" → RENT_QUERY

Level 2: LLM Classification (GPT-4o-mini)
├── Business Context Understanding
├── Entity Extraction (Namen, Adressen)
└── Template Availability Check

Level 3: Intelligent Fallback
├── Structured Search für Entity Lookups
├── Legacy SQL für Complex Analytics
└── Error Handling mit Graceful Degradation
```

#### Query Routing Logic
```python
def route_query(query: str, context: Dict) -> ExecutionPath:
    """
    Intelligente Query-Routing basierend auf:
    1. Intent Classification (Regex → LLM → Fallback)
    2. Query Complexity Analysis
    3. Performance Requirements
    4. Fallback Availability
    """
    if simple_lookup_pattern(query):
        return OptimizedSearchPath(response_time="1-5ms")
    elif templatable_query(query):
        return TemplateEnginePath(response_time="~100ms")
    else:
        return LegacyFallbackPath(response_time="500-2000ms")
```

### 4. Knowledge Base Architecture

#### Zero-Hardcoding System
```python
class KnowledgeExtractor:
    """
    Automatische Field-Mapping Extraktion aus SQL-Dateien
    - Parst 35 SQL-Dateien mit sqlparse
    - Extrahiert 226 Field-Mappings
    - Analysiert Join-Relationships
    - Identifiziert Business-Vokabular
    """
    
class KnowledgeBaseLoader:
    """
    Runtime Context-Injection für LLM-Prompts
    - Singleton Pattern für Performance
    - Kritische Mapping-Injection (KALTMIETE = BEWOHNER.Z1)
    - SQL-Validierung gegen bekannte Patterns
    """
```

#### Knowledge Base Files Structure
```
knowledge_base/
├── alias_map.json              # 226 field mappings (alias → canonical)
├── join_graph.json             # Table relationships & foreign keys
├── business_vocabulary.json    # German terms → SQL context mappings
├── business_vocabulary_candidates.json  # Potential new mappings
└── extraction_report.txt       # Analysis summary & statistics
```

### 5. Data Access Layer

#### Unified Data Access Pattern
```python
class DataAccessLayer:
    """
    Abstrahiert verschiedene Datenquellen:
    - Firebird Database (real-time queries)
    - JSON Exports (cached fast access)  
    - In-Memory Search Index (ultra-fast)
    """
    
    def execute_query(self, query: str, source: DataSource) -> QueryResult:
        if source == DataSource.OPTIMIZED_SEARCH:
            return self.search_engine.query(query)  # 1-5ms
        elif source == DataSource.JSON_CACHE:
            return self.json_loader.query(query)    # ~300ms
        else:
            return self.database.execute(query)     # 500-2000ms
```

### 6. Performance Architecture

#### Multi-tier Performance Design
```
Performance Tier 1: Optimized Search (1-5ms)
├── In-Memory Multi-Index für 588 Entitäten
├── Exact Match + Fuzzy Search
└── 100% Success Rate für Entity Lookups

Performance Tier 2: Template Engine (~100ms)  
├── Parametrisierte SQL mit Security
├── Firebird-optimierte Queries
└── Business-Logic Templates

Performance Tier 3: Legacy Fallback (500-2000ms)
├── LLM-basierte SQL-Generierung
├── Full Database Access
└── 100% Fallback Guarantee
```

### 7. Logging & Analytics Architecture

#### Multi-Layer Logging System
```
logs/
├── layer2.log              # Main application logs (783KB)
├── layer2_api.log          # API interaction logs (13MB) 
├── layer2_errors.log       # Error tracking (28KB)
├── layer2_performance.log  # Performance metrics (811KB)
└── query_paths.log         # Query routing decisions (6KB)
```

#### Analytics Components
```python
class WincasaAnalyticsSystem:
    """
    Business Analytics mit Real-time Monitoring
    - Query Performance Tracking
    - Mode Usage Distribution
    - Error Pattern Analysis
    - Cost Optimization Metrics
    """

class WincasaUnifiedLogger:
    """
    Zentrales Logging Framework
    - Structured Logging mit JSON Format
    - Query Path Tracking (Template/Search/Legacy)
    - Performance Metrics Collection
    - Error Categorization & Alerting
    """
```

---

## Deployment-Architektur

### Feature Flag System
```python
def should_use_unified_engine(user_id: str) -> bool:
    """
    Hash-based consistent assignment für graduelle Rollout
    - Feature Flag Check
    - Override Users (Always Unified)
    - Hash-based Percentage Assignment
    """
    if not config["unified_system_enabled"]:
        return False
    
    if user_id in config["override_users"]:
        return True
    
    hash_value = md5(f"{user_id}{salt}").hexdigest()
    percentage = int(hash_value[:2], 16) / 255 * 100
    return percentage < config["rollout_percentage"]
```

### Configuration Management
```
config/
├── sql_paths.json          # Zentrale Pfad-Konfiguration
├── query_engine.json       # Query Engine Konfiguration  
└── feature_flags.json      # Feature Toggle System
```

---

## Security Architecture

### Datenschutz & Sicherheit
```python
class SecurityLayer:
    """
    Multi-layer Security Implementation
    - API Keys in separaten ENV-Dateien (/home/envs/openai.env)
    - Firebird Embedded Mode (kein Server)
    - SQL Injection Prevention via Parameter-Substitution
    - 100k Row Limit für Runaway Query Prevention
    """
```

### Query Validation
```python
def validate_sql_query(query: str, known_patterns: List[str]) -> bool:
    """
    Knowledge-based SQL Validation
    - Prüfung gegen bekannte Field-Mappings
    - Business Rule Validation (EIGNR = -1, ONR >= 890)
    - Kritische Field-Mapping Enforcement (KALTMIETE = BEWOHNER.Z1)
    """
```

---

## Evolution Path

### Legacy → Modern Transformation
```
Phase 0: Legacy System (Modi 1-4)
    ↓
Phase 2.1: Optimized Search (1000x Performance)
    ↓  
Phase 2.2: Template System (Structured SQL)
    ↓
Phase 2.3: Unified Engine (Intelligent Routing)
    ↓
Phase 2.4: Knowledge System (Zero-Hardcoding)
    ↓
Current: Production Ready (100% Test Coverage)
```

### Future Architecture Considerations
- Microservice Decomposition für horizontale Skalierung
- GraphQL API für flexible Client-Integration  
- Real-time WebSocket für Live-Updates
- Distributed Logging für Enterprise-Scale
- Machine Learning für Query Intent Optimization

---

Diese Architektur ermöglicht **risikofreie Migration**, **datengetriebene Entscheidungen** und **Enterprise-Grade Performance** für ein production-ready AI-powered Property Management System.