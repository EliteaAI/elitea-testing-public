"""Check if cards are actually hidden vs just existing in DOM."""

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
    agents.search_input.click()
    agents.search_input.clear()
    agents.search_input.press_sequentially("DEFINITELYNONEXISTENTTERM", delay=50)
    page.wait_for_timeout(3000)
    
    # Check if cards are visible or hidden
    cards = page.locator("[data-testid='entity-card']")
    total = cards.count()
    print(f"Total cards in DOM: {total}")
    
    visible = 0
    for i in range(min(5, total)):
        is_vis = cards.nth(i).is_visible()
        visible += 1 if is_vis else 0
        name = cards.nth(i).locator("[data-testid='entity-card-name']").text_content()
        print(f"  Card {i} ({name[:20]}: visible={is_vis}")
    
    print(f"First 5 cards visible: {visible}/5")
    
    browser.close()
