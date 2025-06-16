# TASKS.md

## Aktuelle Tasks

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
Session 14: HTMX Migration (NEW)
- T14.001: HTMX-Static-Generator-Core (20h)
- T14.002: Minimal-CGI-API-Endpoints (16h)
- T14.003: Dynamic-UI-Model-Generation (12h)
- T14.004: HTMX-Component-Library (14h)
- T14.005: Nginx-HTMX-Deployment-Pipeline (8h)
- T14.006: Streamlit-HTMX-Parallel-Testing (6h)
Total: 76h (Major Architecture Migration)

Session 15: HTMX Enhancement & Core Features
- T9.002: KB-Auto-Update (12h) - Enhanced for HTMX
- T9.011: Multi-User (20h) - HTMX-based
- T14.007: Real-time-Analytics-HTMX (16h)
Total: 48h

Session 16: Business Features (HTMX-native)
- T9.030: Report-Generator (18h) - HTMX integration
- T9.031: Financial-Dashboard (16h) - Pure HTMX
- T14.008: Export-System-HTMX (12h)
Total: 46h
```

### Success-Metrics
- Velocity: ~35h/Session (Session 14: 76h for major migration)
- Quality: >95% Test-Coverage
- **Accuracy: 100% Correct Results** (contextually and actual values)
- Reliability: <1% Error-Rate

### HTMX Migration Metrics (Session 14)
- **Architecture**: Streamlit (1,328 lines) → Static HTMX + CGI (estimated <400 lines)
- **Performance**: Target 10x improvement (no Python reload per request)
- **Maintainability**: Generated UI from Schema (Zero-Drift compliance)
- **Dependencies**: Remove Streamlit dependency, add nginx + fcgiwrap
- **Deployment**: One-command build + deploy via enhanced sync-project.sh