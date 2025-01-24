#!/usr/bin/env python3
"""Test ekko Streamlit application with Playwright"""

import asyncio
from playwright.async_api import async_playwright

async def test_ekko_app():
    """Test the ekko Streamlit application"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Go to the landing page
        print("🚀 Navigating to landing page...")
        await page.goto('http://localhost:8501')
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot of landing page
        await page.screenshot(path='test_landing.png')
        print("📸 Landing page screenshot saved")
        
        # Check if landing page loaded
        title = await page.title()
        print(f"✅ Page title: {title}")
        
        # Look for the 'Get Started' button or link to navigate to main app
        # Streamlit pages appear in sidebar
        print("🔍 Looking for navigation to main app...")
        
        # Try to find and click on the app page in sidebar
        # In Streamlit multi-page apps, pages are usually in the sidebar
        await page.wait_for_timeout(2000)  # Wait for page to fully load
        
        # Check for sidebar toggle if collapsed
        sidebar_toggle = page.locator('[data-testid="collapsedControl"]')
        if await sidebar_toggle.count() > 0:
            print("📱 Opening sidebar...")
            await sidebar_toggle.click()
            await page.wait_for_timeout(1000)
        
        # Look for the app page link
        app_link = page.locator('a:has-text("app")')
        if await app_link.count() > 0:
            print("🔗 Found app page link, clicking...")
            await app_link.click()
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            # Take screenshot of main app
            await page.screenshot(path='test_app_main.png')
            print("📸 Main app screenshot saved")
            
            # Now search for "Lenny's Podcast"
            print("🔍 Searching for 'Lenny's Podcast'...")
            
            # Find search input - Streamlit text inputs have data-testid
            search_input = page.locator('input[type="text"]').first
            if await search_input.count() > 0:
                await search_input.fill("Lenny's Podcast")
                print("✅ Filled search query")
                
                # Find and click search button
                search_button = page.locator('button:has-text("Search")')
                if await search_button.count() > 0:
                    await search_button.click()
                    print("🔍 Search initiated...")
                    
                    # Wait for results
                    await page.wait_for_timeout(5000)
                    
                    # Take screenshot of search results
                    await page.screenshot(path='test_search_results.png')
                    print("📸 Search results screenshot saved")
                else:
                    print("❌ Could not find search button")
            else:
                print("❌ Could not find search input")
        else:
            print("❌ Could not find app page link in sidebar")
        
        # Get page content for debugging
        content = await page.content()
        with open('test_page_content.html', 'w') as f:
            f.write(content)
        print("📄 Page HTML saved for debugging")
        
        await browser.close()
        print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_ekko_app())