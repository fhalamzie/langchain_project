#!/usr/bin/env python3
"""
WINCASA Layer 4 Streamlit Frontend
Production-ready UI für alle 4 Modi mit Layer 4 JSON Integration
Enhanced with Phase 2 Features: Unified Engine, Feature Flags
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# Custom imports
from wincasa.utils.config_loader import WincasaConfig
from wincasa.data.layer4_json_loader import Layer4JSONLoader
# json_exporter is not needed for the streamlit app
from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.monitoring.wincasa_monitoring_dashboard import WincasaMonitoringDashboard
# Phase 2 imports
from wincasa.core.wincasa_query_engine import WincasaQueryEngine
from wincasa.monitoring.wincasa_unified_logger import (QueryLogEntry, get_query_logger,
                                    query_path_logger)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="WINCASA Layer 4 - WEG Verwaltung",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class WincasaStreamlitApp:
    def __init__(self):
        self.config = WincasaConfig()
        self.llm_handler = WincasaLLMHandler()
        self.layer4_loader = Layer4JSONLoader()
        
        # Initialize query logger and monitoring
        self.query_logger = get_query_logger(debug_mode=False)
        
        # Initialize unified query engine
        try:
            from wincasa.core.wincasa_query_engine import WincasaQueryEngine
            self.query_engine = WincasaQueryEngine(debug_mode=False)
            logger.info("✅ WincasaQueryEngine initialized successfully")
        except Exception as e:
            logger.error(f"❌ Could not initialize WincasaQueryEngine: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"Warning: Could not initialize WincasaQueryEngine: {e}")
            self.query_engine = None
        
        # Don't call init_session_state here - will be called in run()
    
    def ensure_session_state(self):
        """Ensures session state is initialized"""
        # Call the global init function
        init_session_state()
    
    def render_sidebar(self):
        """Rendert Sidebar mit Konfiguration"""
        st.sidebar.title("🏠 WINCASA Layer 4")
        st.sidebar.markdown("**WEG-Verwaltungsassistent**")
        
        # Mode Selection
        st.sidebar.subheader("System-Modi")
        
        # Multi-Mode Selection - 5 Modi (4 Legacy + 1 Unified)
        modes = {
            'json_standard': '📊 JSON Layer 4 Standard (detailliert)',
            'json_vanilla': '📋 JSON Layer 4 Vanilla (minimal)', 
            'sql_standard': '🔍 SQL Layer 4 Standard (detailliert)',
            'sql_vanilla': '⚡ SQL Layer 4 Vanilla (minimal)',
            'unified': '🚀 Unified Engine (Phase 2 - intelligent)'
        }
        
        selected_modes = []
        for mode_key, mode_label in modes.items():
            if st.sidebar.checkbox(mode_label, key=f"mode_{mode_key}"):
                selected_modes.append(mode_key)
        
        # LLM Configuration - OpenAI Only
        st.sidebar.subheader("OpenAI Konfiguration")
        
        # Fixed provider
        provider = 'openai'
        st.sidebar.info("🚀 OpenAI Direct API - Latest GPT-4.1 & 4o models with function calling")
        
        # Model selection
        model_options = [
            'gpt-4.1-nano',     # Ultra-low cost for simple tasks ($0.10/$0.40)
            'gpt-4.1-mini',     # Fast & cost-effective ($0.40/$1.60)
            'gpt-4.1',          # High performance ($2.00/$8.00)
            'gpt-4o-mini',      # Legacy reliable ($0.15/$0.60)
            'gpt-4o'            # Premium multimodal ($2.50/$10.00)
        ]
        current_model = self.config.get('openai_model', 'gpt-4.1-nano')
        
        try:
            model_index = model_options.index(current_model)
        except ValueError:
            model_index = 0
        
        model = st.sidebar.selectbox(
            "Model",
            options=model_options,
            index=model_index,
            help="gpt-4.1-nano recommended: Ultra-low cost, perfect for property management queries"
        )
        
        # Show cost information
        if model == 'gpt-4.1-nano':
            st.sidebar.success("💰 Ultra-low cost: $0.10 input / $0.40 output per 1M tokens")
        elif model == 'gpt-4o-mini':
            st.sidebar.success("💰 Low cost: $0.15 input / $0.60 output per 1M tokens")
        elif model == 'gpt-4.1-mini':
            st.sidebar.info("💵 Medium cost: $0.40 input / $1.60 output per 1M tokens")
        elif model == 'gpt-4.1':
            st.sidebar.warning("💸 High cost: $2.00 input / $8.00 output per 1M tokens")
        elif model == 'gpt-4o':
                st.sidebar.error("💸 Premium cost: $2.50 input / $10.00 output per 1M tokens")
        
        # Temperature
        temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
        
        # Check if unified engine is available
        if 'unified' in selected_modes and not self.query_engine:
            st.sidebar.error("⚠️ Unified Engine nicht verfügbar")
            logger.warning("Unified Engine selected but not available, removing from modes")
            selected_modes.remove('unified')
            
            # Add button to clear cache and reinitialize
            if st.sidebar.button("🔄 App neu initialisieren"):
                st.cache_resource.clear()
                st.rerun()
        
        return selected_modes, model, temperature
    
    def load_json_data(self):
        """Lädt Layer 4 JSON-Daten für JSON-Modi"""
        if st.session_state.json_data_loaded:
            return
        
        try:
            # Get available Layer 4 queries
            available_queries = self.layer4_loader.list_available_queries()
            
            # Load a subset of key queries for performance
            key_queries = [
                '01_eigentuemer',
                '03_aktuelle_mieter', 
                '05_objekte',
                '09_konten',
                '26_detaillierte_buchungen'
            ]
            
            loaded_count = 0
            for query_name in key_queries:
                data = self.layer4_loader.load_json_data(query_name)
                if data:
                    st.session_state.json_data[query_name] = data
                    loaded_count += 1
                    logger.info(f"Layer 4 JSON-Daten geladen: {query_name}")
            
            if loaded_count > 0:
                st.session_state.json_data_loaded = True
                logger.info(f"Erfolgreich {loaded_count} Layer 4 JSON-Dateien geladen")
            else:
                st.error("Keine Layer 4 JSON-Dateien gefunden")
                
        except Exception as e:
            st.error(f"Fehler beim Laden der Layer 4 JSON-Daten: {e}")
            logger.error(f"Layer 4 JSON loading error: {e}")
        
        st.session_state.json_data_loaded = True
    
    def execute_real_llm_query(self, query: str, mode: str, provider: str = 'openai', model: str = None) -> Dict[str, Any]:
        """Führt echte LLM-Abfrage aus (OpenAI only)"""
        try:
            # Temporarily set model in environment if provided
            original_openai_model = os.environ.get('OPENAI_MODEL')
            
            if model:
                os.environ['OPENAI_MODEL'] = model
            
            # Create fresh LLM Handler with updated config
            llm_handler = WincasaLLMHandler()
            result = llm_handler.query_llm(query, mode)
            
            # Restore original environment
            if original_openai_model:
                os.environ['OPENAI_MODEL'] = original_openai_model
            
            return result
        except Exception as e:
            logger.error(f"LLM Query Fehler in {mode}: {e}")
            return {
                "answer": f"**Fehler in {mode.upper()}:** {str(e)}",
                "source": f"Fehler - {mode}",
                "response_time": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def render_query_interface(self, selected_modes: List[str]):
        """Rendert Query-Interface"""
        st.header("Abfrage-Interface")
        
        # Quick Examples
        st.subheader("🚀 Beispiel-Abfragen")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👥 Alle Eigentümer anzeigen", key=f"example_owners_{st.session_state.session_id}"):
                st.session_state.current_query = "Zeige mir alle Eigentümer mit Kontaktdaten"
                # Auto-execute if modes are selected
                if selected_modes:
                    model = getattr(st.session_state, 'current_model', 'gpt-4.1-nano')
                    self.execute_query(st.session_state.current_query, selected_modes, model)
        
        with col2:
            if st.button("💰 Mieteinnahmen 2024", key=f"example_rent_{st.session_state.session_id}"):
                st.session_state.current_query = "Analysiere die Mieteinnahmen für 2024"
                # Auto-execute if modes are selected  
                if selected_modes:
                    model = getattr(st.session_state, 'current_model', 'gpt-4o-mini')
                    self.execute_query(st.session_state.current_query, selected_modes, model)
        
        with col3:
            if st.button("🏦 Rücklagen-Status", key=f"example_reserves_{st.session_state.session_id}"):
                st.session_state.current_query = "Wie hoch sind die aktuellen Rücklagen?"
                # Auto-execute if modes are selected
                if selected_modes:
                    model = getattr(st.session_state, 'current_model', 'gpt-4.1-nano')
                    self.execute_query(st.session_state.current_query, selected_modes, model)
        
        # Manual Query Input
        st.subheader("✍️ Eigene Abfrage")
        
        # Query input
        query = st.text_area(
            "Ihre Frage an den WEG-Assistenten:",
            value=getattr(st.session_state, 'current_query', ''),
            height=100,
            placeholder="z.B. 'Zeige mir alle Eigentümer der Kupferstraße 190' oder 'Welche Wohnungen stehen leer?'",
            key="query_input"
        )
        
        # Submit button - centered and simplified
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            # Use session-unique key to prevent ghost buttons
            execute_key = f"main_execute_button_{st.session_state.session_id}"
            if st.button("🔍 Abfrage ausführen", type="primary", use_container_width=True, key=execute_key):
                if query and selected_modes:
                    # Get current model from session state or config
                    model = getattr(st.session_state, 'current_model', 'gpt-4.1-nano')
                    self.execute_query(query, selected_modes, model)
                elif query and not selected_modes:
                    st.warning("⚠️ Bitte wählen Sie mindestens einen der 5 Modi in der Sidebar aus.")
                elif not query:
                    st.warning("⚠️ Bitte geben Sie eine Frage ein.")
    
    def execute_query(self, query: str, modes: List[str], model: str = 'gpt-4.1-nano'):
        """Führt Query in allen gewählten Modi aus"""
        # Results header will be shown in display_results instead
        
        # Start unified query logging with path tracking
        query_id = query_path_logger.start_query(query, modes, 
                                               st.session_state.user_id, 
                                               st.session_state.session_id)
        logger.info(f"Starting query execution - ID: {query_id}, Modes: {modes}")
        
        results = {}
        
        # Progress bar for all modes
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_modes = len(modes)
        
        for i, mode in enumerate(modes):
            status_text.text(f"Führe Abfrage aus in {mode} mit OpenAI {model}...")
            progress_bar.progress((i + 1) / total_modes)
            
            if mode == 'unified':
                # Execute unified query and convert result
                logger.info(f"Executing unified query: {query[:50]}...")
                query_path_logger.log_event(query_id, 'streamlit', 'execute', {
                    'mode': 'unified',
                    'model': model
                })
                unified_result = self.execute_unified_query(query, model, query_id)
                if unified_result:
                    results[mode] = unified_result
                    logger.info("✅ Unified query executed successfully")
                else:
                    logger.warning("⚠️ Unified query returned None")
                    query_path_logger.log_event(query_id, 'streamlit', 'error', {
                        'mode': 'unified',
                        'error': 'No result returned'
                    })
            else:
                # Execute other modes
                query_path_logger.log_event(query_id, 'streamlit', 'execute', {
                    'mode': mode,
                    'model': model,
                    'provider': 'openai'
                })
                result = self.execute_real_llm_query(query, mode, 'openai', model)
                results[mode] = result
        
        progress_bar.empty()
        status_text.empty()
        
        # Display all results together
        if results:
            self.display_results(query, results)
            
        # Complete query path logging
        query_path_logger.complete_query(query_id, results)
        
        # Analyze and log any issues
        analysis = query_path_logger.analyze_query_path(query_id)
        if analysis.get('missing_modes'):
            logger.warning(f"Query {query_id} - Missing modes: {analysis['missing_modes']}")
            st.warning(f"⚠️ Fehlende Modi: {', '.join(analysis['missing_modes'])}")
        if analysis.get('errors'):
            logger.error(f"Query {query_id} - Errors: {analysis['errors']}")
        
        # Save to history (session-based) - include all executed modes
        if results:
            st.session_state.query_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'modes': list(results.keys()),
                'provider': 'openai',
                'model': model,
                'results': results
            })
        
        # Log each mode result to persistent storage
        for mode, result in results.items():
            if result.get('success', False):
                log_entry = QueryLogEntry(
                    query_id=query_id,  # Now includes query_id!
                    timestamp=datetime.now().isoformat(),
                    query=query,
                    mode=mode,
                    model=model,
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    response_time_ms=result.get('response_time', 0) * 1000,  # Convert to ms
                    result_count=result.get('result_count', 1 if result.get('answer') else 0),
                    confidence=result.get('confidence', 0.8),  # Use actual confidence if available
                    cost_estimate=result.get('cost', result.get('cost_estimate', 0.01)),  # Use actual cost if available
                    success=True,
                    answer_preview=result.get('answer', '')[:200] if result.get('answer') else None,
                    source_data=mode,
                    selected_modes=modes
                )
            else:
                log_entry = QueryLogEntry(
                    query_id=query_id,  # Now includes query_id!
                    timestamp=datetime.now().isoformat(),
                    query=query,
                    mode=mode,
                    model=model,
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id,
                    response_time_ms=result.get('response_time', 0) * 1000,
                    result_count=0,
                    confidence=0.0,
                    cost_estimate=0.005,
                    success=False,
                    error=result.get('error', 'Unknown error'),
                    source_data=mode,
                    selected_modes=modes
                )
            
            # Log to unified logger (includes path tracking)
            query_path_logger.log_mode_result(query_id, log_entry)
    
    def execute_unified_query(self, query: str, model: str = 'gpt-4.1-nano', query_id: str = None):
        """Executes unified query and returns result in standard format"""
        if not self.query_engine:
            logger.error("Query engine is None, cannot execute unified query")
            if query_id:
                query_path_logger.log_error(query_id, 'streamlit', 
                                          Exception("Query engine not initialized"), 
                                          {'phase': 'init_check'})
            return None
        
        try:
            if query_id:
                query_path_logger.log_layer_transition(query_id, 'streamlit', 'query_engine',
                                                     {'query': query, 'model': model})
            start_time = time.time()
            logger.info(f"Calling query_engine.process_query with query: {query[:50]}...")
            
            # Execute query through unified engine
            result = self.query_engine.process_query(
                query, 
                user_id=st.session_state.user_id
            )
            logger.info(f"Query engine returned result: {result.processing_mode}")
            
            # Convert to standard format for display
            return {
                'answer': result.answer,
                'response_time': time.time() - start_time,
                'source': f"Unified Engine v{result.engine_version}",
                'confidence': result.confidence,
                'result_count': result.result_count,
                'cost': result.cost_estimate,
                'success': True  # Add success field for compatibility
            }
            
        except Exception as e:
            return {
                'answer': f"❌ Fehler: {str(e)}",
                'response_time': time.time() - start_time,
                'source': "Unified Engine Error",
                'confidence': 0.0,
                'result_count': 0,
                'cost': 0.0,
                'success': False,  # Add success field for error case
                'error': str(e)  # Add error field for logging
            }
    
    def execute_phase2_query(self, query: str, model: str = 'gpt-4.1-nano'):
        """Führt Query über Phase 2 Unified Engine aus"""
        
        if not self.query_engine:
            st.error("Query Engine not initialized. Please enable Unified Engine in sidebar.")
            return
        
        
        # Progress indicator
        with st.spinner("Führe Query über Unified Engine aus..."):
            try:
                start_time = time.time()
                
                # Execute query through unified engine
                result = self.query_engine.process_query(
                    query, 
                    user_id=st.session_state.user_id
                )
                
                # Display results
                self.display_phase2_results(query, result)
                    
            except Exception as e:
                st.error(f"Phase 2 query execution failed: {e}")
                # Fallback to legacy
                st.info("Falling back to legacy system...")
                modes = ['json_standard']  # Default fallback
                return self.execute_query(query, modes, model)
    
    def display_phase2_results(self, query: str, result):
        """Zeigt Phase 2 Query Ergebnisse an"""
        
        st.markdown(f"**Abfrage:** {query}")
        st.markdown("---")
        
        # Main result display
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Engine badge
            st.markdown(f"🔷 **{result.processing_mode.replace('_', ' ').title()}**")
            
            # Answer
            st.markdown(result.answer)
        
        with col2:
            # Metrics
            st.metric("Antwortzeit", f"{result.processing_time_ms:.0f}ms")
            st.metric("Konfidenz", f"{result.confidence:.1%}")
            st.metric("Ergebnisse", result.result_count)
            st.metric("Kosten", f"${result.cost_estimate:.4f}")
            
            # Engine details
            with st.expander("🔧 Engine Details"):
                st.write(f"**Engine:** {result.engine_version}")
                st.write(f"**Processing Mode:** {result.processing_mode}")
                st.write(f"**User ID:** {result.user_id}")
                st.write(f"**Timestamp:** {result.timestamp.strftime('%H:%M:%S')}")
        
        
        # Log to history
        st.session_state.query_history.append({
            'timestamp': datetime.now(),
            'query': query,
            'engine': 'phase2_unified',
            'result': result
        })
    
    def display_results(self, query: str, results: Dict[str, Dict]):
        """Zeigt Ergebnisse aller Modi an"""
        # Use full-width container for results
        with st.container():
            st.subheader("📊 Ergebnisse")
            st.markdown(f"**Abfrage:** {query}")
            st.markdown("---")
            
            # Tabs für Modi
            if len(results) > 1:
                tabs = st.tabs([f"{mode.replace('_', ' ').title()}" for mode in results.keys()])
                
                for tab, (mode, result) in zip(tabs, results.items()):
                    with tab:
                        self.display_single_result(mode, result)
            else:
                mode, result = next(iter(results.items()))
                self.display_single_result(mode, result)
        
            # Performance Comparison - inside the container
            if len(results) > 1:
                st.subheader("⚡ Performance-Vergleich")
                perf_data = []
                for mode, result in results.items():
                    perf_data.append({
                        'Modus': mode.replace('_', ' ').title(),
                        'Antwortzeit': f"{result['response_time']:.1f}s",
                        'Quelle': result['source']
                    })
                
                st.table(perf_data)
    
    def display_single_result(self, mode: str, result: Dict):
        """Zeigt einzelnes Ergebnis an"""
        # Mode Badge with appropriate icon
        if mode == 'unified':
            icon = "🚀"
        elif 'json' in mode:
            icon = "🔵"
        elif 'sql' in mode:
            icon = "🟢"
        else:
            icon = "🔶"
        
        st.markdown(f"{icon} **{mode.replace('_', ' ').title()}**")
        
        # Answer - Full width container with explicit expansion
        st.markdown("**Antwort:**")
        with st.container():
            st.markdown(result['answer'])
        
        # Metadata with more metrics - Below the answer
        st.markdown("**Metadaten:**")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Antwortzeit", f"{result['response_time']:.1f}s")
        with cols[1]:
            st.metric("Quelle", result['source'][:15] + "..." if len(result['source']) > 15 else result['source'])
        with cols[2]:
            if 'confidence' in result:
                st.metric("Konfidenz", f"{result.get('confidence', 0):.1%}")
        with cols[3]:
            if 'cost' in result:
                st.metric("Kosten", f"${result.get('cost', 0):.4f}")
    
    def render_history(self):
        """Rendert Session Query-Historie"""
        st.header("📝 Session-Verlauf")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        
        if not st.session_state.query_history:
            st.info("Noch keine Abfragen in dieser Session ausgeführt.")
            return
        
        st.subheader(f"Letzte {len(st.session_state.query_history)} Abfragen")
        
        for i, entry in enumerate(reversed(st.session_state.query_history[-20:])):  # Letzte 20
            with st.expander(f"{entry.get('timestamp', 'unknown').strftime('%H:%M:%S') if hasattr(entry.get('timestamp'), 'strftime') else 'unknown'} - {entry.get('query', 'No query')[:50]}..."):
                st.write(f"**Modi:** {', '.join(entry.get('modes', ['legacy']))}")
                st.write(f"**Abfrage:** {entry.get('query', 'No query')}")
                st.write(f"**Model:** {entry.get('model', 'unknown')}")
                
                # Performance Summary
                results = entry.get('results', {})
                if len(results) > 1:
                    try:
                        avg_time = sum(r.get('response_time', 0) for r in results.values()) / len(results)
                        st.write(f"**Durchschnittliche Antwortzeit:** {avg_time:.1f}s")
                    except (ZeroDivisionError, TypeError):
                        pass
                
                # Show results preview
                for mode, result in results.items():
                    status = "✅" if result.get('success') else "❌"
                    st.write(f"**{mode}** {status}: {result.get('answer', result.get('error', 'No response'))[:100]}...")
    
    def render_query_analytics(self):
        """Rendert umfassende Query Analytics"""
        st.header("📈 Query Analytics & History")
        
        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            days = st.selectbox("Zeitraum", [1, 7, 30, 90], index=1, key="analytics_days")
        with col2:
            if st.button("📊 Analytics aktualisieren"):
                st.rerun()
        
        try:
            # Get statistics
            stats = self.query_logger.get_statistics(days=days)
            
            # Overview metrics
            st.subheader(f"📊 Übersicht (Letzte {days} Tage)")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gesamt Queries", stats['total_queries'])
            with col2:
                st.metric("Erfolgsrate", f"{stats['success_rate']*100:.1f}%")
            with col3:
                st.metric("Ø Antwortzeit", f"{stats['avg_response_time_ms']:.0f}ms")
            with col4:
                st.metric("Kosten", f"${stats['total_cost']:.2f}")
            
            # Mode Distribution
            if stats['mode_distribution']:
                st.subheader("🔄 Mode Verteilung")
                mode_data = stats['mode_distribution']
                
                # Create columns for mode distribution
                cols = st.columns(len(mode_data))
                for i, (mode, count) in enumerate(mode_data.items()):
                    with cols[i]:
                        percentage = (count / stats['total_queries']) * 100 if stats['total_queries'] > 0 else 0
                        st.metric(mode.replace('_', ' ').title(), f"{count} ({percentage:.1f}%)")
            
            # Recent queries
            st.subheader("🕒 Neueste Queries")
            recent_queries = self.query_logger.get_history(limit=20)
            
            if recent_queries:
                # Create a dataframe for better display
                import pandas as pd
                
                df_data = []
                for q in recent_queries:
                    df_data.append({
                        "Timestamp": q['timestamp'][:19],  # Remove microseconds
                        "Query": q['query'][:50] + "..." if len(q['query']) > 50 else q['query'],
                        "Mode": q['mode'],
                        "Model": q['model'],
                        "Success": "✅" if q['success'] else "❌",
                        "Time (ms)": f"{q['response_time_ms']:.0f}",
                        "Results": q['result_count']
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"wincasa_queries_{days}d.csv",
                    mime="text/csv"
                )
            else:
                st.info("Keine Queries in der ausgewählten Zeitspanne gefunden.")
            
            # Popular queries
            st.subheader("🔥 Beliebte Queries")
            popular = self.query_logger.get_popular_queries(days=days, limit=10)
            
            if popular:
                for i, (query, count) in enumerate(popular, 1):
                    st.write(f"{i}. **{query[:80]}{'...' if len(query) > 80 else ''}** ({count}x)")
            else:
                st.info("Keine beliebten Queries gefunden.")
            
            # Performance trends
            st.subheader("📈 Performance Trends")
            trends = self.query_logger.get_performance_trends(days=min(days, 30))
            
            if trends and len(trends) > 1:
                import pandas as pd

                # Create trend dataframe
                trend_df = pd.DataFrame(trends)
                trend_df['date'] = pd.to_datetime(trend_df['date'])
                
                # Plot response time trend
                st.line_chart(trend_df.set_index('date')[['avg_response_time_ms']])
                
                # Plot query volume
                st.bar_chart(trend_df.set_index('date')[['query_count']])
            else:
                st.info("Nicht genügend Daten für Trend-Analyse.")
            
            # Error analysis
            if stats['error_count'] > 0:
                st.subheader("⚠️ Error Analysis")
                error_patterns = self.query_logger.get_error_patterns(days=days)
                
                if error_patterns:
                    for error, count in list(error_patterns.items())[:5]:
                        st.write(f"**{error[:100]}{'...' if len(error) > 100 else ''}**: {count}x")
                
                st.metric("Fehlerrate", f"{(stats['error_count']/stats['total_queries'])*100:.1f}%")
            
            # System statistics
            st.subheader("🔧 System Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Eindeutige User", stats['unique_users'])
            with col2:
                st.metric("Eindeutige Sessions", stats['unique_sessions'])
                
        except Exception as e:
            st.error(f"Fehler beim Laden der Analytics: {e}")
            st.info("Query Logger möglicherweise noch nicht initialisiert. Führen Sie eine Abfrage aus.")
    
    def run(self):
        """Hauptfunktion der App"""
        # Ensure session state is initialized
        self.ensure_session_state()
        
        # Sidebar
        selected_modes, model, temperature = self.render_sidebar()
        
        # Store current model in session state
        st.session_state.current_model = model
        st.session_state.current_temperature = temperature
        
        # Main content
        st.title("🏠 WINCASA Layer 4 - WEG Verwaltungsassistent")
        st.markdown("**Production-Ready JSON Exports & Advanced SQL Analysis**")
        
        # Tabs - Always show tabs, but show warning in query tab if no modes selected
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Abfragen", 
            "📊 System-Info", 
            "📝 Session-Verlauf", 
            "📈 Query Analytics", 
            "📂 JSON Viewer"
        ])
        
        with tab1:
            if not selected_modes:
                st.warning("⚠️ Bitte wählen Sie mindestens einen Modus in der Sidebar aus.")
                st.info("Verfügbare Modi:")
                st.markdown("""
                - **📊 JSON Layer 4 Standard** - Detaillierte Antworten mit JSON-Daten
                - **📋 JSON Layer 4 Vanilla** - Minimale Antworten mit JSON-Daten
                - **🔍 SQL Layer 4 Standard** - Detaillierte Antworten mit SQL-Abfragen
                - **⚡ SQL Layer 4 Vanilla** - Minimale Antworten mit SQL-Abfragen
                - **🚀 Unified Engine** - Intelligente Phase 2 Engine
                """)
            else:
                # Load Layer 4 JSON data for JSON modes
                if any('json' in mode for mode in selected_modes):
                    if not st.session_state.json_data_loaded:
                        with st.spinner("Lade Layer 4 JSON-Daten..."):
                            self.load_json_data()
                self.render_query_interface(selected_modes)
        
        with tab2:
            self.render_system_info(selected_modes, model)
        
        with tab3:
            self.render_history()
        
        with tab4:
            self.render_query_analytics()
        
        with tab5:
            self.render_json_viewer()
    
    def render_json_viewer(self):
        """Layer 4 JSON Data Viewer with search and filtering"""
        st.header("📂 Layer 4 JSON Data Viewer")
        
        # Get available Layer 4 queries
        available_queries = self.layer4_loader.list_available_queries()
        existing_queries = [q for q in available_queries if q['exists']]
        
        if not existing_queries:
            st.warning("Keine Layer 4 JSON-Dateien gefunden.")
            st.info("Layer 4 JSON-Dateien sollten im exports/ Verzeichnis verfügbar sein.")
            return
        
        # Query selector with categories
        categories = ['Alle'] + list(set(q['category'] for q in existing_queries))
        selected_category = st.selectbox("Kategorie:", categories)
        
        # Filter queries by category
        if selected_category == 'Alle':
            filtered_queries = existing_queries
        else:
            filtered_queries = [q for q in existing_queries if q['category'] == selected_category]
        
        # Query selector
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_query = st.selectbox(
                "Layer 4 Query auswählen:",
                filtered_queries,
                format_func=lambda x: f"{x['name']}: {x['rows']:,} Zeilen - {x['description']}"
            )
        
        with col2:
            if st.button("🔄 Aktualisieren"):
                st.rerun()
        
        # Load selected query data
        if selected_query:
            try:
                query_name = selected_query['name']
                data = self.layer4_loader.load_json_data(query_name)
                
                if not data:
                    st.error(f"Fehler beim Laden der Query: {query_name}")
                    return
                
                # Data explorer
                st.subheader("🔍 Layer 4 Daten Explorer")
                
                # Show query info
                query_info = data.get('query_info', {})
                summary = data.get('summary', {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Datensätze", f"{summary.get('row_count', 0):,}")
                with col2:
                    st.metric("Spalten", len(data.get('columns', [])))
                with col3:
                    st.metric("Kategorie", selected_query['category'].title())
                
                # Query metadata
                with st.expander("📋 Query-Details"):
                    st.write(f"**Business Purpose:** {query_info.get('business_purpose', 'N/A')}")
                    st.write(f"**Generated:** {query_info.get('generated', 'N/A')}")
                    if query_info.get('sql_file'):
                        st.write(f"**SQL Template:** {query_info['sql_file']}")
                
                # Get the actual data
                json_data = data.get('data', [])
                
                if not json_data:
                    st.warning("Keine Daten in diesem Export vorhanden.")
                    return
                
                # Search box
                search_term = st.text_input("🔍 Suche in allen Feldern:", "")
                
                # Filter data if search term provided
                if search_term:
                    filtered_data = []
                    for item in json_data:
                        # Search in all string fields
                        if any(search_term.lower() in str(v).lower() for v in item.values()):
                            filtered_data.append(item)
                    display_data = filtered_data
                    st.info(f"Gefunden: {len(filtered_data)} von {len(json_data)} Einträgen")
                else:
                    display_data = json_data
                    
                    # Display options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        show_table = st.checkbox("📊 Als Tabelle", value=True)
                    with col2:
                        show_json = st.checkbox("📄 Als JSON", value=False)
                    with col3:
                        limit = st.number_input("Max. Einträge:", min_value=1, max_value=1000, value=100, step=10)
                    
                    # Display data
                    if display_data:
                        limited_data = display_data[:limit]
                        
                        if show_table:
                            import pandas as pd
                            df = pd.DataFrame(limited_data)
                            st.dataframe(df, use_container_width=True)
                            
                            # Download button
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Als CSV herunterladen",
                                data=csv,
                                file_name=f"{query_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime='text/csv'
                            )
                        
                        if show_json:
                            st.json(limited_data)
                    else:
                        st.warning("Keine Daten gefunden.")
                        
                # Statistics
                if json_data:
                    st.subheader("📊 Statistiken")
                    st.write(f"- Gesamt Einträge: {len(json_data)}")
                    if json_data and isinstance(json_data[0], dict):
                        all_keys = set()
                        for item in json_data[:10]:  # Check first 10 items for keys
                            all_keys.update(item.keys())
                        st.write(f"- Felder: {', '.join(sorted(all_keys)[:10])}")
                        if len(all_keys) > 10:
                            st.write(f"  ... und {len(all_keys)-10} weitere Felder")
                    
            except Exception as e:
                st.error(f"Fehler beim Laden der Datei: {e}")
    
    
    def render_system_info(self, selected_modes: List[str], model: str):
        """Zeigt System-Informationen an"""
        st.subheader("🔧 System-Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Gewählte Modi:**")
            for mode in selected_modes:
                icon = "📊" if "json" in mode else "🔍"
                st.write(f"{icon} {mode.replace('_', ' ').title()}")
        
        with col2:
            st.markdown("**LLM-Konfiguration:**")
            st.write(f"🤖 Provider: OpenAI")
            st.write(f"🧠 Model: {model}")
        
        # Data Status
        st.subheader("📁 Datenstatus")
        
        # Layer 4 JSON Data Status
        if any('json' in mode for mode in selected_modes):
            if st.session_state.json_data_loaded:
                st.success("✅ Layer 4 JSON-Daten geladen")
                for query_name, data in st.session_state.json_data.items():
                    if isinstance(data, dict) and 'data' in data:
                        row_count = len(data['data'])
                        st.write(f"  - {query_name}: {row_count:,} Datensätze")
            else:
                st.warning("⚠️ Layer 4 JSON-Daten nicht geladen")
                
            # Show Layer 4 statistics
            try:
                stats = self.layer4_loader.get_summary_statistics()
                st.info(f"Verfügbar: {stats['total_queries']} Queries mit {stats['total_rows']:,} Datensätzen")
            except Exception as e:
                st.warning(f"Fehler beim Laden der Statistiken: {e}")
        
        # SQL Connection Status
        if any('sql' in mode for mode in selected_modes):
            db_path = self.config.get('db_path')
            if os.path.exists(db_path):
                st.success(f"✅ Datenbank verfügbar: {os.path.basename(db_path)}")
            else:
                st.error(f"❌ Datenbank nicht gefunden: {db_path}")


def get_app():
    """App initialization without caching to prevent ghost buttons"""
    try:
        # Check if app is already in session state to avoid re-initialization
        if 'wincasa_app' not in st.session_state:
            st.session_state.wincasa_app = WincasaStreamlitApp()
            # Verify that query engine is initialized
            if not hasattr(st.session_state.wincasa_app, 'query_engine') or st.session_state.wincasa_app.query_engine is None:
                logger.warning("Query engine initialization failed in app")
        return st.session_state.wincasa_app
    except Exception as e:
        logger.error(f"Failed to initialize WincasaStreamlitApp: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def init_session_state():
    """Initialize session state variables"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = {}
    if 'json_data_loaded' not in st.session_state:
        st.session_state.json_data_loaded = False
    if 'json_data' not in st.session_state:
        st.session_state.json_data = {}
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
    # Phase 2 state
    if 'use_unified_engine' not in st.session_state:
        st.session_state.use_unified_engine = False

if __name__ == "__main__":
    # Initialize session state before creating app
    init_session_state()
    app = get_app()
    app.run()