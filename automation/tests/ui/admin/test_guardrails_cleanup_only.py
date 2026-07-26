"""Test guardrails cleanup in isolation.

This test file is for debugging cleanup logic locally.
Run with: cd automation && pytest tests/ui/admin/test_guardrails_cleanup_only.py -v -s
"""

import logging
import pytest
from playwright.sync_api import Browser, Page

from pages.guardrails_admin_page import GuardrailsAdminPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin]

# Test data matching main test file
TEST_TOOLKIT = "github"
TEST_TOOL = "get_ISSUE"


@pytest.fixture
def admin_page(browser: Browser, auth_state) -> Page:
    """Create a browser page for Admin UI tests."""
    ctx = browser.new_context(
        storage_state=auth_state,
        viewport={"width": 1920, "height": 1080},
    )
    ctx.set_default_timeout(15000)
    ctx.set_default_navigation_timeout(30000)

    pg = ctx.new_page()
    yield pg

    pg.close()
    ctx.close()


def test_cleanup_before(admin_page: Page):
    """Test cleanup BEFORE tests - removes any leftover blocked items."""
    print("\n" + "="*80)
    print("TESTING CLEANUP BEFORE TESTS")
    print("="*80)

    guardrails = GuardrailsAdminPage(admin_page)
    guardrails.navigate_to_guardrails()
    print("[DEBUG] Navigated to guardrails page")

    # Get current state
    print("\n[DEBUG] Getting current blocked toolkits...")
    try:
        blocked_toolkits = guardrails.get_blocked_toolkits()
        print(f"[DEBUG] Currently blocked toolkits: {blocked_toolkits}")
    except Exception as e:
        print(f"[DEBUG] Error getting blocked toolkits: {e}")
        blocked_toolkits = []

    # Debug: Try different locator strategies to find chips
    print("\n[DEBUG] Trying different locator strategies to find chips...")

    # Strategy 1: All chips on the page
    all_chips = admin_page.locator('.MuiChip-label').all()
    print(f"[DEBUG] Strategy 1 - All .MuiChip-label on page: {len(all_chips)} found")
    for i, chip in enumerate(all_chips):
        print(f"  Chip {i}: '{chip.text_content()}'")

    # Strategy 2: Chips with deletable class
    deletable_chips = admin_page.locator('.MuiChip-deletable .MuiChip-label').all()
    print(f"[DEBUG] Strategy 2 - Deletable chips: {len(deletable_chips)} found")
    for i, chip in enumerate(deletable_chips):
        print(f"  Deletable chip {i}: '{chip.text_content()}'")

    # Strategy 3: Look for "github" specifically
    github_chip = admin_page.locator('.MuiChip-label:has-text("github")').first
    if github_chip.count() > 0:
        print(f"[DEBUG] Strategy 3 - Found github chip: visible={github_chip.is_visible()}")
    else:
        print("[DEBUG] Strategy 3 - No github chip found")

    # Try to remove blocked toolkits
    print("\n[DEBUG] Attempting to remove blocked toolkits...")
    for toolkit in [TEST_TOOLKIT, "github", "GITHUB", "Github"]:
        try:
            is_blocked = guardrails.is_toolkit_blocked(toolkit)
            print(f"[DEBUG] Checking toolkit '{toolkit}': blocked={is_blocked}")
            if is_blocked:
                print(f"[DEBUG] Removing blocked toolkit: {toolkit}")
                guardrails.remove_blocked_toolkit(toolkit)
                print(f"[DEBUG] ✓ Removed blocked toolkit: {toolkit}")
        except Exception as e:
            print(f"[DEBUG] ✗ Could not remove toolkit {toolkit}: {e}")

    # Try to remove blocked tools
    print("\n[DEBUG] Attempting to remove blocked tools...")
    for tool in [TEST_TOOL, "get_issue", "GET_ISSUE", "Get_Issue"]:
        try:
            is_blocked = guardrails.is_tool_blocked(tool)
            print(f"[DEBUG] Checking tool '{tool}': blocked={is_blocked}")
            if is_blocked:
                print(f"[DEBUG] Removing blocked tool: {tool}")
                guardrails.remove_blocked_tool(tool)
                print(f"[DEBUG] ✓ Removed blocked tool: {tool}")
        except Exception as e:
            print(f"[DEBUG] ✗ Could not remove tool {tool}: {e}")

    # Try to remove empty toolkit containers
    print("\n[DEBUG] Attempting to remove empty toolkit containers...")
    try:
        guardrails.remove_empty_toolkit_containers()
        print("[DEBUG] ✓ Removed empty toolkit containers")
    except Exception as e:
        print(f"[DEBUG] ✗ Could not remove empty toolkit containers: {e}")

    # Try to remove sensitive tools
    print("\n[DEBUG] Attempting to remove sensitive tools...")
    for tool in [TEST_TOOL, "get_issue", "GET_ISSUE", "Get_Issue"]:
        try:
            is_sensitive = guardrails.is_tool_in_sensitive_list(tool, TEST_TOOLKIT)
            print(f"[DEBUG] Checking tool '{tool}': sensitive={is_sensitive}")
            if is_sensitive:
                print(f"[DEBUG] Removing sensitive tool: {tool}")
                guardrails.remove_sensitive_tool(tool)
                print(f"[DEBUG] ✓ Removed sensitive tool: {tool}")
        except Exception as e:
            print(f"[DEBUG] ✗ Could not remove sensitive tool {tool}: {e}")

    # Check Save button state
    print("\n[DEBUG] Checking Save button state...")
    save_btn = admin_page.locator('button:has-text("Save")').last
    if save_btn.count() > 0:
        print(f"[DEBUG] Save button: visible={save_btn.is_visible()}, enabled={save_btn.is_enabled()}")
        if save_btn.is_enabled():
            print("[DEBUG] Saving configuration...")
            guardrails.save_configuration(timeout=20000)
            print("[DEBUG] ✓ Configuration saved")
        else:
            print("[DEBUG] Save button not enabled - no changes to save")
    else:
        print("[DEBUG] Save button not found")

    print("\n" + "="*80)
    print("CLEANUP BEFORE TESTS - COMPLETE")
    print("="*80)


def test_cleanup_after(admin_page: Page):
    """Test cleanup AFTER tests - removes any blocked items added during tests."""
    print("\n" + "="*80)
    print("TESTING CLEANUP AFTER TESTS")
    print("="*80)

    # This is the same as cleanup_before
    test_cleanup_before(admin_page)
