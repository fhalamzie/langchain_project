# WINCASA Enhancement Tasks: 5-Step JOIN-Enhanced Architecture

## Overview

Implementation roadmap for the extended JOIN-component architecture integrating business glossar, graph-based JOIN reasoning, multi-hop retrieval, LangGraph control logic, and SQL validation.

**Target**: Improve SQL generation accuracy from current ~70% to >85% through systematic JOIN reasoning and business knowledge integration.

## Phase 1: Foundation Components (Week 1-2)

### Task 1.1: Business Glossar Implementation ✅ PRIORITY: HIGH
**Module**: `business_glossar.py`
**Estimated Time**: 2-3 days
**Dependencies**: None

#### Subtasks:
- [ ] 1.1.1 Create `business_glossar.py` module with rule-based mappings
  - [ ] Define core business terms → SQL condition mappings
  - [ ] Implement glossar lookup functions
  - [ ] Add WINCASA-specific domain knowledge
  
- [ ] 1.1.2 Extend `global_context.py` with business glossar
  - [ ] Integrate BUSINESS_GLOSSAR dictionary
  - [ ] Add term resolution functions
  - [ ] Create context injection methods
  
- [ ] 1.1.3 Implement term extraction from user queries
  - [ ] NLP-based business term detection
  - [ ] Fuzzy matching for term variations
  - [ ] Context-aware term disambiguation

**Example Implementation**:
```python
BUSINESS_GLOSSAR = {
    "Kredit": "SOLLSTELLUNG WHERE ARTBEZ LIKE '%KREDIT%' AND BETRAG > 0",
    "Mieter": "BEWOHNER WHERE BMIETV IS NOT NULL", 
    "Eigentümer": "EIGENTUEMER E JOIN VEREIG V ON E.EIGNR = V.EIGNR",
    "Leerstand": "WOHNUNG W LEFT JOIN BEWOHNER B ON W.ONR = B.ONR WHERE B.ONR IS NULL",
    "Adresse": "BSTR + ', ' + BPLZORT + CASE WHEN HNRZU IS NOT NULL THEN ' ' + HNRZU ELSE '' END"
}
```

**Testing**: `test_business_glossar.py`
**Success Criteria**: 95% accuracy in term-to-SQL mapping for 20 core business terms

---

### Task 1.2: FK-Graph Analyzer with NetworkX ✅ PRIORITY: HIGH  
**Module**: `fk_graph_analyzer.py`
**Estimated Time**: 3-4 days
**Dependencies**: Task 1.1, existing `global_context.py`

#### Subtasks:
- [ ] 1.2.1 Install and configure NetworkX
  - [ ] Add networkx to requirements.txt
  - [ ] Test NetworkX graph operations
  
- [ ] 1.2.2 Build schema graph from existing relationships
  - [ ] Parse `global_context.py` relationships into graph edges
  - [ ] Add foreign key constraints from database schema
  - [ ] Weight edges by join complexity/performance
  
- [ ] 1.2.3 Implement JOIN path finding algorithms  
  - [ ] shortest_path for direct connections
  - [ ] all_simple_paths for multiple JOIN options
  - [ ] Path ranking by complexity and reliability
  
- [ ] 1.2.4 Generate SQL JOIN sequences from paths
  - [ ] Convert graph paths to SQL JOIN syntax
  - [ ] Handle complex relationships (many-to-many)
  - [ ] Optimize JOIN order for performance

**Example Implementation**:
```python
class FKGraphAnalyzer:
    def find_join_path(self, from_table: str, to_table: str) -> List[str]:
        path = nx.shortest_path(self.graph, from_table, to_table)
        return self._generate_join_sql(path)
    
    def get_all_related_tables(self, tables: List[str], max_hops: int = 2):
        related = set(tables)
        for table in tables:
            neighbors = self._get_neighbors_within_hops(table, max_hops)
            related.update(neighbors)
        return list(related)
```

**Testing**: `test_fk_graph_analyzer.py`
**Success Criteria**: Generate correct JOIN paths for 15 common table combinations

---

### Task 1.3: SQLGlot Validation Framework ✅ PRIORITY: MEDIUM
**Module**: `sql_validator.py`  
**Estimated Time**: 2-3 days
**Dependencies**: None

#### Subtasks:
- [ ] 1.3.1 Install and configure SQLGlot
  - [ ] Add sqlglot to requirements.txt
  - [ ] Test Firebird dialect parsing
  
- [ ] 1.3.2 Implement SQL syntax validation
  - [ ] Parse SQL with Firebird dialect
  - [ ] Validate table/column existence
  - [ ] Check for common syntax errors
  
- [ ] 1.3.3 Create automatic SQL fixing capabilities
  - [ ] LIMIT → FIRST conversion for Firebird
  - [ ] Table alias standardization
  - [ ] Column name correction suggestions
  
- [ ] 1.3.4 Integrate validation into query pipeline
  - [ ] Pre-execution validation step
  - [ ] Error reporting and suggestions
  - [ ] Feedback loop for continuous improvement

**Example Implementation**:
```python
class FirebirdSQLValidator:
    def validate_and_fix(self, sql: str) -> ValidationResult:
        try:
            parsed = parse_one(sql, dialect="firebird")
            issues = self._check_common_issues(sql, parsed)
            missing_refs = self._validate_table_column_refs(parsed)
            return ValidationResult(
                valid=len(issues + missing_refs) == 0,
                issues=issues,
                fixed_sql=self._apply_fixes(sql, issues)
            )
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))
```

**Testing**: `test_sql_validator.py`
**Success Criteria**: 95% syntax validation accuracy, 80% automatic fix success rate

---

## Phase 2: Advanced Integration (Week 3-4)

### Task 2.1: Multi-Hop Retrieval Enhancement ✅ PRIORITY: HIGH
**Module**: `multi_hop_retriever.py`
**Estimated Time**: 4-5 days
**Dependencies**: Task 1.2, existing `enhanced_retrievers.py`

#### Subtasks:
- [ ] 2.1.1 Extend enhanced retrieval with JOIN-aware context
  - [ ] Inherit from existing EnhancedRetriever
  - [ ] Integrate FK graph analyzer for path discovery
  - [ ] Retrieve documentation for all tables in JOIN paths
  
- [ ] 2.1.2 Implement table context expansion
  - [ ] Given user entities, find all related tables within N hops
  - [ ] Load relevant YAML documentation for expanded table set
  - [ ] Prioritize context by relationship strength
  
- [ ] 2.1.3 Create JOIN-specific documentation retrieval
  - [ ] Extract JOIN examples from existing YAML files
  - [ ] Create specialized prompts for complex relationships
  - [ ] Add relationship-specific business context
  
- [ ] 2.1.4 Optimize context window management  
  - [ ] Prioritize most relevant tables/relationships
  - [ ] Implement smart truncation for large context sets
  - [ ] Balance global context vs. specific retrieval

**Example Implementation**:
```python
class MultiHopRetriever(EnhancedRetriever):
    def retrieve_with_join_context(self, query: str) -> RetrievalResult:
        # 1. Extract entities from query
        entities = self._extract_table_entities(query)
        
        # 2. Find all related tables via graph traversal
        related_tables = self.fk_analyzer.get_all_related_tables(entities, max_hops=2)
        
        # 3. Retrieve context for expanded table set
        base_docs = super().retrieve(query)
        join_docs = self._retrieve_for_tables(related_tables)
        
        # 4. Add JOIN path documentation
        join_paths = self._generate_join_examples(entities)
        
        return RetrievalResult(
            documents=base_docs + join_docs,
            join_paths=join_paths,
            related_tables=related_tables
        )
```

**Testing**: `test_multi_hop_retriever.py`
**Success Criteria**: Retrieve relevant context for 90% of multi-table queries

---

### Task 2.2: LangGraph Workflow Implementation ✅ PRIORITY: HIGH
**Module**: `langgraph_controller.py`
**Estimated Time**: 5-6 days  
**Dependencies**: Tasks 1.1, 1.2, 1.3, 2.1

#### Subtasks:
- [ ] 2.2.1 Install and configure LangGraph
  - [ ] Add langgraph to requirements.txt
  - [ ] Test StateGraph basic functionality
  
- [ ] 2.2.2 Design query processing state machine
  - [ ] Define QueryState with all required fields
  - [ ] Map processing steps to state transitions
  - [ ] Design error handling and retry logic
  
- [ ] 2.2.3 Implement core processing nodes
  - [ ] extract_entities: Business term extraction from query
  - [ ] apply_glossar: Business rule mapping
  - [ ] find_joins: FK graph path discovery
  - [ ] retrieve_context: Multi-hop context retrieval
  - [ ] generate_sql: Enhanced LLM prompting
  - [ ] validate_sql: SQLGlot validation
  - [ ] execute_or_fix: Query execution with feedback loop
  
- [ ] 2.2.4 Create conditional edges and feedback loops
  - [ ] Validation failure → SQL regeneration
  - [ ] Execution error → Context enhancement
  - [ ] User clarification requests → State updates
  
- [ ] 2.2.5 Integrate with existing WINCASA architecture
  - [ ] Replace/extend firebird_sql_agent_direct.py
  - [ ] Maintain compatibility with existing retrieval modes
  - [ ] Add as 6th retrieval mode: "langgraph"

**Example Implementation**:
```python
def create_query_workflow():
    workflow = StateGraph(QueryState)
    
    workflow.add_node("extract_entities", extract_business_entities)
    workflow.add_node("apply_glossar", apply_business_glossar)
    workflow.add_node("find_joins", find_join_paths)  
    workflow.add_node("retrieve_context", multi_hop_retrieve)
    workflow.add_node("generate_sql", enhanced_llm_generation)
    workflow.add_node("validate_sql", sqlglot_validation)
    workflow.add_node("execute_or_fix", execute_with_feedback)
    
    # Conditional edges for error handling
    workflow.add_conditional_edges(
        "validate_sql",
        should_regenerate,
        {"regenerate": "generate_sql", "execute": "execute_or_fix"}
    )
    
    return workflow.compile()
```

**Testing**: `test_langgraph_workflow.py`
**Success Criteria**: Complete workflow execution for 80% of test queries

---

### Task 2.3: Enhanced LLM Prompting Integration ✅ PRIORITY: MEDIUM
**Module**: Update `firebird_sql_agent_direct.py`
**Estimated Time**: 2-3 days
**Dependencies**: Tasks 1.1, 1.2, 2.1

#### Subtasks:
- [ ] 2.3.1 Integrate business glossar into prompts
  - [ ] Add glossar mappings to system prompt
  - [ ] Include resolved business terms in context
  - [ ] Create examples of term → SQL transformations
  
- [ ] 2.3.2 Add JOIN path guidance to prompts  
  - [ ] Include discovered JOIN paths in prompt
  - [ ] Add JOIN examples from similar queries
  - [ ] Provide table relationship explanations
  
- [ ] 2.3.3 Enhance prompt with expanded context
  - [ ] Include multi-hop retrieved documentation
  - [ ] Add related table information
  - [ ] Balance context size vs. relevance
  
- [ ] 2.3.4 Create adaptive prompting based on query complexity
  - [ ] Simple queries: Basic context + glossar
  - [ ] Complex queries: Full graph context + multi-hop retrieval
  - [ ] Financial queries: Specialized accounting context

**Example Implementation**:
```python
def build_enhanced_prompt(self, query: str, state: QueryState):
    return f"""
    WINCASA Database Query: "{query}"
    
    BUSINESS CONTEXT (Resolved Terms):
    {self._format_glossar_mappings(state['glossar_mappings'])}
    
    IDENTIFIED JOIN PATHS:
    {self._format_join_paths(state['join_paths'])}
    
    RELATED TABLES & CONTEXT:
    {self._format_table_context(state['retrieved_context'])}
    
    SCHEMA RELATIONSHIPS:
    {self._format_relevant_subgraph(state['extracted_entities'])}
    
    Generate Firebird SQL using:
    - FIRST n syntax (not LIMIT)
    - Proper JOIN syntax for identified paths
    - Business logic from resolved terms
    """
```

**Testing**: `test_enhanced_prompting.py`
**Success Criteria**: 15% improvement in SQL generation accuracy

---

## Phase 3: Testing & Optimization (Week 5)

### Task 3.1: Comprehensive Testing Framework ✅ PRIORITY: HIGH
**Module**: `test_langgraph_integration.py`
**Estimated Time**: 3-4 days
**Dependencies**: All previous tasks

#### Subtasks:
- [ ] 3.1.1 Create comprehensive test suite
  - [ ] Test all 6 retrieval modes (including new langgraph)
  - [ ] Compare performance across modes
  - [ ] Measure accuracy improvements
  
- [ ] 3.1.2 Implement query complexity categorization
  - [ ] Simple: Single table queries
  - [ ] Medium: 2-3 table JOINs
  - [ ] Complex: Multi-hop relationships, business logic
  - [ ] Expert: Financial calculations, aggregations
  
- [ ] 3.1.3 Create success metrics and benchmarks
  - [ ] SQL syntax correctness (0-100%)
  - [ ] Business logic accuracy (0-100%)  
  - [ ] Execution success rate (0-100%)
  - [ ] Response time performance (seconds)
  - [ ] User satisfaction scores (1-10)
  
- [ ] 3.1.4 Automated regression testing
  - [ ] Golden dataset of query-SQL pairs
  - [ ] Automated accuracy measurement
  - [ ] Performance regression detection

**Testing Commands**:
```bash
# Test all 6 modes with comprehensive metrics
python test_langgraph_integration.py --modes all --metrics comprehensive

# Performance comparison
python optimized_retrieval_test.py --modes enhanced,faiss,none,sqlcoder,langchain,langgraph

# Accuracy validation  
python accuracy_validation_test.py --dataset golden_queries.json
```

**Success Criteria**: 
- LangGraph mode: >85% accuracy (vs current ~70%)
- <20s average response time
- >90% execution success rate

---

### Task 3.2: Performance Optimization ✅ PRIORITY: MEDIUM
**Module**: Various performance-critical modules
**Estimated Time**: 2-3 days
**Dependencies**: Task 3.1

#### Subtasks:
- [ ] 3.2.1 Optimize FK graph operations
  - [ ] Cache graph construction
  - [ ] Optimize shortest path algorithms
  - [ ] Precompute common JOIN paths
  
- [ ] 3.2.2 Optimize multi-hop retrieval
  - [ ] Implement smart context truncation
  - [ ] Cache retrieved documentation
  - [ ] Parallel document processing
  
- [ ] 3.2.3 Optimize LangGraph workflow
  - [ ] Minimize state transitions
  - [ ] Cache validation results  
  - [ ] Optimize LLM API calls
  
- [ ] 3.2.4 Memory and resource optimization
  - [ ] Profile memory usage across modes
  - [ ] Optimize embedding storage
  - [ ] Clean up unused resources

**Performance Targets**:
- Graph operations: <100ms
- Multi-hop retrieval: <2s
- LangGraph workflow: <15s total
- Memory usage: <2GB peak

---

### Task 3.3: Documentation & Integration ✅ PRIORITY: MEDIUM
**Module**: Documentation files and integration guides
**Estimated Time**: 2 days
**Dependencies**: Tasks 3.1, 3.2

#### Subtasks:
- [ ] 3.3.1 Update architecture documentation
  - [ ] Add new components to architecture_documentation.md
  - [ ] Document LangGraph workflow
  - [ ] Update system diagrams
  
- [ ] 3.3.2 Update user guides and README
  - [ ] Add langgraph mode documentation
  - [ ] Update usage examples
  - [ ] Add troubleshooting guides
  
- [ ] 3.3.3 Create developer guides
  - [ ] Business glossar extension guide
  - [ ] FK graph customization
  - [ ] LangGraph workflow modification
  
- [ ] 3.3.4 Update CLAUDE.md with new features
  - [ ] Document new retrieval mode
  - [ ] Update testing procedures
  - [ ] Add configuration options

---

## Optional Advanced Tasks (Future Phases)

### Task 4.1: Neo4j Graph Database Integration ⚡ PRIORITY: LOW
**Module**: `neo4j_graph_integration.py`
**Estimated Time**: 1-2 weeks
**Dependencies**: Phase 1-3 completion

#### Subtasks:
- [ ] 4.1.1 Enhanced FK graph with Neo4j persistence
- [ ] 4.1.2 Cypher query generation capabilities  
- [ ] 4.1.3 Graph-based relationship discovery
- [ ] 4.1.4 Performance comparison with NetworkX approach

### Task 4.2: LLM Fine-tuning for WINCASA ⚡ PRIORITY: LOW
**Module**: `wincasa_finetuning.py`
**Estimated Time**: 2-3 weeks
**Dependencies**: Phase 1-3 completion, success metrics

#### Subtasks:
- [ ] 4.2.1 Collect successful query-SQL pairs dataset
- [ ] 4.2.2 Create WINCASA-specific fine-tuning dataset
- [ ] 4.2.3 Fine-tune model on Firebird SQL + business logic
- [ ] 4.2.4 Compare fine-tuned vs. general model performance

---

## Success Metrics & Validation

### Primary Goals:
1. **Accuracy Improvement**: 70% → 85% SQL generation accuracy
2. **JOIN Quality**: 90% correct JOIN path generation
3. **Business Logic**: 95% correct business term mapping
4. **Performance**: <20s average response time
5. **User Satisfaction**: >8/10 user rating

### Testing Strategy:
- **Continuous Testing**: Run tests after each subtask completion
- **Regression Testing**: Ensure existing functionality remains intact
- **Performance Monitoring**: Track response times and resource usage
- **User Acceptance Testing**: Real user validation of improvements

### Rollback Plan:
- Maintain backward compatibility with existing 5 retrieval modes
- Feature flags for gradual rollout of new components
- Comprehensive logging for debugging and issue resolution

---

## Implementation Notes

### Development Environment:
```bash
# Install new dependencies
pip install networkx sqlglot langgraph

# Test environment setup
python -m pytest tests/ -v --cov=.

# Development server
./start_enhanced_qa_direct.sh
```

### Code Quality Standards:
- **Type Hints**: Full type annotation for all new modules
- **Documentation**: Comprehensive docstrings following Google style
- **Testing**: 90%+ test coverage for new components
- **Linting**: Black formatting, flake8 compliance

### Risk Mitigation:
- **Incremental Development**: Each task produces working intermediate results
- **Backwards Compatibility**: New features don't break existing functionality  
- **Performance Monitoring**: Continuous performance tracking
- **Graceful Degradation**: Fallback to existing modes if new components fail

---

**Total Estimated Time**: 3-5 weeks
**Team Size**: 1-2 developers
**Risk Level**: Medium (well-defined integration points, existing architecture support)
**Expected ROI**: High (significant accuracy improvement, better user experience)