"""Debug search and check for empty state message."""

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
    page.wait_for_timeout(2000)
    
    # Take screenshot
    page.screenshot(path="debug_search2.png")
    
    # Check if "Nothing found" text exists anywhere
    try:
        text_elem = page.locator("text=/No agents found|Nothing found/").first
        print(f"Found empty-state text")
        print(f"Text: {text_elem.text_content()}")
    except Exception as e:
        print(f"No empty-state text found: {e}")
    
    # Check all text on the page
    body_text = page.locator("body").text_content()
    if "Nothing found" in body_text:
        print("'Nothing found' is somewhere on page")
    if "No agents found" in body_text:
        print("'No agents found' is somewhere on page")
    if "agents" in body_text.lower():
        print("'agents' word found on page")
    
    # Check what's currently showing in the card grid
    cards = page.locator("[data-testid='entity-card-name']")
    print(f"Card count: {cards.count()}")
    
    browser.close()
