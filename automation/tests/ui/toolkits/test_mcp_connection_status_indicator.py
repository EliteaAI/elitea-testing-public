"""UI test — Remote MCP connection-status indicator (Not Connected -> Connected!).

TMS: ELITEA-1936 (test-specs/mcp/l2_remote-mcp-connection-status-indicator_ELITEA-1936.md)

Seeds a Remote MCP pointing at the public DeepWiki MCP server, then drives the
case: the MCP list carries no connection badge (case-text drift, see below),
the detail page shows ``Not Connected`` with an enabled ``Login`` button, and
clicking Login performs a real connection check that flips the indicator to
``Connected!`` with the button becoming ``Logout``.

Case-text drift, asserted as an ABSENCE rather than dropped (reverse-masking
guard, .agents/testing.md): case step 2 requires every Remote MCP list card to
render a ``Disconnected`` connection badge. **No such badge exists in the
product** — verified live across the whole list and in EliteaUI source; the
connection status lives only on the detail page. Filed as a CLARIFICATION,
EliteaAI/elitea-testing-public#1723. The live product is correct and the case
text is stale, so step 2 asserts the absence and keeps the claim guarded.

Fidelity: no substitution. The status text, the button label, the absence of a
card badge and the sessionStorage connection record are all produced by the
system, against a real MCP server over a real socket round-trip. Step 7's
sessionStorage check is a READ of state the product wrote — nothing is
injected (see ``McpFormPage.get_mcp_connection_record``).

Isolation: the product's connection record lives in ``sessionStorage`` keyed by
SERVER URL, not by toolkit — so a unique toolkit name does NOT isolate this
test. The framework's ``page`` fixture opens a FRESH browser context per test,
which starts with empty sessionStorage and gives step 4's ``Not Connected``
baseline its honesty.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

# Must be a REAL, reachable, auth-free MCP server: steps 5-7 require the
# connection check to genuinely succeed. A placeholder URL would leave the
# indicator at "Not Connected" forever (test-specs/mcp/_surface.md § Fixtures).
DEEPWIKI_MCP_URL = "https://mcp.deepwiki.com/mcp"

# Connection-state strings the case expects on a list CARD. None of them is
# rendered there — see the module docstring and clarification #1723.
CONNECTION_STATE_STRINGS = ("Disconnected", "Not Connected", "Connected!")


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1936_remote-mcp-connection-status-indicator.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_connection_status_indicator(page, toolkit_api: ToolkitAPI):
    """The Remote MCP detail page shows Not Connected, and Login flips it to Connected!."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    mcp_list = McpListPage(page)

    # ---- Setup (transit, NOT a case step) -------------------------------
    # The case allows any pre-existing Remote MCP; a freshly seeded one against
    # the DeepWiki fixture makes step 4's "Not Connected" baseline deterministic
    # and gives step 2 a card whose name this test controls.
    form.navigate_to_create()
    form.select_remote_mcp_type()
    # MAX_NAME_LENGTH=32 truncates silently — "autotest_conn_status_" is 21
    # chars, +4 hex = 25. Safe.
    toolkit_name = f"autotest_conn_status_{uuid.uuid4().hex[:4]}"
    form.fill_name(toolkit_name)
    form.fill_url(DEEPWIKI_MCP_URL)
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    try:
        with allure.step("Step 1 — Navigate to the MCP list page; the list loads"):
            mcp_list.navigate()
            mcp_list.wait_for_page_load()
            assert mcp_list.get_card_count() >= 1, (
                "At least one Remote MCP card should be present (the seeded one)"
            )
            assert toolkit_name in mcp_list.get_card_names(), (
                f"The seeded MCP {toolkit_name!r} should appear in the list"
            )

        with allure.step(
            "Step 2 — CLARIFICATION #1723: no Remote MCP card renders a connection-status badge"
        ):
            # The case expects every card to show a "Disconnected" badge. It does
            # not exist: a card's complete testid inventory is entity-card-icon,
            # entity-card-name, entity-card-tag-chip and mcp-pin-toggle-button-<id>,
            # and the tag chip carries the TYPE ("Remote"), not a connection state.
            # Asserting the case as written would reverse-mask a stale case text,
            # so the claim is inverted and kept test-enforced.
            card_texts = mcp_list.get_card_texts()
            assert card_texts, "Expected at least one rendered MCP card to inspect"
            offenders = [
                text
                for text in card_texts
                if any(state in text for state in CONNECTION_STATE_STRINGS)
            ]
            assert not offenders, (
                "No MCP list card should render a connection-status badge "
                f"(clarification #1723), but found: {offenders!r}"
            )
            assert mcp_list.get_card_type_badge_text(toolkit_name).strip() == "Remote", (
                "The only chip on an MCP card is the TYPE badge, got: "
                f"{mcp_list.get_card_type_badge_text(toolkit_name)!r}"
            )

        with allure.step("Step 3 — Open the Remote MCP detail page"):
            # open_card_by_name() does NOT wait for the destination page — always
            # follow it with wait_for_page_load() (test-specs/mcp/_surface.md).
            mcp_list.open_card_by_name(toolkit_name)
            form.wait_for_page_load()
            expect(form.detail_title).to_have_text(toolkit_name)

        with allure.step(
            "Step 4 — The connection-status area shows 'Not Connected' with a 'Login' button"
        ):
            expect(form.connection_status).to_have_text("Not Connected")
            expect(form.login_button).to_be_visible()
            expect(form.login_button).to_have_text("Login")
            # Analyst addition (AFS Axis 2): isButtonDisabled is a real derived
            # state (!canLogin || isRunning || patInvalid) — a regression that
            # rendered the button permanently disabled would satisfy the case's
            # literal "Login button is present" while making the feature unusable.
            expect(form.login_button).to_be_enabled()
            # Analyst addition (AFS Axis 2): the case demands "with icon", but
            # attaches it to the card badge that does not exist. The icon genuinely
            # lives here, next to the status text.
            expect(form.connection_status_icon).to_be_visible()

        with allure.step("Step 5 — Click the 'Login' button; the connection flow initiates"):
            # For a server that needs no OAuth this is an in-page socket
            # test_mcp_connection round-trip — no external window, no redirect.
            form.click_connection_login()

        with allure.step("Step 6 — The connection flow completes without error"):
            # The transient "Logging in..." label is deliberately NOT asserted:
            # the DeepWiki round-trip completes faster than a 500 ms poll, so
            # asserting it would be a guaranteed flake. Assert the terminal state.
            expect(form.login_button).to_have_text("Logout")
            # useMcpAuthCheck routes error socket frames to toastError — without
            # this, a run where the check errored but the label happened to be
            # stale would pass (AFS Axis 2).
            expect(form.sync_error_toast_message).to_have_count(0)

        with allure.step("Step 7 — The status changes to 'Connected!'"):
            # The product literal carries a trailing "!" (McpAuthStatus.jsx); the
            # case text says "Connected". Assert the product's literal.
            expect(form.connection_status).to_have_text("Connected!")
            expect(form.login_button).to_have_text("Logout")
            # Analyst addition (AFS Axis 2): the product's OWN durable record of
            # the verified connection, as opposed to a label flipped
            # optimistically. Read-only observation, never a write.
            record = form.get_mcp_connection_record(DEEPWIKI_MCP_URL)
            assert record is not None, (
                "The product should have written a sessionStorage connection record "
                f"for {DEEPWIKI_MCP_URL!r} after a successful check"
            )
            assert record.get("connection_verified") is True, (
                f"The connection record should be marked verified, got: {record!r}"
            )
            assert record.get("access_token") == "__connection_verified__", (
                f"The connection record should carry the verified-connection marker, got: {record!r}"
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above (AFS § Cleanup).
        # sessionStorage needs no explicit clearing: the `page` fixture's browser
        # context closes with the test, taking the connection record with it.
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )
