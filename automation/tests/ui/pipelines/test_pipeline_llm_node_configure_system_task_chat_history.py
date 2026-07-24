"""UI test — Configure LLM Node: System, Task, Chat History (fields persist
across Save + reload).

TMS: ELITEA-2004
(test-specs/pipelines/l2_configure-llm-node-system-task-chat-history_ELITEA-2004.md)

Configures an existing LLM node's SYSTEM (Fixed), TASK (F-String), and
CHAT HISTORY (Fixed) fields plus its tool-agnostic Input/Output
state-variable selects, saves, and confirms every field persists through a
full page reload — verified via both the Flow-view fields and the YAML-view
tab independently (AFS Axis 2 addition), plus zero console errors and zero
failed (4xx/5xx) network requests across the ENTIRE configure->save->reload
cycle (both side channels stay registered through the Step 10 hard reload,
not just up to Save).
"""

import logging
import re

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_SYSTEM_VALUE = "You are a helpful assistant"
_TASK_VALUE = "User Input: {input}"
_CHAT_HISTORY_VALUE = "[]"


def _failed_requests(captured) -> list:
    """Filter a CapturedRequests list down to 4xx/5xx entries.

    Entries whose response hasn't arrived yet carry ``status=None`` —
    excluded here (not a failure, just still in flight).
    """
    return [r for r in captured if r["status"] is not None and r["status"] >= 400]


def _yaml_node_field(yaml_text: str, field_name: str) -> str:
    """Extract a pipeline-node YAML field's raw value text (stripped).

    Terminates the capture at the next lowercase_snake_case YAML key or a
    newline, whichever comes first — the SAME technique
    ``PipelineDetailPage.get_entrypoint_node_id()`` already relies on for its
    ``entry_point:`` field, because ``get_yaml_content()`` falls back to a
    single concatenated string (no line breaks at all) whenever the
    ``pipeline-yaml-lines`` testid selector matches 0 elements — confirmed
    live (2026-07-24): the YAML view genuinely renders with no separators
    between CodeMirror lines in this environment, so a plain
    ``.split("\\n")`` is not reliable and ``yaml.safe_load()`` would fail to
    parse the squashed text. Reused here as a standalone helper (not
    duplicated regex logic — same technique) because
    ``get_entrypoint_node_id`` only ever extracts ``entry_point``, not an
    arbitrary node field.

    Review fix (ELITEA-2004): replaces a bare ``"input" in yaml_text``
    substring check, which is vacuous — the TASK f-string placeholder
    ``{input}`` (``_TASK_VALUE``) already guarantees the literal substring
    'input' appears in the YAML regardless of whether the Input select
    actually wrote anything, so a regression that leaves ``input: []``
    empty would go undetected. This extracts ONLY the ``input:`` node
    field's own value so the caller can assert its actual structural
    content (e.g. ``"- input"``, not empty ``"[]"``).
    """
    match = re.search(rf"\b{re.escape(field_name)}:\s*(.+?)(?=\s*[a-z_]+:|\n|$)", yaml_text, re.DOTALL)
    return match.group(1).strip() if match else ""


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2004_configure-llm-node-system-task-chat-history.md",
    "onetest-ai Test Case link",
)
def test_configure_llm_node_system_task_chat_history(page, pipeline_with_llm_id):
    """Configure SYSTEM/TASK/CHAT HISTORY + Input/Output; verify Save + reload persistence."""
    pipeline_id = pipeline_with_llm_id
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 (reused via BasePage.capture_console_errors /
    # capture_requests_matching — Hard Rule 7, reuse-before-create) so BOTH
    # console errors and network responses from every step (field edits,
    # dropdown opens, Save, AND the Step 10 hard reload) are captured — the
    # AFS Expected Results require "zero error-level console messages and
    # zero failed (4xx/5xx) network requests across the entire
    # configure->save->reload cycle", not just up to Save. An empty
    # url_substring ("") matches every request (`"" in url` is always True),
    # so this is a whole-page monitor, not a URL-scoped one like this
    # method's other call sites in the suite.
    console_errors = None  # CapturedConsoleMessages, needs stop() in finally
    network_activity = None  # CapturedRequests, needs stop() in finally

    try:
        console_errors = pipeline_page.capture_console_errors()
        network_activity = pipeline_page.capture_requests_matching("")

        with allure.step("Step 1 — Navigate to the fixture-created pipeline; LLM node on canvas"):
            pipeline_page.navigate(pipeline_id)
            pipeline_page.dismiss_banner_if_present()
            pipeline_page.wait_for_canvas()
            canonical_url = page.url  # captured for the reload step — same
            # /pipelines/all/{id}?viewMode=owner pattern the MCP-node specs rely on.
            node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
            assert node_id, "LLM node should be present on the canvas with a non-empty data-id"

        with allure.step(
            "Step 2/3 — Config fields are always rendered inline on the node card "
            "(no separate open/close action — same live simplification as ELITEA-1954)"
        ):
            assert pipeline_page.get_llm_node_type("system", timeout=UI_ELEMENT_TIMEOUT) is not None, (
                "SYSTEM Type select should be visible inline on the canvas card"
            )
            assert pipeline_page.get_llm_node_type("task") is not None, "TASK Type select should be visible"
            assert pipeline_page.get_llm_node_type("chat_history") is not None, (
                "CHAT HISTORY Type select should be visible"
            )
            assert pipeline_page.llm_node_input_select.is_visible(), "Input select should be visible inline"
            assert pipeline_page.llm_node_output_select.is_visible(), "Output select should be visible inline"
            # AFS Coverage Map row 3 claims ALL 9 listed sections are
            # confirmed present (Trigger, SYSTEM, TASK, CHAT HISTORY, Input,
            # Output, Toolkits, Interrupt before/after, Structured output) —
            # the 4 assertions above cover SYSTEM/TASK/CHAT-HISTORY/Input/
            # Output; the remaining 5 are asserted here (review fix pass,
            # ELITEA-2004). `pipeline_with_llm_id`'s LLM node is the
            # pipeline's `entry_point`, so its NodeCard renders
            # TriggerTypeSelector (see
            # PipelineAPI.create_pipeline_with_llm_node's YAML).
            assert pipeline_page.pipeline_trigger_select.is_visible(), (
                "Trigger select should be visible inline on the entry-point node card"
            )
            assert pipeline_page.toolkits_section.is_visible(), (
                "Toolkits section should be visible inline on the node card"
            )
            assert pipeline_page.node_interrupt_before_switch.is_visible(), (
                "'Interrupt before' toggle should be visible inline on the node card"
            )
            assert pipeline_page.node_interrupt_after_switch.is_visible(), (
                "'Interrupt after' toggle should be visible inline on the node card"
            )
            assert pipeline_page.node_structured_output_switch.is_visible(), (
                "'Structured output' toggle should be visible inline on the node card"
            )

        with allure.step('Step 4 — SYSTEM: set Type to "Fixed", enter Value'):
            pipeline_page.set_llm_node_field("system", "fixed", _SYSTEM_VALUE, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.get_llm_node_type("system") == "Fixed", "SYSTEM Type should show 'Fixed'"
            assert pipeline_page.get_llm_node_value("system") == _SYSTEM_VALUE, (
                "SYSTEM Value should read back the typed text"
            )

        with allure.step('Step 5 — TASK: set Type to "F-String", enter Value'):
            pipeline_page.set_llm_node_field("task", "fstring", _TASK_VALUE, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.get_llm_node_type("task") == "F-String", "TASK Type should show 'F-String'"
            assert pipeline_page.get_llm_node_value("task") == _TASK_VALUE, (
                "TASK Value should read back the typed f-string text verbatim"
            )

        with allure.step('Step 6 — CHAT HISTORY: set Type to "Fixed", enter Value "[]"'):
            pipeline_page.set_llm_node_field(
                "chat_history", "fixed", _CHAT_HISTORY_VALUE, timeout=UI_ELEMENT_TIMEOUT
            )
            assert pipeline_page.get_llm_node_type("chat_history") == "Fixed", (
                "CHAT HISTORY Type should show 'Fixed'"
            )
            assert pipeline_page.get_llm_node_value("chat_history") == _CHAT_HISTORY_VALUE, (
                "CHAT HISTORY Value should read back '[]'"
            )

        with allure.step('Step 7 — Set Input combobox to include "input"'):
            pipeline_page.select_llm_node_input("input", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 8 — Set Output combobox to "messages"'):
            pipeline_page.select_llm_node_output("messages", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 7/8 verification — YAML view corroborates Input/Output selections "
            "(AFS Concrete Handles: chip-reading is out of scope, YAML view suffices)"
        ):
            pipeline_page.switch_to_yaml_view()
            yaml_before_save = pipeline_page.get_yaml_content()
            pipeline_page.switch_to_flow_view()
            # Structural check (review fix, ELITEA-2004) — see _yaml_node_field's
            # docstring. A bare "input" in yaml_before_save is vacuous: the TASK
            # f-string placeholder "{input}" (_TASK_VALUE) already guarantees the
            # literal substring appears regardless of whether the Input select
            # actually wrote anything to the node's `input:` field (the fixture
            # pre-seeds `input: []`, empty). Extracting the field's own value and
            # asserting its real content proves select_llm_node_input() actually
            # added "input" to the Input list.
            input_field_before_save = _yaml_node_field(yaml_before_save, "input")
            assert input_field_before_save == "- input", (
                "Input field should round-trip as a YAML list containing exactly "
                "the selected 'input' variable, got field text: "
                f"{input_field_before_save!r} — full YAML:\n{yaml_before_save}"
            )
            assert "messages" in yaml_before_save, "YAML should show 'messages' as an Output variable"
            # AFS Coverage Map row 6 / Test Data note: SimpleLLMInputItem.jsx's
            # onInput JSON.parses the CHAT HISTORY field when
            # variableName === 'chat_history' && type === 'fixed', silently
            # falling back to a raw STRING on parse failure. `value: []`
            # (unquoted) only renders when the YAML dumper is holding a real
            # list; a string that merely looks like "[]" serializes quoted
            # (`value: '[]'`/`value: "[]"`) to disambiguate from a list.
            assert "value: []" in yaml_before_save, (
                "CHAT HISTORY should round-trip as a real YAML list (unquoted "
                f"'value: []'), not a string — got YAML:\n{yaml_before_save}"
            )
            assert "value: '[]'" not in yaml_before_save and 'value: "[]"' not in yaml_before_save, (
                "CHAT HISTORY must not have fallen back to a quoted string "
                f"representation of '[]' — got YAML:\n{yaml_before_save}"
            )

        with allure.step(
            "Step 9 — Save pipeline; verify 201 + Discard clears + no console/network errors so far"
        ):
            save_response = pipeline_page.save_and_wait_for_update(
                project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
            )
            assert save_response is not None, "Save should return the persisted pipeline version"
            assert not pipeline_page.is_discard_enabled(), (
                "Discard button (dirty-state indicator) should disable after a successful Save"
            )
            assert not console_errors, f"Save should not introduce console errors: {console_errors}"
            failed_so_far = _failed_requests(network_activity)
            assert not failed_so_far, (
                f"No 4xx/5xx network requests should occur through Save, got: {failed_so_far}"
            )
            assert pipeline_page.get_llm_node_type("system") is not None  # canvas still rendered post-save

        with allure.step(
            "Step 10 — Hard reload via the canonical URL; all fields persisted "
            "(dual-sourced: Flow-view fields AND YAML view independently)"
        ):
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.wait_for_canvas()
            pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

            assert pipeline_page.get_llm_node_type("system") == "Fixed"
            assert pipeline_page.get_llm_node_value("system") == _SYSTEM_VALUE, (
                "SYSTEM Value should persist after reload"
            )
            assert pipeline_page.get_llm_node_type("task") == "F-String"
            assert pipeline_page.get_llm_node_value("task") == _TASK_VALUE, (
                "TASK Value should persist after reload"
            )
            assert pipeline_page.get_llm_node_type("chat_history") == "Fixed"
            assert pipeline_page.get_llm_node_value("chat_history") == _CHAT_HISTORY_VALUE, (
                "CHAT HISTORY Value should persist after reload"
            )

            pipeline_page.switch_to_yaml_view()
            yaml_after_reload = pipeline_page.get_yaml_content()
            pipeline_page.switch_to_flow_view()
            assert "You are a helpful assistant" in yaml_after_reload, (
                "YAML view should independently corroborate the persisted SYSTEM value"
            )
            assert "User Input: {input}" in yaml_after_reload, (
                "YAML view should independently corroborate the persisted TASK value"
            )
            # Same structural check as pre-save (see _yaml_node_field's docstring) —
            # a bare "input" in yaml_after_reload is equally vacuous here.
            input_field_after_reload = _yaml_node_field(yaml_after_reload, "input")
            assert input_field_after_reload == "- input", (
                "Input field should still round-trip as a YAML list containing "
                f"exactly 'input' after reload, got field text: {input_field_after_reload!r} "
                f"— full YAML:\n{yaml_after_reload}"
            )
            assert "messages" in yaml_after_reload, (
                "YAML view should show 'messages' still mapped after reload"
            )
            # Second, post-reload corroboration that CHAT HISTORY persisted
            # as a real YAML list (not a string) server-side — same check
            # as the pre-save one above, now against the value the backend
            # actually persisted and served back.
            assert "value: []" in yaml_after_reload, (
                "CHAT HISTORY should still round-trip as a real YAML list "
                f"(unquoted 'value: []') after reload — got YAML:\n{yaml_after_reload}"
            )
            assert "value: '[]'" not in yaml_after_reload and 'value: "[]"' not in yaml_after_reload, (
                "CHAT HISTORY must not have persisted as a quoted string "
                f"representation of '[]' — got YAML:\n{yaml_after_reload}"
            )

        with allure.step(
            "Whole-cycle side-channel check — zero console errors and zero "
            "failed (4xx/5xx) network requests across configure->save->reload"
        ):
            # console_errors/network_activity have stayed registered on the
            # SAME page object since before Step 1 — page.on() listeners
            # survive page.reload()/page.goto() (same target Page), so this
            # single check at the end covers the reload too, closing the gap
            # the review flagged (console_errors was previously only
            # asserted before the Step 10 reload).
            assert not console_errors, (
                "Expected no console errors across the whole configure->save->reload cycle, "
                f"got: {[m.text for m in console_errors]}"
            )
            failed_overall = _failed_requests(network_activity)
            assert not failed_overall, (
                "Expected zero failed (4xx/5xx) network requests across the whole "
                f"configure->save->reload cycle, got: {failed_overall}"
            )
    finally:
        # Stop listeners to prevent resource leaks that cause test hangs.
        if console_errors is not None:
            console_errors.stop()
        if network_activity is not None:
            network_activity.stop()
