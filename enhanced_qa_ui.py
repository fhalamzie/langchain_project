"""
enhanced_qa_ui.py - Integration der direkten FDB-Schnittstelle in die Streamlit-Oberfläche

Diese Datei erweitert die bestehende Streamlit-Anwendung um einen neuen Tab, der die
direkte Firebird-Datenbankschnittstelle (FDB) mit SQL-Ausführung und Ergebnisaufbereitung nutzt.

WICHTIGE ÄNDERUNG: Diese Version verwendet FirebirdDirectSQLAgent anstatt FirebirdDocumentedSQLAgent,
um SQLAlchemy-Sperrprobleme (SQLCODE -902) zu umgehen.

Features der direkten FDB-Schnittstelle:
- Direkte fdb-Treiber-Verbindung ohne SQLAlchemy
- Automatisches Server/Embedded-Fallback
- Custom Langchain Tools für FDB-Operationen
- Verbesserte Fehlerbehandlung und Performance
"""

import os
import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import time
import random

# Importiere lokale Module
from qa_enhancer import QAEnhancer # Behalten wir vorerst für Feedback-Speicherung, falls nötig
from db_executor import get_all_tables, execute_sql, results_to_dataframe # execute_sql für Rohdaten
from firebird_sql_agent_direct import FirebirdDirectSQLAgent

# Konfiguration
FEEDBACK_DIR = Path("./output/feedback")
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

# Singleton-Instanz des QAEnhancer (vorerst beibehalten, falls Teile noch genutzt werden)
@st.cache_resource
def get_qa_enhancer():
    """Erzeugt eine zwischengespeicherte Instanz des QAEnhancer."""
    return QAEnhancer()

# Platzhalter für den Datenbank-Verbindungsstring - BITTE ANPASSEN
# Beispiel: "firebird+fdb://sysdba:masterkey@localhost:3050//path/to/your/WINCASA2022.FDB"
# Oder für SQLite In-Memory Test: "sqlite:///:memory:"
# Wichtig: Der Pfad zur .FDB Datei muss für den Server, auf dem Python läuft, erreichbar sein.
# Sicherstellen, dass das Präfix korrekt ist.
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB")
LLM_MODEL_NAME = "gpt-4-1106-preview"

@st.cache_resource
def get_firebird_sql_agent(retrieval_mode: str = 'faiss'):
    """Erzeugt eine zwischengespeicherte Instanz des FirebirdDirectSQLAgent."""
    st.info(f"Initialisiere FirebirdDirectSQLAgent mit DB: {DB_CONNECTION_STRING} und Retrieval: {retrieval_mode}")
    try:
        agent = FirebirdDirectSQLAgent(
            db_connection_string=DB_CONNECTION_STRING,
            llm=LLM_MODEL_NAME,
            retrieval_mode=retrieval_mode
        )
        st.success("FirebirdDirectSQLAgent erfolgreich initialisiert.")
        return agent
    except Exception as e:
        st.error(f"Fehler bei der Initialisierung des FirebirdDirectSQLAgent: {e}")
        import traceback
        st.error(f"Detaillierter Fehler: {traceback.format_exc()}")
        return None

def create_enhanced_qa_tab():
    """Erstellt einen Tab für die erweiterte Q&A-Funktionalität mit dem direkten FDB SQL Agent."""
    st.header("🚀 Intelligente Datenbankabfrage (Direkte FDB-Schnittstelle)")
    
    st.markdown("""
    Dieser Tab nutzt einen intelligenten SQL-Agenten mit **direkter Firebird-Datenbankverbindung**, um Ihre Fragen zu beantworten.
    
    **🎉 Neue Features:**
    - **Direkte FDB-Schnittstelle**: Umgeht SQLAlchemy-Sperrprobleme (SQLCODE -902)
    - **Verbesserte Performance**: Keine Zwischenschicht mehr
    - **Robuste Verbindung**: Automatisches Server/Embedded-Fallback
    
    Stellen Sie eine Frage in natürlicher Sprache. Das System wird:
    1. Relevante Dokumentation und Schema-Informationen abrufen.
    2. Eine SQL-Abfrage direkt auf der Firebird-Datenbank generieren und ausführen.
    3. Die Ergebnisse in mehreren Textvarianten präsentieren.
    """)
        
    # Sidebar-Konfiguration
    st.sidebar.markdown("### 🔧 Konfiguration")
    
    # Auswahl des Retrieval-Modus
    retrieval_options = ['faiss', 'neo4j'] # Neo4j ist noch nicht voll implementiert im Agenten
    selected_retrieval_mode = st.sidebar.selectbox(
        "Retrieval-Modus:",
        retrieval_options,
        index=0, # Standardmäßig FAISS
        help="FAISS für Vektorsuche, Neo4j für Graph-basierte Suche (experimentell)."
    )
    
    # Status-Anzeige
    st.sidebar.markdown("### 📊 System-Status")
    st.sidebar.success("✅ Direkte FDB-Schnittstelle aktiv")
    st.sidebar.info(f"🔍 Retrieval-Modus: {selected_retrieval_mode.upper()}")
    
    # Datenbankverbindung anzeigen
    db_display = DB_CONNECTION_STRING.replace("masterkey", "***")  # Passwort verstecken
    st.sidebar.text(f"🗄️ DB: {db_display}")

    # Lade Firebird SQL Agent
    agent = get_firebird_sql_agent(retrieval_mode=selected_retrieval_mode)
    
    if agent is None:
        st.error("❌ Direkte FDB SQL Agent konnte nicht geladen werden. Bitte überprüfen Sie die Konfiguration und Fehlermeldungen.")
        st.sidebar.error("❌ Agent nicht verfügbar")
        return
    else:
        st.sidebar.success("✅ Agent bereit")

    # Initialisiere Session State für die Chat-Historie
    if "enhanced_chat_history" not in st.session_state:
        st.session_state.enhanced_chat_history = []
    
    # Initialisiere Session State für Feedback
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = {}
    
    # Chat-Container für die Historie
    chat_container = st.container()
    
    # Zeige Chat-Historie
    with chat_container:
        for i, entry in enumerate(st.session_state.enhanced_chat_history):
            # Zeige Benutzeranfrage
            st.markdown(f"**👤 Sie:** {entry['natural_language_query']}")
            
            if entry.get('error'):
                st.error(f"**🤖 Fehler:** {entry['error']}")
            else:
                # Zeige Systemantwort
                with st.expander("🔍 Details zur Agenten-Verarbeitung", expanded=False):
                    if 'generated_sql' in entry and entry['generated_sql']:
                        st.markdown("**Generierte SQL-Abfrage:**")
                        st.code(entry['generated_sql'], language="sql")
                    
                    if 'retrieved_context' in entry and entry['retrieved_context']:
                        st.markdown("**Abgerufener Dokumentationskontext (Auszug):**")
                        st.text(entry['retrieved_context'][:1000] + "..." if len(entry['retrieved_context']) > 1000 else entry['retrieved_context'])

                    if 'agent_final_answer' in entry and entry['agent_final_answer']:
                        st.markdown("**Antwort des direkten FDB SQL-Agenten (Roh):**")
                        st.text(entry['agent_final_answer'])
                    
                    # Neue Funktion: Detaillierte Schritte der direkten FDB-Schnittstelle anzeigen
                    if 'detailed_steps' in entry and entry['detailed_steps']:
                        st.markdown("**🔧 Detaillierte Agent-Schritte (Direkte FDB-Schnittstelle):**")
                        for i, step in enumerate(entry['detailed_steps']):
                            with st.expander(f"Schritt {i+1}: {step.get('action', {}).get('tool', 'Unbekannt')}", expanded=False):
                                if 'action' in step:
                                    st.json(step['action'])
                                if 'observation' in step:
                                    st.text(f"Beobachtung: {step['observation']}")
                                if 'error' in step:
                                    st.error(f"Fehler: {step['error']}")

                # Zeige Textvarianten der Antwort
                if 'text_variants' in entry and entry['text_variants']:
                    st.markdown(f"**🤖 Antworten:**")
                    variant_tabs = st.tabs([variant['variant_name'] for variant in entry['text_variants']])
                    for tab, variant_data in zip(variant_tabs, entry['text_variants']):
                        with tab:
                            st.markdown(variant_data['text'])
                elif 'agent_final_answer' in entry: # Fallback, falls text_variants nicht da sind
                     st.markdown(f"**🤖 Antwort:** {entry['agent_final_answer']}")


            # Feedback-System (muss ggf. angepasst werden, welche Antwort bewertet wird)
            # Fürs Erste bewerten wir die erste Textvariante oder den agent_final_answer
            feedback_target_answer = ""
            if entry.get('text_variants') and entry['text_variants']:
                feedback_target_answer = entry['text_variants'][0]['text'] # Nimm die erste Variante
            elif entry.get('agent_final_answer'):
                feedback_target_answer = entry['agent_final_answer']

            feedback_id = f"query_{i}" # ID bleibt gleich
            if feedback_id not in st.session_state.feedback_given:
                cols = st.columns([1, 1, 1, 1, 5])
                
                # Bewertungsbuttons
                if cols[0].button("👍 Sehr gut", key=f"vgood_{i}"):
                    _save_feedback(entry['natural_language_query'], feedback_target_answer, 5, "Sehr gut")
                    st.session_state.feedback_given[feedback_id] = True
                    st.rerun()
                    
                if cols[1].button("👌 Gut", key=f"good_{i}"):
                    _save_feedback(entry['natural_language_query'], feedback_target_answer, 4, "Gut")
                    st.session_state.feedback_given[feedback_id] = True
                    st.rerun()
                    
                if cols[2].button("👎 Ungenau", key=f"bad_{i}"):
                    _save_feedback(entry['natural_language_query'], feedback_target_answer, 2, "Ungenau")
                    st.session_state.feedback_given[feedback_id] = True
                    st.rerun()
                    
                if cols[3].button("❌ Falsch", key=f"vbad_{i}"):
                    _save_feedback(entry['natural_language_query'], feedback_target_answer, 1, "Falsch")
                    st.session_state.feedback_given[feedback_id] = True
                    st.rerun()
            elif entry.get('error'):
                 st.markdown("*Kein Feedback für fehlerhafte Anfragen möglich.*")
            else:
                st.markdown("*Vielen Dank für Ihr Feedback!*")
            
            # Trennlinie
            st.markdown("---")
    
    # Eingabeformular
    with st.form(key="enhanced_qa_form"):
        # Texteingabe
        user_query = st.text_area("Ihre Frage:", height=100, 
                                 placeholder="z.B. 'Welche Bewohner leben in der Marienstraße 26?'")
        
        # Erweiterte Optionen
        with st.expander("Erweiterte Optionen", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                use_cache = st.checkbox("Cache verwenden", value=True, 
                                     help="Bereits ausgeführte Abfragen aus dem Cache laden")
            
            with col2:
                show_sql = st.checkbox("SQL-Vorschau", value=True,
                                     help="SQL-Abfrage vor der Ausführung anzeigen")
        
        # Submit-Button
        submit_button = st.form_submit_button("Frage senden")
        
        if submit_button and user_query:
            if agent is None:
                st.error("❌ Direkte FDB SQL Agent ist nicht verfügbar. Anfrage kann nicht bearbeitet werden.")
                return

            with st.spinner("🔄 Direkte FDB Agent verarbeitet Ihre Anfrage... Bitte haben Sie einen Moment Geduld."):
                # Verarbeite die Anfrage mit dem direkten FDB Agenten
                # Der retrieval_mode wird beim Initialisieren des Agenten übergeben
                agent_response = agent.query(user_query)
                
                # Füge das Ergebnis zur Chat-Historie hinzu
                # Die Struktur von agent_response der direkten FDB-Schnittstelle ist:
                # {
                #     "natural_language_query": ...,
                #     "retrieved_context": ...,
                #     "agent_final_answer": ...,
                #     "generated_sql": ...,
                #     "text_variants": [{"variant_name": ..., "text": ...}, ...],
                #     "detailed_steps": [...],  # Neue Eigenschaft der direkten FDB-Schnittstelle
                #     "error": ... or None
                # }
                history_entry = {
                    'natural_language_query': user_query, # Stelle sicher, dass dieser Schlüssel immer da ist
                    **agent_response, # Überschreibe ggf. mit Agenten-Antwort, falls vorhanden
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.enhanced_chat_history.append(history_entry)
                
                # Aktualisiere die Seite, um die neue Antwort anzuzeigen
                st.rerun()

def _save_feedback(user_query: str, answer: str, rating: int, comment: str):
    """
    Speichert Benutzerfeedback zu einer Antwort.
    Args:
        user_query: Die ursprüngliche Benutzeranfrage.
        answer: Die vom System generierte Antwort, die bewertet wird.
        rating: Bewertung (1-5).
        comment: Kommentar (z.B. "Sehr gut", "Falsch").
    """
    # Verwende QAEnhancer Instanz für save_feedback, da es dort implementiert ist
    # oder implementiere es hier neu/kopiere es.
    # Fürs Erste nehmen wir an, QAEnhancer.save_feedback ist generisch genug.
    enhancer_for_feedback = get_qa_enhancer() # Holt die gecachte Instanz
    
    if hasattr(enhancer_for_feedback, 'save_feedback'):
        enhancer_for_feedback.save_feedback(
            user_query=user_query,
            answer=answer, # Die spezifische Antwortvariante, die bewertet wurde
            feedback=comment, # z.B. "Sehr gut", "Ungenau"
            rating=rating,
            user_id=f"user_{random.randint(1000, 9999)}"
        )
        st.success(f"Feedback gespeichert: {comment} ({rating}/5)")
    else:
        st.warning("Feedback-Speicherfunktion nicht im QAEnhancer gefunden.")


# Funktionen zum Testen und Debuggen (vorerst unverändert lassen)
def test_qa_enhancer():
    """Führt einen einfachen Test der QAEnhancer-Klasse durch."""
    enhancer = QAEnhancer()
    
    test_queries = [
        "Welche Bewohner leben in der Marienstraße 26?",
        "Zeige mir alle Eigentümer in Berlin",
        "Wie viele Wohnungen gibt es pro Gebäude?",
        "Welche Bankverbindungen haben wir für Eigentümer?"
    ]
    
    for query in test_queries:
        st.subheader(f"Test-Anfrage: {query}")
        
        start_time = time.time()
        result = enhancer.process_query(query)
        end_time = time.time()
        
        st.write(f"Verarbeitungszeit: {end_time - start_time:.2f} Sekunden")
        
        st.write("Relevante Tabellen:", ", ".join(result['relevant_tables']))
        
        st.markdown("**Generierte SQL:**")
        st.code(result['sql'], language="sql")
        
        st.markdown("**Antwort:**")
        st.write(result['answer'])
        
        st.markdown("---")

# Diese Funktion wird aufgerufen, wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    st.set_page_config(page_title="Erweiterte Q&A", page_icon="🔍", layout="wide")
    create_enhanced_qa_tab()