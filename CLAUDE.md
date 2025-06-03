# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WINCASA is a database documentation generator and natural language query system that bridges Firebird databases with modern LLM technology. The system enables users to query complex databases using natural language without SQL knowledge.

## Key Architecture

The system uses a modular architecture with these critical components:

1. **Direct FDB Interface** (`fdb_direct_interface.py`) - Bypasses SQLAlchemy to avoid lock issues (SQLCODE -902)
2. **SQL Agent** (`firebird_sql_agent_direct.py`) - Converts natural language to SQL using LLM + RAG
3. **FAISS Retriever** (`retrievers.py`) - Vector-based documentation search for context
4. **Streamlit UI** (`streamlit_integration.py`, `enhanced_qa_ui.py`) - User interface

## Common Commands

### Running the Application
```bash
# Main Streamlit app
source .venv/bin/activate
streamlit run streamlit_integration.py

# Enhanced Q&A UI with direct FDB (recommended)
./start_enhanced_qa_direct.sh
# or manually:
source .venv/bin/activate
streamlit run enhanced_qa_ui.py

# Command-line query
python run_llm_query.py
```

### Testing
```bash
# Test direct FDB interface
python test_fdb_direct_interface.py

# Test enhanced UI integration  
python test_enhanced_qa_ui_integration.py

# Test Firebird SQL agent
python test_firebird_sql_agent.py

# Test retrievers
python test_retrievers.py
```

### Database Schema Export
```bash
python extract_from_firebird.py
```

## Critical Technical Context

1. **SQLAlchemy Lock Issue**: The project initially used SQLAlchemy but encountered persistent lock issues (SQLCODE -902) with Firebird Embedded. The solution was implementing a direct FDB interface that bypasses SQLAlchemy entirely. Always use `FirebirdDirectSQLAgent` instead of the original `FirebirdDocumentedSQLAgent`.

2. **Connection Management**: The direct FDB interface uses connection pooling and automatic server/embedded fallback. Never create raw FDB connections - always use `FDBDirectInterface` for database access.

3. **Token Limits**: Document content is limited to 1500 characters to prevent token overflow. This is configured in the retriever classes.

4. **Environment Setup**: 
   - OpenAI API key must be in `/home/envs/openai.env`
   - Firebird client library must be at `./lib/libfbclient.so`
   - Database file `WINCASA2022.FDB` must be in project root

## Development Workflow

When modifying the system:

1. **For SQL Agent changes**: Work with `firebird_sql_agent_direct.py` (not the original)
2. **For UI changes**: Modify `enhanced_qa_ui.py` for the Q&A interface
3. **For retrieval improvements**: Update `retrievers.py` (FAISS is primary, Neo4j is experimental)
4. **For database access**: Always use `FDBDirectInterface` from `fdb_direct_interface.py`

## Testing Approach

Always test database connections first:
```bash
python test_fdb_direct_interface.py
```

Then test the complete flow:
```bash
python test_enhanced_qa_ui_integration.py
```
Write for each new item in the implemention_plan.md a unit test and verify the implemention

## Important Files

- `implementation_status.md` - Current project status and phase completion
- `plan.md` - Detailed implementation plan for Langchain SQL Agent with RAG approaches
- `query_router.py` - Central database access component (legacy, replaced by direct FDB)
- `db_executor.py` - Secure SQL execution with validation and caching
- `query_memory.py` - Stores query history for context

## Current Implementation Status

- **Phase 1 (FAISS RAG)**: ✅ Complete
- **Phase 1.5 (Direct FDB)**: ✅ Complete - Critical solution for SQLAlchemy lock issues
- **Phase 2 (Neo4j RAG)**: ✅ Implemented but optional/lower priority
- **Phase 3 (Integration)**: ✅ Complete for FAISS
- **Phase 4 (UI Integration)**: ✅ Complete
- **Phase 5 (Extended Tests)**: ✅ Complete as of 3.6.2025

## Key Technical Solutions

1. **Direct FDB Interface**: Custom Langchain tools (`FDBQueryTool`, `FDBSchemaInfoTool`, `FDBListTablesTool`) that bypass SQLAlchemy
2. **Connection Pooling**: Efficient connection management with automatic server/embedded fallback
3. **Character Encoding**: Proper handling of WIN1252 to UTF-8 conversion for German text


## Git

Please commmit prior to any major change