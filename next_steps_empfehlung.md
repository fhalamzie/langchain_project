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

### **Sofort (1-2 Tage)**
1. **System Prompt Update**: HV-Domain Wissen integrieren
2. **Modi-Mapping**: Klare Definition der 3 neuen Modi
3. **Quick Win**: Contextual Embeddings für BEWOHNER-Tabelle testen

### **Kurzfristig (3-5 Tage)**
1. **Intelligent RAG Modus**: Enhanced + FAISS + TAG zusammenführen
2. **Hybrid Search**: Semantic + Keyword Search implementieren
3. **Reranking**: Cross-encoder für bessere Präzision

### **Mittelfristig (1-2 Wochen)**
1. **Agentic Modus**: LangChain + LangGraph konsolidieren
2. **Performance Testing**: A/B Test alte vs. neue Architektur
3. **Business Logic**: HV-spezifische Testszenarien

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