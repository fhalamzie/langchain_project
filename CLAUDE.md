# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

WINCASA is a production-ready German property management system with AI-powered query interface, knowledge-based SQL generation, and comprehensive data exports. The system features dual architecture: legacy modes (1-4) and unified intelligent engine (mode 5).

**Current Status**: Cleaned, production-ready codebase with 100% Phase 2 completion.

## Core Architecture

### Dual Query System
- **Legacy Modes (1-4)**: Direct LLM → Database/JSON pattern
- **Unified Engine (5)**: Intelligent routing through Template → Search → Legacy fallback
- **Knowledge System**: 226 field mappings extracted from SQL files prevent field errors

### Key Components
```
streamlit_app.py          # Main UI with 5-mode selection
wincasa_query_engine.py   # Phase 2 intelligent routing engine  
llm_handler.py           # Legacy modes LLM integration
layer4_json_loader.py    # JSON data access layer
knowledge_extractor.py   # Extracts field mappings from SQL files
wincasa_unified_logger.py # Query path tracking and analytics
data_access_layer.py     # Unified data access abstraction
wincasa_optimized_search.py # High-performance search (1-5ms)
```

### Data Flow Architecture
```
Query Input → Mode Router → Execution Engine → Results Display
     ↓             ↓              ↓              ↓
Streamlit UI → Query Engine → (JSON|SQL|Search) → Formatted Output
     ↓             ↓              ↓              ↓  
Session State → Logger → Database/Files → Analytics Dashboard
```

## Developer Navigation

### 🗺️ Code Map - Where to Find What

#### **🎯 Entry Points by Task**
```python
# NEW DEVELOPER START HERE:
streamlit_app.py          # UI Entry Point - Main application
  └── Line 89: execute_query()  # Core query execution method

# WORKING ON MODE 5 (UNIFIED ENGINE):
wincasa_query_engine.py   # Intelligent routing engine
  └── Line 45: execute_query()     # 3-path routing logic
  └── Line 78: route_query()       # Intent classification & routing

# WORKING ON LEGACY MODES (1-4):
llm_handler.py           # Legacy LLM integration
  └── Line 34: process_query()     # Legacy query processing
  └── Line 156: _enhance_with_knowledge()  # Knowledge base integration

# WORKING ON DATA ACCESS:
layer4_json_loader.py    # JSON data operations
data_access_layer.py     # Unified data abstraction  
wincasa_optimized_search.py  # 1-5ms search engine
```

#### **🔧 Core Functions to Debug**
```python
# Query Execution Flow:
1. streamlit_app.py:89 → execute_query()
2. wincasa_query_engine.py:45 → execute_query() [Mode 5]
   OR llm_handler.py:34 → process_query() [Mode 1-4] 
3. layer4_json_loader.py:67 → search() [Data layer]

# Performance Critical:
wincasa_optimized_search.py:123 → search()  # <5ms target
sql_template_engine.py:89 → execute_template()  # ~100ms target

# Business Logic:
knowledge_base_loader.py:45 → enhance_query()  # Field mapping injection
```

#### **🧪 Testing & Debugging Files**
```python
# Quick Testing:
test_suite_quick.py      # Fast test subset (5 key tests)
test_golden_queries_kb.py # Real business queries
debug_single_query.py    # Interactive query debugging (create this)

# Comprehensive Testing:  
test_suite_phase2.py     # Full test suite (26 tests)
benchmark_current_modes.py # Performance comparison

# Data Validation:
test_layer4.py          # SQL→JSON export validation
knowledge_extractor.py  # Field mapping analysis
```

#### **📊 Monitoring & Logs**
```python
# Log Analysis:
logs/layer2.log              # Main application logs (783KB)
logs/layer2_api.log          # API interactions (13MB)
logs/layer2_performance.log  # Performance metrics (811KB)
logs/query_paths.log         # Query routing decisions (6KB)

# Analytics:
wincasa_analytics_system.py     # Business metrics dashboard
wincasa_monitoring_dashboard.py # Real-time monitoring
wincasa_unified_logger.py       # Central logging framework
```

### 🐛 Debugging Workflow

#### **Debug a Specific Query:**
```bash
# 1. Quick test single query
python -c "
from streamlit_app import WincasaStreamlitApp
app = WincasaStreamlitApp()
result = app.execute_mode('Zeige alle Mieter', 'UNIFIED')
print(f'Result: {result}')
"

# 2. Debug with full tracing  
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# ... same as above
"

# 3. Mode comparison
python benchmark_current_modes.py --query='Ihre Test Query'
```

#### **Debug Mode 5 Routing:**
```bash
# Set breakpoint at routing decision
python -c "
from wincasa_query_engine import WincasaQueryEngine
engine = WincasaQueryEngine()
import pdb; pdb.set_trace()  # Manual breakpoint
result = engine.execute_query('Test query')
"
```

#### **Debug Legacy Modes:**
```bash
# Test specific legacy mode
python -c "
from llm_handler import process_query
import pdb; pdb.set_trace()
result = process_query('Test query', 'JSON_VANILLA')
"
```

### 📚 Architecture Deep Dive

#### **Mode 5 (Unified Engine) Flow:**
```
Query → Intent Classification → Route Decision
                ↓
    ┌─────────────────────────────────┐
    │ 1. Template Engine (~100ms)    │ → SQL Templates
    │ 2. Optimized Search (1-5ms)    │ → In-Memory Index  
    │ 3. Legacy Fallback (500-2000ms)│ → LLM Generation
    └─────────────────────────────────┘
                ↓
        Unified Response Format
```

#### **Legacy Modes (1-4) Flow:**
```
Query → LLM Processing → Data Layer → Response
   ↓         ↓              ↓           ↓
User → llm_handler → layer4_json → Formatted Results
```

## Developer Commands

### 🚀 Server Management
```bash
# Basic server operations
./run_streamlit.sh               # Start web interface (port 8667)
./run_streamlit.sh --restart     # Clean restart (kills all streamlit processes)
./run_streamlit.sh 8668          # Custom port
./run_streamlit.sh 8667 127.0.0.1  # Local only

# Developer modes  
./run_streamlit.sh --dev         # Developer mode (verbose logging)
./run_streamlit.sh --debug       # Debug mode (with breakpoint instructions)
./run_streamlit.sh --test        # Test mode (runs tests before starting)
./run_streamlit.sh --restart --debug  # Clean restart in debug mode

# Environment setup
# Script automatically creates venv/ and installs dependencies from requirements.txt
# Run ./run_streamlit.sh on first setup - handles everything automatically
```

### 🧪 Testing Commands
```bash
# Quick testing
python test_suite_quick.py       # Fast test subset (5 tests)
python test_golden_queries_kb.py # Test with real business queries
python benchmark_current_modes.py # Performance comparison of all modes

# Comprehensive testing
python test_suite_phase2.py      # Full test suite (26 tests)
python test_layer4.py            # SQL→JSON export validation

# Mode-specific testing
python -c "
from wincasa_query_engine import WincasaQueryEngine
engine = WincasaQueryEngine()
result = engine.execute_query('Test query')
print(f'Mode 5 result: {result}')
"

# Legacy mode testing
python -c "
from llm_handler import process_query  
result = process_query('Test query', 'JSON_VANILLA')
print(f'Legacy result: {result}')
"
```

### 🔧 Development Utilities
```bash
# Data operations
./export_json.sh                 # Export all SQL queries to JSON
python knowledge_extractor.py    # Extract field mappings from SQL files

# Debug single query
python -c "
from streamlit_app import WincasaStreamlitApp
app = WincasaStreamlitApp()
import pdb; pdb.set_trace()  # Manual breakpoint
result = app.execute_mode('Zeige alle Mieter', 'UNIFIED')
"

# Real-time log monitoring
tail -f logs/layer2.log          # Main application logs
tail -f logs/layer2_performance.log  # Performance metrics
tail -f logs/query_paths.log     # Query routing decisions

# Clean development environment
find . -name "*.pyc" -delete     # Clear Python cache
find . -name "__pycache__" -delete # Clear cache directories

# Server restart procedures (if experiencing issues)
./run_streamlit.sh --restart     # Recommended: Clean restart with cache clearing
pkill -f "streamlit"             # Manual: Kill all streamlit processes
lsof -ti:8667 | xargs kill       # Manual: Kill process on specific port
```

### Data Operations
```bash
./export_json.sh                 # Export all 35 SQL queries to JSON
python3 test_layer4.py           # Test all SQL queries
python3 knowledge_extractor.py   # Extract field mappings from SQL files
```

### Testing & Validation
```bash
# Core testing
python3 test_layer4.py                    # Test all SQL queries
python3 json_exporter.py --verify         # Verify JSON exports

# Phase 2 testing 
python3 test_suite_phase2.py              # Run full test suite (26 tests)
python3 benchmark_current_modes.py        # Performance baseline testing
python3 test_golden_queries_kb.py         # Test knowledge base integration

# Quick testing
python3 test_suite_quick.py               # Fast test subset
python3 test_kaltmiete_query.py           # Test specific critical query
```

### Export Operations
```bash
# Single query export
python3 json_exporter.py --single 01_eigentuemer.sql

# Export with verification  
python3 json_exporter.py --verify --min-rows 10

# View export status
cat exports/_export_summary.json
cat exports/_verification_summary.json
```

## Development Guidelines

### Session State Management
The UI uses session-based app initialization to prevent ghost buttons:
```python
# In streamlit_app.py
if 'wincasa_app' not in st.session_state:
    st.session_state.wincasa_app = WincasaStreamlitApp()
```

### Button Key Requirements
All buttons must use session-unique keys to prevent duplicates:
```python
execute_key = f"main_execute_button_{st.session_state.session_id}"
st.button("🔍 Abfrage ausführen", key=execute_key)
```

### Configuration Management
All paths centralized in `config/sql_paths.json`:
```json
{
  "sql_queries_dir": "SQL_QUERIES",
  "json_exports_dir": "exports", 
  "database_path": "wincasa_data/WINCASA2022.FDB",
  "source_data_dir": "wincasa_data/source"
}
```

### Query Engine Integration
The unified engine bypasses legacy handlers completely:
```python
# Legacy: streamlit → llm_handler → layer4_json_loader
# Unified: streamlit → wincasa_query_engine → (template|search|fallback)
```

## Critical Business Rules

- `EIGNR = -1`: All WEG owners collectively
- `ONR >= 890`: System/test data (excluded from queries)
- `VENDE IS NULL`: Active tenant contracts only
- `KKLASSE = 62`: WEG owner accounts
- **CRITICAL**: `KALTMIETE = BEWOHNER.Z1` (not KBETRAG!) - fixed in knowledge base

## Knowledge Base System

### Field Mapping Extraction
```bash
python3 knowledge_extractor.py  # Analyzes 35 SQL files → 226 mappings
```

### Runtime Integration
The knowledge base automatically injects critical mappings into LLM prompts:
```python
# In knowledge_base_loader.py
if 'kaltmiete' in query.lower():
    return query + "\nWICHTIG: KALTMIETE = BEWOHNER.Z1"
```

## UI Layout Best Practices

### Container Structure
Results must use full-width containers to prevent narrow display:
```python
def display_results(self, query: str, results: Dict[str, Dict]):
    with st.container():  # Full-width container
        st.subheader("📊 Ergebnisse")
        # ... rest of results display
```

### Mode Selection Logic
Always show tabs regardless of mode selection to prevent UI blocking:
```python
# Always show tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([...])

with tab1:
    if not selected_modes:
        st.warning("⚠️ Bitte wählen Sie mindestens einen Modus aus.")
    else:
        self.render_query_interface(selected_modes)
```

## Production Data

- **35 SQL queries** → **35 JSON exports** (229,500 total rows)
- **311 owners**, **189 tenants**, **77 properties**, **539 apartments**
- **Export Status**: 32/35 queries have ≥10 rows (3 have 0-5 rows due to good payment behavior)

## Security & Environment

- API keys: `/home/envs/openai.env` (not in repository)
- Firebird embedded mode (no server required)
- UTF-8 encoding for German characters
- 100k row safety limit prevents runaway queries

## Query Logging & Analytics

### Central Logging System
```bash
# Database location
wincasa_data/query_logs.db  # SQLite database with query history
```

### Logging Integration
All queries automatically logged with metadata:
```python
from wincasa_query_logger import get_query_logger, QueryLogEntry

logger = get_query_logger()  # Singleton pattern
entry = QueryLogEntry(
    query="Zeige alle Mieter",
    mode="optimized_search", 
    response_time_ms=125.5,
    success=True
)
logger.log_query(entry)
```

### Analytics Features
- **Cross-Session History**: View queries from previous sessions
- **Performance Trends**: Response time and query volume charts  
- **Mode Distribution**: Usage patterns across query modes
- **Error Analysis**: Systematic error pattern tracking
- **Cost Tracking**: API usage optimization

## Phase 2 Status: COMPLETE

All Phase 2 components are production-ready:
- ✅ **42/42 tasks completed** (107h actual vs 200h estimate)  
- ✅ **100% test coverage** (26/26 tests passing)
- ✅ **Knowledge-based SQL system** with 226 field mappings
- ✅ **Unified query engine** with intelligent routing
- ✅ **Performance improvements**: 1-5ms search, 100ms templates
- ✅ **Central logging system** with persistent storage and analytics