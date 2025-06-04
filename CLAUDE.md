# LLM Development Guidelines - WINCASA System

## Project Context
Intelligent natural language database query system for Firebird databases using LLM agents. Processes SQL queries from German/English natural language input with multi-modal RAG retrieval and real-time monitoring.

## Core Tech Stack
- **Backend:** Python, Firebird FDB, LangChain, SQLAlchemy, Phoenix Monitoring, Context7 MCP
- **LLM Integration:** OpenAI GPT-4, OpenRouter APIs, Local SQLCoder models
- **RAG System:** FAISS vectorization, Multi-stage retrieval, Hybrid context strategy
- **Infrastructure:** Streamlit UI, Direct FDB interface, SQLite monitoring backend

---

## Development Guidelines for LLM

### 🧪 **MANDATORY: Testing Before Completion**
**CRITICAL:** Every new feature MUST include comprehensive tests BEFORE marking as complete:
- **Unit Tests** for all new functions and modules
- **Integration Tests** for database connections and LLM integrations
- **System Tests** for complete query workflows and retrieval modes
- **Performance Tests** for query execution and retrieval benchmarks
- **Execute test suites after every implementation**
- **Tests must pass BEFORE git commit/push**
- **Minimum 90% code coverage for new modules**

### 🔧 **Testing Commands**
```bash
# Before every commit:
python -m pytest tests/ -v                    # Unit tests (when available)
python test_enhanced_qa_ui_integration.py     # Core integration test
python test_fdb_direct_interface.py          # Database interface test
python test_firebird_sql_agent.py            # Agent functionality test
python test_business_glossar_simple.py       # Business glossar validation

# System-level testing:
python optimized_retrieval_test.py --concurrent --workers 2  # All modes
python quick_hybrid_context_test.py --timeout 45            # Quick validation
python test_langchain_fix.py                               # LangChain integration

# Performance benchmarks:
python automated_retrieval_test.py                         # Comprehensive evaluation
python iterative_improvement_test.py                      # Context strategy testing

# Coverage check (when pytest configured):
pytest --cov=firebird_sql_agent_direct --cov-report=html
```

### 📝 **Git & Commits**
- **Regular commits** with meaningful commit messages following conventional format
- **Reference file locations** using pattern `file_path:line_number`
- **Push to GitHub** regularly to maintain backup
- **Test locally first, then commit** - no exceptions (no CI/CD, all testing done locally)
- **Each retrieval mode change** requires dedicated commit
- **Update CLAUDE.md** for all significant changes

### 🏗️ **Code Structure Rules**
- **Max 800 lines per .py file** (prefer 500 lines for complex SQL logic)
- **Modular architecture** with clear separation between retrieval modes
- **Every module starts** with descriptive docstring explaining purpose
- **Use existing patterns** from `firebird_sql_agent_direct.py` and `enhanced_retrievers.py`
- **Follow existing code conventions** especially for Firebird SQL generation
- **Consistent error handling** patterns across all modes

### 📚 **Documentation Requirements**
- **Update CLAUDE.md** after every major change (retrieval modes, LLM integrations)
- **README.md updates** for user-facing functionality changes
- **Code documentation** for complex SQL generation logic
- **Performance documentation** for new retrieval optimizations
- **API key management** documentation updates

### ⚙️ **Environment & Configuration**
- **Primary config:** Environment variables in `/home/envs/`
- **API Keys location:** `/home/envs/openai.env`, `/home/envs/openrouter.env`
- **Database:** `WINCASA2022.FDB` (151 tables, 517 apartments, 698 residents)
- **Firebird Server:** Port 3050 for LangChain mode
- **Phoenix Monitoring:** SQLite backend at `localhost:6006`
- **Test files:** Use `/logs/` for test outputs and analysis

### 🔍 **Development Workflow**
1. **Read existing code** to understand retrieval mode patterns
2. **Write tests first** for new SQL agent functionality
3. **Implement feature** following existing Firebird conventions
4. **Run test suite** and ensure all retrieval modes pass
5. **Update documentation** including performance metrics
6. **Commit with clear message** referencing specific components
7. **Verify in both server and embedded Firebird modes**

### 📍 **File References**
Always reference specific code locations as `file_path:line_number` for easy navigation.

### 🚨 **Critical Paths**
- **SQL Agent Core:** `firebird_sql_agent_direct.py:1-800`
- **Retrieval System:** `enhanced_retrievers.py:1-600`
- **Database Interface:** `fdb_direct_interface.py:1-400`
- **LangChain Integration:** `langchain_sql_retriever_fixed.py:1-300`
- **Global Context:** `global_context.py:1-200`
- **Business Glossar:** `business_glossar.py:1-600`
- **Phoenix Monitoring:** `phoenix_monitoring.py:1-400`

---

## 🚀 **Quick Project Status**

### Current Implementation Status
- ✅ **All 5 Retrieval Modes:** Enhanced, FAISS, None, SQLCoder, LangChain fully operational
- ✅ **Firebird Integration:** Direct FDB interface + server mode for LangChain
- ✅ **LLM Agents:** OpenAI GPT-4, OpenRouter fallback, local SQLCoder support
- ✅ **MCP Context7:** Real-time LangChain documentation integration
- ✅ **Phoenix Monitoring:** OTEL tracing with SQLite backend optimization
- ✅ **Hybrid Context Strategy:** Global context + dynamic retrieval implemented

### Active Interfaces & Deployment
- **Development UI:** `http://localhost:8501` (Streamlit with all features)
- **Production UI:** `http://localhost:8502` (Clean interface)
- **Phoenix Dashboard:** `http://localhost:6006` (Performance monitoring)
- **Command Line:** `python run_llm_query.py` (Direct queries)

### Development Environment Setup
```bash
# Quick start:
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project
pip install -r requirements.txt

# Server mode (for LangChain):
sudo systemctl start firebird  # Automatic with start script
./start_enhanced_qa_direct.sh

# Development mode:
streamlit run enhanced_qa_ui.py

# Access: UI at :8501, Phoenix at :6006, Firebird at :3050
```

---

## System Architecture & Components

### Core Components
1. **`firebird_sql_agent_direct.py`** - Main SQL agent with 5 retrieval modes
2. **`fdb_direct_interface.py`** - Direct Firebird interface (bypasses SQLAlchemy issues)
3. **`enhanced_retrievers.py`** - Multi-stage RAG with FAISS vectorization
4. **`langchain_sql_retriever_fixed.py`** - LangChain SQL Database Agent integration
5. **`global_context.py`** - Hybrid context strategy implementation
6. **`phoenix_monitoring.py`** - OTEL-based performance monitoring
7. **`db_knowledge_compiler.py`** - Database schema compilation system

### Database Configuration
- **File:** `WINCASA2022.FDB` (151 user tables)
- **Server Mode:** Port 3050 with SYSDBA authentication
- **Connection Auto-conversion:** Embedded ↔ Server format conversion
- **Knowledge Base:** 248 YAML files, compiled JSON context

### Retrieval Modes Comparison

| Mode | Performance | Context Quality | Use Case |
|------|-------------|-----------------|----------|
| **Enhanced** | 1.3s, 9 docs | Multi-stage RAG | Complex business queries |
| **FAISS** | 0.2s, 4 docs | Vector similarity | Standard semantic search |
| **None** | 0.0s, fallback | Global context only | Simple queries, fallback |
| **LangChain** | 10.3s, full schema | Native SQL agent | Schema introspection |
| **SQLCoder** | Variable | Specialized SQL | Complex JOIN operations |

---

## Development Standards

### Code Quality Requirements
- **Type Hints:** Mandatory for all new functions dealing with LLM responses
- **Docstrings:** Google-style docstrings required for SQL generation functions
- **Formatting:** Black code formatter (line length: 88)
- **Linting:** flake8 compliance with Firebird SQL exceptions
- **Testing:** 90% minimum coverage for new retrieval mode implementations

### Security Guidelines
- **Database Access:** Always use parameterized queries for FDB operations
- **API Keys:** Environment variables only (`/home/envs/`), never in code
- **Logging:** Sanitize SQL connection strings and remove credentials
- **Error Handling:** Never expose internal database schema to users
- **Phoenix Data:** Ensure no API keys in monitoring traces

### Documentation Standards
- **Code Comments:** Explain Firebird SQL dialect specifics and retrieval logic
- **CLAUDE.md Updates:** Required for any retrieval mode changes
- **Performance Metrics:** Document query times and context retrieval stats
- **Architecture Docs:** Update for significant RAG or LLM integration changes

---

## Testing Framework

### Test Hierarchy
1. **Unit Tests** (`tests/unit/` - planned)
   - Individual retriever component testing
   - Mock LLM responses and database connections
   - Fast execution (<1s per test)

2. **Integration Tests** (`tests/integration/`)
   - `test_enhanced_qa_ui_integration.py` - Full UI workflow
   - `test_fdb_direct_interface.py` - Database connectivity
   - `test_firebird_sql_agent.py` - Agent functionality
   - `test_langchain_fix.py` - LangChain mode validation

3. **System Tests** (`tests/system/`)
   - `optimized_retrieval_test.py` - All mode comparison
   - `automated_retrieval_test.py` - Comprehensive evaluation
   - `quick_hybrid_context_test.py` - Performance validation

### Performance Testing
```bash
# Quick performance validation (recommended)
python quick_hybrid_context_test.py --concurrent --workers 3 --timeout 45

# Comprehensive mode comparison
python optimized_retrieval_test.py --modes enhanced,faiss,none,langchain --concurrent

# Specific component testing
python test_phoenix_monitoring.py           # Monitoring integration
python test_hybrid_context_integration.py  # Context strategy
python iterative_improvement_test.py       # Context optimization
```

### Test Data Management
```bash
# Database status check
python test_fdb_direct_interface.py

# Server connectivity (LangChain mode)
netstat -ln | grep :3050
sudo systemctl status firebird

# Knowledge base validation
ls -la output/compiled_knowledge_base.json
ls -la output/yamls/ | wc -l  # Should show 248 files
```

---

## Debugging and Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check Firebird server status
sudo systemctl status firebird
netstat -ln | grep :3050

# Test direct connection
python test_fdb_direct_interface.py

# Validate connection string conversion
python test_firebird_connection_formats.py

# Fix SQLCODE -902 (database lock)
# Wait for running tests to complete or restart Firebird service
```

#### LLM Integration Issues
```bash
# Test API connectivity
python test_openrouter_auth.py
python test_direct_openai.py

# Validate headers configuration (LangChain)
python test_headers_issue.py

# Check MCP Context7 integration
python test_langchain_context7_fix.py
```

#### Retrieval Performance Issues
```bash
# Profile retrieval modes
python optimized_retrieval_test.py --modes enhanced,faiss --timeout 30

# Check Phoenix monitoring
# Access: http://localhost:6006

# Analyze context quality
python test_hybrid_context_integration.py

# Validate knowledge compilation
python db_knowledge_compiler.py --validate
```

### Log Analysis
- **Query Logs:** Located in `/logs/` directory with timestamped files
- **Performance Metrics:** Phoenix dashboard provides detailed trace analysis
- **Error Tracking:** Systematic error categorization in test output files
- **Retrieval Analysis:** Context document relevance scoring in test logs

---

## Integration Guidelines

### Adding New Retrieval Modes
1. **Create Retriever Class:** Inherit from base retriever in `enhanced_retrievers.py`
2. **Register Mode:** Add to mode selection in `firebird_sql_agent_direct.py:200-250`
3. **Add Tests:** Create integration test for new mode functionality
4. **Update Documentation:** Add mode description to CLAUDE.md and README.md
5. **Performance Validation:** Benchmark against existing modes using test framework

### Extending LLM Support
1. **LLM Interface:** Implement in `llm_interface.py` with proper error handling
2. **Agent Integration:** Update SQL agent configuration in main agent class
3. **Cost Tracking:** Phoenix monitoring integration for new LLM provider
4. **Fallback Logic:** Handle API failures gracefully with fallback models
5. **Context7 Integration:** Use MCP tools for real-time documentation access

### Database Schema Changes
1. **Knowledge Update:** Regenerate YAML documentation using `generate_yaml_ui.py`
2. **Context Refresh:** Update global context patterns in `global_context.py`
3. **Test Validation:** Verify all retrieval modes with new schema
4. **Cache Invalidation:** Clear compiled knowledge base and regenerate
5. **Performance Impact:** Benchmark query performance after schema changes

---

## Monitoring & Observability

### Phoenix Integration (Arize-AI) - OTEL Backend
```bash
# Installation
pip install arize-phoenix arize-phoenix-otel
pip install openinference-instrumentation-langchain openinference-instrumentation-openai

# Usage
from phoenix.otel import register
tracer_provider = register(project_name="WINCASA", auto_instrument=True)

# Dashboard access
http://localhost:6006  # Real-time performance monitoring
```

### Performance Metrics Collected
- **LLM Calls:** Model, prompts, tokens, costs, response time
- **Retrievals:** Mode, documents retrieved, relevance scores, duration
- **SQL Execution:** Query text, execution time, rows returned, errors
- **End-to-End:** Total query time, success/failure, complete trace

### Production Monitoring
```bash
# Start monitoring
python phoenix_monitoring.py --enable-ui

# System metrics
python production_monitoring.py --profile

# Performance analysis
python performance_analysis.py --generate-report
```

---

## 📚 **References**
- **Technical Guide:** `README.md` (user documentation)
- **Implementation Plan:** `plan.md` (development phases)
- **Task Details:** `task.md` (feature breakdown)
- **System Status:** `implementation_status.md` (completion tracking)
- **Performance Data:** `test_analysis_summary.md` (benchmarks)

---

## 🎯 **Current Production Status**

### ✅ **Fully Operational (2025-06-04)**
- **All 5 Retrieval Modes:** Enhanced, FAISS, None, SQLCoder, LangChain
- **MCP Context7 Integration:** Real-time LangChain documentation access
- **Phoenix OTEL Monitoring:** SQLite backend optimization (400% faster)
- **Firebird Server Setup:** Complete authentication and permission configuration
- **Hybrid Context Strategy:** Global context + dynamic retrieval implementation

### 🚀 **Ready for Production**
```bash
# Production startup
sudo systemctl start firebird
./start_enhanced_qa_direct.sh

# Monitoring access
http://localhost:6006  # Phoenix dashboard
http://localhost:8501  # Development UI
http://localhost:8502  # Production UI
```

**📈 Performance:** Enhanced mode (1.3s), FAISS mode (0.2s), LangChain agent (10.3s with full schema introspection)