"""UI test — discard unsaved edits on a Remote MCP's detail page.

TMS: ELITEA-1928 (test-specs/mcp/l1_edit-remote-mcp-discard-changes_ELITEA-1928.md)

Edits the Description field on a Remote MCP's detail page, confirms Save and
Discard become enabled, clicks Discard, confirms the warning modal, and verifies
the description reverts to its original value with both buttons disabled again —
and that nothing was persisted (no update PUT is issued, and the original value
survives a full reload).

No substitution of the system under test is performed: every asserted value is
produced by the product (the rendered field, the rendered buttons, the modal's own
text, the browser's real network log). The only deviation from the case text is the
*test data* — the case assumes a pre-existing Remote MCP, which cannot be
discovered at runtime on this environment (see the AFS § Test Data), so a
disposable MCP is seeded through the real UI create flow and deleted in teardown.
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

ORIGINAL_DESCRIPTION = "Original description for discard case"
# Verbatim from the case's Test Data table.
TEMPORARY_DESCRIPTION = "This should be discarded"
DISCARD_WARNING_TEXT = "Are you sure you want to discard changes?"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1928_edit-remote-mcp-discard-changes.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_discard_changes(page, toolkit_api: ToolkitAPI):
    """Unsaved description edits are reverted by Discard; buttons reset and nothing is saved."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data:
    # generate-shared-with-cleanup). ToolkitAPI.list_all_toolkits() returns an
    # empty list on this environment regardless of auth method (documented
    # quirk — see config.py's remote_github_mcp_toolkit_id comment), so an
    # existing MCP's id cannot be rediscovered at runtime. Seeded with a
    # NON-EMPTY description so the case's "reverts to the original value" is an
    # observable revert rather than a revert-to-empty.
    # MAX_NAME_LENGTH = 32 truncates the Toolkit Name field client-side — this
    # name is 27 chars.
    toolkit_name = f"autotest_mcp_discard_{uuid.uuid4().hex[:6]}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    form.fill_description(ORIGINAL_DESCRIPTION)
    # Stored only — this case never clicks Load Tools, so the URL is never dialled.
    form.fill_url("https://mcp.example.com/sse")
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — same pattern as the sibling test_mcp_edit_name.py /
    # test_mcp_edit_toggle_enable_caching.py specs: capture "error"-type console
    # messages, filter the two pre-existing React dev-mode warnings tracked in
    # EliteaAI/elitea-testing-public#291, and soft-fail (never silently drop) the
    # known #549 MUI Tabs warning, so a genuine regression in this discard flow
    # can't hide behind an already-tracked warning (case Pass criterion: "All
    # steps complete without errors").
    console_messages = []
    soft_failures = []

    def _is_known_291_warning(msg) -> bool:
        text = msg.text
        return (
            'unique "key" prop' in text
            or ("validateDOMNesting" in text and "<p>" in text)
            or ("validateDOMNesting" in text and "%s" in text)
        )

    def _is_known_549_warning(msg) -> bool:
        return "Tabs component is invalid" in msg.text

    page.on(
        "console",
        lambda msg: console_messages.append(msg)
        if msg.type == "error" and not _is_known_291_warning(msg)
        else None,
    )

    def _check_no_new_console_errors(step_label: str) -> None:
        """Split captured console errors: known #549 -> soft; anything else -> hard fail."""
        new_549 = [m for m in console_messages if _is_known_549_warning(m)]
        unexpected = [m for m in console_messages if not _is_known_549_warning(m)]
        for msg in new_549:
            soft_failures.append(
                "Known defect github.com/EliteaAI/elitea-testing-public/issues/549: "
                f"{step_label} — MUI Tabs invalid-value console error: {msg.text!r}"
            )
        assert not unexpected, (
            f"{step_label} — unexpected new console errors beyond the two "
            "pre-existing dev-mode warnings tracked in #291 and the known "
            f"#549 Tabs warning, got: {[m.text for m in unexpected]}"
        )
        console_messages.clear()

    # Absence-of-request guard for the case's Expected Final State ("all unsaved
    # changes are discarded"): a UI revert alone would not prove nothing reached
    # the server. The listener is registered BEFORE the edit that could trigger a
    # save and is asserted after the discard completes, so it genuinely spans the
    # whole window in which a PUT could have fired.
    update_puts = []
    page.on(
        "request",
        lambda request: update_puts.append(request.url)
        if request.method == "PUT" and f"/tool/prompt_lib/{project_id}/{toolkit_id}" in request.url
        else None,
    )

    try:
        with allure.step("Step 1 — Open the Remote MCP detail page in Form view"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )
            assert form.get_detail_heading_text() == toolkit_name, (
                f"Detail title should show the toolkit's name, "
                f"got: {form.get_detail_heading_text()!r}"
            )

        with allure.step("Step 2 — Note the current description value"):
            # The Description field renders INLINE on the detail page (it goes
            # through NameDescriptionInput.jsx, not the collapsed schema-driven
            # ToolBaseProperty.jsx section) — no expand_configuration_section()
            # is needed here.
            assert form.description_input.input_value() == ORIGINAL_DESCRIPTION, (
                f"Description should hold the seeded original value, "
                f"got: {form.description_input.input_value()!r}"
            )
            # Pristine baseline for Step 4: both buttons gate on
            # `isFormDirtyExcluding` (ToolkitsTabBarContainer.jsx:150,158-161),
            # so without this baseline "become enabled" proves nothing.
            assert form.detail_save_button.is_disabled(), (
                "Save should be disabled on a pristine detail form"
            )
            assert form.detail_discard_button.is_disabled(), (
                "Discard should be disabled on a pristine detail form"
            )

        with allure.step(f"Step 3 — Change the description to {TEMPORARY_DESCRIPTION!r}"):
            form.fill_description(TEMPORARY_DESCRIPTION)
            assert form.description_input.input_value() == TEMPORARY_DESCRIPTION, (
                f"Description field should display the temporary value, "
                f"got: {form.description_input.input_value()!r}"
            )

        with allure.step("Step 4 — Verify Save and Discard buttons become enabled"):
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once the form is dirty"
            )
            assert not form.detail_discard_button.is_disabled(), (
                "Discard should be enabled once the form is dirty"
            )

        with allure.step("Step 5 — Click Discard"):
            # Discard is a two-step gesture: the first click only raises a
            # confirmation modal. Nothing reverts until it is confirmed —
            # asserted below before confirming, so a future product change that
            # silently reverts on the first click cannot pass unnoticed.
            form.click_discard()
            assert DISCARD_WARNING_TEXT in form.get_discard_confirm_message(), (
                f"Discard should raise the discard-changes warning modal, "
                f"got: {form.get_discard_confirm_message()!r}"
            )
            assert form.description_input.input_value() == TEMPORARY_DESCRIPTION, (
                "Description should still hold the temporary value while the "
                "confirmation modal is open"
            )
            form.confirm_discard()

        with allure.step("Step 6 — Verify the description reverts to the original value"):
            expect(form.description_input).to_have_value(ORIGINAL_DESCRIPTION)

        with allure.step("Step 7 — Verify Save and Discard return to the disabled state"):
            assert form.detail_save_button.is_disabled(), (
                "Save should be disabled again after the changes are discarded"
            )
            assert form.detail_discard_button.is_disabled(), (
                "Discard should be disabled again after the changes are discarded"
            )
            _check_no_new_console_errors("Step 7 (after discard)")

        with allure.step(
            "Expected Final State — nothing was persisted (no update PUT; "
            "the original value survives a reload)"
        ):
            assert update_puts == [], (
                "Discarding changes must not issue an update request, "
                f"but these PUTs were sent: {update_puts!r}"
            )
            form.reload_and_wait()
            assert form.description_input.input_value() == ORIGINAL_DESCRIPTION, (
                f"Description should still read as the original after a full "
                f"reload, got: {form.description_input.input_value()!r}"
            )
            _check_no_new_console_errors("Expected Final State (reload)")

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known non-blocking product defect, "
                "not test/infrastructure — rest of the flow passed cleanly):\n"
                + "\n".join(soft_failures)
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above.
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )
