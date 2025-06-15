# CLEANUP_INVENTORY.md

## Hintergrund

Dieses Inventar dokumentiert den aktuellen Stand der WINCASA-Codebasis durch eine vollständige Neuanalyse (Stand: 2025-06-15). Es dient als Grundlage für weitere Aufräumarbeiten und die Migration zu einer systematischen Dokumentationsstruktur.

**Status**: Produktionsreife Codebasis mit identifizierten Cleanup-Opportunitäten

---

## 📊 Gesamtübersicht

**Projektumfang**:
- **Python-Dateien**: 35 Dateien (~510KB)
- **Nicht-Python-Dateien**: 313 Dateien (~195MB)
- **Gesamtdateien**: 348 Dateien (~195.5MB)
- **Nach empfohlener Bereinigung**: ~270 Dateien (~95.5MB)

**Architektur**: Dual Query System - Legacy Modes (1-4) + Unified Engine (5)  
**Phase Status**: Phase 2 Complete (42/42 Tasks, 100% Test Coverage)

---

## 🐍 Python-Dateien Inventar

### Core Production Files (12 Dateien, ~200KB) ✅ BEHALTEN

- ID: streamlit_app.py
  Typ: Modul
  Status: active
  Begründung: Haupt-UI-Anwendung, 43KB, Einstiegspunkt
  Empfehlung: dokumentieren
  SessionID: ui-main-20250615

- ID: wincasa_query_engine.py
  Typ: Modul
  Status: active
  Begründung: Phase 2 unified query routing, 19KB, von 7 Dateien importiert
  Empfehlung: dokumentieren
  SessionID: query-engine-20250615

- ID: llm_handler.py
  Typ: Modul
  Status: active
  Begründung: Legacy-Modi LLM-Integration, 48KB, von 9 Dateien importiert
  Empfehlung: dokumentieren
  SessionID: llm-core-20250615

- ID: layer4_json_loader.py
  Typ: Modul
  Status: active
  Begründung: JSON-Datenzugriffsschicht, 8.4KB, von 3 Dateien importiert
  Empfehlung: dokumentieren
  SessionID: json-loader-20250615

- ID: wincasa_unified_logger.py
  Typ: Modul
  Status: active
  Begründung: Zentrales Logging-System, 17KB, kritisch für Monitoring
  Empfehlung: dokumentieren
  SessionID: logger-20250615

- ID: wincasa_query_logger.py
  Typ: Modul
  Status: active
  Begründung: Query-History-Datenbank, 20KB, für Analytics
  Empfehlung: dokumentieren
  SessionID: query-logger-20250615

- ID: data_access_layer.py
  Typ: Modul
  Status: active
  Begründung: Unified data abstraction, 16KB
  Empfehlung: dokumentieren
  SessionID: data-layer-20250615

- ID: config_loader.py
  Typ: Modul
  Status: active
  Begründung: Konfigurations-Management, 13KB
  Empfehlung: dokumentieren
  SessionID: config-20250615

- ID: wincasa_optimized_search.py
  Typ: Modul
  Status: active
  Begründung: High-Performance-Suche, 23KB, 1-5ms Response
  Empfehlung: dokumentieren
  SessionID: search-20250615

- ID: sql_template_engine.py
  Typ: Modul
  Status: active
  Begründung: SQL-Template-System, 22KB, intern verwendet
  Empfehlung: dokumentieren
  SessionID: template-20250615

- ID: unified_template_system.py
  Typ: Modul
  Status: active
  Begründung: Template-Management, 18KB, von Query Engine verwendet
  Empfehlung: dokumentieren
  SessionID: unified-20250615

- ID: knowledge_base_loader.py
  Typ: Modul
  Status: active
  Begründung: Field-Mapping-Loader, 9KB, 226 Mappings
  Empfehlung: dokumentieren
  SessionID: knowledge-20250615

### Analytics & Monitoring (3 Dateien, ~80KB) ✅ BEHALTEN

- ID: wincasa_analytics_system.py
  Typ: Anwendung
  Status: active
  Begründung: Business-Metriken-Dashboard, 33KB, Standalone
  Empfehlung: dokumentieren
  SessionID: analytics-20250615

- ID: wincasa_monitoring_dashboard.py
  Typ: Anwendung
  Status: active
  Begründung: Real-time Monitoring, 23KB, Standalone
  Empfehlung: dokumentieren
  SessionID: monitoring-20250615

- ID: business_dashboard_simple.py
  Typ: Anwendung
  Status: active
  Begründung: Vereinfachtes Business-Dashboard, 24KB, Standalone
  Empfehlung: dokumentieren
  SessionID: business-dash-20250615

### Test-Dateien (7 Dateien, ~60KB) ✅ BEHALTEN

- ID: test_suite_phase2.py
  Typ: Test
  Status: active
  Begründung: Vollständige Testsuite, 19KB, 26 Tests
  Empfehlung: dokumentieren
  SessionID: test-phase2-20250615

- ID: test_suite_quick.py
  Typ: Test
  Status: active
  Begründung: Schnelle Test-Teilmenge, 7.3KB
  Empfehlung: dokumentieren
  SessionID: test-quick-20250615

- ID: test_layer4.py
  Typ: Test
  Status: active
  Begründung: SQL→JSON Validierung, 4.5KB
  Empfehlung: dokumentieren
  SessionID: test-layer4-20250615

- ID: test_golden_queries_kb.py
  Typ: Test
  Status: active
  Begründung: Business-Query-Tests, 6.3KB
  Empfehlung: dokumentieren
  SessionID: test-golden-20250615

- ID: test_kaltmiete_query.py
  Typ: Test
  Status: active
  Begründung: Spezifischer Query-Test, 1.6KB
  Empfehlung: dokumentieren
  SessionID: test-kaltmiete-20250615

- ID: test_knowledge_integration.py
  Typ: Test
  Status: active
  Begründung: Wissensbasis-Tests, 1.7KB
  Empfehlung: dokumentieren
  SessionID: test-knowledge-20250615

- ID: phase24_integration_test.py
  Typ: Test
  Status: active
  Begründung: Phase 2.4 Integrationstests, 21KB
  Empfehlung: dokumentieren
  SessionID: test-integration-20250615

### Utility-Skripte (7 Dateien, ~90KB) 🔄 REVIEW

- ID: json_exporter.py
  Typ: Utility
  Status: active
  Begründung: SQL→JSON Export-Utility, 25KB, Standalone
  Empfehlung: dokumentieren
  SessionID: exporter-20250615

- ID: knowledge_extractor.py
  Typ: Utility
  Status: active
  Begründung: Extrahiert Field-Mappings, 13KB, Standalone
  Empfehlung: dokumentieren
  SessionID: extractor-20250615

- ID: benchmark_current_modes.py
  Typ: Utility
  Status: active
  Begründung: Performance-Benchmarking, 13KB, Standalone
  Empfehlung: dokumentieren
  SessionID: benchmark-20250615

- ID: debug_single_query.py
  Typ: Utility
  Status: active
  Begründung: Interaktiver Query-Debugger, 6.6KB, Standalone
  Empfehlung: dokumentieren
  SessionID: debug-20250615

- ID: create_views_step_by_step.py
  Typ: Utility
  Status: refactor-needed
  Begründung: Datenbank-View-Ersteller, 12KB, einmalig
  Empfehlung: verschieben
  SessionID: views-20250615

- ID: realistic_golden_queries.py
  Typ: Utility
  Status: refactor-needed
  Begründung: Golden-Set-Generator, 15KB, einmalig
  Empfehlung: verschieben
  SessionID: golden-gen-20250615

- ID: sql_executor.py
  Typ: Utility
  Status: active
  Begründung: SQL-Ausführungs-Handler, 9.3KB
  Empfehlung: dokumentieren
  SessionID: sql-exec-20250615

### Experimentelle/Ungenutzte Dateien (6 Dateien, ~65KB) ❌ LÖSCHEN

- ID: hierarchical_intent_router.py
  Typ: Modul
  Status: unused
  Begründung: Experimentell, 19KB, nicht importiert
  Empfehlung: löschen
  SessionID: intent-router-20250615

- ID: intent_classification_schema.py
  Typ: Modul
  Status: unused
  Begründung: Experimentell, 19KB, nicht importiert
  Empfehlung: löschen
  SessionID: intent-schema-20250615

- ID: json_search_app.py
  Typ: Anwendung
  Status: deprecated
  Begründung: Alternative UI, 7.4KB, nicht verwendet
  Empfehlung: löschen
  SessionID: search-app-20250615

- ID: sql_syntax_fixer.py
  Typ: Utility
  Status: unused
  Begründung: SQL-Korrektur-Utility, 3.5KB, nicht importiert
  Empfehlung: löschen
  SessionID: sql-fixer-20250615

- ID: wincasa_tools.py
  Typ: Modul
  Status: unused
  Begründung: Verschiedene Tools, 16KB, nicht importiert
  Empfehlung: löschen
  SessionID: tools-20250615

- ID: database_connection.py
  Typ: Modul
  Status: unused
  Begründung: Datenbank-Verbindungs-Helper, 3.2KB, nicht importiert
  Empfehlung: löschen
  SessionID: db-conn-20250615

---

## 📁 Verzeichnis- und Daten-Inventar

### Produktions-Daten (✅ BEHALTEN)

- ID: SQL_QUERIES/
  Typ: Verzeichnis
  Status: active
  Begründung: 35 SQL-Dateien, Core Business Logic
  Empfehlung: dokumentieren
  SessionID: sql-queries-20250615

- ID: exports/
  Typ: Verzeichnis
  Status: active
  Begründung: 35 JSON-Exports, 229,500 Zeilen Produktionsdaten
  Empfehlung: dokumentieren
  SessionID: exports-20250615

- ID: wincasa_data/WINCASA2022.FDB
  Typ: Datei
  Status: active
  Begründung: Produktionsdatenbank, 68MB
  Empfehlung: dokumentieren
  SessionID: database-20250615

- ID: config/
  Typ: Verzeichnis
  Status: active
  Begründung: Konfigurationsdateien (sql_paths.json, feature_flags.json, etc.)
  Empfehlung: dokumentieren
  SessionID: config-dir-20250615

- ID: knowledge_base/
  Typ: Verzeichnis
  Status: active
  Begründung: 226 Field-Mappings, Business-Vokabular
  Empfehlung: dokumentieren
  SessionID: kb-dir-20250615

### Test- und Entwicklungsdaten (❌ ARCHIVIEREN/LÖSCHEN)

- ID: wincasa_data/source/
  Typ: Verzeichnis
  Status: deprecated
  Begründung: 151 CSV-Dateien, 80MB Entwicklungsdaten
  Empfehlung: löschen
  SessionID: source-data-20250615

- ID: golden_set/
  Typ: Verzeichnis
  Status: refactor-needed
  Begründung: Test-Queries und Baseline-Ergebnisse
  Empfehlung: verschieben
  SessionID: golden-set-20250615

- ID: monitoring_data/
  Typ: Verzeichnis
  Status: deprecated
  Begründung: Alte Monitoring-Snapshots
  Empfehlung: löschen
  SessionID: monitoring-data-20250615

- ID: analytics_data/
  Typ: Verzeichnis
  Status: deprecated
  Begründung: Alte Analytics-Reports
  Empfehlung: löschen
  SessionID: analytics-data-20250615

- ID: shadow_mode_data/
  Typ: Verzeichnis
  Status: deprecated
  Begründung: A/B-Test-Daten
  Empfehlung: löschen
  SessionID: shadow-data-20250615

### Log-Dateien (🔄 ROTIEREN)

- ID: logs/
  Typ: Verzeichnis
  Status: operational
  Begründung: Aktuelle Log-Dateien (layer2.log 783KB, layer2_api.log 13MB)
  Empfehlung: behalten
  SessionID: logs-20250615

- ID: *.log (Root-Verzeichnis)
  Typ: Dateien
  Status: deprecated
  Begründung: 15 Log-Dateien im Root, sollten in logs/ sein
  Empfehlung: löschen
  SessionID: root-logs-20250615

### Dokumentation (🔄 KONSOLIDIEREN)

#### Behalten:
- ID: CLAUDE.md
  Typ: Datei
  Status: active
  Begründung: Hauptentwicklerdokumentation
  Empfehlung: dokumentieren
  SessionID: claude-doc-20250615

- ID: readme.md
  Typ: Datei
  Status: active
  Begründung: Projektübersicht
  Empfehlung: dokumentieren
  SessionID: readme-20250615

- ID: ARCHITECTURE.md
  Typ: Datei
  Status: active
  Begründung: Technische Architektur
  Empfehlung: dokumentieren
  SessionID: arch-doc-20250615

- ID: API.md
  Typ: Datei
  Status: active
  Begründung: API-Dokumentation
  Empfehlung: dokumentieren
  SessionID: api-doc-20250615

#### Archivieren:
- ID: PHASE2_FINAL_SUMMARY.md
  Typ: Datei
  Status: deprecated
  Begründung: Historisches Dokument
  Empfehlung: verschieben
  SessionID: phase2-doc-20250615

- ID: KNOWLEDGE_BASE_IMPLEMENTATION.md
  Typ: Datei
  Status: deprecated
  Begründung: Implementierungsdetails
  Empfehlung: verschieben
  SessionID: kb-doc-20250615

- ID: tasks.md
  Typ: Datei
  Status: deprecated
  Begründung: Erledigte Tasks
  Empfehlung: löschen
  SessionID: tasks-doc-20250615

### Sonstige Dateien

- ID: requirements.txt
  Typ: Datei
  Status: active
  Begründung: Python-Abhängigkeiten
  Empfehlung: dokumentieren
  SessionID: requirements-20250615

- ID: run_streamlit.sh
  Typ: Datei
  Status: active
  Begründung: Server-Start-Skript
  Empfehlung: dokumentieren
  SessionID: run-script-20250615

- ID: export_json.sh
  Typ: Datei
  Status: active
  Begründung: Export-Skript
  Empfehlung: dokumentieren
  SessionID: export-script-20250615

---

## 🧹 Cleanup-Zusammenfassung

### Empfohlene Aktionen:

**1. Python-Dateien löschen (6 Dateien, ~65KB):**
```bash
rm hierarchical_intent_router.py
rm intent_classification_schema.py
rm json_search_app.py
rm sql_syntax_fixer.py
rm wincasa_tools.py
rm database_connection.py
```

**2. Verzeichnisse löschen (~80MB):**
```bash
rm -rf wincasa_data/source/
rm -rf monitoring_data/
rm -rf analytics_data/
rm -rf shadow_mode_data/
```

**3. Log-Dateien aufräumen:**
```bash
rm *.log  # Alle Logs im Root-Verzeichnis
```

**4. Dokumentation archivieren:**
```bash
mkdir -p archive/docs
mv PHASE2_FINAL_SUMMARY.md archive/docs/
mv KNOWLEDGE_BASE_IMPLEMENTATION.md archive/docs/
mv tasks.md archive/docs/
```

**5. Test-Daten verschieben:**
```bash
mkdir -p test_data
mv golden_set/ test_data/
```

**6. Utility-Skripte organisieren:**
```bash
mkdir -p scripts
mv create_views_step_by_step.py scripts/
mv realistic_golden_queries.py scripts/
```

### Ergebnis nach Bereinigung:

**Vorher:**
- Python-Dateien: 35 (~510KB)
- Nicht-Python-Dateien: 313 (~195MB)
- Gesamt: 348 Dateien (~195.5MB)

**Nachher:**
- Python-Dateien: 29 (~445KB) [-17%]
- Nicht-Python-Dateien: ~240 (~95MB) [-23%]
- Gesamt: ~270 Dateien (~95.5MB) [-51% Speicherplatz]

**Cleanup-Status**: ✅ Bereit zur Durchführung

### Vorteile der Bereinigung:

1. **Klarere Struktur**: Entfernung experimenteller und ungenutzter Dateien
2. **Weniger Verwirrung**: Keine duplizierten oder veralteten Komponenten
3. **Bessere Performance**: 100MB weniger Speicherplatz
4. **Einfachere Wartung**: Fokus auf produktive Komponenten

---

## 🚀 Nächste Schritte

1. **Backup erstellen** vor der Bereinigung
2. **Cleanup-Skript ausführen** (siehe Befehle oben)
3. **Tests durchführen** nach der Bereinigung
4. **INVENTORY.md erstellen** basierend auf diesem Cleanup-Inventar
5. **Dokumentation aktualisieren** für die bereinigte Struktur

**Migration zu strukturierter Dokumentation:**
- CLEANUP_INVENTORY.md → INVENTORY.md (strukturiertes Komponenten-Inventar)
- Archivierte Docs → CHANGELOG.md (Historie)
- Bereinigte Struktur → ARCHITECTURE.md (aktualisierte Architektur)