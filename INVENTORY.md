# INVENTORY.md

## Projektstruktur (Refactored)

### Core Package: `src/wincasa/`

#### Core Modules (`src/wincasa/core/`)
- ~~streamlit_app.py~~ - REMOVED Session 16 - Ersetzt durch benchmark_streamlit.py
- benchmark_streamlit.py - **NEW Session 16** - Benchmark UI für 5-Modi-Vergleich (Import: `wincasa.core.benchmark_streamlit`)
- wincasa_query_engine.py - Unified Engine (4-Pfad-Routing mit Mode 6) (Import: `wincasa.core.wincasa_query_engine`)
- semantic_template_engine.py - Mode 6: Semantic Templates (95% Erkennung) (Import: `wincasa.core.semantic_template_engine`)
- llm_handler.py - Legacy-Modi (1-4) OpenAI-Integration (Import: `wincasa.core.llm_handler`)
- wincasa_optimized_search.py - In-Memory-Suche (1-5ms) (Import: `wincasa.core.wincasa_optimized_search`)
- unified_template_system.py - SQL-Template-System (Import: `wincasa.core.unified_template_system`)
- sql_template_engine.py - Sichere SQL-Generierung (Import: `wincasa.core.sql_template_engine`)

#### Data Layer (`src/wincasa/data/`)
- layer4_json_loader.py - JSON-Export-Loader (Import: `wincasa.data.layer4_json_loader`)
- data_access_layer.py - Unified Interface SQL/JSON (Import: `wincasa.data.data_access_layer`)
- sql_executor.py - Firebird SQL-Ausführung (Import: `wincasa.data.sql_executor`)
- json_exporter.py - SQL→JSON Export-Pipeline (Import: `wincasa.data.json_exporter`)
- db_singleton.py - **NEW Session 16** - Firebird Singleton Connection (Import: `wincasa.data.db_singleton`)

#### Knowledge Base (`src/wincasa/knowledge/`)
- knowledge_base_loader.py - 400+ Feldmappings Runtime (Import: `wincasa.knowledge.knowledge_base_loader`)
- knowledge_extractor.py - SQL-Analyse & Extraktion (Import: `wincasa.knowledge.knowledge_extractor`)

#### Monitoring & Analytics (`src/wincasa/monitoring/`)
- wincasa_unified_logger.py - Zentrales Logging (Import: `wincasa.monitoring.wincasa_unified_logger`)
- wincasa_query_logger.py - SQLite Query-Historie (Import: `wincasa.monitoring.wincasa_query_logger`)
- wincasa_monitoring_dashboard.py - Performance-Monitoring (Import: `wincasa.monitoring.wincasa_monitoring_dashboard`)
- wincasa_analytics_system.py - Business-Metriken (Import: `wincasa.monitoring.wincasa_analytics_system`)
- business_dashboard_simple.py - HTML Dashboard (Import: `wincasa.monitoring.business_dashboard_simple`)

#### Utilities (`src/wincasa/utils/`)
- config_loader.py - Konfigurationsverwaltung (Import: `wincasa.utils.config_loader`)
- benchmark_current_modes.py - Performance-Vergleich (Import: `wincasa.utils.benchmark_current_modes`)
- debug_single_query.py - Query-Debugging (Import: `wincasa.utils.debug_single_query`)
- text_to_table_parser.py - **NEW Session 16** - Text zu Tabelle Parser (Import: `wincasa.utils.text_to_table_parser`)

### Testing Suite (`tests/`)

#### Unit Tests (`tests/unit/`)
- test_suite_quick.py - 5 Schnelltests ohne LLM
- test_kaltmiete_query.py - KALTMIETE-Test

#### Integration Tests (`tests/integration/`)
- test_suite_phase2.py - 26 Tests, 100% Coverage
- test_layer4.py - SQL-Query-Validierung
- test_golden_queries_kb.py - 100 Business-Queries
- test_knowledge_integration.py - KB-Integration
- phase24_integration_test.py - End-to-End Tests

#### End-to-End Tests (`tests/e2e/`) - To be implemented
- test_ui_interactions.py - Playwright UI Tests
- test_critical_flows.py - Business-Szenarien
- test_performance.py - Performance-Benchmarks

#### Pipeline Tests (`tests/pipeline/`) - To be implemented
- test_schema_propagation.py - SAD Schema-Change-Detection
- test_breaking_change.py - Breaking Change Detection
- test_documentation.py - Documentation Pipeline

#### Test Data (`tests/test_data/`)
- golden_set/ - 100 Test-Queries mit Baseline-Ergebnissen

### Development Tools (`tools/`)

#### Scripts (`tools/scripts/`)
- run_streamlit.sh - Server-Start (deprecated, use pm2-wincasa.sh)
- pm2-wincasa.sh - PM2 Server Management (empfohlen) [SessionID: server-pm2-20250615]
- wincasa-server.sh - Supervisord Server Management (Alternative, nicht verwendet) [SessionID: server-pm2-20250615]
- export_json.sh - SQL→JSON Export
- sync-project.sh - Self-Updating Stack Sync (SAD.md)
- update-docs.sh - Sphinx Documentation Update
- docs-live.sh - Live Sphinx Documentation Server

#### Utilities (`tools/`)
- create_views_step_by_step.py - DB View Creation
- realistic_golden_queries.py - Test Query Generation

### Configuration (`config/`)
- sql_paths.json - SQL-Pfade
- query_engine.json - Engine-Flags
- feature_flags.json - System-Flags

### Data Assets (`data/`)

#### SQL Queries (`data/sql/`)
- 01_eigentuemer.sql bis 35_buchungskonten_uebersicht.sql - 35 Business-SQL-Queries

#### Exports (`data/exports/`)
- 01_eigentuemer.json bis 35_buchungskonten_uebersicht.json - 35 JSON-Exports (229.5k Zeilen)
- rag_data/ - RAG-optimierte Datenexporte

#### Knowledge Base (`data/knowledge_base/`)
- alias_map.json - 400+ Field-Mappings (erweitert von 226)
- business_vocabulary.json - 41 German Property Terms (erweitert von 12)
- join_graph.json - Tabellen-Beziehungen
- extraction_report.txt - Analyse-Summary
- complex_query_examples.json - 24 komplexe Query-Beispiele (8 Kategorien) [SessionID: quality-focus-20250615]
- semantic_pattern_extensions.json - 5 erweiterte semantische Muster [SessionID: quality-focus-20250615]
- advanced_sql_templates.json - 3 komplexe SQL-Templates [SessionID: quality-focus-20250615]
- complex_query_guide.md - Umfassende Dokumentation für komplexe Queries [SessionID: quality-focus-20250615]
- business_vocabulary_candidates.json - Extrahierte Business-Begriffe aus SQL-Dateien [SessionID: quality-focus-20250615]

#### Database (`data/wincasa_data/`)
- WINCASA2022.FDB - Firebird-DB (126 Tabellen)
- query_logs.db - SQLite Query-Historie

#### Database Views (`data/database/`)
- create_phase2_views.sql - View-Definitionen
- views/ - Individuelle View-SQL-Dateien

### Documentation (`docs/`)
- Sphinx HTML-Dokumentation mit RTD Theme
- Automatisch generiert über update-docs.sh

### Root Documentation
- SAD.md - Self-Updating Stack (inkl. sync-project.sh & update-docs.sh)
- ARCHITECTURE.md - System-Architektur
- CLAUDE.md - Entwickler-Manual
- LOGGING.md - Logging-Standards
- TESTING.md - Test-Strategie
- TASKS.md - Aufgaben-Backlog
- API.md - API-Spezifikation
- CHANGELOG.md - Session-History
- INVENTORY.md - Dieses Dokument
- readme.md - Projektübersicht

### Process Management [SessionID: server-pm2-20250615]
- ecosystem.config.js - PM2 Konfiguration für WINCASA Server
- supervisord.conf - Alternative Supervisord Konfiguration (nicht verwendet)
- server_control.sh - Einfaches Server Control Script (deprecated)

### HTMX UI [SessionID: benchmark-ui-20250616]
- htmx/benchmark.html - **NEW Session 16** - Statische HTML Benchmark UI
- htmx/server.py - **NEW Session 16** - Python HTTP Server für HTMX

### Archive (`archive/`)
- Historische Dateien und veraltete Implementierungen

## Migration Notes

### Import Changes
Alle Python-Module verwenden jetzt die neue Package-Struktur:
```python
# Alt:
from streamlit_app import WincasaStreamlitApp

# Neu:
from wincasa.core.streamlit_app import WincasaStreamlitApp
```

### PYTHONPATH Setup
Scripts und Tests setzen automatisch: `PYTHONPATH=${PYTHONPATH}:$(pwd)/src`

### Session References
- Core Modules: phase2-20250614, unified-20250614
- Knowledge System: kb-20250614  
- Monitoring: monitoring-20250614
- Testing: test-20250614, golden-20250614
- Refactoring: refactor-20250615
- Quality Enhancement: quality-focus-20250615

### Root Scripts (Session 12)
- create_complex_query_examples.py - Generates complex query patterns [SessionID: quality-focus-20250615]
- test_complex_query_integration.py - Tests complex pattern integration [SessionID: quality-focus-20250615]
- expand_field_mappings.py - Adds initial field mappings [SessionID: quality-focus-20250615]
- add_remaining_mappings.py - Adds operational mappings [SessionID: quality-focus-20250615]
- final_mappings_batch.py - Completes 400+ field mappings [SessionID: quality-focus-20250615]
- enhance_german_vocabulary.py - Expands German business vocabulary [SessionID: quality-focus-20250615]

## Key Metrics (Updated Session 12)
- Test-Coverage: 100% (26/26 tests in integration/)
- Field-Mappings: 400+ (erweitert von 226 in data/knowledge_base/)
- Business Vocabulary: 41 German Terms (erweitert von 12)
- Complex Query Examples: 24 across 8 categories
- Semantic Patterns: 95% recognition accuracy (Mode 6)
- Entities-Indexed: 588 (wincasa.core.wincasa_optimized_search)
- Performance: 1-5ms Search, ~50ms Semantic Templates, ~100ms Templates
- Code-Modules: 22 (src/wincasa/*, added semantic_template_engine.py)
- Test-Files: 7 (tests/*/)
- Scripts: 11 (tools/scripts/ + 6 root scripts for Session 12)