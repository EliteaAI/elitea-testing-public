#!/usr/bin/env python3
"""Debug script to test guardrails cleanup logic."""

import sys
from playwright.sync_api import sync_playwright
from pages.guardrails_admin_page import GuardrailsAdminPage
from config import settings
import json

def main():
    print(f"Testing against: {settings.elitea_url}")
    print(f"User: {settings.test_user_email}")

    # Load auth state
    try:
        with open('.auth/state.json', 'r') as f:
            storage_state = json.load(f)
    except FileNotFoundError:
        print("ERROR: Auth state not found. Run tests first to generate .auth/state.json")
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            storage_state=storage_state,
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        guardrails = GuardrailsAdminPage(page)

        print("\n=== NAVIGATING TO GUARDRAILS ===")
        guardrails.navigate_to_guardrails()
        page.wait_for_timeout(2000)

        print("\n=== TESTING remove_empty_sensitive_toolkit_blocks() ===")
        try:
            guardrails.remove_empty_sensitive_toolkit_blocks(timeout=10000)
            print("\n✅ Cleanup completed successfully")
        except Exception as e:
            print(f"\n❌ Cleanup failed: {e}")
            import traceback
            traceback.print_exc()

        print("\n=== Waiting 5s for visual inspection ===")
        page.wait_for_timeout(5000)

        browser.close()

if __name__ == "__main__":
    sys.exit(main() or 0)
