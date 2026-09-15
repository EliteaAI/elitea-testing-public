#!/usr/bin/env python3
"""Manual agent creation - stops at login for manual authentication.

Usage:
    python manual_agent_create.py
"""

import sys
from pathlib import Path

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from config import settings

def main():
    """Create agent with manual login."""

    print("=" * 80)
    print("MANUAL AGENT CREATION SCRIPT")
    print("=" * 80)
    print(f"\nTarget: {settings.elitea_url}")
    print(f"Project: {settings.elitea_project_id}")
    print("\nThis script will:")
    print("  1. Open browser")
    print("  2. Navigate to Stage2")
    print("  3. PAUSE at login page - you manually log in")
    print("  4. After login, continue to create agent")
    print("\n" + "=" * 80)

    with sync_playwright() as p:
        # Launch browser in headed mode
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,  # Slow down actions for visibility
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )

        page = context.new_page()

        # Navigate to Stage2
        print(f"\n[1] Navigating to {settings.elitea_url}...")
        page.goto(settings.elitea_url, wait_until="domcontentloaded")

        # Check if we're on login page
        print("\n[2] Checking login status...")
        page.wait_for_timeout(2000)

        # Check for Keycloak login page
        if "auth" in page.url.lower() or "login" in page.url.lower():
            print("\n" + "=" * 80)
            print("⏸️  WAITING AT LOGIN PAGE")
            print("=" * 80)
            print("\n📋 INSTRUCTIONS:")
            print("  1. Manually log in with your Stage2 credentials in the browser")
            print("  2. Username: autotest_user_admin")
            print("  3. Password: <your password>")
            print("  4. Waiting 90 seconds for you to complete login...")
            print("\n" + "=" * 80)

            # Wait 90 seconds for manual login
            print("\n⏳ Waiting 90 seconds...")
            page.wait_for_timeout(90000)

            # Wait a bit more for redirect after login
            print("\n[3] Checking if login completed...")
            page.wait_for_timeout(3000)
        else:
            print("✅ Already logged in or redirected")

        print(f"\n[4] Current URL: {page.url}")

        # Navigate to create agent page
        print("\n[5] Navigating to create agent page...")
        create_url = f"{settings.elitea_url}{settings.app_prefix}/agents/all"
        page.goto(create_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Click create button
        print("\n[6] Looking for 'Create' button...")
        try:
            # Try to find and click Create button
            create_button = page.locator('button:has-text("Create")').first
            if create_button.is_visible():
                print("✅ Found 'Create' button, clicking...")
                create_button.click()
                page.wait_for_timeout(2000)
            else:
                print("⚠️  Create button not visible")
        except Exception as e:
            print(f"⚠️  Could not click Create button: {e}")

        # Fill form
        print("\n[7] Filling agent form...")
        page.wait_for_timeout(1000)

        agent_name = f"manual_test_agent_{int(__import__('time').time())}"

        # Fill name field
        try:
            name_input = page.locator('input[name="name"]').first
            if name_input.is_visible():
                name_input.click()
                name_input.fill(agent_name)
                print(f"✅ Name: {agent_name}")
        except Exception as e:
            print(f"⚠️  Could not fill name: {e}")

        # Fill description
        try:
            desc_input = page.locator('input[name="description"]').first
            if desc_input.is_visible():
                desc_input.click()
                desc_input.fill("Manual test agent - created via Playwright script")
                print("✅ Description filled")
        except Exception as e:
            print(f"⚠️  Could not fill description: {e}")

        # Fill instructions
        try:
            instructions_input = page.locator('textarea[name="instructions"]').first
            if instructions_input.is_visible():
                instructions_input.click()
                instructions_input.fill("You are a helpful assistant for manual testing.")
                print("✅ Instructions filled")
        except Exception as e:
            print(f"⚠️  Could not fill instructions: {e}")

        # Pause before save
        print("\n" + "=" * 80)
        print("⏸️  WAITING BEFORE SAVE")
        print("=" * 80)
        print("\n📋 AGENT FORM FILLED:")
        print(f"  Name: {agent_name}")
        print(f"  Description: Manual test agent - created via Playwright script")
        print(f"  Instructions: You are a helpful assistant for manual testing.")
        print("\n📋 NEXT STEPS:")
        print("  1. Review the form in the browser")
        print("  2. Waiting 10 seconds, then will click Save")
        print("  3. OR manually click Save in the browser yourself")
        print("\n" + "=" * 80)

        print("\n⏳ Waiting 10 seconds...")
        page.wait_for_timeout(10000)

        # Click Save
        print("\n[8] Clicking Save button...")
        try:
            save_button = page.locator('button:has-text("Save")').first
            if save_button.is_visible() and save_button.is_enabled():
                print("✅ Save button is enabled, clicking...")
                save_button.click()
                page.wait_for_timeout(3000)
                print(f"✅ Agent created! Current URL: {page.url}")
            else:
                print("⚠️  Save button not ready")
        except Exception as e:
            print(f"⚠️  Could not click Save: {e}")

        # Keep browser open
        print("\n" + "=" * 80)
        print("✅ SCRIPT COMPLETE")
        print("=" * 80)
        print("\nBrowser will stay open for 60 seconds for you to inspect.")
        print("Waiting 60 seconds before closing...")
        print("=" * 80)

        page.wait_for_timeout(60000)

        browser.close()
        print("\n✅ Browser closed. Script complete!")


if __name__ == "__main__":
    main()
