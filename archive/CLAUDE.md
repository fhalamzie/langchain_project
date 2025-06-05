# WINCASA Development Guidelines

## Project Context
Intelligent natural language database query system for Firebird databases using LLM agents. Processes SQL queries from German/English natural language input with multi-modal RAG retrieval and real-time monitoring.

## Core Tech Stack
- **Backend:** Python, Firebird FDB, LangChain, SQLAlchemy, Phoenix Monitoring
- **LLM Integration:** OpenAI GPT-4, OpenRouter APIs
- **RAG System:** FAISS vectorization, Multi-stage retrieval, Hybrid context strategy
- **Infrastructure:** Streamlit UI, Direct FDB interface, SQLite monitoring backend

---

## Development Guidelines

### 🔧 **Testing Requirements**
**CRITICAL:** Every new feature MUST include tests BEFORE marking as complete:
- **Unit Tests** for all new functions and modules
- **Integration Tests** for database connections and LLM integrations  
- **System Tests** for complete query workflows
- **Execute test suites after every implementation**
- **Tests must pass BEFORE git commit/push**

**Quick Testing Commands:**
```bash
# Modern pytest framework
./run_tests.sh test                    # Run all unit tests
./run_tests.sh all                     # Run all checks and tests
./run_tests.sh format-fix              # Auto-format code (Black + isort)

# Key integration tests
python test_enhanced_qa_ui_integration.py     # Core integration test
python test_fdb_direct_interface.py          # Database interface test
python optimized_retrieval_test.py           # All retrieval modes
```

### 📝 **Documentation Policy**
**IMPORTANT:** Keep documentation focused and current:
- **CLAUDE.md & README.md:** Update only for major architectural changes
- **plan.md:** High-level strategy and development phases  
- **task.md:** Detailed implementation tasks and progress tracking
- **All routine updates** go in plan.md or task.md, not CLAUDE.md/README.md

### 🏗️ **Code Standards**
- **Max 800 lines per .py file** (prefer 500 lines for complex SQL logic)
- **Modular architecture** with clear separation between retrieval modes
- **Every module starts** with descriptive docstring explaining purpose
- **Use existing patterns** from `firebird_sql_agent_direct.py` and `enhanced_retrievers.py`
- **Follow existing code conventions** especially for Firebird SQL generation

### 📍 **File References**
Always reference specific code locations as `file_path:line_number` for easy navigation.

### 🚨 **Critical System Files**
- **SQL Agent Core:** `firebird_sql_agent_direct.py:1-800`
- **Retrieval System:** `enhanced_retrievers.py:1-600`
- **Database Interface:** `fdb_direct_interface.py:1-400`
- **LangChain Integration:** `langchain_sql_retriever_fixed.py:1-300`
- **Global Context:** `global_context.py:1-200`
- **Business Glossar:** `business_glossar.py:1-600`

### ⚙️ **Environment & Configuration**
- **Primary config:** Environment variables in `/home/envs/`
- **API Keys location:** `/home/envs/openai.env`, `/home/envs/openrouter.env`
- **Database:** `WINCASA2022.FDB` (151 tables, 517 apartments, 698 residents)
- **Firebird Server:** Port 3050 for LangChain mode
- **Phoenix Monitoring:** SQLite backend at `localhost:6006`

### 🔍 **Development Workflow**
1. **Consult MCP Context7** for documentation on relevant technologies/frameworks before making changes
2. **Read existing code** to understand retrieval mode patterns
3. **Write tests first** for new SQL agent functionality
4. **Implement feature** following existing Firebird conventions
5. **Run test suite** and ensure all retrieval modes pass
6. **Update task.md** with progress and implementation details
7. **Commit with clear message** referencing specific components
8. **Push to GitHub** regularly to maintain backup

### 📚 **MCP Context7 Usage**
**IMPORTANT:** Use MCP Context7 tools for consulting documentation BEFORE implementing:
- **Purpose**: Documentation lookup and best practices research only
- **When**: Before making code changes to understand frameworks/libraries
- **Not for**: Actual implementation - use for learning and reference
- **Examples**: LangChain patterns, SQLAlchemy usage, pytest best practices

### 🧪 **Git & Commits**
- **Regular commits** with meaningful commit messages following conventional format
- **Reference file locations** using pattern `file_path:line_number`
- **Test locally first, then commit** - no exceptions
- **Each retrieval mode change** requires dedicated commit
- **Update task.md** for progress tracking (NOT CLAUDE.md unless major architectural change)

---

## System Architecture

### Current Implementation Status (June 2025)
- ✅ **All 5 Retrieval Modes:** Enhanced, FAISS, None, SQLCoder, LangChain operational
- ✅ **Firebird Integration:** Direct FDB interface + server mode for LangChain
- ✅ **Phoenix Monitoring:** OTEL tracing with SQLite backend optimization
- ✅ **Testing Framework:** Modern pytest setup (13/13 tests passing, 0.02s execution)
- 🚨 **Current Issue:** 80%+ wrong SQL generation requiring TAG model implementation

### Active Interfaces
- **Development UI:** `http://localhost:8501` (Streamlit with all features)
- **Phoenix Dashboard:** `http://localhost:6006` (Performance monitoring)
- **Command Line:** `python run_llm_query.py` (Direct queries)

### Core Components
1. **`firebird_sql_agent_direct.py`** - Main SQL agent with 5 retrieval modes
2. **`fdb_direct_interface.py`** - Direct Firebird interface (bypasses SQLAlchemy issues)
3. **`enhanced_retrievers.py`** - Multi-stage RAG with FAISS vectorization
4. **`langchain_sql_retriever_fixed.py`** - LangChain SQL Database Agent integration
5. **`global_context.py`** - Hybrid context strategy implementation
6. **`phoenix_monitoring.py`** - OTEL-based performance monitoring

### Database Configuration
- **File:** `WINCASA2022.FDB` (151 user tables)
- **Server Mode:** Port 3050 with SYSDBA authentication
- **Knowledge Base:** 248 YAML files, compiled JSON context

---

## Development Standards

### Code Quality Requirements
- **Type Hints:** Mandatory for all new functions dealing with LLM responses
- **Docstrings:** Google-style docstrings required for SQL generation functions
- **Formatting:** Black code formatter (line length: 88)
- **Linting:** flake8 compliance with Firebird SQL exceptions
- **Testing:** 75% minimum coverage for new modules

### Security Guidelines
- **Database Access:** Always use parameterized queries for FDB operations
- **API Keys:** Environment variables only (`/home/envs/`), never in code
- **Logging:** Sanitize SQL connection strings and remove credentials
- **Error Handling:** Never expose internal database schema to users

---

## Quick Reference

### Environment Setup
```bash
# Quick start
git clone https://github.com/fhalamzie/langchain_project.git
cd langchain_project
pip install -r requirements.txt

# Start system
./start_enhanced_qa_direct.sh
```

### Development Commands
```bash
# Testing
./run_tests.sh test              # All unit tests
python diagnostic_test.py       # System validation

# Code Quality  
./run_tests.sh format-fix        # Auto-format
./run_tests.sh lint             # Check code quality

# Monitoring
# Phoenix dashboard: http://localhost:6006
```

---

**For detailed implementation tasks and progress:** See `task.md`  
**For high-level strategy and planning:** See `plan.md`