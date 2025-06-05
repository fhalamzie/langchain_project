#!/bin/bash

# Aktiviere die virtuelle Umgebung
. .venv/bin/activate

# Setze den OpenAI API-Key aus der env-Datei
export OPENAI_API_KEY=$(grep -oP 'OPENAI_API_KEY=\K.*' /home/envs/openai.env)

# Installiere zusätzliche Abhängigkeiten, falls sie noch nicht vorhanden sind
pip install -q scikit-learn pandas mermaid-magic

# Erläuterung
echo "=== Erweiterte Q&A-Anwendung für Wincasa Datenbank ==="
echo "Diese Anwendung erweitert die bestehende Dokumentationsfunktionalität um:"
echo "- Direkte Ausführung von SQL-Abfragen auf der Datenbank"
echo "- Verbesserte Kontextauswahl für präzisere Antworten"
echo "- Aufbereitung der Ergebnisse in natürlicher Sprache"
echo "- Feedback-Mechanismen für kontinuierliche Verbesserung"
echo ""
echo "Starte Streamlit-Server..."

# Starte den Streamlit-Server mit der neuen Integrationsdatei
streamlit run streamlit_integration.py --server.address=127.0.0.1 --server.port=8502