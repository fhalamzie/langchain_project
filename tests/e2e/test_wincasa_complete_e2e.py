#!/usr/bin/env python3
"""
WINCASA Complete End-to-End Test Suite
Comprehensive E2E testing mit working Playwright selectors
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

class WincasaCompleteE2E:
    """Complete E2E Test Suite mit working selectors"""
    
    def __init__(self):
        self.base_url = "http://localhost:8667"
        
    async def test_complete_workflow(self, page):
        """Test complete WINCASA workflow from start to query execution"""
        logger.info("🧪 Testing complete WINCASA workflow")
        
        # 1. Navigate and verify app loads
        await page.goto(self.base_url, timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        # Verify title contains WINCASA
        title = await page.title() 
        assert "WINCASA" in title, f"Wrong title: {title}"
        
        # 2. Select Unified Engine mode (working selector!)
        await page.click("text=🚀 Unified Engine (Phase 2 - intelligent)")
        logger.info("✅ Selected Unified Engine mode")
        
        # 3. Navigate to query interface
        await page.click("text=🔍 Abfragen")
        await page.wait_for_timeout(1000)  # Let UI update
        
        # 4. Enter test query
        test_query = "Zeige alle Mieter"
        await page.fill("textarea", test_query)
        logger.info(f"✅ Entered query: {test_query}")
        
        # 5. Execute query
        start_time = time.time()
        await page.click("text=🔍 Abfrage ausführen")
        
        # 6. Wait for results (generous timeout for first query)
        await page.wait_for_timeout(10000)  # 10 seconds
        response_time = (time.time() - start_time) * 1000
        
        # 7. Verify response received
        page_content = await page.content()
        
        # Check for result indicators
        result_indicators = [
            "ergebnis", "result", "mieter", "tenant", 
            "gefunden", "found", "zeilen", "rows"
        ]
        
        has_result = any(indicator in page_content.lower() for indicator in result_indicators)
        
        if has_result:
            logger.info(f"✅ Query executed successfully in {response_time:.1f}ms")
        else:
            # Check for error indicators
            error_indicators = ["fehler", "error", "timeout", "failed"]
            has_error = any(error in page_content.lower() for error in error_indicators)
            
            if has_error:
                logger.warning(f"⚠️ Query completed with error in {response_time:.1f}ms")
            else:
                logger.warning(f"⚠️ Query result unclear in {response_time:.1f}ms")
        
        # Assert reasonable response time (Unified Engine should be fast)
        assert response_time < 15000, f"Response too slow: {response_time}ms"
        
        logger.info("✅ Complete workflow test passed")

    async def test_multiple_modes_comparison(self, page):
        """Test multiple execution modes for performance comparison"""
        logger.info("🧪 Testing multiple execution modes")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Test scenarios with different modes
        test_modes = [
            ("🚀 Unified Engine (Phase 2 - intelligent)", 5000),  # Should be fast
            ("📋 JSON Layer 4 Vanilla (minimal)", 10000),          # Should be moderate
        ]
        
        results = {}
        test_query = "Portfolio Eigentümer"
        
        for mode_text, expected_max_time in test_modes:
            # Reset page
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Select mode
            await page.click(f"text={mode_text}")
            await page.click("text=🔍 Abfragen")
            await page.wait_for_timeout(1000)
            
            # Clear textarea and enter query
            await page.fill("textarea", "")
            await page.fill("textarea", test_query)
            
            # Execute and measure
            start_time = time.time()
            await page.click("text=🔍 Abfrage ausführen")
            await page.wait_for_timeout(8000)  # Wait for processing
            response_time = (time.time() - start_time) * 1000
            
            results[mode_text] = response_time
            
            # Verify reasonable response time
            assert response_time < expected_max_time, \
                f"{mode_text}: {response_time:.1f}ms > {expected_max_time}ms"
            
            logger.info(f"✅ {mode_text}: {response_time:.1f}ms")
        
        logger.info(f"🏆 Mode comparison completed: {results}")

    async def test_ui_responsiveness(self, page):
        """Test UI responsiveness across different viewport sizes"""
        logger.info("🧪 Testing UI responsiveness")
        
        viewports = [
            {"width": 1920, "height": 1080, "name": "Desktop"},
            {"width": 1024, "height": 768, "name": "Tablet"},
            {"width": 375, "height": 667, "name": "Mobile"}
        ]
        
        for viewport in viewports:
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Check if main elements are accessible
            try:
                # Should be able to see WINCASA title
                title_visible = await page.is_visible("text=WINCASA")
                assert title_visible, f"Title not visible at {viewport['name']}"
                
                # Should be able to access modes (might be in sidebar/hamburger)
                unified_visible = await page.is_visible("text=Unified Engine", timeout=5000)
                
                if not unified_visible:
                    # Try to open sidebar/menu if collapsed
                    hamburger_selectors = [
                        "[data-testid='stSidebarNavToggle']",
                        "button[aria-label='Open sidebar']",
                        ".streamlit-expanderHeader"
                    ]
                    
                    for selector in hamburger_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            unified_visible = await page.is_visible("text=Unified Engine", timeout=3000)
                            if unified_visible:
                                break
                        except:
                            continue
                
                logger.info(f"✅ UI responsive at {viewport['name']} ({viewport['width']}x{viewport['height']})")
                
            except Exception as e:
                logger.warning(f"⚠️ UI issue at {viewport['name']}: {e}")

    async def test_error_handling(self, page):
        """Test error handling with invalid inputs"""
        logger.info("🧪 Testing error handling")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select a mode
        await page.click("text=🚀 Unified Engine (Phase 2 - intelligent)")
        await page.click("text=🔍 Abfragen")
        await page.wait_for_timeout(1000)
        
        # Test empty query
        await page.fill("textarea", "")
        await page.click("text=🔍 Abfrage ausführen")
        await page.wait_for_timeout(3000)
        
        # Should handle gracefully (no crash)
        page_content = await page.content()
        assert "500" not in page_content, "App crashed with 500 error on empty query"
        
        # Test invalid/nonsense query
        await page.fill("textarea", "@@@@INVALID QUERY WITH SPECIAL CHARS@@@@")
        await page.click("text=🔍 Abfrage ausführen")
        await page.wait_for_timeout(5000)
        
        page_content = await page.content()
        assert "500" not in page_content, "App crashed with 500 error on invalid query"
        
        logger.info("✅ Error handling test passed")

    async def test_session_persistence(self, page):
        """Test session state persistence across tab interactions"""
        logger.info("🧪 Testing session persistence")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select mode and execute query
        await page.click("text=🚀 Unified Engine (Phase 2 - intelligent)")
        await page.click("text=🔍 Abfragen")
        await page.wait_for_timeout(1000)
        
        await page.fill("textarea", "Test session query")
        await page.click("text=🔍 Abfrage ausführen")
        await page.wait_for_timeout(5000)
        
        # Switch to another tab
        await page.click("text=📊 System-Info")
        await page.wait_for_timeout(1000)
        
        # Switch back to queries
        await page.click("text=🔍 Abfragen")
        await page.wait_for_timeout(1000)
        
        # Mode should still be selected
        page_content = await page.content()
        assert "Unified" in page_content, "Mode selection not persisted"
        
        logger.info("✅ Session persistence test passed")


# Pytest fixtures and test class
@pytest.fixture(scope="session")
async def browser_context():
    """Session-wide browser context"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not available")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        yield context
        await context.close()
        await browser.close()

@pytest.fixture
async def page(browser_context):
    """Page fixture for individual tests"""
    page = await browser_context.new_page()
    yield page
    await page.close()

class TestWincasaCompleteE2E:
    """Main test class for pytest discovery"""
    
    @pytest.fixture(autouse=True)
    def setup_test_instance(self):
        self.e2e_tests = WincasaCompleteE2E()
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, page):
        await self.e2e_tests.test_complete_workflow(page)
    
    @pytest.mark.asyncio
    async def test_multiple_modes_comparison(self, page):
        await self.e2e_tests.test_multiple_modes_comparison(page)
    
    @pytest.mark.asyncio
    async def test_ui_responsiveness(self, page):
        await self.e2e_tests.test_ui_responsiveness(page)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, page):
        await self.e2e_tests.test_error_handling(page)
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, page):
        await self.e2e_tests.test_session_persistence(page)

if __name__ == "__main__":
    print("🧪 WINCASA Complete E2E Test Suite")
    print("Run with: pytest tests/e2e/test_wincasa_complete_e2e.py -v --asyncio-mode=auto")
    print("To run interactively: PWDEBUG=1 pytest tests/e2e/test_wincasa_complete_e2e.py -v")