# WINCASA Implementation Tasks

## Current Priority: TAG Model Implementation

### 🚨 Phase 0: Critical Foundation (IMMEDIATE)

#### Task 0.1: Fix Dependencies & Environment ⚡ CRITICAL
**Estimated**: 30 minutes  
**Status**: Pending

```bash
# Install missing dependencies
pip install langgraph sqlglot langchain-experimental

# Verify installation
python -c "import langgraph, sqlglot; print('Dependencies OK')"

# Update requirements.txt
pip freeze > requirements.txt
```

**Success Criteria**: All imports work without errors

---

#### Task 0.2: Diagnose Current SQL Generation Issues ⚡ CRITICAL
**Estimated**: 2-4 hours  
**Status**: Pending

**Subtasks**:
1. **Test all 5 retrieval modes**
   ```bash
   python diagnostic_test.py
   ```
   
2. **Create minimal prompt test** 
   - Test LLM with ONLY system prompt + query (no retrieval)
   - Verify if LLM follows basic SQL rules without context noise
   - Test with: "Wer wohnt in der Marienstr. 26, 45307 Essen"
   
3. **Analyze context interference**
   - Test if 498 YAML docs override system instructions
   - Measure prompt effectiveness vs. context overwhelming

**Example Test**:
```python
# Test system prompt compliance without retrieval noise
test_prompt = '''
CRITICAL RULES FOR SQL GENERATION:
- Table BEWOHNER contains residents
- Column BSTR contains: "Straßenname Hausnummer" (e.g. "Marienstraße 26")  
- Column BPLZORT contains: "PLZ Ort" (e.g. "45307 Essen")
- ALWAYS use LIKE patterns for addresses, NEVER exact match
- Example: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

Query: Wer wohnt in der Marienstr. 26, 45307 Essen
Generate ONLY the SQL query.
'''
```

**Success Criteria**: LLM generates correct SQL with minimal, focused prompts

---

### 🔧 Phase 1: TAG Core Implementation

#### Task 1.1: Create TAG SYN (Synthesis) Module ⚡ HIGH PRIORITY  
**File**: `tag_synthesizer.py`  
**Estimated**: 3-4 days  
**Status**: Pending  
**Dependencies**: Task 0.1, 0.2

**Implementation**:
```python
class QuerySynthesizer:
    QUERY_TYPE_SCHEMAS = {
        "address_lookup": {
            "tables": ["BEWOHNER", "BEWADR"],
            "rules": [
                "BSTR contains full street with number",
                "BPLZORT contains postal code and city", 
                "Use LIKE '%pattern%' for matching"
            ],
            "example_sql": "SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'"
        },
        "owner_lookup": {
            "tables": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "rules": ["EIGENTUEMER contains owners", "Join with VEREIG for properties"],
            "example_sql": "SELECT * FROM EIGENTUEMER E JOIN EIGADR A ON E.ID = A.EIGNR"
        },
        "financial_queries": {
            "tables": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
            "rules": ["Use ONR to link properties to accounts"],
            "example_sql": "SELECT * FROM KONTEN WHERE ONR = ?"
        },
        "property_queries": {
            "tables": ["OBJEKTE", "WOHNUNG"],
            "rules": ["OBJEKTE are buildings, WOHNUNG are individual apartments"],
            "example_sql": "SELECT COUNT(*) FROM WOHNUNG"
        }
    }
    
    def synthesize(self, query: str) -> SynthesisResult:
        query_type = self._classify_query(query)
        schema_context = self.QUERY_TYPE_SCHEMAS[query_type]
        entities = self._extract_entities(query)
        sql = self._generate_sql(entities, schema_context)
        return SynthesisResult(sql, query_type, entities, schema_context)
```

**Testing**: Create `test_tag_synthesizer.py`  
**Success Criteria**: 90% correct table selection, proper LIKE pattern usage for addresses

---

#### Task 1.2: Create SQL Validation Layer ⚡ HIGH PRIORITY
**File**: `sql_validator.py`  
**Estimated**: 2-3 days  
**Status**: Pending  
**Dependencies**: Task 0.1 (sqlglot dependency)

**Implementation**:
```python
class SQLValidator:
    def validate_and_fix(self, sql: str, available_tables: List[str]) -> ValidationResult:
        try:
            parsed = sqlglot.parse_one(sql, dialect="firebird")
            issues = []
            
            # Check table existence
            for table in self._extract_tables(parsed):
                if table not in available_tables:
                    issues.append(f"Table '{table}' does not exist")
            
            # Check Firebird syntax
            if "LIMIT" in sql.upper():
                fixed_sql = sql.upper().replace("LIMIT", "FIRST")
                issues.append("Converted LIMIT to FIRST for Firebird")
            
            return ValidationResult(
                valid=len(issues) == 0,
                issues=issues,
                fixed_sql=fixed_sql if issues else sql,
                suggestions=self._generate_suggestions(issues)
            )
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))
```

**Testing**: Create `test_sql_validator.py`  
**Success Criteria**: 95% syntax validation accuracy, 80% automatic fix success

---

#### Task 1.3: Create TAG GEN (Generation) Module ⚡ HIGH PRIORITY
**File**: `tag_generator.py`  
**Estimated**: 2 days  
**Status**: Pending  
**Dependencies**: Task 1.1

**Implementation**:
```python
class ResponseGenerator:
    def generate(self, sql_results: List[Dict], query_type: str, original_query: str) -> str:
        if not sql_results:
            return self._generate_empty_response(query_type, original_query)
        
        formatter = self.FORMATTERS[query_type]
        return formatter.format(sql_results, original_query)
    
    def _generate_empty_response(self, query_type: str, query: str) -> str:
        templates = {
            "address_lookup": f"Es wurden keine Bewohner für die angegebene Adresse gefunden.",
            "owner_lookup": f"Es wurden keine Eigentümer für die Anfrage gefunden.", 
            "count_query": f"Die Anzahl beträgt 0."
        }
        return templates.get(query_type, "Keine Ergebnisse gefunden.")
```

**Testing**: Create `test_tag_generator.py`  
**Success Criteria**: Clear, contextual German responses for all query types

---

### 🔗 Phase 2: TAG Integration

#### Task 2.1: Create TAG Pipeline Integration ⚡ HIGH PRIORITY
**File**: `tag_pipeline.py`  
**Estimated**: 2-3 days  
**Status**: Pending  
**Dependencies**: Tasks 1.1, 1.2, 1.3

**Implementation**:
```python
class TAGPipeline:
    def process(self, query: str) -> TAGResult:
        # Phase 1: SYN (Synthesis)
        synthesis = self.synthesizer.synthesize(query)
        
        # Validation
        validation = self.validator.validate_and_fix(synthesis.sql, self.available_tables)
        if not validation.valid:
            # Retry with enhanced context
            synthesis = self.synthesizer.synthesize_enhanced(query, validation.suggestions)
            validation = self.validator.validate_and_fix(synthesis.sql, self.available_tables)
        
        # Phase 2: EXEC (Execution) - Use existing FDB interface
        results = self.executor.execute(validation.fixed_sql or synthesis.sql)
        
        # Phase 3: GEN (Generation)
        response = self.generator.generate(results, synthesis.query_type, query)
        
        return TAGResult(
            query=query,
            sql=validation.fixed_sql or synthesis.sql,
            raw_results=results,
            response=response,
            synthesis_info=synthesis,
            validation_info=validation
        )
```

**Integration**: Update `firebird_sql_agent_direct.py` to include TAG as 6th retrieval mode  
**Testing**: Create `test_tag_pipeline.py`  
**Success Criteria**: End-to-end processing for all 11 test queries

---

#### Task 2.2: LangGraph Workflow Implementation ⚡ HIGH PRIORITY
**File**: `langgraph_sql_workflow.py`  
**Estimated**: 3-4 days  
**Status**: Pending  
**Dependencies**: Task 0.1, 2.1

**Implementation**:
```python
from langgraph.graph import StateGraph
from typing import TypedDict, Literal

class QueryState(TypedDict):
    query: str
    query_type: str
    entities: List[str]
    sql: str
    validation_result: ValidationResult
    execution_result: List[Dict]
    response: str
    retry_count: int
    error: Optional[str]

def create_sql_workflow():
    workflow = StateGraph(QueryState)
    
    # Add nodes
    workflow.add_node("classify_query", classify_query_node)
    workflow.add_node("synthesize_sql", synthesize_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("enhance_context", enhance_context_node)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_sql",
        decide_after_validation,
        {
            "execute": "execute_sql",
            "retry": "enhance_context", 
            "fail": "generate_response"
        }
    )
    
    return workflow.compile()
```

**Testing**: Create `test_langgraph_workflow.py`  
**Success Criteria**: Complex workflow execution with 90% success rate

---

### 🧪 Phase 3: Testing & Validation

#### Task 3.1: Comprehensive Mode Comparison ⚡ HIGH PRIORITY
**File**: `comprehensive_mode_test.py`  
**Estimated**: 2-3 days  
**Status**: Pending  
**Dependencies**: All previous tasks

**Test All 6 Modes**:
1. Enhanced mode (existing)
2. FAISS mode (existing)  
3. None mode (existing)
4. LangChain mode (fixed)
5. LangGraph mode (new)
6. TAG mode (new)

**Test Queries**:
1. "Wer wohnt in der Marienstr. 26, 45307 Essen"
2. "Wer wohnt in der Marienstraße 26"
3. "Wer wohnt in der Bäuminghausstr. 41, Essen"
4. "Wer wohnt in der Schmiedestr. 8, 47055 Duisburg"
5. "Alle Mieter der MARIE26"
6. "Alle Eigentümer vom Haager Weg bitte"
7. "Liste aller Eigentümer"
8. "Liste aller Eigentümer aus Köln"
9. "Liste aller Mieter in Essen"
10. "Durchschnittliche Miete in Essen"
11. "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg"

**Testing Commands**:
```bash
# Test all modes with comprehensive analysis
python comprehensive_mode_test.py --all-modes --detailed-analysis

# Generate comparison report
python generate_comparison_report.py --output comparison_report.md
```

**Success Criteria**: 
- TAG mode: >90% SQL correctness (vs current ~20%)
- LangGraph mode: >85% SQL correctness
- All modes: Complete execution without crashes

---

---

### 🔗 Phase 2: Information Architecture Redesign

#### Task 2.3: Analyze Current Information Distribution ⚡ HIGH PRIORITY
**File**: Information architecture analysis
**Estimated**: 1 day
**Status**: Pending
**Dependencies**: Analysis of current system

**Current State Analysis**:
- **System Prompt**: Currently mixed with retrieval context
- **YAML Structure**: 498 files with everything mixed together
- **Problem**: LLM overwhelmed by detailed info when it needs basic rules

**Information Audit**:
```
Current YAML Content (BEWOHNER.yaml example):
├── Basic Info (table_name, description) → System Prompt
├── Business Context (business_examples) → System Prompt  
├── Detailed Columns (125+ lines) → Embeddings
├── Constraints & Relations → Embeddings
├── Internal Conventions → Embeddings
└── Common Queries → Embeddings
```

**Analysis Results**: 
- **80% of YAML content** should be in embeddings (detailed technical info)
- **20% of YAML content** should be in system prompt (essential rules)

---

#### Task 2.4: Redesign System Prompt ⚡ HIGH PRIORITY
**File**: `optimized_system_prompt.py`
**Estimated**: 1-2 days
**Status**: Pending
**Dependencies**: Task 2.3

**New System Prompt Structure**:
```python
OPTIMIZED_SYSTEM_PROMPT = """
CORE FIREBIRD SQL RULES:
- Use FIRST instead of LIMIT for row limiting
- Use LIKE '%pattern%' for address matching, NEVER exact match
- Primary tables: BEWOHNER (residents), EIGENTUEMER (owners), WOHNUNG (apartments), OBJEKTE (buildings), KONTEN (accounts)

CRITICAL ADDRESS PATTERNS:
- BSTR column: "Straßenname Hausnummer" (e.g. "Marienstraße 26")
- BPLZORT column: "PLZ Ort" (e.g. "45307 Essen")
- ALWAYS use: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

KEY RELATIONSHIPS:
- ONR (Object Number): Central linking field between properties, residents, accounts
- JOIN paths: BEWOHNER.ONR → OBJEKTE.ONR, EIGENTUEMER → VEREIG.ONR → OBJEKTE.ONR

QUERY CLASSIFICATION:
- Address lookup: "Wer wohnt in..." → BEWOHNER table with LIKE patterns
- Property count: "Wie viele Wohnungen..." → COUNT(*) FROM WOHNUNG  
- Owner lookup: "Eigentümer..." → EIGENTUEMER table with city filters
- Financial: "Miete, Kosten..." → KONTEN/BUCHUNG tables with aggregations
"""
```

**Testing**: Compare LLM compliance with focused vs. overwhelming prompts

---

#### Task 2.5: Create Focused Embedding System ⚡ HIGH PRIORITY
**File**: `focused_embeddings.py`
**Estimated**: 2-3 days
**Status**: Pending
**Dependencies**: Task 2.4

**New Embedding Strategy**:
1. **Table-Specific Chunks**: Each table gets focused document with detailed info
2. **Query-Driven Retrieval**: Retrieve only tables identified by TAG SYN
3. **Structured Content**: Separate technical details from essential rules

**Implementation**:
```python
class FocusedEmbeddingSystem:
    def __init__(self):
        self.table_embeddings = {}  # Table name → detailed YAML content
        self.query_classifier = QuerySynthesizer()  # From TAG SYN
    
    def retrieve_table_details(self, table_names: List[str]) -> str:
        """Retrieve only specific table details, not all 498 YAMLs"""
        relevant_details = []
        for table in table_names:
            if table in self.table_embeddings:
                relevant_details.append(self.table_embeddings[table])
        return "\n\n".join(relevant_details)
    
    def process_query(self, query: str) -> str:
        # 1. TAG SYN determines needed tables
        synthesis = self.query_classifier.synthesize(query)
        tables_needed = synthesis.schema_context["primary_tables"]
        
        # 2. Retrieve only relevant table details
        detailed_context = self.retrieve_table_details(tables_needed)
        
        # 3. Combine focused prompt + targeted details
        return OPTIMIZED_SYSTEM_PROMPT + "\n\nRELEVANT TABLES:\n" + detailed_context
```

**Success Criteria**: Retrieve 2-5 relevant table details instead of all 498 YAMLs

---

#### Task 2.6: Implement TAG Pipeline with Information Architecture ⚡ HIGH PRIORITY
**File**: `tag_pipeline_optimized.py`
**Estimated**: 2-3 days
**Status**: Pending
**Dependencies**: Tasks 2.4, 2.5

**Optimized Pipeline**:
```python
class OptimizedTAGPipeline:
    def process(self, query: str) -> TAGResult:
        # Phase 1: SYN with focused context
        synthesis = self.synthesizer.synthesize(query)
        
        # Phase 2: Retrieve only needed table details
        needed_tables = synthesis.schema_context["primary_tables"] 
        detailed_context = self.embedding_system.retrieve_table_details(needed_tables)
        
        # Phase 3: Generate SQL with focused context
        focused_prompt = OPTIMIZED_SYSTEM_PROMPT + detailed_context
        sql = self.llm.generate_sql(query, focused_prompt)
        
        # Phase 4: EXEC (existing FDB interface)
        results = self.executor.execute(sql)
        
        # Phase 5: GEN (existing response formatter)
        response = self.generator.generate(results, synthesis.query_type, query)
        
        return TAGResult(query, sql, results, response, synthesis)
```

---

### 🔧 Phase 4: Unified Embedding System Consolidation (Future Implementation)

#### Task 4.1: Analyze Current Embedding Fragmentation ⚡ MEDIUM PRIORITY
**File**: Analysis of current embedding systems
**Estimated**: 1 day
**Status**: Pending (Future Phase)
**Dependencies**: TAG pipeline completion

**Current Fragmented State**:
- **Enhanced Mode**: `enhanced_retrievers.py` - Multi-stage FAISS with categories
- **FAISS Mode**: `retrievers.py` - Basic FAISS implementation  
- **None Mode**: No embeddings
- **LangChain Mode**: Uses own retrieval system
- **TAG Mode**: `focused_embeddings.py` - Strategic focused approach

**Problems**:
- Multiple separate embedding models → memory waste
- Duplicate vector stores for same documents → performance loss
- Inconsistent context quality across modes
- Complex maintenance across multiple files

---

#### Task 4.2: Design Unified Embedding Architecture ⚡ MEDIUM PRIORITY
**File**: `unified_embedding_hub.py`
**Estimated**: 2-3 days
**Status**: Pending (Future Phase)
**Dependencies**: Task 4.1

**Unified Architecture Design**:
```python
class UnifiedEmbeddingHub:
    """Central embedding system used by all retrieval modes"""
    
    def __init__(self, openai_api_key: str):
        # Single embedding model shared across all modes
        self.embeddings_model = OpenAIEmbeddings(...)
        # Shared vector stores for efficiency
        self.shared_vector_stores = {...}
    
    # Mode-specific retrieval methods
    def get_enhanced_context(self, query: str) -> str:
        """Multi-stage retrieval for enhanced mode"""
        
    def get_faiss_context(self, query: str) -> str:
        """Similarity-based retrieval for FAISS mode"""
        
    def get_minimal_context(self, query: str) -> str:
        """Essential context only for None mode"""
        
    def get_schema_context(self, query: str) -> str:
        """Schema-focused retrieval for LangChain mode"""
        
    def get_focused_context(self, query: str, tables: List[str]) -> str:
        """Strategic focused retrieval for TAG mode"""
```

**Benefits**:
- **Performance**: Single embedding model, shared vector stores, reduced memory
- **Consistency**: All modes use same strategic information architecture  
- **Maintenance**: One place to update embedding logic
- **Quality**: Unified context delivery across all retrieval modes

---

#### Task 4.3: Implement Mode-Specific Retrieval Strategies ⚡ MEDIUM PRIORITY
**File**: Extend `focused_embeddings.py` or create `unified_embedding_hub.py`
**Estimated**: 2-3 days
**Status**: Pending (Future Phase)
**Dependencies**: Task 4.2

**Implementation Strategy**:
1. **Extend current `focused_embeddings.py`** with mode-specific methods
2. **Create retrieval strategy mapping**:
```python
retrieval_strategies = {
    "enhanced": hub.get_enhanced_context,
    "faiss": hub.get_faiss_context,
    "none": hub.get_minimal_context, 
    "langchain": hub.get_schema_context,
    "tag": hub.get_focused_context
}
```
3. **Maintain backward compatibility** while improving performance
4. **Share vector stores** across all modes for efficiency

---

#### Task 4.4: Refactor Existing Modes to Use Unified System ⚡ LOW PRIORITY
**Files**: `firebird_sql_agent_direct.py`, `enhanced_retrievers.py`, `retrievers.py`
**Estimated**: 3-4 days
**Status**: Pending (Future Phase)
**Dependencies**: Task 4.3

**Refactoring Strategy**:
1. **Update mode initialization** to use unified embedding hub
2. **Replace individual embedding systems** with shared hub calls
3. **Ensure backward compatibility** for existing functionality
4. **Test all modes** with unified system
5. **Performance benchmarking** to verify improvements

**Success Criteria**:
- All 5+ modes work with unified embedding system
- Memory usage reduced by consolidating duplicate embeddings
- Consistent context quality across all modes
- Maintenance simplified to single embedding codebase

---

## Current Status Tracking

### ✅ Completed
- All 5 original retrieval modes working
- Testing framework (pytest) operational  
- Database connection pooling implemented
- Business Glossar with JOIN-reasoning
- FK-Graph Analysis with NetworkX
- **TAG SYN (Synthesis) Module** ✅
- **TAG GEN (Generation) Module** ✅
- **SQL Validator with Firebird fixes** ✅
- **Optimized system prompt with role definition and document railroad** ✅
- **Focused embedding system for strategic information architecture** ✅

### 🔄 In Progress
- Information architecture analysis

### ⏳ Pending
- TAG pipeline with strategic information architecture
- Comprehensive testing of new approach
- **Unified embedding system consolidation** (Future Phase)

### 🎯 Success Metrics
- **Target**: SQL generation accuracy 20% → 90%
- **Information Efficiency**: 498 YAMLs → 2-5 targeted retrievals per query
- **Context Size**: Reduce from overwhelming to focused, relevant information
- **Timeline**: 2 weeks for information architecture + 2 weeks integration
- **Expected ROI**: Very High (fixing fundamental context delivery issues)

---

**Commands to Start**:
```bash
# 1. Install dependencies (30 minutes)
pip install langgraph sqlglot langchain-experimental

# 2. Test current modes (1 hour)  
python diagnostic_test.py

# 3. Begin TAG implementation
# Start with tag_synthesizer.py
```