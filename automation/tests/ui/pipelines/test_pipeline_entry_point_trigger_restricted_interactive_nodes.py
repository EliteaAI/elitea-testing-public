"""UI test — Entry Point Node: schedule blocked when HITL/Printer/interrupts are present.

TMS: ELITEA-2008
(test-specs/pipelines/lextend_schedule-risk-block-on-new-schedule-page_ELITEA-2008.md)

EL-7011 moved scheduling out of the Trigger dropdown: the New Schedule page
("+ Schedule" in the SCHEDULES section) runs a risk check against the pipeline's
LAST-SAVED version and, when it holds a Printer or HITL node, shows the blocking
risk box, disables Save and shows the "Fix the risk check to save" hint. The
restriction is keyed on the saved YAML, not the live canvas. Removing every
restricting element and saving lifts it.

Known defect #2984: a saved non-empty interrupt_before is NOT flagged by the risk
check (DEV returns `blocking: []`). That step asserts the CORRECT behaviour with a
soft assertion and is RED BY DESIGN until the product ships the fix.

The entry-point Trigger dropdown now offers only "Chat Message" (Webhook left it
too); Step 1 asserts that live contract. The old Webhook-disabled checks cannot
hold on DEV and are pending a lead ruling (reported in the Run Report).
"""

import logging

import allure
import pytest
from config import settings
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

from pages.schedule_form_page import ScheduleFormPage
from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
CHAT_MESSAGE_ONLY_ENABLED = {"chat_message": True}
RISK_INTRO = "This pipeline asks a person for input"
RISK_LINES = (
    "Scheduled runs can't answer it.",
    "You can't save this schedule.",
    "Remove the human-input step, or run the pipeline from the chat.",
    "Open pipeline to change steps",
)


def _assert_blocked(form, label, soft=None):
    """The New Schedule page shows the blocking risk box, a disabled Save and the hint."""
    checks = soft if soft is not None else None

    def _check(cond, msg):
        if checks is None:
            assert cond, msg
        elif not cond:
            checks.append(msg)

    _check(form.risk_block_box.count() == 1, f"{label}: risk block box should be shown")
    if form.risk_block_box.count() == 1:
        text = form.get_risk_block_text()
        _check(RISK_INTRO in text, f"{label}: box should say {RISK_INTRO!r}, got {text!r}")
        for line in RISK_LINES:
            _check(line in text, f"{label}: box should contain {line!r}, got {text!r}")
    _check(form.save_button.is_disabled(), f"{label}: Save should be disabled")
    _check(
        form.risk_hint.count() == 1 and "Fix the risk check to save" in (form.risk_hint.text_content() or ""),
        f"{label}: hint 'Fix the risk check to save' should be shown",
    )


def _assert_not_blocked(form, label):
    assert form.risk_block_box.count() == 0, f"{label}: no risk box expected"
    expect(form.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
    assert form.risk_hint.count() == 0, f"{label}: no risk hint expected"


@pytest.mark.tms("ELITEA-2008")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2008_entry-point-node-trigger-restricted-hitl-printer.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_restricted_interactive_nodes(page, pipeline_with_llm_id):
    """Schedule creation is blocked by a SAVED Printer/HITL node (and interrupt - #2984), keyed on the saved version."""
    project_id = str(settings.elitea_project_id)
    console_errors = collect_console_errors(page)
    soft_failures: list[str] = []
    form = ScheduleFormPage(page)

    with allure.step("Step 1 — Navigate to the fresh pipeline; baseline: no risk box on the New Schedule page"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.dismiss_announcement_dialog_if_present()
        baseline_states = pipeline_page.get_trigger_option_states(
            timeout=UI_ELEMENT_TIMEOUT, entry_point_node_id=llm_node_id
        )
        assert baseline_states == CHAT_MESSAGE_ONLY_ENABLED, (
            f"Trigger dropdown should offer only an enabled Chat Message on DEV, got {baseline_states!r}"
        )
        form.open_from_pipeline(pipeline_page)
        _assert_not_blocked(form, "baseline")
        form.cancel()
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()

    with allure.step("Step 2 — Add a Printer node (unconnected); verify it exists on canvas"):
        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert printer_node_id in pipeline_page.get_node_ids(), "Printer node should be on the canvas after add_node"

    with allure.step("Step 3 — WITHOUT saving, open New Schedule; verify the restriction does NOT apply yet"):
        # Risk check is keyed on the saved version, not the live canvas.
        form.open_from_pipeline(pipeline_page)
        _assert_not_blocked(form, "unsaved Printer")
        form.cancel()
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        if printer_node_id not in pipeline_page.get_node_ids():
            pipeline_page.add_node("Printer")
            printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 4 — Save the pipeline"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the updated pipeline version"

    with allure.step("Step 5 — Open New Schedule; verify the Printer blocks it (box, Save disabled, hint) and survives reload"):
        form.open_from_pipeline(pipeline_page)
        _assert_blocked(form, "saved Printer")
        form.cancel()
        pipeline_page.wait_for_detail_page_load()
        page.goto(page.url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 6 — Remove Printer, add a HITL node; Save; verify the same block (and the link opens the editor)"):
        pipeline_page.dismiss_announcement_dialog_if_present()
        pipeline_page.delete_node(printer_node_id)
        pipeline_page.add_node("Human-in-the-loop")
        hitl_node_id = pipeline_page.wait_for_node_on_canvas("hitl", timeout=UI_ELEMENT_TIMEOUT)
        assert hitl_node_id in pipeline_page.get_node_ids(), "HITL node should be on the canvas after add_node"
        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        form.open_from_pipeline(pipeline_page)
        _assert_blocked(form, "saved HITL")
        with page.context.expect_page() as popup_info:
            form.risk_open_pipeline_link.within(form.risk_block_box).click(timeout=UI_ELEMENT_TIMEOUT)
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")
        assert f"/pipelines/all/{pipeline_with_llm_id}" in popup.url, (
            f"'Open pipeline to change steps' should open this pipeline's editor, got {popup.url!r}"
        )
        popup.close()
        form.cancel()
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()

    with allure.step(
        "Step 7 — Remove HITL; add a Code node with interrupt_before via YAML; Save; verify the same block"
    ):
        pipeline_page.dismiss_announcement_dialog_if_present()
        pipeline_page.delete_node(hitl_node_id)
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.set_interrupt_before_via_yaml(code_node_id)
        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        form.open_from_pipeline(pipeline_page)
        # Known defect: #2984 - the risk check does not flag a saved interrupt_before (blocking: []).
        _assert_blocked(form, "saved interrupt_before", soft=soft_failures)
        form.cancel()
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()

    with allure.step("Step 8 — Remove all restricting configuration; Save; reload; verify scheduling is unblocked"):
        pipeline_page.dismiss_announcement_dialog_if_present()
        pipeline_page.clear_interrupt_before_via_yaml()
        pipeline_page.delete_node(code_node_id)
        assert llm_node_id in pipeline_page.get_node_ids(), "The entry-point LLM node should remain after cleanup"
        pipeline_page.save_and_wait_for_update(project_id, pipeline_with_llm_id, timeout=SAVE_RESPONSE_TIMEOUT)
        page.goto(page.url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        form.open_from_pipeline(pipeline_page)
        _assert_not_blocked(form, "restored")

    assert not console_errors, (
        f"Exercising the schedule-restriction lifecycle should not introduce console errors: {console_errors}"
    )
    assert not soft_failures, "Known defect #2984 (and any other soft failures): " + "; ".join(soft_failures)
