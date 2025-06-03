# CLAUDE.md

This file provides technical guidance for working with the WINCASA database query system.

## System Overview

WINCASA is a natural language database query system for Firebird databases. The system uses LLM agents to generate SQL queries based on natural language input.

## Core Components

1. **`firebird_sql_agent_direct.py`** - Main SQL agent with direct FDB integration
2. **`fdb_direct_interface.py`** - Direct Firebird interface (bypasses SQLAlchemy SQLCODE -902 issues)
3. **`enhanced_qa_ui.py`** - Streamlit UI for development/testing
4. **`streamlit_qa_app.py`** - Clean production UI
5. **`enhanced_retrievers.py`** - Multi-Stage RAG system with FAISS vectorization
6. **`db_knowledge_compiler.py`** - Database knowledge compilation system

## Available Interfaces

### Web Interfaces
```bash
# Clean production UI
./start_clean_qa.sh
# Access: http://localhost:8502

# Development UI (all features)
streamlit run enhanced_qa_ui.py
# Access: http://localhost:8501

# Legacy production UI
./start_enhanced_qa_direct.sh
```

### Command Line
```bash
# Direct CLI queries
python run_llm_query.py
```

## Testing Framework

### Basic System Tests
```bash
# Core integration test
python test_enhanced_qa_ui_integration.py

# Database interface test
python test_fdb_direct_interface.py

# Agent functionality test
python test_firebird_sql_agent.py
```

### Retrieval Mode Evaluation
```bash
# Optimized test framework (recommended)
python optimized_retrieval_test.py

# Concurrent testing (2 workers)
python optimized_retrieval_test.py --concurrent --workers 2

# Original test framework
python automated_retrieval_test.py
```

## System Configuration

### Database
- **File**: `WINCASA2022.FDB` 
- **Tables**: 151 user tables
- **Data**: 517 apartments, 698 residents

### API Configuration
- **OpenAI**: `/home/envs/openai.env`
- **OpenRouter**: `/home/envs/openrouter.env` (fallback)

### Knowledge Base
- **Compiled**: `/output/compiled_knowledge_base.json`
- **Documentation**: `/output/yamls/` (248 YAML files)

## Retrieval Modes

The system supports three retrieval modes for context augmentation:

### 1. Enhanced Mode (`enhanced`)
- Multi-stage RAG with business context
- Uses compiled knowledge base and YAML documentation
- 3-level retrieval: schema, relationships, business patterns

### 2. FAISS Mode (`faiss`)
- Vector similarity search using FAISS
- Basic document retrieval with embeddings
- Standard vectorization approach

### 3. None Mode (`none`)
- Direct SQL generation without retrieval augmentation
- Baseline mode using only LLM knowledge
- No additional context from documentation

## Current Performance Data

Based on comprehensive testing (11 queries × 3 modes = 33 tests):

### Success Rates
- Enhanced Mode: 63.6% (7/11 queries successful)
- FAISS Mode: 63.6% (7/11 queries successful)  
- None Mode: 63.6% (7/11 queries successful)

### Average Execution Times
- Enhanced Mode: 22.5 seconds
- FAISS Mode: 34.6 seconds
- None Mode: 20.8 seconds

### Timeout Behavior
- Enhanced Mode: 3 timeouts
- FAISS Mode: 5 timeouts
- None Mode: 0 timeouts

## Known Issues

### System-Level Errors
- **SOLLSTELLUNG Error**: 2 queries fail across all modes with "Target SOLLSTELLUNG is not in G"
- **Database Schema Issue**: Not retrieval-mode specific

### Mode-Specific Issues
- **FAISS Mode**: Prone to timeouts on complex queries
- **Enhanced Mode**: Occasional incorrect table selection
- **None Mode**: Limited business context understanding

### Accuracy Limitations
- Current success rate of 63.6% indicates significant room for improvement
- Query results often do not match expected real-world data
- Table selection and SQL generation require optimization

## Development Notes

### Database Lock Issues
When running tests, the database may be locked by other processes. Symptoms:
```
SQLCODE: -902 - Database already opened with engine instance
```

Solution: Wait for running tests to complete or restart processes.

### Testing Optimization
The optimized test framework provides:
- Agent reuse (13.6s initialization vs 45s+ repeated)
- Real-time progress logging
- Concurrent execution support

### Log Monitoring
```bash
# Monitor test progress
tail -f optimized_retrieval_test_*.log

# Check latest results
ls -la optimized_retrieval_test_*.json
```

## Next Steps for Development

### Immediate Improvements Needed
1. Address SOLLSTELLUNG system error
2. Improve query accuracy from current 63.6%
3. Optimize table selection logic
4. Reduce timeout frequency in FAISS/Enhanced modes

### Testing Recommendations
1. Use `optimized_retrieval_test.py` for performance testing
2. Monitor logs for timeout patterns
3. Analyze query comparison reports for accuracy issues
4. Test with real user queries beyond current test set

### Architecture Considerations
1. Consider hybrid mode selection based on query type
2. Implement timeout management and retry logic
3. Improve business context integration
4. Enhance error handling and user feedback

## Monitoring & Observability Integration

### Phoenix Integration (Arize-AI)
Integration of Phoenix for comprehensive AI observability:

#### Installation
```bash
pip install arize-phoenix
```

#### Integration Points
- **LLM Tracing**: Track all OpenAI API calls and response quality
- **Retrieval Evaluation**: Monitor RAG performance across Enhanced/FAISS/None modes
- **Performance Monitoring**: Track query execution times and success rates
- **Prompt Management**: Systematically test and version prompt variations

#### Implementation Plan
1. **Core Integration**: Add Phoenix tracing to `firebird_sql_agent_direct.py`
2. **Retrieval Monitoring**: Instrument `enhanced_retrievers.py` for RAG evaluation
3. **UI Integration**: Add Phoenix dashboard links to `enhanced_qa_ui.py`
4. **Testing Integration**: Enhance automated tests with Phoenix metrics

#### Configuration
```python
import phoenix as px
px.launch_app()  # Launch Phoenix UI at http://localhost:6006
```

## Development Workflow Requirements

### Unit Testing Standards
- **Coverage**: 100% unit test coverage for all new features
- **Test Location**: Tests in `/tests/` directory with `test_*.py` naming
- **Framework**: Use pytest for consistent testing approach
- **Mocking**: Mock external dependencies (OpenAI API, database connections)
- **Performance Tests**: Include performance benchmarks for critical paths

### Git Workflow Requirements
- **Commit Strategy**: Each major change requires dedicated git commit
- **Commit Messages**: Descriptive messages following conventional commits format
- **Push Policy**: All commits must be pushed to remote repository
- **Documentation Updates**: Every code change requires corresponding documentation update

### Documentation Maintenance
- **CLAUDE.md**: Update technical guidance for new features
- **README.md**: Update user-facing documentation and examples
- **implementation_status.md**: Track completion status of all features
- **Code Comments**: Inline documentation for complex logic

This system is functional but requires significant optimization before production deployment.