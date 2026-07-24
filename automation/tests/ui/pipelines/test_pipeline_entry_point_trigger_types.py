"""UI test — Entry Point Node: Trigger Types (Chat Message, Schedule, Webhook).

TMS: ELITEA-2005
(test-specs/pipelines/l3_entry-point-node-trigger-types_ELITEA-2005.md)

Verifies the entry-point node's Trigger dropdown exposes exactly the three
trigger types (Chat Message default, Schedule, Webhook), that each type
persists correctly across a pipeline Save + full page reload, and that the
dropdown (with all 3 options) is available on ANY node type promoted to
entry point — not just the node type used to explore the first steps.

This case's own Webhook step stays intentionally shallow (open -> GitHub
default -> Apply -> persisted); the Webhook settings modal's own internals
(type switching, URL/Secret fields) are ELITEA-2006's job
(test_pipeline_webhook_trigger_settings_modal.py), not re-litigated here.
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

    Newly discovered during this implementation, filed as
    EliteaAI/elitea-testing-public#1021: opening the Schedule settings modal
    (Step 7) deterministically fires two React console warnings entirely
    inside the third-party ``react-js-cron`` library's own antd ``Select``
    usage (an antd-version prop mismatch: ``popupClassName`` deprecation +
    an unrecognized ``dropdownAlign`` DOM prop) — not from any app-authored
    JSX in ``PipelineScheduleModal.jsx``. The modal's own functionality
    (cron defaults, Apply, persistence) is unaffected. Filtered like #291/#554
    (background noise unrelated to this case's own flow) rather than
    soft-tracked, per the same precedent established in
    ``test_credential_search_by_name.py``.
    """
    text = msg.text
    return (
        "popupClassName" in text
        or ("dropdownAlign" in text and "does not recognize" in text)
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2005_entry-point-node-trigger-types.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_types(page, pipeline_with_llm_id):
    """All 3 trigger types are listed, selectable, persist, and travel with the entry point."""
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

    with allure.step('Step 2 — Verify the Trigger field is visible, defaulting to "Chat Message"'):
        assert pipeline_page.trigger_select.is_visible(), (
            "Trigger select should render on the entry-point node's card"
        )
        assert pipeline_page.get_trigger_type_value() == "Chat Message", (
            "Trigger should default to 'Chat Message'"
        )

    with allure.step("Step 3 — Open the Trigger dropdown; verify exactly 3 options"):
        pipeline_page.trigger_select.click(timeout=UI_ELEMENT_TIMEOUT)
        option_names = pipeline_page.get_open_listbox_option_names()
        assert option_names == ["Chat Message", "Schedule", "Webhook"], (
            f"Trigger dropdown should list exactly these 3 options in order, got {option_names!r}"
        )
        page.keyboard.press("Escape")

    with allure.step('Step 4 — Select "Webhook"; verify auto-save + settings modal opens defaulting to GitHub'):
        trigger_response = pipeline_page.select_trigger_type("webhook", timeout=UI_ELEMENT_TIMEOUT)
        assert trigger_response is not None and trigger_response.get("type") == "webhook", (
            f"Selecting Webhook should auto-save type=webhook server-side immediately, got {trigger_response!r}"
        )
        pipeline_page.wait_for_webhook_settings_loaded(timeout=MODAL_TIMEOUT)
        assert pipeline_page.get_selected_webhook_type() == "github", (
            "Webhook settings modal should default to Webhook Type = GitHub"
        )

    with allure.step('Step 5 — Click Apply in the Webhook modal; verify Trigger select shows "Webhook"'):
        apply_response = pipeline_page.apply_webhook_settings(timeout=MODAL_TIMEOUT)
        assert apply_response is not None and apply_response.get("type") == "webhook", (
            f"Apply should persist type=webhook server-side, got {apply_response!r}"
        )
        assert not pipeline_page.webhook_modal.is_visible(), "Webhook modal should be closed after Apply"

        trigger_value = pipeline_page.get_trigger_type_value()
        assert trigger_value == "Webhook", f"Trigger select should display 'Webhook', got {trigger_value!r}"

    with allure.step("Step 6 — Save the pipeline; reload; verify Trigger still shows 'Webhook'"):
        # Declared improvisation (role-overrides.md § Declared-improvisation
        # protocol) — same finding ELITEA-2006's implementer already made on
        # this identical fixture (test_pipeline_webhook_trigger_settings_modal.py):
        # trigger/webhook config is a separate server-side entity, persisted
        # immediately by its own PUT calls above, so the pipeline's own
        # Formik-tracked form is never dirtied and Save stays correctly
        # DISABLED. Reloading directly is what exercises this step's real
        # intent (does the already-persisted trigger survive a reload).
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled — trigger/webhook config persists via its own "
            "endpoint, independent of the pipeline's own Formik-tracked form state"
        )

        canonical_url = page.url  # carries ?viewMode=owner
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # Immediately after reload, currentTriggerType falls back to its
        # "chat_message" default while the GET .../pipeline_trigger/.../trigger
        # refetch is still in flight (TriggerTypeSelector.jsx:
        # `triggerData?.type || TRIGGER_TYPES.chat_message`) — same
        # cache-invalidation lag as the Apply-click lag noted in the AFS
        # Automation Hints, just triggered by navigation instead of a click.
        # Poll instead of reading same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Webhook", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 7 — Re-open Trigger, select "Schedule"; verify NO auto-save (unlike Webhook)'):
        # Axis 2 addition: Schedule has no pre-Apply auto-save, unlike
        # Webhook's — select_trigger_type("schedule") returns None (no PUT
        # fires on selection; source-confirmed handleTriggerTypeChange only
        # calls setIsScheduleModalOpen(true)) and the Trigger select's OWN
        # displayed text must still read the previous value ("Webhook")
        # behind the just-opened modal.
        schedule_response = pipeline_page.select_trigger_type("schedule", timeout=UI_ELEMENT_TIMEOUT)
        assert schedule_response is None, (
            "Selecting Schedule should NOT auto-save (no PUT until the modal's own Apply)"
        )
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)

        summary_text = pipeline_page.get_schedule_summary_text()
        assert "00:00" in summary_text and "Saturday" in summary_text, (
            f"Schedule modal should default to 'At 00:00, only on Saturday', got {summary_text!r}"
        )

        trigger_value_behind_modal = pipeline_page.get_trigger_type_value()
        assert trigger_value_behind_modal == "Webhook", (
            "Trigger select should still show the PREVIOUS value ('Webhook') behind the "
            f"open Schedule modal (no pre-Apply auto-save), got {trigger_value_behind_modal!r}"
        )

    with allure.step('Step 8 — Click Apply in the Schedule modal; verify Trigger updates to "Schedule"'):
        schedule_apply_response = pipeline_page.apply_schedule_settings(timeout=MODAL_TIMEOUT)
        assert schedule_apply_response is not None and schedule_apply_response.get("type") == "schedule", (
            f"Apply should persist type=schedule server-side, got {schedule_apply_response!r}"
        )
        assert not pipeline_page.schedule_modal.is_visible(), "Schedule modal should be closed after Apply"

        # The displayed text lags the mutation's cache-invalidation by up to
        # ~2s (Known Defects / Automation Hints) — Playwright's auto-retrying
        # expect().to_have_text() polls instead of asserting same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=MODAL_TIMEOUT)

    with allure.step("Step 9 — Save the pipeline; reload; verify Trigger shows 'Schedule'"):
        assert not pipeline_page.is_save_enabled(), (
            "Save should still be disabled — schedule config also persists via its own endpoint"
        )

        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # Same post-reload cache-invalidation lag as Step 6 — poll, don't
        # read same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 10 — Switch back to "Chat Message" (no modal); verify it saves directly'):
        chat_message_response = pipeline_page.select_trigger_type("chat_message", timeout=UI_ELEMENT_TIMEOUT)
        assert chat_message_response is not None and chat_message_response.get("type") == "chat_message", (
            f"Selecting Chat Message should auto-save type=chat_message server-side, got {chat_message_response!r}"
        )
        # Same toast-vs-display-update lag as Schedule's Apply — poll, don't
        # assert same-tick.
        expect(pipeline_page.trigger_select).to_have_text("Chat Message", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 11 — Add a Code node; make it the entry point; verify LLM's Trigger field disappears"
    ):
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.make_node_entrypoint(code_node_id, timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_entrypoint_node_id() == code_node_id, (
            f"'{code_node_id}' (Code node) should now be the pipeline's entry point"
        )
        # TriggerTypeSelector is rendered conditionally (isEntrypoint && ...),
        # page-wide-safe because only one node can be entry point at a time
        # (AFS Concrete Handles) — exactly one instance should exist, proving
        # the LLM node's own copy unmounted rather than a second one
        # appearing alongside a stale first.
        assert pipeline_page.trigger_select.count() == 1, (
            "Exactly one Trigger select should exist on the page — the previous entry-point "
            "node's (LLM) copy must disappear when a different node becomes the entry point"
        )

    with allure.step(
        "Step 12 — Observe the Code node's own Trigger field; verify same 3 options available"
    ):
        assert pipeline_page.get_trigger_type_value() == "Chat Message", (
            "Code node's Trigger should show the persisted 'Chat Message' value from Step 10"
        )
        pipeline_page.trigger_select.click(timeout=UI_ELEMENT_TIMEOUT)
        code_option_names = pipeline_page.get_open_listbox_option_names()
        assert code_option_names == ["Chat Message", "Schedule", "Webhook"], (
            "Trigger dropdown should list the same 3 options regardless of entry-point node "
            f"type, got {code_option_names!r}"
        )
        page.keyboard.press("Escape")

        assert not console_errors, (
            f"Configuring entry-point triggers should not introduce console errors: {console_errors}"
        )
