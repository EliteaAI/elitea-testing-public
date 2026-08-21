"""UI test — Pipeline: Interrupt Before/After Toggles.

TMS: ELITEA-2047
(test-specs/pipelines/l2_pipeline-interrupt-before-after-toggles_ELITEA-2047.md)

Builds a two-node pipeline (Code 1 -> Printer 1), enables "Interrupt after"
on Code 1 (only clickable once an outgoing edge exists — Step 0's setup),
saves and round-trips the pipeline-level ``interrupt_after:`` YAML field,
then executes via the embedded chat and verifies the run correctly pauses
after Code 1 (steps 6-7 — no product defect, matches the case text exactly).

**Known product defect (step 8, sanctioned RED):** resuming via the UI's own
advertised "type anything" chat instruction does NOT resume the paused run —
a second, distinct run is spawned instead of the checkpointed one resuming.
Filed as `EliteaAI/elitea-testing-public#1327`. Per `.agents/testing.md` §
Merge gate's analysis-time exception, steps 0-7's assertions stay hard (they
pass cleanly); only step 8's resume-completion assertions are
`soft_failures` tagged `# Known defect: #1327`.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000
PAUSE_TIMEOUT = 60_000
RESUME_SETTLE_MS = 20_000

_CODE_VALUE = 'result = "code node ran"'

_KNOWN_DEFECT_1327 = "https://github.com/EliteaAI/elitea-testing-public/issues/1327"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2047_pipeline-interrupt-before-after-toggles.md",
    "onetest-ai Test Case link",
)
def test_interrupt_after_toggle_pauses_and_attempts_resume(page, pipeline_id):
    """Interrupt-after toggle pauses execution after the node (hard); resume is a known defect (soft, #1327)."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 0 so console errors from every step are
    # captured — AFS Expected Results require "no console errors" through
    # steps 0-7 (step 8's own console-cleanliness is asserted separately,
    # after the known-defect soft assertions, matching the HITL runtime
    # test's ordering rule: console check MUST run before any pytest.fail()
    # so it's never left unreachable dead code while #1327 stays open).
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 0 (setup) — create a Code node + a Printer node and connect them, "
        "so Code 1's 'Interrupt after' switch is not disabled (no outgoing edge = disabled)"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        canonical_url = page.url  # captured for the reload step (?viewMode=owner already included)

        pipeline_page.add_node("Code")
        code_node_id = pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        assert code_node_id, "Code node should appear on canvas with a non-empty data-id"
        pipeline_page.fill_code_node_value(_CODE_VALUE, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_code_node_value() == _CODE_VALUE, (
            "CODE Value field should hold the entered Python code exactly"
        )

        pipeline_page.add_node("Printer")
        printer_node_id = pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT)
        assert printer_node_id, "Printer node should appear on canvas with a non-empty data-id"

        # ReactFlow spawns a freshly-added node at the same default canvas
        # position every time — confirmed live, Printer 1 landed fully
        # overlapping Code 1. connect_nodes() cannot compute a valid drag
        # path between overlapping handles, so separate them first.
        pipeline_page.move_node(printer_node_id, dx=450, dy=100)

        # fit_view() before connect_nodes() is required — connect_nodes()
        # reads handle bounding boxes via JS, and freshly-added nodes can
        # sit outside/overlapping the current viewport (established pattern,
        # see test_pipeline_advanced.py's UI-added-node connect steps).
        pipeline_page.fit_view()
        pipeline_page.wait_for_network()
        pipeline_page.connect_nodes(code_node_id, printer_node_id)
        # wait_for_edge_present() (not wait_for_edge()) — pre-Save, a
        # drag-created edge's testid carries the ReactFlow handle-id suffix
        # (confirmed live: "rf__edge-xy-edge__Code 1source-Printer 1target"),
        # not the clean post-reload "---"-only shape wait_for_edge() polls
        # (same documented shape difference as wait_for_edge_present()'s own
        # Decision-node docstring). Step 5 re-navigates via the canonical
        # URL after Save, where the edge IS in the clean post-reload shape.
        pipeline_page.wait_for_edge_present(code_node_id, printer_node_id, timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 1 — Pipeline is open with both nodes visible"):
        assert pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT), (
            "Code node should still be present on canvas"
        )
        assert pipeline_page.wait_for_node_on_canvas("printer", timeout=UI_ELEMENT_TIMEOUT), (
            "Printer node should still be present on canvas"
        )

    with allure.step(
        "Step 2 — Locate 'Interrupt before' switch; verify visible AND disabled "
        "(Code 1 is the pipeline's entry point — CommonInterruptSettings.jsx gating, "
        "Axis-2 addition matching the ELITEA-2037/2009/2034 disabled-state convention)"
    ):
        assert pipeline_page.is_node_interrupt_before_toggle_visible(code_node_id, timeout=UI_ELEMENT_TIMEOUT), (
            "Interrupt before switch should be visible on Code 1"
        )
        assert pipeline_page.is_node_interrupt_before_toggle_disabled(code_node_id, timeout=UI_ELEMENT_TIMEOUT), (
            "Interrupt before switch should be disabled — Code 1 is the entry point"
        )

    with allure.step(
        "Step 3 — Locate 'Interrupt after' switch; verify visible AND NOT disabled "
        "(Step 0's edge gives Code 1 an outgoing transition)"
    ):
        expect(pipeline_page.code_node_interrupt_after_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert not pipeline_page.code_node_interrupt_after_toggle.is_disabled(), (
            "Interrupt after switch should be enabled once Code 1 has an outgoing edge"
        )

    with allure.step("Step 4 — Toggle 'Interrupt after' to enabled"):
        pipeline_page.code_node_interrupt_after_toggle.click()
        expect(pipeline_page.code_node_interrupt_after_toggle).to_be_checked(checked=True)

    with allure.step(
        "Step 5 — Save the pipeline; verify no console errors, a 201 Created response, "
        "and the pipeline-level 'interrupt_after:' YAML round-trips through reload"
    ):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.code_node_interrupt_after_toggle).to_be_checked(checked=True)

        pipeline_page.switch_to_yaml_view()
        yaml_content = pipeline_page.get_yaml_content()
        assert "interrupt_after:" in yaml_content, "interrupt_after should be a top-level YAML key"
        assert f"- {code_node_id}" in yaml_content, (
            f"interrupt_after should list {code_node_id!r} as a list item — got:\n{yaml_content}"
        )
        assert not console_errors, f"Reload should not introduce console errors: {console_errors}"

    with allure.step(
        "Steps 6/7 — Execute via embedded chat; verify the run pauses after Code 1: "
        "Code 1's output reaches the chat, the interrupt edge pill appears, and Code 1's "
        "whole config panel locks. Printer 1 does NOT execute yet. (Asserted together per "
        "the AFS — case step 7 restates step 6's expected result, not a distinct mechanism.)"
    ):
        # Step 5 left the editor in YAML view — return to Flow view so the
        # canvas (edge label, node panel) is interactable for this step.
        pipeline_page.flow_view_button.click()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("code", timeout=UI_ELEMENT_TIMEOUT)

        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat("Hello")
        pipeline_page.wait_for_embedded_chat_response(initial_count=initial_count, timeout=PAUSE_TIMEOUT)

        # Code 1's own execution result reached the chat.
        assert pipeline_page.get_embedded_chat_message_count() >= initial_count + 2, (
            "At least a user message and Code 1's execution response should be in the chat"
        )
        last_message = pipeline_page.get_embedded_chat_last_message()
        assert "execution_info" in last_message and "Execution time" in last_message, (
            f"Code 1's execution result (execution_info/Execution time) should reach the chat, "
            f"got: {last_message!r}"
        )

        # The interrupt edge pill on Code 1 -> Printer 1 (testid added this
        # session, EliteaAI/EliteaUI@94d190c9) is the synchronization point —
        # waiting on it (not a sleep) proves the pause has actually landed.
        interrupt_label = pipeline_page.get_edge_label_locator(code_node_id, printer_node_id)
        expect(interrupt_label).to_have_text("interrupt", timeout=PAUSE_TIMEOUT)

        # Code 1's whole config panel locks — representative fields whose
        # disabled mechanism is directly verifiable: the Value field (native
        # HTML `disabled` attribute) and the Interrupt-after/Structured-output
        # switches (native `disabled` on the nested checkbox input) flip from
        # enabled to disabled; the Type/Input/Output MUI Selects expose their
        # disabled state only via the `Mui-disabled` CSS class (confirmed
        # live — no native `disabled`/`aria-disabled` attribute on these).
        assert pipeline_page.code_node_value.is_disabled(), "CODE Value field should lock while paused"
        assert pipeline_page.code_node_interrupt_after_toggle.is_disabled(), (
            "Interrupt after switch should lock (flip from enabled to disabled) while paused"
        )
        assert pipeline_page.code_node_structured_output_toggle.is_disabled(), (
            "Structured output switch should lock while paused"
        )
        for locked_select in (
            pipeline_page.code_node_type_select,
            pipeline_page.code_node_input_select,
            pipeline_page.code_node_output_select,
        ):
            assert "Mui-disabled" in (locked_select.get_attribute("class") or ""), (
                "CODE/Input/Output selects should carry Mui-disabled while paused"
            )

        # AFS case-text CLARIFICATION (implementer correction, reverse-masking
        # guard — .agents/testing.md § Merge gate): the AFS's Step 6 claimed
        # the chat auto-posts a distinct "How to proceed?..." hint message.
        # Re-confirmed live on a FRESH pipeline (this test, 2 independent
        # runs) and separately on the AFS's own exploration pipeline
        # (id 8159) via manual probe: the chat shows exactly 2 messages
        # (the user's trigger + Code 1's execution-result bubble) — no
        # separate hint bubble ever appears, even after a further 10s
        # settle wait. The case's own wording only requires "UI indicates
        # pipeline is paused", which the edge pill + locked config panel +
        # run-in-progress node label already prove without this text — so
        # no coverage is lost by not asserting a message that does not
        # exist. Not filed as a defect: the interrupt mechanism itself
        # works correctly, only the AFS's specific hint-message claim was
        # inaccurate.

        # Printer 1 did NOT execute yet — no Printer-specific output bubble
        # (checked both concatenated/spaced id forms — chat text rendering
        # sometimes drops the space, see the run-details digest's
        # "Timeline step:LLM1" gotcha).
        assert not pipeline_page.find_message_containing("Printer1") and not pipeline_page.find_message_containing(
            "Printer 1"
        ), "Printer 1 should not have produced output yet — pipeline is paused before it"

        assert not console_errors, f"Pause sequence should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 8 — Resume via chat message (the UI's own advertised instruction); verify "
        "completion. KNOWN DEFECT — sanctioned RED (EliteaAI/elitea-testing-public#1327): "
        "resume does not work; a second run spawns instead of the checkpoint resuming"
    ):
        soft_failures = []

        before_resume_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat("continue")
        page.wait_for_timeout(RESUME_SETTLE_MS)

        # Correct expected behaviour (per case): Printer 1's output should
        # reach the chat once the pipeline resumes and completes.
        if not pipeline_page.find_message_containing("Printer1") and not pipeline_page.find_message_containing(
            "Printer 1"
        ):
            soft_failures.append(
                f"Known defect {_KNOWN_DEFECT_1327}: resuming via chat should let Printer 1 execute and "
                "its output reach the chat, but no Printer 1 output appeared after resume."
            )

        # Correct expected behaviour: the interrupt pill should clear once resumed.
        if pipeline_page.get_edge_label_locator(code_node_id, printer_node_id).count() > 0:
            soft_failures.append(
                f"Known defect {_KNOWN_DEFECT_1327}: the 'interrupt' edge pill should clear after a "
                "successful resume, but it is still present."
            )

        # Correct expected behaviour: Code 1's config panel should re-enable.
        if pipeline_page.code_node_value.is_disabled():
            soft_failures.append(
                f"Known defect {_KNOWN_DEFECT_1327}: Code 1's config panel should re-enable after a "
                "successful resume, but the Value field is still locked."
            )

        # Console-error check MUST run before the known-defect pytest.fail()
        # below — #1327 fires deterministically while open, and a
        # pytest.fail() raised first would make this assertion unreachable
        # dead code for the entire time the defect stays open (same
        # ordering rule as test_pipeline_hitl_node_runtime_behavior.py).
        assert not console_errors, f"No console errors expected at any step: {console_errors}"

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (sanctioned RED — known defect #1327, resume path):\n"
                + "\n".join(soft_failures)
            )

        # Reached only once #1327 is fixed — resume genuinely worked.
        assert pipeline_page.get_embedded_chat_message_count() > before_resume_count, (
            "Resume should produce at least one new chat message once #1327 is fixed"
        )
