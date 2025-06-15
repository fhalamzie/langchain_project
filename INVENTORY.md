# INVENTORY.md

## Aktive Komponenten

### Core Modules
- streamlit_app.py - Haupt-UI mit 5-Modi-Auswahl
- wincasa_query_engine.py - Unified Engine (3-Pfad-Routing)
- llm_handler.py - Legacy-Modi (1-4) OpenAI-Integration
- wincasa_optimized_search.py - In-Memory-Suche (1-5ms)
- unified_template_system.py - SQL-Template-System
- sql_template_engine.py - Sichere SQL-Generierung

### Data Layer
- layer4_json_loader.py - JSON-Export-Loader
- data_access_layer.py - Unified Interface SQL/JSON
- sql_executor.py - Firebird SQL-Ausführung
- json_exporter.py - SQL→JSON Export-Pipeline

### Knowledge Base
- knowledge_base_loader.py - 226 Feldmappings Runtime
- knowledge_extractor.py - SQL-Analyse & Extraktion

### Monitoring & Analytics
- wincasa_unified_logger.py - Zentrales Logging
- wincasa_query_logger.py - SQLite Query-Historie
- wincasa_monitoring_dashboard.py - Performance-Monitoring
- wincasa_analytics_system.py - Business-Metriken
- business_dashboard_simple.py - HTML Dashboard

### Testing
- test_suite_phase2.py - 26 Tests, 100% Coverage
- test_suite_quick.py - 5 Schnelltests ohne LLM
- test_layer4.py - SQL-Query-Validierung
- test_golden_queries_kb.py - 100 Business-Queries
- test_kaltmiete_query.py - KALTMIETE-Test
- test_knowledge_integration.py - KB-Integration
- phase24_integration_test.py - End-to-End Tests

### Utilities
- benchmark_current_modes.py - Performance-Vergleich
- debug_single_query.py - Query-Debugging
- config_loader.py - Konfigurationsverwaltung

### Scripts
- run_streamlit.sh - Server-Start
- export_json.sh - SQL→JSON Export
- sync-project.sh - Self-Updating Stack Sync (SAD.md)
- update-docs.sh - Sphinx Documentation Update
- run-tests.sh - Test-Runner (aus CLAUDE.md)

### Configuration
- config/sql_paths.json - SQL-Pfade
- config/query_engine.json - Engine-Flags
- config/feature_flags.json - System-Flags

### Data Assets
- SQL_QUERIES/ - 35 Business-SQL-Queries
- exports/ - 35 JSON-Exports (229.5k Zeilen)
- knowledge_base/ - Field-Mappings & Vocabulary
- test_data/golden_set/ - 100 Test-Queries
- wincasa_data/WINCASA2022.FDB - Firebird-DB
- wincasa_data/query_logs.db - SQLite Logs

### Documentation
- SAD.md - Self-Updating Stack (inkl. sync-project.sh & update-docs.sh)
- ARCHITECTURE.md - System-Architektur
- CLAUDE.md - Entwickler-Manual
- LOGGING.md - Logging-Standards
- TESTING.md - Test-Strategie
- TASKS.md - Aufgaben-Backlog
- API.md - API-Spezifikation
- CHANGELOG.md - Session-History
- readme.md - Projektübersicht
- docs/ - Sphinx HTML-Dokumentation