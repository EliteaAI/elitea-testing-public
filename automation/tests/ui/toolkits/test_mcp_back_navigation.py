"""UI test — MCP back navigation from detail to list (ELITEA-1961).

Filters the MCP list down to a single disposable MCP, opens that MCP's detail
page with a real card click, returns to the list through the product's own
top-left navigation control, and verifies the list's search filter survived
the round trip.

**The control is a breadcrumb, not a back arrow.** The case text (steps 3-4)
describes an arrow-icon back button; ``/mcps/all/:id`` declares a breadcrumb
trail (``breadcrumb.constants.js``) and ``EditToolkit.jsx`` renders
``hasBreadcrumbTrail ? <Breadcrumbs/> : (<BackButton/> + title)``, so the
BackButton branch is unreachable on this route. That is case-text drift, not a
product defect — filed as CLARIFICATION
EliteaAI/elitea-testing-public#1731 — so this test asserts the LIVE contract
(the breadcrumb link) and additionally asserts ``back-button`` has count 0, to
keep the finding test-enforced rather than documentation-only.

**Scroll position is deliberately not asserted, in either direction.** The
case's step 6 expects the list scroll position to be restored; live it is not
(``scrollTop`` 99 -> 0, no restoration code exists anywhere in ``src/``).
Asserting preservation would reverse-mask a permanent RED for behaviour the
product never implemented; asserting reset-to-0 would cement possibly
unintended behaviour as the contract. Filed as CLARIFICATION
EliteaAI/elitea-testing-public#1732 for a human to rule on. The "filters still
applied" half of step 6 IS asserted, and passes.

No substitutions (AFS § Fidelity Declaration): the filter is applied through
the product's own search control, the detail page is reached by a real card
click, and the return is a real click on the product's breadcrumb link. No
``page.route``, no fabricated response, no injected state, no API-seeded
stand-in for a UI step.

Spec: test-specs/mcp/l2_mcp-back-navigation-detail-to-list_ELITEA-1961.md
"""

import logging
import time

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
from playwright.sync_api import expect

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

# Toolkit names are silently truncated at MAX_NAME_LENGTH = 32 (AFS § Test
# Data): 21-char prefix + a 10-digit unix timestamp = 31 chars. The stored
# name is still read back off the create response rather than assumed.
NAME_PREFIX = "autotest_mcp_backnav_"

LIST_PATH = "/mcps/all"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1961_mcp-back-navigation-from-detail-to-list.md",
    "onetest-ai Test Case link",
)
def test_mcp_back_navigation_detail_to_list(page, toolkit_api: ToolkitAPI):
    """The MCP detail page's breadcrumb 'MCPs' link returns to the MCP list,
    and the list's applied search filter survives the round trip."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)

    name = f"{NAME_PREFIX}{int(time.time())}"

    # Console-error side channel (AFS step 6b). Registered AFTER setup,
    # deliberately: the /mcps/create type-picker emits a React dev-mode
    # "unique key prop" console error on every mount (tracked as
    # EliteaAI/elitea-testing-public#656) on a page this CASE never visits.
    # Scoping the listener to the case's own flow keeps the assertion about
    # the surface under test instead of about our scaffolding — the known
    # defect stays filed and unmasked.
    console_errors: list = []
    # A full document load fires page's "load" event; a client-side route
    # change does not. Watching for its ABSENCE is how step 4 proves the
    # breadcrumb navigates in-app rather than reloading.
    document_loads: list = []

    toolkit_id: int | None = None
    try:
        with allure.step("Setup — create a disposable Remote MCP through the UI create flow"):
            form.navigate_to_create()
            form.select_remote_mcp_type()
            form.fill_name(name)
            form.fill_url(TOOLKIT_URL)
            created = form.save_and_wait_for_created(project_id)
            toolkit_id = created["id"]
            assert isinstance(toolkit_id, int), (
                f"Save response should carry a numeric id: {created!r}"
            )
            # The name may be truncated at MAX_NAME_LENGTH — search on what
            # the product actually stored, never on the literal we typed.
            stored_name = created["name"]
            logger.info("Created MCP id=%s stored_name=%r (typed %r)", toolkit_id, stored_name, name)

        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page.on("load", lambda loaded_page: document_loads.append(loaded_page))

        with allure.step("Step 1 — Navigate to the MCP list page; capture the unfiltered baseline"):
            list_page.navigate()
            count_unfiltered = list_page.get_card_count()
            assert count_unfiltered > 1, (
                "The project needs at least 2 MCPs for the filter observable to be a "
                f"provable narrowing (AFS § Preconditions), got {count_unfiltered}"
            )
            # The breadcrumb nav is the detail-vs-list discriminator: it must
            # NOT be present on the list page.
            expect(form.breadcrumbs_nav).to_have_count(0)

        with allure.step("Step 1b — Apply a search filter; verify it narrows the list to one card"):
            list_page.search(stored_name)
            assert list_page.get_card_count() == 1, (
                f"Searching for the unique name {stored_name!r} should leave exactly one "
                f"card, got {list_page.get_card_count()} ({list_page.get_card_names()})"
            )
            assert list_page.get_card_names() == [stored_name], (
                f"The single remaining card should be {stored_name!r}, "
                f"got {list_page.get_card_names()}"
            )
            expect(list_page.search_input).to_have_value(stored_name)
            # The filter is client-side redux state (src/slices/search.js), not
            # a URL param — recording that mechanism here means a future move
            # of the filter into the URL flags this assertion instead of
            # silently changing why step 6 passes.
            assert page.url.endswith(LIST_PATH), (
                f"The filtered list URL should still be {LIST_PATH!r} with no query string, "
                f"got {page.url}"
            )

        with allure.step("Step 2 — Open the MCP's detail page with a real card click"):
            list_page.open_card_by_name(stored_name)
            # open_card_by_name() does NOT wait for the destination page
            # (_surface.md) — the caller owns the detail page's ready wait.
            form.wait_for_page_load()
            assert f"{LIST_PATH}/{toolkit_id}" in page.url, (
                f"Should be on the MCP's detail page, got: {page.url}"
            )
            assert "viewMode=owner" in page.url, (
                f"Detail URL should carry viewMode=owner, got: {page.url}"
            )
            expect(form.detail_title).to_have_text(stored_name)

        with allure.step(
            "Step 3 — Verify the detail page's top-left navigation control: a breadcrumb "
            "trail (NOT the case's back arrow — CLARIFICATION #1731)"
        ):
            expect(form.breadcrumbs_nav).to_be_visible()
            assert form.get_breadcrumb_text() == f"MCPs/{stored_name}", (
                f"The breadcrumb trail should read 'MCPs/{stored_name}', "
                f"got {form.get_breadcrumb_text()!r}"
            )
            # Count-then-text, not .first: exactly one parent crumb renders on
            # this page today, and asserting the count makes that an enforced
            # invariant instead of a silent assumption.
            expect(form.breadcrumb_parent_link).to_have_count(1)
            expect(form.breadcrumb_parent_link).to_have_text("MCPs")
            # The case's arrow-icon back button does not exist on this route.
            # This absence assertion is first-class and deliberate: if the UI
            # team restores the arrow, this test goes red and the case text
            # gets revisited, instead of the drift rotting in a docstring.
            expect(form.back_button).to_have_count(0)

        with allure.step("Step 4 — Click the 'MCPs' breadcrumb link; verify no full reload"):
            loads_before = len(document_loads)
            form.click_breadcrumb_parent()
            assert len(document_loads) == loads_before, (
                "The breadcrumb should navigate client-side; a document 'load' event "
                "means the app did a full reload instead"
            )

        with allure.step("Step 5 — Verify the MCP list page is displayed again"):
            assert page.url.endswith(LIST_PATH), (
                f"The breadcrumb should return to {LIST_PATH!r}, got {page.url}"
            )
            expect(list_page.search_input).to_be_visible()
            # Left the detail route for real, not just changed the URL.
            expect(form.breadcrumbs_nav).to_have_count(0)

        with allure.step("Step 6 — Verify the list's applied filter survived the round trip"):
            expect(list_page.search_input).to_have_value(stored_name)
            assert list_page.get_card_count() == 1, (
                "The search filter should still be applied after returning from the "
                f"detail page, got {list_page.get_card_count()} cards "
                f"({list_page.get_card_names()})"
            )
            assert list_page.get_card_names() == [stored_name], (
                f"The still-filtered list should hold only {stored_name!r}, "
                f"got {list_page.get_card_names()}"
            )
            # Scroll position (the case's other half) is NOT asserted — see
            # the module docstring and CLARIFICATION #1732.

        with allure.step("Step 6b — Verify no console errors were raised across steps 1-6"):
            assert not console_errors, (
                "No console errors expected across the back-navigation flow, got: "
                f"{[m.text for m in console_errors]}"
            )

    finally:
        if toolkit_id is not None:
            try:
                toolkit_api.delete_toolkit(toolkit_id)
            except Exception:
                logger.warning(
                    "Failed to delete MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
                )
