# Strukturelle Modi-Optimierung - Implementierungsplan

## 🎯 Übergeordnete Strategie

**Phase 1**: Strukturelle Optimierung aller 6 bestehenden Modi
**Phase 2**: Implementation der vielversprechendsten Kombinationen (Modi 7-9)
**Phase 3**: Performance-Vergleich und finale Architektur-Entscheidung

---

## 📋 Phase 1: Strukturelle Optimierung (6 Modi)

### **Modus 1: Enhanced → Contextual Enhanced**
**Problem**: Information Overload durch statische 9-Dokument-Auswahl
**Lösung**: Query-Type + Contextual Retrieval + Business Context

#### Tasks:
- [ ] **Task 1.1**: HV-Domain Contextual Chunks erstellen
  - Anreichern von Top-10 Tabellen-Docs mit Geschäftskontext
  - Format: Technical Details + Business Purpose + Relationships
  - Timeframe: 2 Tage

- [ ] **Task 1.2**: Query-Type-basierte Dokumentfilterung
  - Enhanced's 9 Docs nach Query-Type kategorisieren
  - address_lookup → 3 Docs, financial → 3 Docs, owner → 3 Docs
  - Timeframe: 1 Tag

- [ ] **Task 1.3**: Contextual Retrieval Pipeline
  - Anthropic-style chunk enrichment implementieren
  - Integration in bestehende Enhanced-Architektur
  - Timeframe: 2 Tage

**Erfolgskriterium**: Bessere Präzision bei gleicher Content-Qualität

---

### **Modus 2: FAISS → Hybrid FAISS**
**Problem**: Semantic Gap - versteht HV-Business-Logic nicht
**Lösung**: Semantic + Keyword + HV-Terminologie-Mapping

#### Tasks:
- [ ] **Task 2.1**: HV-Business-Terminologie-Dictionary
  - Mapping: "Mieter"→BEWOHNER, "Eigentümer"→EIGENTUEMER, etc.
  - Synonym-Expansion für Embeddings
  - Timeframe: 1 Tag

- [ ] **Task 2.2**: Hybrid Search Implementation
  - BM25 Keyword Search + FAISS Semantic Search
  - Gewichtete Kombination der Ergebnisse
  - Timeframe: 2 Tage

- [ ] **Task 2.3**: Domain-Enhanced Embeddings
  - HV-spezifische Terms in Embedding-Pipeline
  - Re-embedding kritischer Dokumente mit Business-Context
  - Timeframe: 2 Tage

**Erfolgskriterium**: Findet "BEWOHNER" auch bei Query "Mieter"

---

### **Modus 3: None → Smart Fallback**
**Problem**: Zu statisch, veralteter Global Context
**Lösung**: Dynamic Schema + HV-Domain Prompt + Pattern Learning

#### Tasks:
- [ ] **Task 3.1**: Dynamic Schema Loading
  - Live DB-Schema-Extraktion statt statischer Context
  - Table relationships und FK-Info dynamisch laden
  - Timeframe: 2 Tage

- [ ] **Task 3.2**: HV-Domain System Prompt
  - WINCASA-spezifischer System Prompt mit Geschäftslogik
  - Integration von Hausverwaltungs-Geschäftsregeln
  - Timeframe: 1 Tag

- [ ] **Task 3.3**: Query Pattern Learning
  - Häufige Query-Patterns erkennen und optimieren
  - Erfolgreiche Query-SQL-Pairs als Fallback-Examples
  - Timeframe: 2 Tage

**Erfolgskriterium**: Robuster Fallback mit aktuellem Schema-Wissen

---

### **Modus 4: LangChain → Filtered Agent**
**Problem**: Schema Overload - lädt alle 151 Tabellen
**Lösung**: Query-Type-spezifische Schema-Filterung + Business Logic

#### Tasks:
- [ ] **Task 4.1**: Schema-Filtering Pipeline
  - Query-Analysis zur Tabellen-Relevanz-Bestimmung
  - Nur 3-8 relevante Tabellen statt alle 151 laden
  - Timeframe: 2 Tage

- [ ] **Task 4.2**: Business Logic Integration
  - HV-Geschäftsregeln in Agent Tools
  - Hausverwaltungs-spezifische SQL-Patterns
  - Timeframe: 2 Tage

- [ ] **Task 4.3**: Firebird Connection Optimization
  - Connection pooling und retry logic verbessern
  - Firebird-spezifische Optimierungen
  - Timeframe: 1 Tag

**Erfolgskriterium**: Agent Power ohne Schema Overwhelm

---

### **Modus 5: TAG → Adaptive TAG**
**Problem**: Statische Regeln, begrenzte Query-Type-Coverage
**Lösung**: ML-basierte Klassifikation + Dynamic Schema Discovery

#### Tasks:
- [ ] **Task 5.1**: ML-basierte Query-Klassifikation
  - Ersetze regelbasierte durch lernende Klassifikation
  - Training mit bestehenden Query-Examples
  - Timeframe: 3 Tage

- [ ] **Task 5.2**: Dynamic Schema Discovery
  - Automatische Tabellen-Relationship-Erkennung
  - Schema-Pattern-Learning aus successful queries
  - Timeframe: 2 Tage

- [ ] **Task 5.3**: Extended Query-Type Coverage
  - Von 4-5 auf 10+ Query-Types erweitern
  - Edge cases und komplexe Queries abdecken
  - Timeframe: 2 Tage

**Erfolgskriterium**: Adaptive Classification + umfassende Coverage

---

### **Modus 6: LangGraph → Complexity Evaluation**
**Problem**: Over-Engineering für meist einfache SQL-Queries
**Lösung**: Evaluate ob Workflow-Komplexität gerechtfertigt ist

#### Tasks:
- [ ] **Task 6.1**: Use Case Analysis
  - Welche Queries profitieren wirklich von Workflows?
  - Multi-Step vs. Single-Step Query Classification
  - Timeframe: 1 Tag

- [ ] **Task 6.2**: Workflow Simplification
  - Minimale notwendige States definieren
  - Unnötige Workflow-Komplexität entfernen
  - Timeframe: 2 Tage

- [ ] **Task 6.3**: Integration Decision
  - Entweder: Simplify zu nützlichen Workflows
  - Oder: In LangChain Modus integrieren
  - Performance/Komplexität Trade-off bewerten
  - Timeframe: 1 Tag

**Erfolgskriterium**: Klare Entscheidung über LangGraph's Zukunft

---

## 📋 Phase 2: Modi-Kombinationen (Modi 7-9)

### **Modus 7: Smart Enhanced (Enhanced + TAG)**
#### Tasks:
- [ ] **Task 7.1**: TAG-Enhanced Integration
  - TAG's Query-Classification für Enhanced-Doc-Auswahl
  - 3-4 relevante Docs statt 9 laden
  - Timeframe: 2 Tage

- [ ] **Task 7.2**: Performance Validation
  - A/B Test gegen Enhanced und TAG einzeln
  - Synergieeffekte messen
  - Timeframe: 1 Tag

### **Modus 8: Guided Agent (LangChain + TAG)**
#### Tasks:
- [ ] **Task 8.1**: TAG-LangChain Integration
  - TAG's Schema-Filtering für LangChain Agent
  - Nur relevante Tabellen an Agent weitergeben
  - Timeframe: 2 Tage

- [ ] **Task 8.2**: Business Logic Bridge
  - TAG's Business Context in Agent Prompt
  - Seamless integration testen
  - Timeframe: 1 Tag

### **Modus 9: Contextual Vector (FAISS + TAG)**
#### Tasks:
- [ ] **Task 9.1**: Context-Enhanced Vector Search
  - TAG's Query-Context als FAISS-Priming
  - Context-biased similarity search
  - Timeframe: 2 Tage

- [ ] **Task 9.2**: Hybrid Context Integration
  - TAG-Schema + FAISS-Docs kombinieren
  - Optimal weighting strategy
  - Timeframe: 1 Tag

---

## 📋 Phase 3: Evaluation & Entscheidung

### **Comprehensive Testing**
- [ ] **Task E.1**: 9-Modi Performance Matrix
  - Alle 11 Standardabfragen gegen alle 9 Modi
  - SQL-Genauigkeit, Response-Zeit, Business Logic
  - Timeframe: 2 Tage

- [ ] **Task E.2**: Business Scenario Testing
  - HV-spezifische komplexe Szenarien
  - Real-world Query patterns
  - Timeframe: 2 Tage

- [ ] **Task E.3**: Architektur-Empfehlung
  - Finale Ranking und Empfehlung für Production
  - Trade-off Analyse: Performance vs. Komplexität
  - Timeframe: 1 Tag

---

## 📊 Gesamtumfang

**Phase 1**: ~18 Tage (6 Modi strukturell optimieren)
**Phase 2**: ~7 Tage (3 Modi-Kombinationen)
**Phase 3**: ~5 Tage (Evaluation)
**TOTAL**: ~30 Tage (6 Wochen)

**Deliverable**: 9 optimierte Modi + finale Architektur-Empfehlung für Production