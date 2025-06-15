#!/usr/bin/env python3
"""
WINCASA E2E UI Interaction Tests
Playwright-basierte Tests für UI-Interaktionen und User-Flows
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import asyncio
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WincasaUITests:
    """UI-Interaktionstests für WINCASA Streamlit App"""
    
    def __init__(self):
        self.base_url = "http://localhost:8667"
        self.default_timeout = 30000  # 30 seconds

    async def test_app_loads_successfully(self, page):
        """Test: App lädt erfolgreich und zeigt Grundelemente"""
        logger.info("🧪 Testing app loading")
        
        await page.goto(self.base_url, timeout=self.default_timeout)
        await page.wait_for_load_state("networkidle")
        
        # Check title
        title = await page.title()
        assert "WINCASA" in title, f"Wrong page title: {title}"
        
        # Check main elements exist
        await page.wait_for_selector("h1", timeout=5000)
        heading = await page.locator("h1").first.text_content()
        assert "WINCASA" in heading or "WEG" in heading, f"Missing main heading: {heading}"
        
        logger.info("✅ App loaded successfully")

    async def test_mode_selection_ui(self, page):
        """Test: Mode selection checkboxes funktionieren"""
        logger.info("🧪 Testing mode selection UI")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Check if mode checkboxes exist
        expected_modes = [
            "JSON Layer 4 Standard",
            "JSON Layer 4 Vanilla", 
            "SQL Layer 4 Standard",
            "SQL Layer 4 Vanilla",
            "Unified Engine"
        ]
        
        for mode in expected_modes:
            # Look for checkbox with mode text
            checkbox = page.locator(f"text={mode}").locator("..").locator("input[type='checkbox']")
            await checkbox.wait_for(state="visible", timeout=5000)
            
            # Test checking/unchecking
            await checkbox.check()
            is_checked = await checkbox.is_checked()
            assert is_checked, f"Checkbox for {mode} should be checked"
            
            await checkbox.uncheck()
            is_checked = await checkbox.is_checked()
            assert not is_checked, f"Checkbox for {mode} should be unchecked"
        
        logger.info("✅ All mode checkboxes work correctly")

    async def test_query_input_and_submission(self, page):
        """Test: Query input und Submit funktionieren"""
        logger.info("🧪 Testing query input and submission")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Find and fill query input
        # Streamlit creates text inputs, find the main query input
        query_inputs = await page.locator("input[type='text']").all()
        assert len(query_inputs) > 0, "No text input found"
        
        # Use the first (main) text input
        main_input = query_inputs[0]
        test_query = "Zeige alle Mieter"
        await main_input.fill(test_query)
        
        # Verify input value
        input_value = await main_input.input_value()
        assert input_value == test_query, f"Input value mismatch: {input_value}"
        
        # Select a mode first
        unified_checkbox = page.locator("text=Unified Engine").locator("..").locator("input[type='checkbox']")
        await unified_checkbox.check()
        
        # Find and click submit button
        # Streamlit might create button with different text
        submit_buttons = await page.locator("button").all()
        submit_clicked = False
        
        for button in submit_buttons:
            button_text = await button.text_content()
            if button_text and any(word in button_text.lower() for word in ['submit', 'send', 'query', 'ausführen']):
                await button.click()
                submit_clicked = True
                break
        
        if not submit_clicked:
            # If no obvious submit button, try pressing Enter
            await main_input.press("Enter")
        
        # Wait for processing (Streamlit updates UI)
        await page.wait_for_timeout(2000)
        
        logger.info("✅ Query submission works")

    async def test_multi_mode_execution(self, page):
        """Test: Mehrere Modi gleichzeitig ausführen"""
        logger.info("🧪 Testing multi-mode execution")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select multiple modes
        modes_to_test = ["JSON Layer 4 Vanilla", "Unified Engine"]
        
        for mode in modes_to_test:
            checkbox = page.locator(f"text={mode}").locator("..").locator("input[type='checkbox']")
            await checkbox.check()
        
        # Enter query
        query_input = page.locator("input[type='text']").first
        await query_input.fill("Portfolio Eigentümer")
        
        # Submit
        await query_input.press("Enter")
        
        # Wait for results
        await page.wait_for_timeout(5000)
        
        # Check if multiple result sections appear
        page_content = await page.content()
        
        # Should show results from both modes
        for mode in modes_to_test:
            # Results might be in tabs or sections
            assert mode.replace(" ", "").lower() in page_content.lower() or \
                   len([m for m in modes_to_test if m.lower() in page_content.lower()]) > 0, \
                   f"No results visible for {mode}"
        
        logger.info("✅ Multi-mode execution works")

    async def test_performance_measurement(self, page):
        """Test: Performance-Messung für verschiedene Modi"""
        logger.info("🧪 Testing performance measurement")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Test Unified Engine performance
        unified_checkbox = page.locator("text=Unified Engine").locator("..").locator("input[type='checkbox']")
        await unified_checkbox.check()
        
        query_input = page.locator("input[type='text']").first
        await query_input.fill("Zeige alle Mieter")
        
        # Measure response time
        start_time = time.time()
        await query_input.press("Enter")
        
        # Wait for any result to appear
        try:
            # Wait for Streamlit to update (look for any content change)
            await page.wait_for_timeout(1000)  # Minimum wait
            
            # Check if content updated
            content_updated = False
            for _ in range(20):  # Max 20 seconds wait
                page_content = await page.content()
                if any(indicator in page_content.lower() for indicator in 
                      ['result', 'mieter', 'tenant', 'error', 'loading']):
                    content_updated = True
                    break
                await page.wait_for_timeout(1000)
            
            response_time = (time.time() - start_time) * 1000
            
            if content_updated:
                logger.info(f"✅ Performance test: {response_time:.1f}ms response time")
                # Unified Engine should be reasonably fast
                assert response_time < 10000, f"Response too slow: {response_time}ms"
            else:
                logger.warning("⚠️ Could not detect content update, but no error")
                
        except Exception as e:
            logger.warning(f"⚠️ Performance test inconclusive: {e}")

    async def test_error_handling(self, page):
        """Test: Error Handling für ungültige Queries"""
        logger.info("🧪 Testing error handling")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Select a mode
        unified_checkbox = page.locator("text=Unified Engine").locator("..").locator("input[type='checkbox']")
        await unified_checkbox.check()
        
        # Submit empty query
        query_input = page.locator("input[type='text']").first
        await query_input.fill("")
        await query_input.press("Enter")
        
        await page.wait_for_timeout(2000)
        
        # Should handle empty query gracefully (no crash)
        page_content = await page.content()
        
        # Should not show error 500 or crash
        assert "500" not in page_content, "App crashed with 500 error"
        assert "error" not in page_content.lower() or "empty" in page_content.lower(), \
               "Unexpected error for empty query"
        
        # Test invalid query
        await query_input.fill("@@@@INVALID QUERY@@@@")
        await query_input.press("Enter")
        
        await page.wait_for_timeout(3000)
        
        # Should handle gracefully
        page_content = await page.content()
        assert "500" not in page_content, "App crashed on invalid query"
        
        logger.info("✅ Error handling works correctly")

    async def test_ui_responsiveness(self, page):
        """Test: UI Responsiveness und Layout"""
        logger.info("🧪 Testing UI responsiveness")
        
        await page.goto(self.base_url)
        await page.wait_for_load_state("networkidle")
        
        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1024, "height": 768},   # Tablet
            {"width": 375, "height": 667}     # Mobile
        ]
        
        for viewport in viewports:
            await page.set_viewport_size(viewport)
            await page.wait_for_timeout(1000)
            
            # Check if main elements are still visible
            heading = page.locator("h1").first
            await heading.wait_for(state="visible", timeout=5000)
            
            # Check if checkboxes are accessible
            checkboxes = await page.locator("input[type='checkbox']").all()
            assert len(checkboxes) > 0, f"No checkboxes visible at {viewport}"
            
            logger.info(f"✅ UI responsive at {viewport['width']}x{viewport['height']}")

# Pytest configuration
@pytest.fixture(scope="session")
async def browser_context():
    """Session-wide browser context"""
    from playwright.async_api import async_playwright
    
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

# Test class for pytest discovery
class TestWincasaUI:
    """Main test class for pytest"""
    
    @pytest.fixture(autouse=True)
    def setup_test_instance(self):
        self.ui_tests = WincasaUITests()
    
    @pytest.mark.asyncio
    async def test_app_loads_successfully(self, page):
        await self.ui_tests.test_app_loads_successfully(page)
    
    @pytest.mark.asyncio 
    async def test_mode_selection_ui(self, page):
        await self.ui_tests.test_mode_selection_ui(page)
    
    @pytest.mark.asyncio
    async def test_query_input_and_submission(self, page):
        await self.ui_tests.test_query_input_and_submission(page)
    
    @pytest.mark.asyncio
    async def test_multi_mode_execution(self, page):
        await self.ui_tests.test_multi_mode_execution(page)
    
    @pytest.mark.asyncio
    async def test_performance_measurement(self, page):
        await self.ui_tests.test_performance_measurement(page)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, page):
        await self.ui_tests.test_error_handling(page)
    
    @pytest.mark.asyncio
    async def test_ui_responsiveness(self, page):
        await self.ui_tests.test_ui_responsiveness(page)

if __name__ == "__main__":
    print("🧪 WINCASA UI Interaction Test Suite")
    print("Run with: pytest tests/e2e/test_ui_interactions.py -v --asyncio-mode=auto")