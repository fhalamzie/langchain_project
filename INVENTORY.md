# INVENTORY.md

## Projektstruktur (Refactored)

### Core Package: `src/wincasa/`

#### Core Modules (`src/wincasa/core/`)
- streamlit_app.py - Haupt-UI mit 5-Modi-Auswahl (Import: `wincasa.core.streamlit_app`)
- wincasa_query_engine.py - Unified Engine (3-Pfad-Routing) (Import: `wincasa.core.wincasa_query_engine`)
- llm_handler.py - Legacy-Modi (1-4) OpenAI-Integration (Import: `wincasa.core.llm_handler`)
- wincasa_optimized_search.py - In-Memory-Suche (1-5ms) (Import: `wincasa.core.wincasa_optimized_search`)
- unified_template_system.py - SQL-Template-System (Import: `wincasa.core.unified_template_system`)
- sql_template_engine.py - Sichere SQL-Generierung (Import: `wincasa.core.sql_template_engine`)

#### Data Layer (`src/wincasa/data/`)
- layer4_json_loader.py - JSON-Export-Loader (Import: `wincasa.data.layer4_json_loader`)
- data_access_layer.py - Unified Interface SQL/JSON (Import: `wincasa.data.data_access_layer`)
- sql_executor.py - Firebird SQL-Ausführung (Import: `wincasa.data.sql_executor`)
- json_exporter.py - SQL→JSON Export-Pipeline (Import: `wincasa.data.json_exporter`)

#### Knowledge Base (`src/wincasa/knowledge/`)
- knowledge_base_loader.py - 226 Feldmappings Runtime (Import: `wincasa.knowledge.knowledge_base_loader`)
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
- run_streamlit.sh - Server-Start (aktualisiert für src/ Struktur)
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
- alias_map.json - 226 Field-Mappings
- business_vocabulary.json - Deutsch→SQL Mappings
- join_graph.json - Tabellen-Beziehungen
- extraction_report.txt - Analyse-Summary

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

## Key Metrics (Unchanged)
- Test-Coverage: 100% (26/26 tests in integration/)
- Field-Mappings: 226 (data/knowledge_base/)
- Entities-Indexed: 588 (wincasa.core.wincasa_optimized_search)
- Performance: 1-5ms Search, ~100ms Templates
- Code-Modules: 21 (src/wincasa/*)
- Test-Files: 7 (tests/*/)
- Scripts: 5 (tools/scripts/)