# WINCASA Testing Guide

**Comprehensive testing strategy for a 5-mode query system**

## 🎯 Quick Testing

### One-Line Tests
```bash
# Fastest tests first
python test_suite_quick.py              # 5 core tests (~30 seconds)
python debug_single_query.py "Test" --compare  # Compare all modes

# With server validation
./run_streamlit.sh --test               # Tests + starts server
```

### Test Categories
```bash
# Unit Tests
python test_suite_phase2.py            # 26 comprehensive tests (~2 minutes)

# Integration Tests  
python test_golden_queries_kb.py       # Real business queries (~1 minute)
python test_layer4.py                  # SQL→JSON validation (~45 seconds)

# Performance Tests
python benchmark_current_modes.py      # Performance comparison (~3 minutes)
```

## 🔧 Mode-Specific Testing

### Mode 5: Unified Engine Testing
```bash
# Test only unified engine components
python -c "
from wincasa_query_engine import WincasaQueryEngine
engine = WincasaQueryEngine()

# Test different execution paths
test_queries = [
    'Alle Mieter',           # Should hit optimized search (1-5ms)
    'Portfolio FHALAMZIE',   # Should hit template engine (~100ms)  
    'Complex analytics',     # Should hit legacy fallback (500-2000ms)
]

for query in test_queries:
    result = engine.execute_query(query)
    print(f'{query}: {result.execution_path} ({result.response_time_ms}ms)')
"

# Debug unified engine routing
python debug_single_query.py "Zeige alle Mieter" --mode=UNIFIED --trace
```

### Legacy Modes (1-4) Testing
```bash
# Test each legacy mode individually
for mode in JSON_VANILLA JSON_SYSTEM SQL_VANILLA SQL_SYSTEM; do
    echo "Testing $mode..."
    python debug_single_query.py "Test query" --mode=$mode
done

# Compare legacy vs unified
python debug_single_query.py "Alle Mieter" --compare
```

### Performance Testing by Mode
```bash
# Benchmark specific modes
python -c "
import time
from wincasa_query_engine import WincasaQueryEngine
from llm_handler import process_query

query = 'Zeige alle Mieter'

# Test Mode 5 (Unified)
engine = WincasaQueryEngine()
start = time.time()
result = engine.execute_query(query)
unified_time = (time.time() - start) * 1000
print(f'Unified: {unified_time:.1f}ms')

# Test Mode 1 (JSON_VANILLA)  
start = time.time()
result = process_query(query, 'JSON_VANILLA')
legacy_time = (time.time() - start) * 1000
print(f'Legacy: {legacy_time:.1f}ms')

print(f'Performance gain: {legacy_time/unified_time:.1f}x faster')
"
```

## 🧪 Development Testing Workflows

### Adding a New Feature
```bash
# 1. Write your feature code
# 2. Test in isolation first
python debug_single_query.py "New feature query" --mode=UNIFIED --trace

# 3. Run mode-specific tests
python test_suite_quick.py

# 4. Add to golden set if successful
echo "New feature query" >> golden_set/additional_queries.txt

# 5. Full regression test
python test_suite_phase2.py
```

### Debugging a Failing Query
```bash
# 1. Isolate the issue
python debug_single_query.py "Failing query" --trace

# 2. Test across all modes to see pattern
python debug_single_query.py "Failing query" --compare

# 3. Check logs for details
tail -f logs/layer2_errors.log

# 4. Test specific components
python -c "
from knowledge_base_loader import get_knowledge_base
kb = get_knowledge_base()
enhanced = kb.enhance_query('Failing query')
print(f'Enhanced query: {enhanced}')
"
```

### Testing Knowledge Base Changes
```bash
# 1. Re-extract knowledge after SQL changes
python knowledge_extractor.py

# 2. Test critical field mappings
python test_golden_queries_kb.py

# 3. Verify specific field mappings
python -c "
from knowledge_base_loader import get_knowledge_base
kb = get_knowledge_base()
print('KALTMIETE mapping:', kb.get_canonical_field('KALTMIETE'))
print('Should be: BEWOHNER.Z1')
"
```

## 🚀 End-to-End Testing

### New Business Query Workflow
```bash
# Example: Adding "Leerstand in Hauptstraße" query

# 1. Analyze requirement
python debug_single_query.py "Leerstand in Hauptstraße" --compare
# Determines best mode for this query type

# 2. If needs new template, add to templates
# Edit sql_template_engine.py 

# 3. If needs new search capability, update search
# Edit wincasa_optimized_search.py

# 4. Test the change
python debug_single_query.py "Leerstand in Hauptstraße" --mode=UNIFIED --trace

# 5. Add to test suite
echo "Leerstand in Hauptstraße" >> golden_set/vacancy_queries.txt

# 6. Performance validation
python benchmark_current_modes.py --query="Leerstand in Hauptstraße"

# 7. Full regression test
python test_suite_phase2.py
```

### Pre-Deployment Testing
```bash
# 1. Full test suite must pass
python test_suite_phase2.py
if [ $? -ne 0 ]; then echo "❌ Fix tests first!"; exit 1; fi

# 2. Performance benchmarks
python benchmark_current_modes.py

# 3. Golden set validation  
python test_golden_queries_kb.py

# 4. Log analysis for errors
grep "ERROR" logs/layer2_errors.log | tail -10

# 5. Ready to deploy
echo "✅ All tests passed - ready for deployment"
```

## 📊 Test Data Management

### Using Real vs Mock Data
```bash
# Switch to real database for testing
export TEST_WITH_REAL_DB=true
python test_suite_quick.py

# Switch back to mock for speed
unset TEST_WITH_REAL_DB  
python test_suite_quick.py
```

### Golden Set Management
```bash
# View current golden queries
cat golden_set/realistic_golden_set.json | jq '.[] | .query'

# Add new golden query
python -c "
import json
with open('golden_set/realistic_golden_set.json', 'r') as f:
    golden = json.load(f)
    
golden.append({
    'query': 'New test query',
    'expected_entities': ['tenant', 'property'],
    'min_results': 1
})

with open('golden_set/realistic_golden_set.json', 'w') as f:
    json.dump(golden, f, indent=2)
"
```

## 🔍 Debug Strategies

### Common Testing Patterns
```python
# 1. Test with breakpoints
import pdb; pdb.set_trace()  # Manual breakpoint
result = engine.execute_query("Test")

# 2. Test with logging
import logging
logging.basicConfig(level=logging.DEBUG)
result = engine.execute_query("Test")

# 3. Test with timing
import time
start = time.time()
result = engine.execute_query("Test")
print(f"Took: {(time.time() - start) * 1000}ms")

# 4. Test with validation
assert result.success == True
assert result.response_time_ms < 1000  # Performance requirement
assert len(result.data) > 0           # Data requirement
```

### Error Categories
```bash
# Knowledge Base Errors
grep "knowledge.*error" logs/layer2_errors.log

# Query Routing Errors  
grep "routing.*failed" logs/layer2_errors.log

# Database Connection Errors
grep "database.*connection" logs/layer2_errors.log

# Template Engine Errors
grep "template.*error" logs/layer2_errors.log
```

## 📈 Performance Testing

### Response Time Targets
- **Optimized Search**: <5ms
- **Template Engine**: <200ms  
- **Legacy JSON**: <500ms
- **Legacy SQL**: <2000ms

### Performance Test Script
```bash
python -c "
import time
from wincasa_query_engine import WincasaQueryEngine

engine = WincasaQueryEngine()
query = 'Performance test query'

# Run 10 times and average
times = []
for i in range(10):
    start = time.time()
    result = engine.execute_query(query)
    times.append((time.time() - start) * 1000)

avg_time = sum(times) / len(times)
print(f'Average response time: {avg_time:.1f}ms')
print(f'Target met: {avg_time < 5000}')  # 5s max target
"
```

---

**Testing Status**: Production-ready with comprehensive coverage across all 5 modes and testing workflows.