# WINCASA Phase 2 - Optimierung & Neue Query-Architektur

## Überblick

Phase 2 transformiert das WINCASA Query-System von starren SQL-Templates zu einem intelligenten, mehrstufigen Ansatz. Statt die bestehenden 4 Modi zu ersetzen, werden sie optimiert und durch neue Komponenten ergänzt.

## Ausgangslage

- **Problem**: 35 SQL-Queries mit 100+ Zeilen, schlechte Treffsicherheit bei natürlichen Fragen
- **Bestehend**: 4 Modi (JSON/SQL × Standard/Vanilla) funktionieren unzureichend
- **Ziel**: Pragmatische Verbesserung ohne komplette Neuentwicklung

## Architektur-Vision

```
User Query → Intent Router → [Template System | Structured RAG | Fallback SQL] → Response
```

### Komponenten

1. **Intent Router**: Klassifiziert Anfragen in 3 Kategorien
   - Template-Queries (80% der Fälle)
   - RAG-Lookups (15% der Fälle) 
   - Fallback SQL (5% der Fälle)

2. **Template System**: 30 parametrisierte SQL-Templates
3. **Structured RAG**: JSON/CSV für Faktenabfragen
4. **Optimierte Basis**: Views + SQL-Cleanup der bestehenden Modi

## Phase 2.1: Foundation & Quick Wins (Woche 1)

### Ziele
- 30-50% Verbesserung der bestehenden Modi
- Basis-Infrastruktur für neue Komponenten

### Tasks

#### Tag 1: Baseline & Analyse
```bash
# 1. Golden Set erstellen (50-100 Test-Anfragen)
cp -r templates/ golden_set/
python create_golden_set.py --sample-size 100

# 2. Current Performance messen
python benchmark_current_modes.py --output baseline_metrics.json
```

#### Tag 2-3: Database Views
```sql
-- Core Views für vereinfachte Abfragen
CREATE VIEW vw_mieter_komplett AS
SELECT 
    m.BEWNR, m.BEWNAME, m.BEWVNAME, m.BTEL, m.BEMAIL,
    o.OSTRASSE as GEBAEUDE_ADRESSE,
    SUBSTRING(o.OPLZORT FROM POSITION(' ' IN o.OPLZORT) + 1) as STADT,
    w.EBEZ as WOHNUNG,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, m.VBEGINN)) as MIETDAUER_JAHRE
FROM BEWOHNER m
JOIN OBJEKTE o ON m.ONR = o.ONR
JOIN WOHNUNG w ON m.ONR = w.ONR AND m.ENR = w.ENR
WHERE m.VENDE IS NULL;

CREATE VIEW vw_eigentuemer_portfolio AS
SELECT 
    e.EIGNR, e.ENAME, e.EVNAME, e.ETEL1, e.EEMAIL,
    o.ONR, o.OSTRASSE, o.OBEZ,
    COUNT(*) OVER (PARTITION BY e.EIGNR) as ANZAHL_OBJEKTE
FROM EIGADR e
JOIN EIGENTUEMER eu ON e.EIGNR = eu.EIGNR
JOIN OBJEKTE o ON eu.ONR = o.ONR;
```

#### Tag 4-5: SQL Cleanup & System Prompts
```python
# SQL-Query Optimizer
def optimize_legacy_queries():
    """Reduziert komplexe SQLs auf Views basierte Versionen"""
    for query_file in Path("SQL_QUERIES").glob("*.sql"):
        if is_view_candidate(query_file):
            optimized = convert_to_view_query(query_file)
            save_optimized_query(query_file, optimized)

# Enhanced System Prompts
ENHANCED_PROMPTS = {
    "sql_standard": """
Du hast Zugriff auf optimierte Views:
- vw_mieter_komplett: Alle Mieter mit Gebäudeadressen
- vw_eigentuemer_portfolio: Eigentümer mit Portfolio-Übersicht

Schema-Beispiele:
{schema_context}

Beispiel-Queries:
1. Mieter finden: SELECT * FROM vw_mieter_komplett WHERE GEBAEUDE_ADRESSE LIKE :pattern
2. Eigentümer Portfolio: SELECT * FROM vw_eigentuemer_portfolio WHERE ENAME = :name
"""
}
```

### Deliverables Phase 2.1
- [ ] 5 Core Database Views
- [ ] Optimierte SQL-Queries (reduziert von 100+ auf ~30 Zeilen)
- [ ] Verbesserte System-Prompts mit Schema-Kontext
- [ ] Golden Set mit 100 Test-Anfragen
- [ ] Baseline-Metriken der aktuellen Modi

## Phase 2.2: Structured RAG Prototype (Woche 2)

### Ziele
- RAG-System für Fakten-Lookups ("Wer wohnt in X?", "Kontakt von Y")
- Vergleich RAG vs. bestehende Modi

### Architecture
```python
class StructuredRAG:
    def __init__(self):
        self.data = {
            "mieter": self.load_json("data/mieter_komplett.json"),
            "eigentuemer": self.load_json("data/eigentuemer_portfolio.json"),
            "objekte": self.load_json("data/objekte_details.json")
        }
    
    def query(self, user_question: str):
        context = self.prepare_context(user_question)
        return self.llm.query_with_context(user_question, context)
```

### Tasks

#### Tag 1-2: Export Pipeline
```python
# data_exporter.py
EXPORT_CONFIGS = {
    "mieter_komplett": {
        "sql": "SELECT * FROM vw_mieter_komplett LIMIT 500",
        "file": "data/mieter_komplett.json"
    },
    "eigentuemer_portfolio": {
        "sql": "SELECT * FROM vw_eigentuemer_portfolio LIMIT 300", 
        "file": "data/eigentuemer_portfolio.json"
    },
    "objekte_details": {
        "sql": "SELECT * FROM OBJEKTE WHERE ONR < 890 LIMIT 100",
        "file": "data/objekte_details.json"
    }
}

def export_all_data():
    for name, config in EXPORT_CONFIGS.items():
        df = execute_sql(config["sql"])
        df.to_json(config["file"], orient="records", force_ascii=False)
        print(f"Exported {len(df)} rows to {config['file']}")
```

#### Tag 3-4: RAG Implementation
```python
# structured_rag.py
class WincasaRAG:
    def __init__(self):
        self.load_data()
        self.llm = OpenAI(model="gpt-4o-mini")  # Cost-efficient
    
    def classify_query_type(self, query: str) -> str:
        """Bestimmt ob RAG geeignet ist"""
        lookup_patterns = [
            "wer wohnt", "kontakt von", "adresse von", 
            "telefon von", "email von", "details zu"
        ]
        
        if any(pattern in query.lower() for pattern in lookup_patterns):
            return "lookup"
        else:
            return "complex"  # Fallback zu anderen Modi
    
    def query(self, user_question: str):
        if self.classify_query_type(user_question) != "lookup":
            return None  # Kein RAG-Fall
            
        # Relevante Daten laden (max 2000 Zeilen für Token-Limit)
        context_data = self.get_relevant_context(user_question)
        
        prompt = f"""
        Beantworte die Frage basierend nur auf den bereitgestellten Daten:
        
        Daten: {json.dumps(context_data, ensure_ascii=False)}
        
        Frage: {user_question}
        
        Antwort nur mit den verfügbaren Informationen. Bei fehlenden Daten sage: "Information nicht verfügbar".
        """
        
        return self.llm.complete(prompt)
```

#### Tag 5: A/B Testing Setup
```python
# ab_testing.py
class ABTestManager:
    def __init__(self):
        self.config = {
            "rag_percentage": 10,  # 10% traffic zu RAG
            "baseline_percentage": 90  # 90% zu bestehenden Modi
        }
    
    def route_query(self, query: str, user_id: str):
        # Hash-basierte konsistente Zuordnung
        user_hash = hash(user_id) % 100
        
        if user_hash < self.config["rag_percentage"]:
            return "rag"
        else:
            return "baseline"
```

### Deliverables Phase 2.2
- [ ] JSON-Export Pipeline für 3 Core-Entities
- [ ] RAG-Prototype für Lookup-Queries
- [ ] A/B Testing Framework
- [ ] Performance-Vergleich RAG vs. Modi
- [ ] Token-Cost Analysis

## Phase 2.3: Template System (Woche 3-4)

### Ziele
- Intent Router für automatische Query-Klassifizierung
- 10 wichtigste SQL-Templates implementieren
- Integration in bestehende Architektur

### Architecture
```python
class TemplateSystem:
    def __init__(self):
        self.intent_router = IntentRouter()
        self.templates = SQLTemplateEngine()
    
    def process(self, query: str):
        # 1. Intent erkennen
        intent = self.intent_router.classify(query)
        
        # 2. Parameter extrahieren  
        params = self.intent_router.extract_parameters(query, intent)
        
        # 3. Template ausführen
        return self.templates.execute(intent, params)
```

### Tasks

#### Woche 3: Intent Router
```python
# intent_router.py
class HierarchicalIntentRouter:
    def __init__(self):
        self.keyword_rules = self.load_keyword_rules()
        self.llm_classifier = OpenAI(model="gpt-4o-mini")
    
    def classify(self, query: str) -> dict:
        # Level 1: Keyword/Regex (hochpräzise)
        for intent, patterns in self.keyword_rules.items():
            if any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns):
                return {"intent": intent, "confidence": 0.95, "method": "keyword"}
        
        # Level 2: LLM Classifier
        return self.llm_classify(query)
    
    def llm_classify(self, query: str) -> dict:
        prompt = f"""
        Klassifiziere diese WINCASA-Anfrage:
        
        Verfügbare Intents:
        - mieter_suche: Fragen nach Mietern/Bewohnern
        - eigentuemer_info: Fragen nach Eigentümern  
        - objekt_details: Fragen nach Objekten/Gebäuden
        - finanz_abfrage: Fragen nach Kosten/Finanzen
        - leerstand: Fragen nach freien Wohnungen
        - kontakt_lookup: Fragen nach Kontaktdaten
        - unknown: Keine Zuordnung möglich
        
        Anfrage: "{query}"
        
        Antwort als JSON: {{"intent": "...", "confidence": 0.85}}
        """
        
        response = self.llm_classifier.complete(prompt)
        return json.loads(response)
```

#### Woche 4: SQL Templates
```python
# sql_templates.py
TEMPLATES = {
    "mieter_suche": {
        "sql": """
            SELECT BEWNAME, BEWVNAME, BTEL, GEBAEUDE_ADRESSE, WOHNUNG
            FROM vw_mieter_komplett 
            WHERE 1=1
            {% if adresse %} AND GEBAEUDE_ADRESSE ILIKE '%{{ adresse }}%' {% endif %}
            {% if stadt %} AND STADT ILIKE '%{{ stadt }}%' {% endif %}
            ORDER BY BEWNAME
        """,
        "params": ["adresse", "stadt"],
        "description": "Findet Mieter nach Adresse oder Stadt"
    },
    
    "eigentuemer_info": {
        "sql": """
            SELECT ENAME, EVNAME, ETEL1, EEMAIL, ANZAHL_OBJEKTE, OSTRASSE
            FROM vw_eigentuemer_portfolio
            WHERE 1=1
            {% if name %} AND (ENAME ILIKE '%{{ name }}%' OR EVNAME ILIKE '%{{ name }}%') {% endif %}
            {% if objekt %} AND OSTRASSE ILIKE '%{{ objekt }}%' {% endif %}
            ORDER BY ANZAHL_OBJEKTE DESC
        """,
        "params": ["name", "objekt"],
        "description": "Findet Eigentümer-Informationen"
    }
}

class SQLTemplateEngine:
    def __init__(self):
        self.jinja_env = Environment(loader=DictLoader({}))
        
    def execute(self, intent: str, params: dict) -> dict:
        if intent not in TEMPLATES:
            raise ValueError(f"Template für Intent '{intent}' nicht gefunden")
        
        template_config = TEMPLATES[intent]
        template = self.jinja_env.from_string(template_config["sql"])
        
        # Sichere Parameter-Substitution
        safe_params = self.sanitize_params(params)
        sql = template.render(**safe_params)
        
        # SQL ausführen
        results = execute_sql(sql)
        
        return {
            "intent": intent,
            "sql": sql,
            "results": results.to_dict('records'),
            "count": len(results)
        }
```

### Deliverables Phase 2.3
- [ ] Hierarchical Intent Router (Keyword + LLM)
- [ ] 10 SQL-Templates für häufigste Use Cases
- [ ] Parameter-Extraction System
- [ ] Template-Engine mit Jinja2
- [ ] Security: SQL-Injection Prevention

## Phase 2.4: Integration & Rollout (Woche 5-6)

### Ziele
- Vollständige Integration aller Komponenten
- Schrittweiser Rollout mit Feature Flags
- Monitoring & Rollback-Strategie

### Architecture
```python
class WincasaQueryEngine:
    def __init__(self):
        self.intent_router = IntentRouter()
        self.template_system = TemplateSystem()
        self.structured_rag = StructuredRAG()
        self.legacy_modes = LegacyModes()  # Fallback
        
    def process_query(self, query: str, user_id: str) -> dict:
        # Feature Flag Check
        if not self.feature_enabled("new_query_engine", user_id):
            return self.legacy_modes.process(query)
        
        try:
            # 1. Intent Classification
            classification = self.intent_router.classify(query)
            
            # 2. Route to appropriate handler
            if classification["confidence"] > 0.8:
                if classification["intent"] in TEMPLATE_INTENTS:
                    return self.template_system.process(query)
                elif classification["intent"] == "lookup":
                    return self.structured_rag.query(query)
            
            # 3. Fallback to legacy
            return self.legacy_modes.process(query)
            
        except Exception as e:
            # Error fallback
            logger.error(f"New engine failed: {e}")
            return self.legacy_modes.process(query)
```

### Tasks

#### Woche 5: Shadow Mode
```python
# shadow_mode.py
class ShadowTesting:
    def __init__(self):
        self.new_engine = WincasaQueryEngine()
        self.legacy_engine = LegacyEngine()
        
    def process_with_shadow(self, query: str, user_id: str):
        # Hauptantwort vom alten System
        legacy_response = self.legacy_engine.process(query)
        
        # Parallel neues System testen (keine User-Ausgabe)
        try:
            new_response = self.new_engine.process_query(query, user_id)
            self.log_comparison(query, legacy_response, new_response)
        except Exception as e:
            self.log_error(query, str(e))
        
        return legacy_response  # User sieht nur Legacy-Result
```

#### Woche 6: Feature Flag Rollout
```python
# feature_flags.py
class FeatureFlags:
    def __init__(self):
        self.flags = {
            "new_query_engine": {
                "enabled": True,
                "percentage": 1,  # Start with 1%
                "user_whitelist": ["admin", "testuser"]
            }
        }
    
    def is_enabled(self, flag: str, user_id: str) -> bool:
        config = self.flags.get(flag, {})
        
        if user_id in config.get("user_whitelist", []):
            return True
            
        if not config.get("enabled", False):
            return False
            
        # Hash-based percentage rollout
        user_hash = hash(user_id) % 100
        return user_hash < config.get("percentage", 0)

# Rollout Schedule:
# Tag 1: 1% users
# Tag 2: 5% users  
# Tag 3: 25% users
# Tag 4: 50% users
# Tag 5: 100% users
```

### Deliverables Phase 2.4
- [ ] Unified Query Engine
- [ ] Shadow Mode Testing (1 Woche)
- [ ] Feature Flag System
- [ ] Monitoring Dashboard
- [ ] Rollback Procedures
- [ ] Documentation & Training

## Monitoring & Metrics

### Key Performance Indicators
```python
METRICS = {
    "accuracy": "% korrekte Antworten (vs. Golden Set)",
    "latency": "Durchschnittliche Response-Zeit",
    "error_rate": "% fehlgeschlagene Queries", 
    "intent_accuracy": "% korrekte Intent-Klassifizierung",
    "template_coverage": "% Queries die Templates nutzen",
    "fallback_rate": "% Queries die zu Legacy fallen"
}
```

### Logging Strategy
```python
# query_logger.py
def log_query_execution(query: str, user_id: str, result: dict):
    log_entry = {
        "timestamp": datetime.utcnow(),
        "query": query,
        "user_id": hash(user_id),  # Anonymized
        "classification": result.get("classification"),
        "engine_used": result.get("engine"),  # template/rag/legacy
        "sql_generated": result.get("sql"),
        "execution_time_ms": result.get("timing"),
        "error": result.get("error"),
        "result_count": result.get("count")
    }
    
    # Ship to monitoring system
    send_to_monitoring(log_entry)
```

## Risk Mitigation

### Critical Risks
1. **Intent Router Fehler** → Hierarchical Fallback + Golden Set Testing
2. **SQL Injection** → Template Engine + Parameter Sanitization  
3. **Performance Regression** → Shadow Mode + Gradual Rollout
4. **Data Staleness (RAG)** → TTL-based Cache + Update Monitoring

### Rollback Strategy
```python
def emergency_rollback():
    """Sofortiger Rollback bei kritischen Fehlern"""
    FeatureFlags.set("new_query_engine", enabled=False)
    # Alle neuen Requests gehen sofort zu Legacy-Modi
    logger.critical("Emergency rollback activated")
```

## Success Criteria

### Phase 2.1 Success
- [ ] 30% Verbesserung Baseline-Metrics
- [ ] 5 funktionsfähige Database Views  
- [ ] Golden Set mit 100% Coverage

### Phase 2.2 Success  
- [ ] RAG-System beantwortet Lookup-Queries mit >90% Genauigkeit
- [ ] Token-Kosten <$0.01 pro Query
- [ ] A/B Test zeigt Verbesserung vs. Legacy

### Phase 2.3 Success
- [ ] Intent Router mit >85% Klassifizierungs-Genauigkeit
- [ ] 10 Templates decken 60% aller Queries ab
- [ ] Keine SQL-Injection Vulnerabilities

### Phase 2.4 Success
- [ ] 100% Rollout ohne kritische Fehler
- [ ] Gesamtverbesserung >50% vs. Baseline
- [ ] User Satisfaction Score >8/10

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 2.1 | Woche 1 | Optimierte Basis + Views |
| 2.2 | Woche 2 | Structured RAG Prototype |
| 2.3 | Woche 3-4 | Template System + Intent Router |
| 2.4 | Woche 5-6 | Integration + Rollout |

**Total Duration: 6 Wochen**
**Total Effort: ~200 Personenstunden**

## Next Steps

1. **Sofort**: Golden Set erstellen und Baseline messen
2. **Woche 1**: Database Views implementieren
3. **Review-Points**: Nach jeder Phase Go/No-Go Entscheidung
4. **Monitoring**: Kontinuierliche Metriken-Überwachung

---

*Phase 2 ist darauf ausgelegt, das bestehende System pragmatisch zu verbessern, ohne es komplett zu ersetzen. Der schrittweise Ansatz minimiert Risiken und ermöglicht schnelle Korrekturen bei Problemen.*