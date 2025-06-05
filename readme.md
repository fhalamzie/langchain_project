# WINCASA - Intelligentes Datenbank-Abfrage-System

[![GitHub Repository](https://img.shields.io/badge/GitHub-fhalamzie%2Flangchain__project-blue?logo=github)](https://github.com/fhalamzie/langchain_project)
[![Phoenix Monitoring](https://img.shields.io/badge/Phoenix-AI%20Observability-green?logo=phoenix-framework)](http://localhost:6006)
[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Testing Framework](https://img.shields.io/badge/Testing-pytest%20%7C%2013%2F13%20passing-brightgreen)]()
[![Code Quality](https://img.shields.io/badge/Code%20Quality-Black%20%7C%20isort%20%7C%20flake8%20%7C%20bandit-blue)]()

## Projektübersicht

WINCASA ist ein produktionsbereites System zur natürlichsprachigen Abfrage von Firebird-Datenbanken. Das System nutzt moderne LLM-Technologie (GPT-4) in Kombination mit direkter Datenbankanbindung und erweiterten RAG-Verfahren (Retrieval Augmented Generation), um komplexe Datenbankabfragen in natürlicher Sprache zu ermöglichen.

**Status: ✅ Produktionsbereit** - Alle Kernfunktionen implementiert und getestet.

## Quick Start

```bash
# Von GitHub klonen
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project

# Umgebung vorbereiten
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# API-Schlüssel konfigurieren
mkdir -p /home/envs
echo "OPENAI_API_KEY=your_api_key_here" > /home/envs/openai.env

# System starten
./start_enhanced_qa_direct.sh
```

**URL**: `http://localhost:8501`

## Systemanforderungen

- **Python 3.8+**
- **Firebird-Datenbank** (WINCASA2022.FDB)
- **OpenAI API-Schlüssel**
- **Dependencies**: langchain, streamlit, faiss-cpu, fdb, PyYAML, networkx
- **SQL-LLM Dependencies**: transformers, torch, sqlalchemy (für SQLCoder-2)
- **LangChain SQL Tools**: langchain-experimental (für SQL Database Agent)
- **Firebird Server**: ✅ Konfiguriert mit SYSDBA authentication (sudo systemctl start firebird)
- **Monitoring**: arize-phoenix (für AI Observability)

## Beispielabfragen

- *"Wer wohnt in der Marienstraße 26, 45307 Essen?"*
- *"Wie viele Wohnungen gibt es insgesamt?"*
- *"Zeige mir Bewohner mit ihren Adressdaten"*
- *"Welche Eigentümer gibt es in Köln?"*

## Dokumentation

Detaillierte Informationen zum Projekt finden Sie in folgenden Dokumenten:

- **[claude.md](claude.md)** - Zentrale Einführung und Dokumentationsübersicht
- **[development-guidelines.md](development-guidelines.md)** - Entwicklungsrichtlinien und -workflows
- **[code-quality.md](code-quality.md)** - Tools für Code-Qualitätssicherung
- **[testing.md](testing.md)** - Testmodule und -standards
- **[high-level-design.md](high-level-design.md)** - Übergeordnetes Projektdesign
- **[tasks.md](tasks.md)** - Implementierungsaufgaben und Fortschrittsverfolgung

---

**Status: ✅ PRODUCTION-READY**