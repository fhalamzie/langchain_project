# WINCASA Implementierungsaufgaben

## Aktuelle Priorität: TAG-Modell-Implementierung

### 🚨 Phase 0: Kritische Grundlage (SOFORT)

#### Aufgabe 0.1: Abhängigkeiten & Umgebung korrigieren ⚡ KRITISCH
**Geschätzt**: 30 Minuten
**Status**: ✅ Abgeschlossen

```bash
# Fehlende Abhängigkeiten installieren
pip install langgraph sqlglot langchain-experimental

# Installation überprüfen
python -c "import langgraph, sqlglot; print('Dependencies OK')"

# requirements.txt aktualisieren
pip freeze > requirements.txt
```

**Erfolgskriterien**: Alle Importe funktionieren fehlerfrei

---

#### Aufgabe 0.2: Aktuelle SQL-Generierungsprobleme diagnostizieren ⚡ KRITISCH
**Geschätzt**: 2-4 Stunden  
**Status**: Ausstehend

**Teilaufgaben**:
1. **Alle 5 Retrieval-Modi testen**
   ```bash
   python diagnostic_test.py
   ```
   
2. **Minimalen Prompt-Test erstellen** 
   - LLM NUR mit Systemprompt + Abfrage testen (ohne Retrieval)
   - Überprüfen, ob LLM grundlegende SQL-Regeln ohne Kontextrauschen befolgt
   - Testen mit: "Wer wohnt in der Marienstr. 26, 45307 Essen"
   
3. **Kontextinterferenz analysieren**
   - Testen, ob 498 YAML-Dokumente Systemanweisungen überschreiben
   - Prompteffektivität vs. überwältigenden Kontext messen

**Beispieltest**:
```python
# Systemprompt-Compliance ohne Retrieval-Rauschen testen
test_prompt = '''
KRITISCHE REGELN FÜR SQL-GENERIERUNG:
- Tabelle BEWOHNER enthält Bewohner
- Spalte BSTR enthält: "Straßenname Hausnummer" (z.B. "Marienstraße 26")  
- Spalte BPLZORT enthält: "PLZ Ort" (z.B. "45307 Essen")
- IMMER LIKE-Muster für Adressen verwenden, NIE exakte Übereinstimmung
- Beispiel: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

Abfrage: Wer wohnt in der Marienstr. 26, 45307 Essen
Generiere NUR die SQL-Abfrage.
'''
```

**Erfolgskriterien**: LLM generiert korrekte SQL mit minimalen, fokussierten Prompts

---

### 🔧 Phase 1: TAG-Kernimplementierung

#### Aufgabe 1.1: TAG SYN (Synthesis) Modul erstellen ⚡ HOHE PRIORITÄT  
**Datei**: `tag_synthesizer.py`  
**Geschätzt**: 3-4 Tage  
**Status**: Ausstehend  
**Abhängigkeiten**: Aufgabe 0.1, 0.2

**Implementierung**:
```python
class QuerySynthesizer:
    QUERY_TYPE_SCHEMAS = {
        "address_lookup": {
            "tables": ["BEWOHNER", "BEWADR"],
            "rules": [
                "BSTR contains full street with number",
                "BPLZORT contains postal code and city", 
                "Use LIKE '%pattern%' for matching"
            ],
            "example_sql": "SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'"
        },
        "owner_lookup": {
            "tables": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "rules": ["EIGENTUEMER contains owners", "Join with VEREIG for properties"],
            "example_sql": "SELECT * FROM EIGENTUEMER E JOIN EIGADR A ON E.ID = A.EIGNR"
        },
        "financial_queries": {
            "tables": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
            "rules": ["Use ONR to link properties to accounts"],
            "example_sql": "SELECT * FROM KONTEN WHERE ONR = ?"
        },
        "property_queries": {
            "tables": ["OBJEKTE", "WOHNUNG"],
            "rules": ["OBJEKTE are buildings, WOHNUNG are individual apartments"],
            "example_sql": "SELECT COUNT(*) FROM WOHNUNG"
        }
    }
    
    def synthesize(self, query: str) -> SynthesisResult:
        query_type = self._classify_query(query)
        schema_context = self.QUERY_TYPE_SCHEMAS[query_type]
        entities = self._extract_entities(query)
        sql = self._generate_sql(entities, schema_context)
        return SynthesisResult(sql, query_type, entities, schema_context)
```

**Tests**: `test_tag_synthesizer.py` erstellen  
**Erfolgskriterien**: 90% korrekte Tabellenauswahl, korrekte LIKE-Muster-Verwendung für Adressen

---

#### Aufgabe 1.2: SQL-Validierungsschicht erstellen ⚡ HOHE PRIORITÄT
**Datei**: `sql_validator.py`
**Geschätzt**: 2-3 Tage
**Status**: ✅ Abgeschlossen
**Abhängigkeiten**: Aufgabe 0.1 (sqlglot-Abhängigkeit)

**Implementierung**:
```python
class SQLValidator:
    def validate_and_fix(self, sql: str, available_tables: List[str]) -> ValidationResult:
        try:
            parsed = sqlglot.parse_one(sql, dialect="firebird")
            issues = []
            
            # Tabellenexistenz prüfen
            for table in self._extract_tables(parsed):
                if table not in available_tables:
                    issues.append(f"Table '{table}' does not exist")
            
            # Firebird-Syntax prüfen
            if "LIMIT" in sql.upper():
                fixed_sql = sql.upper().replace("LIMIT", "FIRST")
                issues.append("Converted LIMIT to FIRST for Firebird")
            
            return ValidationResult(
                valid=len(issues) == 0,
                issues=issues,
                fixed_sql=fixed_sql if issues else sql,
                suggestions=self._generate_suggestions(issues)
            )
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))
```

**Tests**: `test_sql_validator.py` erstellen  
**Erfolgskriterien**: 95% Syntax-Validierungsgenauigkeit, 80% automatischer Fix-Erfolg

---

#### Aufgabe 1.3: TAG GEN (Generation) Modul erstellen ⚡ HOHE PRIORITÄT
**Datei**: `tag_generator.py`  
**Geschätzt**: 2 Tage  
**Status**: Ausstehend  
**Abhängigkeiten**: Aufgabe 1.1

**Implementierung**:
```python
class ResponseGenerator:
    def generate(self, sql_results: List[Dict], query_type: str, original_query: str) -> str:
        if not sql_results:
            return self._generate_empty_response(query_type, original_query)
        
        formatter = self.FORMATTERS[query_type]
        return formatter.format(sql_results, original_query)
    
    def _generate_empty_response(self, query_type: str, query: str) -> str:
        templates = {
            "address_lookup": f"Es wurden keine Bewohner für die angegebene Adresse gefunden.",
            "owner_lookup": f"Es wurden keine Eigentümer für die Anfrage gefunden.", 
            "count_query": f"Die Anzahl beträgt 0."
        }
        return templates.get(query_type, "Keine Ergebnisse gefunden.")
```

**Tests**: `test_tag_generator.py` erstellen  
**Erfolgskriterien**: Klare, kontextbezogene deutsche Antworten für alle Abfragetypen

---

### 🔗 Phase 2: TAG-Integration

#### Aufgabe 2.1: TAG-Pipeline-Integration erstellen ⚡ HOHE PRIORITÄT
**Datei**: `tag_pipeline.py`  
**Geschätzt**: 2-3 Tage  
**Status**: Ausstehend  
**Abhängigkeiten**: Aufgaben 1.1, 1.2, 1.3

**Implementierung**:
```python
class TAGPipeline:
    def process(self, query: str) -> TAGResult:
        # Phase 1: SYN (Synthesis)
        synthesis = self.synthesizer.synthesize(query)
        
        # Validierung
        validation = self.validator.validate_and_fix(synthesis.sql, self.available_tables)
        if not validation.valid:
            # Mit erweitertem Kontext erneut versuchen
            synthesis = self.synthesizer.synthesize_enhanced(query, validation.suggestions)
            validation = self.validator.validate_and_fix(synthesis.sql, self.available_tables)
        
        # Phase 2: EXEC (Execution) - Bestehende FDB-Schnittstelle verwenden
        results = self.executor.execute(validation.fixed_sql or synthesis.sql)
        
        # Phase 3: GEN (Generation)
        response = self.generator.generate(results, synthesis.query_type, query)
        
        return TAGResult(
            query=query,
            sql=validation.fixed_sql or synthesis.sql,
            raw_results=results,
            response=response,
            synthesis_info=synthesis,
            validation_info=validation
        )
```

**Integration**: `firebird_sql_agent_direct.py` aktualisieren, um TAG als 6. Retrieval-Modus einzubeziehen  
**Tests**: `test_tag_pipeline.py` erstellen  
**Erfolgskriterien**: End-to-End-Verarbeitung für alle 11 Testabfragen

---

#### Aufgabe 2.2: LangGraph-Workflow-Implementierung ⚡ HOHE PRIORITÄT
**Datei**: `langgraph_sql_workflow.py`
**Geschätzt**: 3-4 Tage
**Status**: ✅ Abgeschlossen
**Abhängigkeiten**: Aufgabe 0.1, 2.1

**Implementierung**:
```python
from langgraph.graph import StateGraph
from typing import TypedDict, Literal

class QueryState(TypedDict):
    query: str
    query_type: str
    entities: List[str]
    sql: str
    validation_result: ValidationResult
    execution_result: List[Dict]
    response: str
    retry_count: int
    error: Optional[str]

def create_sql_workflow():
    workflow = StateGraph(QueryState)
    
    # Knoten hinzufügen
    workflow.add_node("classify_query", classify_query_node)
    workflow.add_node("synthesize_sql", synthesize_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("enhance_context", enhance_context_node)
    
    # Bedingte Kanten hinzufügen
    workflow.add_conditional_edges(
        "validate_sql",
        decide_after_validation,
        {
            "execute": "execute_sql",
            "retry": "enhance_context", 
            "fail": "generate_response"
        }
    )
    
    return workflow.compile()
```

**Tests**: `test_langgraph_workflow.py` erstellen  
**Erfolgskriterien**: Komplexe Workflow-Ausführung mit 90% Erfolgsrate

---

### 🧪 Phase 3: Testen & Validierung

#### Aufgabe 3.1: Umfassender Modus-Vergleich ⚡ HOHE PRIORITÄT
**Datei**: `comprehensive_mode_test.py`  
**Geschätzt**: 2-3 Tage  
**Status**: Ausstehend  
**Abhängigkeiten**: Alle vorherigen Aufgaben

**Alle 6 Modi testen**:
1. Enhanced-Modus (bestehend)
2. FAISS-Modus (bestehend)  
3. None-Modus (bestehend)
4. LangChain-Modus (behoben)
5. LangGraph-Modus (neu)
6. TAG-Modus (neu)

**Testabfragen**:
1. "Wer wohnt in der Marienstr. 26, 45307 Essen"
2. "Wer wohnt in der Marienstraße 26"
3. "Wer wohnt in der Bäuminghausstr. 41, Essen"
4. "Wer wohnt in der Schmiedestr. 8, 47055 Duisburg"
5. "Alle Mieter der MARIE26"
6. "Alle Eigentümer vom Haager Weg bitte"
7. "Liste aller Eigentümer"
8. "Liste aller Eigentümer aus Köln"
9. "Liste aller Mieter in Essen"
10. "Durchschnittliche Miete in Essen"
11. "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg"

**Testbefehle**:
```bash
# Alle Modi mit umfassender Analyse testen
python comprehensive_mode_test.py --all-modes --detailed-analysis

# Vergleichsbericht generieren
python generate_comparison_report.py --output comparison_report.md
```

**Erfolgskriterien**: 
- TAG-Modus: >90% SQL-Korrektheit (vs. aktuell ~20%)
- LangGraph-Modus: >85% SQL-Korrektheit
- Alle Modi: Vollständige Ausführung ohne Abstürze

---

### 🔗 Phase 2: Informationsarchitektur-Neugestaltung

#### Aufgabe 2.3: Aktuelle Informationsverteilung analysieren ⚡ HOHE PRIORITÄT
**Datei**: Informationsarchitekturanalyse
**Geschätzt**: 1 Tag
**Status**: Ausstehend
**Abhängigkeiten**: Analyse des aktuellen Systems

**Analyse des aktuellen Zustands**:
- **Systemprompt**: Derzeit mit Retrieval-Kontext gemischt
- **YAML-Struktur**: 498 Dateien mit allem vermischt
- **Problem**: LLM von detaillierten Informationen überwältigt, wenn es grundlegende Regeln benötigt

**Informationsaudit**:
```
Aktueller YAML-Inhalt (BEWOHNER.yaml Beispiel):
├── Grundlegende Informationen (table_name, description) → Systemprompt
├── Geschäftskontext (business_examples) → Systemprompt  
├── Detaillierte Spalten (125+ Zeilen) → Embeddings
├── Einschränkungen & Beziehungen → Embeddings
├── Interne Konventionen → Embeddings
└── Häufige Abfragen → Embeddings
```

**Analyseergebnisse**: 
- **80% des YAML-Inhalts** sollten in Embeddings sein (detaillierte technische Informationen)
- **20% des YAML-Inhalts** sollten im Systemprompt sein (wesentliche Regeln)

---

#### Aufgabe 2.4: Systemprompt neu gestalten ⚡ HOHE PRIORITÄT
**Datei**: `optimized_system_prompt.py`
**Geschätzt**: 1-2 Tage
**Status**: ✅ Abgeschlossen
**Abhängigkeiten**: Aufgabe 2.3

**Neue Systemprompt-Struktur**:
```python
OPTIMIZED_SYSTEM_PROMPT = """
CORE FIREBIRD SQL RULES:
- Use FIRST instead of LIMIT for row limiting
- Use LIKE '%pattern%' for address matching, NEVER exact match
- Primary tables: BEWOHNER (residents), EIGENTUEMER (owners), WOHNUNG (apartments), OBJEKTE (buildings), KONTEN (accounts)

CRITICAL ADDRESS PATTERNS:
- BSTR column: "Straßenname Hausnummer" (e.g. "Marienstraße 26")
- BPLZORT column: "PLZ Ort" (e.g. "45307 Essen")
- ALWAYS use: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

KEY RELATIONSHIPS:
- ONR (Object Number): Central linking field between properties, residents, accounts
- JOIN paths: BEWOHNER.ONR → OBJEKTE.ONR, EIGENTUEMER → VEREIG.ONR → OBJEKTE.ONR

QUERY CLASSIFICATION:
- Address lookup: "Wer wohnt in..." → BEWOHNER table with LIKE patterns
- Property count: "Wie viele Wohnungen..." → COUNT(*) FROM WOHNUNG  
- Owner lookup: "Eigentümer..." → EIGENTUEMER table with city filters
- Financial: "Miete, Kosten..." → KONTEN/BUCHUNG tables with aggregations
"""
```

**Tests**: Fokussierte vs. überwältigende Prompts für LLM-Compliance vergleichen

---

#### Aufgabe 2.5: Fokussiertes Embedding-System erstellen ⚡ HOHE PRIORITÄT
**Datei**: `focused_embeddings.py`
**Geschätzt**: 2-3 Tage
**Status**: ✅ Abgeschlossen
**Abhängigkeiten**: Aufgabe 2.4

**Neue Embedding-Strategie**:
1. **Tabellenspezifische Chunks**: Jede Tabelle erhält fokussiertes Dokument mit detaillierten Informationen
2. **Abfragegesteuerte Abrufe**: Nur von TAG SYN identifizierte Tabellen abrufen
3. **Strukturierter Inhalt**: Technische Details von wesentlichen Regeln trennen

**Implementierung**:
```python
class FocusedEmbeddingSystem:
    def __init__(self):
        self.table_embeddings = {}  # Tabellenname → detaillierter YAML-Inhalt
        self.query_classifier = QuerySynthesizer()  # Von TAG SYN
    
    def retrieve_table_details(self, table_names: List[str]) -> str:
        """Nur spezifische Tabellendetails abrufen, nicht alle 498 YAMLs"""
        relevant_details = []
        for table in table_names:
            if table in self.table_embeddings:
                relevant_details.append(self.table_embeddings[table])
        return "\n\n".join(relevant_details)
    
    def process_query(self, query: str) -> str:
        # 1. TAG SYN bestimmt benötigte Tabellen
        synthesis = self.query_classifier.synthesize(query)
        tables_needed = synthesis.schema_context["primary_tables"]
        
        # 2. Nur relevante Tabellendetails abrufen
        detailed_context = self.retrieve_table_details(tables_needed)
        
        # 3. Fokussierten Prompt + gezielte Details kombinieren
        return OPTIMIZED_SYSTEM_PROMPT + "\n\nRELEVANT TABLES:\n" + detailed_context
```

**Erfolgskriterien**: 2-5 relevante Tabellendetails anstelle aller 498 YAMLs abrufen

---

#### Aufgabe 2.6: TAG-Pipeline mit Informationsarchitektur implementieren ⚡ HOHE PRIORITÄT
**Datei**: `tag_pipeline_optimized.py`
**Geschätzt**: 2-3 Tage
**Status**: Teilweise abgeschlossen
**Abhängigkeiten**: Aufgaben 2.4, 2.5

**Optimierte Pipeline**:
```python
class OptimizedTAGPipeline:
    def process(self, query: str) -> TAGResult:
        # Phase 1: SYN mit fokussiertem Kontext
        synthesis = self.synthesizer.synthesize(query)
        
        # Phase 2: Nur benötigte Tabellendetails abrufen
        needed_tables = synthesis.schema_context["primary_tables"] 
        detailed_context = self.embedding_system.retrieve_table_details(needed_tables)
        
        # Phase 3: SQL mit fokussiertem Kontext generieren
        focused_prompt = OPTIMIZED_SYSTEM_PROMPT + detailed_context
        sql = self.llm.generate_sql(query, focused_prompt)
        
        # Phase 4: EXEC (bestehende FDB-Schnittstelle)
        results = self.executor.execute(sql)
        
        # Phase 5: GEN (bestehender Antwortformatierer)
        response = self.generator.generate(results, synthesis.query_type, query)
        
        return TAGResult(query, sql, results, response, synthesis)
```

---

### 🔧 Phase 4: Unified Embedding System Consolidation (Zukünftige Implementierung)

#### Aufgabe 4.1: Aktuelle Embedding-Fragmentierung analysieren ⚡ MITTLERE PRIORITÄT
**Datei**: Analyse aktueller Embedding-Systeme
**Geschätzt**: 1 Tag
**Status**: Ausstehend (Zukünftige Phase)
**Abhängigkeiten**: TAG-Pipeline-Fertigstellung

**Aktueller fragmentierter Zustand**:
- **Enhanced-Modus**: `enhanced_retrievers.py` - Mehrstufiges FAISS mit Kategorien
- **FAISS-Modus**: `retrievers.py` - Grundlegende FAISS-Implementierung  
- **None-Modus**: Keine Embeddings
- **LangChain-Modus**: Verwendet eigenes Abrufsystem
- **TAG-Modus**: `focused_embeddings.py` - Strategischer fokussierter Ansatz

**Probleme**:
- Mehrere separate Embedding-Modelle → Speicherverschwendung
- Doppelte Vektorspeicher für dieselben Dokumente → Leistungsverlust
- Inkonsistente Kontextqualität über Modi hinweg
- Komplexe Wartung über mehrere Dateien hinweg

---

#### Aufgabe 4.2: Unified Embedding Architecture entwerfen ⚡ MITTLERE PRIORITÄT
**Datei**: `unified_embedding_hub.py`
**Geschätzt**: 2-3 Tage
**Status**: Ausstehend (Zukünftige Phase)
**Abhängigkeiten**: Aufgabe 4.1

**Einheitliche Architektur-Design**:
```python
class UnifiedEmbeddingHub:
    """Zentrales Embedding-System, das von allen Retrieval-Modi verwendet wird"""
```

## ✅ Abgeschlossen

- Core System mit 5 Retrieval-Modi implementiert und funktionsfähig
- Testing Framework mit 13/13 bestandenen Tests (0,02s Ausführung)
- Datenbank-Integration mit direkter FDB-Schnittstelle und Connection-Pooling
- Business-Logik mit erweitertem Business-Glossar und JOIN-Reasoning
- Schema-Analyse mit FK-Graph-Analyzer und NetworkX
- Monitoring mit Phoenix OTEL-Integration und SQLite-Backend
- Code-Qualität mit Black, isort, flake8, bandit konfiguriert

## ⏳ Ausstehend

- TAG-Modell-Implementierung zur Verbesserung der SQL-Generierungsgenauigkeit
- Informationsarchitektur-Neugestaltung für optimierte Prompts
- Unified Embedding System für konsistenten Kontext über alle Modi

## 🎯 Erfolgskriterien

- SQL-Generierungsgenauigkeit: 20% → 90%
- Tabellenauswahl: >95% korrekte Identifikation
- Adressabfragen: 100% korrekte LIKE-Muster-Verwendung statt exakter Übereinstimmung
- Geschäftslogik: >90% korrekte Begriff-zu-Tabelle-Zuordnung
- Antwortzeit: <10s für komplexe Abfragen, <5s für einfache Abfragen