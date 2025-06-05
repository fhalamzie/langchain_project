#!/bin/bash

# Aktiviere die virtuelle Umgebung
. .venv/bin/activate

# Setze den OpenAI API-Key aus der env-Datei
export OPENAI_API_KEY=$(grep -oP 'OPENAI_API_KEY=\K.*' /home/envs/openai.env)

# Installiere zusätzliche Abhängigkeiten, falls sie noch nicht vorhanden sind
pip install sklearn pandas mermaid-magic

# Starte den Streamlit-Server nur lokal (nicht im Internet)
streamlit run generate_yaml_ui.py --server.address=127.0.0.1 --server.port=8501