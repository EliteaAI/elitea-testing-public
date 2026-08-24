"""UI test — MCP dashboard: pin/unpin an MCP from its list card (ELITEA-1945).

Seeds two disposable Remote MCPs through the UI create flow, pins the OLDER
one from its list card, verifies it jumps above the newer one, that its
control's label flips, that unpinning flips it back, and that the next list
fetch restores the exact pre-pin order.

Two MCPs, A created **before** B, and A is the one pinned: the list's default
sort is newest-first, so a freshly created MCP is already at index 0 and
pinning it would satisfy "moves to top" vacuously. ``index(A) < index(B)``
after the pin is what proves the pin re-sorted anything (AFS § Preconditions,
``_surface.md`` "vacuity trap").

The pin/unpin timing is **asymmetric** and the test is written around the real
behaviour: pinning re-sorts the list immediately, client-side; unpinning does
NOT — the card keeps its index-0 position, with its label already flipped back,
until the next list fetch. So step 7 re-navigates before asserting "no longer
at the top". That re-navigation is not in the case text and is filed as
clarification EliteaAI/elitea-testing-public#1740; asserting the case text
literally would fail against a correctly-behaving product. The intermediate
"still at index 0 right after the unpin" state is deliberately NOT asserted —
it is an optimistic-update detail, not the case's observable.

Card-hover reveal: unhovered, the pin toggle renders at ``opacity: 0``.
Playwright's visibility definition ignores opacity, so a bare
``to_be_visible()`` would pass on a control no human can see — case step 2
("Pin to top button is visible on the card") is therefore asserted as
``opacity == 1`` after a hover.

No substitutions (AFS § Test Data, fidelity note): seeding two MCPs via the UI
create flow is **transit only** — it merely produces the entities to pin. Every
asserted observable (list order, ``aria-label`` state, pin/unpin HTTP status,
restored baseline order) is produced by the live product.

Spec: test-specs/mcp/l2_mcp-dashboard-pin-unpin-mcp_ELITEA-1945.md
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
# Data), so the prefix + a 10-digit unix timestamp must fit.
NAME_PREFIX_A = "autotest_mcp_pin_a_"  # 19 chars + 10 = 29
NAME_PREFIX_B = "autotest_mcp_pin_b_"

LABEL_PIN = "Pin to top"
LABEL_UNPIN = "Unpin from top"


def _create_mcp(form: McpFormPage, project_id: str, name: str) -> int:
    """Create a Remote MCP through the UI create flow and return its numeric id.

    The merged, proven path (``test_mcp_three_dot_menu_actions.py``): the
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
    "automated-full-regression-ui/mcp/ELITEA-1945_mcp-dashboard-pin-unpin-mcp.md",
    "onetest-ai Test Case link",
)
def test_mcp_dashboard_pin_unpin(page, toolkit_api: ToolkitAPI):
    """Pinning an MCP from its list card moves it above a newer MCP and flips
    its control to "Unpin from top"; unpinning flips the control back and the
    next list fetch restores the original order exactly."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    list_page = McpListPage(page)

    ts = int(time.time())
    name_a = f"{NAME_PREFIX_A}{ts}"
    name_b = f"{NAME_PREFIX_B}{ts}"

    # Console-error side channel (AFS § Test Steps 9). Registered AFTER setup,
    # deliberately: the /mcps/create type picker emits a React dev-mode "unique
    # key prop" warning on every mount — already tracked as
    # EliteaAI/elitea-testing-public#656, on a page this CASE never visits.
    # Scoping the listener to the case's own flow keeps the assertion about the
    # surface under test instead of about our scaffolding; it is not a
    # weakening (the known defect stays filed and unmasked).
    console_errors: list = []

    id_a: int | None = None
    id_b: int | None = None
    try:
        with allure.step("Setup — create MCP A, then MCP B (B sorts above A: newest-first)"):
            id_a = _create_mcp(form, project_id, name_a)
            id_b = _create_mcp(form, project_id, name_b)
            logger.info("Created MCP A id=%s (%s), MCP B id=%s (%s)", id_a, name_a, id_b, name_b)

        with allure.step(
            "Step 1 — Navigate to the MCP list in Card view; capture the baseline order "
            "and verify nothing is pinned"
        ):
            page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
            list_page.navigate()
            baseline_names = list_page.get_card_names()
            assert name_a in baseline_names, (
                f"{name_a!r} should appear in the MCP list after creation, got {baseline_names[:5]}"
            )
            assert name_b in baseline_names, (
                f"{name_b!r} should appear in the MCP list after creation, got {baseline_names[:5]}"
            )
            baseline_index_a = baseline_names.index(name_a)
            baseline_index_b = baseline_names.index(name_b)
            assert baseline_index_a > 0, (
                f"MCP A {name_a!r} must NOT already be first (index {baseline_index_a}) — pinning an "
                "MCP that is already at the top would satisfy the case's central assertion vacuously"
            )
            assert baseline_index_b < baseline_index_a, (
                f"The newer MCP B {name_b!r} (index {baseline_index_b}) should sort above the older "
                f"MCP A {name_a!r} (index {baseline_index_a}) under the default newest-first sort"
            )
            pin_labels = list_page.get_all_pin_toggle_labels()
            assert pin_labels, "Every MCP card should render a pin toggle; found none"
            assert LABEL_UNPIN not in pin_labels, (
                "Precondition: no MCP in the project may be pinned before this test pins one "
                f"(a stray pin sits at index 0 and breaks the 'moved to top' read). Labels: {pin_labels}"
            )

        with allure.step(
            'Step 2 — Hover MCP A\'s pin toggle; verify it is revealed and reads "Pin to top"'
        ):
            list_page.hover_pin_toggle(id_a)
            # Playwright reports an opacity:0 element as visible, so the case's
            # "button is visible on the card" is only honestly asserted by the
            # computed opacity of the hover-revealed control (AFS step 3).
            expect(list_page.pin_toggle_button(id_a).first).to_have_css(
                "opacity", "1", timeout=UI_ELEMENT_TIMEOUT
            )
            assert list_page.get_pin_toggle_label(id_a) == LABEL_PIN, (
                f"MCP A's card pin toggle should read {LABEL_PIN!r} while the MCP is unpinned, "
                f"got {list_page.get_pin_toggle_label(id_a)!r}"
            )

        with allure.step('Step 3 — Click "Pin to top" on MCP A; verify the pin POST returns 201'):
            pin_response = list_page.click_pin_toggle(id_a)
            assert pin_response.status == 201, (
                f"Pinning should POST .../social/pin/prompt_lib/{project_id}/toolkit/{id_a} and "
                f"return 201, got {pin_response.status} for {pin_response.url}"
            )

        with allure.step("Step 4 — Verify MCP A moved to the top of the list, above the newer MCP B"):
            # The re-sort is an immediate client-side update — awaited on its
            # own condition (first card's name), never on a sleep.
            list_page.wait_for_card_at_top(name_a)
            names_after_pin = list_page.get_card_names()
            index_a = names_after_pin.index(name_a)
            index_b = names_after_pin.index(name_b)
            assert index_a == 0, (
                f"The pinned MCP {name_a!r} should be first in the list, got index {index_a} "
                f"(top of list: {names_after_pin[:5]})"
            )
            assert index_a < index_b, (
                f"The pinned MCP {name_a!r} (index {index_a}) should now sort above the newer "
                f"{name_b!r} (index {index_b}), which was above it before the pin — this is what "
                "proves the pin re-sorted the list rather than the default sort"
            )

        with allure.step('Step 5 — Verify MCP A\'s control now reads "Unpin from top", MCP B\'s does not'):
            list_page.wait_for_pin_toggle_label(id_a, LABEL_UNPIN)
            assert list_page.get_pin_toggle_label(id_b) == LABEL_PIN, (
                f"MCP B's toggle should still read {LABEL_PIN!r} — the label flip is scoped to the "
                f"pinned entity, got {list_page.get_pin_toggle_label(id_b)!r}"
            )

        with allure.step(
            'Step 6 — Click "Unpin from top" on MCP A; verify the DELETE returns 204 and the '
            "label flips back"
        ):
            unpin_response = list_page.click_pin_toggle(id_a)
            assert unpin_response.status == 204, (
                f"Unpinning should DELETE .../social/pin/prompt_lib/{project_id}/toolkit/{id_a} and "
                f"return 204, got {unpin_response.status} for {unpin_response.url}"
            )
            list_page.wait_for_pin_toggle_label(id_a, LABEL_PIN)

        with allure.step(
            "Step 7 — Re-fetch the list; verify MCP A is back in its original position and the "
            "whole order matches the pre-pin baseline"
        ):
            # The re-navigation is MANDATORY and is not in the case text
            # (clarification EliteaAI/elitea-testing-public#1740): unpinning
            # does not re-sort in place, so the order is only recomputed from
            # the next list fetch. Asserting "no longer at the top" straight
            # after the unpin click would fail against a correct product.
            list_page.navigate()
            restored_names = list_page.get_card_names()
            restored_index_a = restored_names.index(name_a)
            assert restored_index_a > 0, (
                f"After unpinning and re-fetching, {name_a!r} should no longer be at the top, "
                f"got index {restored_index_a}"
            )
            assert restored_index_a == baseline_index_a, (
                f"{name_a!r} should be back at its original index {baseline_index_a}, "
                f"got {restored_index_a}"
            )
            assert restored_names == baseline_names, (
                "The whole restored list order should match the pre-pin baseline exactly "
                f"(catches a re-sort that puts A back while disturbing everything else).\n"
                f"baseline: {baseline_names}\nrestored: {restored_names}"
            )
            restored_labels = list_page.get_all_pin_toggle_labels()
            assert LABEL_UNPIN not in restored_labels, (
                f"No MCP should be left pinned after the test, got labels {restored_labels}"
            )

        assert not console_errors, (
            "No console errors expected across the whole pin/unpin flow, got: "
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
