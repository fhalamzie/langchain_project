# CLAUDE.md - AI Instructions

Essential instructions for Claude AI working with the WINCASA property management system.

---

## ⚠️ CRITICAL FIRST STEPS

### 🔥 Database Fix (MUST RUN FIRST)

**ALWAYS run after system restart:**
```bash
python fix_database_permissions.py
```

**Why**: Firebird resets database ownership on restart, breaking all SQL execution.

### 🧪 System Verification

**Test system works (run in background and check logs):**
```bash
nohup python test_all_6_modes_11_questions.py > test_output.log 2>&1 &
tail -f test_output.log
```

**Expected**: All 6 modes working with successful SQL execution

---

## 📚 Essential Reading Order

1. **This file** - AI instructions and patterns
2. **`readme.md`** - System architecture and technical details  
3. **`tasks.md`** - Current task backlog

---

## 🚫 Never Modify These Files

**Core System Files:**
- `test_all_6_modes_11_questions.py` - Comprehensive testing
- `fix_database_permissions.py` - Critical database fix
- `gemini_llm.py` - LLM configuration
- `real_schema_extractor.py` - Schema discovery
- `phoenix_config.py` - Monitoring setup

**All Retriever Files:**
- `contextual_enhanced_retriever.py`
- `hybrid_faiss_retriever.py` 
- `guided_agent_retriever.py`
- `contextual_vector_retriever.py`
- `adaptive_tag_classifier.py`
- `standard_db_interface.py`

---

## 🔧 Implementation Patterns

### Environment Setup
```bash
# Required environment file: /home/envs/openai.env
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

### Database Connection Pattern
```python
# Always use embedded mode (preferred)
db_connection = "firebird+fdb:///home/projects/langchain_project/WINCASA2022.FDB"
```

### LLM Configuration Pattern
```python
from gemini_llm import get_gemini_llm

# Always use this - never configure LLM manually
llm = get_gemini_llm()
```

### Retriever Initialization Patterns

**Document-based retrievers:**
```python
retriever = RetrieverClass(
    documents=documents,
    openai_api_key=openai_api_key,
    db_connection_string=db_connection,
    llm=llm
)
```

**Database-based retrievers:**
```python  
retriever = RetrieverClass(
    db_connection_string=db_connection,
    llm=llm,
    enable_monitoring=False
)
```

**Classifier-based retrievers:**
```python
classifier = ClassifierClass()  # No parameters
```

---

## 🧪 Testing Workflow

### For New AI Sessions
1. **Fix database**: `python fix_database_permissions.py`
2. **Run test in background**: `nohup python test_all_6_modes_11_questions.py > test_output.log 2>&1 &`
3. **Monitor results**: `tail -f test_output.log`
4. **Read docs**: Check `readme.md` for system details
5. **Check tasks**: Review `tasks.md` for current priorities

### Before Making Changes
1. Run comprehensive test in background to ensure system works
2. Make incremental changes only
3. Test after each change

### Test Scripts
- **`test_all_6_modes_11_questions.py`** - Comprehensive testing (5-10 min)
- **`phoenix_enabled_benchmark.py`** - Phoenix monitoring demo

### Running Tests in Background
```bash
# Start test in background
nohup python test_all_6_modes_11_questions.py > test_output.log 2>&1 &

# Check the process ID
ps aux | grep test_all_6_modes

# Monitor output
tail -f test_output.log

# Check final results
grep "FINAL RESULTS" test_output.log -A 20
```

---

## 📊 Phoenix Monitoring

**Dashboard**: http://localhost:6006

**Setup Phoenix in scripts:**
```python
from phoenix_config import setup_phoenix_monitoring, create_span

phoenix_config = setup_phoenix_monitoring(
    project_name="WINCASA-YourComponent",
    port=6006,
    enable_ui=True
)

with create_span("operation", {"key": "value"}) as span:
    result = your_function()
    span.set_attributes({"success": True})
```

**Environment control:**
```bash
export PHOENIX_ENABLED=true
export PHOENIX_PORT=6006
```

---

## 🛠️ Development Guidelines

### Safe Change Process
1. **Read existing patterns** before modifying
2. **Test before changes** - verify system works
3. **Make small changes** - incremental modifications
4. **Test after changes** - ensure no breakage
5. **Use Phoenix monitoring** - check performance impact

### Coding Standards
- **Follow existing patterns** - mimic current implementations
- **Include error handling** - always use try/catch blocks
- **Use logging** - Python logging, not print statements
- **Environment variables** - for configuration settings
- **No hardcoded values** - especially database connections

### Library Usage
**Never assume libraries are available** - always check first:
- Look at existing imports in similar files
- Check requirements.txt or package.json
- Verify library is already used in codebase

---

## 🔥 Emergency Recovery

**If system breaks:**
```bash
# 1. Fix database permissions (fixes 90% of issues)
python fix_database_permissions.py

# 2. Verify system works (in background)
nohup python test_all_6_modes_11_questions.py > test_output.log 2>&1 &
tail -f test_output.log

# 3. Check Phoenix dashboard for errors
# http://localhost:6006
```

### Common Issues

**Database problems:**
```bash
python fix_database_permissions.py
python debug_table_names.py
```

**Environment issues:**
```bash
source /home/envs/openai.env
echo $OPENAI_API_KEY | cut -c1-10
```

**Retriever issues:**
```bash
python test_pattern_integration.py
python debug_sqldb_creation.py
```

---

## 🏗️ Key System Knowledge

### Schema Discovery (Critical)
- **No hardcoded mappings** - LLM discovers schema dynamically
- **Real-time learning** - system learns from successful/failed queries
- **Dynamic SQL generation** - queries adapt to database structure

### WINCASA Domain
- **German property management** (Hausverwaltung)
- **6 operational retrieval modes**
- **Real database** with 517 apartments, 699 residents
- **Complex join patterns** (ONR+ENR, ONR+KNR+ENR)

### Critical Dependencies
1. **Database fix** - Required after every restart
2. **API keys** - OpenAI and OpenRouter in environment file
3. **Virtual environment** - Must be activated
4. **Phoenix monitoring** - For performance tracking

---

## 📁 File Organization

### Directory Structure
- **Source code** - Root directory
- **Results** - `output/results/` (JSON), `output/analysis/` (markdown)
- **Tests** - Main tests in root, specialized in `/temp/`
- **Archive** - Historical files in `/archive/`

### Daily Cleanup
```bash
# Move result files to organized structure
mv *_results*.json output/results/ 2>/dev/null
mv *_insights*.json output/analysis/ 2>/dev/null
mv *_answers*.md output/analysis/ 2>/dev/null
```

---

## 🎯 Success Patterns

### Always Remember
1. **Database fix first** - After every system restart
2. **Test before changes** - Verify system works
3. **Use Phoenix** - Monitor performance and errors
4. **Follow patterns** - Use existing code patterns
5. **Dynamic schema** - Never hardcode database mappings

### Never Do
1. **Skip database fix** - System will fail
2. **Modify without testing** - Always test first
3. **Hardcode schema** - Use dynamic discovery
4. **Assume libraries** - Check existing usage first
5. **Leave results scattered** - Organize files properly

---

## 🔒 Security Guidelines

- **API keys** in `/home/envs/openai.env` only
- **No secrets** in git repository
- **Environment variables** for configuration
- **Parameterized SQL** queries only
- **Error handling** without exposing internals

---

## 📚 Quick Reference

### Essential Commands
```bash
# Critical first step
python fix_database_permissions.py

# Comprehensive testing (always run in background)
nohup python test_all_6_modes_11_questions.py > test_output.log 2>&1 &

# Monitor test progress
tail -f test_output.log

# Check test results
grep "FINAL RESULTS" test_output.log -A 20
```

### Key Locations
- **Tests**: Root directory
- **Results**: `output/results/` and `output/analysis/`
- **Config**: `/home/envs/openai.env`
- **Database**: `WINCASA2022.FDB` in root
- **Monitoring**: http://localhost:6006

---

**Remember**: This system has **dynamic schema discovery** - let it learn the database structure. Never hardcode column mappings or table relationships. Always run the database fix after system restarts.

**Last Updated**: January 9, 2025