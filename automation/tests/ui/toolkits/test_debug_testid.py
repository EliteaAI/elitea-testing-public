"""Debug test for Test #7 - pause at missing testid to inspect UI manually."""

import pytest
from pages.toolkit_creation_page import ToolkitCreationPage
from pages.base_page import BasePage

# Timeouts
UI_ELEMENT_TIMEOUT = 20_000
NAVIGATION_TIMEOUT = 15_000

@pytest.mark.ui
@pytest.mark.p1
def test_debug_missing_testid(page, auth_state):
    """Debug Test #7 - pause at Step 13 where testid is missing."""

    print("\n" + "="*80)
    print("DEBUG TEST - Will pause at missing testid for manual inspection")
    print("="*80)

    # Navigate to toolkit creation
    print("\nStep 1: Navigating to toolkits page...")
    page.goto("/toolkits/all", wait_until="networkidle", timeout=NAVIGATION_TIMEOUT)
    page.wait_for_timeout(2000)

    # Click create toolkit button
    print("Step 2: Clicking 'Create Toolkit' button...")
    create_button = page.get_by_test_id("toolkit-list-create-button")
    create_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
    create_button.click()
    page.wait_for_timeout(2000)

    # Click on Artifact card
    print("Step 3: Looking for Artifact toolkit card...")
    artifact_card = page.locator('[data-testid*="artifact"], [data-testid*="Artifact"]').first
    if artifact_card.count() == 0:
        # Try alternative - look for text
        artifact_card = page.locator('text="Artifact"').first

    print(f"Found {artifact_card.count()} artifact cards")
    artifact_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
    artifact_card.click()

    print("Step 4: Waiting for form to load...")
    page.wait_for_timeout(15000)  # User said form takes ~10s

    # Check if TOOLS section needs expanding
    print("Step 5: Checking if TOOLS section is collapsed...")
    tools_accordion = page.get_by_test_id("toolkit-tools-accordion-summary")
    if tools_accordion.count() > 0:
        expanded = tools_accordion.get_attribute("aria-expanded")
        print(f"TOOLS accordion found, aria-expanded={expanded}")

        if expanded == "false":
            print("Expanding TOOLS section...")
            tools_accordion.click()
            page.wait_for_timeout(1000)

    # Now we're at Step 13 - where the missing testid should be
    print("\n" + "="*80)
    print("STEP 13 - Looking for missing testid...")
    print("="*80)
    print("\nSearching for: [data-testid='toolkit-field-available_by_mcp-checkbox-field']")

    # Try to find it
    mcp_checkbox = page.locator('[data-testid="toolkit-field-available_by_mcp-checkbox-field"]')
    count = mcp_checkbox.count()

    print(f"\nResult: Found {count} elements with that testid")

    if count == 0:
        print("\n⚠️  TESTID NOT FOUND")
        print("\nLet's search for alternative patterns...")

        # Search for any MCP-related testids
        print("\n1. Searching for testids containing 'mcp':")
        mcp_testids = page.locator('[data-testid*="mcp"]')
        print(f"   Found {mcp_testids.count()} elements")
        for i in range(min(5, mcp_testids.count())):
            testid = mcp_testids.nth(i).get_attribute("data-testid")
            print(f"   - {testid}")

        # Search for any available-related testids
        print("\n2. Searching for testids containing 'available':")
        avail_testids = page.locator('[data-testid*="available"]')
        print(f"   Found {avail_testids.count()} elements")
        for i in range(min(5, avail_testids.count())):
            testid = avail_testids.nth(i).get_attribute("data-testid")
            print(f"   - {testid}")

        # Search for text "MCP"
        print("\n3. Searching for text containing 'MCP':")
        mcp_text = page.locator('text=/MCP/i')
        print(f"   Found {mcp_text.count()} elements")
        for i in range(min(5, mcp_text.count())):
            text = mcp_text.nth(i).text_content()
            testid = mcp_text.nth(i).get_attribute("data-testid")
            print(f"   - Text: '{text[:50]}...' | testid: {testid}")

        # Search for checkboxes in TOOLS section
        print("\n4. Searching for checkbox/switch elements in TOOLS section:")
        tools_section = page.locator('[data-testid*="tools"]').first
        if tools_section.count() > 0:
            checkboxes = tools_section.locator('input[type="checkbox"], [role="switch"]')
            print(f"   Found {checkboxes.count()} checkbox/switch elements")

        print("\n" + "="*80)
        print("PAUSING FOR MANUAL INSPECTION")
        print("="*80)
        print("\nThe browser window should be visible.")
        print("Please inspect the UI to find the correct element for MCP availability.")
        print("\nPress Enter in this terminal when you're done inspecting...")
        print("="*80)

        # PAUSE HERE - wait for user input
        input()

        print("\nResuming test...")

    else:
        print(f"\n✅ TESTID FOUND - {count} element(s)")
        print("Checking if it's a checkbox...")
        is_checkbox = mcp_checkbox.first.get_attribute("type") == "checkbox"
        role = mcp_checkbox.first.get_attribute("role")
        print(f"   Type: {mcp_checkbox.first.get_attribute('type')}")
        print(f"   Role: {role}")

    print("\nTest complete.")
