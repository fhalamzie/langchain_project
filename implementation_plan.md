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

## 7. Überarbeitete Implementierungsstrategie (Januar 2025)

### **7.1. Neue Drei-Phasen-Roadmap**

#### **Phase 1: Foundation + Baseline (Sofort umsetzbar)**

**1.1 Strukturierten Global-Context erstellen**
```python
GLOBAL_CONTEXT = {
    "core_entities": {
        "people": ["BEWOHNER", "EIGENTUEMER"],
        "properties": ["OBJEKTE", "WOHNUNG"], 
        "finance": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"]
    },
    "key_relationships": {
        "BEWOHNER -> OBJEKTE": "BWO = ONR",
        "EIGENTUEMER -> OBJEKTE": "via VEREIG table",
        "KONTEN -> BUCHUNG": "KNR = BKNR"
    },
    "critical_patterns": {
        "address_search": "BEWOHNER: BSTR + BPLZORT",
        "financial_lookup": "KONTEN -> BUCHUNG -> SOLLSTELLUNG"
    }
}
```

**1.2 Echte Datenextraktion für Kontextanreicherung**
- Top 30 Zeilen pro High-Priority-Tabelle extrahieren
- Irrelevante Spalten filtern (NULL, 0, leer)
- Datenpattern und -formate erkennen
- Komprimierte Samples in Kontext integrieren

**1.3 Iterativer Testparcours implementieren**
```python
# iterative_improvement_test.py
TEST_QUERIES = {
    "basic_lookups": ["Wer wohnt in der Marienstraße 26?"],
    "joins_required": ["Welche Bewohner wohnen in Objekt ONR 1001?"],
    "complex_business": ["Welche Eigentümer haben mehr als 2 Wohnungen?"],
    "aggregations": ["Durchschnittliche Miete pro Objekt"]
}

FEEDBACK_FORMAT = {
    "iteration_X": {
        "context_version": "...",
        "success_rate": 0.xx,
        "user_feedback": "...",
        "improvements_needed": ["..."],
        "best_practices_learned": ["..."]
    }
}
```

#### **Phase 2: Strukturelle Verbesserungen (Kurzfristig)**

**2.1 Schema-Graph-Representation entwickeln**
```python
class SchemaGraph:
    def get_relevant_subgraph(self, query_entities):
        # Relevante Tabellen für Query finden
        # Kürzeste Pfade zwischen Entitäten
        # Kompakte Sub-Schema zurückgeben
```

**2.2 Join-Path-Finder implementieren**
```python
def find_join_path(from_table, to_table, schema_graph):
    # Automatische JOIN-Generierung basierend auf Pfad
    # Beispiel: BEWOHNER -> KONTEN via OBJEKTE
```

**2.3 Retrieval auf Struktur statt Text umstellen**
```python
class StructuralRetriever:
    def retrieve_context(self, user_query):
        # 1. Entitäten extrahieren
        # 2. Relevante Tabellen finden  
        # 3. Schema-Subgraph erstellen
        # 4. Samples + Patterns laden
```

#### **Phase 3: Erweiterte Optimierungen (Mittelfristig)**

**3.1 Neo4j-Integration evaluieren**
- Firebird-Schema als Cypher-Graph
- Multi-Hop-Beziehungen modellieren
- Cypher-zu-SQL-Translation

**3.2 LLM-Fine-Tuning vorbereiten**
- Erfolgreiche Query-SQL-Paare sammeln
- User-Feedback als Quality-Score
- Training-Dataset erstellen

**3.3 Automatisierter Feedback-Loop**
- Erfolgreiche Patterns extrahieren
- Fehlermuster identifizieren
- Kontext automatisch anpassen

### **7.2. Testgetriebene Entwicklung**

**Test-Framework**: `comprehensive_improvement_test.py`
- GPT-4o-mini als konsistenter Test-Agent
- Feedback-JSON für jede Iteration
- Automatischer Vergleich zwischen Phasen
- Ziel: >85% Erfolgsrate

**Bewertungskriterien** (0-15 Punkte pro Query):
- SQL-Syntax (0-3)
- Tabellen-Selektion (0-3) 
- JOIN-Logik (0-3)
- Business-Logic (0-3)
- Ergebnis-Genauigkeit (0-3)

## 8. Zukünftige Überlegungen und mögliche Erweiterungen

### 8.1. Nutzung einer Graphdatenbank (z.B. Neo4j) zur Kontextanreicherung

*   **Idee:** Exploration der Integration einer Graphdatenbank zur expliziten Modellierung und Abfrage der komplexen Beziehungen zwischen den Firebird-Tabellen.
*   **Potenzieller Nutzen:**
    *   Verbessertes Verständnis von Multi-Hop-Beziehungen und komplexen Abhängigkeiten durch das LLM.
    *   Präzisere Extraktion von relevanten Sub-Graphen als Kontext für die SQL-Generierung.
    *   Formale Repräsentation der Wissensbasis als Wissensgraph.
*   **Herausforderungen:**
    *   Erhöhte Systemkomplexität (zusätzliche Datenbank, Synchronisationsaufwand).
    *   Entwicklung von Mechanismen zur Kontext-Extraktion aus dem Graphen und Integration in den LLM-Prompt.
*   **Status:** Eine konzeptionelle Überlegung für eine spätere Optimierungsphase, nachdem die aktuelle hybride Kontextstrategie vollständig implementiert und evaluiert wurde.