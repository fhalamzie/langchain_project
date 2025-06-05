# WINCASA Development Plan

## Current System Status (June 2025)

### ✅ Completed Components
- **Core System**: All 5 retrieval modes implemented and working
- **Testing Framework**: Modern pytest setup (13/13 tests passing, 0.02s execution)
- **Database Integration**: Direct FDB interface with connection pooling
- **Business Logic**: Enhanced Business Glossar with JOIN-reasoning (Task 1.1)
- **Schema Analysis**: FK-Graph Analyzer with NetworkX (Task 1.2)
- **Monitoring**: Phoenix OTEL integration with SQLite backend
- **Code Quality**: Black, isort, flake8, bandit configured (649 improvements identified)

### 🚨 Critical Issue Identified
**Problem**: 80%+ wrong SQL generation across all modes despite working infrastructure
**Root Cause**: LLM ignoring system prompts, overwhelmed by 498 YAML context documents
**Target**: Improve SQL accuracy from ~20% to >90%

## High-Level Strategy: TAG Model Implementation

### Three-Step Approach (TAG)
1. **SYN (Synthesis)**: Query classification → Targeted schema context → Focused SQL generation
2. **EXEC (Execution)**: Existing FDB interface (already working well)
3. **GEN (Generation)**: Natural language response formatting with business context

### Key Innovation: Strategic Information Architecture
**Problem**: 498 YAML documents overwhelm LLM context, causing 80%+ wrong SQL generation

**Solution**: Clear separation of information layers:
- **System Prompt**: Essential rules, syntax, core patterns (always present)
- **Focused Embeddings**: Table-specific details retrieved only when needed
- **Hybrid Retrieval**: LLM decides which tables → retrieve only relevant YAMLs

### Information Architecture Strategy

#### Layer 1: System Prompt (Always Present)
- **Core SQL Rules**: Firebird syntax (FIRST not LIMIT), LIKE patterns for addresses
- **Essential Tables**: BEWOHNER, EIGENTUEMER, WOHNUNG, OBJEKTE, KONTEN (names only)
- **Key Relationships**: ONR as central linking field, basic JOIN patterns
- **Query Types**: Address lookup, owner queries, property counts, financial calculations
- **Critical Patterns**: BSTR contains "Street Number", BPLZORT contains "PLZ City"

#### Layer 2: Targeted Embeddings (Retrieved on Demand)
- **Detailed Column Info**: Full column descriptions, constraints, examples
- **Business Context**: Internal conventions, business examples, common queries
- **Complex Relationships**: Foreign key details, table clustering information
- **Edge Cases**: Special handling, data quality notes, processing hints

#### Layer 3: Dynamic Context Assembly
1. TAG SYN identifies needed tables based on query type

## Unified Embedding Architecture (Future Implementation)

### Current Problem: Fragmented Embedding Systems
- **Enhanced Mode**: Multi-stage FAISS with categories (`enhanced_retrievers.py`)
- **FAISS Mode**: Basic FAISS implementation (`retrievers.py`)
- **None Mode**: No embeddings
- **LangChain Mode**: Uses own retrieval system
- **TAG Mode**: New strategic focused approach

### Solution: Consolidated Embedding Hub
**Central System**: `focused_embeddings.py` becomes single embedding source for all modes

#### Benefits:
- **Performance**: Single embedding model, shared vector stores, reduced memory
- **Consistency**: All modes use same strategic information architecture
- **Maintenance**: One place to update embedding logic, shared improvements
- **Quality**: Unified context delivery across all retrieval modes

#### Unified Architecture:
```python
# Central embedding system used by all modes
focused_embeddings = FocusedEmbeddingSystem(openai_api_key)

# Mode-specific retrieval strategies
retrieval_strategies = {
    "enhanced": focused_embeddings.get_multi_stage_context,
    "faiss": focused_embeddings.get_similarity_context, 
    "none": focused_embeddings.get_minimal_context,
    "langchain": focused_embeddings.get_schema_context,
    "tag": focused_embeddings.get_focused_context
}
```

#### Implementation Strategy:
1. **Extend `focused_embeddings.py`** with mode-specific retrieval methods
2. **Refactor existing modes** to use unified embedding system
3. **Maintain backward compatibility** while improving performance
4. **Share vector stores** across all modes for efficiency
2. Retrieve only relevant YAML details for those specific tables
3. Combine focused system prompt + targeted table details
4. Deliver precise context without overwhelming noise

## Development Phases

### Phase 0: Foundation (Week 1) 🚨 IMMEDIATE
**Goal**: Fix critical dependencies and diagnose prompt issues

#### Objectives:
- Install missing dependencies (langgraph, sqlglot, langchain-experimental)
- Test all 5 retrieval modes for basic functionality
- Isolate why LLM ignores system prompts with minimal test cases
- Identify context interference from excessive YAML documents

### Phase 1: TAG Core Implementation (Week 2-3)
**Goal**: Implement TAG architecture with query-type-specific context

#### Major Components:
1. **QuerySynthesizer** (`tag_synthesizer.py`)
   - Query type classification (address, owner, financial, property queries)
   - Targeted schema context delivery per query type
   - Business entity to table mapping

2. **SQLValidator** (`sql_validator.py`) 
   - Firebird dialect validation with sqlglot
   - Automatic syntax fixing (LIMIT → FIRST, etc.)
   - Validation feedback loop for iterative improvement

3. **ResponseGenerator** (`tag_generator.py`)
   - Query-type-specific response formatting
   - German language support with business terminology
   - Context-aware error messages

### Phase 2: Integration & Optimization (Week 4)
**Goal**: Integrate TAG as 6th retrieval mode and validate performance

#### Deliverables:
- **TAGPipeline** orchestrator with SYN→EXEC→GEN flow
- **LangGraph workflow** with state machine for complex queries
- **Comprehensive testing** across all 6 modes with 11 standard test queries
- **Performance benchmarks** and accuracy validation

## Success Metrics

### Primary Goals:
- **SQL Generation Accuracy**: 20% → 90%
- **Table Selection**: >95% correct identification
- **Address Queries**: 100% proper LIKE pattern usage instead of exact match
- **Business Logic**: >90% correct term-to-table mapping
- **Response Time**: <10s for complex queries, <5s for simple queries

### Testing Strategy:
- **11 Standard Queries**: From simple lookups to complex aggregations
- **Continuous Validation**: After each implementation phase
- **Regression Prevention**: Ensure existing modes continue working
- **Real-world Testing**: WINCASA-specific business scenarios

## Risk Mitigation

### Incremental Approach:
- Each phase produces working, testable results
- Existing retrieval modes remain fully functional
- TAG mode as additional option, not replacement
- Comprehensive logging and debugging support

### Fallback Strategy:
- TAG mode falls back to Enhanced mode on failure
- Multi-level error recovery with context enhancement
- Performance monitoring for all modes

## Long-term Vision

### Post-TAG Enhancements:
- **Performance Optimization**: Caching, parallel processing
- **Extended Query Support**: Complex business scenarios
- **Production Monitoring**: Advanced observability
- **User Experience**: Enhanced UI with query suggestions

### Maintenance Strategy:
- Regular accuracy validation against business requirements
- Continuous improvement based on user feedback
- Documentation updates reflecting system evolution
- Code quality maintenance with automated tools

---

**Next Steps**: See `task.md` for detailed implementation tasks
**Development Guidelines**: See `CLAUDE.md` for coding standards and testing procedures