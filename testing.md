# WINCASA Testing-Framework

Diese Dokumentation beschreibt das Testframework, die Teststandards und die Testverfahren für das WINCASA-Projekt.

## Testanforderungen

**KRITISCH:** Jede neue Funktion MUSS Tests BEVOR sie als vollständig markiert wird enthalten:
- **Unit-Tests** für alle neuen Funktionen und Module
- **Integrationstests** für Datenbankverbindungen und LLM-Integrationen
- **Systemtests** für vollständige Abfrage-Workflows
- **Tests nach jeder Implementierung ausführen**
- **Tests müssen VOR Git-Commit/Push bestanden werden**

## Testframework

Das WINCASA-Projekt verwendet ein modernes pytest-Framework mit einer 100% Test-Erfolgsrate.

### Teststruktur

```
tests/
├── unit/                 # Unit-Tests für einzelne Komponenten
│   └── test_sample.py    # Beispiel-Unit-Test
├── integration/          # Integration-Tests für Komponenteninteraktionen
├── conftest.py           # Pytest-Konfiguration und Fixtures
└── __init__.py           # Package-Initialisierung
```

Zusätzlich befinden sich spezielle Integrationstests im Hauptverzeichnis:
- `test_enhanced_qa_ui_integration.py` - UI-Workflow-Test
- `test_fdb_direct_interface.py` - Datenbankschnittstellen-Test
- `test_firebird_sql_agent.py` - SQL-Agent-Funktionalitätstest

### Test-Kategorien

#### 1. Unit-Tests (pytest-basiert)
- Konzentrieren sich auf einzelne Funktionen und Klassen
- Isolierte Tests mit Mocks für externe Abhängigkeiten
- Schnelle Ausführung für schnelles Feedback

```bash
# Unit-Tests ausführen
python -m pytest tests/unit/ -v
```

#### 2. Integrationstests
- Testen die Interaktion zwischen Komponenten
- Validieren, dass Module korrekt zusammenarbeiten
- Überprüfen End-to-End-Workflows

```bash
# Beispiele für Integrationstests
python test_enhanced_qa_ui_integration.py  # UI-Workflow vollständig
python test_fdb_direct_interface.py        # Datenbankverbindung
python test_firebird_sql_agent.py          # Agent-Funktionalität
python test_business_glossar_simple.py     # Business-Begriffe
python test_langchain_fix.py               # LangChain-Integration
```

#### 3. Systemtests (Performance & Retrieval)
- Testen das Gesamtsystem unter realen Bedingungen
- Fokus auf Leistung und Korrektheit
- Überprüfen aller Retrieval-Modi

```bash
# Systemtests ausführen
python automated_retrieval_test.py             # Vollständige Evaluierung
python optimized_retrieval_test.py --concurrent # Alle Modi parallel
python quick_hybrid_context_test.py --timeout 45 # Schnelle Validierung
```

### Testausführung

#### Quick Start Testing

```bash
# Alle Tests ausführen (empfohlen)
./run_tests.sh test              # 13/13 Tests in 0.02s ✅

# Mit Code-Qualitätsprüfungen
./run_tests.sh all               # Tests + Linting + Security

# Code automatisch formatieren
./run_tests.sh format-fix        # Black + isort

# Pre-commit hooks einrichten
./run_tests.sh pre-commit        # Automatische Qualitätsprüfung

# Setup validieren
./run_tests.sh validate          # Konfiguration prüfen
```

## Teststandards

### Testabdeckung
- **Mindestanforderung**: 75% Testabdeckung für neue Module
- **Ziel**: 100% Abdeckung für kritische Komponenten
- **Messung**: pytest-cov für Abdeckungsmessung und -berichte

```bash
# Testabdeckung messen
python -m pytest --cov=. tests/
```

### Test-Design-Prinzipien
- **Isolation**: Tests sollten unabhängig voneinander sein
- **Wiederholbarkeit**: Tests sollten konsistente Ergebnisse liefern
- **Lesbarkeit**: Testcode sollte klar und verständlich sein
- **Schnelligkeit**: Tests sollten schnell ausgeführt werden können

### Mocking und Fixtures
- **Externe Abhängigkeiten**: Immer mocken oder mit Fixtures ersetzen
- **Datenbank**: Test-Fixtures für Datenbankzugriff verwenden
- **LLM-Aufrufe**: Mock-Antworten für OpenAI-API-Aufrufe verwenden

## Besondere Testkonfigurationen

### Retrieval-Modi-Tests
Für jeden Retrieval-Modus sollten folgende Tests durchgeführt werden:
1. **Enhanced**: Multi-stage RAG mit 9 Kontextdokumenten
2. **FAISS**: Vektorähnlichkeitssuche mit 4 Dokumenten
3. **None**: Direkte Generierung mit hybridem Kontext
4. **SQLCoder**: CPU-Fallback-Modus
5. **LangChain**: SQL Database Agent

```bash
# Alle Retrieval-Modi testen
python optimized_retrieval_test.py --modes enhanced,faiss,none,sqlcoder,langchain
```

### Test-Queries
Standardisierte Testabfragen für konsistente Evaluierung:
1. *"Wer wohnt in der Marienstr. 26, 45307 Essen"*
2. *"Wer wohnt in der Marienstraße 26"*
3. *"Wer wohnt in der Bäuminghausstr. 41, Essen"*
4. *"Zeige mir Bewohner mit ihren Adressdaten"*
5. *"Wie viele Wohnungen gibt es insgesamt?"*

## Continuous Integration

Das Projekt verwendet Pre-Commit-Hooks und sollte Tests vor jedem Commit ausführen:

```bash
# Pre-commit-Hooks einrichten (enthält Testausführung)
./run_tests.sh pre-commit
```

## Testfortschritt

- **Aktuelle Tests**: 13/13 Tests bestanden (0.02s Ausführungszeit)
- **Gesamtstatus**: ✅ Alle Tests bestanden
- **Nächste Schritte**: Tests für TAG-Modell-Implementierung hinzufügen

---

Für weitere Informationen zu Code-Qualität und Entwicklungsrichtlinien siehe:
- [code-quality.md](code-quality.md)
- [development-guidelines.md](development-guidelines.md)