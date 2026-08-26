"""UI Tests for Chat HITL Sensitive Action Authorization (direct toolkit call).

Covers ELITEA-2211..2214 — the "+ > Toolkits" direct-toolkit-call flow (no
agent) that triggers the Sensitive Action Authorization card when a tool is
marked sensitive in the org's Guardrails configuration, and the three ways to
resolve it (Authorize / Block / Block with Comment).

Test Cases (1 manual = 1 auto each, 4 cases in this module):
- ELITEA-2211: Sensitive Action Authorization Card Displays When Toolkit Called Directly
- ELITEA-2212: Click Authorize Executes the Toolkit Tool Directly
- ELITEA-2213: Click Block Prevents the Toolkit Tool from Executing
- ELITEA-2214: Block with Comment Records the Reason and Blocks the Toolkit Action

Specs:
- test-specs/chat-interface/l2_hitl-sensitive-action-card-display_ELITEA-2211.md
- test-specs/chat-interface/l2_hitl-sensitive-action-authorize_ELITEA-2212.md
- test-specs/chat-interface/l2_hitl-sensitive-action-block_ELITEA-2213.md
- test-specs/chat-interface/l2_hitl-sensitive-action-block-with-comment_ELITEA-2214.md

PRECONDITION — TRANSIT SUBSTITUTION (AFS § Fidelity Declaration): the
``sensitive_delete_file_toolkit`` module-scoped fixture
(``fixtures/data_fixtures.py``) marks ``artifact``/``delete_file`` sensitive
through the guardrails **config REST endpoint**
(``PUT {api}/admin/plugin_config_values/administration/guardrails``), not
through the Admin UI, because the Admin UI is a separate deployed application
that ``localhost:5173`` does not serve at all (there is no ``/admin`` route in
``EliteaUI/src/routes.js``; issue #1140 tracks the route, and
``test_guardrails_live_reload.py`` / ``test_guardrails_cleanup_only.py``
genuinely do test that UI and keep their ``guardrails`` marker — this module
does not). The substitution only *reaches* the step under test: every
observable these four cases assert on — the card, its heading, its action name,
its three buttons, and whether the tool actually executed — is produced end to
end by the real LLM → real tool call → real backend interrupt → real WebSocket
frame. Nothing is mocked, injected or intercepted.

The flag applies immediately (``requires_restart: []``) and is toolkit-TYPE
scoped, so it is a real ORG-WIDE side effect while the module runs: the fixture
captures the original configuration, mutates it additively, and restores the
captured original verbatim in a ``finally`` (verified by readback). Do not run
this module under ``pytest-xdist`` alongside artifact-toolkit suites.

Each case reaches its OWN fresh Sensitive Action Authorization card (own
``conversation_id`` + own ``artifact_toolkit`` — both function-scoped fixtures)
— never a shared conversation/resume state across 2212/2213/2214, matching
the isolation precedent ELITEA-2015 established for pipeline HITL Approve vs
Reject (AFS § Preconditions).

CLARIFICATION (case-text ambiguity, confirmed live, not a defect): the case's
own message text ("use delete_file toolkit to remove from the bucket all
files") does NOT reach a real tool-call attempt against a project with many
existing buckets — the LLM asks a clarifying question instead ("which
bucket(s)?"). These tests use an unambiguous message naming the bucket and
file explicitly instead (AFS § Test Data).

Testids this cluster added to EliteaUI for its own executed path —
``sensitive-action-block-button``, ``sensitive-action-block-with-comment-button``,
``sensitive-action-block-comment-input``, ``sensitive-action-block-comment-submit-button``
(``ChatHitlActions.jsx`` / ``BlockWithCommentControl.jsx``), plus the shared
``chat-answer-tool-chip`` ask (ELITEA-2212 asserts presence, ELITEA-2213
asserts absence — canon ruling #277 shape (b)) — are all present on
``EliteaAI/EliteaUI`` ``main`` (verified 2026-08-27), so nothing here waits on a
cherry-pick.
"""

import logging

import allure
import pytest
from api import ArtifactAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger("elitea.tests.chat")

# No ``guardrails`` marker: the precondition is a REST config write, not the
# Admin UI, so this module belongs in the local loop (AFS rework delta row 3).
pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 15_000
CHAT_RESPONSE_TIMEOUT = 60_000
SENSITIVE_ACTION_TIMEOUT = 30_000

SENSITIVE_TOOLKIT_TYPE = "artifact"
SENSITIVE_TOOL_NAME = "delete_file"

# Response phrases that would indicate the delete actually went through —
# used as the "does NOT claim success" half of the loose Block-acknowledgement
# signal (AFS: the exact LLM wording is non-deterministic, so the assertion is
# on what the response must NOT claim, not on a literal string).
_SUCCESS_CLAIM_PHRASES = (
    "deleted successfully",
    "has been deleted",
    "successfully removed",
    "successfully deleted",
)


def _unambiguous_delete_message(bucket_name: str, file_key: str) -> str:
    """Explicit-bucket delete_file message (AFS § Test Data — CONFIRMED CASE-TEXT
    AMBIGUITY: the case's own wording does not reach a real tool-call attempt)."""
    return (
        f'Use delete_file toolkit to delete a file named "{file_key}" from '
        f'bucket "{bucket_name}". Execute the tool now, do not ask for clarification.'
    )


def _reach_sensitive_action_card(
    page, conversation_id: str, toolkit: dict, file_key: str
) -> ChatPage:
    """Shared setup for ELITEA-2211..2214 — reach a FRESH Sensitive Action
    Authorization card in *this test's own* conversation.

    Covers each case's own steps 1 ("add toolkit via + > Toolkits", "toolkit
    in PARTICIPANTS") through the card becoming visible.

    The toolkit row is resolved by its dynamic testid
    (``add_toolkit_participant_via_slash_menu``), NOT by the legacy
    name-search flow (``add_toolkit_participant``). That is both the
    locator-policy-compliant shape (``.agents/testing.md`` § Locator policy —
    the legacy flow resolves by accessible name / ``:has-text``) and a
    correctness fix: the legacy flow types into a non-debounced search field
    and clicks whatever ``li[role="menuitem"]`` matches first, which was
    observed live (2026-08-27, 3/3 runs) to leave the toolkit UNATTACHED —
    the LLM then had no tool to call, answered that it had deleted the file
    while the file was still in the bucket, and no HITL interrupt ever fired.
    The attachment is therefore asserted explicitly here (AFS step 3's own
    "Toolkits in this conversation" verification) instead of being inferred
    from a downstream signal.
    """
    chat = ChatPage(page)
    toolkit_name = toolkit["name"]
    bucket_name = toolkit["bucket_name"]
    chat.navigate_to_chat(conversation_id=conversation_id)

    with allure.step(f"Step 1 — Add toolkit '{toolkit_name}' via + > Toolkits (no agent)"):
        chat.add_toolkit_participant_via_slash_menu(
            project_id=toolkit["project_id"], toolkit_id=toolkit["id"], timeout=UI_ELEMENT_TIMEOUT,
        )
        chat.close_plus_menu_popper()
        assert chat.is_participants_badge_visible(section="toolkits"), (
            f"TOOLKITS participants badge should appear after adding '{toolkit_name}' "
            "— without it the model has no tool to call and cannot trigger the HITL interrupt"
        )

    with allure.step("Step 2 — Send message triggering the sensitive action"):
        chat.send_message(_unambiguous_delete_message(bucket_name, file_key))
        expect(chat.answer_thought_accordion).to_be_visible(timeout=CHAT_RESPONSE_TIMEOUT)

    with allure.step("Step 3 — Verify the Sensitive Action Authorization card appears"):
        appeared = chat.wait_for_sensitive_action_panel(timeout=SENSITIVE_ACTION_TIMEOUT)
        assert appeared, "Sensitive Action Authorization card should appear for a sensitive delete_file call"

    return chat


# ===========================================================================
# ELITEA-2211: Sensitive Action Authorization Card Displays
# ===========================================================================


class TestSensitiveActionCardDisplay:
    """ELITEA-2211: Chat – HITL – Sensitive Action Authorization Card Displays for a Direct Toolkit Call (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2211_chat-hitl-authorization-card-displays-for-sensitive-action.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_sensitive_action_card_displays_for_direct_toolkit_call(
        self,
        page,
        conversation_id: str,
        artifact_toolkit: dict,
        artifact_seeded_file: str,
        sensitive_delete_file_toolkit,
    ):
        """Card shows correct heading, action-name block, and exactly 3 buttons.

        TRANSIT SUBSTITUTION (declared, AFS § Fidelity Declaration): only the
        precondition is substituted — ``sensitive_delete_file_toolkit`` marks
        ``artifact``/``delete_file`` sensitive over REST because the Admin UI is
        not served on localhost. The card itself and every value asserted below
        come from the real backend HITL flow.
        """
        toolkit_name = artifact_toolkit["name"]

        console_issues = collect_console_errors(page)
        page_errors = []

        page.on("pageerror", lambda e: page_errors.append(str(e)))

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step("Step 4 — Verify heading text 'Sensitive Action Authorization Required'"):
            expect(chat.sensitive_action_panel).to_contain_text(
                "Sensitive Action Authorization Required"
            )

        with allure.step(
            "Step 5 — Verify 'Agent is about to perform:' + the composed "
            "'{toolkit_name}.{tool_name}' action name (the case's "
            "'aaa.delete_file' is the literal format — live-verified)"
        ):
            expect(chat.sensitive_action_panel).to_contain_text("Agent is about to perform:")
            expect(chat.sensitive_action_panel).to_contain_text(
                f"{toolkit_name}.{SENSITIVE_TOOL_NAME}"
            )

        with allure.step(
            "Step 6 — Verify all three buttons render: Authorize, Block, Block with Comment"
        ):
            expect(chat.sensitive_action_authorize_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_with_comment_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Side-channel check — no console/JS errors across the whole flow"):
            # Errors only. The backend also emits an unhandled `parallel_hitl_ready`
            # socket message during this flow, which the frontend logs as a
            # console.WARNING (# Known defect: #1831) — a warning is not captured
            # here, and this assertion must not be widened to swallow it.
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {console_issues!r}; "
                f"page errors: {page_errors!r}"
            )

        with allure.step(
            "Cleanup (not a case step) — resolve the pending card with Block so "
            "the conversation is not left paused before it is deleted"
        ):
            chat.sensitive_action_block_button.first.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)


# ===========================================================================
# ELITEA-2212: Click Authorize Executes the Toolkit Tool Directly
# ===========================================================================


class TestSensitiveActionAuthorize:
    """ELITEA-2212: Chat – HITL Authorization – Click Authorize Executes the Toolkit Tool Directly (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2212_chat-hitl-authorization-click-authorize-executes-toolkit-directly.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_authorize_executes_toolkit_tool_directly(
        self,
        page,
        conversation_id: str,
        artifact_toolkit: dict,
        artifact_seeded_file: str,
        artifact_api: ArtifactAPI,
        sensitive_delete_file_toolkit,
    ):
        """Authorize closes the card and the delete_file call genuinely executes
        (backend-verified via ArtifactAPI, not just a UI-only signal)."""
        toolkit_name = artifact_toolkit["name"]
        bucket_name = artifact_toolkit["bucket_name"]

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step(
            "Step — Verify all three action buttons are visible on THIS "
            "case's own card instance (independent verification — fix round "
            "1: the AFS Coverage Map row 1 previously cited ELITEA-2211, a "
            "same-batch/not-yet-merged spec, as the sole site of this "
            "assertion, which is not a valid merged-target citation; this "
            "case now asserts it independently too)"
        ):
            expect(chat.sensitive_action_authorize_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_with_comment_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step — Click Authorize; verify the card closes"):
            chat.sensitive_action_authorize_button.first.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step — Verify the toolkit call actually executes: the fixture "
            "file is genuinely gone from the bucket (backend ground truth, "
            "not a UI-only signal)"
        ):
            def _file_deleted() -> bool:
                return artifact_seeded_file not in artifact_api.list_bucket_files(bucket_name)

            expect.poll(_file_deleted, timeout=CHAT_RESPONSE_TIMEOUT).to_be_truthy()

        with allure.step(
            "Step — Verify tool-execution chips: an LLM-model chip AND a "
            "toolkit/tool chip showing '{toolkit_name}: delete_file'"
        ):
            expect(chat.answer_model_chip.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_tool_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_tool_chip).to_contain_text(f"{toolkit_name}: {SENSITIVE_TOOL_NAME}")

        with allure.step("Step — Verify the conversation continues normally (composer re-enabled)"):
            assert chat.message_input.is_editable(), (
                "Message input should be editable again after authorization completes"
            )
            assert chat.sensitive_action_panel.count() == 0, (
                "Sensitive action panel should stay gone once resolved"
            )


# ===========================================================================
# ELITEA-2213: Click Block Prevents the Toolkit Tool from Executing
# ===========================================================================


class TestSensitiveActionBlock:
    """ELITEA-2213: Chat – HITL Authorization – Click Block Prevents the Toolkit Tool from Executing (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2213_chat-hitl-authorization-click-block-prevents-toolkit-execution.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_block_prevents_toolkit_tool_from_executing(
        self,
        page,
        conversation_id: str,
        artifact_toolkit: dict,
        artifact_seeded_file: str,
        artifact_api: ArtifactAPI,
        sensitive_delete_file_toolkit,
    ):
        """Block closes the card without executing — file survives, no tool
        chip renders, and the LLM response acknowledges the block."""
        bucket_name = artifact_toolkit["bucket_name"]

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step(
            "Step — Verify all three action buttons are visible on THIS "
            "case's own card instance (independent verification — fix round "
            "1: the AFS Coverage Map row 1 previously cited ELITEA-2211, a "
            "same-batch/not-yet-merged spec, as the sole site of this "
            "assertion, which is not a valid merged-target citation; this "
            "case now asserts it independently too)"
        ):
            expect(chat.sensitive_action_authorize_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_with_comment_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step — Click Block; verify the card closes"):
            chat.sensitive_action_block_button.first.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step — Verify the toolkit tool does NOT execute: the fixture "
            "file is STILL present (backend ground truth — a UI-only 'card "
            "closed' signal can't distinguish Block from a silent failure)"
        ):
            chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)
            remaining_files = artifact_api.list_bucket_files(bucket_name)
            assert artifact_seeded_file in remaining_files, (
                f"File '{artifact_seeded_file}' should still be present after Block, "
                f"found: {remaining_files}"
            )

        with allure.step(
            "Step — Verify the LLM response acknowledges the block (loose "
            "signal — non-empty, does not claim success; the exact wording is "
            "LLM-nondeterministic, see AFS note)"
        ):
            last_text = chat.get_last_message_text()
            assert last_text.strip(), "Expected a non-empty LLM response acknowledging the block"
            lowered = last_text.lower()
            assert not any(phrase in lowered for phrase in _SUCCESS_CLAIM_PHRASES), (
                f"Response should not claim the delete succeeded: {last_text!r}"
            )

        with allure.step(
            "Step — Verify NO tool-execution chip renders for the blocked "
            "tool (absence assertion — canon ruling #511, first-class "
            "reference to the shared 'chat-answer-tool-chip' testid)"
        ):
            expect(chat.answer_tool_chip).to_have_count(0)


# ===========================================================================
# ELITEA-2214: Block with Comment Records the Reason and Blocks the Action
# ===========================================================================


class TestSensitiveActionBlockWithComment:
    """ELITEA-2214: Chat – HITL – Block with Comment Records the Reason and Blocks the Action (l2, high)."""

    BLOCK_COMMENT = "This action is too risky and could delete important data"

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2214_chat-hitl-authorization-click-block-with-comment.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_block_with_comment_records_reason_and_blocks_action(
        self,
        page,
        conversation_id: str,
        artifact_toolkit: dict,
        artifact_seeded_file: str,
        artifact_api: ArtifactAPI,
        sensitive_delete_file_toolkit,
    ):
        """Block with Comment expands an inline textarea+submit ON the card
        (source-confirmed: NOT an MUI Dialog — case's own "Modal" wording is
        imprecise, the observable is unaffected), records the typed reason,
        and blocks execution the same way plain Block does."""
        bucket_name = artifact_toolkit["bucket_name"]

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step(
            "Step — Click 'Block with Comment'; verify the inline textarea + "
            "submit control appears IN PLACE on the card"
        ):
            chat.sensitive_action_block_with_comment_button.click()
            expect(chat.sensitive_action_block_comment_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_comment_submit_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step — Type the comment into the textarea"):
            chat.sensitive_action_block_comment_input.click()
            chat.sensitive_action_block_comment_input.press_sequentially(self.BLOCK_COMMENT, delay=20)
            expect(chat.sensitive_action_block_comment_input).to_have_value(self.BLOCK_COMMENT)

        with allure.step("Step — Click Submit; verify the card closes"):
            chat.sensitive_action_block_comment_submit_button.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step — Verify the toolkit tool does NOT execute (backend "
            "ground truth, same pattern as ELITEA-2213)"
        ):
            chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)
            remaining_files = artifact_api.list_bucket_files(bucket_name)
            assert artifact_seeded_file in remaining_files, (
                f"File '{artifact_seeded_file}' should still be present after Block with Comment, "
                f"found: {remaining_files}"
            )

        with allure.step(
            "Step — Verify the LLM response acknowledges the block (same "
            "loose signal as ELITEA-2213 — wording is LLM-nondeterministic)"
        ):
            last_text = chat.get_last_message_text()
            assert last_text.strip(), "Expected a non-empty LLM response acknowledging the block"
            lowered = last_text.lower()
            assert not any(phrase in lowered for phrase in _SUCCESS_CLAIM_PHRASES), (
                f"Response should not claim the delete succeeded: {last_text!r}"
            )
