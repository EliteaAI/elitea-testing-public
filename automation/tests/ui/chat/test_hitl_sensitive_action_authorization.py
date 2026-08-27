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
captured original verbatim in a ``finally`` that is armed BEFORE the mutating
write (so a failure of the readback or its assertion cannot strand the flag),
verified by readback. Do not run this module under ``pytest-xdist`` alongside
artifact-toolkit suites.

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
``chat-answer-tool-chip`` ask (asserted PRESENT, with its text, by BOTH
ELITEA-2212 and ELITEA-2213) — are all present on ``EliteaAI/EliteaUI`` ``main``
(verified 2026-08-27), so nothing here waits on a cherry-pick.

Canon ruling #277 shape (b) — both branches of ``ActionView.jsx``'s
model/tool testid ternary referenced on a test's executed path — is satisfied
**entirely by ELITEA-2212's own path**, which references both POSITIVELY:
``chat-answer-model-chip`` (its Step 7) and ``chat-answer-tool-chip`` (its Step
8). ELITEA-2213 previously carried an absence assertion on the tool chip and no
longer does — that assertion was factually wrong, not a #277 obligation (see
``TestSensitiveActionBlock``'s docstring; clarification issue #1839).

SANCTIONED-RED (``.agents/testing.md`` § Merge gate, closed-set variant): TWO
specs in this module are EXPECTED to end pytest-FAILED — ELITEA-2212
(``TestSensitiveActionAuthorize``) and ELITEA-2213
(``TestSensitiveActionBlock``). Both are the same root-cause family: the HITL
resume drops the turn, whichever decision was taken.

**ELITEA-2212 — ``TestSensitiveActionAuthorize``.** Its closed, enumerable set
of known defects — all on the one dropped authorize-resume, all OPEN, all
soft-routed so every one of them is reported on every run — is:

* **#1834** — the toolkit tool never executes (seeded file still in the bucket
  90 s after Authorize). Fired **7 of 7** runs, 2026-08-27.
* **#1835** — the sensitive-action card, correctly closed ~0.1 s after
  Authorize, is rendered AGAIN ~90 s later with live buttons. Fired **7 of 7**.
* **#1834** — the LLM-model chip never renders. Fired **3 of 7**; the chip DID
  render in the other four runs. This is the subset-firing member the
  closed-set variant explicitly allows.

**What a gate operator should expect, so nobody mistakes it for a new symptom:**
the failure is a ``BaseExceptionGroup`` whose sub-exception count legitimately
alternates between **2 and 3** — 2 when the model chip happens to render, 3 when
it does not. **Both are the SAME signature.** A new symptom means a failure
naming something OUTSIDE the three bullets above; anything else is this set.

**ELITEA-2213 — ``TestSensitiveActionBlock``.** Live re-analysis on 2026-08-27
(AFS § REWORK, two independent runs) established that the BLOCK resume drops the
turn exactly like the authorize one. Its own closed, enumerable set — both OPEN,
both soft-routed, both fired 2/2 runs — is:

* **#1834** — the Block resume drops the turn: no assistant response ever
  arrives (answer body still empty after 230 s / 90 s), no console error, no
  failed request, and the decision is never committed as a tool outcome — the
  NEXT user message re-triggers an identical authorization card.
* **#1835** — the correctly-closed card is rendered AGAIN ~2-6 s later with
  live, ``disabled === false`` buttons, and persists until a page reload.

**What a gate operator should expect here:** a ``BaseExceptionGroup`` with
exactly **2** sub-exceptions — the ``expect.soft`` for #1835 ("the resolved
sensitive-action card must stay gone") and the ``pytest.fail`` drain carrying
#1834 ("the Block resume dropped the turn"). Unlike ELITEA-2212 this count does
not alternate: neither member has been observed to not-fire, and a clean run is
~95 s. A **new symptom** is any failure naming something outside those two
bullets.

One shape in particular must NOT be mistaken for either: a raw, uncaught
assertion inside ``_reach_sensitive_action_card`` — its Step 2
(``chat-answer-thought-accordion`` never becomes visible, i.e. the assistant
never starts a turn) or its Step 3 (``Sensitive Action Authorization card should
appear``). That is the known TRIGGER flake (``.agents/testing.md`` § Unconfirmed;
seen 1 of 4 invocations here on 2026-08-27, and 1 of 6 on the sibling
ELITEA-2212 case). It fires UPSTREAM of everything either case asserts, is not a
member of any closed set, and by construction blocks the gate: **re-run it,
never accept it as the signature.**

Every affected assertion states the CORRECT behaviour, so the spec flips green
unchanged when the product is fixed. A green run is a signal that these defects
were fixed, not that the test drifted.
"""

import logging
import time

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
# Deliberately short: "the resolved card stays gone" is a settled state by the
# time it is checked, so a long retry window would only make the assertion more
# lenient (`to_have_count(0)` retries until the count reaches 0).
PANEL_STAYS_GONE_TIMEOUT = 5_000

SENSITIVE_TOOLKIT_TYPE = "artifact"
SENSITIVE_TOOL_NAME = "delete_file"

# Backend-execution poll budget (SECONDS — these are `time` values, not
# Playwright timeouts). Once Authorize is granted the tool runs asynchronously
# on the backend, so the deletion becomes observable some time after the card
# closes; the AFS measured the honest flow at ~25 s to the card and budgets up
# to 90 s of execution polling.
EXECUTION_POLL_TIMEOUT_S = 90
EXECUTION_POLL_INTERVAL_S = 3

# The OPEN product defect this module's ELITEA-2212 test is red on.
KNOWN_DEFECT_AUTHORIZE_NO_EXECUTION = "#1834"
# The SAME open issue, aliased under the name the ELITEA-2213 Block path shows it
# by: there the resume does not merely fail to execute the tool, it drops the
# whole turn — no assistant response ever arrives and the decision is never
# committed (AFS § REWORK, 2/2 runs 2026-08-27). One issue, two symptom names;
# an alias rather than a second literal so the two never drift apart, and so the
# constant three merged ELITEA-2212 assertions already reference is untouched.
KNOWN_DEFECT_RESUME_DROPS_TURN = KNOWN_DEFECT_AUTHORIZE_NO_EXECUTION
# Sibling of #1834 (possibly the same root cause): the resolved card comes back.
KNOWN_DEFECT_CARD_REAPPEARS = "#1835"

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


def _poll_bucket_until_file_absent(
    artifact_api: ArtifactAPI,
    bucket_name: str,
    file_key: str,
    timeout_s: int = EXECUTION_POLL_TIMEOUT_S,
    interval_s: int = EXECUTION_POLL_INTERVAL_S,
) -> list[str]:
    """Poll the bucket listing until ``file_key`` is gone, or the deadline passes.

    Returns the LAST observed listing, so the caller asserts on real backend
    ground truth rather than on a boolean this helper decided.

    Why a ``time.sleep`` loop and not a framework wait (AFS § Rework delta row
    1): the oracle here is a REST read of the backend, not anything the browser
    renders — there is no locator to wait on and no request the page will make.
    ``expect.poll(...)`` does NOT exist in Python Playwright (it is the
    JavaScript API; ``hasattr(expect, "poll") is False`` on 1.61.0), so the
    merged version of this assertion could not execute at all. This is a real
    deadline poll over a real backend condition, exits as soon as the condition
    holds, and is NOT a sleep standing in for a UI wait.
    """
    deadline = time.monotonic() + timeout_s
    remaining_files = artifact_api.list_bucket_files(bucket_name)
    while file_key in remaining_files and time.monotonic() < deadline:
        time.sleep(interval_s)
        remaining_files = artifact_api.list_bucket_files(bucket_name)
    return remaining_files


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
        """Card shows correct heading, action-name block, and all three action buttons.

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
            chat.sensitive_action_block_button.click()
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
    # reruns=0 because this spec is SANCTIONED-RED (#1834 + #1835): it is expected
    # to fail, so `pytest.ini`'s global `--reruns=2` could never rescue it — it
    # could only multiply wall clock and put retry noise in the record. Verified
    # by observation 2026-08-27 that the marker overrides the CLI value in this
    # venv (pytest-rerunfailures 16.4): an unmarked test failing on an
    # `--only-rerun` pattern ran 3x/10.06s, the same test marked reruns=0 ran
    # 1x/0.03s.
    @pytest.mark.flaky(reruns=0)
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
        (backend-verified via ArtifactAPI, not just a UI-only signal).

        TRANSIT SUBSTITUTION (declared, AFS § Fidelity Declaration): only the
        precondition is substituted — ``sensitive_delete_file_toolkit`` marks
        ``artifact``/``delete_file`` sensitive over REST
        (``PUT {api}/admin/plugin_config_values/administration/guardrails``)
        because the Admin UI is a separate deployed application localhost does
        not serve (#1140). Every observable asserted below — the card closing,
        the file being gone from the bucket, the chips, the composer, the
        console — is produced end to end by the real LLM → real tool call →
        real backend interrupt → real WebSocket frame. Nothing is mocked,
        injected or intercepted.

        SANCTIONED-RED — # Known defect: #1834, # Known defect: #1835. Three of
        this case's expected results do not hold today, all downstream of the one
        dropped authorize-resume (module docstring enumerates the closed set).
        Each is asserted here as the CORRECT behaviour and each is SOFT, so every
        later step still runs and every member of the set is reported on every
        run, and the spec flips green unchanged when the product is fixed.

        Two soft channels are used, one per observable shape — ``expect.soft``
        wherever a locator exists (model chip, card-stays-gone: a bounded
        framework wait applies and Playwright reports the failure whatever else
        happens), and a ``soft_failures`` entry drained from a ``finally`` by
        ``pytest.fail`` for the backend file listing, which has no locator
        (``expect.poll`` is the JavaScript API and does not exist here).

        Weakening any of these assertions, skipping the test, or reading
        "execution" off the tool chip would all be masking.

        Step numbering continues from ``_reach_sensitive_action_card`` (its
        Steps 1-3 = AFS steps 2-4); Steps 4-10 below are AFS steps 5-11.
        """
        toolkit_name = artifact_toolkit["name"]
        bucket_name = artifact_toolkit["bucket_name"]

        # Soft-failure sink for the #1834 symptom that has no locator to assert
        # on (the backend file listing). Drained once, loudly, at the end of the
        # test — never swallowed (`.agents/testing.md` § Merge gate).
        soft_failures: list[str] = []

        console_issues = collect_console_errors(page)
        page_errors: list[str] = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step(
            "Step 4 — Verify all three action buttons are visible on this "
            "case's own card instance"
        ):
            expect(chat.sensitive_action_authorize_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_with_comment_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 5 — Click Authorize; verify the card closes"):
            chat.sensitive_action_authorize_button.first.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        # `try`/`finally` so the #1834 evidence can NEVER be lost: without it, a
        # hard failure in any later step aborts before the drain and silently
        # discards a recorded soft failure (observed 3/3 on 2026-08-27 — the
        # file-not-deleted finding vanished behind the Step 9 failure). The
        # `finally` raise chains onto whatever else failed, so both surface.
        try:
            with allure.step(
                "Step 6 — Verify the toolkit tool genuinely executed: the seeded "
                "file is gone from the bucket (backend ground truth)"
            ):
                # Known defect: #1834 — the file is still present after the full
                # poll budget: Authorize resumes nothing. Backend listing is the
                # only honest oracle: the card closing and the tool chip both
                # render whether or not the tool ran.
                remaining_files = _poll_bucket_until_file_absent(
                    artifact_api, bucket_name, artifact_seeded_file
                )
                if artifact_seeded_file in remaining_files:
                    soft_failures.append(
                        f"Tool did not execute: '{artifact_seeded_file}' is still in bucket "
                        f"'{bucket_name}' {EXECUTION_POLL_TIMEOUT_S}s after Authorize "
                        f"(listing: {remaining_files})"
                    )

            with allure.step(
                "Step 7 — Verify the LLM-model chip renders (the signal that the "
                "authorized turn actually completed)"
            ):
                # Known defect: #1834 — the chip is absent on SOME runs of the
                # broken authorize flow (1 of 4 on 2026-08-27; it rendered in the
                # other three). It is the subset-firing member of the closed set
                # (`.agents/testing.md` § Merge gate, closed-set variant), which
                # is why it must be soft rather than hard: it is a real symptom,
                # not a stable one. The expectation itself is correct — a
                # guardrails-OFF control run renders the chip every time.
                # `expect.soft` (not the `soft_failures` list) because this one
                # has a locator to wait on: the chip appears when the authorized
                # turn completes, which in a fixed product can land after the
                # deletion is observable, so a bounded framework wait is what
                # makes it flip green reliably rather than racing.
                expect.soft(chat.answer_model_chip.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 8 — Verify the toolkit/tool chip renders '{toolkit_name}: {SENSITIVE_TOOL_NAME}'"
            ):
                # NOT execution evidence, and must never be read as such: the chip
                # is rendered from the PENDING tool-call intent and is already
                # present while the card is still open, before Authorize is clicked
                # (live-verified every run, AFS § What this pass established). It is
                # kept because the case's step 4 asks for it. `.first` guards the
                # strict-mode violation a second tool call would cause.
                expect(chat.answer_tool_chip.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.answer_tool_chip.first).to_contain_text(
                    f"{toolkit_name}: {SENSITIVE_TOOL_NAME}"
                )

            with allure.step(
                "Step 9 — Verify the conversation continues normally (composer "
                "re-enabled, panel stays gone)"
            ):
                assert chat.message_input.is_editable(), (
                    "Message input should be editable again after authorization completes"
                )
                # Known defect: #1835 — the card, correctly closed ~0.1s after
                # the Authorize click (Step 5 asserts that, hard, and it passes),
                # is rendered AGAIN by the time this step runs ~90s later, with
                # live buttons, as if the interrupt were still pending. Asserted
                # as the CORRECT behaviour and soft-routed so Step 10's
                # side-channel check still runs and reports.
                expect.soft(
                    chat.sensitive_action_panel,
                    f"Known defect {KNOWN_DEFECT_CARD_REAPPEARS}: the resolved "
                    "sensitive-action card must stay gone",
                ).to_have_count(0, timeout=PANEL_STAYS_GONE_TIMEOUT)

            with allure.step("Step 10 — Side-channel: no console/JS errors across the whole flow"):
                # Errors only. The backend also emits an unhandled `parallel_hitl_ready`
                # socket message during this flow, which the frontend logs as a
                # console.WARNING (# Known defect: #1831) — a warning is not captured
                # here, and this assertion must not be widened to swallow it.
                assert not console_issues and not page_errors, (
                    f"Unexpected console errors: {console_issues!r}; "
                    f"page errors: {page_errors!r}"
                )

        finally:
            if soft_failures:
                # Sanctioned-RED terminal signal (see the docstring). Raised from
                # `finally` so it reports even when a later step failed hard —
                # Python chains the two, so neither finding is lost.
                pytest.fail(
                    f"# Known defect: {KNOWN_DEFECT_AUTHORIZE_NO_EXECUTION} — Authorize closed "
                    "the sensitive-action card but the toolkit tool never executed:\n  - "
                    + "\n  - ".join(soft_failures)
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
    # reruns=0 for exactly the reason ELITEA-2212 above carries it: this spec is
    # SANCTIONED-RED (#1834 + #1835), so `pytest.ini`'s global `--reruns=2` could
    # never rescue it — it could only triple a ~3-minute run and put retry noise
    # in the record.
    @pytest.mark.flaky(reruns=0)
    def test_block_prevents_toolkit_tool_from_executing(
        self,
        page,
        conversation_id: str,
        artifact_toolkit: dict,
        artifact_seeded_file: str,
        artifact_api: ArtifactAPI,
        sensitive_delete_file_toolkit,
    ):
        """Block closes the card and the delete_file call never runs — proven on
        the backend listing, not on any UI-only signal.

        TRANSIT SUBSTITUTION (declared, AFS § Fidelity Declaration): only the
        precondition is substituted — ``sensitive_delete_file_toolkit`` marks
        ``artifact``/``delete_file`` sensitive over REST
        (``PUT {api}/admin/plugin_config_values/administration/guardrails``)
        because the Admin UI is a separate deployed application localhost does
        not serve (#1140). Every observable asserted below — the card, its
        closing, the bucket listing, the chips, the response, the console — is
        produced end to end by the real LLM → real tool call → real backend
        interrupt → real WebSocket frame. Nothing is mocked, injected or
        intercepted.

        **HONESTY CAVEAT — read before trusting a green Step 6.** *The file is
        still there* is NOT proof that Block worked. A turn that silently DIED
        before the tool ran leaves byte-identical evidence. Step 6 is the case's
        own primary observable and must be asserted, but the step that actually
        distinguishes "blocked" from "died" is the response step (Step 7) — and
        that one is red today. Step 10 re-reads the bucket after the response
        window so the "did not execute" claim is time-bounded rather than
        instantaneous.

        SANCTIONED-RED — # Known defect: #1834, # Known defect: #1835. Two of
        this case's observables do not hold today, both downstream of the one
        dropped block-resume (module docstring enumerates the closed set and the
        exact 2-sub-exception signature). Each is asserted here as the CORRECT
        behaviour and each is SOFT, so every later step still runs, every member
        of the set is reported on every run, and the spec flips green unchanged
        when the product is fixed.

        Two soft channels are used, one per observable shape, matching
        ``TestSensitiveActionAuthorize`` — ``expect.soft`` where a locator exists
        (the card staying gone: a bounded framework wait applies and Playwright
        reports the failure whatever else happens), and a ``soft_failures`` entry
        drained from a ``finally`` by ``pytest.fail`` for the missing assistant
        response, whose failure mode is a raised ``TimeoutError`` rather than a
        locator state.

        CORRECTNESS FIX (not a weakening — the removed assertion was factually
        wrong): this test used to end on
        ``expect(chat.answer_tool_chip).to_have_count(0)``, "no tool-EXECUTION
        chip for the blocked tool". Live re-analysis proved the product never
        enters that state: ``ActionView.jsx:407`` renders the chip from the tool
        **call attempt** with no execution predicate, so its count is 1 while the
        card is still pending, 1 after Block, and only drops to 0 on a page
        reload (chip is a live-stream render, not persisted). The case asks for a
        distinction between a "call" chip and an "execution" chip that this
        product does not make — case-text drift, filed as clarification #1839,
        NOT a product defect. It is replaced by the STRONGER positive assertion
        (Step 9: the chip is present and names the blocked tool), and
        non-execution is proven where it actually can be, on the backend
        (Steps 6 + 10). Canon ruling #277 shape (b) is unaffected: both branches
        of the ternary are positively referenced on ELITEA-2212's executed path
        (module docstring).

        DECLARED IMPROVISATION — assertion ORDER differs from AFS § Corrected
        assertion set for one row, on determinism grounds; the assertion itself,
        its soft channel and its defect link are exactly as specified. The AFS
        orders row D ("the resolved card stays gone") immediately after row C,
        i.e. ~1 s after the click — but the card reappears at ~2-6 s, and
        ``to_have_count(0)`` is satisfied the instant the count is already 0, so
        evaluated there it would race and usually pass, asserting nothing. It is
        therefore evaluated as Step 8, after the response window, where the
        reappearance is a settled state that persists until reload — the same
        placement ``TestSensitiveActionAuthorize`` Step 9 already uses, and the
        only one under which this member of the closed set fires deterministically.

        Step numbering continues from ``_reach_sensitive_action_card`` (its
        Steps 1-3); Steps 4-11 below are AFS § Corrected assertion set rows
        A, B, C, E, D, F, G, H in that evaluation order.
        """
        toolkit_name = artifact_toolkit["name"]
        bucket_name = artifact_toolkit["bucket_name"]

        # Soft-failure sink for the #1834 symptom that has no locator to assert
        # on (an assistant response that never arrives at all). Drained once,
        # loudly, at the end — never swallowed (`.agents/testing.md` § Merge gate).
        soft_failures: list[str] = []

        console_issues = collect_console_errors(page)
        page_errors: list[str] = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        chat = _reach_sensitive_action_card(
            page, conversation_id, artifact_toolkit, artifact_seeded_file
        )

        with allure.step(
            "Step 4 — Verify all three action buttons are visible on THIS "
            "case's own card instance"
        ):
            expect(chat.sensitive_action_authorize_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.sensitive_action_block_with_comment_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 5 — Click Block; verify the card closes"):
            chat.sensitive_action_block_button.first.click()
            expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

        # `try`/`finally` so the #1834 evidence can NEVER be lost: without it a
        # hard failure in any later step aborts before the drain and silently
        # discards a recorded soft failure. The `finally` raise chains onto
        # whatever else failed, so both surface.
        try:
            with allure.step(
                "Step 6 — PRIMARY OBSERVABLE: the toolkit tool did NOT execute — "
                "the seeded file is still in the bucket (backend ground truth, "
                "read BEFORE the response wait so this check is reached even "
                "while # Known defect: #1834 keeps that wait from ever settling)"
            ):
                remaining_files = artifact_api.list_bucket_files(bucket_name)
                assert artifact_seeded_file in remaining_files, (
                    f"File '{artifact_seeded_file}' should still be present after Block, "
                    f"found: {remaining_files}"
                )

            with allure.step(
                "Step 7 — Verify the LLM response acknowledges the block (loose "
                "signal — non-empty and does not claim success; the exact "
                "wording is LLM-nondeterministic, AFS § Test Steps)"
            ):
                # Known defect: #1834 — no assistant response EVER arrives on the
                # Block path: the answer body stays empty (observed 230 s and 90 s
                # in the two live runs), so this wait raises rather than settling.
                # The expectation is correct — a resolved HITL turn must produce a
                # reply — so it is asserted, soft-routed, and flips green unchanged
                # when the resume stops dropping the turn. This is also the ONLY
                # step that separates "blocked" from "silently died": Step 6 reads
                # identically in both worlds (see the docstring's honesty caveat).
                try:
                    chat.wait_for_message_content_stable(
                        stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT
                    )
                except TimeoutError as exc:
                    soft_failures.append(
                        "No assistant response arrived after Block within "
                        f"{CHAT_RESPONSE_TIMEOUT}ms — the turn was dropped instead of "
                        f"being resumed as blocked ({exc})"
                    )
                else:
                    last_text = chat.get_last_message_text()
                    if not last_text.strip():
                        soft_failures.append(
                            "Assistant response after Block is empty — expected a reply "
                            "acknowledging that the action was blocked"
                        )
                    elif any(phrase in last_text.lower() for phrase in _SUCCESS_CLAIM_PHRASES):
                        soft_failures.append(
                            "Assistant response after Block claims the delete succeeded: "
                            f"{last_text!r}"
                        )

            with allure.step(
                "Step 8 — Verify the resolved card stays gone (evaluated here, "
                "after the response window, where the state is settled — see "
                "the docstring's DECLARED IMPROVISATION)"
            ):
                # Known defect: #1835 — the card, correctly closed within a few
                # hundred ms of the Block click (Step 5 asserts that, hard, and it
                # passes), is rendered AGAIN ~2-6 s later with live, enabled
                # buttons and persists until a page reload — so a user can issue a
                # SECOND decision, including Authorize, on an action they already
                # blocked. Asserted as the CORRECT behaviour and soft-routed so
                # Steps 9-11 still run and report.
                expect.soft(
                    chat.sensitive_action_panel,
                    f"Known defect {KNOWN_DEFECT_CARD_REAPPEARS}: the resolved "
                    "sensitive-action card must stay gone",
                ).to_have_count(0, timeout=PANEL_STAYS_GONE_TIMEOUT)

            with allure.step(
                f"Step 9 — Verify the tool-call chip renders '{toolkit_name}: "
                f"{SENSITIVE_TOOL_NAME}', naming the tool that was blocked"
            ):
                # This chip is the tool-CALL-ATTEMPT chip and carries NO execution
                # meaning: `ActionView.jsx:407` renders it from the call intent with
                # no execution predicate, so it is already present while the card is
                # still pending, before Block is clicked (live-verified 2/2 runs).
                # It is asserted PRESENT — never absent — precisely because the
                # product has no execution chip to be absent (clarification #1839);
                # reading execution off it in either direction would be a lie.
                # `.first` guards the strict-mode violation a second tool call would
                # cause.
                expect(chat.answer_tool_chip.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.answer_tool_chip.first).to_contain_text(
                    f"{toolkit_name}: {SENSITIVE_TOOL_NAME}"
                )

            with allure.step(
                "Step 10 — Late-execution guard: the file is STILL present after "
                "the response window, so 'did not execute' is time-bounded rather "
                "than instantaneous"
            ):
                remaining_files_late = artifact_api.list_bucket_files(bucket_name)
                assert artifact_seeded_file in remaining_files_late, (
                    f"File '{artifact_seeded_file}' was deleted LATE — the blocked "
                    f"delete_file executed after all, found: {remaining_files_late}"
                )

            with allure.step("Step 11 — Side-channel: no console/JS errors across the whole flow"):
                # Errors only. The backend also emits an unhandled `parallel_hitl_ready`
                # socket message during this flow, which the frontend logs as a
                # console.WARNING (# Known defect: #1831) — a warning is not captured
                # here, and this assertion must not be widened to swallow it. Its
                # cleanness is itself the finding that makes "the turn dies SILENTLY"
                # a verified statement rather than an impression.
                assert not console_issues and not page_errors, (
                    f"Unexpected console errors: {console_issues!r}; "
                    f"page errors: {page_errors!r}"
                )

        finally:
            if soft_failures:
                # Sanctioned-RED terminal signal (see the docstring). Raised from
                # `finally` so it reports even when a later step failed hard —
                # Python chains the two, so neither finding is lost.
                pytest.fail(
                    f"# Known defect: {KNOWN_DEFECT_RESUME_DROPS_TURN} — Block closed the "
                    "sensitive-action card but the resume dropped the turn:\n  - "
                    + "\n  - ".join(soft_failures)
                )


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
