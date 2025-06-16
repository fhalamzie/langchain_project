
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('UIButtonTest_2025-06-15', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://0.0.0.0:8667');

    // Take screenshot
    await page.screenshot({ path: 'ui_initial_state.png', { fullPage: true } });

    // Click element
    await page.click('text="📊 JSON Layer 4 Standard (detailliert)"');

    // Click element
    await page.click('text="👥 Alle Eigentümer anzeigen"');

    // Click element
    await page.click('text="💰 Mieteinnahmen 2024"');

    // Click element
    await page.click('text="🏦 Rücklagen-Status"');

    // Click element
    await page.click('text="🔍 JSON Layer 4 Vanilla (rein)"');

    // Take screenshot
    await page.screenshot({ path: 'ui_after_button_clicks.png', { fullPage: true } });

    // Click element
    await page.click('text="💰 Mieteinnahmen 2024"');

    // Take screenshot
    await page.screenshot({ path: 'rental_income_results.png', { fullPage: true } });

    // Click element
    await page.click('text="🏦 Rücklagen-Status"');

    // Click element
    await page.click('text="📋 JSON Layer 4 Vanilla (minimal)"');

    // Click element
    await page.click('text="👥 Alle Eigentümer anzeigen"');

    // Take screenshot
    await page.screenshot({ path: 'final_test_state.png', { fullPage: true } });
});