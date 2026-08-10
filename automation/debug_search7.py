"""Check if search is actually filtering."""

from pages.agents_list_page import AgentsListPage
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    agents = AgentsListPage(page)
    agents.navigate()
    agents.wait_for_page_load()
    
    before_count = len(agents.get_agent_card_names())
    print(f"Before search: {before_count} agent cards visible")
    
    # Try using press_sequentially instead of fill (MUI pattern)
    agents.search_input.click()
    agents.search_input.clear()
    agents.search_input.press_sequentially("DEFINITELYNONEXISTENTTERM", delay=50)
    page.wait_for_timeout(3000)
    
    after_count = len(agents.get_agent_card_names())
    print(f"After search (press_sequentially): {after_count} agent cards visible")
    
    search_val = agents.search_input.input_value()
    print(f"Search input value: '{search_val}'")
    
    browser.close()
