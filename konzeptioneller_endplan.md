# Konzeptioneller Endplan - Modi Optimierung

## 🎯 Übergeordnetes Ziel
**Jeden Modus zu seiner strukturell optimalen Form entwickeln** durch:
1. Behebung identifizierter struktureller Schwächen
2. Integration von HV-Domain-Wissen in alle Modi
3. Selektive Anwendung moderner RAG-Techniken

---

## 📊 Modus-spezifische Optimierungsstrategien

### **Enhanced Modus → Contextual Enhanced**
**Problem**: Information Overload + Kontextverlust
**Lösung**: 
- ✅ **Contextual Retrieval**: Chunks mit HV-Geschäftskontext anreichern
- ✅ **Query-Type Filtering**: Nur relevante Dokumente basierend auf Query-Klassifikation
- ✅ **Business-Technical Bridge**: Geschäftslogik + technische Details verknüpfen

```python
enhanced_v2_strategy = {
    "pre_retrieval": "Query-Type klassifizieren",
    "retrieval": "3-5 relevante Docs statt 9",
    "post_retrieval": "Contextual enrichment pro Chunk",
    "expected_improvement": "Fokussiert + Business-Context"
}
```

### **FAISS Modus → Hybrid FAISS**
**Problem**: Semantic Gap + Missing Business Logic
**Lösung**:
- ✅ **Hybrid Search**: Semantic (Konzepte) + Keyword (exakte Terme)
- ✅ **Domain Embeddings**: HV-spezifische Begriffe in Embedding-Space
- ✅ **Business Synonym Mapping**: "Mieter"→BEWOHNER, "Eigentümer"→EIGENTUEMER

```python
faiss_v2_strategy = {
    "search_method": "semantic + BM25 hybrid",
    "embedding_enhancement": "HV domain fine-tuning",
    "business_mapping": "Synonym dictionary integration",
    "expected_improvement": "Bessere Business-Term Recognition"
}
```

### **None Modus → Smart Fallback**
**Problem**: Statisch + zu generisch
**Lösung**:
- ✅ **Dynamic Schema Info**: Live DB-Schema statt statischer Kontext
- ✅ **HV Domain Prompt**: Geschäftslogik-orientierter System Prompt
- ✅ **Query Pattern Learning**: Häufige Query-Patterns optimieren

```python
none_v2_strategy = {
    "context_source": "Dynamic schema + HV business rules",
    "prompt_enhancement": "Domain-specific system prompt",
    "adaptivity": "Learn from successful query patterns",
    "expected_improvement": "Robust fallback mit Domain-Wissen"
}
```

### **LangChain Modus → Filtered Agent**
**Problem**: Schema Overload + Missing Business Context
**Lösung**:
- ✅ **Smart Schema Filtering**: Nur relevante Tabellen basierend auf Query-Type
- ✅ **Business Logic Injection**: HV-Geschäftsregeln in Agent Tools
- ✅ **Connection Optimization**: Firebird-spezifische Optimierungen

```python
langchain_v2_strategy = {
    "schema_loading": "Query-type specific table subset",
    "business_context": "HV domain rules in agent prompt",
    "tool_enhancement": "Firebird-optimized database tools",
    "expected_improvement": "Focused agent mit Business Logic"
}
```

### **LangGraph Modus → Simplified Workflow** 
**Problem**: Over-Engineering + Unnecessary Complexity
**Lösung**:
- ⚠️ **Complexity Evaluation**: Ist Workflow-Overhead gerechtfertigt?
- ✅ **Query-specific Workflows**: Nur für komplexe Multi-Step Queries
- ✅ **Fallback Integration**: Einfache Queries an anderen Modus weiterleiten

```python
langgraph_v2_strategy = {
    "use_case_definition": "Nur für Multi-Step/Complex queries",
    "workflow_simplification": "Minimale notwendige States",
    "integration": "Fallback zu anderen Modi",
    "evaluation_metric": "Ist Komplexität gerechtfertigt?"
}
```

### **TAG Modus → Adaptive TAG**
**Problem**: Statische Regeln + Limited Coverage
**Lösung**:
- ✅ **ML-based Classification**: Lernende Query-Klassifikation
- ✅ **Dynamic Schema Discovery**: Automatische Schema-Pattern-Erkennung
- ✅ **Extended Coverage**: Mehr Query-Types abdecken

```python
tag_v2_strategy = {
    "classification": "ML-based statt regelbasiert",
    "schema_discovery": "Dynamic table relationship mapping",
    "coverage_expansion": "Neue Query-Types lernen",
    "expected_improvement": "Adaptive + umfassende Coverage"
}
```

---

## 🏢 HV-Domain Integration (übergreifend)

### **Universeller HV-Context für alle Modi**
```python
HV_DOMAIN_CONTEXT = """
WINCASA HAUSVERWALTUNGSSOFTWARE KONTEXT:

GESCHÄFTSMODELL:
- Professionelle Immobilienverwaltung
- Zentrale Objektverwaltung mit Mieter- und Eigentümerbeziehungen
- Finanzbuchhaltung für Mieten, Umlagen, Abrechnungen

DATENSTRUKTUR-LOGIK:
- ONR (Objektnummer): Zentraler Verknüpfungsschlüssel für alles
- Hierarchie: OBJEKTE (Gebäude) → WOHNUNG (Einheiten) → BEWOHNER (Mieter)
- Eigentum: EIGENTUEMER → VEREIG (Verknüpfung) → OBJEKTE
- Finanzen: KONTEN → BUCHUNG → SOLLSTELLUNG

BUSINESS-TERMINOLOGIE-MAPPING:
- "Mieter/Bewohner" = BEWOHNER Tabelle
- "Vermieter/Eigentümer" = EIGENTUEMER + VEREIG Tabellen
- "Wohnung/Apartment" = WOHNUNG Tabelle  
- "Gebäude/Immobilie" = OBJEKTE Tabelle
- "Miete/Nebenkosten" = KONTEN + BUCHUNG Tabellen

KRITISCHE GESCHÄFTSREGELN:
- Adressen IMMER mit LIKE-Mustern suchen (nie exakt)
- BSTR Format: "Straßenname Hausnummer" 
- BPLZORT Format: "PLZ Ort"
- ONR ist der Schlüssel für alle Beziehungen
"""
```

---

## 📋 Implementierungs-Roadmap

### **Phase 1: Domain Foundation** (2-3 Tage)
- [ ] HV-Domain System Prompt für alle Modi erstellen
- [ ] Business-Terminologie-Mapping implementieren
- [ ] Contextual Chunks für Top-5 Tabellen erstellen

### **Phase 2: Strukturelle Fixes** (1 Woche pro Modus)
- [ ] Enhanced → Contextual Enhanced (Query-Type + Contextual Retrieval)
- [ ] FAISS → Hybrid FAISS (Semantic + Keyword)
- [ ] None → Smart Fallback (Dynamic Schema + HV Prompt)
- [ ] LangChain → Filtered Agent (Schema Filtering + Business Logic)

### **Phase 3: Advanced Features** (2. Woche)
- [ ] TAG → Adaptive TAG (ML Classification)
- [ ] LangGraph Evaluation (Simplify or Integrate?)
- [ ] Cross-Modi Testing & Optimization

### **Phase 4: Performance Analysis** (3. Woche)
- [ ] A/B Testing aller verbesserter Modi
- [ ] Business Logic Validation mit HV-Szenarien
- [ ] Performance Benchmarking
- [ ] Final Modus-Ranking für Production

---

## 🎯 Erfolgskriterien

### **Strukturelle Verbesserungen**:
- ✅ Jeder Modus hat klare strukturelle Verbesserungen
- ✅ HV-Domain-Wissen ist überall integriert
- ✅ Moderne RAG-Techniken sind sinnvoll angewendet

### **Performance Verbesserungen**:
- ✅ SQL-Genauigkeit >85% für alle Modi
- ✅ Business-Logic-Verständnis messbar verbessert
- ✅ Response-Zeit stabil oder besser

### **Experimenteller Wert**:
- ✅ Klare Erkenntnisse über optimale Retrieval-Strategien
- ✅ Basis für finale Production-Architektur-Entscheidung
- ✅ Methodische Validation verschiedener Ansätze

**Endresultat**: 6 strukturell optimierte Modi als Basis für finale Architektur-Entscheidung