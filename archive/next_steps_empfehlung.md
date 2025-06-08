# Nächste Schritte - Empfehlung

## 🎯 Kernproblem: Zu viele redundante Modi

**Aktuell**: 6 Modi mit Überschneidungen
**Optimal**: 3 fokussierte Modi mit klaren Anwendungsfällen

## 📊 Konzeptionelle Verbesserungen

### 1. **Modi-Konsolidierung** (HÖCHSTE PRIORITÄT)

```
ALT (6 Modi):                    NEU (3 Modi):
├── Enhanced (Multi-RAG)         ├── 🧠 Intelligent RAG
├── FAISS (Vector)              │   ├── Query Classification (TAG)
├── TAG (Focused)           →   │   ├── Contextual Embeddings (Anthropic)
├── LangChain (Agent)           │   └── Hybrid Search + Reranking
├── LangGraph (Workflow)    →   ├── 🤖 Agentic Mode (LangChain+Graph)
└── None (Fallback)         →   └── ⚡ Fast Fallback (Enhanced None)
```

### 2. **Contextual Retrieval Integration** (Anthropic-Ansatz)

**Problem**: Chunks verlieren Kontext beim Embedding
**Lösung**: Chunk-spezifischen Kontext hinzufügen

```python
# Vorher:
"BEWOHNER table has columns BWO, BNAME, BSTR..."

# Nachher: 
"KONTEXT: BEWOHNER-Tabelle in WINCASA Hausverwaltung für Mieterdaten.
VERWENDUNG: Adressabfragen, Kontaktdaten, Vertragsverknüpfung.
BEZIEHUNG: ONR verknüpft mit OBJEKTE.
DETAILS: BEWOHNER table has columns BWO (Bewohner-ID), BNAME (Nachname), BSTR (Straße+Hausnummer)..."
```

### 3. **HV Software Domain Integration**

**Fehlender Kontext**: System kennt WINCASA-Domäne nicht ausreichend
**Lösung**: Hausverwaltungs-spezifischen System Prompt

```python
HV_DOMAIN_PROMPT = """
WINCASA HAUSVERWALTUNG KONTEXT:
- Software für professionelle Immobilienverwaltung
- ONR (Objektnummer): Zentraler Verknüpfungsschlüssel
- Hierarchie: OBJEKTE (Gebäude) → WOHNUNG (Einheiten) → BEWOHNER (Mieter)
- Eigentumsverhältnisse: EIGENTUEMER → VEREIG → OBJEKTE
- Finanzmanagement: KONTEN → BUCHUNG → SOLLSTELLUNG

TYPISCHE GESCHÄFTSLOGIK:
- "Mieter" = BEWOHNER Tabelle
- "Vermieter/Eigentümer" = EIGENTUEMER + VEREIG
- "Immobilie/Objekt" = OBJEKTE + WOHNUNG
- "Miete/Nebenkosten" = KONTEN + BUCHUNG
"""
```

## 🚀 Implementierungsplan

### **✅ Phase 1 COMPLETED: Strukturelle Optimierung (6/6 Modi)**
- ✅ Task 1: Enhanced → Contextual Enhanced (completed)
- ✅ Task 2: FAISS → Hybrid FAISS (completed) 
- ✅ Task 3: None → Smart Fallback (completed)
- ✅ Task 4: LangChain → Filtered Agent (completed)
- ✅ Task 5: TAG → Adaptive TAG (completed)
- ✅ Task 6: LangGraph → REMOVED (evaluation complete)

### **🎯 Phase 2 CURRENT: Modi-Kombinationen (3 Prioritäten)**

#### **Kombination 1: Enhanced + TAG = "Smart Enhanced"** (Priorität 1)
- TAG's Query-Klassifikation für Enhanced-Doc-Auswahl
- 3-4 relevante Docs statt 9 laden
- Timeframe: 2-3 Tage

#### **Kombination 2: LangChain + TAG = "Guided Agent"** (Priorität 2)  
- TAG's Schema-Filtering für LangChain Agent
- Nur relevante Tabellen (3-5 statt 151) an Agent
- Timeframe: 2-3 Tage

#### **Kombination 3: FAISS + TAG = "Contextual Vector"** (Priorität 3)
- TAG's Query-Context als FAISS-Priming
- Context-biased similarity search
- Timeframe: 2-3 Tage

### **Phase 3: Performance Testing & Evaluation**
1. **9-Modi Performance Matrix**: Alle Modi gegen 11 Standardabfragen
2. **Business Scenario Testing**: HV-spezifische komplexe Szenarien
3. **Architektur-Empfehlung**: Finale Ranking für Production

## 💡 Konkrete nächste Aktion

**Vorschlag**: Beginnen wir mit dem System Prompt Update und einem Quick Test:

1. **HV-Domain System Prompt** erstellen
2. **Contextual Embeddings** für 2-3 wichtige Tabellen testen
3. **Performance Vergleich** mit aktueller TAG-Implementation

**Ziel**: Schnell validieren, dass der konzeptionelle Ansatz funktioniert, bevor wir größere Refactoring-Arbeiten machen.

## 🔍 Was denkst du?

- Macht die 6→3 Modi Konsolidierung Sinn?
- Sollen wir mit System Prompt + HV-Domain starten?
- Priorität auf Contextual Retrieval oder Hybrid Search?