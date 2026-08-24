"""UI test — Remote MCP: Copy link from the three-dot menu (ELITEA-1959).

Creates a uniquely-named disposable Remote MCP, opens its detail page from the
list, copies its link via the three-dot menu's "Copy link" item, asserts the
CLIPBOARD's actual content, then opens the copied URL in a new tab of the same
authenticated context and verifies the same MCP's detail page loads.

Case-text drift, filed as CLARIFICATION
https://github.com/EliteaAI/elitea-testing-public/issues/1729 (NOT a product
defect — reverse-masking guard applies): the case's § Test Data "Expected URL
format" (``https://dev.elitea.ai/app/mcps/all/{id}?viewMode=owner&name={name}``)
omits the ``/{projectId}`` path segment the product actually emits. The shape
is by design — ``useProjectEntityLink.js`` builds
``origin + basename + projectPath + search``, and ``usePageDetails().projectPath``
carries ``PROJECT_ID_URL_PREFIX``. This test asserts the LIVE contract, built
from config (``settings.app_base_url`` + ``settings.elitea_project_id``) so it
is correct on localhost and on a deployed env alike — never a hardcoded host.

The ``/{projectId}`` prefix triggers ``ProjectSwitcher``, which performs a hard
``window.location.replace()`` BEFORE the MCP page mounts — so the new tab's URL
is asserted on the SETTLED state (after waiting on the detail page's own ready
signal), never immediately after ``goto``.

The clipboard is read via ``page.wait_for_function`` polling, not a direct
``navigator.clipboard.readText()`` call: a direct call hung ~30 min on an
un-grantable permission prompt during ELITEA-2049's exploration. The clipboard
is cleared with a real write first, which turns the post-click wait into a real
condition instead of a sleep.

No substitutions (AFS § Fidelity Declaration): the clipboard is written by the
product's own ``navigator.clipboard.writeText()`` inside ``useCopyLink`` — the
test only clears and READS it — and step 5 navigates to the exact string the
product produced. No ``page.route``, no fabricated response, no injected state.

Spec: test-specs/mcp/l2_remote-mcp-copy-link-from-three-dot-menu_ELITEA-1959.md
"""

import logging
import time
from urllib.parse import quote

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
CLIPBOARD_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 20_000

# Silently truncated at MAX_NAME_LENGTH = 32 — 22-char prefix + a 10-digit unix
# timestamp is exactly 32 (AFS § Test Data).
NAME_PREFIX = "autotest_mcp_copylink_"

COPY_LINK_TOAST = "The link has been copied to the clipboard."


def _copy_link_via_menuitem(page, form: McpFormPage, timeout: int) -> tuple[str, str]:
    """Click "Copy link"; return ``(toast text, the URL the product copied)``.

    Mirrors ``test_pipeline_three_dot_menu_actions.py``'s helper of the same
    name (itself lifted from ``test_agent_copy_version_link.py``) per the AFS
    § Automation Hints — reused rather than re-derived: clear the clipboard
    with a real write, click the menu item (which also closes the menu), wait
    for the toast in the same chain, then POLL ``readText()`` via
    ``wait_for_function`` instead of calling it directly.
    """
    page.evaluate("() => navigator.clipboard.writeText('')")
    toast_text = form.click_copy_link_menu_item(timeout=timeout)
    page.wait_for_function(
        "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
        timeout=timeout,
    )
    copied = page.evaluate("async () => await navigator.clipboard.readText()")
    logger.info("Copy link toast=%r clipboard=%r", toast_text, copied)
    return toast_text, copied


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1959_remote-mcp-copy-link-from-three-dot-menu.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/elitea-testing-public/issues/1729",
    "Case-text drift CLARIFICATION #1729",
)
def test_remote_mcp_copy_link_from_three_dot_menu(page, toolkit_api: ToolkitAPI):
    """"Copy link" copies the MCP's project-scoped deep link, and that URL opens
    the same MCP's detail page in a new tab."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)

    name = f"{NAME_PREFIX}{int(time.time())}"

    console_errors: list = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    created_id: int | None = None
    new_page = None
    try:
        with allure.step("Setup — create a uniquely-named Remote MCP via the UI create flow"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            form.fill_name(name)
            form.fill_url(TOOLKIT_URL)
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), (
                f"Save response should carry a numeric id: {save_response!r}"
            )
            # The product silently truncates at 32 chars — assert the PERSISTED
            # name rather than assuming the literal survived (AFS § Test Data).
            persisted_name = save_response.get("name", name)
            assert persisted_name == name, (
                f"Created MCP's persisted name {persisted_name!r} should match {name!r} "
                "(32-char truncation boundary)"
            )

        with allure.step("Step 1 — Open the MCP's detail page from the list; verify it loaded"):
            list_page.navigate()
            assert name in list_page.get_card_names(), (
                f"{name!r} should appear in the MCP list after creation"
            )
            list_page.open_card_by_name(name)
            form.wait_for_page_load()
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should be on the MCP's detail page, got: {page.url}"
            )
            assert form.get_detail_heading_text() == name, (
                f"Detail title should read {name!r}, got {form.get_detail_heading_text()!r}"
            )

        with allure.step("Precondition — grant clipboard permissions on the browser context"):
            page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        with allure.step("Step 2 — Click the three-dot menu button; verify the menu opens"):
            form.open_controls_menu()
            assert form.controls_menu.is_visible(), "Three-dot menu should be visible after the click"

        with allure.step('Step 3 — Click "Copy link"; verify the toast and that the menu closes'):
            toast_text, copied_url = _copy_link_via_menuitem(page, form, CLIPBOARD_TIMEOUT)
            assert toast_text.strip() == COPY_LINK_TOAST, (
                f"Copy link should raise the toast {COPY_LINK_TOAST!r}, got {toast_text!r}"
            )
            assert form.controls_menu.count() == 0, (
                "The menu should close (unmount) as a side effect of clicking a menu item"
            )

        with allure.step(
            "Step 4 — Verify the clipboard holds this MCP's project-scoped URL "
            "(live contract includes /{projectId} — CLARIFICATION #1729)"
        ):
            expected_prefix = f"{settings.app_base_url}/{project_id}/mcps/all/{created_id}"
            assert copied_url.startswith(expected_prefix), (
                f"Copied URL should start with {expected_prefix!r} — the live product emits a "
                f"/{{projectId}} segment the case text omits (CLARIFICATION #1729); got {copied_url!r}"
            )
            assert "viewMode=owner" in copied_url, (
                f"Copied URL should carry viewMode=owner, got {copied_url!r}"
            )
            assert f"name={quote(name)}" in copied_url, (
                f"Copied URL should carry the URL-encoded MCP name, got {copied_url!r}"
            )

        with allure.step(
            "Step 5 — Open the copied URL in a new tab of the same authenticated "
            "context; verify the same MCP's detail page loads"
        ):
            # page.context.new_page(), NOT browser.new_page(): the latter creates
            # an UNAUTHENTICATED context (note already carried by
            # test_agent_hub_copy_link_from_modal.py).
            new_page = page.context.new_page()
            new_page_console_errors: list = []
            new_page.on(
                "console",
                lambda msg: new_page_console_errors.append(msg) if msg.type == "error" else None,
            )
            new_page.goto(copied_url, wait_until="load", timeout=NAVIGATION_TIMEOUT)

            new_tab_form = McpFormPage(new_page)
            # Waits past the "Edit MCP" placeholder AND past ProjectSwitcher's
            # hard location.replace() — so the URL assertion below reads the
            # SETTLED state, not the pre-redirect one.
            new_tab_form.wait_for_page_load()
            assert new_tab_form.get_detail_heading_text() == name, (
                f"The copied URL should open {name!r}'s detail page, got "
                f"{new_tab_form.get_detail_heading_text()!r}"
            )
            assert new_tab_form.name_input.input_value() == name, (
                "The new tab's Toolkit Name field should hold the same MCP's name"
            )

            settled_prefix = f"{settings.app_base_url}/mcps/all/{created_id}"
            assert new_page.url.startswith(settled_prefix), (
                f"The new tab should settle at {settled_prefix!r} — ProjectSwitcher strips the "
                f"/{{projectId}} prefix after switching project — got {new_page.url!r}"
            )
            assert "viewMode=owner" in new_page.url, (
                f"The settled URL should keep viewMode=owner, got {new_page.url!r}"
            )
            assert not new_page_console_errors, (
                "No console errors expected on the deep-linked tab, got: "
                f"{[m.text for m in new_page_console_errors]}"
            )

        assert not console_errors, (
            "No console errors expected across the copy-link flow, got: "
            f"{[m.text for m in console_errors]}"
        )

    finally:
        if new_page is not None:
            try:
                new_page.close()
            except Exception:
                logger.warning("Failed to close the deep-link tab during cleanup", exc_info=True)
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning(
                    "Failed to delete MCP toolkit id=%s during cleanup", created_id, exc_info=True
                )
