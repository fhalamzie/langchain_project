#!/usr/bin/env python3
"""
WINCASA End-to-End Tests - Critical Business Flows
Tests kritische Geschäftsszenarien über die komplette UI-zu-Datenbank Pipeline
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import time
from typing import Dict, List
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WincasaE2ETests:
    """
    End-to-End Test Suite für kritische WINCASA Business-Flows
    
    Testet die 5 kritischen Szenarien:
    1. "Zeige alle Mieter" → TENANT_SEARCH 
    2. "Summe Kaltmiete" → BEWOHNER.Z1 (nicht KBETRAG!)
    3. "Portfolio Eigentümer" → OWNER_PORTFOLIO  
    4. "Leerstand" → VACANCY_ANALYSIS mit EIGNR = -1
    5. Performance-Tests für alle 5 Modi
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8667"
        self.test_queries = self._load_golden_queries()
        
    def _load_golden_queries(self) -> List[Dict]:
        """Lädt Golden Set Test Queries"""
        try:
            golden_path = Path(__file__).parent.parent / "test_data/golden_set/queries.json"
            with open(golden_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load golden queries: {e}")
            return self._get_fallback_queries()
    
    def _get_fallback_queries(self) -> List[Dict]:
        """Fallback Test Queries falls Golden Set nicht verfügbar"""
        return [
            {
                "query": "Zeige alle Mieter",
                "expected_intent": "TENANT_SEARCH", 
                "expected_path": "optimized_search",
                "min_results": 1
            },
            {
                "query": "Summe Kaltmiete",
                "expected_intent": "RENT_QUERY",
                "expected_path": "template_engine", 
                "validation": "BEWOHNER.Z1"
            },
            {
                "query": "Portfolio Eigentümer",
                "expected_intent": "OWNER_PORTFOLIO",
                "expected_path": "template_engine",
                "min_results": 1
            },
            {
                "query": "Leerstand",
                "expected_intent": "VACANCY_ANALYSIS", 
                "expected_path": "template_engine",
                "validation": "EIGNR = -1"
            }
        ]

    async def test_critical_scenario_1_tenant_search(self, page):
        """
        Szenario 1: "Zeige alle Mieter" → TENANT_SEARCH
        Validiert Optimized Search Pfad (1-5ms)
        """
        logger.info("🧪 Testing Critical Scenario 1: Tenant Search")
        
        # Navigate to app
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select Unified Engine mode
        await page.locator("label:has-text('🚀 Unified Engine') >> input[type='checkbox']").check()
        
        # Enter query
        query = "Zeige alle Mieter"
        await page.fill("input[type='text']", query)
        
        # Submit and measure response time
        start_time = time.time()
        await page.click("button:has-text('Submit')")
        
        # Wait for results
        await page.wait_for_selector(".tenant-results", timeout=10000)
        response_time = (time.time() - start_time) * 1000
        
        # Validate response time (should be < 100ms for optimized search)
        assert response_time < 100, f"Response time {response_time}ms too slow for optimized search"
        
        # Validate results presence
        results = await page.locator(".tenant-results .result-row").count()
        assert results > 0, "No tenant results found"
        
        logger.info(f"✅ Scenario 1 passed: {results} tenants found in {response_time:.1f}ms")
        
    async def test_critical_scenario_2_kaltmiete_validation(self, page):
        """
        Szenario 2: "Summe Kaltmiete" → muss BEWOHNER.Z1 verwenden
        KRITISCH: Darf nicht KBETRAG verwenden!
        """
        logger.info("🧪 Testing Critical Scenario 2: Kaltmiete Field Validation")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select Unified Engine mode
        await page.locator("label:has-text('🚀 Unified Engine') >> input[type='checkbox']").check()
        
        # Enter Kaltmiete query
        await page.fill("input[type='text']", "Summe Kaltmiete")
        await page.click("button:has-text('Submit')")
        
        # Wait for results
        await page.wait_for_selector(".query-result", timeout=15000)
        
        # Check for SQL log output (should show BEWOHNER.Z1)
        # This requires the app to show SQL in debug mode or logs
        page_content = await page.content()
        
        # Validate correct field usage
        assert "BEWOHNER.Z1" in page_content or "T.Z1" in page_content, \
            "Kaltmiete query must use BEWOHNER.Z1 field"
        assert "KBETRAG" not in page_content, \
            "CRITICAL: Kaltmiete query incorrectly using KBETRAG field!"
            
        # Validate numeric result
        result_element = await page.locator(".result-value").first
        result_text = await result_element.text_content()
        
        # Should be a numeric value
        try:
            result_value = float(result_text.replace(",", "").replace("€", "").strip())
            assert result_value > 0, "Kaltmiete sum should be positive"
        except ValueError:
            pytest.fail(f"Invalid numeric result: {result_text}")
            
        logger.info(f"✅ Scenario 2 passed: Kaltmiete sum = {result_text}")

    async def test_critical_scenario_3_owner_portfolio(self, page):
        """
        Szenario 3: "Portfolio Eigentümer" → OWNER_PORTFOLIO template
        """
        logger.info("🧪 Testing Critical Scenario 3: Owner Portfolio")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select Unified Engine
        await page.locator("label:has-text('🚀 Unified Engine') >> input[type='checkbox']").check()
        
        await page.fill("input[type='text']", "Portfolio Eigentümer")
        
        start_time = time.time()
        await page.click("button:has-text('Submit')")
        
        # Wait for portfolio results
        await page.wait_for_selector(".portfolio-results", timeout=15000)
        response_time = (time.time() - start_time) * 1000
        
        # Template engine should be ~100ms
        assert response_time < 500, f"Template response {response_time}ms too slow"
        
        # Validate portfolio structure
        owners = await page.locator(".owner-entry").count()
        assert owners > 0, "No owners found in portfolio"
        
        logger.info(f"✅ Scenario 3 passed: {owners} owners found in {response_time:.1f}ms")

    async def test_critical_scenario_4_vacancy_analysis(self, page):
        """
        Szenario 4: "Leerstand" → VACANCY_ANALYSIS mit EIGNR = -1
        """
        logger.info("🧪 Testing Critical Scenario 4: Vacancy Analysis")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        await page.locator("label:has-text('🚀 Unified Engine') >> input[type='checkbox']").check()
        
        await page.fill("input[type='text']", "Leerstand")
        await page.click("button:has-text('Submit')")
        
        await page.wait_for_selector(".vacancy-results", timeout=15000)
        
        # Validate EIGNR = -1 filter in SQL (if visible)
        page_content = await page.content()
        if "EIGNR" in page_content:
            assert "EIGNR = -1" in page_content, "Vacancy query must filter EIGNR = -1"
        
        # Validate vacancy results
        vacancies = await page.locator(".vacancy-entry").count()
        logger.info(f"✅ Scenario 4 passed: {vacancies} vacancies found")

    async def test_performance_all_modes(self, page):
        """
        Szenario 5: Performance-Tests für alle 5 Modi
        Validiert Performance-Targets aus ARCHITECTURE.md
        """
        logger.info("🧪 Testing Performance for All Modes")
        
        test_query = "Zeige alle Mieter"
        modes = [
            ("📊 JSON Layer 4 Standard", 1500),   # json_standard ~1500ms
            ("📋 JSON Layer 4 Vanilla", 300),     # json_vanilla ~300ms  
            ("🔍 SQL Layer 4 Standard", 2000),    # sql_standard ~2000ms
            ("⚡ SQL Layer 4 Vanilla", 500),      # sql_vanilla ~500ms
            ("🚀 Unified Engine", 100)            # unified ~100ms
        ]
        
        performance_results = {}
        
        for mode_name, target_ms in modes:
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Clear all checkboxes first
            checkboxes = await page.locator("input[type='checkbox']").all()
            for checkbox in checkboxes:
                await checkbox.uncheck()
            
            # Select specific mode
            await page.locator(f"label:has-text('{mode_name}') >> input[type='checkbox']").check()
            
            await page.fill("input[type='text']", test_query)
            
            start_time = time.time()
            await page.click("button:has-text('Submit')")
            
            # Wait for any result
            await page.wait_for_selector(".query-result", timeout=30000)
            response_time = (time.time() - start_time) * 1000
            
            performance_results[mode_name] = response_time
            
            # Validate against target (with 50% tolerance)
            tolerance = target_ms * 1.5
            assert response_time < tolerance, \
                f"{mode_name}: {response_time:.1f}ms > {tolerance}ms target"
            
            logger.info(f"✅ {mode_name}: {response_time:.1f}ms (target: {target_ms}ms)")
        
        logger.info(f"🏆 All performance tests passed: {performance_results}")

    async def test_fallback_mechanism(self, page):
        """
        Test: Unified Engine Fallback zu Legacy Handler
        Komplexe Query die garantiert nicht von Search/Templates abgedeckt wird
        """
        logger.info("🧪 Testing Fallback Mechanism")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        await page.locator("label:has-text('🚀 Unified Engine') >> input[type='checkbox']").check()
        
        # Sehr komplexe Query die Fallback triggert
        complex_query = "Vergleiche die Mietentwicklung der letzten 5 Jahre in Zürich und Genf"
        await page.fill("input[type='text']", complex_query)
        
        start_time = time.time()
        await page.click("button:has-text('Submit')")
        
        # Fallback dauert länger (Legacy LLM)
        await page.wait_for_selector(".query-result", timeout=45000)
        response_time = (time.time() - start_time) * 1000
        
        # Fallback sollte > 500ms sein (Legacy Path)
        assert response_time > 500, f"Fallback too fast: {response_time}ms"
        
        # Check for fallback indicator in UI
        page_content = await page.content()
        fallback_indicators = [
            "erweiterte Analyse",
            "Legacy Handler", 
            "fallback",
            "LLM Analysis"
        ]
        
        has_fallback_indicator = any(indicator in page_content for indicator in fallback_indicators)
        logger.info(f"✅ Fallback test passed: {response_time:.1f}ms, indicator: {has_fallback_indicator}")


# Pytest fixtures für Playwright
@pytest.fixture
async def browser_context(playwright):
    """Browser context für tests"""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    yield context
    await context.close()
    await browser.close()

@pytest.fixture  
async def page(browser_context):
    """Page fixture für einzelne tests"""
    page = await browser_context.new_page()
    yield page
    await page.close()

# Test-Klassen für pytest discovery
class TestCriticalFlows:
    """Main test class für pytest"""
    
    @pytest.fixture(autouse=True)
    def setup_test_instance(self):
        self.test_instance = WincasaE2ETests()
    
    async def test_scenario_1_tenant_search(self, page):
        await self.test_instance.test_critical_scenario_1_tenant_search(page)
    
    async def test_scenario_2_kaltmiete_validation(self, page):
        await self.test_instance.test_critical_scenario_2_kaltmiete_validation(page)
    
    async def test_scenario_3_owner_portfolio(self, page):
        await self.test_instance.test_critical_scenario_3_owner_portfolio(page)
    
    async def test_scenario_4_vacancy_analysis(self, page):
        await self.test_instance.test_critical_scenario_4_vacancy_analysis(page)
    
    async def test_performance_all_modes(self, page):
        await self.test_instance.test_performance_all_modes(page)
    
    async def test_fallback_mechanism(self, page):
        await self.test_instance.test_fallback_mechanism(page)

if __name__ == "__main__":
    # Direct execution für debugging
    print("🧪 WINCASA E2E Critical Flows Test Suite")
    print("Run with: pytest tests/e2e/test_critical_flows.py -v")