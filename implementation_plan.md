# Implementierungsplan: Hybride Kontextstrategie

## 1. Zielsetzung

Verbesserung der Kontextqualität und -relevanz für den LLM-Agenten, um die Genauigkeit von Datenbankabfragen zu erhöhen und Fehler (z.B. Timeouts, falsche SQL-Generierung) zu reduzieren.

## 2. Problembeschreibung

Die aktuelle Kontextbereitstellung für den LLM-Agenten ist möglicherweise unzureichend oder nicht optimal priorisiert. Dies kann dazu führen, dass der Agent wichtige Informationen übersieht oder von weniger relevanten Details abgelenkt wird, was die Performanz und Genauigkeit beeinträchtigt.

## 3. Vorgeschlagene Lösung: Hybride Kontextstrategie

Die hybride Kontextstrategie kombiniert einen direkten, globalen Basiskontext mit einem dynamischen, embedding-basierten Retrieval-Mechanismus.

### 3.1. Direkter Globaler Basiskontext

*   **Beschreibung:** Essentielle, hoch-priorisierte Informationen, die jeder LLM-Anfrage direkt als Teil des Prompts mitgegeben werden.
*   **Zweck:** Sicherstellung, dass der LLM immer über ein grundlegendes Verständnis der Datenbankstruktur, der Kernentitäten und der wichtigsten Geschäftsregeln verfügt.
*   **Inhalte (Beispiele, müssen verfeinert werden):**
    *   **Kern-Schema-Informationen:** Wichtigste Tabellen, kritische Spalten und deren Datentypen.
    *   **Kernentitäten und Hauptbeziehungen:** Definition der zentralen Geschäftsobjekte (z.B. Bewohner, Wohnungen, Verträge) und deren primäre Verknüpfungen.
    *   **Top-Level Geschäftsregeln:** Kritische operative Logik oder häufig benötigte Definitionen.
    *   **Abgeleitet aus Dokumenten wie:**
        *   `docs/index.md` (Projektübersicht)
        *   `output/schema/index.md` (Schema-Übersicht)
        *   `output/schema/db_overview.md` (Datenbank-Übersicht)
        *   Auszüge aus `output/schema/relation_report.md` (wichtigste Beziehungen)
        *   Auszüge aus `output/schema/table_clusters.md` (Tabellengruppierungen)
*   **Implementierungsansatz:**
    *   Identifikation und Extraktion der relevantesten Informationen aus den genannten Quelldokumenten.
    *   Erstellung einer kompakten, präzisen Zusammenfassung dieser Informationen.
    *   Integration dieser Zusammenfassung in die Prompt-Generierung für den LLM-Agenten.

### 3.2. Embedding-basiertes Dynamisches Retrieval

*   **Beschreibung:** Nutzung der bestehenden RAG-Mechanismen (z.B. FAISS, "Enhanced Mode") für detailliertere oder spezifischere Informationen, die dynamisch basierend auf der Nutzeranfrage abgerufen werden.
*   **Zweck:** Ermöglicht den Zugriff auf eine umfangreiche Wissensbasis, ohne das Kontextfenster des LLM bei jeder Anfrage zu überlasten.
*   **Inhalte (Beispiele):**
    *   Detaillierte Tabellenbeschreibungen und Spaltendefinitionen.
    *   Vollständige Beziehungsdetails zwischen allen Tabellen.
    *   Spezifische Geschäftslogik, Fallbeispiele, komplexe Abfragemuster.
    *   Inhalte aus `output/compiled_knowledge_base.json` und detaillierten YAML-Dateien (`output/yamls/`).
*   **Implementierungsansatz:**
    *   Weiterentwicklung und Optimierung der bestehenden Retrieval-Methoden.
    *   Sicherstellung, dass die Retrieval-Ergebnisse gut mit dem globalen Basiskontext harmonieren.

## 4. Implementierungsschritte

1.  **Analyse und Auswahl des globalen Basiskontexts:**
    *   Sichtung der relevanten Dokumente (`docs/index.md`, `output/schema/*` etc.).
    *   Definition der Kriterien für "essentielle" Informationen.
    *   Erstellung eines ersten Entwurfs des globalen Basiskontexts (max. Token-Anzahl festlegen).
2.  **Integration des Basiskontexts in den Prompt:**
    *   Anpassung der Prompt-Engineering-Logik in `firebird_sql_agent_direct.py` oder verwandten Modulen.
    *   Strategie zur Platzierung des Basiskontexts im Prompt (z.B. vor dem Schema, nach der User-Frage).
3.  **Anpassung der Retrieval-Modi:**
    *   Überprüfung, wie die bestehenden Modi (`enhanced`, `faiss`, `none`) mit dem neuen Basiskontext interagieren.
    *   Der Modus "none" könnte zu einem "base_context_only"-Modus werden.
    *   Sicherstellen, dass dynamisch abgerufener Kontext den Basiskontext ergänzt und nicht redundant ist.
4.  **Überarbeitung der Wissensbasis-Dokumente (optional):**
    *   Prüfung, ob einige Dokumente für die Nutzung im direkten oder abgerufenen Kontext neu strukturiert werden müssen.
5.  **Testing und Evaluierung:**
    *   Durchführung von Tests mit `automated_retrieval_test.py` unter Verwendung der neuen Kontextstrategie.
    *   Vergleich der Ergebnisse (Genauigkeit, Timeouts, SQL-Qualität) mit der bisherigen Methode.
    *   Analyse der LLM-Traces (Phoenix) zur Bewertung der Kontextnutzung.
6.  **Dokumentation:**
    *   Aktualisierung von `README.md` und `CLAUDE.md` mit der Beschreibung der neuen Strategie.

## 5. Zu erwartende Ergebnisse

*   Verbesserte Genauigkeit der generierten SQL-Abfragen.
*   Reduktion von Timeouts durch relevanteren und präziseren Kontext.
*   Besseres Verständnis komplexer Anfragen durch den LLM.
*   Konsistentere Performance über verschiedene Abfragetypen hinweg.

## 6. Risiken und Herausforderungen

*   **Balance finden:** Der globale Basiskontext darf nicht zu umfangreich werden, um das Kontextfenster nicht unnötig zu füllen.
*   **Redundanz vermeiden:** Sicherstellen, dass der dynamisch abgerufene Kontext den Basiskontext sinnvoll ergänzt.
*   **Komplexität der Implementierung:** Die Anpassung der Prompt-Logik und der Retrieval-Modi erfordert sorgfältige Planung.
*   **Evaluierungsaufwand:** Umfassende Tests sind notwendig, um die Wirksamkeit der neuen Strategie nachzuweisen.

## 7. Nächste Schritte (Priorisiert)

1.  **[ ] Task 1:** Detaillierte Ausarbeitung des Inhalts für den "Direkten Globalen Basiskontext".
    *   **Verantwortlich:** Entwicklungsteam
    *   **Deadline:** TT.MM.JJJJ
2.  **[ ] Task 2:** Implementierung der Integration des Basiskontexts in die Prompt-Generierung.
    *   **Verantwortlich:** Entwicklungsteam
    *   **Deadline:** TT.MM.JJJJ
3.  **[ ] Task 3:** Durchführung erster Tests und Iteration am Basiskontext.
    *   **Verantwortlich:** Entwicklungsteam
    *   **Deadline:** TT.MM.JJJJ