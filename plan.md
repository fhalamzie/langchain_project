# Plan zur Implementierung eines Langchain SQL Agents mit parallelen RAG-Ansätzen (FAISS & Neo4j)

**Status:** Siehe [`implementation_status.md`](implementation_status.md) für den detaillierten Fortschritt.

**🎉 KRITISCHES UPDATE:** Das Hauptproblem mit SQLAlchemy-Sperrfehlern wurde durch die Implementierung einer direkten FDB-Schnittstelle gelöst!

Dieses Dokument beschreibt die geplanten Schritte zur Integration eines Langchain SQL Agents in das bestehende WINCASA-Datenbank-Dokumentationsgenerator & Abfrage-Tool. Ziel ist es, die Qualität der LLM-basierten Datenbankabfragen durch die Nutzung von zwei parallel entwickelten RAG-Ansätzen (FAISS-basierte Vektorsuche und Neo4j-basierte Graphsuche) zu verbessern und deren Effektivität zu vergleichen.

## 1. Technologie-Stack

### 🔄 Aktualisierte Architektur (Nach FDB-Lösung)

*   **Core Framework:** Langchain
    *   `create_react_agent` (für direkte FDB-Integration)
    *   Custom Tools (`FDBQueryTool`, `FDBSchemaInfoTool`, `FDBListTablesTool`)
    *   `BaseRetriever` (als Interface für unsere Retriever)
*   **Datenbankanbindung (SQL):**
    *   **Primär:** Direkte FDB-Schnittstelle (`fdb_direct_interface.py`)
    *   **Fallback:** SQLAlchemy für andere Datenbanken
*   **LLM:** OpenAI GPT-4 Modell (via OpenRouter oder direkt)
*   **RAG-Ansatz 1: Vektor-basiert**
    *   FAISS für den Vektorindex
    *   `OpenAIEmbeddings` für die Textvektorisierung
*   **RAG-Ansatz 2: Graph-basiert** (Optional)
    *   Neo4j als Graphdatenbank
    *   Langchain-Integrationen für Neo4j
*   **Programmiersprache:** Python
*   **Hilfsbibliotheken:** `PyYAML`, `fdb`, `faiss-cpu`

### 🏗️ Neue Architektur-Komponenten

#### FDBDirectInterface (`fdb_direct_interface.py`)
```python
class FDBDirectInterface:
    def get_table_names() -> List[str]
    def get_table_info(table_names: List[str]) -> str
    def run_sql(query: str) -> List[Tuple]
    def get_column_names(query: str) -> List[str]
```

#### FirebirdDirectSQLAgent (`firebird_sql_agent_direct.py`)
```python
class FirebirdDirectSQLAgent:
    def __init__(db_connection_string, llm, retrieval_mode='faiss')
    def query(natural_language_query: str) -> Dict[str, Any]
```

#### Custom Langchain Tools
- **FDBQueryTool**: Direkte SQL-Ausführung ohne SQLAlchemy
- **FDBSchemaInfoTool**: Schema-Informationen via direkter fdb-Verbindung
- **FDBListTablesTool**: Tabellenauflistung ohne Sperrprobleme

### 🔧 Ursprünglicher Stack (Referenz)
*   ~~`SQLDatabaseToolkit`~~ → Ersetzt durch Custom FDB Tools
*   ~~`SQLDatabase` (via SQLAlchemy)~~ → Ersetzt durch `FDBDirectInterface`

## 2. Kernänderungen und Implementierungsschritte

### 2.1. Entwicklung des `FirebirdDocumentedSQLAgent` und der Retriever-Komponenten

Um die RAG-Pfade klar zu trennen und die Modularität zu erhöhen, schlagen wir folgende Struktur vor:

**A. Basis-Retriever-Interface (Abstraktion)**

*   Wir definieren eine abstrakte Basisklasse (oder ein `Protocol`) für unsere Dokumentations-Retriever, z.B. `BaseDocumentationRetriever(BaseRetriever)`.
*   Diese Klasse spezifiziert eine Methode wie `get_relevant_documents(query: str) -> List[Document]`.

**B. FAISS Retriever (`FaissDocumentationRetriever(BaseDocumentationRetriever)`)**

*   **Initialisierung (`__init__`):**
    *   Nimmt geparste Dokumentationsdaten entgegen.
    *   Erstellt Embeddings (`OpenAIEmbeddings`).
    *   Baut den FAISS-Index (`faiss_vectorstore`) auf.
    *   Initialisiert eine `RetrievalQA` Chain oder eine ähnliche Logik für das Retrieval.
*   **Implementierung von `get_relevant_documents`:** Führt die Abfrage gegen den FAISS-Index aus.

**C. Neo4j Retriever (`Neo4jDocumentationRetriever(BaseDocumentationRetriever)`)**

*   **Initialisierung (`__init__`):**
    *   Nimmt geparste Dokumentationsdaten und Neo4j-Verbindungsparameter entgegen.
    *   Stellt die Verbindung zur Neo4j-Instanz her.
    *   **Datenimport-Logik:** Enthält oder ruft eine Methode auf, um die Dokumentationsdaten in das definierte Neo4j-Graphmodell zu importieren (dies könnte beim ersten Start oder bei Bedarf erfolgen).
    *   Initialisiert Langchain-Tools für Neo4j-Abfragen (z.B. `Neo4jGraph`).
*   **Implementierung von `get_relevant_documents`:** Formuliert und führt Cypher-Abfragen (oder andere Neo4j-spezifische Abfragen) aus, um relevante Dokumente/Knoten/Subgraphen zu finden.

**D. `FirebirdDocumentedSQLAgent` Klasse**

*   **Initialisierung (`__init__`):**
    *   Parameter `retrieval_mode: str` (z.B. 'faiss', 'neo4j').
    *   Firebird DB-Verbindungsparameter, LLM-Konfiguration.
    *   Lädt und parst die Dokumentationsdaten einmalig (zentrale Methode `_load_and_parse_documentation`).
    *   Initialisiert *beide* Retriever-Instanzen:
        *   `self.faiss_retriever = FaissDocumentationRetriever(parsed_docs, ...)`
        *   `self.neo4j_retriever = Neo4jDocumentationRetriever(parsed_docs, neo4j_config, ...)`
    *   Initialisiert den SQL-Agenten (`self.sql_agent = self._setup_sql_agent()`).

*   **Zentrale Dokumentationsladung (`_load_and_parse_documentation`):**
    *   **Datenquellen:** [`output/schema/*.md`](output/schema/), [`output/yamls/*.yaml`](output/yamls/), [`output/ddl/*.sql`](output/ddl/).
    *   Liest die Dateien ein und konvertiert sie in eine einheitliche, strukturierte Form (z.B. eine Liste von `Document`-Objekten oder Dictionaries), die von beiden Retrievern verwendet werden kann.

*   **SQL Agent Setup (`_setup_sql_agent`):**
    *   Erstellt `SQLDatabaseToolkit`.
    *   Definiert die System-Nachricht für den Agenten.
    *   Erstellt den `create_sql_agent`.

*   **Abfragemethode (`query(natural_language_query: str, retrieval_mode: Optional[str] = None)`):**
    1.  **Retriever-Auswahl:**
        *   Bestimmt den zu verwendenden Retriever. Falls `retrieval_mode` im Methodenaufruf übergeben wird, hat dieser Vorrang. Ansonsten wird der im Konstruktor gesetzte Modus verwendet.
        *   `current_retriever = self.faiss_retriever if selected_mode == 'faiss' else self.neo4j_retriever`
    2.  **Dokumentationsabruf:**
        *   `doc_context = current_retriever.get_relevant_documents(natural_language_query)`
    3.  **Erweiterte Anfrage an den SQL-Agenten:**
        *   Formuliert den Prompt für den `self.sql_agent` unter Einbeziehung von `doc_context`.
    4.  **Agentenausführung:**
        *   `agent_result = self.sql_agent.run(enhanced_query)` (liefert typischerweise die SQL und das Ergebnis).
    5.  **Generierung von drei Antwortvarianten (Text):**
        *   Ruft eine separate Methode `_generate_textual_responses(query, sql_generated, sql_result, doc_context)` auf.
        *   Diese Methode verwendet das LLM, um drei verschiedene natürlichsprachige Antworten zu formulieren.
        *   Gibt die generierte SQL und die drei Textvarianten zurück.

*   **Textantwort-Generierung (`_generate_textual_responses`):**
    *   Nimmt die notwendigen Informationen entgegen.
    *   Formuliert einen geeigneten Prompt für das LLM, um drei diverse und informative Antworten zu generieren.

Diese Struktur trennt die Verantwortlichkeiten klar: Die Retriever sind für die Beschaffung der Dokumentationskontexte zuständig, während der `FirebirdDocumentedSQLAgent` die Orchestrierung, die Interaktion mit dem SQL-Agenten und die finale Antwortgenerierung übernimmt.

### 2.2. Integration in das bestehende System
(Bleibt im Wesentlichen wie im vorherigen Plan, aber die Konfigurationsmöglichkeit für `retrieval_mode` wird wichtiger.)

### 2.3. Anpassungen an der Benutzeroberfläche ([`enhanced_qa_ui.py`](enhanced_qa_ui.py:73))
(Bleibt wie im vorherigen Plan.)

## 3. Zu modifizierende/erstellende Skripte
*   **Neu zu erstellen / Stark zu modifizieren:**
    *   `firebird_sql_agent.py` (oder ähnlich): Enthält die Klasse `FirebirdDocumentedSQLAgent`.
    *   `retrievers.py` (oder ähnlich): Enthält die Klassen `BaseDocumentationRetriever`, `FaissDocumentationRetriever`, `Neo4jDocumentationRetriever`.
    *   `neo4j_importer.py` (kann Teil von `Neo4jDocumentationRetriever` oder ein separates Modul sein): Logik zum Aufbau des Neo4j-Graphen.
*   Restliche Skripte wie im vorherigen Plan.

## 4. Installation und Setup

*   **Python-Pakete sicherstellen/installieren:**
    ```bash
    pip install langchain langchain-community langchain-openai streamlit pandas numpy scikit-learn fdb faiss-cpu neo4j tiktoken PyYAML python-dotenv
    # Ggf. faiss-gpu wenn eine GPU verfügbar ist und genutzt werden soll
    ```
*   **OpenAI API-Schlüssel:** Konfiguration in `/home/envs/openai.env` bleibt bestehen.
*   **Firebird-Client-Bibliothek:** Sicherstellen, dass `./lib/libfbclient.so` verfügbar ist.
*   **Firebird-Datenbank-Verbindungszeichenfolge:** Muss konfigurierbar sein (z.B. Umgebungsvariable oder Konfigurationsdatei).
*   **Neo4j-Setup:** Installation einer Neo4j-Instanz (z.B. Docker oder als Desktop-Anwendung). Konfiguration der Verbindungsdaten zur Neo4j-Instanz.


## 5. Meilensteine (Aktualisiert)

### ✅ **M1: Basis-Struktur und FAISS-Retriever** (ABGESCHLOSSEN)
*   [x] `FirebirdDocumentedSQLAgent`-Grundgerüst, `_load_and_parse_documentation` und `_setup_sql_agent` implementiert.
*   [x] `FaissDocumentationRetriever` implementiert und liefert Kontext.
*   [x] API-Key-Logik (OpenRouter/OpenAI) in `__init__` und `__main__` implementiert.
*   [x] Dynamische Tabellenerstellung für SQLite-Tests in `_setup_sql_agent` implementiert.
*   [x] End-to-End-Abfragen über den FAISS-Pfad (SQL + 3 Textvarianten) im `__main__`-Block von `firebird_sql_agent.py` vorbereitet und getestet.
*   [x] ~~Debugging: SQL Agent findet `TestTable` in SQLite In-Memory DB nicht zuverlässig~~ **GELÖST**
*   [x] Unit-Tests für FAISS-Pfad vervollständigt.
*   [x] SQL-Extraktion implementiert.

### ✅ **M1.5: Direkte FDB-Schnittstelle** (ABGESCHLOSSEN - KRITISCHE LÖSUNG)
*   [x] **Problem identifiziert:** SQLAlchemy-Sperrfehler (SQLCODE -902) mit Firebird Embedded
*   [x] **`FDBDirectInterface` implementiert** (`fdb_direct_interface.py`)
    *   [x] Direkte fdb-Treiber-Verbindung ohne SQLAlchemy
    *   [x] Methoden: `get_table_names()`, `get_table_info()`, `run_sql()`, `get_column_names()`
    *   [x] Server/Embedded-Fallback-Mechanismus
    *   [x] Korrekte Firebird-Datentyp-Behandlung
*   [x] **`FirebirdDirectSQLAgent` implementiert** (`firebird_sql_agent_direct.py`)
    *   [x] Custom Langchain Tools: `FDBQueryTool`, `FDBSchemaInfoTool`, `FDBListTablesTool`
    *   [x] ReAct Agent mit direkter FDB-Integration
    *   [x] Vollständige FAISS-Dokumentationsretrieval-Integration
*   [x] **Umfassende Tests** (`test_fdb_direct_interface.py`)
    *   [x] 151 Tabellen erfolgreich erkannt
    *   [x] BEWOHNER-Tabelle vollständig zugänglich
    *   [x] Keine SQLAlchemy-Sperrfehler mehr
*   [x] **Integration in bestehenden Agent** (`firebird_sql_agent.py`)

### 🔄 **M2: Neo4j-Datenimport und -Retriever** (Optional - Niedrigere Priorität)
*   [ ] Neo4j-Instanz läuft, Graphmodell definiert.
*   [ ] Datenimport-Logik für Neo4j funktioniert.
*   [ ] `Neo4jDocumentationRetriever` implementiert und liefert Kontext.

### 🔄 **M3: Integration Neo4j-Retriever und Auswahlmechanismus** (Optional)
*   [ ] Beide Retriever können im `FirebirdDocumentedSQLAgent` genutzt werden.
*   [ ] Auswahlmechanismus für `retrieval_mode` funktioniert.
*   [ ] End-to-End-Abfragen über den Neo4j-Pfad.

### ✅ **M4: UI-Anpassungen und Integration** (ABGESCHLOSSEN)
*   [x] Integration der direkten FDB-Schnittstelle in die Streamlit UI ([`enhanced_qa_ui.py`](enhanced_qa_ui.py))
*   [x] Auswahlmechanismus für RAG-Modus in UI implementieren
*   [x] Performance-Optimierung der direkten FDB-Verbindungen

### ✅ **M5: Erweiterte Tests** (ABGESCHLOSSEN am 03.06.2025)
*   [x] Komplexere SQL-Abfragen und Edge Cases
*   [x] Implementiert in test_fdb_direct_interface.py und test_enhanced_qa_ui_integration.py
*   [x] Abdeckung von JOINs, Aggregationen, Subqueries
*   [x] Natürlichsprachige Abfragen mit komplexen Szenarien
*   [x] Anpassung an reale Datenstruktur

### 📊 **M6: Vergleichende Tests und Evaluierung** (Zukünftig)
*   [ ] Systematische vergleichende Tests zwischen SQLAlchemy- und direktem FDB-Ansatz
*   [ ] Performance-Benchmarks
*   [ ] Ergebnisse analysieren und dokumentieren

## 🎯 Aktuelle Prioritäten

1. **Vergleichende Tests** - Systematische Evaluierung der Lösungsansätze
2. **Dokumentation** - Vollständige Dokumentation der neuen Architektur
3. **Neo4j-Integration** - Optionaler Graph-basierter Ansatz

## 6. MCP-Server
Nutze insbesondere für LangChain und Neo4j den MCP-Server context7

## 7. Unit-Tests
Schreibe Basis-Unit-Tests für alle Änderungen