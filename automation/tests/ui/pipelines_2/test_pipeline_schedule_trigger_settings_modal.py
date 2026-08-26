"""UI test — Entry Point Node: Schedule Trigger Settings Modal.

TMS: ELITEA-2007
(test-specs/pipelines/l3_entry-point-schedule-trigger-settings-modal_ELITEA-2007.md)

Selects "Schedule" from the entry-point node's Trigger dropdown, verifies the
Schedule settings modal opens with all fields present immediately (no timing
gap, unlike the Webhook modal), drives the Default-mode Every/hour/minute
controls (including the hour/minute multi-select-checkbox uncheck-then-check
mechanics), verifies the Summary line re-derives dynamically, exercises the
Default <-> Advanced mode switch (raw cron text input), applies, and confirms
the schedule survives a full page reload with the saved cron round-tripping
back into the modal on reopen.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipeline_helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
MODAL_TIMEOUT = 10_000


def _is_known_1021_warning(msg) -> bool:
    """Filter the react-js-cron/antd console noise the Schedule modal emits on open.

    Filed as EliteaAI/elitea-testing-public#1021 — see
    test_pipeline_entry_point_trigger_types_persist.py for the full note.
    Not this case's own concern (third-party library internals), so filtered
    like #291/#554 rather than soft-tracked.
    """
    text = msg.text
    return (
        "popupClassName" in text
        or ("dropdownAlign" in text and "does not recognize" in text)
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2007_entry-point-schedule-trigger-settings-modal.md",
    "onetest-ai Test Case link",
)
def test_schedule_trigger_settings_modal(page, pipeline_with_llm_id):
    """Schedule settings modal: Default/Advanced modes, dynamic summary, and persistence."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1021_warning(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify single entry-point node"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            "Pipeline should be ready with the LLM node as the single entry-point node"
        )

    with allure.step('Step 2 — Select "Schedule" from the Trigger dropdown'):
        schedule_response = pipeline_page.select_trigger_type("schedule", timeout=UI_ELEMENT_TIMEOUT)
        assert schedule_response is None, (
            "Selecting Schedule should NOT auto-save (no PUT until the modal's own Apply, "
            "unlike Webhook's immediate PUT)"
        )

    with allure.step(
        "Step 3 — Verify the Schedule settings modal opens with all listed elements, present immediately"
    ):
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)

        summary_text = pipeline_page.get_schedule_summary_text()
        assert "00:00" in summary_text and "Saturday" in summary_text, (
            f"Schedule modal should default to 'At 00:00, only on Saturday', got {summary_text!r}"
        )
        # Mode radio has no visible group heading (RadioButtonGroup.jsx drops
        # the `label` prop it's given — AFS CLARIFICATION, not a defect) — the
        # two option labels are the reliable handle.
        assert pipeline_page.schedule_mode_radio_default.is_visible(), "Mode radio 'Default' option should be visible"
        assert pipeline_page.schedule_mode_radio_advanced.is_visible(), (
            "Mode radio 'Advanced' option should be visible"
        )
        assert pipeline_page.get_schedule_cron_select_count() == 4, (
            "Default mode should show 4 react-js-cron selects (week/on/hour/minute) for the default 'week' period"
        )
        assert pipeline_page.schedule_modal_cancel_button.is_visible(), "Cancel button should be visible"
        assert pipeline_page.schedule_modal_apply_button.is_visible(), "Apply button should be visible"

    with allure.step('Step 4 — Change "Every" to "day"; verify the "on" field hides'):
        # The Every/on/hour/minute controls are third-party `react-js-cron`
        # (ant-design) widgets — sanctioned #579 raw-handle exception, scoped
        # to the testid'd schedule_modal root (AFS Concrete Handles).
        every_select = pipeline_page.schedule_modal.locator(pipeline_page.SCHEDULE_CRON_SELECT).first
        every_select.click(timeout=UI_ELEMENT_TIMEOUT)
        # The open dropdown is antd's own `.ant-select-dropdown` (NOT
        # role="presentation" — confirmed live via DOM dump), each row an
        # `.ant-select-item-option` — same class family the hour/minute
        # popovers use (page object's CRON_DROPDOWN_OPTION constant).
        day_option = pipeline_page.page.locator(pipeline_page.CRON_DROPDOWN).locator(
            pipeline_page.CRON_DROPDOWN_OPTION.format("day")
        )
        day_option.click(timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_schedule_cron_select_count() == 3, (
            "The 'on' (day-of-week) selector should be entirely removed from the DOM for 'day' period"
        )
        summary_after_day = pipeline_page.get_schedule_summary_text()
        assert "Saturday" not in summary_after_day, (
            f"Summary's 'only on Saturday' clause should drop for the daily period, got {summary_after_day!r}"
        )

    with allure.step('Step 5 — Change hour to "09", minute to "30"; verify the Summary updates'):
        pipeline_page.set_schedule_hour_minute("09", "30", timeout=UI_ELEMENT_TIMEOUT)

        summary_after_time = pipeline_page.get_schedule_summary_text()
        # UI intentionally adds quotes around the summary message
        assert summary_after_time == '"At 09:30"', (
            f'Summary should show "At 09:30" (with quotes), got {summary_after_time!r}'
        )

    with allure.step('Step 6 — Switch to "Advanced" mode; verify the raw cron text input appears'):
        pipeline_page.schedule_mode_radio_advanced.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.schedule_cron_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

        cron_value = pipeline_page.schedule_cron_input.input_value()
        assert cron_value.split()[0] == "30" and cron_value.split()[1] == "9", (
            f"Advanced-mode cron input should carry over the Default-mode 09:30 value, got {cron_value!r}"
        )

    with allure.step('Step 7 — Switch back to "Default" mode; verify the dropdowns return'):
        pipeline_page.schedule_mode_radio_default.click(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_schedule_cron_select_count() == 3, (
            "Default-mode dropdowns should re-render, re-parsed from the same cron string (day period, no 'on')"
        )
        summary_after_switch_back = pipeline_page.get_schedule_summary_text()
        # UI intentionally adds quotes around the summary message
        assert summary_after_switch_back == '"At 09:30"', (
            f'Summary should still show "At 09:30" (with quotes) after switching modes both directions, '
            f"got {summary_after_switch_back!r}"
        )

    with allure.step('Step 8 — Click "Apply"; verify modal closes and Trigger shows "Schedule"'):
        apply_response = pipeline_page.apply_schedule_settings(timeout=MODAL_TIMEOUT)
        assert apply_response is not None and apply_response.get("type") == "schedule", (
            f"Apply should persist type=schedule server-side, got {apply_response!r}"
        )
        # Cron fields drop leading zeros (hour "09" -> "9"); minute+hour are
        # the first two space-separated fields.
        persisted_minute, persisted_hour = apply_response.get("cron", "").split()[:2]
        assert persisted_minute == "30" and persisted_hour == "9", (
            f"Persisted cron should carry the 09:30 values, got {apply_response!r}"
        )
        assert not pipeline_page.schedule_modal.is_visible(), "Schedule modal should be closed after Apply"

        # Immediate-read staleness risk documented in the AFS's shared §
        # Quirks — poll via auto-retrying expect rather than a bare
        # same-tick read.
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=MODAL_TIMEOUT)

    with allure.step("Step 9 — Save is a no-op (disabled); reload; verify the Schedule trigger persists"):
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled — schedule config persists via its own endpoint, "
            "independent of the pipeline's own Formik-tracked form state"
        )

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # currentTriggerType falls back to its "chat_message" default while
        # the post-reload GET .../trigger refetch is still in flight — poll
        # instead of reading same-tick (AFS § Quirks, same as ELITEA-2005/2006).
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=UI_ELEMENT_TIMEOUT)

        # The saved cron round-trips, not just the trigger `type` string.
        pipeline_page.trigger_schedule_edit_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)
        persisted_summary = pipeline_page.get_schedule_summary_text()
        # UI intentionally adds quotes around the summary message
        assert persisted_summary == '"At 09:30"', (
            f'Reopened Schedule modal should show "At 09:30" (with quotes) round-tripped cron, got {persisted_summary!r}'
        )
        pipeline_page.schedule_modal_cancel_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.schedule_modal.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    assert not console_errors, (
        f"Configuring the schedule trigger should not introduce console errors: "
        f"{[m.text for m in console_errors]}"
    )
