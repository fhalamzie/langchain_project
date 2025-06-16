#!/usr/bin/env python3
"""
WINCASA Benchmark Streamlit UI - Stable Version
Compares all 5 modes with proper database handling
"""

import json
import logging
import os
import time
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st

from wincasa.utils.text_to_table_parser import extract_table_from_answer, is_table_data

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import WINCASA modules with error handling
try:
    from wincasa.core.llm_handler import WincasaLLMHandler
    from wincasa.core.wincasa_query_engine import WincasaQueryEngine
    from wincasa.data.layer4_json_loader import Layer4JSONLoader
    from wincasa.utils.config_loader import WincasaConfig
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Failed to import WINCASA modules: {e}")

# LLM Models and pricing
LLM_MODELS = {
    'gpt-4o-mini': {
        'name': 'GPT-4o Mini',
        'description': 'Most cost-effective',
        'input_cost': 0.15,
        'output_cost': 0.60
    },
    'gpt-4o': {
        'name': 'GPT-4o',
        'description': 'Premium multimodal',
        'input_cost': 2.50,
        'output_cost': 10.00
    },
    'o1-mini': {
        'name': 'O1 Mini',
        'description': 'Fast reasoning',
        'input_cost': 3.00,
        'output_cost': 12.00
    },
    'o1': {
        'name': 'O1',
        'description': 'Advanced reasoning',
        'input_cost': 15.00,
        'output_cost': 60.00
    }
}

# WINCASA Modes
MODES = {
    'json_standard': '📊 JSON Standard',
    'json_vanilla': '📋 JSON Vanilla',
    'sql_standard': '🔍 SQL Standard', 
    'sql_vanilla': '⚡ SQL Vanilla',
    'unified': '🚀 Unified Engine'
}

class BenchmarkStreamlit:
    """Stable benchmark UI with proper initialization"""
    
    def __init__(self):
        """Initialize handlers carefully"""
        self._llm_handler = None
        self._query_engine = None
        self._layer4_loader = None
        self._initialized = False
        logger.info("BenchmarkStreamlit initialized")
    
    def init_handlers(self):
        """Initialize handlers once when needed"""
        if self._initialized:
            return
        
        try:
            # Initialize config first
            self.config = WincasaConfig()
            
            # Initialize handlers one by one
            logger.info("Initializing LLM handler...")
            self._llm_handler = WincasaLLMHandler()
            
            logger.info("Initializing Layer4 loader...")
            self._layer4_loader = Layer4JSONLoader()
            
            logger.info("Initializing Query engine...")
            self._query_engine = WincasaQueryEngine()
            
            self._initialized = True
            logger.info("✅ All handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            st.error(f"Initialization failed: {e}")
            self._initialized = False
    
    def execute_single_mode(self, query: str, mode: str, model: str) -> Dict[str, Any]:
        """Execute query in a single mode with proper error handling"""
        logger.info(f"Executing mode {mode} with model {model}")
        start_time = time.time()
        
        try:
            if mode == 'unified':
                # Unified engine doesn't use LLM model
                if not self._query_engine:
                    raise Exception("Query engine not initialized")
                
                result = self._query_engine.process_query(query)
                
                return {
                    'success': True,
                    'answer': result.answer,
                    'time': time.time() - start_time,
                    'confidence': result.confidence,
                    'cost': result.cost_estimate,
                    'processing_mode': result.processing_mode,
                    'result_count': result.result_count
                }
            else:
                # LLM-based modes
                if not self._llm_handler:
                    raise Exception("LLM handler not initialized")
                
                # Set model temporarily
                original_model = os.environ.get('OPENAI_MODEL')
                os.environ['OPENAI_MODEL'] = model
                
                try:
                    # Execute query
                    result = self._llm_handler.query_llm(query, mode)
                    
                    return {
                        'success': result.get('success', True),
                        'answer': result.get('answer', 'No answer'),
                        'time': time.time() - start_time,
                        'cost': self.estimate_cost(result, model),
                        'source': result.get('source', mode)
                    }
                finally:
                    # Restore original model
                    if original_model:
                        os.environ['OPENAI_MODEL'] = original_model
                    else:
                        os.environ.pop('OPENAI_MODEL', None)
                
        except Exception as e:
            logger.error(f"Error in mode {mode}: {e}")
            return {
                'success': False,
                'answer': f"Error: {str(e)}",
                'time': time.time() - start_time,
                'cost': 0,
                'error': str(e)
            }
    
    def estimate_cost(self, result: Dict, model: str) -> float:
        """Estimate cost based on model"""
        if model not in LLM_MODELS:
            return 0.001
        
        # Simple estimation
        tokens = result.get('total_tokens', 1000)
        model_info = LLM_MODELS[model]
        
        cost = (tokens * model_info['input_cost'] / 1_000_000)
        return max(cost, 0.0001)
    
    def run_benchmark(self, query: str, model: str) -> Dict[str, Any]:
        """Run benchmark across all modes sequentially"""
        results = {}
        
        # Initialize handlers if needed
        if not self._initialized:
            with st.spinner("Initializing handlers..."):
                self.init_handlers()
        
        if not self._initialized:
            st.error("Failed to initialize handlers")
            return {}
        
        # Progress tracking
        progress = st.progress(0)
        status = st.empty()
        
        modes = list(MODES.keys())
        
        # Execute each mode sequentially to avoid database conflicts
        for i, mode in enumerate(modes):
            status.text(f"Executing {MODES[mode]}...")
            progress.progress((i + 1) / len(modes))
            
            # Small delay between modes to avoid conflicts
            if i > 0:
                time.sleep(0.1)
            
            results[mode] = self.execute_single_mode(query, mode, model)
        
        progress.empty()
        status.empty()
        
        return results
    
    def display_results(self, query: str, model: str, results: Dict[str, Any]):
        """Display benchmark results"""
        st.markdown("### 📊 Benchmark Results")
        st.markdown(f"**Query:** {query}")
        st.markdown(f"**Model:** {LLM_MODELS.get(model, {}).get('name', model)}")
        st.markdown("---")
        
        # Summary table
        summary_data = []
        for mode, result in results.items():
            summary_data.append({
                'Mode': MODES[mode],
                'Status': '✅' if result['success'] else '❌',
                'Time (s)': f"{result['time']:.2f}",
                'Cost ($)': f"{result.get('cost', 0):.4f}",
                'Answer Length': len(result['answer'])
            })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)
        
        # Detailed results in tabs
        tabs = st.tabs([MODES[mode] for mode in results.keys()])
        
        for tab, (mode, result) in zip(tabs, results.items()):
            with tab:
                if result['success']:
                    st.success("✅ Success")
                else:
                    st.error("❌ Failed")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Response Time", f"{result['time']:.2f}s")
                with col2:
                    st.metric("Cost", f"${result.get('cost', 0):.4f}")
                with col3:
                    if 'confidence' in result:
                        st.metric("Confidence", f"{result.get('confidence', 0):.1%}")
                
                # Answer with JSON detection
                st.markdown("**Answer:**")
                
                # Check if answer is JSON
                answer = result['answer']
                is_json = False
                json_data = None
                table_df = None
                remaining_text = None
                
                # Try to parse as JSON
                if isinstance(answer, str) and (answer.strip().startswith('{') or answer.strip().startswith('[')):
                    try:
                        json_data = json.loads(answer)
                        is_json = True
                    except:
                        pass
                
                # If not JSON, try to extract table from text
                if not is_json and isinstance(answer, str) and is_table_data(answer):
                    table_df, remaining_text = extract_table_from_answer(answer)
                
                if is_json and json_data:
                    # Display as formatted JSON with table option
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        view_mode = st.radio(
                            "View as:",
                            ["Table", "JSON", "Text"],
                            key=f"view_{mode}"
                        )
                    
                    if view_mode == "Table":
                        # Try to convert JSON to table
                        if isinstance(json_data, list) and len(json_data) > 0:
                            # List of records - perfect for table
                            df = pd.DataFrame(json_data)
                            st.dataframe(df, use_container_width=True)
                        elif isinstance(json_data, dict):
                            # Single record or nested structure
                            if all(isinstance(v, (str, int, float, bool, type(None))) for v in json_data.values()):
                                # Simple dict - show as single row table
                                df = pd.DataFrame([json_data])
                                st.dataframe(df, use_container_width=True)
                            else:
                                # Complex nested structure - show as JSON
                                st.info("Complex nested structure - showing as JSON")
                                st.json(json_data)
                        else:
                            st.json(json_data)
                    elif view_mode == "JSON":
                        st.json(json_data)
                    else:
                        st.markdown(answer)
                elif table_df is not None and not table_df.empty:
                    # Display parsed table from text
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        view_mode = st.radio(
                            "View as:",
                            ["Table", "Text"],
                            key=f"view_text_{mode}"
                        )
                    
                    if view_mode == "Table":
                        # Show any header text
                        if remaining_text:
                            st.markdown(remaining_text)
                        # Show table
                        st.dataframe(table_df, use_container_width=True)
                    else:
                        st.markdown(answer)
                else:
                    # Regular text display
                    st.markdown(answer)
                
                # Debug info
                if st.checkbox(f"Show debug info for {MODES[mode]}", key=f"debug_{mode}"):
                    debug_info = {k: v for k, v in result.items() if k != 'answer'}
                    st.json(debug_info)
        
        # Performance comparison
        st.markdown("### ⏱️ Performance Comparison")
        perf_df = pd.DataFrame({
            'Mode': [MODES[m] for m in results.keys()],
            'Time (s)': [r['time'] for r in results.values()]
        })
        st.bar_chart(perf_df.set_index('Mode'))
    
    def render_sidebar(self):
        """Render sidebar"""
        st.sidebar.title("🔬 Benchmark Settings")
        
        # Model selection
        st.sidebar.subheader("🤖 LLM Model")
        model = st.sidebar.selectbox(
            "Select model:",
            options=list(LLM_MODELS.keys()),
            format_func=lambda x: f"{LLM_MODELS[x]['name']} - {LLM_MODELS[x]['description']}"
        )
        
        # Show pricing
        model_info = LLM_MODELS[model]
        st.sidebar.info(
            f"**Pricing (per 1M tokens):**\n"
            f"Input: ${model_info['input_cost']:.2f}\n"
            f"Output: ${model_info['output_cost']:.2f}"
        )
        
        # Mode info
        st.sidebar.subheader("ℹ️ Modes")
        st.sidebar.markdown("All 5 modes will be tested:")
        for mode_key, mode_name in MODES.items():
            st.sidebar.write(f"• {mode_name}")
        
        return model
    
    def render_query_section(self, model: str):
        """Render query input section"""
        st.header("🔍 Benchmark Query")
        
        # Example queries
        examples = {
            "Simple": "Zeige alle Eigentümer",
            "Search": "Wer wohnt in der Marienstr. 26?",
            "Analysis": "Summe aller Kaltmieten",
            "Complex": "Mieteinnahmen 2024 nach Objekten"
        }
        
        cols = st.columns(len(examples))
        for col, (label, query) in zip(cols, examples.items()):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state.query = query
        
        # Query input
        query = st.text_area(
            "Enter your query:",
            value=st.session_state.get('query', ''),
            height=100
        )
        
        # Run button
        if st.button("🚀 Run Benchmark", type="primary", use_container_width=True):
            if query:
                with st.spinner(f"Running benchmark with {LLM_MODELS[model]['name']}..."):
                    results = self.run_benchmark(query, model)
                    
                    if results:
                        st.session_state.last_results = {
                            'query': query,
                            'model': model,
                            'results': results,
                            'timestamp': datetime.now()
                        }
            else:
                st.error("Please enter a query")
    
    def run(self):
        """Main app loop"""
        st.title("🔬 WINCASA Benchmark Tool")
        st.markdown("Compare all 5 modes with different LLM models")
        
        # Sidebar
        model = self.render_sidebar()
        
        # Main content
        self.render_query_section(model)
        
        # Results
        if 'last_results' in st.session_state:
            st.markdown("---")
            data = st.session_state.last_results
            self.display_results(data['query'], data['model'], data['results'])
            
            # Export options
            st.markdown("### 💾 Export")
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV export
                export_data = []
                for mode, result in data['results'].items():
                    export_data.append({
                        'Mode': MODES[mode],
                        'Query': data['query'],
                        'Model': data['model'],
                        'Success': result['success'],
                        'Time': result['time'],
                        'Cost': result.get('cost', 0),
                        'Answer': result['answer']
                    })
                
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # JSON export
                json_export = {
                    'timestamp': data['timestamp'].isoformat(),
                    'query': data['query'],
                    'model': data['model'],
                    'results': data['results']
                }
                
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(json_export, indent=2),
                    file_name=f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )


def main():
    """Main entry point"""
    st.set_page_config(
        page_title="WINCASA Benchmark",
        page_icon="🔬",
        layout="wide"
    )
    
    # Initialize session state
    if 'query' not in st.session_state:
        st.session_state.query = ''
    
    # Create and run app
    app = BenchmarkStreamlit()
    app.run()


if __name__ == "__main__":
    main()