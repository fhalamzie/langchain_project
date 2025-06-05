# WINCASA High-Level Design

Diese Dokumentation beschreibt die übergeordnete Systemarchitektur, Hauptkomponenten und deren Interaktionen im WINCASA-Projekt.

## Systemarchitektur

WINCASA ist ein intelligentes Datenbank-Abfrage-System, das natürliche Sprache verwendet, um komplexe SQL-Abfragen für Firebird-Datenbanken zu generieren. Das System kombiniert moderne LLM-Technologie (GPT-4) mit direkter Datenbankanbindung und erweiterten RAG-Verfahren (Retrieval Augmented Generation).

### Architekturübersicht

```
                      +-------------------+
                      |  Streamlit UI     |
                      | (enhanced_qa_ui)  |
                      +--------+----------+
                               |
                               v
+------------------+  +--------+----------+  +-------------------+
| Phoenix          |  | SQL Agent Core    |  | Retrieval System  |
| Monitoring       |<-| (firebird_sql_    |->| (enhanced_        |
| (OTEL + SQLite)  |  |  agent_direct)    |  |  retrievers)      |
+------------------+  +--------+----------+  +-------------------+
                               |                       ^
                               v                       |
+------------------+  +--------+----------+  +-------------------+
| Database         |  | FDB Interface     |  | Knowledge Base    |
| (WINCASA2022.FDB)|<-| (fdb_direct_      |  | (YAML Documents,  |
| (151 tables)     |  |  interface)        |  |  Business Glossar)|
+------------------+  +-------------------+  +-------------------+
```

## Hauptkomponenten

### 1. SQL-Agent (Core)

**Datei:** [`firebird_sql_agent_direct.py`](firebird_sql_agent_direct.py)

Der SQL-Agent ist die zentrale Komponente, die natürlichsprachige Abfragen in SQL-Statements umwandelt. Er orchestriert den gesamten Prozess:

- Empfängt natürlichsprachige Abfragen
- Koordiniert den Retrieval-Prozess für Kontextinformationen
- Kommuniziert mit dem LLM für SQL-Generierung
- Validiert generierte SQL-Anweisungen
- Führt SQL über die Datenbankschnittstelle aus
- Formatiert Ergebnisse für die Endbenutzer

Der Agent unterstützt fünf verschiedene Retrieval-Modi:
- **Enhanced**: Multi-stage RAG mit kategorisierten Kontext (9 Dokumente)
- **FAISS**: Vektorähnlichkeitssuche (4 Dokumente)
- **None**: Direkte Generierung mit hybridem Kontext
- **SQLCoder**: Spezialisiertes SQL-Modell (CPU-Fallback)
- **LangChain**: SQL Database Agent Integration

### 2. Datenbank-Schnittstelle

**Datei:** [`fdb_direct_interface.py`](fdb_direct_interface.py)

Diese Komponente bietet eine direkte, optimierte Schnittstelle zur Firebird-Datenbank:

- Implementiert Verbindungspooling für verbesserte Leistung
- Enthält Retry-Logik für robuste Datenbankoperationen
- Umgeht SQLAlchemy-Probleme durch direkte FDB-Nutzung
- Verarbeitet Firebird-spezifische SQL-Dialekt-Anforderungen
- Überwacht Datenbankverbindungen und -leistung

### 3. Retrieval-System

**Datei:** [`enhanced_retrievers.py`](enhanced_retrievers.py)

Das RAG-System (Retrieval Augmented Generation) ist verantwortlich für:

- Auswahl relevanter Kontextdokumente basierend auf Benutzerabfragen
- Management der FAISS-Vektorindizes für Ähnlichkeitssuche
- Implementierung mehrstufiger Abrufstrategien
- Integration mit dem Business-Glossar für domänenspezifischen Kontext
- Dynamische Kombination verschiedener Kontextquellen

### 4. Business-Glossar

**Datei:** [`business_glossar.py`](business_glossar.py)

Domänenspezifisches Wissensmodul:

- Mapping von 25+ WINCASA-spezifischen Geschäftsbegriffen auf Datenbankentitäten
- JOIN-Reasoning-Engine für komplexe Tabellenbeziehungen
- Geschäftslogik-Übersetzung für natürlichsprachige Abfragen
- Bereitstellung von Domain-Kontext für den SQL-Agent

### 5. FK-Graph-Analyzer

**Datei:** [`fk_graph_analyzer.py`](fk_graph_analyzer.py)

Analysiert Datenbankbeziehungen für intelligente JOIN-Strategien:

- NetworkX-basierte Graphanalyse der Datenbankstruktur
- Identifiziert optimale JOIN-Pfade zwischen Tabellen
- Unterstützt das Business-Glossar bei der JOIN-Logik
- Visualisiert Beziehungen für besseres Verständnis

### 6. Monitoring-System

**Datei:** [`phoenix_monitoring.py`](phoenix_monitoring.py)

AI Observability mit optimiertem lokalen Backend:

- OTEL-Instrumentierung für LLM-Aufrufe und SQL-Ausführung
- SQLite-Backend für verbesserte Leistung (400% schneller)
- Real-time-Dashboards auf http://localhost:6006
- Kostentracking für API-Aufrufe
- Leistungsmetriken für alle Retrieval-Modi

### 7. Streamlit UI

**Datei:** [`enhanced_qa_ui.py`](enhanced_qa_ui.py)

Benutzerfreundliche Weboberfläche für das System:

- Einfache Textabfrageschnittstelle
- Anzeige von SQL-Abfragen und Ergebnissen
- Modus-Auswahl für verschiedene Retrieval-Strategien
- Verbindungsstatus und Systemdiagnostik
- Formatierte Ergebnisdarstellung

## Kontextstrategie

Das WINCASA-System implementiert eine hybride Kontextstrategie, die statisches Basiswissen mit dynamischem Retrieval kombiniert:

### Strukturierter globaler Kontext

**Datei:** [`global_context.py`](global_context.py)

- Kernentitäten: BEWOHNER, EIGENTUEMER, OBJEKTE, KONTEN
- Kritische Beziehungen: ONR-basierte Verbindungen und JOIN-Pfade
- Query-Patterns: Adresssuche, Finanzabfragen, Eigentümer-Zuordnungen
- Optimierte Versionen: Kompakt (671 Zeichen) & vollständig (2819 Zeichen)

### Dynamischer Retrieval-Kontext

- 248 YAML-Dokumente für detaillierte Tabellen- und Spalteninformationen
- Geschäftsbegriffe und Domänenkontext aus dem Business-Glossar
- Datenpatterns aus echten Datenbankeinträgen für realistischen Kontext

## Datenbank-Konfiguration

- **Datenbankdatei:** `WINCASA2022.FDB`
- **Tabellen:** 151 Benutzertabellen
- **Daten:** 517 Wohnungen, 698 Bewohner
- **Zugriffsmodi:**
  - Direkter Dateienzugriff über FDB für Enhanced/FAISS/None-Modi
  - Firebird-Server auf Port 3050 für LangChain-Modus

## Technologiestack

### Kernkomponenten
- **Backend:** Python 3.8+
- **Datenbank:** Firebird (FDB-Direktzugriff)
- **LLM-Integration:** OpenAI GPT-4, OpenRouter-APIs
- **UI:** Streamlit
- **Vektorisierung:** FAISS (CPU-Version)
- **Monitoring:** Arize Phoenix mit OTEL

### Abhängigkeiten
- **Kernanforderungen:** langchain, streamlit, faiss-cpu, fdb, PyYAML, networkx
- **SQL-LLM:** transformers, torch, sqlalchemy (für SQLCoder-2)
- **Monitoring:** arize-phoenix, arize-phoenix-otel
- **Instrumentation:** openinference-instrumentation-langchain, openinference-instrumentation-openai

## Aktuelle Entwicklungsprioritäten

Das WINCASA-System ist funktional vollständig und produktionsbereit. Die aktuelle Hauptpriorität ist die Implementierung des TAG-Modells (Synthesis-Execution-Generation) zur Verbesserung der SQL-Generierungsgenauigkeit:

### TAG-Modell-Architektur

Das TAG-Modell besteht aus drei Hauptkomponenten:

1. **SYN (Synthesis)**
   - Klassifizierung des Abfragetyps
   - Zielgerichteter Schema-Kontext
   - Fokussierte SQL-Generierung

2. **EXEC (Execution)**
   - Nutzung der bestehenden FDB-Schnittstelle

3. **GEN (Generation)**
   - Formatierung natürlichsprachiger Antworten mit Geschäftskontext

Die geplante TAG-Implementierung wird als sechster Retrieval-Modus hinzugefügt und soll die SQL-Generierungsgenauigkeit von etwa 20% auf über 90% verbessern.

## Zukunftsausrichtung

Nach Abschluss der TAG-Implementierung sind folgende Erweiterungen geplant:

1. **Unified Embedding Architecture**
   - Konsolidierung aller Embedding-Systeme
   - Zentrales Embedding-System für alle Retrieval-Modi
   - Verbesserte Leistung und Konsistenz

2. **Performance-Optimierungen**
   - Caching-Strategien
   - Parallele Verarbeitung
   - Weitere SQLite-Backend-Optimierungen

3. **Erweiterte Abfrageunterstützung**
   - Komplexe Geschäftsszenarien
   - Erweiterte Aggregations- und Analysefunktionen
   - Mehrschrittiges Reasoning

4. **Verbesserte Benutzeroberfläche**
   - Abfragevorschläge
   - Erweiterte Visualisierungen
   - Mehr Benutzerinteraktionsmöglichkeiten

## Referenzen auf andere Module

Neue Dokumente oder Module, die erstellt werden, müssen hier referenziert und erklärt werden.

---

Für detaillierte Implementierungsaufgaben und Fortschritte, siehe [tasks.md](tasks.md).