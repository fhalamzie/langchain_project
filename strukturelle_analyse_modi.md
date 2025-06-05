# Strukturelle Analyse der 6 Retrieval Modi

## 🔬 Strukturelle Probleme je Modus

### **Modus 1: Enhanced** (Multi-stage RAG)
**Struktur**: 9 Dokumente über mehrere Stufen
**Probleme**:
- ❌ **Information Overload**: 9 Dokumente zu viel für fokussierte Abfragen
- ❌ **Kontextverlust**: Chunks ohne Tabellenbeziehung-Kontext
- ❌ **Statische Auswahl**: Immer gleiche 9 Dokumente, unabhängig von Query-Type
- ❌ **Redundante Information**: Überschneidungen zwischen den 9 Dokumenten

**Strukturelle Ursache**: Retrieval ohne Query-Klassifikation

### **Modus 2: FAISS** (Vector Similarity)
**Struktur**: 4 ähnlichste Dokumente via Embedding
**Probleme**:
- ❌ **Semantic Gap**: Embeddings verstehen Business-Logik nicht (z.B. "Mieter" ≠ BEWOHNER)
- ❌ **Kontext-Fragmentierung**: Chunks verlieren Tabellenbeziehungen
- ❌ **Embedding Quality**: Standard Embeddings ohne Domain-Anpassung
- ❌ **Recall Problem**: Relevante Dokumente mit anderen Worten werden übersehen

**Strukturelle Ursache**: Embedding-Modell kennt HV-Domain nicht

### **Modus 3: None** (Global Context)
**Struktur**: Statischer globaler Kontext
**Probleme**:
- ❌ **Zu generisch**: Keine spezifischen Tabellendetails
- ❌ **Veralteter Kontext**: Statische Information, nicht datenbankaktuell
- ❌ **Missing Business Logic**: Keine HV-spezifischen Geschäftsregeln
- ❌ **Skalierungsproblem**: Kann nicht mit DB-Schema-Änderungen mithalten

**Strukturelle Ursache**: Statisches System ohne Dynamic Schema Loading

### **Modus 4: LangChain** (SQL Database Agent)
**Struktur**: Native SQL Agent mit Schema Introspection
**Probleme**:
- ❌ **Schema Überladung**: Lädt ALLE 151 Tabellen ins Working Memory
- ❌ **Fehlende Business-Context**: Technische Schema ≠ Geschäftslogik
- ❌ **Connection Issues**: Firebird-spezifische Verbindungsprobleme
- ❌ **Performance**: Schema-Introspection bei jeder Query

**Strukturelle Ursache**: Keine Query-Type-spezifische Schema-Filterung

### **Modus 5: LangGraph** (State Machine)
**Struktur**: Workflow-basierte SQL-Generierung
**Probleme**:
- ❌ **Komplexität ohne Nutzen**: Workflow-Overhead für einfache Queries
- ❌ **State Management**: Unnötige Komplexität für SQL-Generierung
- ❌ **Debugging**: Schwer nachvollziehbare Workflow-Pfade
- ❌ **Latenz**: Mehrere LLM-Calls pro Query

**Strukturelle Ursache**: Over-Engineering für das Problem

### **Modus 6: TAG** (Focused Context)
**Struktur**: Query-Type → Schema-Mapping → Focused Prompt
**Probleme**:
- ❌ **Statische Schemas**: Hardcoded Query-Type-Mappings
- ❌ **Limited Classification**: Nur 4-5 Query Types abgedeckt
- ❌ **Missing Fallback**: Unbekannte Query Types schlecht behandelt
- ❌ **Keine Adaptivität**: Lernt nicht aus Query-Patterns

**Strukturelle Ursache**: Regelbasierte statt lernende Klassifikation

---

## 🎯 RAG-Verbesserungen Bewertung

### **1. Contextual Retrieval** (Anthropic)
**Konzept**: Chunks mit erklärendem Kontext anreichern
**Passt zu unserem System**: ✅ **JA - HOCH**
```python
# Statt:
"BWO, BNAME, BSTR, BPLZORT"

# Besser:
"KONTEXT: BEWOHNER-Tabelle speichert Mieterdaten in WINCASA Hausverwaltung.
VERKNÜPFUNG: ONR verbindet mit Wohnung/Objekt. 
GESCHÄFTSLOGIK: BSTR='Straße+Nr', BPLZORT='PLZ+Ort'
TECHNISCH: BWO (ID), BNAME (Nachname), BSTR (Adresse), BPLZORT (Ort)"
```
**Anwendung**: Enhanced + FAISS Modi würden massiv profitieren

### **2. Hybrid Search** (Semantic + Keyword)
**Konzept**: Vector similarity + BM25 kombinieren
**Passt zu unserem System**: ✅ **JA - MITTEL**
- **Pro**: Findet "BEWOHNER" auch bei Query "Mieter" (semantic) und exakte Tabellennamen (keyword)
- **Con**: Zusätzliche Komplexität, möglicherweise overkill für strukturierte DB-Abfragen
**Anwendung**: FAISS Modus könnte davon profitieren

### **3. Reranking** (Cross-Encoder)
**Konzept**: Final reranking mit Query-Document-Pairs
**Passt zu unserem System**: ⚠️ **MAYBE - NIEDRIG**
- **Pro**: Bessere Präzision bei mehrdeutigen Queries
- **Con**: Weitere Latenz, DB-Abfragen meist eindeutig strukturiert
**Anwendung**: Nur für Enhanced Modus bei komplexen Queries

### **4. Query-Aware Chunking**
**Konzept**: Chunks basierend auf Query-Type strukturieren
**Passt zu unserem System**: ✅ **JA - HOCH**
```python
query_chunks = {
    "address_lookup": ["BEWOHNER_address", "BEWADR_mapping"],
    "financial": ["KONTEN_structure", "BUCHUNG_patterns"],
    "ownership": ["EIGENTUEMER_data", "VEREIG_relations"]
}
```
**Anwendung**: Perfekt für TAG Modus, könnte Enhanced ersetzen

---

## 🏢 Domain-Wissen Integration

### **Strukturelles Problem**: Fehlendes HV-Context
Alle Modi leiden unter **fehlendem Hausverwaltungs-Domain-Wissen**:

```python
# Aktuell: Technisch
"BEWOHNER table with columns BWO, BNAME..."

# Besser: Business + Technical
"""WINCASA HAUSVERWALTUNG - BEWOHNER (Mieter/Bewohner)

GESCHÄFTSZWECK: Verwaltung von Mietern und Bewohnern in Immobilien
ZENTRALE VERKNÜPFUNG: ONR (Objektnummer) verbindet mit Wohnung/Gebäude
TYPISCHE ABFRAGEN: Wer wohnt wo? Kontaktdaten? Mietverträge?

ADRESS-LOGIK (KRITISCH):
- BSTR: "Straßenname Hausnummer" (z.B. "Marienstraße 26") 
- BPLZORT: "PLZ Ort" (z.B. "45307 Essen")
- IMMER LIKE-Muster verwenden, NIE exakte Suche

TECHNISCHE STRUKTUR: BWO (Bewohner-ID), BNAME (Nachname), BVNAME (Vorname)..."""
```

---

## 📋 Strukturelle Verbesserungsansätze

### **Enhanced Modus** → **Contextual Enhanced**
- ✅ Contextual Retrieval implementieren
- ✅ Query-Type-spezifische Dokumentauswahl
- ✅ HV-Domain Kontext zu jedem Chunk

### **FAISS Modus** → **Hybrid FAISS**
- ✅ Hybrid Search (Semantic + Keyword)
- ✅ Domain-spezifische Embeddings
- ✅ HV-Business-Terminologie in Embeddings

### **None Modus** → **Smart Fallback**
- ✅ Dynamic Schema Loading
- ✅ HV-Domain System Prompt
- ✅ Query-Pattern-Learning für bessere Fallbacks

### **LangChain Modus** → **Filtered Agent**
- ✅ Query-Type-spezifische Schema-Filterung
- ✅ Nur relevante Tabellen laden
- ✅ HV-Business-Logic in Agent Prompt

### **LangGraph Modus** → **Simplified Workflow**
- ⚠️ Evaluieren: Ist Workflow-Komplexität gerechtfertigt?
- ✅ Falls ja: Query-Type-spezifische Workflows
- ❌ Falls nein: In LangChain Modus integrieren

### **TAG Modus** → **Adaptive TAG**
- ✅ Lernende Query-Klassifikation statt statische Regeln
- ✅ Dynamic Schema Discovery
- ✅ Erweiterte Query-Type-Abdeckung

---

## 🎯 Konzeptioneller Endplan

### **Ziel**: Jeden Modus zu seiner optimalen Form entwickeln
### **Methode**: Strukturelle Schwächen beheben, nicht Modi eliminieren
### **Fokus**: Domain-Wissen + moderne RAG-Techniken wo sinnvoll