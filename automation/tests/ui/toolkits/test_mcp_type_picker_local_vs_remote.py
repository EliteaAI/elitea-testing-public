"""UI test — MCP type picker: Local vs Remote sections, Documentation link, type filters.

TMS: ELITEA-1949 (test-specs/mcp/l2_mcp-type-selection-local-vs-remote-display_ELITEA-1949.md)

Read-only walk of ``/mcps/create``: the "Choose the MCP type" heading, the Local
section's empty-state message and its external Documentation link, the Remote MCP
type card, and the two client-side type-filter chips.

No substitution of the system under test is performed anywhere in this spec — it
navigates, reads rendered text/attributes and clicks two chips. Every asserted value
(heading text, empty-state copy, link href, card label, chip ``data-selected`` state,
no-results strings) is produced by the live product.

Case-text drift, asserted against the LIVE contract per the reverse-masking guard
(`.agents/testing.md` § Fidelity policy): the case's Step 7 expects "only the Local
section is visible" after selecting the Local filter. The product instead unmounts the
empty Local section entirely (``GroupedCategory.jsx`` keeps an empty category only while
nothing is selected) and renders the generic catalog "No MCPs found" state. That is
coherent-by-design, so this spec asserts what the product does and the wording fix is
tracked as clarification
github.com/EliteaAI/elitea-testing-public/issues/1742.
"""

import re

import allure
import pytest
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

HEADING_TEXT = "Choose the MCP type"
LOCAL_EMPTY_STATE_TEXT = (
    "Still no local MCP available. Follow creation guides in our Documentation."
)
# Verbatim from the case's Test Data table.
DOCUMENTATION_URL = "https://docs.elitea.ai/integrations/mcp/create-and-use-server-stdio"
REMOTE_CARD_LABEL = "Remote MCP"
NO_RESULTS_TITLE = "No MCPs found"
NO_RESULTS_DESCRIPTION = "Try adjusting your search terms"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1949_mcp-type-selection-local-vs-remote-display.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
class TestMcpTypePickerLocalVsRemote:
    """MCP type-picker page: section content, Documentation link and type filters."""

    def test_type_picker_sections_documentation_link_and_filters(self, page):
        """Both sections render as specified, the doc link is correct, and the filters filter."""
        form = McpFormPage(page)

        # Console listener — the case's Pass criterion is "All steps complete
        # without errors". /mcps/create emits one already-tracked React dev-mode
        # `key` warning on every mount (EliteaAI/elitea-testing-public#656) from
        # CategorySection.jsx; it is filtered EXACTLY (not blanket-disabled) so a
        # genuine regression in this flow still fails the test. Registered before
        # the navigation so it spans the whole flow, both filter clicks included.
        console_messages = []

        def _is_known_656_warning(msg) -> bool:
            return 'unique "key" prop' in msg.text

        page.on(
            "console",
            lambda msg: console_messages.append(msg)
            if msg.type == "error" and not _is_known_656_warning(msg)
            else None,
        )

        with allure.step("Step 1 — Navigate to the MCP creation page (/mcps/create)"):
            # The case writes /app/mcps/create; APP_PREFIX is empty on localhost
            # and "/app" on deployed envs, so the bare path is used and
            # settings.app_base_url injects the prefix per environment.
            form.navigate_to_create()
            expect(page).to_have_url(re.compile(r"/mcps/create$"))

        with allure.step(f"Step 2 — Verify the {HEADING_TEXT!r} heading is displayed"):
            expect(form.type_picker_heading).to_be_visible()
            expect(form.type_picker_heading).to_have_text(HEADING_TEXT)

        with allure.step("Step 3 — Verify the Local section's empty-state message"):
            expect(form.local_empty_state).to_have_text(LOCAL_EMPTY_STATE_TEXT)

        with allure.step(
            "Step 4 — Verify 'Documentation' is a link pointing at the stdio-server guide"
        ):
            # Asserted, never clicked: the link is target="_blank" to an external
            # site and the case only asks that it points at the right URL.
            expect(form.local_documentation_link).to_be_visible()
            expect(form.local_documentation_link).to_have_text("Documentation")
            expect(form.local_documentation_link).to_have_attribute("href", DOCUMENTATION_URL)
            expect(form.local_documentation_link).to_have_attribute("target", "_blank")

        with allure.step("Step 5 — Verify the Remote section shows the 'Remote MCP' card"):
            expect(form.remote_mcp_type_card).to_be_visible()
            expect(form.remote_mcp_type_card).to_have_text(REMOTE_CARD_LABEL)

        with allure.step("Step 6 — Verify both 'Local' and 'Remote' type filter chips are present"):
            local_chip = form.type_filter_chip("local")
            remote_chip = form.type_filter_chip("remote")
            expect(local_chip).to_be_visible()
            expect(local_chip).to_have_text("Local")
            expect(remote_chip).to_be_visible()
            expect(remote_chip).to_have_text("Remote")
            # Unfiltered baseline. Load-bearing beyond steps 7/8: the Local
            # empty-state placeholder asserted in step 3 only renders while
            # NOTHING is selected, so without this the page could have arrived
            # pre-filtered and steps 3-5 would mean something else.
            expect(local_chip).to_have_attribute("data-selected", "false")
            expect(remote_chip).to_have_attribute("data-selected", "false")

        with allure.step("Step 7 — Click the 'Local' filter"):
            form.click_type_filter("local")
            expect(local_chip).to_have_attribute("data-selected", "true")
            # LIVE CONTRACT, not the case text (clarification #1742): selecting
            # Local drops the empty Local section entirely rather than leaving it
            # as the only visible section, and the catalog falls through to its
            # generic no-results state. Elements are UNMOUNTED, not hidden.
            expect(form.no_results_title).to_have_text(NO_RESULTS_TITLE)
            expect(form.no_results_description).to_have_text(NO_RESULTS_DESCRIPTION)
            expect(form.remote_mcp_type_card).to_have_count(0)
            expect(form.local_empty_state).to_have_count(0)

        with allure.step("Step 8 — Click the 'Remote' filter"):
            form.click_type_filter("remote")
            expect(form.remote_mcp_type_card).to_be_visible()
            expect(form.remote_mcp_type_card).to_have_text(REMOTE_CARD_LABEL)
            expect(form.local_empty_state).to_have_count(0)
            expect(form.no_results_title).to_have_count(0)
            # The chips are MULTI-SELECT and this surface has no "clear all", so
            # after the case's literal 7 -> 8 sequence BOTH chips are lit. Step 8
            # passes today only because Local contributes no items; pinning the
            # multi-select fact means a future switch to single-select (or the
            # arrival of a Local MCP, question #1738) turns this red instead of
            # silently changing what step 8 verifies.
            expect(local_chip).to_have_attribute("data-selected", "true")
            expect(remote_chip).to_have_attribute("data-selected", "true")

        with allure.step(
            "Expected Final State — with ONLY the Remote filter selected, the Remote "
            "MCP card is shown and the Local section is hidden"
        ):
            # Deselect Local so the case's Expected Final State is asserted in its
            # clean form, proving step 8's outcome is genuinely "Remote filter
            # shows the Remote section" and not an artefact of the two-chip state.
            form.click_type_filter("local")
            expect(local_chip).to_have_attribute("data-selected", "false")
            expect(remote_chip).to_have_attribute("data-selected", "true")
            expect(form.remote_mcp_type_card).to_be_visible()
            expect(form.remote_mcp_type_card).to_have_text(REMOTE_CARD_LABEL)
            expect(form.local_empty_state).to_have_count(0)
            expect(form.no_results_title).to_have_count(0)

        with allure.step("Pass criterion — no unexpected console errors"):
            assert not console_messages, (
                "Unexpected console errors beyond the pre-existing #656 React "
                f"`key` warning, got: {[m.text for m in console_messages]}"
            )
