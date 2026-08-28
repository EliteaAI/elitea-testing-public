"""UI test — Context Management settings apply to NEW conversations only (ELITEA-2390).

A conversation snapshots the user's Settings -> Memory context-management
defaults **at creation time**. Changing those defaults afterwards must affect
only conversations created after the change; an existing conversation keeps
the values it was born with.

AFS: test-specs/settings-user-profile/
l1_context-settings-apply-to-new-conversations-only_ELITEA-2390.md

Shape of the run (the AFS explains why the first two steps exist):
    baseline A (32000 / 10) -> create conversation #1 -> read ITS modal
    -> case values (32000 / 3) -> create conversation #2 -> read ITS modal
    -> reopen conversation #1 -> its Preserve Recent Messages must STILL be 10

The case says "open a previously existing conversation", but the account has
none (verified live: the conversation list renders folders only), and
"unchanged" is unfalsifiable without a recorded before-value — so the spec
creates its own baseline conversation under a deliberately DIFFERENT Preserve
Recent Messages (10 vs the case's 3). That difference is what makes the final
assertion a real discriminator rather than a coincidence.

Known case-text vs live-product divergence (not weakened — the live contract
is asserted; EliteaAI/elitea-testing-public#1238): the case says
"Settings -> Personalization -> DEFAULT CONTEXT MANAGEMENT";
`/settings/personalization` 404s and the live route is Settings -> Memory.

No substitution of the system under test: every asserted value is read from
the product's own UI (the per-conversation "Edit context settings" modal),
after the product itself produced it. The modal is opened read-only — its
Save button is never clicked, because saving would rewrite the very value the
final step observes.

Deliberately does NOT wait for an AI answer: the conversation and its context
snapshot exist as soon as the message is SENT (confirmed live — the
`/chat/<id>` route and a 200 `context_analytics` carrying the inherited
`max_tokens` both land before any answer). That keeps the documented
LLM trigger-side flakiness out of this case entirely.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - chat: drives the chat surface for the per-conversation half
    - p1: high priority (case priority `high` -> l1 -> p1)
    - regression
"""

import logging
import re

import allure
import pytest
from components.mui import Dialog
from pages.chat_page import ChatPage
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import Response, expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.chat,
    pytest.mark.p1,
    pytest.mark.regression,
]

# ---------------------------------------------------------------------------
# Timeout / autosave constants
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000     # Fields, toggles, section container
NAVIGATION_TIMEOUT = 30_000     # SPA route changes / conversation creation
AUTOSAVE_TIMEOUT = 15_000       # Autosave PUT round-trip (per-keystroke typing)
CONTEXT_PANEL_TIMEOUT = 30_000  # Context Budget panel (waits on context_analytics)
AUTOSAVE_PUT_PATH = "/api/v2/social/author/"

# AFS § Test Data — the two phases. The Preserve Recent Messages values MUST
# differ: `10` is what conversation #1 is born with, `3` is the case's value
# applied afterwards.
MAX_CONTEXT_TOKENS = 32000
BASELINE_PRESERVE_RECENT = 10
CASE_PRESERVE_RECENT = 3

SEED_MESSAGE = "Reply with the single word OK."


def _is_autosave_put_response(response: Response) -> bool:
    """True for the Settings -> Memory autosave PUT."""
    return response.request.method == "PUT" and AUTOSAVE_PUT_PATH in response.url


class TestContextSettingsApplyToNewConversationsOnly:
    """Settings changes reach new conversations; existing ones keep their own."""

    # ------------------------------------------------------------------
    # Suite-local helpers (single caller each — kept beside the test per the
    # project's suite-local-helper convention, not promoted to a page object)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_settings(page, profile: UserProfileSettingsPage, preserve_recent: int) -> None:
        """Set Max Context Tokens + Preserve Recent Messages and assert each autosave.

        Blur is the page's save trigger (no Save button exists here), so the
        PUT status is asserted rather than merely awaited.
        """
        with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
            profile.type_max_context_tokens_raw(str(MAX_CONTEXT_TOKENS))
        assert put_info.value.status == 200, (
            f"Setting Max Context Tokens to {MAX_CONTEXT_TOKENS} should autosave via "
            f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
        )

        with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
            profile.set_preserve_recent_messages(preserve_recent)
        assert put_info.value.status == 200, (
            f"Setting Preserve Recent Messages to {preserve_recent} should autosave via "
            f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
        )

    @staticmethod
    def _create_conversation(page, chat: ChatPage) -> str:
        """Send the seed message on a fresh /chat and return the new conversation id.

        The conversation is created by SENDING — no AI answer is awaited (see
        the module docstring).
        """
        chat.navigate_to_chat()
        chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        chat.send_message(SEED_MESSAGE, use_enter=True)
        page.wait_for_url(
            lambda url: re.search(r"/chat/\d+", url) is not None,
            timeout=NAVIGATION_TIMEOUT,
        )
        match = re.search(r"/chat/(\d+)", page.url)
        assert match, f"Sending a message should create a conversation; URL was {page.url!r}"
        conversation_id = match.group(1)
        logger.info("Created conversation %s", conversation_id)
        return conversation_id

    @staticmethod
    def _read_conversation_context_settings(page, chat: ChatPage) -> dict:
        """Open the conversation's 'Edit context settings' modal and read it.

        The Context Budget panel is UNMOUNTED while the participants panel is
        collapsed (it starts collapsed on every conversation load), so the
        panel is expanded first — otherwise a missing panel is
        indistinguishable from a product failure. Closes the dialog with
        Escape; the Save button is never clicked (read-only by design).
        """
        chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
        chat.context_budget_panel.wait_for(state="visible", timeout=CONTEXT_PANEL_TIMEOUT)

        chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        chat.edit_context_settings()
        Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)

        settings = {
            "management_enabled": chat.is_context_modal_management_enabled(),
            "max_tokens": chat.context_modal_max_tokens_input.input_value(),
            "preserve_recent": chat.context_modal_preserve_recent_input.input_value(),
        }
        logger.info("Conversation context settings read from modal: %s", settings)

        chat.close_context_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
        return settings

    # ------------------------------------------------------------------
    # The case
    # ------------------------------------------------------------------

    def test_context_settings_apply_to_new_conversations_only(self, page, conversation_api):
        """A settings change reaches new conversations only; existing ones keep theirs."""
        profile = UserProfileSettingsPage(page)
        chat = ChatPage(page)
        baseline_conversation_id = None
        new_conversation_id = None

        with allure.step(
            "Setup — Navigate to Settings -> Memory, ensure Context Management "
            "is ON, and record the account's current values for teardown"
        ):
            profile.navigate_to_profile()
            expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            if not profile.is_context_management_enabled():
                with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                assert put_info.value.status == 200, (
                    f"Turning Context Management ON should autosave via PUT "
                    f"{AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )
            original_max_tokens = profile.get_max_context_tokens()
            original_preserve_recent = profile.get_preserve_recent_messages()
            logger.info(
                "Account originals: max_context_tokens=%d, preserve_recent_messages=%d",
                original_max_tokens,
                original_preserve_recent,
            )

        try:
            with allure.step(
                f"Setup — Baseline A: set Max Context Tokens {MAX_CONTEXT_TOKENS} "
                f"and Preserve Recent Messages {BASELINE_PRESERVE_RECENT} (the "
                f"values the 'previously existing' conversation will be born with)"
            ):
                self._apply_settings(page, profile, BASELINE_PRESERVE_RECENT)

            with allure.step(
                "Setup — Create the 'previously existing' conversation and read "
                "its context settings (the before-value step 7 compares against)"
            ):
                baseline_conversation_id = self._create_conversation(page, chat)
                baseline_settings = self._read_conversation_context_settings(page, chat)
                assert baseline_settings["management_enabled"], (
                    "The baseline conversation should have context management active"
                )
                assert baseline_settings["max_tokens"] == str(MAX_CONTEXT_TOKENS), (
                    f"The baseline conversation should inherit Max Context Tokens "
                    f"{MAX_CONTEXT_TOKENS}, got {baseline_settings['max_tokens']!r}"
                )
                assert baseline_settings["preserve_recent"] == str(BASELINE_PRESERVE_RECENT), (
                    f"The baseline conversation should inherit Preserve Recent Messages "
                    f"{BASELINE_PRESERVE_RECENT}, got {baseline_settings['preserve_recent']!r}"
                )

            with allure.step(
                f"Step 1-2 — Back on Settings -> Memory: context management "
                f"enabled, Max Context Tokens {MAX_CONTEXT_TOKENS}, Preserve "
                f"Recent Messages {CASE_PRESERVE_RECENT}"
            ):
                profile.navigate_to_profile()
                expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert profile.is_context_management_enabled(), (
                    "Context Management should still read ON before applying the case values"
                )
                self._apply_settings(page, profile, CASE_PRESERVE_RECENT)

            with allure.step(
                "Step 3 — Navigate away and back; the values were auto-saved"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                profile.navigate_to_profile()
                expect(profile.max_context_tokens_input).to_have_value(
                    str(MAX_CONTEXT_TOKENS), timeout=UI_ELEMENT_TIMEOUT
                )
                expect(profile.preserve_recent_messages_input).to_have_value(
                    str(CASE_PRESERVE_RECENT), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 4 — Create a new conversation"):
                new_conversation_id = self._create_conversation(page, chat)
                assert new_conversation_id != baseline_conversation_id, (
                    f"Step 4 should create a NEW conversation, but landed back on "
                    f"{baseline_conversation_id}"
                )

            with allure.step(
                f"Step 5 — The new conversation has context management active "
                f"with the configured values ({MAX_CONTEXT_TOKENS} / "
                f"{CASE_PRESERVE_RECENT})"
            ):
                new_settings = self._read_conversation_context_settings(page, chat)
                assert new_settings["management_enabled"], (
                    "The new conversation should have context management active"
                )
                assert new_settings["max_tokens"] == str(MAX_CONTEXT_TOKENS), (
                    f"The new conversation should show Max Context Tokens "
                    f"{MAX_CONTEXT_TOKENS}, got {new_settings['max_tokens']!r}"
                )
                assert new_settings["preserve_recent"] == str(CASE_PRESERVE_RECENT), (
                    f"The new conversation should show the newly configured Preserve "
                    f"Recent Messages {CASE_PRESERVE_RECENT}, got "
                    f"{new_settings['preserve_recent']!r}"
                )

            with allure.step("Step 6 — Open the previously existing conversation"):
                chat.navigate_to_chat(conversation_id=baseline_conversation_id)
                chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert f"/chat/{baseline_conversation_id}" in page.url, (
                    f"Should be on the baseline conversation {baseline_conversation_id}, "
                    f"URL is {page.url!r}"
                )

            with allure.step(
                f"Step 7 — Its context management settings remain unchanged: "
                f"Preserve Recent Messages is still {BASELINE_PRESERVE_RECENT} "
                f"(its creation-time value), NOT the new global "
                f"{CASE_PRESERVE_RECENT}"
            ):
                reopened_settings = self._read_conversation_context_settings(page, chat)
                assert reopened_settings == baseline_settings, (
                    f"The pre-existing conversation's context settings must be unchanged "
                    f"by the later settings edit: expected {baseline_settings}, got "
                    f"{reopened_settings}"
                )
                assert reopened_settings["preserve_recent"] != str(CASE_PRESERVE_RECENT), (
                    f"The pre-existing conversation must NOT pick up the new global "
                    f"Preserve Recent Messages ({CASE_PRESERVE_RECENT}) — settings apply "
                    f"to new conversations only"
                )
        finally:
            # Cleanup (not case steps — no allure.step): delete both
            # conversations and restore the shared ${TEST_USER} account's
            # settings. Best-effort so a cleanup failure cannot mask the real
            # assertion failure, but each failure is logged loudly.
            for conversation_id in (baseline_conversation_id, new_conversation_id):
                if conversation_id:
                    try:
                        conversation_api.delete_conversation(int(conversation_id))
                        logger.info("Cleanup: deleted conversation %s", conversation_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Cleanup: failed to delete conversation %s: %s", conversation_id, exc
                        )
            try:
                profile.navigate_to_profile()
                profile.type_max_context_tokens_raw(str(original_max_tokens))
                profile.set_preserve_recent_messages(original_preserve_recent)
                profile.wait_for_autosave(timeout=AUTOSAVE_TIMEOUT)
                logger.info(
                    "Cleanup: restored max_context_tokens=%d, preserve_recent_messages=%d",
                    original_max_tokens,
                    original_preserve_recent,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Cleanup: failed to restore profile context settings: %s", exc)
