# TESTING.md

## Test-Strategie & E2E Testing

### Test-Pyramid Architecture

**4-Layer Test Strategy**:
```
┌─────────────────────────────────┐
│        Pipeline Tests           │ ← tests/pipeline/
│      (SAD System Validation)    │
├─────────────────────────────────┤
│          E2E Tests              │ ← tests/e2e/
│    (Playwright UI Automation)   │
├─────────────────────────────────┤  
│      Integration Tests          │ ← tests/integration/
│    (Real System Components)     │
├─────────────────────────────────┤
│         Unit Tests              │ ← tests/unit/
│    (src/wincasa/* modules)      │
└─────────────────────────────────┘
```

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

### Quality Tests
- ID: benchmark_current_modes.py
  Modi: All 5
  Baseline: Established
  Focus: Accuracy and correctness validation
  SessionID: benchmark-20250614

### E2E Testing with Playwright

**End-to-End Test Suite (tests/e2e/)**:
```python
# test_wincasa_complete_e2e.py
class TestWincasaE2E:
    async def test_complete_workflow_cycle(self):
        """Full user workflow: start → query → results → comparison"""
        await page.navigate_to_streamlit_app()
        await page.select_mode("🚀 Unified Engine (Phase 2 - intelligent)")
        await page.enter_query("Zeige alle Mieter in Berlin")
        await page.click_search()
        await page.verify_results_displayed()
        
    async def test_multi_mode_comparison(self):
        """Test all 5 modes with same query"""
        query = "Portfolio Übersicht alle Eigentümer"
        for mode in ["json_vanilla", "json_system", "sql_vanilla", "sql_system", "unified"]:
            results = await self.run_mode_test(mode, query)
            assert results.success == True
            
    async def test_ui_responsiveness(self):
        """Verify UI interactions and state management"""
        await page.test_checkbox_interactions()
        await page.test_session_state_preservation()
        await page.test_error_handling()
```

**Pipeline Validation Tests (tests/pipeline/)**:
```python
# test_sad_system.py  
class TestSADPipeline:
    def test_project_structure_integrity(self):
        """Validate src/wincasa/ package structure"""
        
    def test_import_paths_work(self):
        """Test all wincasa.module.submodule imports"""
        
    def test_config_loading_works(self):
        """Validate configuration from new paths"""
        
    def test_system_prompts_exist(self):
        """Check VERSION_*.md files in utils/"""
```

### Test Execution
```bash
# All tests with coverage
./tools/scripts/run-tests.sh

# E2E tests only  
pytest tests/e2e/ -v

# Integration tests
pytest tests/integration/ -v

# Pipeline validation
pytest tests/pipeline/ -v

# Unit tests
pytest tests/unit/ -v

# Quick tests (no LLM)
python test_suite_quick.py

# Quality benchmark
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
- Post-deployment: benchmark_current_modes.py (quality validation)

### Test Patterns
```python
# Unit Test Pattern
def test_optimized_search_accuracy():
    search = WincasaOptimizedSearch()
    result = search.search("Müller")
    assert result.accuracy == 100.0

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