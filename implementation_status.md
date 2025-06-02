# Implementierungsstatus: Langchain SQL Agent mit parallelen RAG-Ansätzen

Dieses Dokument verfolgt den Fortschritt der Implementierung des Langchain SQL Agents mit FAISS- und Neo4j-basierten RAG-Ansätzen.

## Gesamtfortschritt

-   [ ] **Phase 1: FAISS RAG-Pfad**
    -   [x] Basis-Struktur des `FirebirdDocumentedSQLAgent` und der Retriever-Komponenten (`retrievers.py`, `firebird_sql_agent.py`)
    -   [x] `BaseDocumentationRetriever`-Schnittstelle definiert
    -   [x] `_load_and_parse_documentation`-Methode in `FirebirdDocumentedSQLAgent` implementiert
    -   [x] `FaissDocumentationRetriever`-Klasse implementiert
    -   [x] `_initialize_components` in `FirebirdDocumentedSQLAgent` für FAISS-Modus implementiert (inkl. API-Key-Logik für OpenRouter/OpenAI)
    -   [x] `_setup_sql_agent` in `FirebirdDocumentedSQLAgent` implementiert (inkl. dynamischer Tabellenerstellung für SQLite-Tests)
    -   [x] `query`-Methode in `FirebirdDocumentedSQLAgent` für FAISS-Pfad implementiert
    -   [x] `_generate_textual_responses`-Methode in `FirebirdDocumentedSQLAgent` implementiert
    -   [x] Grundlegender End-to-End-Test im `if __name__ == '__main__':`-Block von `firebird_sql_agent.py` für FAISS-Pfad erstellt und Fehler analysiert.
    -   [x] Debugging: SQL Agent findet `TestTable` in SQLite In-Memory DB nicht, obwohl sie erstellt wurde. **Gelöst durch Verwendung einer persistenten `sqlite3.Connection` und eines darauf basierenden SQLAlchemy `Engine` für den In-Memory-Testfall.**
    -   [x] Unit-Tests für `FirebirdDocumentedSQLAgent` und `FaissDocumentationRetriever` erstellen/vervollständigen (`test_firebird_sql_agent.py`, `test_retrievers.py`)
    -   [x] Implementierung der Extraktion der tatsächlichen SQL-Query aus dem Agenten (z.B. via Callbacks)
    -   [ ] **Integration in die Streamlit UI ([`enhanced_qa_ui.py`](enhanced_qa_ui.py)) - Blockiert durch Datenbankverbindungsproblem**
        -   [x] Grundlegende UI-Anpassungen für den Agenten-Workflow vorgenommen.
        -   [x] `KeyError: 'natural_language_query'` in der UI-Anzeige behoben.
        -   [x] FAISS Token Limit durch Kürzung der Dokumenteninhalte in `_load_and_parse_documentation` auf `MAX_DOC_CONTENT_LENGTH = 1500` behoben.
        -   [ ] **Blockierendes Problem:** Der `FirebirdDocumentedSQLAgent` kann aufgrund des Fehlers `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:firebird.fdb` nicht initialisiert werden.
            -   **Untersuchte Ursachen/Versuche (bisher ohne Erfolg für dieses spezifische Problem):**
                -   Installation des `fdb`-Pakets überprüft und erzwungen neu installiert.
                -   `LD_LIBRARY_PATH` gesetzt, um auf `./lib` mit `libfbclient.so` zu verweisen.
                -   `FIREBIRD_LIBRARY_PATH` im Python-Code gesetzt, um auf `lib/libfbclient.so` zu verweisen.
                -   Zusätzliche Firebird-Umgebungsvariablen (z.B. `FIREBIRD_TMP`, `FB_HOME`) aus funktionierenden Skripten übernommen.
                -   Verwendung einer benutzerdefinierten `creator`-Funktion für `create_engine` in SQLAlchemy, die `fdb.connect()` direkt aufruft.
                -   Konflikt mit dem Paket `firebird-driver` durch Deinstallation gelöst.
                -   Inkonsistenzen mit `python-dateutil` durch Neuinstallation behoben.
                -   Frühzeitiger Import von `import fdb` in `firebird_sql_agent.py`.
            -   **Nächste Schritte für dieses Problem:** Tiefere Analyse der SQLAlchemy-Dialektregistrierung, alternative Ansätze zur Datenbankanbindung für den Agenten oder Überprüfung der Python-/Systemumgebung auf spezifische Konfigurationsprobleme, die das Laden des `fdb`-Plugins durch SQLAlchemy verhindern.

-   [ ] **Phase 2: Neo4j RAG-Pfad**
    -   [ ] Neo4j-Datenimport-Logik (`neo4j_importer.py` oder Teil von `Neo4jDocumentationRetriever`)
    -   [ ] `Neo4jDocumentationRetriever`-Klasse implementieren
    -   [ ] `_initialize_components` in `FirebirdDocumentedSQLAgent` für Neo4j-Modus erweitern
    -   [ ] `query`-Methode in `FirebirdDocumentedSQLAgent` für Neo4j-Pfad erweitern/testen
    -   [ ] Unit-Tests für Neo4j-Komponenten
-   [ ] **Phase 3: Vergleich und Evaluierung**
    -   [ ] Auswahlmechanismus für RAG-Modus in UI implementieren
    -   [ ] Systematische vergleichende Tests durchführen
    -   [ ] Ergebnisse analysieren und dokumentieren
-   [ ] **Phase 4: Finale Integration und Verfeinerung**
    -   [ ] Code-Refactoring und Optimierungen
    -   [ ] Fehlerbehandlung verbessern
    -   [ ] Dokumentation aktualisieren (README, etc.)

## Nächste unmittelbare Aufgaben

1.  ~~**Debugging des SQL Agenten:** Sicherstellen, dass der Agent die dynamisch erstellte `TestTable` in der SQLite In-Memory-Datenbank erkennt. Möglicher Ansatz: `db.refresh_schema()` verwenden.~~ **ERLEDIGT**
2.  ~~Analyse der doppelten "Loaded 4 documents"-Ausgabe.~~ **ERLEDIGT**
3.  ~~Vervollständigung der Unit-Tests für den FAISS-Pfad in `test_firebird_sql_agent.py`.~~ **ERLEDIGT**
4.  ~~Implementierung der Extraktion der tatsächlichen SQL-Query.~~ **ERLEDIGT**