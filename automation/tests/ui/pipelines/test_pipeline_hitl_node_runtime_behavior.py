"""UI test — Pipeline HITL Node: Runtime Behavior.

TMS: ELITEA-2015
(test-specs/pipelines/l2_hitl-node-runtime-behavior_ELITEA-2015.md)

Executes a pipeline (LLM 1 -> HITL 1 -> Printer 1 -> END) with HITL routes
configured (APPROVE -> Printer 1, REJECT -> END), verifies the pipeline
pauses at the HITL node with the configured message and Approve/Edit/Reject
buttons, then exercises both the Approve and Reject resume actions — Reject
on a SEPARATE, freshly-created pipeline/conversation per the AFS's Test
isolation note (rules out session-state pollution between the two variants).

**Implementer correction to the AFS's Known Defects classification**
(2026-08-02, fresh live websocket capture, 2/2 repro attempts each,
independent of the analyst's original session): Approve correctly routes to
the configured APPROVE target — Printer 1's formatted output reaches the
chat. The live product does NOT reproduce the "static hint, no Printer
execution" defect the AFS / EliteaAI/elitea-testing-public#1103 describe for
Approve. Reject DOES reproduce exactly as described: the backend restarts
the whole pipeline from the entry point (a fresh `start_task`/`agent_start`
sequence re-invoking LLM 1) instead of ending at END. Per the reverse-masking
guard (the live product is ground truth, not the filed defect's text),
Approve is asserted as a normal hard assertion; only Reject's assertions are
`# Known defect: #1103` soft failures (sanctioned RED,
`.agents/testing.md` § Merge gate). See the implementer's comment on #1103
documenting this split so the ticket isn't chased for a non-repro half.

**Second case-text/AFS correction:** the case's precondition configures only
APPROVE and REJECT routes (no EDIT), yet its step 3 describes all three
buttons as always present. Live-confirmed (websocket `agent_hitl_interrupt`
payload's `available_actions` field): the Edit action is only offered when
the HITL node has an `edit` route configured — with this precondition,
`available_actions` is exactly `["approve", "reject"]`, no `edit`. This is
the same class of route-gating behavior as ELITEA-2014's EDIT-STATE-KEY-gates-
EDIT-route finding, not a defect. Step 3 asserts the Edit button's absence,
matching the precondition as literally specified rather than inventing an
edit route the case never asked for.
"""

import logging

import allure
import pytest
from fixtures.data_fixtures import build_hitl_runtime_nodes
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

PAUSE_TIMEOUT = 60_000
RESUME_SETTLE_MS = 8_000

_KNOWN_DEFECT_1103 = "https://github.com/EliteaAI/elitea-testing-public/issues/1103"


def _chat_predict_events(frames, inner_type):
    """Return every received ``chat_predict``-namespaced frame with *inner_type*.

    The pipeline/chat wire protocol nests everything (LLM streaming, HITL
    pause, resume responses) under the single socket.io event
    ``chat_predict``, disambiguated by an inner ``"type"`` field — see AFS §
    Network Behavior.
    """
    return [f for f in frames if f.get("event") == "chat_predict" and f.get("type") == inner_type]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2015_pipeline-hitl-node-runtime-behavior.md",
    "onetest-ai Test Case link",
)
def test_hitl_node_runtime_behavior(page, hitl_runtime_pipeline, pipeline_api):
    """Verify HITL pause + Approve routing (hard) and Reject non-restart (known defect #1103)."""
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    pipeline_page = PipelineDetailPage(page)

    with allure.step("Step 1 — Pipeline is saved with the described topology"):
        readback = pipeline_api.get_pipeline(hitl_runtime_pipeline["id"])
        instructions = readback["versions"][0]["instructions"]
        assert "entry_point: LLM 1" in instructions, "Entry point should be LLM 1"
        assert "type: hitl" in instructions, "Pipeline should contain a HITL node"
        assert "approve: Printer 1" in instructions, "APPROVE route should target Printer 1"
        assert "reject: END" in instructions, "REJECT route should target END"

    # capture_websocket_frames() must be entered BEFORE navigate() —
    # Playwright's "websocket" event fires once, at connection-open time
    # (see the page-object docstring for the confirmed-live gotcha).
    with pipeline_page.capture_websocket_frames() as frames:
        with allure.step("Step 2 — Execute the pipeline by sending a message in embedded chat"):
            before_send = len(frames)
            pipeline_page.navigate(hitl_runtime_pipeline["id"])
            pipeline_page.wait_for_canvas()
            pipeline_page.send_message_in_embedded_chat("Hello")
            # The chat's HITL pause card appearing IS this AFS step's "Run N
            # details" execution-started signal on this surface — there is
            # no separate canvas indicator distinct from the chat pause here.
            pipeline_page.wait_for_chat_hitl_actions_panel(timeout=PAUSE_TIMEOUT)
            # Real execution-start assertion (fix-round correction,
            # 2026-08-02 — AFS Coverage Map row for this step previously
            # cited a "Run indicator" assertion that did not exist in code).
            # The AFS's originally-specced canvas "Run N details" indicator
            # does not exist on this surface (confirmed live); the actual
            # observable proof that the pipeline began executing (as opposed
            # to the message merely being queued) is the LLM node's
            # streaming output starting to arrive over the socket — see AFS
            # § Network Behavior (`agent_llm_chunk` precedes
            # `agent_hitl_interrupt`). Step 3 asserts the interrupt itself;
            # this assertion is the distinct "execution started" signal.
            execution_started_frames = _chat_predict_events(frames[before_send:], "agent_llm_chunk")
            assert execution_started_frames, (
                "Expected at least one agent_llm_chunk frame confirming pipeline execution started"
            )

        with allure.step(
            "Step 3 — Verify the pipeline pauses at HITL: message + Approve/Edit/Reject buttons"
        ):
            interrupts = _chat_predict_events(frames, "agent_hitl_interrupt")
            assert len(interrupts) == 1, (
                f"Expected exactly one agent_hitl_interrupt frame, got {len(interrupts)}"
            )
            assert interrupts[0].get("content") == hitl_runtime_pipeline["hitl_message"], (
                f"HITL interrupt payload content should be the configured user_message, "
                f"got {interrupts[0].get('content')!r}"
            )
            assert pipeline_page.chat_hitl_approve_button.count() == 1, "Exactly one Approve button"
            assert pipeline_page.chat_hitl_reject_button.count() == 1, "Exactly one Reject button"
            # No Edit button — the precondition configures no `edit` route,
            # and the live product only offers Edit when one exists (see
            # module docstring's second case-text correction).
            assert pipeline_page.chat_hitl_edit_button.count() == 0, (
                "Edit button should be absent — no edit route is configured for this HITL node"
            )
            assert pipeline_page.chat_hitl_approve_button.is_enabled(), "Approve button should be enabled"
            assert pipeline_page.chat_hitl_reject_button.is_enabled(), "Reject button should be enabled"

        with allure.step(
            "Steps 4/5 — Click Approve; verify flow continues to the configured APPROVE route "
            "and its output reaches the chat (confirmed working live — see module docstring)"
        ):
            before = len(frames)
            pipeline_page.click_chat_hitl_approve()
            page.wait_for_timeout(RESUME_SETTLE_MS)
            approve_frames = frames[before:]

            resume_sent = [
                f for f in approve_frames
                if f.get("event") == "chat_continue_predict" and f.get("hitl_action") == "approve"
            ]
            assert len(resume_sent) == 1, "Approve click should send exactly one chat_continue_predict frame"
            assert resume_sent[0].get("hitl_resume") is True, "Resume frame should carry hitl_resume=true"

            responses = _chat_predict_events(approve_frames, "agent_response")
            assert responses, "Approve should produce an agent_response frame"
            assert hitl_runtime_pipeline["printer_output"] in (responses[-1].get("content") or ""), (
                f"Approve should route to Printer 1 and include its formatted output "
                f"{hitl_runtime_pipeline['printer_output']!r} in the chat response, "
                f"got {responses[-1].get('content')!r}"
            )

    with allure.step(
        "Step 6 — Execute again on a fresh pipeline/conversation, click Reject; verify no "
        "further processing and no Printer output (known defect #1103, sanctioned RED)"
    ):
        reject_pipeline = pipeline_api.create_pipeline_with_nodes(
            name="autotest_hitl_reject_variant",
            description="Auto-created HITL reject-variant pipeline (fresh isolation, ELITEA-2015)",
            entry_point="LLM 1",
            nodes=build_hitl_runtime_nodes(hitl_runtime_pipeline["hitl_message"]),
        )
        reject_pipeline_id = reject_pipeline["id"]
        soft_failures = []
        try:
            with pipeline_page.capture_websocket_frames() as reject_frames:
                pipeline_page.navigate(reject_pipeline_id)
                pipeline_page.wait_for_canvas()
                pipeline_page.send_message_in_embedded_chat("Hello")
                pipeline_page.wait_for_chat_hitl_actions_panel(timeout=PAUSE_TIMEOUT)

                before = len(reject_frames)
                pipeline_page.click_chat_hitl_reject()
                page.wait_for_timeout(RESUME_SETTLE_MS)
                reject_result = reject_frames[before:]

            reject_sent = [
                f for f in reject_result
                if f.get("event") == "chat_continue_predict" and f.get("hitl_action") == "reject"
            ]
            assert len(reject_sent) == 1, "Reject click should send exactly one chat_continue_predict frame"
            assert reject_sent[0].get("hitl_resume") is True, "Resume frame should carry hitl_resume=true"

            # Correct expected behavior (per case): Reject ends at END —
            # no further node execution, so no fresh start_task/agent_start
            # should fire after the resume frame.
            restarted_types = sorted(
                {f["type"] for f in _chat_predict_events(reject_result, "start_task")}
                | {f["type"] for f in _chat_predict_events(reject_result, "agent_start")}
            )
            if restarted_types:
                soft_failures.append(
                    f"Known defect {_KNOWN_DEFECT_1103}: Reject should end the pipeline at END with "
                    f"no further processing, but the backend re-emitted {restarted_types} — the "
                    "pipeline restarted from the entry point instead."
                )

            printer_leak = [
                f for f in _chat_predict_events(reject_result, "agent_response")
                if hitl_runtime_pipeline["printer_output"] in (f.get("content") or "")
            ]
            if printer_leak:
                soft_failures.append(
                    f"Known defect {_KNOWN_DEFECT_1103}: Reject should not reach Printer 1, "
                    "but its formatted output appeared in the chat response."
                )
        finally:
            pipeline_api.delete_pipeline(reject_pipeline_id)

        # Console-error check MUST run before the known-defect pytest.fail()
        # below — #1103 fires deterministically on every Reject run, so a
        # pytest.fail() raised first would make any assertion after this
        # `with` block permanently unreachable (fix-round correction,
        # 2026-08-02: the trailing top-level assert was dead code for the
        # entire time this known defect stays open).
        assert not console_errors, f"No console errors expected at any step: {console_errors}"

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (sanctioned RED — known defect #1103):\n"
                + "\n".join(soft_failures)
            )
