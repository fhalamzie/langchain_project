# Retriever Modes Implementation Guide for Claude

This document provides exact implementation patterns for the 5 core retriever modes. **Mock/redundant modes have been eliminated** for system optimization.

## Available Core Modes (5/5)

### 1. Contextual Enhanced Mode ✅
- **Class**: `ContextualEnhancedRetriever`
- **Type**: Document-based with real WINCASA data (517 apartments)
- **Initialization**: `ContextualEnhancedRetriever(real_documents, openai_api_key)`
- **Features**: Query-type classification, contextual document selection
- **Data Source**: Real database via `real_schema_extractor.py`

### 2. Hybrid FAISS Mode ✅  
- **Class**: `HybridFAISSRetriever`
- **Type**: Document-based with vector + keyword search
- **Initialization**: `HybridFAISSRetriever(real_documents, openai_api_key)`
- **Features**: BM25 + semantic similarity, query expansion
- **Data Source**: Real database embeddings

### 3. Guided Agent Mode ✅
- **Class**: `GuidedAgentRetriever`
- **Type**: Database-based with TAG + LangChain integration
- **Initialization**: `GuidedAgentRetriever(db_connection_string, llm, enable_monitoring=False)`
- **Features**: ML-guided schema filtering, **LangChain parsing error recovery**
- **Data Source**: Direct WINCASA2022.FDB queries

### 4. TAG Classifier Mode ✅
- **Class**: `AdaptiveTAGClassifier`
- **Type**: Machine learning query classifier (10 patterns)
- **Initialization**: `AdaptiveTAGClassifier()`
- **Features**: Query type classification, table selection guidance
- **Model**: Pre-trained ML classifier with adaptive learning

### 5. Contextual Vector Mode ✅
- **Class**: `ContextualVectorRetriever`
- **Type**: Advanced vector search with TAG integration
- **Initialization**: `ContextualVectorRetriever(real_documents, openai_api_key)`
- **Features**: TAG-enhanced embeddings, contextual boosting
- **Data Source**: Enhanced real documents with ML classification

## Eliminated Modes (44% Reduction)

### ❌ Removed Modes
- **Enhanced Mode** - 100% alias for Contextual Enhanced (redundant)
- **Filtered LangChain Mode** - Superseded by Guided Agent with better error handling
- **Smart Fallback Mode** - Mock solution with simulated schema data
- **Smart Enhanced Mode** - Redundant functionality with Contextual Vector

## Real Data Integration

All document-based modes now use:
```python
from real_schema_extractor import create_real_documents
real_docs = create_real_documents()  # Extracts from WINCASA2022.FDB
```

**Real database counts:**
- 517 apartments (not 1250 mock)
- 698 residents with actual addresses
- 540 property owners
- 81 objects, 3595 accounts

## Benchmarking

To test all 5 core modes:
```bash
python quick_3question_benchmark_final.py
```

Expected output:
```
🎯 Working Modes: 5/5
✅ Functional: Contextual Enhanced, Hybrid FAISS, Guided Agent, TAG Classifier, Contextual Vector
✅ Real data: 517 apartments, 698 residents, 540 owners
🎉 System ready for production with real database integration!
```

## Latest Fixes

- **✅ LangChain Parsing Recovery**: Guided Agent extracts responses from parsing error messages
- **✅ Real Data Architecture**: Zero mock documents, all data from WINCASA2022.FDB  
- **✅ System Optimization**: Cleaner codebase with 44% reduction in complexity