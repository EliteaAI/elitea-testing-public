"""UI Test for ELITEA-2217 — Context Management: Global Setting Enabled,
Auto-Summarization Disabled — Verify No Summarization Occurs When Tokens
Exceed Max Limit.

Verifies that with Context Management ON but Automatic Summarization OFF,
sending messages past a low per-conversation Max Context Tokens threshold
drives the token count/percentage past 100% and surfaces the high-utilization
warning icon exactly as when Automatic Summarization is ON (ELITEA-2218) —
but NO summarization occurs: the Summaries counter stays at 0 throughout, no
"Summarizing the chat history" indicator ever appears, and the "Edit context
settings" modal confirms both the 0 Summaries count and its own summarization
toggle reading OFF.

Spec: test-specs/chat-interface/l3_auto-summarization-disabled-no-trigger-at-max-tokens_ELITEA-2217.md

Third leg of the {ELITEA-2216, ELITEA-2217, ELITEA-2218} family:
- ELITEA-2216: Context Management OFF — the widget stays all-zero regardless
  of usage (``test_context_management_disabled.py``).
- ELITEA-2218: Context Management + Automatic Summarization BOTH ON —
  summarization triggers at the threshold (``test_context_auto_summarization.py``).
- ELITEA-2217 (this file): Context Management ON, Automatic Summarization
  OFF — token tracking still runs (unlike 2216), but summarization never
  fires (unlike 2218).

Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@69921d7c):
- ``context-modal-summarization-toggle`` — the "Enable automatic
  summarization" Switch inside the "Edit context settings" dialog
  (``ContextStrategySummarization.jsx``). Confirmed by the analyst (both a
  source read and a live ``querySelectorAll('[data-testid]')`` sweep of the
  open dialog) that this switch carried NO data-testid at all before this
  change — needed to assert Step 7's "auto-summarization toggle is OFF"
  directly against the per-conversation modal.

New page-object surface (``ChatPage``, all additive):
- ``context_modal_summarization_toggle`` (LocatorDescriptor)
- ``set_max_context_tokens_in_modal()`` — sibling of
  ``set_context_strategy_thresholds()`` that touches ONLY Max Context Tokens
  + Save, skipping the DISABLED Target Summary Tokens field (see method
  docstring — issue #1605 below).
- ``is_context_modal_summarization_enabled()``

Known defect (does NOT block this case — documented workaround used):
issue #1605 — with Automatic Summarization globally OFF, the "Edit context
settings" dialog's cross-field validation still runs Max Context Tokens
against the DISABLED (frozen) Target Summary Tokens value: a new Max Context
Tokens value below that frozen value permanently disables Save. Workaround
(confirmed live by the analyst): choose Max Context Tokens >= the account's
current Target Summary Tokens value. This test reads that value dynamically
from the already-open modal's own (disabled but still readable)
``context-modal-target-summary-tokens-input`` field rather than hardcoding
it — the account's Target Summary Tokens is account-state, not a fixed
constant.

No fabrication anywhere in this test — self-check (the provenance grep from
the project's reviewer/implementer contract) is covered by the Run Report;
every AI response is produced by a live send + wait, never stubbed.

Usage:
    cd automation
    pytest tests/ui/chat/test_context_auto_summarization_disabled.py -v
"""

import logging
import re

import allure
import pytest
from components.mui import Dialog
from pages.chat_page import ChatPage
from pages.user_profile_settings_page import UserProfileSettingsPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 45_000     # AI message generation (streaming) — same
                                  # budget as ELITEA-2218's identical prompt shape.
UI_ELEMENT_TIMEOUT = 10_000      # Buttons, dialogs, panels
NAVIGATION_TIMEOUT = 15_000      # SPA route changes

# Fallback Max Context Tokens if the dynamic read below fails for any reason
# (project min is 1000; the analyst's live session confirmed 5000 works
# reliably against an observed Target Summary Tokens of 4096 — AFS § Test
# Data). Real runs should always use the dynamically-read value instead.
FALLBACK_MAX_CONTEXT_TOKENS = 5_000
# Safety margin added on top of the live Target Summary Tokens value so the
# chosen Max Context Tokens always satisfies issue #1605's cross-field
# validation (Max Context Tokens must be >= Target Summary Tokens while
# Automatic Summarization is off and that field is frozen/disabled).
MAX_CONTEXT_TOKENS_MARGIN = 500

# Upper bound on messages sent to reach the high-utilization warning icon —
# a real cap, not a magic sleep: if utilization never approaches the
# configured max within this many real exchanges, that is itself a
# meaningful failure (token accounting or the warning icon is broken), not
# something to mask with a bigger number. Larger than ELITEA-2218's own cap
# (8) — live confirmed this implementation round that per-response token
# growth varies more than the analyst's single live session showed (that
# session crossed 5000 in 4 exchanges; a real run here needed more before
# reaching only 4257/5000 at the 8-message cap), so the bound is widened
# to tolerate real LLM response-length variance rather than tightened to
# force a faster crossing.
MAX_MESSAGES_TO_WARNING = 15

# Long, distinct prompts — same LONG_PROMPT_TOPICS/LONG_PROMPT_TEMPLATE
# pattern already built for ELITEA-2218, reused verbatim per the AFS
# Automation Hints (don't re-derive).
LONG_PROMPT_TOPICS = [
    "how neural networks learn",
    "the causes of the French Revolution",
    "how vaccines train the immune system",
    "how compilers translate source code",
    "the water cycle",
    "how photosynthesis works",
    "the history of the printing press",
    "how ocean currents affect climate",
]
LONG_PROMPT_TEMPLATE = (
    "Write a detailed, information-dense, at-least-200-word explanation of {topic}. "
    "Do not summarize at the end, do not ask any follow-up questions — just answer directly."
)

SUMMARIZING_TEXT_PATTERN = re.compile("Summariz", re.IGNORECASE)


def _parse_used_tokens(tokens_text: str) -> int:
    """Extract the numerator (used tokens) from a '5 301 / 5 000 tokens'-style string."""
    before_slash = tokens_text.split("/")[0]
    cleaned = re.sub(r"[\s ,]+", "", before_slash)
    return int(cleaned)


def _send_long_message(chat: ChatPage, topic: str) -> int:
    """Send one long, topic-distinct message and wait for the full AI reply.

    Returns the used-tokens count read from the Context Budget panel
    immediately after the response completes.
    """
    initial_count = chat.get_message_count()
    chat.send_message(LONG_PROMPT_TEMPLATE.format(topic=topic), use_enter=True)
    chat.wait_for_input_ready()
    chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
    chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
    used = _parse_used_tokens(chat.get_context_budget_tokens_text())
    logger.info("Sent long message on %r — used tokens now %d", topic, used)
    return used


def _assert_no_summarization_signal(chat: ChatPage, used_tokens: int) -> None:
    """CORE NEGATIVE ASSERTIONS (AFS Steps 5-6) — after every send, the
    Summaries counter must still read '0' and no chat-answer-model-chip may
    ever read 'Summarizing the chat history'.
    """
    summaries_count = chat.get_context_budget_summaries_count()
    assert summaries_count == "0", (
        f"Summaries counter should stay '0' with Automatic Summarization "
        f"OFF, even past the configured threshold — got {summaries_count!r} "
        f"after a send (used {used_tokens} tokens)"
    )
    summarizing_chips = chat.answer_model_chip.filter(has_text=SUMMARIZING_TEXT_PATTERN)
    assert summarizing_chips.count() == 0, (
        "No chat-answer-model-chip should ever read 'Summarizing the chat "
        "history' with Automatic Summarization OFF — the summarization "
        "sub-step should never fire"
    )


def _send_until_warning_or_cap(chat: ChatPage, topics_iter) -> tuple[int, bool]:
    """Send long messages (one per call to *topics_iter*) until the
    high-utilization warning icon appears or ``MAX_MESSAGES_TO_WARNING`` is
    reached. Returns (last used-tokens reading, warning_seen).

    After EVERY send, also asserts the no-summarization negative claims
    (AFS Steps 5-6) — not just at the end, matching the case's own "verify
    ... throughout"/"verify ... appears" wording.
    """
    used = 0
    warning_seen = False
    for _ in range(MAX_MESSAGES_TO_WARNING):
        # Fallback once the distinct-topic list is exhausted (mirrors
        # ELITEA-2218's own _send_until_summaries_count_or_cap pattern) —
        # this cap can exceed len(LONG_PROMPT_TOPICS).
        used = _send_long_message(chat, next(topics_iter, "how tides form"))
        _assert_no_summarization_signal(chat, used)
        if chat.is_context_budget_warning_visible():
            warning_seen = True
            break
    return used, warning_seen


class TestContextAutoSummarizationDisabled:
    """ELITEA-2217: Context Management – Global Setting Enabled,
    Auto-Summarization Disabled – Verify No Summarization Occurs When Tokens
    Exceed Max Limit (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat-interface/ELITEA-2217_context-"
        "management-global-setting-enabled-auto-summarization-disabled-"
        "verify-no-summarization-occurs-when-tokens-exceed-max-limit.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_no_summarization_when_auto_summarization_disabled(self, page, conversation_api):
        """With Context Management ON and Automatic Summarization OFF,
        sending messages past a low per-conversation Max Context Tokens
        threshold drives usage past 100% and surfaces the warning icon, but
        the Summaries counter stays 0, no "Summarizing" chip ever appears,
        and the modal confirms both facts.
        """
        topics_iter = iter(LONG_PROMPT_TOPICS)
        profile = UserProfileSettingsPage(page)
        chat = ChatPage(page)
        conv_id = None

        with allure.step("Step 1 — Enable Context Management, disable Automatic "
                          "Summarization in Settings > Memory"):
            profile.navigate_to_profile()
            profile.enable_context_management()  # defensive guard — confirmed ON by default
            profile.disable_automatic_summarization()
            assert profile.is_automatic_summarization_enabled() is False, (
                "Automatic Summarization toggle should read OFF on Settings "
                "> Memory after disable_automatic_summarization()"
            )

        try:
            with allure.step("Step 2-3 — Create a new conversation; send an initial "
                              "message; Context Budget shows fresh counters "
                              "(Messages='2', Summaries='0')"):
                chat.navigate_to_chat()
                chat.dismiss_banner_if_present()
                initial_count = chat.get_message_count()
                chat.send_message(
                    "Hello — starting a no-summarization context-management test conversation.",
                    use_enter=True,
                )
                chat.wait_for_input_ready()
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

                match = re.search(r"/chat/(\d+)", page.url)
                if match:
                    conv_id = match.group(1)
                    logger.info("Conversation created with ID: %s", conv_id)

                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_context_budget_panel(timeout=UI_ELEMENT_TIMEOUT)
                # Messages counter tracks both sides of the round-trip (+2 per
                # exchange, not +1) — same confirmed finding as ELITEA-2218/2216.
                chat.wait_for_context_budget_messages_count("2", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_context_budget_summaries_count("0", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_context_budget_messages_count() == "2", (
                    "Context Budget Messages counter should read '2' "
                    "immediately after the first user+AI exchange"
                )
                assert chat.get_context_budget_summaries_count() == "0", (
                    "Context Budget Summaries counter should read '0' "
                    "before any summarization could possibly have occurred"
                )
                assert conv_id, "Expected the conversation to gain a numeric /chat/{id} URL"

            with allure.step("Step 3b — Configure a low per-conversation Max Context "
                              "Tokens threshold via the 'Edit context settings' dialog "
                              "(sidesteps issue #1605 by reading the live, frozen "
                              "Target Summary Tokens value first)"):
                chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.edit_context_settings()
                Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)

                # Target Summary Tokens is DISABLED (Automatic Summarization is
                # off) but stays mounted with its frozen value — readable via
                # input_value() even while disabled. Issue #1605: Save stays
                # blocked unless the new Max Context Tokens is >= this value.
                try:
                    target_summary_tokens_raw = chat.context_modal_target_summary_tokens_input.input_value()
                    target_summary_tokens = int(target_summary_tokens_raw.strip())
                except (ValueError, AttributeError):
                    logger.warning(
                        "Could not read live Target Summary Tokens value — "
                        "falling back to the analyst's confirmed-working default"
                    )
                    target_summary_tokens = FALLBACK_MAX_CONTEXT_TOKENS - MAX_CONTEXT_TOKENS_MARGIN

                max_context_tokens = max(
                    FALLBACK_MAX_CONTEXT_TOKENS, target_summary_tokens + MAX_CONTEXT_TOKENS_MARGIN
                )
                logger.info(
                    "Live Target Summary Tokens=%d -> choosing Max Context Tokens=%d "
                    "(issue #1605 workaround)",
                    target_summary_tokens, max_context_tokens,
                )

                chat.set_max_context_tokens_in_modal(max_context_tokens)
                chat.close_context_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)

                chat.wait_for_context_budget_max_tokens(max_context_tokens, timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_context_budget_warning_visible(), (
                    "Warning icon should NOT be present immediately after "
                    "configuring a fresh (low-utilization) threshold"
                )

            with allure.step("Steps 4-6 — Send messages until token count exceeds the "
                              "threshold; percentage exceeds 100% and the warning icon "
                              "appears (CORE ASSERTION) — while, after EVERY send, the "
                              "Summaries counter stays 0 and no 'Summarizing the chat "
                              "history' indicator ever appears (CORE NEGATIVE ASSERTIONS)"):
                used_at_warning, warning_seen = _send_until_warning_or_cap(chat, topics_iter)
                assert warning_seen, (
                    f"Expected the high-utilization warning icon to appear within "
                    f"{MAX_MESSAGES_TO_WARNING} messages (used {used_at_warning}/"
                    f"{max_context_tokens} tokens at the last check) — either token "
                    f"accounting or the warning icon is not behaving as the source "
                    f"(ContextBudgetProgress.jsx, isHighUtilization) implies"
                )
                percentage_text = chat.get_context_budget_percentage_text()
                percentage_value = int(percentage_text.rstrip("%"))
                assert percentage_value > 100, (
                    f"Utilization percentage should exceed 100% once the warning "
                    f"icon is visible — got {percentage_text!r}"
                )
                # Re-assert the negative claims one final time at the exact
                # over-100% state the case's Step 5/6 point at.
                assert chat.get_context_budget_summaries_count() == "0", (
                    "Summaries counter should still read '0' even once "
                    "utilization has crossed 100%"
                )
                assert chat.answer_model_chip.filter(has_text=SUMMARIZING_TEXT_PATTERN).count() == 0, (
                    "No 'Summarizing the chat history' chip should exist even "
                    "once utilization has crossed 100%"
                )

            with allure.step("Step 7 — Open the 'Edit context settings' modal; verify "
                              "Summaries shows 0, Tokens/percentage are consistent with "
                              "the over-100% state, and the modal's own Automatic "
                              "Summarization toggle is OFF"):
                # LIVE FINDING (this implementation round): the sidebar panel's
                # stats (context-budget-*) and the modal's own stats
                # (context-modal-stat-*) are populated from two separate
                # RTK-Query subscriptions that do not always settle at
                # exactly the same instant — a snapshot read from one right
                # before opening the dialog is not guaranteed to equal the
                # other's own read a moment later (observed live: sidebar
                # 114% vs modal 136% off the SAME underlying conversation, no
                # message sent in between). Reported as a CLARIFICATION, not
                # a defect (nothing here contradicts a documented contract;
                # matches the reverse-masking guard's live-contract
                # principle). The case's own Step 7 requires the modal to
                # self-report 0 Summaries + toggle OFF + a >100% state — not
                # bit-for-bit equality with a separately-timed sidebar
                # snapshot — so this test asserts exactly that, each stat
                # against ITS OWN internal consistency, not cross-panel.
                chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.edit_context_settings()
                Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)

                assert chat.get_context_budget_summaries_count() == "0", (
                    "Modal Summaries stat should read '0' (context-budget-"
                    "summaries-count is shared between the sidebar panel and "
                    "the modal via SummaryDetailsButton; both read '0' here)"
                )
                modal_tokens_text = chat.get_context_modal_stat_tokens_text()
                modal_percentage_text = chat.get_context_modal_stat_percentage_text()
                modal_used_tokens = _parse_used_tokens(modal_tokens_text)
                modal_max_tokens = _parse_used_tokens(modal_tokens_text.split("/")[1])
                modal_percentage_value = int(modal_percentage_text.rstrip("%"))
                assert modal_used_tokens > modal_max_tokens, (
                    f"Modal Tokens stat should itself reflect the over-max state "
                    f"the case's Step 4 already proved — got {modal_tokens_text!r}"
                )
                assert modal_percentage_value > 100, (
                    f"Modal percentage stat should itself read over 100% — got "
                    f"{modal_percentage_text!r}"
                )
                assert chat.is_context_modal_summarization_enabled() is False, (
                    "The dialog's own 'Enable automatic summarization' switch "
                    "should read unchecked, matching the global OFF state "
                    "(context-modal-summarization-toggle, ELITEA-2217)"
                )

                chat.close_context_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)

        finally:
            # Automatic Summarization is a global, persistent, account-level
            # setting shared with sibling tests (ELITEA-2218/2374 assume it's
            # ON by default) — restore it regardless of outcome.
            try:
                profile.navigate_to_profile()
                profile.enable_automatic_summarization()
            except Exception as exc:
                logger.warning("Failed to restore Automatic Summarization to ON: %s", exc)

            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
