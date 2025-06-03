#!/bin/bash
# Startskript für die erweiterte Q&A-UI mit direkter FDB-Schnittstelle
# 
# Dieses Skript startet die Streamlit-Anwendung mit der neuen direkten 
# Firebird-Datenbankschnittstelle, die SQLAlchemy-Sperrprobleme umgeht.

echo "🚀 Starte erweiterte Q&A-UI mit direkter FDB-Schnittstelle..."
echo "============================================================"

# Prüfe, ob virtuelle Umgebung existiert
if [ ! -d ".venv" ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden. Bitte führen Sie zuerst die Installation durch."
    exit 1
fi

# Prüfe, ob Firebird-Datenbank existiert
if [ ! -f "WINCASA2022.FDB" ]; then
    echo "⚠️  WINCASA2022.FDB nicht gefunden. Bitte stellen Sie sicher, dass die Datenbank verfügbar ist."
fi

# Prüfe API-Schlüssel
if [ ! -f "/home/envs/openai.env" ] && [ ! -f "/home/envs/openrouter.env" ]; then
    echo "⚠️  Keine API-Schlüssel-Dateien gefunden. LLM-Funktionen könnten eingeschränkt sein."
fi

echo ""
echo "🔧 Features der direkten FDB-Schnittstelle:"
echo "  ✅ Umgeht SQLAlchemy-Sperrprobleme (SQLCODE -902)"
echo "  ✅ Automatisches Server/Embedded-Fallback"
echo "  ✅ Custom Langchain Tools für FDB-Operationen"
echo "  ✅ Verbesserte Fehlerbehandlung und Performance"
echo "  ✅ Detaillierte Agent-Schritte in der UI"
echo ""

# Aktiviere virtuelle Umgebung und starte Streamlit
echo "🔄 Aktiviere virtuelle Umgebung und starte Streamlit..."
.venv/bin/python -m streamlit run enhanced_qa_ui.py --server.port 8501 --server.address 0.0.0.0

echo ""
echo "👋 Anwendung beendet."