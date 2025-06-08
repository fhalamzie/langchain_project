# Implementation Guide for Claude AI

## Critical Rules

1. **NEVER modify retriever initialization patterns** - They are tested and working
2. **ALWAYS test with `quick_3question_benchmark_final.py`** after any changes
3. **Database connection format is critical**: Use double slash for absolute paths
4. **All 9 modes must remain functional** - No breaking changes allowed

## Common Implementation Patterns

### Pattern 1: Testing a Retriever
```python
# ALWAYS use this pattern for testing retrievers
def test_retriever(retriever, query, llm):
    # Check for direct response method
    if hasattr(retriever, 'get_response'):
        return retriever.get_response(query)
    
    # Check for query method
    elif hasattr(retriever, 'query'):
        return retriever.query(query)
    
    # Check for retrieve method (most common)
    elif hasattr(retriever, 'retrieve'):
        result = retriever.retrieve(query)
        
        # Handle custom result objects
        if hasattr(result, 'documents'):
            docs = result.documents
        elif isinstance(result, list):
            docs = result
        else:
            docs = []
        
        # Generate response
        if docs:
            context = "\n".join([doc.page_content for doc in docs[:2]])
            return llm.invoke(f"Based on this context:\n{context}\n\nAnswer: {query}")
        else:
            return "No relevant documents found"
```

### Pattern 2: Creating Mock Documents
```python
# ALWAYS use this structure for mock documents
from langchain_core.documents import Document

def create_mock_documents():
    return [
        Document(
            page_content="""table_name: WOHNUNG
description: Apartment/housing units database
columns:
  - WHG_NR: Apartment number
  - ONR: Object number
  - QMWFL: Living space in square meters
  - ZIMMER: Number of rooms
sample_data:
  - Total apartments: 1250 units
  - Average rent: €850/month""",
            metadata={"table_name": "WOHNUNG", "query_type": "property_count", "source": "WOHNUNG.yaml"}
        ),
        # Add more documents as needed
    ]
```

### Pattern 3: Database Connection
```python
# ALWAYS use this format for Firebird connections
db_connection = "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
# Note the double slash (//) before absolute path
```

### Pattern 4: Environment Setup
```python
# ALWAYS load environment variables this way
from dotenv import load_dotenv
import os

load_dotenv('/home/envs/openai.env')
openai_api_key = os.getenv('OPENAI_API_KEY')
```

## Error Recovery

If any mode fails:
1. Check initialization parameters match exactly
2. Verify environment variables are loaded
3. Ensure database is running: `sudo systemctl status firebird`
4. Check file permissions on WINCASA2022.FDB
5. Run recovery test: `python quick_3question_benchmark_final.py`

## Adding New Features

When adding new features:
1. Create feature branch
2. Implement without breaking existing modes
3. Test all 9 modes remain functional
4. Update relevant documentation
5. Only then merge to main

## Testing Commands

```bash
# Standard test sequence
source venv/bin/activate

# Quick verification (3 questions, all modes)
python quick_3question_benchmark_final.py

# Comprehensive testing
python comprehensive_endresults_test.py

# Performance benchmarking
python performance_benchmarking_suite.py

# Individual mode status
python test_9_mode_status.py
```

## Common Pitfalls to Avoid

1. **Don't change initialization signatures** - Will break benchmarking
2. **Don't assume retriever interfaces** - Always check with hasattr()
3. **Don't forget custom result objects** - SmartEnhancedResult, ContextualVectorResult
4. **Don't modify mock document structure** - Tests depend on it
5. **Don't skip testing after changes** - All modes must work

## Quick Reference

- **Document-based**: Enhanced, Contextual Enhanced, Hybrid FAISS, Smart Enhanced, Contextual Vector
- **Database-based**: Smart Fallback, Filtered LangChain, Guided Agent
- **Classifier-based**: TAG Classifier

Each has specific initialization requirements documented in retriever-modes.md.