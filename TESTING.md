# TESTING.md

## Test-Strategie

### Test-Suiten
- ID: test_suite_phase2.py
  Coverage: 100%
  Tests: 26
  Status: All passing
  SessionID: phase2-test-20250614

- ID: test_suite_quick.py
  Coverage: Core functionality
  Tests: 5
  Status: No LLM calls
  SessionID: quick-test-20250614

### Integration Tests
- ID: test_layer4.py
  Target: SQL→JSON validation
  Queries: 35
  Status: All validated
  SessionID: layer4-test-20250612

- ID: phase24_integration_test.py
  Target: End-to-End Phase 2.4
  Coverage: 80%
  Status: 4/5 passing
  SessionID: integration-20250614

### Business Tests
- ID: test_golden_queries_kb.py
  Queries: 100 realistic
  Focus: Knowledge Base
  Status: 100% success
  SessionID: golden-20250614

- ID: test_kaltmiete_query.py
  Target: KALTMIETE=BEWOHNER.Z1
  Critical: Bug prevention
  Status: Fixed
  SessionID: kaltmiete-20250614

- ID: test_knowledge_integration.py
  Target: KB field mappings
  Mappings: 226
  Status: Validated
  SessionID: kb-test-20250614

### Performance Tests
- ID: benchmark_current_modes.py
  Modi: All 5
  Baseline: Established
  Improvement: 1000x (1-5ms vs 300-2000ms)
  SessionID: benchmark-20250614

### Test Execution
```bash
# Quick tests (no LLM)
python test_suite_quick.py

# Full test suite
python test_suite_phase2.py

# Specific module
python test_layer4.py

# Performance benchmark
python benchmark_current_modes.py
```

### Test Data
- ID: test_data/golden_set/
  Queries: 100
  Categories: Lookup(13%), Template(22%), Complex(65%)
  Format: JSON with expected results
  SessionID: golden-20250614

### Coverage Requirements
- Core Modules: 100%
- Intelligence Layer: 100%
- Data Layer: 100%
- Knowledge Base: 100%

### CI/CD Integration
- Pre-commit: test_suite_quick.py
- Pre-deployment: test_suite_phase2.py
- Post-deployment: benchmark_current_modes.py

### Test Patterns
```python
# Unit Test Pattern
def test_optimized_search_performance():
    search = WincasaOptimizedSearch()
    result = search.search("Müller")
    assert result.response_time_ms < 5

# Integration Test Pattern  
def test_unified_engine_routing():
    engine = WincasaQueryEngine()
    result = engine.process_query("Zeige alle Mieter")
    assert result.processing_mode in ["template", "structured_search", "legacy"]

# Business Test Pattern
def test_kaltmiete_field_mapping():
    handler = WincasaLLMHandler()
    result = handler.query_llm("Summe Kaltmiete", mode="JSON_SYSTEM")
    assert "BEWOHNER.Z1" in result.get("sql", "")
```