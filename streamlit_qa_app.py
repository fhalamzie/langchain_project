"""
WINCASA Production Q&A Application

Clean, production-ready Streamlit interface for natural language database queries.
Supports 3 retrieval modes: Enhanced (recommended), FAISS, and None (baseline).
"""

import os
import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, Optional
from datetime import datetime
import time

# Import the main agent
from firebird_sql_agent_direct import FirebirdDirectSQLAgent

# Configuration
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", 
    "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB")
LLM_MODEL_NAME = "gpt-4o-mini"

# Page configuration
st.set_page_config(
    page_title="WINCASA Q&A",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_sql_agent(retrieval_mode: str = 'enhanced'):
    """Create cached SQL agent instance with error handling."""
    try:
        with st.spinner(f"Initialisiere {retrieval_mode.upper()} Modus..."):
            agent = FirebirdDirectSQLAgent(
                db_connection_string=DB_CONNECTION_STRING,
                llm=LLM_MODEL_NAME,
                retrieval_mode=retrieval_mode,
                use_enhanced_knowledge=True
            )
        return agent
    except Exception as e:
        error_msg = str(e)
        if "SQLCODE: -902" in error_msg and "Database already opened" in error_msg:
            st.error("🔒 **Database Lock Error**: Die Datenbank ist bereits von einem anderen Prozess geöffnet.")
            st.info("💡 **Lösung**: Stoppen Sie laufende Tests oder warten Sie bis diese beendet sind.")
            with st.expander("🔍 Für Entwickler: Process Details"):
                st.code("# Laufende Prozesse prüfen:\nps aux | grep optimized_retrieval_test")
                st.code("# Test-Logs überwachen:\ntail -f optimized_retrieval_test_*.log")
        else:
            st.error(f"❌ Agent-Initialisierung fehlgeschlagen: {error_msg}")
        return None

def display_agent_reasoning(response: Dict[str, Any]):
    """Display agent reasoning and SQL generation process."""
    with st.expander("🔍 Agent Reasoning & SQL Generierung", expanded=False):
        
        # Generated SQL
        if 'generated_sql' in response and response['generated_sql']:
            st.subheader("📝 Generierte SQL-Abfrage")
            st.code(response['generated_sql'], language='sql')
        
        # Agent steps
        if 'agent_steps' in response and response['agent_steps']:
            st.subheader("🧠 Agent Reasoning Steps")
            for i, step in enumerate(response['agent_steps'], 1):
                with st.container():
                    st.markdown(f"**Step {i}:**")
                    if isinstance(step, dict):
                        if 'tool' in step:
                            st.markdown(f"🔧 Tool: `{step['tool']}`")
                        if 'input' in step:
                            st.markdown(f"📥 Input: {step['input']}")
                        if 'output' in step:
                            with st.expander(f"📤 Output (Step {i})", expanded=False):
                                st.text(str(step['output'])[:1000] + "..." if len(str(step['output'])) > 1000 else str(step['output']))
                    else:
                        st.text(str(step)[:500] + "..." if len(str(step)) > 500 else str(step))
                    st.divider()
        
        # Query results metadata
        if 'query_results' in response:
            results = response['query_results']
            if results:
                st.subheader("📊 Query Results Metadata")
                st.markdown(f"**Anzahl Zeilen:** {len(results)}")
                if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict):
                    st.markdown(f"**Spalten:** {len(results[0])} ({', '.join(list(results[0].keys())[:5])}{'...' if len(results[0]) > 5 else ''})")

def display_query_results(response: Dict[str, Any]):
    """Display query results in a formatted table."""
    if 'query_results' in response and response['query_results']:
        results = response['query_results']
        
        st.subheader("📋 Abfrageergebnisse")
        
        # Convert to DataFrame for better display
        try:
            if isinstance(results, list) and len(results) > 0:
                df = pd.DataFrame(results)
                
                # Show results count
                st.markdown(f"**{len(df)} Ergebnisse gefunden**")
                
                # Display table with pagination for large results
                if len(df) > 100:
                    st.warning(f"Große Ergebnismenge ({len(df)} Zeilen). Zeige erste 100 Zeilen.")
                    df_display = df.head(100)
                else:
                    df_display = df
                
                # Format DataFrame for better readability
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download option for large datasets
                if len(df) > 10:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download als CSV",
                        data=csv,
                        file_name=f"wincasa_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("Keine Ergebnisse gefunden.")
                
        except Exception as e:
            st.error(f"Fehler bei der Darstellung der Ergebnisse: {e}")
            st.json(results)
    else:
        st.info("Keine Daten abgerufen.")

def main():
    """Main application interface."""
    
    # Header
    st.title("🏢 WINCASA Intelligent Database Q&A")
    st.markdown("**Natürlichsprachige Datenbankabfragen mit KI-gestützter SQL-Generierung**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Konfiguration")
        
        # Retrieval mode selection
        st.subheader("🔍 Retrieval Modus")
        
        retrieval_mode = st.radio(
            "Wählen Sie den Retrieval-Modus:",
            options=['enhanced', 'faiss', 'none'],
            index=0,  # Enhanced as default
            format_func=lambda x: {
                'enhanced': '🚀 Enhanced (Empfohlen)',
                'faiss': '📚 FAISS',
                'none': '⚡ None (Baseline)'
            }[x]
        )
        
        # Mode descriptions
        mode_descriptions = {
            'enhanced': """
            **Enhanced Modus (Empfohlen)**
            - Beste Genauigkeit für komplexe Abfragen
            - Intelligente Dokumentationssuche
            - Optimiert für WINCASA Daten
            """,
            'faiss': """
            **FAISS Modus**
            - Standard Vektorsuche
            - Gut für allgemeine Abfragen
            """,
            'none': """
            **Baseline Modus**
            - Ohne zusätzlichen Kontext
            - Für einfache SQL-Abfragen
            """
        }
        
        st.info(mode_descriptions[retrieval_mode])
        
        # Help section
        st.subheader("❓ Hilfe")
        st.info("**Enhanced Modus** empfohlen für beste Ergebnisse.")
        if st.button("🔄 Agent neu laden", use_container_width=True):
            st.cache_resource.clear()
            st.success("Cache geleert - Agent wird neu geladen")
        
        # Example queries
        st.subheader("💡 Beispielabfragen")
        example_queries = [
            "Wer wohnt in der Marienstraße 26, 45307 Essen?",
            "Wie viele Wohnungen gibt es insgesamt?",
            "Liste aller Eigentümer aus Köln",
            "Durchschnittliche Miete in Essen",
            "Alle Mieter der MARIE26"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"📝 {example}", key=f"example_{i}", use_container_width=True):
                st.session_state.query_input = example
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Ihre Frage")
        
        # Query input
        query = st.text_area(
            "Stellen Sie eine Frage zu den WINCASA Daten:",
            value=st.session_state.get('query_input', ''),
            height=100,
            placeholder="z.B. Wer wohnt in der Marienstraße 26?"
        )
        
        # Query button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            submit_button = st.button("🚀 Abfrage starten", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Löschen", use_container_width=True)
        
        if clear_button:
            st.session_state.query_input = ''
            st.rerun()
    
    with col2:
        st.subheader("📈 Performance Metrics")
        if 'last_query_time' in st.session_state:
            st.metric("⏱️ Letzte Abfrage", f"{st.session_state.last_query_time:.1f}s")
        if 'last_query_mode' in st.session_state:
            st.metric("🔧 Letzter Modus", st.session_state.last_query_mode.upper())
        if 'total_queries' in st.session_state:
            st.metric("📊 Gesamtabfragen", st.session_state.total_queries)
    
    # Process query
    if submit_button and query.strip():
        
        # Initialize session state
        if 'total_queries' not in st.session_state:
            st.session_state.total_queries = 0
        
        st.session_state.total_queries += 1
        st.session_state.last_query_mode = retrieval_mode
        
        # Get SQL agent
        agent = get_sql_agent(retrieval_mode)
        
        if agent is None:
            st.error("❌ Agent konnte nicht initialisiert werden. Bitte prüfen Sie die Konfiguration.")
            return
        
        # Execute query
        with st.spinner(f"🔄 Verarbeite Anfrage mit {retrieval_mode.upper()} Modus..."):
            start_time = time.time()
            
            try:
                response = agent.query(query)
                execution_time = time.time() - start_time
                st.session_state.last_query_time = execution_time
                
                # Display results
                st.success(f"✅ Abfrage erfolgreich in {execution_time:.1f}s verarbeitet")
                
                # Main answer
                st.subheader("💬 Antwort")
                if isinstance(response, dict) and 'agent_final_answer' in response:
                    st.markdown(response['agent_final_answer'])
                else:
                    st.markdown(str(response))
                
                # Query results table
                if isinstance(response, dict):
                    display_query_results(response)
                    
                    # Agent reasoning (collapsible)
                    display_agent_reasoning(response)
                
            except Exception as e:
                execution_time = time.time() - start_time
                st.session_state.last_query_time = execution_time
                
                st.error(f"❌ Fehler bei der Abfrage: {str(e)}")
                
                # Show error details in expander
                with st.expander("🔍 Fehlerdetails", expanded=False):
                    st.text(str(e))
                    import traceback
                    st.code(traceback.format_exc())
    
    elif submit_button:
        st.warning("⚠️ Bitte geben Sie eine Frage ein.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🏢 WINCASA Intelligent Database Q&A
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()