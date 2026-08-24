"""UI test — MCP detail page: three-dot menu actions (ELITEA-1946).

Opens a Remote MCP's detail page via a real list-card click, inventories the
three-dot menu's five items and their disabled states, exercises "Copy link"
(toast only — the clipboard's *content* is ELITEA-1959's subject), closes the
menu with Escape, pins the MCP via "Pin to top", and verifies it moves to the
top of ``/mcps/all``.

Two disposable MCPs are created, A **before** B: the list's default sort is
newest-first, so B sorts above A and pinning A therefore has a real position
to move past. Pinning an MCP that is already at the top proves nothing.

Step 6 re-opens the menu before pressing Escape (AFS § Test Steps 6, same fix
ELITEA-2049 took in review round 1): step 5's Copy-link click already closed
the menu (``DotMenu.jsx``'s ``withClose`` fires on every item click), so an
Escape press against an already-closed menu would pass even if Escape-to-close
regressed.

Disabled-ness is asserted via ``aria-disabled``, not ``is_enabled()``: MUI
renders a disabled ``MenuItem`` as ``<li aria-disabled="true" class="…
Mui-disabled">``, which Playwright does not read as disabled on a non-form
element.

No substitutions (AFS § Fidelity Declaration): every asserted value is
produced by the system — menu items and their states from the live DOM, the
toast from the live toast, the pin/unpin outcomes from the real ``POST`` /
``DELETE`` responses and the real re-sorted list.

Environment note (AFS § Preconditions): step 8's ``index == 0`` assertion
assumes no OTHER MCP in the project is pinned — verified live 2026-08-24 (all
19 MCPs in project 399 read "Pin to top"). A leftover pin from an aborted run
would fail this test legitimately rather than silently; the relative
``index(A) < index(B)`` assertion is asserted alongside, not instead.

Spec: test-specs/mcp/l2_mcp-detail-three-dot-menu-actions_ELITEA-1946.md
"""

import logging
import time

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.toolkits,
    pytest.mark.mcp,
    pytest.mark.p2,
    pytest.mark.regression,
]

TOOLKIT_URL = "https://mcp.example.com/sse"
UI_ELEMENT_TIMEOUT = 10_000
TOAST_TIMEOUT = 10_000

# Toolkit names are silently truncated at MAX_NAME_LENGTH = 32 (AFS § Test
# Data), so the prefix + a 10-digit unix timestamp must fit exactly.
NAME_PREFIX_A = "autotest_mcp_menu_a_"  # 20 chars + 10 = 30
NAME_PREFIX_B = "autotest_mcp_menu_b_"

COPY_LINK_TOAST = "The link has been copied to the clipboard."

# Expected menu inventory in DOM order, with the aria-disabled value each item
# must carry (None = the attribute must be absent, i.e. the item is enabled).
EXPECTED_MENU_ITEMS = (
    ("Export", "true"),
    ("Fork", "true"),
    ("Copy link", None),
    ("Pin to top", None),
    ("Delete", None),
)


def _create_mcp(form: McpFormPage, project_id: str, name: str) -> int:
    """Create a Remote MCP through the UI create flow and return its numeric id.

    The merged, proven path from ``test_mcp_delete_remote.py``: the
    ``ToolkitAPI.create_toolkit()`` shortcut exists but its Remote-MCP
    ``settings`` shape is unverified on this surface (AFS § Test Data), so the
    real UI flow is used.
    """
    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(name)
    form.fill_url(TOOLKIT_URL)
    response = form.save_and_wait_for_created(project_id)
    created_id = response["id"]
    assert isinstance(created_id, int), f"Save response should carry a numeric id: {response!r}"
    return created_id


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1946_mcp-detail-three-dot-menu-actions.md",
    "onetest-ai Test Case link",
)
def test_mcp_detail_three_dot_menu_actions(page, toolkit_api: ToolkitAPI):
    """The MCP detail three-dot menu lists five items with the expected states;
    Copy link toasts, Escape closes the menu, and Pin to top pins the MCP and
    moves it to the top of the list."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)

    ts = int(time.time())
    name_a = f"{NAME_PREFIX_A}{ts}"
    name_b = f"{NAME_PREFIX_B}{ts}"

    console_errors: list = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    id_a: int | None = None
    id_b: int | None = None
    try:
        with allure.step("Setup — create MCP A, then MCP B (B sorts above A: newest-first)"):
            id_a = _create_mcp(form, project_id, name_a)
            id_b = _create_mcp(form, project_id, name_b)
            logger.info("Created MCP A id=%s (%s), MCP B id=%s (%s)", id_a, name_a, id_b, name_b)

        with allure.step("Step 1 — Open MCP A's detail page from the list; verify it loaded"):
            list_page.navigate()
            assert name_a in list_page.get_card_names(), (
                f"{name_a!r} should appear in the MCP list after creation"
            )
            list_page.open_card_by_name(name_a)
            form.wait_for_page_load()
            assert f"/mcps/all/{id_a}" in page.url, (
                f"Should be on MCP A's detail page, got: {page.url}"
            )
            assert "viewMode=owner" in page.url, (
                f"Detail URL should carry viewMode=owner, got: {page.url}"
            )
            assert form.get_detail_heading_text() == name_a, (
                f"Detail title should read {name_a!r}, got {form.get_detail_heading_text()!r}"
            )
            assert form.name_input.input_value() == name_a, (
                "Toolkit Name field should hold MCP A's name"
            )

        with allure.step("Step 2 — Click the three-dot menu button; verify the menu opens"):
            form.open_controls_menu()
            assert form.controls_menu.is_visible(), "Three-dot menu should be visible after the click"

        with allure.step(
            "Step 3 — Verify the menu's five items and their states: Export (disabled), "
            "Fork (disabled), Copy link, Pin to top, Delete"
        ):
            menuitems = {
                "Export": form.export_menuitem,
                "Fork": form.fork_menuitem,
                "Copy link": form.copy_link_menuitem,
                "Pin to top": form.pin_toggle_menuitem,
                "Delete": form.delete_menuitem,
            }
            for label, expected_disabled in EXPECTED_MENU_ITEMS:
                item = menuitems[label]
                assert item.is_visible(), f"Menu item {label!r} should be visible"
                assert item.text_content().strip() == label, (
                    f"Menu item testid for {label!r} should render the label {label!r}, "
                    f"got {item.text_content()!r}"
                )
                actual_disabled = item.get_attribute("aria-disabled")
                assert actual_disabled == expected_disabled, (
                    f"Menu item {label!r} should have aria-disabled={expected_disabled!r} "
                    f"(MUI marks disabled MenuItems this way), got {actual_disabled!r}"
                )

            # DOM order, read off the menu popup's own text (the case names the
            # items in a specific order, and a reordered menu is a real change).
            menu_text = form.get_controls_menu_text()
            positions = [menu_text.index(label) for label, _ in EXPECTED_MENU_ITEMS]
            assert positions == sorted(positions), (
                "Menu items should appear in the order Export, Fork, Copy link, "
                f"Pin to top, Delete; got menu text {menu_text!r}"
            )

        with allure.step(
            'Step 4 — Click "Copy link"; verify the confirmation toast and that the menu closes'
        ):
            toast_text = form.click_copy_link_menu_item(timeout=TOAST_TIMEOUT)
            assert toast_text.strip() == COPY_LINK_TOAST, (
                f"Copy link should raise the toast {COPY_LINK_TOAST!r}, got {toast_text!r}"
            )
            # DotMenu.jsx's `withClose` fires on every item click — this is why
            # step 5 must RE-OPEN the menu before exercising Escape.
            assert form.controls_menu.count() == 0, (
                "The menu should close (unmount) as a side effect of clicking a menu item"
            )

        with allure.step("Step 5 — Re-open the menu and press Escape; verify the menu closes"):
            form.open_controls_menu()
            assert form.controls_menu.is_visible(), (
                "The menu must be re-opened before the Escape assertion, or the "
                "assertion could never fail (step 4's click already closed it)"
            )
            form.close_controls_menu_with_escape()
            assert form.controls_menu.count() == 0, (
                "The menu should be removed from the DOM after Escape (DotMenu unmounts it)"
            )

        with allure.step('Step 6 — Re-open the menu and click "Pin to top"; verify the MCP is pinned'):
            form.open_controls_menu()
            assert form.get_pin_toggle_menu_label().strip() == "Pin to top", (
                "The pin item should read 'Pin to top' before the MCP is pinned"
            )
            pin_response = form.click_pin_toggle_menu_item()
            assert pin_response.status == 201, (
                f"Pinning should POST .../social/pin/prompt_lib/{project_id}/toolkit/{id_a} "
                f"and return 201, got {pin_response.status} for {pin_response.url}"
            )
            form.open_controls_menu()
            assert form.get_pin_toggle_menu_label().strip() == "Unpin from top", (
                "The same pin menu item should now read 'Unpin from top' "
                "(usePinMenu's isPinned label contract)"
            )
            form.close_controls_menu_with_escape()

        with allure.step("Step 7 — Navigate to the MCP list; verify MCP A is at the top"):
            list_page.navigate()
            names = list_page.get_card_names()
            assert name_a in names, f"{name_a!r} should be present in the list, got {names[:5]}"
            assert name_b in names, f"{name_b!r} should be present in the list, got {names[:5]}"
            index_a = names.index(name_a)
            index_b = names.index(name_b)
            assert index_a == 0, (
                f"The pinned MCP {name_a!r} should be first in the list, got index {index_a} "
                f"(top of list: {names[:5]}). A stray pinned MCP left by an aborted run "
                "would also produce this failure — check the list before assuming a regression."
            )
            assert index_a < index_b, (
                f"The pinned MCP {name_a!r} (index {index_a}) should now sort above the "
                f"newer {name_b!r} (index {index_b}), which was above it before the pin"
            )
            assert list_page.get_pin_toggle_label(id_a) == "Unpin from top", (
                "MCP A's list-row pin toggle should now offer 'Unpin from top'"
            )
            assert list_page.get_pin_toggle_label(id_b) == "Pin to top", (
                "MCP B's list-row pin toggle should still offer 'Pin to top' (not pinned)"
            )

        with allure.step("Teardown — unpin MCP A via the detail menu; verify the 204"):
            list_page.open_card_by_name(name_a)
            form.wait_for_page_load()
            form.open_controls_menu()
            unpin_response = form.click_pin_toggle_menu_item()
            assert unpin_response.status == 204, (
                "Unpinning should DELETE .../social/pin/prompt_lib/"
                f"{project_id}/toolkit/{id_a} and return 204, got {unpin_response.status}"
            )

        assert not console_errors, (
            "No console errors expected across the whole three-dot-menu flow, got: "
            f"{[m.text for m in console_errors]}"
        )

    finally:
        for toolkit_id in (id_a, id_b):
            if toolkit_id is None:
                continue
            try:
                toolkit_api.delete_toolkit(toolkit_id)
            except Exception:
                logger.warning("Failed to delete MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True)
