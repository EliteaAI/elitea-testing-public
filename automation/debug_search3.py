"""Debug search and check for empty state message - better version."""

from pages.agents_list_page import AgentsListPage
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    agents = AgentsListPage(page)
    agents.navigate()
    agents.wait_for_page_load()
    
    # Search for non-existent term
    agents.search_input.fill("DEFINITELYNONEXISTENTTERM")
    page.wait_for_timeout(3000)  # Longer wait for debounce
    
    # Check search value
    search_val = agents.search_input.input_value()
    print(f"Search value: '{search_val}'")
    
    # Check page content for "Nothing found"
    print("Checking page for 'Nothing found' text...")
    if page.locator("text=Nothing found").count() > 0:
        print("  ✓ Found 'Nothing found' via text locator")
    else:
        print("  ✗ 'Nothing found' not found via text locator")
    
    # Check page content for "No agents"
    print("Checking page for 'No agents' text...")
    if page.locator("text=No agents").count() > 0:
        print("  ✓ Found 'No agents' via text locator")
    else:
        print("  ✗ 'No agents' not found via text locator")
    
    # Check what cards are visible
    visible_cards = 0
    cards = page.locator("[data-testid='entity-card']")
    for i in range(min(3, cards.count())):
        is_vis = cards.nth(i).is_visible()
        if is_vis:
            visible_cards += 1
            print(f"Card {i}: visible")
        else:
            print(f"Card {i}: hidden")
    
    print(f"Total card count: {cards.count()}")
    print(f"Visible cards: {visible_cards}")
    
    # Get screenshot
    page.screenshot(path="debug_search3.png")
    print("Screenshot saved to debug_search3.png")
    
    browser.close()
