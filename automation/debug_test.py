"""Quick debug of search filtering."""

from pages.agents_list_page import AgentsListPage
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    agents = AgentsListPage(page)
    agents.navigate()
    agents.wait_for_page_load()
    
    before = agents.get_agent_card_names()
    print(f"Before search: {len(before)} agents")
    
    # Fill search input
    agents.search_input.fill("DEFINITELYNONEXISTENTTERM")
    page.wait_for_timeout(2000)  # Wait for debounce
    
    # Check input value
    val = agents.search_input.input_value()
    print(f"Search input value: '{val}'")
    
    # Get agent cards after search
    after = agents.get_agent_card_names()
    print(f"After search: {len(after)} agents")
    
    # Take a screenshot
    page.screenshot(path="debug_search.png")
    
    browser.close()
