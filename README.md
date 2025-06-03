# WINCASA - Intelligentes Datenbank-Abfrage-System

[![GitHub Repository](https://img.shields.io/badge/GitHub-fhalamzie%2Flangchain__project-blue?logo=github)](https://github.com/fhalamzie/langchain_project)
[![Phoenix Monitoring](https://img.shields.io/badge/Phoenix-AI%20Observability-green?logo=phoenix-framework)](http://localhost:6006)
[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success)]()

## Projektübersicht

WINCASA ist ein produktionsbereites System zur natürlichsprachigen Abfrage von Firebird-Datenbanken. Das System nutzt moderne LLM-Technologie (GPT-4) in Kombination mit direkter Datenbankanbindung und erweiterten RAG-Verfahren (Retrieval Augmented Generation), um komplexe Datenbankabfragen in natürlicher Sprache zu ermöglichen.

**Status: ✅ Produktionsbereit** - Alle Kernfunktionen implementiert und getestet.

## 📂 GitHub Repository

**Repository**: https://github.com/fhalamzie/langchain_project

```bash
# Code klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project
```

## 🚀 Quick Start

### Produktions-Setup

#### Option 1: Von GitHub klonen
```bash
# 1. Repository klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project

# 2. Umgebung vorbereiten
python3 -m venv .venv
source .venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. API-Schlüssel konfigurieren
mkdir -p /home/envs
echo "OPENAI_API_KEY=your_api_key_here" > /home/envs/openai.env

# 5. System starten
./start_enhanced_qa_direct.sh
```

#### Option 2: Docker Deployment
```bash
# Repository klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project

# Mit Docker starten
docker-compose up -d
```

**URL**: `http://localhost:8501`

## 🏗️ Systemarchitektur

### Hauptkomponenten
- **[`firebird_sql_agent_direct.py`](firebird_sql_agent_direct.py)** - SQL-Agent mit direkter FDB-Integration
- **[`fdb_direct_interface.py`](fdb_direct_interface.py)** - Direkte Firebird-Datenbankschnittstelle
- **[`enhanced_qa_ui.py`](enhanced_qa_ui.py)** - Streamlit Web-Interface
- **[`enhanced_retrievers.py`](enhanced_retrievers.py)** - Multi-Stage RAG-System
- **[`db_knowledge_compiler.py`](db_knowledge_compiler.py)** - Database Knowledge System

## 🧪 Testing

### Haupttests
```bash
python test_enhanced_qa_ui_integration.py
python test_fdb_direct_interface.py
python test_firebird_sql_agent.py
python automated_retrieval_test.py
```

## 🎮 Produktiver Betrieb

### Production UI (Empfohlen)
```bash
# Clean Production Interface
source .venv/bin/activate
./start_clean_qa.sh
# URL: http://localhost:8501
```

### Alternative Startmethoden
```bash
streamlit run enhanced_qa_ui.py
python run_llm_query.py
```

## 💬 Beispielabfragen

- *"Wer wohnt in der Marienstraße 26, 45307 Essen?"*
- *"Wie viele Wohnungen gibt es insgesamt?"*
- *"Zeige mir Bewohner mit ihren Adressdaten"*
- *"Welche Eigentümer gibt es in Köln?"*

## 📊 Performance

- **Database**: 151 Tabellen, 517 Wohnungen, 698 Bewohner
- **Retrieval Modi**: Enhanced (22.5s), None (20.8s), FAISS (34.6s)
- **Erfolgsrate**: 63.6% über alle Modi

## 🔧 Systemanforderungen

- **Python 3.8+**
- **Firebird-Datenbank** (WINCASA2022.FDB)
- **OpenAI API-Schlüssel**
- **Dependencies**: langchain, streamlit, faiss-cpu, fdb, PyYAML
- **Monitoring**: arize-phoenix (für AI Observability)

## 📁 Datenorganisation

- **`/output/yamls/`**: 248 YAML Business-Context-Dateien
- **`/output/compiled_knowledge_base.json`**: Kompilierte Wissensbasis
- **`/home/envs/`**: API-Konfigurationsdateien

## 📊 AI Observability (✅ Implementiert)

### Phoenix Integration
```bash
pip install arize-phoenix
```

**Features:**
- ✅ **LLM Tracing**: Vollständige Überwachung aller OpenAI API-Aufrufe
- ✅ **RAG Evaluation**: Performance-Tracking für Enhanced/FAISS/None Modi
- ✅ **Query Analytics**: End-to-End Query-Execution-Metriken
- ✅ **Cost Tracking**: Automatische Kostenberechnung pro Query
- ✅ **Phoenix Dashboard**: Interaktives Dashboard unter http://localhost:6006

**Integration Points:**
- `phoenix_monitoring.py`: Zentrale Monitoring-Infrastruktur
- `firebird_sql_agent_direct.py`: LLM & SQL Execution Tracking
- `enhanced_retrievers.py`: RAG Performance Monitoring
- `enhanced_qa_ui.py`: Dashboard-Links und Live-Metriken
- `automated_retrieval_test.py`: Test Framework mit Metrics Export

## 💾 Backup & Versionskontrolle

### GitHub Integration
Das komplette Projekt ist auf GitHub gesichert:
- **Repository**: https://github.com/fhalamzie/langchain_project
- **Backup-Status**: ✅ Alle Commits synchronisiert
- **Versionskontrolle**: Git-Historie vollständig verfügbar

### Code-Backup
```bash
# Änderungen sichern
git add .
git commit -m "Beschreibung der Änderungen"
git push origin main
```

### Projekt wiederherstellen
```bash
# Von GitHub klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project

# Setup durchführen
pip install -r requirements.txt
./start_enhanced_qa_direct.sh
```

## 🧪 Entwicklungsstandards

### Testing
- 100% Coverage für neue Features
- pytest Framework
- Mock externe Dependencies

### Git Workflow
- Commit pro Major Change
- Conventional Commits Format
- Push zu Remote Repository
- Dokumentation bei Code-Änderungen

---

**Status: ✅ PRODUCTION-READY**

Details: [`CLAUDE.md`](CLAUDE.md) | [`implementation_status.md`](implementation_status.md)