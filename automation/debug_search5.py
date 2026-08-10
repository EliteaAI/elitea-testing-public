"""Check all text on page after search."""

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
    
    # Get the entire page text and look for relevant messages
    body = page.locator("body")
    body_text = body.text_content()
    
    # Print relevant lines
    for line in body_text.split('\n'):
        if 'nothing' in line.lower() or 'agent' in line.lower() or 'found' in line.lower():
            if len(line.strip()) > 5:  # Skip empty lines
                print(f"  '{line.strip()}'")
    
    browser.close()
