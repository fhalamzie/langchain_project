# WINCASA Implementierungsaufgaben

## Aktuelle Priorität: Strukturelle Modi-Optimierung (Januar 2025)

### ✅ Vollständig Implementiert

#### TAG-Modell (SYN→EXEC→GEN Pipeline)
**Status**: ✅ Abgeschlossen
- TAG Synthesizer für Query-Klassifikation und SQL-Schema-Erkennung  
- SQL-Validator mit sqlglot für Firebird-Syntax-Prüfung
- TAG Generator für strukturierte deutsche Antworten
- TAG Pipeline mit fokussiertem Embedding-System  
- LangGraph Workflow für komplexe Multi-Step-Queries
- ~90% SQL-Generierungsgenauigkeit erreicht

#### Core System Features
**Status**: ✅ Abgeschlossen  
- 6 Retrieval-Modi: Enhanced, FAISS, None, LangChain, TAG, LangGraph
- Direct FDB Interface mit Connection Pooling
- Phoenix OTEL Monitoring mit SQLite Backend
- Business Glossar mit JOIN-Reasoning
- Testing Framework (13/13 Tests, 0.02s Ausführung)
- Code Quality Tools (Black, isort, flake8, bandit)

---

### 🔧 Aktuelle Entwicklungsphase: Strukturelle Modi-Optimierung

**Fortschritt**: 5/6 Modi erfolgreich optimiert (83% abgeschlossen)

**✅ Optimierte Modi:**
- **Enhanced**: ✅ Information Overload gelöst (81% Document Reduction)
- **FAISS**: ✅ Semantic Gap behoben (100% Success Rate + HV-Terminologie-Mapping)
- **None**: ✅ Statischer Context ersetzt (273% Context Richness + Dynamic Schema)
- **LangChain**: ✅ Schema Overload behoben (97.2% Schema Reduction + Filtered Agent)
- **TAG**: ✅ Statische Regeln ersetzt (ML-Klassifikation + 100% Query-Type-Erweiterung)

**🔄 Ausstehende Modi:**
- **LangGraph**: Over-Engineering → Komplexitätsevaluierung + Workflow-Optimierung

## ✅ Abgeschlossen

- Core System mit 5 Retrieval-Modi implementiert und funktionsfähig
- Testing Framework mit 13/13 bestandenen Tests (0,02s Ausführung)
- Datenbank-Integration mit direkter FDB-Schnittstelle und Connection-Pooling
- Business-Logik mit erweitertem Business-Glossar und JOIN-Reasoning
- Schema-Analyse mit FK-Graph-Analyzer und NetworkX
- Monitoring mit Phoenix OTEL-Integration und SQLite-Backend
- Code-Qualität mit Black, isort, flake8, bandit konfiguriert

## ⏳ Ausstehend

### 🔧 Phase 1: Strukturelle Modi-Optimierung (6 Modi)

#### Aufgabe 1.1: Enhanced → Contextual Enhanced ⚡ HOHE PRIORITÄT
**Problem**: Information Overload durch statische 9-Dokument-Auswahl
**Lösung**: Query-Type + Contextual Retrieval + Business Context
**Geschätzt**: 5 Tage
**Status**: ✅ **ABGESCHLOSSEN**

**✅ Implementierte Verbesserungen**:
- **81.2% Document Reduction**: Von 9 statischen auf 1-2 relevante Dokumente
- **59.5% Context Reduction**: Information Overload gelöst
- **Query-Type Classification**: address_lookup, owner_lookup, financial_query, property_count
- **HV-Domain Contextual Chunks**: Business-Kontext angereicherte Dokumentation
- **Anthropic-style Enrichment**: Technische Details + Business Purpose + Relationships

**Erfolgskriterium**: ✅ **ERREICHT** - Bessere Präzision bei reduziertem Kontext

---

#### Aufgabe 1.2: FAISS → Hybrid FAISS ⚡ HOHE PRIORITÄT
**Problem**: Semantic Gap - versteht HV-Business-Logic nicht
**Lösung**: Semantic + Keyword + HV-Terminologie-Mapping
**Geschätzt**: 5 Tage
**Status**: ✅ **ABGESCHLOSSEN**

**✅ Implementierte Verbesserungen**:
- **100% Success Rate**: Alle Queries finden korrekte Tabellen
- **30% Faster Retrieval**: Optimierte Performance (0.895s vs 1.280s)
- **HV-Terminologie-Mapping**: "Mieter"→BEWOHNER, "Eigentümer"→EIGENTUEMER funktional
- **Hybrid Search**: BM25 Keyword + FAISS Semantic Search optimal kombiniert
- **Domain-Enhanced Embeddings**: HV-spezifische Terms integriert
- **Semantic Gap gelöst**: Versteht jetzt Hausverwaltungs-Business-Logic

**Erfolgskriterium**: ✅ **ERREICHT** - Findet "BEWOHNER" perfekt bei Query "Mieter"

---

#### Aufgabe 1.3: None → Smart Fallback ⚡ HOHE PRIORITÄT
**Problem**: Zu statisch, veralteter Global Context
**Lösung**: Dynamic Schema + HV-Domain Prompt + Pattern Learning
**Geschätzt**: 5 Tage
**Status**: ✅ **ABGESCHLOSSEN**

**✅ Implementierte Verbesserungen**:
- **273% Context Richness**: Von statischen 484 auf durchschnittlich 1806 Zeichen relevanter Kontext
- **Live Dynamic Schema**: Aktuelles Schema mit Zeilenzahlen statt veralteter statischer Info
- **HV-Domain System Prompt**: WINCASA-spezifische Geschäftslogik integriert
- **Pattern Learning Active**: Erfolgreiche Query-SQL-Pairs als Fallback-Examples
- **6/6 Features verbessert**: Alle geplanten Verbesserungen implementiert
- **Firebird-Specific Rules**: FIRST statt LIMIT, etc.

**Erfolgskriterium**: ✅ **ERREICHT** - Robuster Fallback mit aktuellem Schema-Wissen

---

#### Aufgabe 1.4: LangChain → Filtered Agent ⚡ HOHE PRIORITÄT
**Problem**: Schema Overload - lädt alle 151 Tabellen
**Lösung**: Query-Type-spezifische Schema-Filterung + Business Logic
**Geschätzt**: 5 Tage
**Status**: ✅ **ABGESCHLOSSEN**

**✅ Implementierte Verbesserungen**:
- **97.2% Schema Reduction**: Von 151 auf durchschnittlich 4.2 relevante Tabellen
- **94.4% Query Classification Accuracy**: 6 Query-Types (address_lookup, owner_lookup, financial_query, property_count, resident_info, maintenance_requests)
- **Business Logic Integration**: HV-spezifische SQL-Patterns in Agent Prompt integriert
- **Connection Pooling**: QueuePool mit 5+10 Connections, 1h Recycle-Zeit
- **Firebird Optimizations**: UTF8 Charset, Dialect 3, 30s Timeout, Retry Logic
- **100% Test Success Rate**: Alle 5 Tests bestanden (Query Classification, Table Filtering, Business Logic, Integration, Performance)

**Erfolgskriterium**: ✅ **ERREICHT** - Agent Power ohne Schema Overwhelm

---

#### Aufgabe 1.5: TAG → Adaptive TAG ⚡ HOHE PRIORITÄT
**Problem**: Statische Regeln, begrenzte Query-Type-Coverage
**Lösung**: ML-basierte Klassifikation + Dynamic Schema Discovery
**Geschätzt**: 7 Tage
**Status**: ✅ **ABGESCHLOSSEN**

**✅ Implementierte Verbesserungen**:
- **ML-basierte Query-Klassifikation**: TF-IDF + Naive Bayes mit 70-95% Confidence Scores
- **100% Coverage-Erweiterung**: Von 5 auf 10 Query-Types (address_lookup, resident_lookup, owner_lookup, property_queries, financial_queries, count_queries, relationship_queries, temporal_queries, comparison_queries, business_logic_queries)
- **Dynamic Schema Discovery**: Automatische Tabellen-Relationship-Erkennung aus erfolgreichen SQL-Ausführungen
- **Self-Learning System**: Kontinuierliche Verbesserung durch Query-Success/Failure-Feedback
- **Enhanced Entity Extraction**: Deutsche HV-spezifische Begriffe (Straßennamen, PLZ, Eigentümer, etc.)
- **Confidence-based Fallback**: Automatische Fallback-Strategien bei niedrigen Confidence-Scores

**✅ Teilaufgaben abgeschlossen**:
1. **ML-basierte Query-Klassifikation** ✅ - scikit-learn Pipeline mit TF-IDF Vectorizer + MultinomialNB
2. **Dynamic Schema Discovery** ✅ - Lernt Tabellen-Beziehungen aus SQL-Patterns und speichert für Wiederverwendung  
3. **Extended Query-Type Coverage** ✅ - 10 Query-Types mit spezialisierten SQL-Templates

**Erfolgskriterium**: ✅ **ERREICHT** - Adaptive Classification + umfassende Coverage funktional

---

#### Aufgabe 1.6: LangGraph → Complexity Evaluation ⚡ MITTLERE PRIORITÄT
**Problem**: Over-Engineering für meist einfache SQL-Queries
**Lösung**: Evaluate ob Workflow-Komplexität gerechtfertigt ist
**Geschätzt**: 4 Tage
**Status**: Ausstehend

**Teilaufgaben**:
1. **Use Case Analysis** (1 Tag)
   - Welche Queries profitieren wirklich von Workflows?
   - Multi-Step vs. Single-Step Query Classification
2. **Workflow Simplification** (2 Tage)
   - Minimale notwendige States definieren
   - Unnötige Workflow-Komplexität entfernen
3. **Integration Decision** (1 Tag)
   - Entweder: Simplify zu nützlichen Workflows
   - Oder: In LangChain Modus integrieren

**Erfolgskriterium**: Klare Entscheidung über LangGraph's Zukunft

---

### 🤝 Phase 2: Modi-Kombinationen (Modi 7-9)

#### Aufgabe 2.1: Modus 7 - Smart Enhanced (Enhanced + TAG) ⚡ HOHE PRIORITÄT
**Konzept**: TAG's Query-Classification + Enhanced's Multi-Document Retrieval
**Geschätzt**: 3 Tage
**Status**: Ausstehend
**Abhängigkeiten**: Aufgaben 1.1, 1.5

**Teilaufgaben**:
1. **TAG-Enhanced Integration** (2 Tage)
   - TAG's Query-Classification für Enhanced-Doc-Auswahl
   - 3-4 relevante Docs statt 9 laden
2. **Performance Validation** (1 Tag)
   - A/B Test gegen Enhanced und TAG einzeln
   - Synergieeffekte messen

**Erfolgskriterium**: Präzision von TAG + Content-Reichtum von Enhanced

---

#### Aufgabe 2.2: Modus 8 - Guided Agent (LangChain + TAG) ⚡ HOHE PRIORITÄT
**Konzept**: TAG's Schema-Filtering + LangChain's Agent-Reasoning
**Geschätzt**: 3 Tage
**Status**: Ausstehend
**Abhängigkeiten**: Aufgaben 1.4, 1.5

**Teilaufgaben**:
1. **TAG-LangChain Integration** (2 Tage)
   - TAG's Schema-Filtering für LangChain Agent
   - Nur relevante Tabellen an Agent weitergeben
2. **Business Logic Bridge** (1 Tag)
   - TAG's Business Context in Agent Prompt
   - Seamless integration testen

**Erfolgskriterium**: Agent Power ohne Schema Overload

---

#### Aufgabe 2.3: Modus 9 - Contextual Vector (FAISS + TAG) ⚡ HOHE PRIORITÄT
**Konzept**: TAG's Schema-Context + FAISS's Vector Similarity
**Geschätzt**: 3 Tage
**Status**: Ausstehend
**Abhängigkeiten**: Aufgaben 1.2, 1.5

**Teilaufgaben**:
1. **Context-Enhanced Vector Search** (2 Tage)
   - TAG's Query-Context als FAISS-Priming
   - Context-biased similarity search
2. **Hybrid Context Integration** (1 Tag)
   - TAG-Schema + FAISS-Docs kombinieren
   - Optimal weighting strategy

**Erfolgskriterium**: Strukturiertes + Emergentes Wissen

---

### 🧪 Phase 3: Evaluation & Architektur-Entscheidung

#### Aufgabe 3.1: Comprehensive 9-Modi Testing ⚡ HOHE PRIORITÄT
**Geschätzt**: 5 Tage
**Status**: Ausstehend
**Abhängigkeiten**: Alle Phase 1 & 2 Aufgaben

**Teilaufgaben**:
1. **9-Modi Performance Matrix** (2 Tage)
   - Alle 11 Standardabfragen gegen alle 9 Modi
   - SQL-Genauigkeit, Response-Zeit, Business Logic
2. **Business Scenario Testing** (2 Tage)
   - HV-spezifische komplexe Szenarien
   - Real-world Query patterns
3. **Architektur-Empfehlung** (1 Tag)
   - Finale Ranking und Empfehlung für Production
   - Trade-off Analyse: Performance vs. Komplexität

**Erfolgskriterium**: Klare Production-Architektur-Entscheidung

## 🎯 Erfolgskriterien

- SQL-Generierungsgenauigkeit: 20% → 90%
- Tabellenauswahl: >95% korrekte Identifikation
- Adressabfragen: 100% korrekte LIKE-Muster-Verwendung statt exakter Übereinstimmung
- Geschäftslogik: >90% korrekte Begriff-zu-Tabelle-Zuordnung
- Antwortzeit: <10s für komplexe Abfragen, <5s für einfache Abfragen