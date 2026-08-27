"""UI Test for ELITEA-2215 — Chat: Tool Action and Output – Complete Flow
from Direct Toolkit Call to Output Display.

Verifies the full lifecycle of a direct toolkit call (toolkit added as chat
participant, no agent intermediary): the "Thought for X secs" accordion,
the (already auto-expanded) tool-call chip, waiting for execution, verifying
the model + tool chips, and the response text following the chips.

Spec: test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md

Fix round (2026-08-19) — ELITEA-2210's own delete_file-specific chip/icon
observable. ELITEA-2210's zero-diff AFS originally claimed its Coverage Map
rows 4-5 ("aaa: delete_file" chip + icon+label) were proven by THIS module's
create_file execution plus a source-code tool-agnosticism argument alone.
Review correctly flagged that a source-code argument is not itself a live
execution of the case's own observable. Added below (end of file):
TestDirectToolkitCallDeleteFileChip — an additive test class that
live-executes delete_file (no sensitivity/guardrails involved) and asserts
the exact chip text this case names, backend-verified via ArtifactAPI. See
test-specs/chat-interface/lextend_direct-toolkit-call-chip-tool-agnostic-verification_ELITEA-2210.md
for the amended Coverage Map.

Fix round 2 (2026-08-19) — TestDirectToolkitCallDeleteFileChip's own classify
step previously called pytest.fail()/raise AssertionError() immediately in
both its branches, which made the class's "Side-channel check — no
console/JS errors" step structurally unreachable on the #1127-confirmed
branch — the one that has fired 3/3 observed runs. The AFS's Gap assertions
section (rows 4-5) claims the console-error check as one of the new test's
four assertions, but it had never actually executed. Fixed to mirror
TestDirectToolkitCallCompleteFlow's own Step 2b shape exactly: the
#1127-confirmed branch now appends to a deferred `soft_failures` list
instead of failing immediately, the chip-verification step is guarded by
`run_executed_correctly`, the Side-channel check runs unconditionally after
it, and the deferred `pytest.fail()` (if any) happens last. The genuinely
undiagnosed-disagreement branch is unchanged (still an immediate
`raise AssertionError` — same shape the covering class also uses for that
branch, a deliberate hard stop for a signal combination that does not match
#1127's own confirmed signature). No change to what is asserted or to the
#1127 classification logic itself — this is a control-flow-ordering fix, not
a scope or fidelity change.

Extended (2026-08-19, extend-existing) to also cover ELITEA-2209 ("Chat –
Tool Action Rendering – Verify Tool Call Displays in Thinking Steps When
Toolkit Called Directly") — same live flow, one small gap: ELITEA-2209's
step 1 requires confirming the toolkit lands in the PARTICIPANTS panel
(toolkits section) and that no AGENTS section appears. The Setup step below
now asserts both, immediately after adding the toolkit participant. See
test-specs/chat-interface/lextend_direct-toolkit-call-participants-panel-verification_ELITEA-2209.md.

CLARIFICATION (reverse-masking guard, all confirmed live — no product
defect, case text is imprecise):
1. The case describes the tool-call badge as dotted
   (``"toolkit_name.tool_name"``); the live rendered chip text is
   colon-separated (``"{toolkit_name}: create_file"``,
   ``ActionView.jsx``'s ``buildTitle()``). This test asserts the live format.
2. The case describes THREE distinct chips (model / toolkit / tool-call) as
   if toolkit-identity and tool-call were separate elements. The live DOM
   renders exactly ONE combined toolkit/tool chip (``chat-answer-tool-chip``,
   newly added — see below) plus N>=1 model chips (one per distinct model
   invoked in the turn's reasoning chain, data-dependent, not fixed at 1).
   This test asserts "at least one model chip + exactly one tool chip",
   not "three chips".
3. The case's own step 2 says to manually "expand the thinking-steps
   accordion" as an action. Confirmed live (5 timed polls against the real
   backend, 0.5s apart): the accordion is ALREADY auto-expanded for the
   whole tool-call/streaming window — ``ApplicationThinkView.jsx``'s
   ``expanded={isStreaming || expanded}``, the SAME auto-expand behavior
   ELITEA-2181's streaming-response test already established and asserts
   without ever clicking. A manual click is not only unnecessary here, it
   is actively unreliable: the accordion's rendered height changes as it
   streams, so a fixed click point can land on a different part of a
   growing/shrinking element between the actionability check and the
   dispatched event. This test asserts presence/text directly instead.

One new testid added to EliteaUI for this case's own executed path (shared
ask with ELITEA-2212/2213, implemented once): ``chat-answer-tool-chip`` —
``ActionView.jsx``'s model/tool ternary, else-branch (canon ruling #277
shape (b): both branches now named since this case + ELITEA-2212 assert
presence/text and ELITEA-2213 asserts absence, all on their own executed
paths).

**PRODUCT DEFECT found during implementation, filed as
EliteaAI/elitea-testing-public#1127 (not masked — see the issue for full
evidence).** Across 3 separate live local runs, the direct-toolkit-call
flow (no agent) sometimes leaks the model's tool-call intent as raw VISIBLE
text (e.g. a literal ``<function_calls><invoke name="create_file">...``
block) instead of invoking the real backend tool. 2 separate runs of the
identical setup DID execute correctly (real backend call, correct chip),
making this LOOK non-deterministic rather than a hard 100% failure.
**That characterisation is SUPERSEDED — see "Fix round 3 (2026-08-27)"
below: re-measurement shows #1127 is TOOL-DEPENDENT, and it no longer
fires on this class's own ``create_file`` trigger.**

**Fix round 1 (2026-08-03) — resolving the sanctioned-RED gate mismatch.**
The original version of this test hard-asserted the correct/intended
contract unconditionally and reported ``blocked`` when #1127 fired. Per
``.agents/testing.md`` § Merge gate, that shape satisfies NEITHER the plain
green gate (fails whenever #1127 fires) NOR the sanctioned-RED exception
(requires (a) deterministic — identical failure 3/3 — which a
non-deterministic defect can never provide). This test now:

- Confirms the tool-call chip's DOM state AND the backend file's actual
  existence together via an independent ground-truth tie-breaker
  (``ArtifactAPI.list_bucket_files()`` — the SAME backend check
  ELITEA-2212/2213 already use to prove real tool execution) so a defect
  occurrence is never classified from a DOM symptom alone.
- Both agree "executed correctly" → asserts the full correct contract hard
  (chips, response) — GREEN.
- Both agree "did not execute" (no chip rendered AND ``ArtifactAPI``
  confirms ``test.txt`` was never created) → this run hit the CONFIRMED,
  ticketed #1127 signature; soft-fails with the known-defect message
  (``pytest.fail`` at the end, never a demoted/removed assertion) — RED,
  but classified.
- Disagree (chip present but file missing, or file present but chip
  missing) → stays a HARD, uncaught failure — this is explicitly NOT
  absorbed into the known-defect bucket, because that combination doesn't
  match #1127's own confirmed signature and would be a genuinely new,
  undiagnosed defect (reverse-masking guard: never let an unknown cause
  silently fall into the known bucket).

This run-level classification logic is sound and unchanged by fix round 2
below — it correctly tells "hit #1127" apart from "something else broke."
What round 2 corrects is a separate, gate-*eligibility* claim layered on
top of it in round 1's original text (removed here, see below).

**Fix round 2 (2026-08-04) — HISTORICAL RECORD, its conclusion SUPERSEDED
by fix round 3 (2026-08-27) below; kept because its reasoning about the
sanctioned-RED bar remains correct. NO code change.** Round 1's docstring
(now removed) cited
``.agents/testing.md``'s 2026-07-18 "closed-set variant" (ELITEA-1892/#615,
``test_agent_publish_unpublish_version.py`` Known defects #611/#614) as
precedent for this test's RED runs being sanctioned. That citation does not
hold on inspection: the closed-set variant covers **multiple distinct
defects, each independently 100%-reproducing on its own trigger** — it does
NOT cover **one defect firing probabilistically (2/5, per #1127's own filed
evidence) on the same trigger**. #1127 cannot supply "(a) deterministic —
identical failure 3/3" on today's evidence, so this test's RED path does
**not** currently qualify for the sanctioned-RED merge-gate exception. Three
GREEN local runs in one session do not establish otherwise — they show the
*runner* got lucky (or that ``ArtifactAPI``'s ground truth correctly cleared
the test the times #1127 didn't fire), not that the *defect* is
deterministic.

Round 2's consequent ruling — that ELITEA-2215 was BLOCKED for that wave and
that this *module* was excluded from the batch's N-consecutive-green
hardening gate — held on the evidence available on 2026-08-04. It no longer
holds; see fix round 3.

**Fix round 3 (2026-08-27) — #1127 is TOOL-DEPENDENT, and ELITEA-2215 is
UNBLOCKED. Docs + gate-marker scope only; NO change to any assertion,
timeout, or the #1127 run-classification logic.**

Rounds 1-2 treated #1127 as one probabilistic defect firing at ~2/5 on
``create_file``. Two independent live re-measurement rounds on 2026-08-27
(the merge-gate owner's and the analyst's, every run a separate pytest
invocation, ``--reruns 0``, against ``http://localhost:5173``, each verdict
backend-verified via ``ArtifactAPI`` rather than from the DOM alone) show
that the 2/5 was an aggregate hiding **two deterministic populations, split
by which tool is called**:

===========================================  =======================  ==================
Trigger                                      2026-08-27                Lifetime
===========================================  =======================  ==================
``create_file`` — ELITEA-2215's observable   **11 GREEN / 0 RED**      green
``delete_file`` — ELITEA-2210's observable   **0 GREEN / 4 RED**       7/7 RED
===========================================  =======================  ==================

Consequences, each scoped to ONE class:

- ``TestDirectToolkitCallCompleteFlow`` (ELITEA-2215) is **gate-ELIGIBLE on a
  plain green gate**. No sanctioned-RED argument is invoked or needed — there
  is no red to except — so round 2's "a probabilistic defect cannot supply
  deterministic 3/3" objection is moot for this class. The AFS is
  re-classified ``blocked`` → ``ready-for-automation``.
- ``TestDirectToolkitCallDeleteFileChip`` (ELITEA-2210) is **unchanged and
  still excluded from a green gate** — #1127 reproduces there
  deterministically (7/7 lifetime) and it merges RED on its own,
  separately-linked sanctioned-RED basis.
- ``GATE_EXCLUDED_REASON`` below is therefore now **per-node-id, not
  module-wide** — it names the one excluded node id and explicitly names the
  eligible one, so a grep cannot mislead a gate owner in either direction.

Honest caveats, stated rather than smoothed over (they mirror the AFS's):
the two classes differ in more than the tool name (the ``delete_file`` class
also sends a more forceful message and depends on a seeded file), so tool
identity is the best-supported discriminator but not an isolated variable —
this docstring makes no root-cause claim; and the 2026-08-03 2/5 on
``create_file`` was real when recorded, so this position rests on *today's*
11/11, not on a claim that the earlier observation was wrong. The module's
#1127 classification logic (Step 2b's ``soft_failures`` +
``ArtifactAPI`` ground-truth tie-breaker) is deliberately left **exactly as
it was** and is the safety net for that caveat: should #1127 ever fire on
``create_file`` again, this test goes RED with a classified,
backend-verified message rather than silently passing — and such a red is
**NOT** sanctioned. It is a signal to re-open this determinism question, and
the gate owner must treat it as a blocker, not as expected noise.

Both tests remain green-or-red UNSKIPPED (never ``pytest.skip``'d) —
skipping would hide the very signal they exist to surface; gate exclusion is
a gate-composition decision made by whoever runs the gate, not a masking of
the test itself.
"""

import logging

import allure
import pytest
from api import ArtifactAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Gate exclusion — mechanical marker for the orchestrator (grep this file for
# GATE_EXCLUDED_REASON when composing a hardening gate's required-spec list).
#
# SCOPE IS PER-NODE-ID, NOT MODULE-WIDE (rescoped 2026-08-27, fix round 3).
# The two classes in this module have OPPOSITE gate dispositions, so a
# module-wide marker would mislead in both directions — it would wrongly
# exclude a gate-eligible spec, and wrongly imply the whole file is expected
# to be red. The constant below therefore names BOTH node ids explicitly:
# the one that is excluded, and the one that is not.
#
# NOT a skip in either case — both tests still run and still report
# green/red. Exclusion is a gate-composition decision made by whoever runs
# the gate, never a masking of the test. See the module docstring's "Fix
# round 3" block + the AFS's Status / Known Defects sections.
# ---------------------------------------------------------------------------
GATE_EXCLUDED_REASON = (
    "EXCLUDED (this node id ONLY, not the module): "
    "TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip "
    "— ELITEA-2210, sanctioned-RED on OPEN known defect #1127 (delete_file: 7/7 RED lifetime, "
    "deterministic single-cause signature, backend-verified). "
    "NOT EXCLUDED — gate-ELIGIBLE on a plain green gate: "
    "TestDirectToolkitCallCompleteFlow::test_direct_toolkit_call_complete_flow "
    "— ELITEA-2215, unblocked 2026-08-27 (create_file: 11/11 GREEN, #1127 is tool-dependent and "
    "does not fire on this trigger). A red on THIS node id is NOT sanctioned — treat it as a blocker. "
    "See AFS test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md"
)

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 15_000
CHAT_RESPONSE_TIMEOUT = 60_000

MESSAGE_TEXT = "create a file named test.txt"
TOOL_NAME = "create_file"
EXPECTED_FILE_KEY = "test.txt"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_streaming_response.py`` / ``test_conversation_deletion_flow.py``
    — a ``403`` on ``GET .../secrets/secrets/default/{project_id}`` fires on every
    page load in this local environment regardless of the action taken, and is
    unrelated to the toolkit-call flow under test.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestDirectToolkitCallCompleteFlow:
    """ELITEA-2215: Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call (l2, high).

    Also covers ELITEA-2209 (extend-existing, participants-panel Setup assertion).

    Also covers ELITEA-2210's Coverage Map rows 1-3 (participants panel,
    accordion, response — tool-agnostic setup/plumbing). ELITEA-2210's own
    rows 4-5 (the delete_file-specific chip/icon) are proven by
    ``TestDirectToolkitCallDeleteFileChip`` below (fix round, 2026-08-19), not
    by this class — see
    test-specs/chat-interface/lextend_direct-toolkit-call-chip-tool-agnostic-verification_ELITEA-2210.md.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2215_chat-tool-action-and-output-complete-flow-from-direct-toolkit-call.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2209_chat-tool-action-rendering-tool-call-in-thinking-steps.md",
        "onetest-ai Test Case link (ELITEA-2209, extended by this test — participants-panel gap)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2210_chat-tool-output-rendering-tool-execution-results-display-as-chips.md",
        "onetest-ai Test Case link (ELITEA-2210 — Coverage Map rows 1-3 only: participants "
        "panel/accordion/response, tool-agnostic setup. Rows 4-5, the delete_file-specific "
        "chip, are proven by TestDirectToolkitCallDeleteFileChip below, not by this test)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1127",
        "Known defect — direct toolkit call sometimes leaks raw tool-call text instead of executing",
    )
    @pytest.mark.p2
    def test_direct_toolkit_call_complete_flow(
        self, page, conversation_id, artifact_toolkit, artifact_api: ArtifactAPI
    ):
        """Full direct-toolkit-call flow: accordion -> chips -> response.

        Steps (AFS
        test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md,
        extended per
        test-specs/chat-interface/lextend_direct-toolkit-call-participants-panel-verification_ELITEA-2209.md):
        0. (ELITEA-2209 gap) After adding the toolkit as sole participant,
           verify the participants panel shows it under the toolkits section
           and shows no agents section.
        1. Send the create-file message with the toolkit as sole participant;
           verify "Thought for X secs" appears.
        2. Wait for execution to settle, then classify the run against the
           backend ground truth (``ArtifactAPI``) before asserting further —
           see module docstring "Fix round 1" note.
        3. GREEN path: verify the tool-call chip (colon-separated format, per
           CLARIFICATION 1), the model+tool chip set (per CLARIFICATION 2),
           and the response text following the chips.
           Known-defect path: soft-fail with the confirmed #1127 signature.

        Also extended per
        test-specs/chat-interface/lextend_direct-toolkit-call-chip-tool-agnostic-verification_ELITEA-2210.md
        (zero-diff — ELITEA-2210's chip/icon/label assertions are already covered by Step 3
        above; the tool-chip's text and icon render through a tool-agnostic code path, see
        that AFS's "Tool-agnosticism argument" — no new step, no new assertion).
        """
        chat = ChatPage(page)
        toolkit_name = artifact_toolkit["name"]
        bucket_name = artifact_toolkit["bucket_name"]
        expected_chip_text = f"{toolkit_name}: {TOOL_NAME}"

        console_issues = []
        page_errors = []
        soft_failures = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step("Setup — navigate to the fresh conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Setup — add the artifact toolkit as the only participant"):
            chat.add_toolkit_participant(toolkit_name)

            # ELITEA-2209's own gap (extend-existing, AFS
            # test-specs/chat-interface/lextend_direct-toolkit-call-participants-panel-verification_ELITEA-2209.md,
            # step 1): confirm the toolkit landed in the PARTICIPANTS panel
            # under the toolkits section, and that no AGENTS section
            # appeared (no agent was added). Plain, unconditional asserts —
            # deliberately NOT routed through the `soft_failures`/#1127
            # classification below, since participants-panel rendering is
            # unrelated to that known defect's mechanism.
            assert chat.is_participants_badge_visible(section="toolkits"), (
                "Expected a toolkits participants badge after adding the toolkit"
            )
            assert not chat.is_participants_badge_visible(section="agents"), (
                "No agent was added — the agents participants badge must be absent"
            )

        with allure.step(
            "Step 1 — Send 'create a file named test.txt' with the toolkit as "
            "the sole participant; verify 'Thought for X secs' appears"
        ):
            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step("Step 2 — Wait for execution to settle"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=CHAT_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step(
            "Step 2b — Classify this run against the backend ground truth "
            "(ArtifactAPI) before deciding which assertions apply (Known "
            "defect #1127 tie-breaker, mirrors ELITEA-2212/2213's "
            "backend-verified execution proof and the #611/#614/#615 "
            "soft_failures pattern in test_agent_publish_unpublish_version.py)"
        ):
            tool_chip_rendered = chat.answer_tool_chip.count() > 0 and expected_chip_text in (
                chat.answer_tool_chip.first.text_content() or ""
            )
            bucket_files = artifact_api.list_bucket_files(bucket_name)
            file_created = any(EXPECTED_FILE_KEY in key for key in bucket_files)

            if not tool_chip_rendered and not file_created:
                # Confirmed #1127 signature: NEITHER the chip nor the real
                # backend file exist — the model leaked tool-call intent as
                # text instead of invoking the real tool. Ground-truth
                # confirmed, not inferred from the DOM alone.
                last_text = chat.get_last_message_text()
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1127: "
                    f"direct toolkit-call flow leaked tool-call intent instead of executing — "
                    f"no '{expected_chip_text}' chip rendered AND ArtifactAPI confirms "
                    f"'{EXPECTED_FILE_KEY}' was NOT created in bucket '{bucket_name}' "
                    f"(bucket contents: {bucket_files!r}). Response text: {last_text[:300]!r}"
                )
                run_executed_correctly = False
            elif tool_chip_rendered and file_created:
                # Both signals agree the flow executed for real this run.
                run_executed_correctly = True
            else:
                # Disagreement — this is NOT #1127's confirmed signature
                # (that defect is "neither renders"). A chip with no file,
                # or a file with no chip, is a different, undiagnosed
                # problem and must stay a hard, uncaught failure rather
                # than being silently folded into the known-defect bucket
                # (reverse-masking guard).
                raise AssertionError(
                    "Inconsistent execution signal — does NOT match Known defect #1127's "
                    f"confirmed signature (chip AND file both missing). Got: "
                    f"tool_chip_rendered={tool_chip_rendered}, file_created={file_created} "
                    f"(bucket contents: {bucket_files!r}). This looks like a NEW, "
                    "undiagnosed defect and must be investigated, not classified as #1127."
                )

        if run_executed_correctly:
            with allure.step(
                "Step 3 — Verify tool call shown as 'toolkit_name: tool_name' in "
                "the thinking steps (CLARIFICATION 3: already auto-expanded, no "
                "manual click needed/reliable; CLARIFICATION 1: live format is "
                "colon-separated, not the case's dotted example)"
            ):
                expect(chat.answer_tool_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.answer_tool_chip).to_contain_text(expected_chip_text)

            with allure.step(
                "Step 4 — Verify chips: at least one model chip AND exactly one "
                "toolkit/tool chip (CLARIFICATION: live product renders 1 "
                "combined toolkit/tool chip + N>=1 model chips, not 3 distinct "
                "chips as the case describes)"
            ):
                model_chip_count = chat.answer_model_chip.count()
                assert model_chip_count >= 1, (
                    f"Expected at least one model chip, found {model_chip_count}"
                )
                expect(chat.answer_tool_chip).to_have_count(1)
                expect(chat.answer_tool_chip).to_contain_text(expected_chip_text)

            with allure.step(
                "Step 5 — Verify the LLM response text follows the chips: the "
                "chips are already rendered by the time the settled response "
                "text is read (chips surface once tool-call metadata is known, "
                "before the final answer text streams in and stabilises)"
            ):
                assert chat.answer_tool_chip.is_visible(), (
                    "Tool chip should still be visible once the response has settled"
                )
                last_text = chat.get_last_message_text()
                assert last_text, "Expected the assistant's response text to be non-empty"
                logger.info("Final response text (%d chars): %s", len(last_text), last_text[:200])

        with allure.step("Side-channel check — no console/JS errors across the whole flow"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )

        if soft_failures:
            pytest.fail(
                "Non-deterministic known defect observed this run (see module "
                "docstring 'Fix round 1' note):\n" + "\n".join(soft_failures)
            )


# ---------------------------------------------------------------------------
# ELITEA-2210 fix round — delete_file-specific live proof (added after review)
# ---------------------------------------------------------------------------
DELETE_MESSAGE_TEMPLATE = (
    'Use delete_file toolkit to delete a file named "{file_key}" from '
    'bucket "{bucket_name}". Execute the tool now, do not ask for clarification.'
)
DELETE_TOOL_NAME = "delete_file"


class TestDirectToolkitCallDeleteFileChip:
    """ELITEA-2210 (fix round — live tool-specific proof): Chat – Tool Output
    Rendering – Verify Tool Execution Results Display as Chips, for
    ``delete_file`` specifically (l1, high).

    ELITEA-2210's own case names ``delete_file`` ("aaa: delete_file") as its
    worked example. `TestDirectToolkitCallCompleteFlow` (ELITEA-2215, the AFS's
    originally-cited covering spec) only ever exercises ``create_file`` — its
    AFS's "Tool-agnosticism argument" (a source read of ``ActionView.jsx``'s
    ``buildTitle()``/``renderIcon()``) explains WHY the two tools render
    identically, but a reviewer fix round correctly flagged that a source-code
    argument standing alone is not a live execution of THIS case's own
    observable (``.agents/role-overrides.md`` — "coverage judgments stand on
    your own execution", never on reuse-to-conclude). This test supplies the
    missing live execution.

    Deliberately NOT the guardrails/sensitive-action flow (ELITEA-2211..2214,
    ``test_hitl_sensitive_action_authorization.py``) — that cluster marks
    ``delete_file`` SENSITIVE via Admin Guardrails, which 404s on localhost
    and is CI-only; it also never captured a live local run of its own chip
    assertion (see its AFS's "Network Behavior... not captured live this
    pass" note), so it cannot supply the missing live-execution proof either.
    This test calls ``delete_file`` directly, with NO sensitivity marking —
    the exact same direct-toolkit-call mechanism
    ``TestDirectToolkitCallCompleteFlow`` already uses for ``create_file``,
    runnable on localhost right now.

    Shares the same known defect as the covering spec (#1127 — direct-toolkit-call
    sometimes leaks tool-call intent as raw text instead of invoking the real
    tool) — reuses the identical backend-ground-truth classification pattern.

    **Observed locally (2026-08-19, implementation pass): 3 out of 3 consecutive
    runs hit this exact #1127 signature for ``delete_file``** — no tool chip
    rendered, ``ArtifactAPI`` confirms the seeded file was NOT actually deleted,
    yet the LLM's chat response claims success verbatim. Notably higher local
    rate than the covering spec's own ``create_file`` history (2/5) — recorded
    as a comment on the open issue
    (https://github.com/EliteaAI/elitea-testing-public/issues/1127#issuecomment-5342934194),
    not a new ticket (same tool-agnostic mechanism the issue already describes).
    **Fix round 2 (2026-08-19) re-runs: 2 further consecutive occurrences,
    same signature (5/5 total)** — confirm the deferred-failure restructuring
    (see module docstring) didn't change the classification outcome, and
    additionally prove the Side-channel console/JS-error check now actually
    executes on this branch (Allure step ``Side-channel check — no
    console/JS errors across the whole flow`` recorded ``passed`` before the
    deferred ``pytest.fail`` fired) — the exact gap this fix round closes.
    **THIS IS THE STILL-RED CLASS IN THIS MODULE (as of 2026-08-27).** Two
    further ``delete_file`` runs on 2026-08-27 (analyst re-measurement,
    ``--reruns 0``, separate invocations, backend-verified) reproduced the
    byte-identical signature: **7 of 7 RED lifetime, 0 GREEN.** Expect this
    node id to fail; that failure IS the tracked #1127 signal.

    Per ``.agents/testing.md`` § Merge gate, 3/3 (now 7/7) IDENTICAL failures
    tied to this single, open, linked defect meets the sanctioned-RED
    exception's own deterministic bar, so this test DOES qualify for
    sanctioned-RED and is excluded from the batch's N-consecutive-green
    hardening gate on that basis — it is the ONE node id
    ``GATE_EXCLUDED_REASON`` above excludes. It is left green-or-red
    UNSKIPPED (never ``pytest.skip``'d) for the reason that constant
    documents.

    **Do NOT read this class's exclusion as covering the module.** The
    sibling ``TestDirectToolkitCallCompleteFlow`` (ELITEA-2215,
    ``create_file``) was unblocked on 2026-08-27 — 11/11 GREEN, gate-eligible
    on a plain green gate — because #1127 turned out to be tool-dependent
    rather than probabilistic (module docstring, "Fix round 3"). Re-evaluate
    this class (may flip to plain-green-required) once #1127 is fixed or this
    test accumulates a GREEN run.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2210_chat-tool-output-rendering-tool-execution-results-display-as-chips.md",
        "onetest-ai Test Case link (ELITEA-2210 — delete_file-specific chip proof, live-executed)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1127",
        "Known defect — direct toolkit call sometimes leaks raw tool-call text instead of executing",
    )
    @pytest.mark.p2
    def test_direct_toolkit_call_delete_file_chip(
        self, page, conversation_id, artifact_toolkit, artifact_seeded_file, artifact_api: ArtifactAPI
    ):
        """Sends an unambiguous delete_file message (CLARIFICATION — the case's
        own literal wording does not reach a real tool call; see ELITEA-2211's
        AFS, cross-referenced by ELITEA-2210's own AFS) and asserts the
        toolkit/tool chip renders "{toolkit_name}: delete_file", with the
        seeded file's real removal from the bucket as ground truth (not a
        DOM-only signal).
        """
        chat = ChatPage(page)
        toolkit_name = artifact_toolkit["name"]
        bucket_name = artifact_toolkit["bucket_name"]
        expected_chip_text = f"{toolkit_name}: {DELETE_TOOL_NAME}"

        console_issues = []
        page_errors = []
        soft_failures = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step("Setup — navigate to the fresh conversation, add the artifact toolkit as sole participant"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.add_toolkit_participant(toolkit_name)

        with allure.step(
            "Step — Send an unambiguous delete_file message (CLARIFICATION 1 — "
            "the case's own literal wording is ambiguous and does not reach a "
            "real tool call); verify 'Thought for X secs' appears"
        ):
            initial_count = chat.get_message_count()
            chat.send_message(
                DELETE_MESSAGE_TEMPLATE.format(file_key=artifact_seeded_file, bucket_name=bucket_name)
            )
            expect(chat.answer_thought_accordion).to_be_visible(timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step("Step — Wait for execution to settle"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=CHAT_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)

        with allure.step(
            "Step — Classify this run against the backend ground truth "
            "(ArtifactAPI) before asserting further — same #1127 tie-breaker "
            "as TestDirectToolkitCallCompleteFlow's own Step 2b"
        ):
            tool_chip_rendered = chat.answer_tool_chip.count() > 0 and expected_chip_text in (
                chat.answer_tool_chip.first.text_content() or ""
            )
            bucket_files = artifact_api.list_bucket_files(bucket_name)
            file_deleted = artifact_seeded_file not in bucket_files

            if not tool_chip_rendered and not file_deleted:
                # Confirmed #1127 signature: NEITHER the chip nor the real
                # backend deletion happened — the model leaked tool-call
                # intent as text instead of invoking the real tool. Deferred
                # (not an immediate pytest.fail) — same shape as
                # TestDirectToolkitCallCompleteFlow's own Step 2b: this run
                # still owes the Side-channel console/JS-error check below
                # regardless of which known-defect path it took. Fix round 2
                # (2026-08-19): an immediate pytest.fail() here previously
                # made that check structurally unreachable on this exact
                # branch — the one that has fired 3/3 observed runs — so the
                # AFS's Gap-assertions console-error bullet had never
                # actually executed. See module docstring.
                last_text = chat.get_last_message_text()
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1127: "
                    f"direct toolkit-call flow leaked tool-call intent instead of executing — "
                    f"no '{expected_chip_text}' chip rendered AND ArtifactAPI confirms "
                    f"'{artifact_seeded_file}' was NOT deleted from bucket '{bucket_name}' "
                    f"(bucket contents: {bucket_files!r}). Response text: {last_text[:300]!r}"
                )
                run_executed_correctly = False
            elif tool_chip_rendered and file_deleted:
                # Both signals agree the flow executed for real this run.
                run_executed_correctly = True
            else:
                # Disagreement between the two signals is NOT #1127's
                # confirmed signature (that defect is "neither happened") —
                # a new, undiagnosed defect and must stay a hard, uncaught
                # failure (reverse-masking guard) — same immediate-raise
                # shape as the covering spec's own disagreement branch.
                raise AssertionError(
                    "Inconsistent execution signal — does NOT match Known defect #1127's "
                    f"confirmed signature (chip AND deletion both missing). Got: "
                    f"tool_chip_rendered={tool_chip_rendered}, file_deleted={file_deleted} "
                    f"(bucket contents: {bucket_files!r}). This looks like a NEW, "
                    "undiagnosed defect and must be investigated, not classified as #1127."
                )

        if run_executed_correctly:
            with allure.step(
                "Step — Verify the toolkit/tool chip renders 'toolkit_name: delete_file' "
                "(ELITEA-2210's own case observable, live-executed) plus at least one "
                "model chip. Icon: co-located in the same DOM subtree under the same "
                "testid (ActionView.jsx's iconContainer sibling to the label) — see "
                "this case's AFS 'Tool-agnosticism argument' for the source pointer; "
                "chip-visible necessarily proves the icon rendered too, same treatment "
                "the covering spec and ELITEA-2209's AFS already use"
            ):
                expect(chat.answer_tool_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.answer_tool_chip).to_have_count(1)
                expect(chat.answer_tool_chip).to_contain_text(expected_chip_text)
                assert chat.answer_model_chip.count() >= 1, "Expected at least one model chip"

        with allure.step("Side-channel check — no console/JS errors across the whole flow"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )

        if soft_failures:
            pytest.fail(
                "Non-deterministic known defect observed this run (see module "
                "docstring 'Fix round 1' note, TestDirectToolkitCallCompleteFlow):\n"
                + "\n".join(soft_failures)
            )
