# WINCASA - Datenbank-Dokumentationsgenerator & Abfrage-Tool

## Projektübersicht

Dieses Projekt ist ein umfassendes Tool zur automatisierten Dokumentation und intelligenten Abfrage einer Firebird-Datenbank (WINCASA2022.FDB). Es kombiniert traditionelle Datenbanktechnologien mit modernen LLM-basierten (Large Language Model) Methoden, um eine intuitive, natürlichsprachige Interaktion mit komplexen Datenbankstrukturen zu ermöglichen.
Das System integriert zwei parallele RAG-Ansätze (FAISS und Neo4j) für erweiterte Kontextualisierung und höhere Abfragegenauigkeit. Der detaillierte Implementierungsplan ist unter [`plan.md`](plan.md) und der aktuelle Fortschritt unter [`implementation_status.md`](implementation_status.md) zu finden.

## Hauptfunktionen

Das System bietet folgende Kernfunktionalitäten:

1. **Automatisierte Dokumentation der Datenbankstruktur**
   - Extraktion von Tabellen, Spalten, Beziehungen und Geschäftsregeln
   - Generierung von Markdown- und YAML-Dokumentation
   - Optimierung bestehender Dokumentation mit Kontextinformationen

2. **Natürlichsprachige Datenbankabfragen**
   - Umwandlung natürlicher Sprache in SQL-Abfragen
   - Intelligente Kontextauswahl relevanter Tabellen
   - Präsentation der Ergebnisse in benutzerfreundlichem Format

3. **Streamlit-basierte Benutzeroberfläche**
   - Interaktive UI für alle Systemfunktionen
   - Unterschiedliche Tabs für verschiedene Anwendungsfälle
   - Feedback-Mechanismen zur kontinuierlichen Verbesserung

4. **Sicherheitsfeatures**
   - Validierung von SQL-Abfragen
   - Beschränkung auf SELECT-Operationen
   - Timeout- und Ressourcenbegrenzungen

5. **Caching und Protokollierung**
   - Caching von Abfrageergebnissen für bessere Performance
   - Ausführliche Protokollierung für Audit und Optimierung
   - Speicherung von Benutzer-Feedback

## Systemarchitektur

Das System ist modular aufgebaut und besteht aus folgenden Hauptkomponenten:

### 1. Datenbankzugriff

- **query_router.py**: Zentrale Komponente für den Datenbankzugriff
  - Verbindungsaufbau zur Firebird-Datenbank
  - Dynamische Suche nach der Firebird-Client-Library
  - Fehlerbehandlung und Logging

- **db_executor.py**: Sichere Ausführung von SQL-Abfragen
  - Validierung von SQL-Anfragen (nur SELECT erlaubt)
  - Caching-Mechanismus für Abfrageergebnisse
  - Timeout-Handling und Ressourcenbegrenzung
  - Konvertierung von Kodierungen (WIN1252 zu UTF-8)

### 2. LLM-Integration

- **llm_interface.py**: Schnittstelle zu OpenAI-API
  - Initialisierung von ChatOpenAI mit GPT-4
  - Generierung von SQL aus natürlichsprachigen Anfragen
  - Verarbeitung von Schema-Kontext

- **qa_enhancer.py**: Erweiterte Q&A-Funktionalität
  - Semantische Suche nach relevanten Tabellen
  - Kontextoptimierung für LLM-Anfragen
  - Natürlichsprachige Aufbereitung von Abfrageergebnissen
  - Feedback-Speicherung und kontinuierliche Verbesserung

### 3. Benutzeroberfläche

- **streamlit_integration.py**: Hauptanwendung
  - Integration aller Komponenten in einer einheitlichen UI
  - Tab-basierte Navigation für verschiedene Funktionalitäten
  - Dynamisches Laden von Modulen

- **enhanced_qa_ui.py**: UI für natürlichsprachige Abfragen
  - Eingabeformular für Benutzeranfragen
  - Anzeige von SQL, Tabellen und Ergebnissen
  - Feedback-Mechanismen (Bewertung von Antworten)

### 4. Unterstützende Komponenten

- **query_memory.py**: Speicherung von Abfragehistorie
  - Protokollierung erfolgreicher und fehlgeschlagener Abfragen
  - Speicherung manueller Korrekturen

- **query_logger.py**: Detaillierte Protokollierung
  - Speicherung von Anfragen, SQL, Ergebnissen
  - Zeitstempel und Erfolgsmetriken

### 5. Datenstrukturen

Das Projekt organisiert generierte Daten in strukturierten Verzeichnissen:

- **/output/schema/**: Enthält detaillierte Dokumentation zur Datenbankstruktur:
    - `index.md`: Ein Gesamtinhaltsverzeichnis aller Tabellen und Prozeduren.
    - `relation_report.md`: Ein Bericht über die Beziehungen zwischen den Tabellen, inklusive einer Liste der am stärksten verbundenen Tabellen.
    - `table_diagrams.md`: Links zu einzelnen Diagrammen, die die direkten Beziehungen jeder Tabelle visualisieren.
    - `table_clusters.md`: Eine Analyse, die Tabellen basierend auf ihren Beziehungen in Cluster gruppiert. Dies hilft, funktionale Module innerhalb der Datenbank zu identifizieren.
    - Individuelle Markdown-Dateien für jede Tabelle (z.B., `KONTEN.md`, `OBJEKTE.md`), die Spalten, Datentypen, Beschreibungen und Beziehungen detailliert beschreiben.
- **/output/yamls/**: YAML-Repräsentationen von Datenbankobjekten (Tabellen und Prozeduren), die für die programmatische Verarbeitung des Schemas genutzt werden.
- **/output/logs/**: Protokolldateien und Statusberichte, z.B. `llm_prompts.log`.
- **/output/memory/**: Verlauf von Benutzeranfragen und deren Ergebnisse.
- **/output/feedback/**: Gesammeltes Benutzerfeedback zur Systemperformance.
- **/output/cache/**: Zwischengespeicherte Abfrageergebnisse zur Performanceoptimierung.

## Ablauf einer Benutzeranfrage

Der typische Ablauf einer natürlichsprachigen Datenbankabfrage wird derzeit überarbeitet, um einen Langchain SQL Agent zu nutzen. Der geplante Ablauf ist in [`plan.md`](plan.md) dokumentiert und beinhaltet die Nutzung von RAG (Retrieval Augmented Generation) zur Anreicherung des Kontexts für den Agenten. Der bisherige Ablauf umfasste:

1.  Eingabe der Benutzeranfrage über die Streamlit-UI
2.  Identifikation relevanter Tabellen durch semantische Ähnlichkeitssuche (TF-IDF)
3.  Erstellung eines Tabellenkontexts
4.  Generierung einer SQL-Abfrage durch das LLM
5.  Validierung und Ausführung der SQL-Abfrage
6.  Verarbeitung und Formatierung der Ergebnisse
7.  Generierung einer natürlichsprachigen Antwort durch das LLM
8.  Präsentation der Ergebnisse und Antwort in der UI
9.  Protokollierung und optionales Feedback

## Installation und Einrichtung

### Voraussetzungen

- Python 3.8+
- Firebird-Datenbank (WINCASA2022.FDB)
- OpenAI API-Schlüssel

### Installation

1. Repository klonen
2. Virtuelle Umgebung erstellen und aktivieren:
   ```
   python3 -m venv .venv
   source .venv/bin/activate  # Unter Linux/macOS
   # oder
   .venv\Scripts\activate     # Unter Windows
   ```
3. Abhängigkeiten installieren:
   ```
   pip install langchain langchain-community langchain-openai streamlit pandas numpy scikit-learn fdb faiss-cpu neo4j neo4j-graphrag tiktoken PyYAML python-dotenv
   ```
4. OpenAI API-Schlüssel in `/home/envs/openai.env` hinterlegen:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Stellen Sie sicher, dass die Firebird-Client-Bibliothek verfügbar ist. Sie kann unter `./lib/libfbclient.so` platziert werden.

### Verzeichnisstruktur vorbereiten

```
mkdir -p output/schema output/yamls output/logs output/memory output/feedback output/cache fb_temp
```

### Wichtiger Hinweis zur Ausführung

Alle Skripte müssen innerhalb der aktivierten virtuellen Umgebung ausgeführt werden. Vor der Ausführung immer sicherstellen, dass die Umgebung aktiviert ist:

```
source .venv/bin/activate  # Unter Linux/macOS
# oder
.venv\Scripts\activate     # Unter Windows
```

## Ausführung

Das System bietet verschiedene Einstiegspunkte:

### Streamlit-Anwendung starten:

```
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Anwendung starten
streamlit run streamlit_integration.py
```

### Kommandozeilen-Query ausführen:

```
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Query ausführen
python run_llm_query.py
```

### Erweiterte Q&A-Benutzeroberfläche (Direkte FDB-Schnittstelle):

```
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# UI mit direkter FDB-Schnittstelle starten
streamlit run enhanced_qa_ui.py

# Oder mit dem neuen Startskript:
./start_enhanced_qa_direct.sh

### Neo4j-Integration

Für die Nutzung des Neo4j RAG-Pfads:
1. Neo4j-Instanz starten:
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j
```
2. Dokumentation importieren:
```python
from neo4j_importer import Neo4jImporter

importer = Neo4jImporter("bolt://localhost:7687", "neo4j", "password", "doc_index")
importer.create_index()
importer.import_documents(docs)  # docs aus _load_and_parse_documentation
```
```

**🎉 Neue Features der direkten FDB-Schnittstelle:**
- Umgeht SQLAlchemy-Sperrprobleme (SQLCODE -902)
- Automatisches Server/Embedded-Fallback
- Custom Langchain Tools für FDB-Operationen
- Verbesserte Fehlerbehandlung und Performance
- Detaillierte Agent-Schritte in der UI

### Lizenzinformationen prüfen:

```
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Lizenzprüfung starten
python check_license.py
```

## Skripte und Hilfsprogramme

- **check_imports.py**: Überprüfung von Abhängigkeiten
- **debug_env.py**: Debugging der Umgebungsvariablen
- **extract_from_firebird.py**: Extraktion von Daten aus der Firebird-DB
- **export_schema.py**: Export des Datenbankschemas
- **start_enhanced_qa.sh**: Startskript für die erweiterte Q&A-UI
- **start_streamlit.sh**: Startskript für die Streamlit-Anwendung

## Technischer Hintergrund

### LLM-Integration

Das System verwendet ChatOpenAI (GPT-4) für zwei Hauptzwecke:
1. **SQL-Generierung**: Umwandlung natürlichsprachiger Anfragen in SQL mit Berücksichtigung des Datenbankschemas
2. **Antwortgenerierung**: Aufbereitung von Abfrageergebnissen in natürlichsprachige, benutzerfreundliche Antworten

Die LLMs werden mit unterschiedlichen Parametern konfiguriert:
- Für SQL-Generierung: Temperatur=0 (deterministische Antworten)
- Für Antwortgenerierung: Temperatur=0.3 (leicht kreative Antworten)

### Semantische Suche

Zur Identifikation relevanter Tabellen wird TF-IDF (Term Frequency-Inverse Document Frequency) mit Cosine-Similarity verwendet:
1. Tabellennamen, Beschreibungen und Spalteninformationen werden in einen Vektor umgewandelt
2. Die Benutzeranfrage wird ebenfalls vektorisiert
3. Tabellen mit der höchsten Ähnlichkeit zur Anfrage werden ausgewählt

### Sicherheitsmaßnahmen

- **SQL-Validierung**: Reguläre Ausdrücke prüfen auf gefährliche Operationen
- **Timeout-Begrenzung**: Abfragen werden nach 30 Sekunden abgebrochen
- **Ergebnisbegrenzung**: Maximal 1000 Zeilen werden zurückgegeben
- **Caching**: Ergebnisse werden zwischengespeichert, um wiederholte Abfragen zu beschleunigen

## Erweiterungsmöglichkeiten

Das System kann in folgenden Bereichen erweitert werden:

1. **Unterstützung weiterer Datenbanktypen** neben Firebird
2. **Implementierung von Benutzer-Authentifizierung und Berechtigungen**
3. **Erweiterte Analysen** der protokollierten Benutzerinteraktionen
4. **Integration mit Business Intelligence Tools**
5. **Optimierung der Kontextauswahl** für bessere SQL-Generierung
6. **Implementierung von Multi-Turn-Konversationen** für komplexere Abfragen

## Beispielabfragen

- "Welche Bewohner leben in der Marienstraße 26?"
- "Zeige mir alle Eigentümer in Berlin"
- "Wie viele Wohnungen gibt es pro Gebäude?"
- "Welche Bankverbindungen haben wir für Eigentümer?"

## Feedback und Verbesserung

Das System sammelt Benutzerfeedback zu generierten Antworten, um kontinuierlich zu lernen und sich zu verbessern. Benutzer können Antworten mit den Optionen "Sehr gut", "Gut", "Ungenau" oder "Falsch" bewerten.

## Zusammenfassung

Das WINCASA-Projekt demonstriert die erfolgreiche Integration von traditionellen Datenbanktechnologien mit modernen LLM-Ansätzen. Es ermöglicht Benutzern, komplexe Datenbankabfragen in natürlicher Sprache zu formulieren und verständliche Antworten zu erhalten, ohne SQL-Kenntnisse zu benötigen. Durch die Kombination von automatisierter Dokumentation, semantischer Suche und natürlichsprachiger Interaktion bietet es einen innovativen Ansatz für den Zugriff auf strukturierte Daten.

## Entwicklungsstand und Roadmap

Das Projekt durchläuft einen kontinuierlichen Verbesserungsprozess. Die aktuelle Roadmap und der detaillierte Implementierungsplan für den Langchain SQL Agent sind in [`plan.md`](plan.md) und der Fortschritt in [`implementation_status.md`](implementation_status.md) dokumentiert. Die ursprüngliche Roadmap umfasste:

### Ursprüngliche Herausforderungen

1. **Optimierung der Kontextauswahl**: Verbesserung der Relevanz von Tabellen für Anfragen
2. **SQL-Validierung und Sicherheit**: Implementierung robuster Sicherheitsmechanismen
3. **Ergebnisaufbereitung**: Strukturierung und Formatierung von Abfrageergebnissen
4. **Feedback-System**: Implementierung von Benutzerfeedback zur Systemverbesserung

### Geplante Verbesserungen

Die Implementierung erfolgt in vier Sprints:

#### Sprint 1: Grundlagen
- SQL-Ausführungsmodul (bereits umgesetzt)
- Optimierte Kontextauswahl (bereits umgesetzt)

#### Sprint 2: Validierung und Ergebnisaufbereitung
- SQL-Validierung
- Ergebnis-Nachbearbeitung
- Natürlichsprachige Antwortgenerierung

#### Sprint 3: Feedback und UI
- Feedback-System
- Erweiterte UI-Komponenten

#### Sprint 4: Lernen und Integration
- Lernende Komponente
- Systemintegration

### Bekannte Risiken und Abhängigkeiten

- **LLM-Tokengrenze**: Die Menge an Kontext, die an das LLM übergeben werden kann, ist begrenzt
- **Sicherheitsbedenken**: Die Ausführung generierter SQL-Abfragen erfordert strenge Validierung
- **Qualität der Metadaten**: Die Effektivität des Systems hängt von der Qualität der vorhandenen Metadaten ab

### Erfolgsmetriken

Die Leistung des Systems wird anhand folgender Metriken gemessen:
1. **Antwortgenauigkeit**: Prozentsatz korrekter Antworten
2. **SQL-Erfolgsrate**: Prozentsatz erfolgreich generierter und ausgeführter SQL-Abfragen
3. **Benutzer-Zufriedenheit**: Gemessen durch das Feedback-System
4. **Abfrageperformance**: Durchschnittliche Zeit von Anfrage bis Antwort
5. **Kontextrelevanz**: Prozentsatz relevanter Tabellen im ausgewählten Kontext