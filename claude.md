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

## Projektstatus (Juni 2025)

* **Status**: ✅ Produktionsbereit - Alle Kernfunktionen implementiert und getestet
* **Aktuelle Priorität**: TAG-Modell-Implementierung zur Verbesserung der SQL-Generierungsgenauigkeit
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

Der aktuelle Entwicklungsschwerpunkt liegt auf der TAG-Modell-Implementierung zur Verbesserung der SQL-Generierungsgenauigkeit. Die TAG-Architektur (SYN→EXEC→GEN) soll die SQL-Generierungsgenauigkeit von aktuell ~20% auf >90% verbessern.

Detaillierte Implementierungsaufgaben und der Fortschritt sind in [tasks.md](tasks.md) dokumentiert.

## Kontakt & Beiträge

* **Repository**: [https://github.com/fhalamzie/langchain_project](https://github.com/fhalamzie/langchain_project)
* **Backup-Status**: ✅ Alle Commits synchronisiert
* **Versionskontrolle**: Git-Historie vollständig verfügbar

Für Beiträge zum Projekt folgen Sie bitte den Richtlinien in [development-guidelines.md](development-guidelines.md).