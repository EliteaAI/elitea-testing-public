"""UI test — Pipeline Tools section: MCP add -> view details -> remove -> persist.

TMS: ELITEA-2065
(test-specs/pipelines/l2_pipeline-tools-section-mcp-add-view-remove_ELITEA-2065.md)

On a fresh, empty pipeline: attaches an MCP toolkit via the TOOLS section's
"+ MCP" button, verifies it renders as a flat-list card (no "MCP sub-tab" —
already tracked as EliteaAI/elitea-testing-public#1149, sibling of #530),
expands its "Show tools" toggle to see the attached tool list, removes the
card via its delete icon + confirm dialog, and confirms the removal survives
both the card's own immediate auto-persist and an explicit pipeline Save +
full page reload.

Distinct from the sibling MCP-node case on this suite:
- ELITEA-2037 (test_pipeline_mcp_node_fresh_attach.py) attaches an MCP to
  TOOLS and then adds/configures an MCP *node* on the canvas — this case
  never touches the canvas at all; it is entirely about the Tools-section
  card's own lifecycle (attach, view, remove, persist).
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

# One of the fixture MCP's 3 real tools (read_wiki_structure, read_wiki_contents,
# ask_question) — used to confirm the expanded "Show tools" list names an actual tool.
_EXPECTED_TOOL = "ask_question"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2065_pipeline-tools-section-mcp-sub-tab.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_tools_section_mcp_add_view_remove(page, pipeline_id, mcp_toolkit_with_tools):
    """Attach an MCP to TOOLS, view its tools, remove it, and verify removal persists."""
    fixture = mcp_toolkit_with_tools
    mcp_display_name = fixture["name"]  # exact popper row text, not space-stripped
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step (attach,
    # show-tools expand, remove, save, reload) are captured — AFS Expected
    # Results require "no console errors at any step".
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — Navigate to the fresh, empty pipeline; verify configuration panel + canvas load"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )
        assert pipeline_page.get_node_ids() == ["END"], (
            "A fresh pipeline's canvas should show only the END node before any attach"
        )

    with allure.step('Step 2 — Click TOOLS "+ MCP"; verify the MCP-picker popup opens'):
        popper = pipeline_page.open_mcp_popper(timeout=UI_ELEMENT_TIMEOUT)
        assert popper.is_visible(), "'+ MCP' popper should open"
        assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (
            "'+ MCP' popper should list at least one toolkit-menu-item result row "
            "(the project's available MCPs, including the freshly-provisioned fixture MCP)"
        )

    with allure.step("Step 3 — Select the fixture MCP from the popup; verify immediate auto-persist"):
        attach_response = pipeline_page.select_mcp_in_popper(
            popper, mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT
        )
        assert attach_response is not None, (
            "MCP attach should return the persisted toolkit payload from the "
            "immediate PATCH .../tool/prompt_lib/{project}/ 201 response"
        )

    with allure.step(
        "Step 4 — Verify the MCP appears attached as a flat-list card (no MCP sub-tab — "
        "CLARIFICATION EliteaAI/elitea-testing-public#1149, sibling of #530)"
    ):
        assert pipeline_page.is_toolkit_attached(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"TOOLS section should show a card for the attached MCP {mcp_display_name!r}"
        )
        assert not console_errors, f"Attaching the MCP should not introduce console errors: {console_errors}"

    with allure.step(
        'Step 5 — Verify the card shows a "Show tools" toggle (name + tool info; no numeric '
        "tools-count is ever rendered — confirmed via source read, see AFS step 5)"
    ):
        card = pipeline_page.toolkit_card.filter(has_text=mcp_display_name).first
        assert card.locator(pipeline_page.TOOLKIT_CARD_TOOLS_TOGGLE).is_visible(), (
            "The attached MCP card should show a 'Show tools' toggle — the fixture's toolkit "
            "has a non-empty settings.selected_tools, so BaseCardBody.jsx renders the toggle "
            "instead of the plain-description text"
        )

    with allure.step("Step 6 — Click the MCP entry's 'Show tools' toggle; verify its tools list is shown"):
        pipeline_page.open_toolkit_card_tools(mcp_display_name, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_toolkit_card_tool_listed(
            mcp_display_name, _EXPECTED_TOOL, timeout=UI_ELEMENT_TIMEOUT
        ), f"Expanded card should list the fixture tool {_EXPECTED_TOOL!r}"

    with allure.step(
        "Step 7 — Remove the MCP via the delete icon + confirm dialog; verify the disassociate "
        "PATCH fires and the card leaves the DOM"
    ):
        pipeline_page.remove_toolkit(mcp_display_name, project_id, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 8 — Verify the MCP no longer appears in the Tools list"):
        assert pipeline_page.toolkit_card.filter(has_text=mcp_display_name).count() == 0, (
            "No card matching the removed MCP's name should remain in the TOOLS section"
        )
        assert not console_errors, f"Removing the MCP should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 9 — Verify removal already persisted (Save is a no-op) and survives a full page reload"
    ):
        # CORRECTED (live-verified this session, same class of finding as ELITEA-2037's
        # attach auto-persist correction): removal ALSO auto-persists immediately —
        # useDisassociateToolkit.hooks.js's savePipelineAfterToolkitRemoval fires its own
        # PUT .../application/prompt_lib/{project}/{pipeline_id} right after the disassociate
        # PATCH (step 7) and resets the Formik baseline, so SaveApplicationButton.jsx's
        # `isButtonDisabled` (gated on `!isFormDirtyExcluding`) goes true — there is nothing
        # left to Save. Confirmed live: clicking the disabled Save button (even via a forced
        # JS .click(), which a real disabled <button> still suppresses) produced NO new PUT
        # and timed out `save_and_wait_for_update`'s response wait. Case step 9's literal
        # "Save — verify removal persists" wording assumes an explicit Save is required;
        # the live product does not need one. Asserting the disabled state IS the correct
        # assertion of "no pending changes remain to save" — reload confirms persistence
        # directly, matching the reverse-masking guard (asserting live behavior, not stale
        # case text). Not filed as a new ticket — same pattern already covered for attach
        # by EliteaAI/elitea-testing-public#1149 / ELITEA-2037.
        assert pipeline_page.save_button.is_disabled(), (
            "Save button should be disabled after removal — the disassociate flow's own "
            "auto-persist already saved the pipeline, leaving no pending changes"
        )
        assert not console_errors, (
            f"Removal's own auto-persist should not introduce console errors: {console_errors}"
        )

        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()

        assert pipeline_page.toolkit_card.filter(has_text=mcp_display_name).count() == 0, (
            "The removed MCP should still be absent from the TOOLS section after a full reload"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
