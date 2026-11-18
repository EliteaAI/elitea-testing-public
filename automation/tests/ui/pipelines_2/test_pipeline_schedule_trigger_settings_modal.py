"""UI test — Entry Point Node: Schedule settings (SCHEDULES section / New Schedule page).

TMS: ELITEA-2007
(test-specs/pipelines/lextend_schedule-trigger-settings-modal-to-schedules-section_ELITEA-2007.md)

EL-7011 moved schedule creation out of the entry-point Trigger dropdown + modal
into the pipeline's SCHEDULES section ("+ Schedule" -> New Schedule page). Every
check of the original case is kept: no auto-save on open, the form elements,
"on" hiding for a daily period, the summary re-deriving for 09:30, the
Builder <-> Cron Expression round trip, save, and persistence after reload.
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
PAGE_TIMEOUT = 15_000


@pytest.mark.tms("ELITEA-2007")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2007_entry-point-node-schedule-trigger-settings-modal.md",
    "onetest-ai Test Case link",
)
def test_schedule_trigger_settings_modal(page, pipeline_with_llm_id):
    """New Schedule page: Builder/Cron modes, dynamic summary, save, and persistence on the pipeline's card."""
    project_id = str(settings.elitea_project_id)
    console_errors = collect_console_errors(page)
    pipe_puts = []
    page.on(
        "request",
        lambda r: pipe_puts.append(r.url)
        if r.method == "PUT" and f"/application/prompt_lib/{project_id}/{pipeline_with_llm_id}" in r.url
        else None,
    )

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify single entry-point node and empty SCHEDULES"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            "Pipeline should be ready with the LLM node as the single entry-point node"
        )
        pipeline_page.dismiss_announcement_dialog_if_present()
        expect(pipeline_page.schedules_add_button).to_be_visible(timeout=PAGE_TIMEOUT)

    with allure.step('Step 2 — Click "+ Schedule"; the New Schedule page opens without auto-saving the pipeline'):
        pipeline_page.open_new_schedule_page(timeout=PAGE_TIMEOUT)
        form = ScheduleFormPage(page)
        form.wait_until_ready(timeout=PAGE_TIMEOUT)
        assert "/schedules/create" in page.url, f"Expected the create-schedule URL, got {page.url!r}"
        expect(form.breadcrumb_current).to_have_text("New Schedule", timeout=UI_ELEMENT_TIMEOUT)
        assert not pipe_puts, f"Opening the schedule page must NOT auto-save the pipeline, saw PUTs: {pipe_puts}"

    with allure.step("Step 3 — Verify the page elements: summary, mode toggle, Every/on/hour/minute, Cancel, Save"):
        expect(form.locked_pipeline).to_contain_text("Pipeline", timeout=UI_ELEMENT_TIMEOUT)
        expect(form.version_select).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        summary = form.get_summary_text()
        assert summary == "Runs every week at 00:00 on Saturday.", (
            f"Schedule should default to 'Runs every week at 00:00 on Saturday.', got {summary!r}"
        )
        expect(form.builder_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(form.cron_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert form.get_cron_select_count() == 4, "Builder mode should show 4 selects (every/on/hour/minute) for 'week'"
        expect(form.cancel_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(form.save_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        schedule_name = f"sched-2007-{pipeline_with_llm_id}"
        form.fill_name(schedule_name)
        expect(form.save_button).to_be_enabled(timeout=PAGE_TIMEOUT)

    with allure.step('Step 4 — Change "Every" to "Day"; verify the "on" field is removed'):
        form.select_period("Day")
        expect(form.weekdays_select_week).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
        assert form.get_cron_select_count() == 3, "Only period/hour/minute selects should remain for 'Day'"
        assert form.get_summary_text() == "Runs every day at 00:00."

    with allure.step('Step 5 — Set hour "09", minute "30"; verify the summary updates'):
        form.set_hour_minute("09", "30")
        expect(form.summary_text).to_have_text("Runs every day at 09:30.", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 6 — Switch to Cron Expression; verify the raw cron input carries 09:30 over"):
        form.cron_button.click(timeout=UI_ELEMENT_TIMEOUT)
        expect(form.cron_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert form.get_cron_value().split()[:2] == ["30", "9"], (
            f"Cron input should carry over 09:30, got {form.get_cron_value()!r}"
        )

    with allure.step("Step 7 — Switch back to Builder; verify the selects return and the summary is unchanged"):
        form.builder_button.click(timeout=UI_ELEMENT_TIMEOUT)
        expect(form.period_select).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert form.get_cron_select_count() == 3, "Builder selects should re-render (period/hour/minute)"
        expect(form.summary_text).to_have_text("Runs every day at 09:30.", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 8 — Save; verify the schedule persists (201, cron 09:30) and the card appears"):
        created = form.save(project_id, timeout=PAGE_TIMEOUT)
        persisted_minute, persisted_hour = created.get("cron", "").split()[:2]
        assert (persisted_minute, persisted_hour) == ("30", "9"), f"Persisted cron should be 09:30, got {created!r}"
        assert created.get("enabled") is True, f"Schedule should be created enabled, got {created!r}"
        pipeline_page.wait_for_detail_page_load()
        assert "/schedules/create" not in page.url, "Save should navigate back to the pipeline, not stay on create"
        schedule_id = created["id"]
        assert pipeline_page.wait_for_schedule_card_rule(schedule_id) == "At 09:30"
        pipeline_page.expect_schedule_card_state(schedule_id, "Active", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 9 — Pipeline Save stays disabled; reload; verify the schedule card persists with 09:30"):
        assert not pipeline_page.is_save_enabled(), (
            "Pipeline Save should stay disabled — the schedule persists via its own endpoint"
        )
        page.goto(page.url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        assert pipeline_page.wait_for_schedule_card_rule(schedule_id) == "At 09:30", "Saved cron should round-trip after reload"

    assert not console_errors, (
        f"Configuring the schedule should not introduce console errors: {console_errors}"
    )
