# Query Examples for Testing

## Standard Test Queries

These are the 3 benchmark queries used in `quick_3question_benchmark_final.py`:

### 1. Property Count Query
```
"How many apartments are there?"
```
**Expected**: Should return count information from WOHNUNG table

### 2. Address Lookup Query  
```
"What is the address of Petra Nabakowski?"
```
**Expected**: Should return "Marienstr. 26, 45307 Essen" from BEWOHNER table

### 3. Owner Information Query
```
"Who are the property owners?"
```
**Expected**: Should return owner names from EIGENTUEMER table

## Database Structure Context

### Main Tables
- **WOHNUNG**: Apartment/housing units (1250+ units)
- **BEWOHNER**: Residents and tenants (698+ residents) 
- **EIGENTUEMER**: Property owners

### Sample Data Points
- Petra Nabakowski lives at Marienstr. 26, 45307 Essen
- Various property owners including "Immobilien GmbH" and "Weber, Klaus"
- Apartments have numbers, object references, room counts, and square meters

## Testing Different Modes

Each of the 9 retrieval modes should handle these queries but may:
- Use different retrieval strategies
- Return results in different formats
- Have different performance characteristics
- Show different accuracy levels

## Query Testing Pattern

```python
# Standard testing approach
from gemini_llm import get_gemini_llm
llm = get_gemini_llm()

def test_queries(retriever):
    queries = [
        "How many apartments are there?",
        "What is the address of Petra Nabakowski?", 
        "Who are the property owners?"
    ]
    
    for query in queries:
        result = test_retriever(retriever, query, llm)
        print(f"Q: {query}")
        print(f"A: {result}")
        print("---")
```

This testing pattern is used to benchmark and compare the effectiveness of different retrieval modes.