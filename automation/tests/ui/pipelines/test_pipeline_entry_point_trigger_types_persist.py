"""UI test — Entry Point Node: Trigger Types (Chat Message, Schedule, Webhook).

TMS: ELITEA-2005
(test-specs/pipelines/l3_entry-point-trigger-types-persist_ELITEA-2005.md)

Verifies the entry-point node's Trigger dropdown exposes exactly the three
trigger types (Chat Message default, Schedule, Webhook), that every
trigger-type change persists through its own dedicated endpoint (independent
of the pipeline's general Save) and survives a full page reload, and that the
same Trigger control (with all 3 options) is available on ANY node type
promoted to entry point.

This case's own Webhook/Schedule steps stay intentionally shallow (open ->
default -> Apply -> persisted); the modals' own field internals are
ELITEA-2006 (Webhook)/ELITEA-2007 (Schedule)'s job, not re-litigated here.

Also covers TMS ELITEA-2041 (extend-existing, second test function below):
verifies the Trigger control is EXCLUSIVE to the entry-point node's own card
(absent on every non-entry node, tried for 2 node types simultaneously) and
that the Information section's own "Trigger:" row mirrors the entry node's
current selection.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
MODAL_TIMEOUT = 10_000


def _is_known_1021_warning(msg) -> bool:
    """Filter the react-js-cron/antd console noise the Schedule modal emits on open.

    Filed as EliteaAI/elitea-testing-public#1021: opening the Schedule
    settings modal deterministically fires two React console warnings
    entirely inside the third-party ``react-js-cron`` library's own antd
    ``Select`` usage (an antd-version prop mismatch: ``popupClassName``
    deprecation + an unrecognized ``dropdownAlign`` DOM prop) — not from any
    app-authored JSX in ``PipelineScheduleModal.jsx``. The modal's own
    functionality (cron defaults, Apply, persistence) is unaffected. Filtered
    like #291/#554 (background noise unrelated to this case's own flow)
    rather than soft-tracked, per the same precedent established in
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
    "ELITEA-2005_entry-point-trigger-types-persist.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_types_persist(page, pipeline_with_llm_id):
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

    with allure.step('Step 2 — Click the entry-point node; verify Trigger defaults to "Chat Message"'):
        assert pipeline_page.trigger_select.is_visible(), (
            "Trigger select should render on the entry-point node's card"
        )
        assert pipeline_page.get_trigger_type_value() == "Chat Message", (
            "Trigger should default to 'Chat Message'"
        )

    with allure.step("Step 3 — Open the Trigger dropdown; verify exactly 3 options in order"):
        pipeline_page.open_trigger_select(timeout=UI_ELEMENT_TIMEOUT)
        option_names = pipeline_page.get_open_listbox_option_names()
        assert option_names == ["Chat Message", "Schedule", "Webhook"], (
            f"Trigger dropdown should list exactly these 3 options in order, got {option_names!r}"
        )
        page.keyboard.press("Escape")

    with allure.step('Step 4 — Select "Webhook"; verify auto-save, settings modal opens, Apply persists'):
        trigger_response = pipeline_page.select_trigger_type("webhook", timeout=UI_ELEMENT_TIMEOUT)
        assert trigger_response is not None and trigger_response.get("type") == "webhook", (
            f"Selecting Webhook should auto-save type=webhook server-side immediately, got {trigger_response!r}"
        )
        pipeline_page.wait_for_webhook_settings_loaded(timeout=MODAL_TIMEOUT)

        apply_response = pipeline_page.apply_webhook_settings(timeout=MODAL_TIMEOUT)
        assert apply_response is not None and apply_response.get("type") == "webhook", (
            f"Apply should persist type=webhook server-side, got {apply_response!r}"
        )
        assert not pipeline_page.webhook_modal.is_visible(), "Webhook modal should be closed after Apply"
        expect(pipeline_page.trigger_select).to_have_text("Webhook", timeout=MODAL_TIMEOUT)

    with allure.step("Step 5 — Save is a no-op (disabled); reload; verify Trigger still shows 'Webhook'"):
        # Declared improvisation (role-overrides.md § Declared-improvisation
        # protocol, AFS Coverage Map row 5): trigger/webhook config is a
        # separate server-side entity persisted immediately by its own PUT
        # (Step 4 above), so the pipeline's own Formik-tracked form is never
        # dirtied and Save stays correctly DISABLED — confirmed live. There
        # is nothing pending to save; reloading directly is what exercises
        # this step's real intent (does the already-persisted trigger survive
        # a reload).
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled — trigger config persists via its own endpoint, "
            "independent of the pipeline's own Formik-tracked form state"
        )

        canonical_url = page.url  # carries ?viewMode=owner
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # currentTriggerType falls back to its "chat_message" default while
        # the post-reload GET .../trigger refetch is still in flight — poll
        # instead of reading same-tick (AFS § Quirks).
        expect(pipeline_page.trigger_select).to_have_text("Webhook", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 6 — Select "Schedule"; Apply with the modal default; verify Trigger updates'):
        schedule_response = pipeline_page.select_trigger_type("schedule", timeout=UI_ELEMENT_TIMEOUT)
        assert schedule_response is None, (
            "Selecting Schedule should NOT auto-save (no PUT until the modal's own Apply)"
        )
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)

        schedule_apply_response = pipeline_page.apply_schedule_settings(timeout=MODAL_TIMEOUT)
        assert schedule_apply_response is not None and schedule_apply_response.get("type") == "schedule", (
            f"Apply should persist type=schedule server-side, got {schedule_apply_response!r}"
        )
        assert not pipeline_page.schedule_modal.is_visible(), "Schedule modal should be closed after Apply"
        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=MODAL_TIMEOUT)

    with allure.step(
        "Step 7 — Reload; verify Trigger shows 'Schedule'; the clock icon reopens the Schedule modal"
    ):
        canonical_url = page.url
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        expect(pipeline_page.trigger_select).to_have_text("Schedule", timeout=UI_ELEMENT_TIMEOUT)

        # Confirms the saved CRON round-trips, not just the trigger `type`
        # string (only rendered while currentTriggerType === "schedule").
        pipeline_page.trigger_schedule_edit_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_schedule_settings_loaded(timeout=MODAL_TIMEOUT)
        summary_text = pipeline_page.get_schedule_summary_text()
        assert "00:00" in summary_text and "Saturday" in summary_text, (
            f"Reopened Schedule modal should show the round-tripped default cron, got {summary_text!r}"
        )
        pipeline_page.schedule_modal_cancel_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.schedule_modal.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 8 — Switch back to "Chat Message" from a genuinely different current value'):
        # Axis 2 addition (AFS): TriggerTypeSelector.jsx's handleTriggerTypeChange
        # short-circuits as a no-op when newType === currentTriggerType — driving
        # this from the CONFIRMED-Schedule state (right after Step 7's reload)
        # guarantees a real state transition, not a silent no-op.
        chat_message_response = pipeline_page.select_trigger_type("chat_message", timeout=UI_ELEMENT_TIMEOUT)
        assert chat_message_response is not None and chat_message_response.get("type") == "chat_message", (
            f"Selecting Chat Message should auto-save type=chat_message server-side, got {chat_message_response!r}"
        )
        expect(pipeline_page.trigger_select).to_have_text("Chat Message", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 9 — Add a Code node, make it the entry point; verify the same Trigger + 3 options render there"
    ):
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.make_node_entrypoint(code_node_id, timeout=UI_ELEMENT_TIMEOUT)

        assert pipeline_page.get_entrypoint_node_id() == code_node_id, (
            f"'{code_node_id}' (Code node) should now be the pipeline's entry point"
        )
        assert pipeline_page.trigger_select.count() == 1, (
            "Exactly one Trigger select should exist on the page — the previous entry-point "
            "node's (LLM) copy must disappear when a different node becomes the entry point"
        )
        assert pipeline_page.get_trigger_type_value() == "Chat Message", (
            "Code node's Trigger should show the persisted 'Chat Message' value from Step 8"
        )

        pipeline_page.open_trigger_select(timeout=UI_ELEMENT_TIMEOUT)
        code_option_names = pipeline_page.get_open_listbox_option_names()
        assert code_option_names == ["Chat Message", "Schedule", "Webhook"], (
            "Trigger dropdown should list the same 3 options regardless of entry-point node "
            f"type, got {code_option_names!r}"
        )
        page.keyboard.press("Escape")

    assert not console_errors, (
        f"Configuring entry-point triggers should not introduce console errors: "
        f"{[m.text for m in console_errors]}"
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2041_pipeline-entry-point-trigger-shown-only-on-entry-node.md",
    "onetest-ai Test Case link",
)
def test_entry_point_trigger_shown_only_on_entry_point_node(page, pipeline_with_llm_id):
    """Trigger control renders ONLY on the entry-point node; Information section mirrors it.

    TMS: ELITEA-2041
    (test-specs/pipelines/lextend_pipeline-entry-point-trigger-shown-only-on-entry-node_ELITEA-2041.md)
    """
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify the LLM entry node has a Trigger control"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            f"'{llm_node_id}' should be the pipeline's single entry-point node"
        )
        assert pipeline_page.get_trigger_control_count_for_node(llm_node_id) == 1, (
            "The entry-point LLM node's own card should render exactly one Trigger control"
        )

    with allure.step(
        "Step 2 — Add a Code node (non-entry); verify entry point unchanged and its own "
        "card shows NO Trigger control"
    ):
        # No click needed to "open" either node's panel (AFS Coverage Map row 2/4
        # CLARIFICATION): NodeCard.jsx renders every node fully expanded by default
        # (isExpanded initial state True) -- clicking the header TOGGLES expand/
        # collapse, which would risk hiding the very field this step observes.
        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            "Adding a non-entry node should not change the pipeline's entry point"
        )
        assert pipeline_page.get_trigger_control_count_for_node(code_node_id) == 0, (
            "The non-entry Code node's own card should render NO Trigger control"
        )

    with allure.step(
        "Step 3 — Add a Printer node too (LLM -> Code -> Printer, matching the case's own "
        "example); verify it ALSO has no Trigger control"
    ):
        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_trigger_control_count_for_node(printer_node_id) == 0, (
            "The non-entry Printer node's own card should render NO Trigger control"
        )

    with allure.step(
        "Step 4 — With all 3 nodes present, re-verify the LLM entry node still shows exactly "
        "one Trigger control, and it is the ONLY one on the whole canvas"
    ):
        assert pipeline_page.get_trigger_control_count_for_node(llm_node_id) == 1, (
            "The entry-point LLM node's Trigger control should survive unaffected by its "
            "non-entry siblings coexisting on the same canvas"
        )
        assert pipeline_page.trigger_select.count() == 1, (
            "Exactly one Trigger control should exist across all 3 nodes -- the entry "
            "point's own"
        )

    with allure.step(
        'Step 5 — Verify the Information section shows "Trigger:<value>" matching the entry '
        "node's own current Trigger selection"
    ):
        entry_trigger_value = pipeline_page.get_trigger_type_value()
        expect(pipeline_page.information_trigger_row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        # Declared improvisation (role-overrides.md reverse-masking guard,
        # confirmed live this session): the row's DOM textContent concatenates
        # label+value with NO literal space ("Trigger:Chat Message") -- the
        # visual gap is CSS flex `gap`, not a text character. Assert the live-
        # contract string, not a "Trigger: <value>" (space) reading.
        expect(pipeline_page.information_trigger_row).to_have_text(
            f"Trigger:{entry_trigger_value}", timeout=UI_ELEMENT_TIMEOUT
        )

    assert not console_errors, (
        f"Verifying Trigger-control exclusivity should not introduce console errors: "
        f"{[m.text for m in console_errors]}"
    )
