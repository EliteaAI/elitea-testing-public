"""UI test for Context Management — toggle enables/disables token fields (ELITEA-2374).

Verifies that turning the Context Management toggle OFF conditionally unmounts
the Max Context Tokens input, Preserve Recent Messages input, and the entire
Automatic Summarization sub-section from the DOM (not merely disables them),
and that turning it back ON remounts them with their prior values intact.

AFS: test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md

Known case-text vs live-product divergence (not a product defect — see AFS
Coverage Map + EliteaAI/elitea-testing-public#1238):
- Case says "Personalization -> DEFAULT CONTEXT MANAGEMENT"; the live route is
  Settings -> Memory -> "Context Management" (/settings/memory).
- Case says fields become "grayed out and uneditable"; the live mechanism is
  a conditional UNMOUNT, not a disabled/grayed-out render. Absence assertions
  (``to_have_count(0)``) are used instead, per canon ruling #511 (absence
  assertions count as references).
- The case's literal default values (Max Context Tokens = 64000, Preserve
  Recent Messages = 5) are unverifiable against the shared ``${TEST_USER}``
  account, which already carries persisted values from earlier sessions —
  this test asserts "non-empty positive integer" instead and round-trips the
  values read at test start (see AFS § Blocked Steps).

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p3: low priority (per case metadata: l3)
    - regression
"""

import logging

import allure
import pytest
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import Response, expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout / autosave constants
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000    # Fields, toggles, section container
AUTOSAVE_TIMEOUT = 10_000      # Autosave PUT round-trip
AUTOSAVE_PUT_PATH = "/api/v2/social/author/"  # Autosave endpoint for /settings/memory


def _is_autosave_put_response(response: Response) -> bool:
    """Check if response is the Context Management autosave PUT request."""
    return response.request.method == "PUT" and AUTOSAVE_PUT_PATH in response.url


def _is_autosave_get_response(response: Response) -> bool:
    """Check if response is the GET refetch that follows the autosave PUT.

    Per the settings-user-profile surface digest: every toggle click fires
    PUT .../author/ -> 200, followed immediately by a GET .../author/
    refetch. Waiting for BOTH (not just the PUT) before reading toggle state
    matters here specifically: firing a second toggle click before the first
    click's GET refetch resolves can race the DOM back to the pre-click
    state when the refetch response lands after the second click (confirmed
    live — a bare PUT-only wait let step 5's disable-click intermittently
    read back as still-enabled). The page's own ``wait_for_autosave()``
    networkidle wait is documented best-effort on this page (a persistent
    WebSocket keeps the network non-idle), so it does not reliably cover
    this — waiting on the concrete GET response here does.
    """
    return response.request.method == "GET" and AUTOSAVE_PUT_PATH in response.url


class TestContextManagementToggle:
    """Verify the Context Management toggle mounts/unmounts token fields + Automatic Summarization."""

    def test_context_management_toggle_enables_disables_fields(self, page):
        """Toggling Context Management OFF unmounts token fields + summarization; ON restores them.

        Steps map 1:1 to the AFS steps (see module docstring for the AFS path).
        """
        profile = UserProfileSettingsPage(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Memory and verify the Context "
            "Management section is visible"
        ):
            profile.navigate_to_profile()
            expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Verify the Context Management toggle is present; if "
            "OFF, turn it ON first (precondition for the rest of the flow)"
        ):
            expect(profile.context_management_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            if profile.is_context_management_enabled():
                logger.info("Context Management already ON — precondition satisfied, no click needed")
            else:
                # Dual PUT+GET wait (not just PUT) — see _is_autosave_get_response
                # docstring: without waiting out this click's own GET refetch,
                # step 5's disable-click can race it and read back as still ON.
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                assert put_info.value.status == 200, (
                    f"Turning Context Management ON (precondition) should "
                    f"autosave via PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )
                _ = get_info.value

        with allure.step(
            "Step 3 — With the toggle ON, verify Max Context Tokens and "
            "Preserve Recent Messages inputs are visible and enabled"
        ):
            expect(profile.max_context_tokens_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(profile.max_context_tokens_input).to_be_enabled()
            expect(profile.preserve_recent_messages_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(profile.preserve_recent_messages_input).to_be_enabled()

        with allure.step(
            "Step 4 — Read current field values and assert they are "
            "non-empty positive integers; store for the step-8 round-trip check"
        ):
            original_max_tokens = profile.get_max_context_tokens()
            original_preserve_messages = profile.get_preserve_recent_messages()
            assert original_max_tokens > 0, (
                f"Max Context Tokens should be a positive integer, got {original_max_tokens}"
            )
            assert original_preserve_messages > 0, (
                f"Preserve Recent Messages should be a positive integer, got {original_preserve_messages}"
            )

        try:
            with allure.step(
                "Step 5 — Click the Context Management toggle OFF; verify "
                "the autosave PUT returns 200"
            ):
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.disable_context_management()
                autosave_response = put_info.value
                assert autosave_response.status == 200, (
                    f"Toggling Context Management OFF should autosave via "
                    f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {autosave_response.status}"
                )
                # Consumed only to settle the post-toggle refetch race before
                # reading DOM state below — see _is_autosave_get_response docstring.
                _ = get_info.value
                assert not profile.is_context_management_enabled(), (
                    "Toggle should read OFF/unchecked after the click"
                )

            with allure.step(
                "Step 6 — Verify Max Context Tokens and Preserve Recent "
                "Messages inputs are absent from the DOM (conditional "
                "unmount, not disabled/grayed-out)"
            ):
                expect(profile.max_context_tokens_input).to_have_count(0)
                expect(profile.preserve_recent_messages_input).to_have_count(0)

            with allure.step(
                "Step 7 — Verify the Automatic Summarization sub-section is "
                "inactive: its toggle is absent from the DOM"
            ):
                expect(profile.automatic_summarization_toggle).to_have_count(0)

            with allure.step(
                "Step 8 — Click the Context Management toggle back ON; "
                "verify the autosave PUT returns 200, fields + Automatic "
                "Summarization reappear, and values equal the originals "
                "read in step 4 (state preserved, not reset)"
            ):
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                autosave_response = put_info.value
                assert autosave_response.status == 200, (
                    f"Toggling Context Management back ON should autosave via "
                    f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {autosave_response.status}"
                )
                # Consumed only to settle the post-toggle refetch race before
                # reading DOM state below — see _is_autosave_get_response docstring.
                _ = get_info.value

                expect(profile.max_context_tokens_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(profile.max_context_tokens_input).to_be_enabled()
                expect(profile.preserve_recent_messages_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(profile.preserve_recent_messages_input).to_be_enabled()
                expect(profile.automatic_summarization_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                restored_max_tokens = profile.get_max_context_tokens()
                restored_preserve_messages = profile.get_preserve_recent_messages()
                assert restored_max_tokens == original_max_tokens, (
                    f"Max Context Tokens should be preserved across the "
                    f"hide/show cycle: expected {original_max_tokens}, got {restored_max_tokens}"
                )
                assert restored_preserve_messages == original_preserve_messages, (
                    f"Preserve Recent Messages should be preserved across "
                    f"the hide/show cycle: expected {original_preserve_messages}, "
                    f"got {restored_preserve_messages}"
                )
        finally:
            # Safety net (not a case step — no allure.step): if a mid-flow
            # assertion failed after step 5 left the toggle OFF, restore it
            # ON so the shared ${TEST_USER} account doesn't stay polluted
            # for this or a sibling settings-user-profile test. No-op if
            # already ON (step 8 succeeded normally).
            if not profile.is_context_management_enabled():
                logger.info("Cleanup: restoring Context Management to ON after test failure")
                profile.enable_context_management()

    def test_automatic_summarization_toggle_enables_disables_own_fields(self, page):
        """Toggling Automatic Summarization OFF disables its own fields; ON re-enables them (ELITEA-2377).

        Distinct observable from ``test_context_management_toggle_enables_disables_fields``
        (ELITEA-2374): that test drives the *parent* Context Management toggle
        and observes the Automatic Summarization sub-section mount/unmount as
        a unit from the OUTSIDE. This test drives the Automatic Summarization
        toggle itself and observes its own two children (Summarization
        Instructions, Target Summary Tokens) — a DIFFERENT disable mechanism:
        a real ``disabled`` prop (``MemorySummarization.jsx``), not a
        conditional unmount. Fields stay mounted; assert
        ``to_be_disabled()`` / ``to_be_enabled()``, never ``to_have_count(0)``.

        AFS: test-specs/settings-user-profile/
        lextend_automatic-summarization-toggle-enables-disables-fields_ELITEA-2377.md
        """
        profile = UserProfileSettingsPage(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Memory and verify the Context "
            "Management section is visible"
        ):
            profile.navigate_to_profile()
            expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Ensure Context Management is enabled (precondition — "
            "Automatic Summarization is unreachable while it's OFF)"
        ):
            if profile.is_context_management_enabled():
                logger.info("Context Management already ON — precondition satisfied, no click needed")
            else:
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                assert put_info.value.status == 200, (
                    f"Turning Context Management ON (precondition) should "
                    f"autosave via PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )
                _ = get_info.value

        with allure.step(
            "Step 3 — Verify the Automatic Summarization toggle is present; "
            "if OFF, turn it ON first (precondition for the rest of the flow)"
        ):
            expect(profile.automatic_summarization_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            if profile.is_automatic_summarization_enabled():
                logger.info("Automatic Summarization already ON — precondition satisfied, no click needed")
            else:
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_automatic_summarization()
                assert put_info.value.status == 200, (
                    f"Turning Automatic Summarization ON (precondition) should "
                    f"autosave via PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )
                _ = get_info.value

        with allure.step(
            "Step 4 — With the toggle ON, verify Summarization Instructions "
            "and Target Summary Tokens are visible and enabled"
        ):
            expect(profile.summarization_instructions_textarea).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(profile.summarization_instructions_textarea).to_be_enabled()
            expect(profile.target_summary_tokens_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(profile.target_summary_tokens_input).to_be_enabled()

        with allure.step(
            "Step 5 — Read the current Target Summary Tokens value and assert "
            "it is a non-empty positive integer; store for the step-8 round-trip check"
        ):
            original_target_tokens = profile.get_target_summary_tokens()
            assert original_target_tokens > 0, (
                f"Target Summary Tokens should be a positive integer, got {original_target_tokens}"
            )

        try:
            with allure.step(
                "Step 6 — Click the Automatic Summarization toggle OFF; "
                "verify the autosave PUT returns 200"
            ):
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.disable_automatic_summarization()
                autosave_response = put_info.value
                assert autosave_response.status == 200, (
                    f"Toggling Automatic Summarization OFF should autosave via "
                    f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {autosave_response.status}"
                )
                _ = get_info.value
                assert not profile.is_automatic_summarization_enabled(), (
                    "Toggle should read OFF/unchecked after the click"
                )

            with allure.step(
                "Step 7 — Verify Summarization Instructions and Target Summary "
                "Tokens become disabled (real `disabled` prop, NOT unmounted — "
                "both fields stay present in the DOM)"
            ):
                expect(profile.summarization_instructions_textarea).to_be_disabled()
                expect(profile.target_summary_tokens_input).to_be_disabled()

            with allure.step(
                "Step 8 — Click the Automatic Summarization toggle back ON; "
                "verify the autosave PUT returns 200, both fields re-enable, "
                "and Target Summary Tokens' value equals the original read in "
                "step 5 (state preserved, not reset)"
            ):
                with page.expect_response(_is_autosave_get_response, timeout=AUTOSAVE_TIMEOUT) as get_info, \
                     page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_automatic_summarization()
                autosave_response = put_info.value
                assert autosave_response.status == 200, (
                    f"Toggling Automatic Summarization back ON should autosave via "
                    f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {autosave_response.status}"
                )
                _ = get_info.value

                expect(profile.summarization_instructions_textarea).to_be_enabled()
                expect(profile.target_summary_tokens_input).to_be_enabled()

                restored_target_tokens = profile.get_target_summary_tokens()
                assert restored_target_tokens == original_target_tokens, (
                    f"Target Summary Tokens should be preserved across the "
                    f"disable/enable cycle: expected {original_target_tokens}, "
                    f"got {restored_target_tokens}"
                )
        finally:
            # Safety net (not a case step — no allure.step): if a mid-flow
            # assertion failed after step 6 left the toggle OFF, restore it
            # ON so the shared ${TEST_USER} account doesn't stay polluted
            # for this or a sibling settings-user-profile test. No-op if
            # already ON (step 8 succeeded normally).
            if not profile.is_automatic_summarization_enabled():
                logger.info("Cleanup: restoring Automatic Summarization to ON after test failure")
                profile.enable_automatic_summarization()
