"""UI test — Entry Point Node: Schedule Trigger Settings Modal.

TMS: ELITEA-2007
(test-specs/pipelines/l3_schedule-trigger-settings-modal_ELITEA-2007.md)

Selects "Schedule" from the entry-point node's Trigger dropdown and deep-dives
the Schedule settings modal's own internals: Default/Advanced mode toggle, the
"Every" period select's cascading day/hour/minute fields (including the
hour/minute MULTI-select deselect-the-default discipline), the dynamic cron
summary text, value round-trip fidelity through the Default<->Advanced
toggle, and full persistence across Save + page reload (verified both via the
Trigger select's text and by re-opening the modal through the new "Edit
schedule" icon).

This case's sibling `test_pipeline_entry_point_trigger_types.py` (ELITEA-2005)
already covers the Schedule step shallowly (open -> default weekly-Saturday
cron -> Apply -> persisted); this test is the deep dive that case's AFS
explicitly defers, mirroring how ELITEA-2006 deep-dives the Webhook modal.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
MODAL_TIMEOUT = 10_000


def _is_known_1021_warning(msg) -> bool:
    """Filter the react-js-cron/antd console noise the Schedule modal emits on open.

    Filed as EliteaAI/elitea-testing-public#1021 (ELITEA-2005 implementer):
    opening the Schedule settings modal deterministically fires two React
    console warnings entirely inside the third-party ``react-js-cron``
    library's own antd ``Select`` usage (an antd-version prop mismatch:
    ``popupClassName`` deprecation + an unrecognized ``dropdownAlign`` DOM
    prop) — not from any app-authored JSX in ``PipelineScheduleModal.jsx``.
    The modal's own functionality (cron defaults, mode toggle, Apply,
    persistence) is unaffected. Filtered like #291/#554/#1021's own
    ELITEA-2005 test (background noise unrelated to this case's own flow).
    """
    text = msg.text
    return (
        "popupClassName" in text
        or ("dropdownAlign" in text and "does not recognize" in text)
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2007_entry-point-node-schedule-trigger-settings-modal.md",
    "onetest-ai Test Case link",
)
def test_schedule_trigger_settings_modal(page, pipeline_with_llm_id):
    """Schedule settings modal: Default/Advanced modes, dynamic summary, and persistence."""
    console_errors = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_1021_warning(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify single entry-point LLM node"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_node_count() == 2, (
            "Pipeline should have exactly one real node (LLM) + the always-present END node"
        )
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            f"'{llm_node_id}' should be the pipeline's single entry-point node"
        )

    with allure.step('Step 2 — Select "Schedule" from the Trigger dropdown; verify modal opens with all elements'):
        schedule_response = pipeline_page.select_trigger_type("schedule", timeout=UI_ELEMENT_TIMEOUT)
        assert schedule_response is None, (
            "Selecting Schedule should NOT auto-save (no PUT until the modal's own Apply)"
        )
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)

        assert pipeline_page.get_selected_schedule_mode() == "default", (
            "Schedule modal should default to Default mode"
        )
        summary_text = pipeline_page.get_schedule_summary_text()
        assert "00:00" in summary_text and "Saturday" in summary_text, (
            f"Schedule modal should default to 'At 00:00, only on Saturday', got {summary_text!r}"
        )
        assert pipeline_page.schedule_period_select.is_visible(), '"Every" period select should be visible'
        assert pipeline_page.schedule_week_days_select.is_visible(), (
            '"on" day-of-week select should be visible for the default "week" period'
        )
        assert pipeline_page.schedule_hours_select.is_visible(), "Hour select should be visible"
        assert pipeline_page.schedule_minutes_select.is_visible(), "Minute select should be visible"
        assert pipeline_page.schedule_cancel_button.is_visible(), "Cancel button should be visible"
        assert pipeline_page.schedule_apply_button.is_visible(), "Apply button should be visible"

    with allure.step('Step 3 — Change "Every" to "day"; verify the "on" day-of-week field hides'):
        pipeline_page.select_schedule_period("day", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.schedule_week_days_select.count() == 0, (
            'The "on" day-of-week field should be removed from the layout entirely '
            "(not just hidden) once period=day"
        )
        summary_text = pipeline_page.get_schedule_summary_text()
        assert summary_text == "At 00:00", f"Summary should update to 'At 00:00', got {summary_text!r}"

    with allure.step('Step 4 — Set hour to "09"; verify summary updates'):
        pipeline_page.set_schedule_hour("09", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_schedule_hour_value() == "09", (
            "Hour select should show exactly '09' after the deselect-the-default sequence"
        )
        summary_text = pipeline_page.get_schedule_summary_text()
        assert summary_text == "At 09:00", f"Summary should update to 'At 09:00', got {summary_text!r}"

    with allure.step('Step 5 — Set minute to "30"; verify summary updates to the live "At 09:30" string'):
        pipeline_page.set_schedule_minute("30", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_schedule_minute_value() == "30", (
            "Minute select should show exactly '30' after the deselect-the-default sequence"
        )
        # AFS CLARIFICATION (EliteaAI/elitea-testing-public#1013): the case's own
        # Test Data table names "At 09:30, every day" — the live product correctly
        # renders "At 09:30" (no day-qualifier suffix for the "day" period; the
        # qualifier only disambiguates periods that need it, e.g. week's "only on
        # Saturday"). Asserting the LIVE string per the reverse-masking guard.
        summary_text = pipeline_page.get_schedule_summary_text()
        assert summary_text == "At 09:30", f"Summary should read exactly 'At 09:30', got {summary_text!r}"

    with allure.step('Step 6 — Switch to "Advanced"; verify the cron input appears, pre-populated'):
        pipeline_page.select_schedule_mode("advanced", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_selected_schedule_mode() == "advanced"
        cron_expression = pipeline_page.get_schedule_cron_expression()
        assert cron_expression == "30 9 * * *", (
            f"Advanced cron input should be pre-populated from the Default-mode state "
            f"(day/09/30), got {cron_expression!r}"
        )
        # Summary heading stays live even in Advanced mode (reads from the same
        # cron expression state, not the Default-mode dropdowns specifically).
        summary_text = pipeline_page.get_schedule_summary_text()
        assert summary_text == "At 09:30", (
            f"Summary should remain 'At 09:30' while in Advanced mode, got {summary_text!r}"
        )

    with allure.step('Step 7 — Switch back to "Default" (without editing the cron text); verify no data loss'):
        pipeline_page.select_schedule_mode("default", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_selected_schedule_mode() == "default"

        # Axis 2 addition: verify the UNDERLYING dropdown values round-tripped
        # through Advanced mode with no data loss — not just the derived summary
        # text (a naive implementation could silently reset to a default cron on
        # mode switch and still show a plausible-looking summary).
        assert pipeline_page.get_schedule_period_value() == "day", (
            "Period select should still read 'day' after the Default<->Advanced round-trip"
        )
        assert pipeline_page.get_schedule_hour_value() == "09", (
            "Hour select should still read '09' after the Default<->Advanced round-trip"
        )
        assert pipeline_page.get_schedule_minute_value() == "30", (
            "Minute select should still read '30' after the Default<->Advanced round-trip"
        )
        summary_text = pipeline_page.get_schedule_summary_text()
        assert summary_text == "At 09:30", f"Summary should remain 'At 09:30', got {summary_text!r}"

    with allure.step('Step 8 — Click "Apply"; verify modal closes, Trigger eventually shows "Schedule"'):
        schedule_apply_response = pipeline_page.apply_schedule_settings(timeout=MODAL_TIMEOUT)
        assert schedule_apply_response is not None and schedule_apply_response.get("type") == "schedule", (
            f"Apply should persist type=schedule server-side, got {schedule_apply_response!r}"
        )
        assert not pipeline_page.schedule_modal.is_visible(), "Schedule modal should be closed after Apply"

        # The displayed text lags the mutation's cache-invalidation by up to
        # a few seconds (AFS Automation Hints, same mechanism ELITEA-2005's AFS
        # documented) — Playwright's auto-retrying expect().to_have_text() polls
        # instead of asserting same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=MODAL_TIMEOUT)

    with allure.step("Step 9 — Save the pipeline; reload; verify the Schedule trigger and its config persist"):
        # Declared improvisation (role-overrides.md § Declared-improvisation
        # protocol), same finding as ELITEA-2005/2006's implementers on this
        # identical fixture: trigger/schedule config is a separate server-side
        # entity, persisted immediately by its own PUT above, so the pipeline's
        # own Formik-tracked form is never dirtied and Save stays DISABLED.
        # Reloading directly is what exercises this step's real intent (does the
        # already-persisted schedule survive a reload).
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled — trigger/schedule config persists via its own "
            "endpoint, independent of the pipeline's own Formik-tracked form state"
        )

        canonical_url = page.url  # carries ?viewMode=owner
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # Same post-reload cache-invalidation lag as Step 8 — poll, don't read
        # same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=UI_ELEMENT_TIMEOUT)

        # Reopen the modal via the "Edit schedule" icon to confirm the FULL
        # Default-mode field state survived reload, not just the Trigger
        # select's label text (AFS Axis 2 — a regression could leave the
        # top-level trigger=schedule flag persisted while the modal silently
        # resets to its own default cron).
        pipeline_page.open_schedule_settings(timeout=MODAL_TIMEOUT)
        assert pipeline_page.get_selected_schedule_mode() == "default", (
            "Re-opened modal should still show Default mode"
        )
        assert pipeline_page.get_schedule_period_value() == "day", (
            "Re-opened modal's period select should still read 'day' after reload"
        )
        assert pipeline_page.get_schedule_hour_value() == "09", (
            "Re-opened modal's hour select should still read '09' after reload"
        )
        assert pipeline_page.get_schedule_minute_value() == "30", (
            "Re-opened modal's minute select should still read '30' after reload"
        )
        persisted_summary = pipeline_page.get_schedule_summary_text()
        assert persisted_summary == "At 09:30", (
            f"Re-opened modal's summary should read 'At 09:30' after reload, got {persisted_summary!r}"
        )
        pipeline_page.cancel_schedule_settings(timeout=UI_ELEMENT_TIMEOUT)

    assert not console_errors, (
        "Configuring/reloading/persisting the Schedule trigger should not introduce "
        f"console errors across the whole flow, got: {[m.text for m in console_errors]}"
    )
