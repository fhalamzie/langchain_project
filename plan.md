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

## 8. Erweiterte SQL-Spezialisierung: SQLCoder-2 & LangChain Integration

### 8.1. SQLCoder-2 mit JOIN-Aware Prompting

**Zielsetzung:** Integration eines SQL-spezialisierten LLM-Modells zur Verbesserung der SQL-Generierung in komplexen Szenarien.

**Technische Details:**
- **Modell**: SQLCoder-2 (7B/15B Parameter) via HuggingFace Transformers
- **Spezialisierung**: Optimiert für SQL-Generierung mit besserer Dialekt-Unterstützung
- **JOIN-Awareness**: Erweiterte Prompting-Techniken für komplexe Tabellenbeziehungen
- **Integration**: Als 4. Retrieval-Modus `sqlcoder` in bestehende Architektur

**Implementierungsplan:**
```python
# sqlcoder_retriever.py
class SQLCoderRetriever:
    def __init__(self, model_name="defog/sqlcoder2"):
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
    def generate_sql(self, query, schema_context, join_hints):
        # JOIN-aware prompting with schema context
        prompt = self._build_join_aware_prompt(query, schema_context, join_hints)
        return self._generate_with_model(prompt)
```

**Performance-Ziele:**
- Erfolgsrate: >75% (vs. 63.6% aktuell)
- Bessere Firebird-SQL-Dialekt-Unterstützung
- Reduzierte Timeouts bei komplexen JOINs

### 8.2. LangChain SQL Database Agent Integration

**Zielsetzung:** Nutzung der nativen LangChain SQL-Tools für verbesserte Error-Recovery und Schema-Introspection.

**Technische Details:**
- **Framework**: LangChain SQL Database Agent mit React-Pattern
- **Tools**: Automatische Schema-Introspection, SQL-Execution, Error-Recovery
- **Integration**: Als 5. Retrieval-Modus `langchain` mit separatem Agent

**Implementierungsplan:**
```python
# langchain_sql_agent.py
from langchain_experimental.sql import SQLDatabaseChain
from langchain.agents import create_sql_agent

class LangChainSQLAgent:
    def __init__(self, db_connection, llm):
        self.db = SQLDatabase.from_uri(db_connection)
        self.agent = create_sql_agent(
            llm=llm,
            db=self.db,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
```

**Performance-Ziele:**
- Erfolgsrate: >70% mit automatischer Error-Recovery
- Bessere Fehlerbehandlung und Debugging
- Chain-of-Thought SQL-Reasoning

### 8.3. Implementierungsroadmap

**Phase 1: SQLCoder-2 Integration (Woche 1-2)**
1. Model Setup und Testing
2. JOIN-Aware Prompting entwickeln
3. Integration in `firebird_sql_agent_direct.py`
4. Initiale Performance-Tests

**Phase 2: LangChain SQL Agent (Woche 3-4)**
1. LangChain SQL Agent Setup
2. Firebird-Kompatibilität testen
3. Error-Recovery-Mechanismen implementieren
4. Performance-Vergleich mit bestehenden Modi

**Phase 3: Vergleichende Evaluation (Woche 5)**
1. Erweiterte Test-Suite für 5 Modi
2. Performance-Benchmarking
3. Dokumentation und Best-Practice-Guides
4. Produktions-Deployment-Vorbereitung

**Testing-Framework:**
```bash
# Vergleichstests aller 5 Modi
python optimized_retrieval_test.py --modes enhanced,faiss,none,sqlcoder,langchain
python comparative_sql_analysis.py --detailed-metrics
```

### 8.4. Erwartete Systemverbesserungen

**Quantitative Ziele:**
- Gesamt-Erfolgsrate: >75% (vs. 63.6% aktuell)
- Timeout-Reduktion: <5% (vs. 27% bei FAISS aktuell)
- Durchschnittliche Ausführungszeit: <20s über alle Modi

**Qualitative Verbesserungen:**
- Bessere SQL-Dialekt-Anpassung (Firebird FIRST vs. LIMIT)
- Verbesserte JOIN-Generierung für komplexe Beziehungen
- Automatische Error-Recovery bei SQL-Syntax-Fehlern
- Erhöhte Robustheit bei unbekannten Query-Patterns

## 9. Aktuelle Issues und Next Steps (2025-06-04)

### 9.1. Identified Issues from Testing

**Minor Issues (Non-Critical):**
- **Phoenix UI Connection**: Connection refused to localhost:6006 (doesn't affect core functionality)
- **Different SQL Strategies**: None mode uses DISTINCT ONR vs Enhanced/FAISS using COUNT(*)
- **Test Framework**: Response extraction needs improvement for better result parsing

**Areas for Extended Testing:**
- **SQLCoder & LangChain Modes**: Full validation pending (implementation complete)
- **Complex Query Testing**: Current validation limited to simple count queries
- **Multi-Query Performance**: Extended test suite needed for production validation

### 9.2. Immediate Next Steps (Priority)

**1. Phoenix UI Fix**
- Investigate Phoenix monitoring dashboard connection issues
- Ensure localhost:6006 service is running or disable UI mode
- Alternative: Use Phoenix logging without UI

**2. SQLCoder & LangChain Mode Testing**
- Run comprehensive tests for all 5 retrieval modes
- Validate SQLCoder-2 model loading and SQL generation
- Test LangChain SQL Database Agent integration

**3. Extended Test Suite**
```bash
# Target test commands
python optimized_retrieval_test.py --modes enhanced,faiss,none,sqlcoder,langchain
python comprehensive_query_test.py  # multiple query types
python accuracy_validation_test.py  # result correctness
```

**4. Test Framework Improvements**
- Fix response parsing in test scripts
- Better result extraction and validation
- Standardized success/failure criteria

### 9.3. Testing Requirements

**Query Coverage:**
- Address lookups: "Wer wohnt in der Marienstraße 26?"
- JOIN operations: "Bewohner mit Adressdaten für Objekt 5"
- Aggregations: "Durchschnittliche Miete pro Objekt"
- Complex business logic: "Eigentümer mit mehr als 2 Wohnungen"

**Performance Validation:**
- Response time targets: <30s per query
- Success rate targets: Document actual rates, not assumed percentages
- Memory usage monitoring
- Error rate tracking

**Accuracy Testing:**
- SQL syntax validation
- Result correctness verification
- Business logic compliance
- Firebird dialect compatibility

### 9.4. Documentation Tasks

**Update Required:**
- Remove inflated success rate claims
- Document actual test results factually
- Update performance baselines with real data
- Clarify testing limitations and scope

**File Updates:**
- `CLAUDE.md`: ✅ Updated with factual test results
- `plan.md`: ✅ Updated with current issues
- Test result files: Need comprehensive validation data

### 9.5. Future Considerations

**Post-Validation Tasks:**
- Production deployment guidelines
- Performance optimization opportunities
- Extended query pattern support
- Real user feedback integration

**Technical Debt:**
- Code cleanup and documentation
- Test framework standardization
- Error handling improvements
- Monitoring system fixes