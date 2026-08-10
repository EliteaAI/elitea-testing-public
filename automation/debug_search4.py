"""Check exact text content of No agents message."""

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
    
    # Get the exact text
    no_agents = page.locator("text=No agents").first
    text = no_agents.text_content()
    print(f"Text content: '{text}'")
    print(f"Text repr: {repr(text)}")
    print(f"Contains 'No agents': {'No agents' in text if text else 'None'}")
    
    browser.close()
