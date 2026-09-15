"""Quick script to inspect the schedule modal structure."""
import sys
from playwright.sync_api import sync_playwright

def inspect_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to dev and login (using storage state)
        page.goto("https://dev.elitea.ai/app")

        input("Navigate to a pipeline, open schedule modal, then press Enter here...")

        # Wait for modal
        modal = page.locator('[role="dialog"]').filter(has_text="Schedule Settings").first
        modal.wait_for(state="visible", timeout=30000)

        # Take snapshot
        print("\n=== MODAL SNAPSHOT ===")
        snapshot = page.accessibility.snapshot(root=modal.element_handle())
        print(snapshot)

        print("\n=== LOOKING FOR TABS/RADIOS ===")
        # Check for tabs
        tabs = modal.locator('[role="tab"]')
        print(f"Tabs count: {tabs.count()}")
        for i in range(tabs.count()):
            print(f"  Tab {i}: {tabs.nth(i).text_content()}")

        # Check for radio buttons
        radios = modal.locator('[role="radio"]')
        print(f"\nRadios count: {radios.count()}")
        for i in range(radios.count()):
            print(f"  Radio {i}: {radios.nth(i).text_content()}")

        # Check for labels with text
        labels = modal.locator('label')
        print(f"\nLabels count: {labels.count()}")
        for i in range(min(10, labels.count())):
            text = labels.nth(i).text_content()
            if text:
                print(f"  Label {i}: {text[:50]}")

        input("\nPress Enter to close...")
        browser.close()

if __name__ == "__main__":
    inspect_modal()
