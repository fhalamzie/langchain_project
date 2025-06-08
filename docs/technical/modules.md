# Core Modules Overview

## 🎯 Core Retriever Modules (9 Modes)

### Document-Based Retrievers
- `enhanced_retrievers.py` - Mode #1: Enhanced retrieval (alias for ContextualEnhanced)
- `contextual_enhanced_retriever.py` - Mode #2: Context-aware document retrieval
- `hybrid_faiss_retriever.py` - Mode #3: FAISS-based hybrid semantic+keyword search
- `smart_enhanced_retriever.py` - Mode #7: Smart Enhanced (TAG + Enhanced combination)
- `contextual_vector_retriever.py` - Mode #9: Contextual Vector (TAG + FAISS combination)

### Database-Based Retrievers
- `smart_fallback_retriever.py` - Mode #6: Smart Fallback (optimized None mode)
- `filtered_langchain_retriever.py` - Mode #4: Filtered LangChain (schema-filtered SQL agent)
- `guided_agent_retriever.py` - Mode #8: Guided Agent (TAG + LangChain combination)

### Classification-Based Retrievers
- `adaptive_tag_classifier.py` - Mode #5: TAG Classifier (ML-based query classification)

## Supporting Modules

### Database
- `database_connection_pool.py` - Connection pooling for Firebird
- `extract_from_firebird.py` - Database schema extraction
- `fdb_direct_interface.py` - Direct Firebird interface

### Optimization
- `sql_query_optimizer.py` - SQL query optimization
- `query_result_cache.py` - Query result caching
- `simple_sql_validator.py` - SQL validation

### Utilities
- `gemini_llm.py` - LLM configuration (Gemini via OpenRouter)
- `business_glossar.py` - Business terminology mapping
- `tag_pipeline.py` - TAG processing pipeline

## 🧪 Testing Modules

### Primary Benchmarking
- `quick_3question_benchmark_final.py` - **CRITICAL**: Main 9/9 verification script
- `comprehensive_endresults_test.py` - End-to-end testing with real database results
- `performance_benchmarking_suite.py` - Performance optimization analysis
- `test_9_mode_status.py` - Quick 9-mode status verification

### Current Test Suite
- `improved_9_mode_test.py` - Improved testing framework
- `final_9mode_comprehensive_test.py` - Comprehensive 9-mode testing
- `test_real_database_results.py` - Real database execution verification
- `phase3_comprehensive_matrix.py` - Performance matrix analysis
- `test_phase2_combinations.py` - Phase 2 combination testing

### Performance Testing
- `test_connection_pool_optimization.py` - Database connection pool testing
- `test_simple_connection_pool.py` - Basic connection pool verification

### Improvement Verification Tests
- `test_contextual_enhanced_improvement.py` - Task 1.1 improvement verification
- `test_hybrid_faiss_improvement.py` - Task 1.2 improvement verification  
- `test_smart_fallback_improvement.py` - Task 1.3 improvement verification
- `test_filtered_langchain_improvement.py` - Task 1.4 improvement verification
- `test_adaptive_tag.py` - Task 1.5 improvement verification

## 🗂️ TAG System Files

- `adaptive_tag_synthesizer.py` - Enhanced TAG processor with synthesis capabilities
- `tag_pipeline.py` - TAG orchestration and processing pipeline
- `tag_retrieval_mode.py` - TAG mode integration utilities

## 📁 Archived Files (Moved to /archive/)

### Legacy Test Files (Superseded)
- `comprehensive_mode_test.py` - Older 6-mode test
- `final_comprehensive_test.py` - Duplicate functionality
- `quick_3question_benchmark.py` - Superseded by _final version
- `quick_endresults_test.py` - Superseded by comprehensive versions
- `test_final_fixes.py` - Specific fix verification (outdated)
- `test_fixes.py` - Generic fixes (outdated)

### Demo/Concept Files
- `firebird_agent_with_tag.py` - Early TAG concept demo
- `quick_tag_demo.py` - Simple TAG demonstration
- `test_tag_concept.py` - TAG concept validation
- `test_tag_mode.py` - Early TAG mode test
- `minimal_prompt_test.py` - Isolated LLM testing