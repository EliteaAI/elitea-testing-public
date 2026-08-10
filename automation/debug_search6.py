"""Check card grid area specifically."""

from pages.agents_list_page import AgentsListPage
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    agents = AgentsListPage(page)
    agents.navigate()
    agents.wait_for_page_load()
    
    # Search
    agents.search_input.fill("DEFINITELYNONEXISTENTTERM")
    page.wait_for_timeout(3000)
    
    # Check main content area  
    # Try to find the agents grid container
    main = page.locator("main").first
    main_text = main.text_content() if main.count() > 0 else "No main found"
    print(f"Main area text snippet (first 500 chars):")
    print(main_text[:500] if isinstance(main_text, str) else main_text)
    
    # Check if main shows any empty state-like text
    if main.count() > 0:
        main_html = main.inner_html()
        if "nothing" in main_html.lower():
            print("\n✓ 'nothing' found in main HTML")
        if "no agent" in main_html.lower():
            print("✓ 'no agent' found in main HTML")
        else:
            print("\n✗ No empty-state message in main area")
    
    browser.close()
