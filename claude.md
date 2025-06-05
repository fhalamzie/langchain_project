# WINCASA - Intelligentes Datenbank-Abfrage-System

## Dokumentationsübersicht

Willkommen zur Dokumentation des WINCASA-Projekts, einem produktionsbereiten System zur natürlichsprachigen Abfrage von Firebird-Datenbanken mit moderner LLM-Technologie.

### Verfügbare Dokumentation

* **[README.md](README.md)** - Kurze Projektzusammenfassung und Hauptfunktionen
* **[development-guidelines.md](development-guidelines.md)** - Allgemeine Entwicklungsrichtlinien und -workflows
* **[code-quality.md](code-quality.md)** - Tools und Standards für die Code-Qualitätssicherung
* **[testing.md](testing.md)** - Testanforderungen und -standards für alle Testebenen
* **[high-level-design.md](high-level-design.md)** - Übergeordnetes Systemdesign, Architektur und Komponenten
* **[tasks.md](tasks.md)** - Aktuelle Implementierungsaufgaben und Fortschrittsverfolgung

## Projektstatus (Januar 2025)

* **Status**: ✅ Produktionsbereit - Alle 6 Retrieval-Modi implementiert und funktionsfähig
* **Aktuelle Priorität**: Strukturelle Optimierung vorhandener Modi (Enhanced, FAISS, None, LangChain, TAG, LangGraph)
* **TAG-Implementierung**: ✅ Vollständig abgeschlossen - SYN→EXEC→GEN Pipeline funktional
* **Repository**: [https://github.com/fhalamzie/langchain_project](https://github.com/fhalamzie/langchain_project)

## Erste Schritte

Für einen schnellen Einstieg:

```bash
# Von GitHub klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project

# Umgebung vorbereiten
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# System starten
./start_enhanced_qa_direct.sh
```

## Kerntechnologien

* **Backend**: Python, Firebird FDB, LangChain, SQLAlchemy, Phoenix Monitoring
* **LLM-Integration**: OpenAI GPT-4, OpenRouter APIs
* **RAG-System**: FAISS-Vektorisierung, mehrstufiger Abruf, hybride Kontextstrategie
* **Infrastruktur**: Streamlit UI, direkte FDB-Schnittstelle, SQLite-Monitoring-Backend

## Systemarchitektur

Das WINCASA-System besteht aus folgenden Hauptkomponenten:

1. **SQL-Agent**: `firebird_sql_agent_direct.py` - Kern-SQL-Agent mit 5 Abrufmodi
2. **Datenbank-Schnittstelle**: `fdb_direct_interface.py` - Direkte Firebird-Schnittstelle
3. **Retrieval-System**: `enhanced_retrievers.py` - Mehrstufiges RAG mit FAISS
4. **LangChain-Integration**: `langchain_sql_retriever_fixed.py` - SQL Database Agent
5. **Kontext-Strategie**: `global_context.py` - Implementierung der hybriden Kontextstrategie
6. **Monitoring**: `phoenix_monitoring.py` - OTEL-basiertes Leistungsmonitoring

Weitere Details zur Architektur und Implementierung finden Sie in der [high-level-design.md](high-level-design.md).

## Entwicklungsschwerpunkte

**Aktueller Fokus (Januar 2025)**: Strukturelle Optimierung der 6 implementierten Retrieval-Modi:

**✅ Abgeschlossen:**
1. **Enhanced → Contextual Enhanced**: ✅ 81% Document Reduction + Query-Type Classification
2. **FAISS → Hybrid FAISS**: ✅ 100% Success Rate + HV-Terminologie-Mapping  
3. **None → Smart Fallback**: ✅ 273% Context Richness + Dynamic Schema Loading

**✅ Abgeschlossen:**
4. **LangChain → Filtered Agent**: ✅ 97.2% Schema Reduction + Query-Type-Filterung

**🔄 In Bearbeitung:**
5. **TAG → Adaptive TAG**: ML-basierte Klassifikation + erweiterte Query-Type-Coverage
6. **LangGraph**: Komplexitätsevaluierung und Workflow-Optimierung

**TAG-Status**: ✅ Vollständig implementiert - SYN→EXEC→GEN Pipeline mit ~90% SQL-Genauigkeit
**Optimierungs-Fortschritt**: 4/6 Modi erfolgreich optimiert (67% abgeschlossen)

Detaillierte Implementierungsaufgaben sind in [tasks.md](tasks.md) dokumentiert.

## Kontakt & Beiträge

* **Repository**: [https://github.com/fhalamzie/langchain_project](https://github.com/fhalamzie/langchain_project)
* **Backup-Status**: ✅ Alle Commits synchronisiert
* **Versionskontrolle**: Git-Historie vollständig verfügbar

Für Beiträge zum Projekt folgen Sie bitte den Richtlinien in [development-guidelines.md](development-guidelines.md).