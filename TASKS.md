# TASKS.md

## Aktuelle Tasks

### P0: CRITICAL - System liefert 0% korrekte Antworten [Session 14 - COMPLETED]

- ID: T14.001
  Title: CRITICAL-SQL-Generation-Failure
  Effort: 2h
  Status: done
  SessionID: ddl-fix-20250616
  Description: SQL generation produced 0% correct queries due to fantasy table/field names
  Root-Cause: System prompts lacked actual Firebird DDL schemas
  Evidence: 
    - LLM generated: EIGENTUMER table (correct: EIGADR)
    - LLM generated: NACHNAME field (correct: ENAME)
    - LLM generated: BEWNAME field (correct: BNAME)
    - LLM generated: KALTMIETE field (correct: Z1)
  Solution: Integrated real DDL schemas into system prompts

- ID: T14.002
  Title: Extract-DDL-Schemas
  Effort: 4h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Extracted real Firebird DDL schemas from database files
  Dependencies: Database-Access
  Components: create_focused_ddl_documentation.py
  Result: ✅ Created focused DDL documentation from data/ddl_creation schema/
  Key Discoveries: 
    - BEWOHNER table has NO EIGNR field (critical!)
    - Correct field names: BNAME not BEWNAME, Z1 not KALTMIETE
    - Exact table names: EIGADR not EIGENTUMER

- ID: T14.003
  Title: Update-System-Prompts-With-DDL
  Effort: 6h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Updated all system prompts with real DDL schemas
  Dependencies: T14.002
  Components: 
    - src/wincasa/utils/VERSION_B_SQL_SYSTEM.md - Updated with DDL schemas
    - Created: update_sql_system_prompts.py, fix_sql_generation.py
    - Created: enhance_sql_prompt.py for explicit table enforcement
  Result: ✅ System prompts now contain exact table/field names

- ID: T14.004
  Title: Fix-Mode-Case-Sensitivity
  Effort: 4h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Fixed case sensitivity bug causing wrong prompt loading
  Dependencies: LLM-Handler
  Components: 
    - src/wincasa/core/llm_handler.py - Fixed mode.lower() handling
    - Created: fix_mode_case.py, fix_llm_handler_prompts.py
  Result: ✅ SQL_VANILLA now correctly maps to sql_vanilla prompt

- ID: T14.005
  Title: Update-Knowledge-Base-DDL
  Effort: 8h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Updated knowledge base with DDL-verified field names
  Dependencies: T14.002
  Components: 
    - data/knowledge_base/alias_map.json - Updated with correct mappings
    - Created: update_knowledge_base_ddl.py
    - Created: fix_json_exporter_fields.py - Fixed 26 SQL files
  Result: ✅ Knowledge base now uses correct DDL field names

- ID: T14.006
  Title: Disable-Confusing-Knowledge-Context
  Effort: 2h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Disabled knowledge base context for SQL modes to avoid confusion
  Dependencies: LLM-Handler
  Components: src/wincasa/core/llm_handler.py
  Result: ✅ SQL modes now use only DDL schemas, not conflicting context

- ID: T14.007
  Title: Test-SQL-Generation-Success
  Effort: 4h
  Status: done
  SessionID: ddl-fix-20250616
  Description: Tested all fixes with realistic queries
  Dependencies: All T14.* tasks
  Components: test_realistic_queries.py, test_sql_mode.py
  Result: ✅ 20/20 test queries successful, 100% correct SQL generation

### Session 14: DDL Schema Integration [COMPLETED]

- ID: T17.008
  Title: Create-FOCUSED-DDL-Documentation
  Effort: 2h
  Status: pending
  SessionID: critical-fix-20250616
  Description: Erstelle FOKUSSIERTE Schema-Dokumentation NUR für aktuell genutzte Tabellen
  Dependencies: data/ddl_creation schema/, data/sql/*.sql (für genutzte Tabellen)
  Priority-Tables: 
    1. CORE (aus SQL-Queries): BEWOHNER, EIGADR, OBJEKTE, WOHNUNG, KONTEN, BUCHUNG
    2. SUPPORT (wenn referenziert): BEWADR, EIGENTUEMER, VERSAMMLUNG, RUECKPOS
    3. IGNORIEREN: Alle anderen 190+ Tabellen!
  Components: 
    - tools/create_focused_ddl_documentation.py
    - Analysiere data/sql/*.sql für tatsächlich genutzte Tabellen/Felder
    - Dokumentiere NUR diese Tabellen aus DDL
  Result: Kompakte, übersichtliche Schema-Referenz für LLM (max. 10-15 Tabellen)

- ID: T17.009
  Title: Update-SQL-System-Prompts-FOCUSED
  Effort: 1h
  Status: pending
  SessionID: critical-fix-20250616
  Description: Update VERSION_B_SQL_*.md mit FOKUSSIERTEM Schema
  Dependencies: T17.008
  Components:
    - VERSION_B_SQL_SYSTEM.md - NUR Core-Tabellen detailliert
    - VERSION_B_SQL_VANILLA.md - Ultra-kompakt (5-6 Haupttabellen)
    - Kritische Korrekturen prominent (KEIN EIGNR in BEWOHNER!)
  Result: Schlanke SQL-Prompts die LLM nicht überfordern

- ID: T17.010
  Title: Update-JSON-System-Prompts-FOCUSED
  Effort: 1h
  Status: pending
  SessionID: critical-fix-20250616
  Description: Update VERSION_A_JSON_*.md mit FOKUSSIERTEN Feld-Mappings
  Dependencies: T17.008
  Components:
    - VERSION_A_JSON_SYSTEM.md - NUR Felder aus genutzten Tabellen
    - VERSION_A_JSON_VANILLA.md - Minimal-Set an Mappings
    - Mappe NUR JSON-Export-Felder die in data/exports/*.json existieren
  Result: Präzise JSON-Prompts ohne unnötigen Ballast

- ID: T17.011
  Title: Generate-MINIMAL-Knowledge-Base
  Effort: 2h
  Status: pending
  SessionID: critical-fix-20250616
  Description: Generiere MINIMALE Knowledge Base nur für genutzte Tabellen
  Dependencies: T17.008
  Components:
    - tools/generate_minimal_kb_from_ddl.py
    - NUR Tabellen/Felder aus data/sql/*.sql extrahieren
    - Beziehungen NUR zwischen genutzten Tabellen
    - Business-Terms NUR für vorhandene Felder
  Result: Schlanke Knowledge Base (~50KB statt mehrere MB)

- ID: T17.012
  Title: Test-DDL-Updates-With-Critical-Queries
  Effort: 2h
  Status: pending
  SessionID: critical-fix-20250616
  Description: Teste kritische Queries die vorher fehlschlugen
  Dependencies: T17.009, T17.010, T17.011
  Test-Queries:
    - "Zeige alle Mieter" (BEWOHNER nicht TENANTS)
    - "Liste aller Eigentümer" (EIGADR nicht OWNERS)
    - "Summe der Kaltmiete" (Z1 nicht KALTMIETE)
    - "Finde Leerstand" (LEFT JOIN, kein EIGNR in BEWOHNER)
  Result: Alle kritischen Queries funktionieren

### P0: Critical Production - HTMX Migration [NEW Session 14]

- ID: T14.001
  Title: HTMX-Static-Generator-Core
  Effort: 20h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: Erstelle HTMX Static Generator der aus Knowledge Base + Schema komplette HTML/HTMX Anwendung generiert
  Dependencies: Knowledge-System, SAD-Pipeline
  Components: tools/generators/htmx_generator.py, UI-Model-Generator, Template-Generator
  Result: Statische HTMX App wird aus Schema generiert (kein FastAPI)

- ID: T14.002
  Title: Minimal-CGI-API-Endpoints
  Effort: 16h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: Python CGI Scripts für HTMX API-Calls ohne Web-Framework (nginx + fcgiwrap)
  Dependencies: Query-Engine, Data-Access-Layer
  Components: api/query.py, api/analytics.py, api/export.py
  Result: Minimale Python API ohne FastAPI-Overhead

- ID: T14.003
  Title: Dynamic-UI-Model-Generation
  Effort: 12h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: UI-Schema-Generator der aus Database-Schema + Knowledge-Base UI-Models erstellt
  Dependencies: Knowledge-System, Database-Schema
  Components: Schema-to-UIModel-Converter, Field-Type-Inference, German-Label-Mapping
  Result: Automatic UI generation from 400+ field mappings

- ID: T14.004
  Title: HTMX-Component-Library
  Effort: 14h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: Wiederverwendbare HTMX-Komponenten für Query-Forms, Result-Tables, Analytics
  Dependencies: UI-Models
  Components: form-components.html, table-components.html, chart-components.html
  Result: Modular HTMX template library

- ID: T14.005
  Title: Nginx-HTMX-Deployment-Pipeline
  Effort: 8h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: Integration in sync-project.sh für automatisches Build + Deploy der HTMX-App
  Dependencies: Static-Generator, CGI-API
  Components: nginx.conf, fcgiwrap.conf, build-scripts
  Result: One-command deployment von generierter HTMX-App

- ID: T14.006
  Title: Streamlit-HTMX-Parallel-Testing
  Effort: 6h
  Status: pending
  SessionID: htmx-migration-20250615
  Description: Parallele Ausführung beider UIs für A/B Testing und schrittweise Migration
  Dependencies: HTMX-Core, Existing-Streamlit
  Components: nginx-routing, comparative-testing
  Result: Nahtloser Übergang zwischen UIs

### P0: Critical Production - Benchmark UI Implementation [Session 16]

- ID: T16.001
  Title: Complete-Benchmark-UI-Rewrite
  Effort: 8h
  Status: done
  SessionID: benchmark-ui-20250616
  Description: Complete rewrite of UI after user revealed "totally wrong UI context" - needed benchmark tool, not complex app
  Dependencies: Query-Engine, LLM-Handler
  Components: 
    - DELETED: src/wincasa/core/streamlit_app.py (1328 lines)
    - NEW: src/wincasa/core/benchmark_streamlit.py
    - NEW: htmx/benchmark.html, htmx/server.py
  Result: Two clean benchmark UIs (Streamlit + HTMX) for mode comparison

- ID: T16.002
  Title: Fix-Firebird-Connection-Issues
  Effort: 4h
  Status: done
  SessionID: benchmark-ui-20250616
  Description: Resolved "connection shutdown" error from embedded Firebird single connection limitation
  Dependencies: Database-Layer
  Components: src/wincasa/data/db_singleton.py
  Result: Multiple UIs can run simultaneously on ports 8668/8669

- ID: T16.003
  Title: Add-JSON-Table-Formatting
  Effort: 3h
  Status: done
  SessionID: benchmark-ui-20250616
  Description: Added automatic table formatting for JSON and structured text results
  Dependencies: UI-Layer
  Components: src/wincasa/utils/text_to_table_parser.py
  Result: JSON/Table/Text view switching in both UIs

### P0: Critical Production - Quality Focus [COMPLETED Session 12]
- ID: T12.001
  Title: Remove-Performance-Speed-Metrics
  Effort: 2h
  Status: done
  SessionID: quality-focus-20250615
  Description: Removed all speed/performance references from documentation. Focus purely on 100% correctness
  Dependencies: Documentation
  
- ID: T12.002
  Title: Enhanced-Field-Mappings-Expansion
  Effort: 24h
  Status: done
  SessionID: quality-focus-20250615
  Description: Expanded Knowledge Base field mappings from 226 to 400+ mappings for complete German property coverage
  Dependencies: Knowledge-System
  Result: Created expand_field_mappings.py, add_remaining_mappings.py, final_mappings_batch.py

- ID: T12.003
  Title: German-Business-Context-Enhancement
  Effort: 16h
  Status: done
  SessionID: quality-focus-20250615
  Description: Added comprehensive domain-specific German property management vocabulary (12→41 terms)
  Dependencies: Knowledge-System
  Result: Created enhance_german_vocabulary.py, enhanced business_vocabulary.json with WEG law, BetrKV compliance

- ID: T12.004
  Title: Few-Shot-Examples-Complex-Patterns
  Effort: 12h
  Status: done
  SessionID: quality-focus-20250615
  Description: Created 24 complex query pattern examples across 8 categories for sophisticated German property management
  Dependencies: LLM-Handler
  Result: Created create_complex_query_examples.py, complex_query_examples.json, complex_query_guide.md

- ID: T12.005
  Title: Semantic-Template-Engine-Mode-6
  Effort: 20h
  Status: done
  SessionID: quality-focus-20250615
  Description: Implemented Mode 6 - Semantic Template Engine with 95% pattern recognition for parameterized business patterns
  Dependencies: Query-Engine, Knowledge-System
  Result: Created semantic_template_engine.py, integrated with wincasa_query_engine.py

- ID: T9.002
  Title: Knowledge-Base-Auto-Update
  Effort: 12h
  Status: pending
  Description: File-Watcher für SQL-Änderungen
  Dependencies: Knowledge-System

### P1: Enhancements
- ID: T9.010
  Title: Advanced-Query-Analytics
  Effort: 16h
  Status: pending
  Description: ML-basierte Query-Pattern-Analyse
  Dependencies: Analytics-System

- ID: T9.011
  Title: Multi-User-Session-Management
  Effort: 20h
  Status: pending
  Description: User-Auth mit personalisierter Historie
  Dependencies: Streamlit-App

- ID: T9.012
  Title: REST-API-Interface
  Effort: 24h
  Status: pending → REPLACED by T14.002 (CGI-API)
  Description: FastAPI für externe Integration → MIGRATION: Minimal CGI API
  Dependencies: Query-Engine → HTMX-Migration

### P2: Optimizations
- ID: T9.020
  Title: Caching-Layer-Enhancement
  Effort: 12h
  Status: pending
  Description: Redis-Integration für Distributed-Cache
  Dependencies: Data-Access-Layer

- ID: T9.021
  Title: Database-Views-Optimization
  Effort: 10h
  Status: pending
  Description: Materialized-Views für Performance
  Dependencies: Database-Layer

- ID: T9.022
  Title: Search-Index-Optimization
  Effort: 8h
  Status: pending
  Description: Fuzzy-Search und Multi-Language
  Dependencies: Optimized-Search

### P3: Business-Features
- ID: T9.030
  Title: Business-Report-Generator
  Effort: 18h
  Status: pending
  Description: Automatisierte PDF/Excel-Reports
  Dependencies: Analytics-System

- ID: T9.031
  Title: Financial-Analytics-Dashboard
  Effort: 16h
  Status: pending
  Description: Cashflow und ROI-Analyse
  Dependencies: Business-Dashboard

- ID: T9.032
  Title: Maintenance-Document-Management
  Effort: 20h
  Status: pending
  Description: Wartungsplanung mit Dokumenten
  Dependencies: Core-System

### Known Issues
- ID: B9.002
  Title: Large-Result-Set-Performance
  Effort: 6h
  Priority: medium
  Impact: Degradation bei >1000 rows

- ID: B14.001
  Title: LLM-Generated-Wrong-Schema
  Effort: 0h (FIXED in T14.001-T14.003)
  Priority: RESOLVED
  Impact: Was generating 100% incorrect SQL
  Resolution: Integrated DDL schemas into prompts

- ID: B14.002
  Title: Mode-Case-Sensitivity
  Effort: 0h (FIXED in T14.004)
  Priority: RESOLVED
  Impact: Wrong prompts loaded for SQL modes
  Resolution: Fixed case handling in llm_handler.py
  
- ID: B14.003
  Title: Field-Mappings-Incorrect
  Effort: 0h (FIXED in T14.005)
  Priority: RESOLVED
  Impact: 26 SQL files had wrong field names
  Resolution: Updated all SQL files with DDL-verified names

### Maintenance-Tasks
- ID: M9.001
  Title: Knowledge-Base-Updates
  Frequency: weekly
  Effort: 2h/week
  Tasks: SQL-Changes, Field-Mappings, Vocabulary

- ID: M9.002
  Title: Performance-Monitoring
  Frequency: daily
  Effort: 30min/day
  Tasks: Metrics, Errors, Response-Times

### Quick-Wins (High-Impact/Low-Effort)
1. T9.020: Caching-Layer (12h)
2. T9.022: Search-Index-Optimization (8h)
3. B9.002: Large-Result-Performance (6h)

### Strategic (High-Impact/High-Effort)
1. T9.011: Multi-User-Management (20h)
2. T9.012: REST-API (24h)
3. T9.030: Report-Generator (18h)

## Completed Tasks

### Session 11: Project Refactoring & E2E Testing (COMPLETED - 2025-06-15)
- ✅ **Major Refactoring**: Migrated from flat structure to Python best practices
- ✅ **Package Structure**: Created src/wincasa/ with core/, data/, knowledge/, monitoring/, utils/
- ✅ **E2E Testing**: Comprehensive testing with Playwright UI automation
- ✅ **Import Updates**: All modules now use wincasa.category.module structure  
- ✅ **Path Fixes**: Resolved all configuration and import path issues
- ✅ **System Prompts**: Created missing VERSION_A_*.md and VERSION_B_*.md files
- ✅ **SAD Pipeline Tests**: Validated Self-Updating Stack with 11/11 tests passing
- ✅ **UI Automation**: Working Playwright selectors for Streamlit interaction
- ✅ **Test Architecture**: 4-layer test pyramid (Unit → Integration → E2E → Pipeline)
- ✅ **Documentation Updates**: Updated all core docs with new structure

### Session 10: Documentation Infrastructure (COMPLETED)
- ✅ Sphinx Documentation System Implementation
- ✅ SAD.md Self-Updating Stack Architecture  
- ✅ Documentation Scripts (sync-project.sh, update-docs.sh, docs-live.sh)
- ✅ Documentation Cleanup (INVENTORY.md, ARCHITECTURE.md, TASKS.md)
- ✅ Command Structure Modernization
- ✅ sphinx-autobuild Live Documentation

### Session 13: Server Management Infrastructure (COMPLETED - 2025-06-15)
- ✅ **Server Management Analysis**: Deep analysis with MCP Zen identifying process management issues
- ✅ **PM2 Integration**: Implemented PM2 process manager for reliable server operations
- ✅ **Logging Enhancement**: PYTHONUNBUFFERED=1 for immediate Python log visibility
- ✅ **Environment Setup**: Proper PYTHONPATH configuration in PM2 environment
- ✅ **Process Control**: Automatic restart with exponential backoff
- ✅ **Documentation**: Updated CLAUDE.md, SAD.md, ARCHITECTURE.md, INVENTORY.md
- ✅ **Scripts Created**: pm2-wincasa.sh for unified server management
- ✅ **Configuration**: ecosystem.config.js with full PM2 setup

### Session-Planning
```
Session 17: CRITICAL FIX - System Total Failure (CURRENT)
- T17.001: Critical-Analysis (2h)
- T17.002: Extract-DDL-Schema (4h)
- T17.003: Fix-System-Prompts (6h)
- T17.004: Fix-DB-Connection (4h)
- T17.005: Rebuild-Field-Mappings (8h)
- T17.006: Fix-Path-Resolution (2h)
- T17.007: Validate-All-Modes (4h)
Total: 30h (CRITICAL - System komplett unbrauchbar)

Session 18: HTMX Migration (POSTPONED until System works)
- T14.001: HTMX-Static-Generator-Core (20h)
- T14.002: Minimal-CGI-API-Endpoints (16h)
- T14.003: Dynamic-UI-Model-Generation (12h)
- T14.004: HTMX-Component-Library (14h)
- T14.005: Nginx-HTMX-Deployment-Pipeline (8h)
- T14.006: Streamlit-HTMX-Parallel-Testing (6h)
Total: 76h (Major Architecture Migration)

Session 19: HTMX Enhancement & Core Features
- T9.002: KB-Auto-Update (12h) - Enhanced for HTMX
- T9.011: Multi-User (20h) - HTMX-based
- T14.007: Real-time-Analytics-HTMX (16h)
Total: 48h

Session 20: Business Features (HTMX-native)
- T9.030: Report-Generator (18h) - HTMX integration
- T9.031: Financial-Dashboard (16h) - Pure HTMX
- T14.008: Export-System-HTMX (12h)
Total: 46h
```

### Success-Metrics
- Velocity: ~35h/Session (Session 17: 30h CRITICAL fix)
- Quality: >95% Test-Coverage
- **Accuracy: AKTUELL 0% → ZIEL 100% Correct Results**
- Reliability: AKTUELL 100% Error-Rate → ZIEL <1%
- **User Assessment: AKTUELL <20% → ZIEL >95% Zufriedenheit**

### HTMX Migration Metrics (Session 14)
- **Architecture**: Streamlit (1,328 lines) → Static HTMX + CGI (estimated <400 lines)
- **Performance**: Target 10x improvement (no Python reload per request)
- **Maintainability**: Generated UI from Schema (Zero-Drift compliance)
- **Dependencies**: Remove Streamlit dependency, add nginx + fcgiwrap
- **Deployment**: One-command build + deploy via enhanced sync-project.sh