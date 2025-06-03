# WINCASA - Intelligentes Datenbank-Abfrage-System

## Projektübersicht

WINCASA ist ein produktionsbereites System zur natürlichsprachigen Abfrage von Firebird-Datenbanken. Das System nutzt moderne LLM-Technologie (GPT-4) in Kombination mit direkter Datenbankanbindung und erweiterten RAG-Verfahren (Retrieval Augmented Generation), um komplexe Datenbankabfragen in natürlicher Sprache zu ermöglichen.

**Status: ✅ Produktionsbereit** - Alle Kernfunktionen implementiert und getestet.

## 🚀 Quick Start

### Produktions-Setup
```bash
# 1. Umgebung vorbereiten
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencies installieren
pip install langchain langchain-community langchain-openai streamlit pandas numpy \
            scikit-learn fdb faiss-cpu tiktoken PyYAML python-dotenv

# 3. API-Schlüssel konfigurieren
echo "OPENAI_API_KEY=your_api_key_here" > /home/envs/openai.env

# 4. System starten
./start_enhanced_qa_direct.sh
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

## 📊 AI Observability (Geplant)

### Phoenix Integration
```bash
pip install arize-phoenix
```

**Features:**
- LLM Tracing
- RAG Evaluation 
- Query Analytics
- Prompt Management

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