"""UI Test for ELITEA-2200 — Chat: File Error States, Verify Unsupported
File Format Displays Error Message.

Verifies selecting a single unsupported file (``.mp4``) via the plus-menu
"Attach Files" item: a toast appears with the exact configured message
(stable prefix/suffix around the dynamic allowed-extensions list), can be
dismissed via its X icon, and the file is never added to the attachment
area. Also carries one soft-asserted, RED-by-design known defect — the
toast's severity is currently ``info`` (blue), not ``error``, despite the
case's own Objective/title expecting error-level styling.

Spec: test-specs/chat-interface/l3_attach-unsupported-file-format-error_ELITEA-2200.md

Known defect (AFS § Known Defects Found, RED-by-design per
``.agents/testing.md`` § Merge gate's analysis-time sanctioned-RED entry —
see this AFS's step-5 implementer amendment):
- EliteaAI/elitea-testing-public#1121 — ``AttachmentButton.jsx``'s
  ``displayErrorMessages()`` calls ``toastInfo(...)`` for the invalid-file
  -types branch, while the sibling 10-file-limit branch correctly uses
  ``toastWarning(...)``. The severity assertion below asserts the CORRECT
  expected severity (``error``) via ``expect.soft()`` — this is expected to
  FAIL (RED) until #1121 ships; every other assertion in this test is a
  hard assert.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@38fdb119) — shared with
ELITEA-2197 (same live session): ``chat-attach-menuitem-button``,
``toast-alert`` (+ ``data-severity``), plus this case's own addition,
``toast-dismiss-button`` on ``Toast.jsx``'s custom ``action`` close
``IconButton`` (replaces MUI's unlabeled default close button, same
onClick behavior preserved).

New page-object surface: same additive ``ChatPage`` methods as ELITEA-2197
(``open_attach_menuitem()`` / ``attach_files_via_menu()`` /
``wait_for_toast()`` / ``get_toast_text()`` / ``get_toast_alert(severity)``
/ ``dismiss_toast()`` / ``get_total_attached_file_count()``).

Usage:
    cd automation
    pytest tests/ui/chat/test_attach_unsupported_file_format_error.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

UNSUPPORTED_FILE_NAME = "unsupported.mp4"

# AFS § Automation Hints — the allowed-extensions list is dynamic
# (backend-driven), so only the stable prefix/suffix are asserted.
TOAST_TEXT_PREFIX = f"Invalid file types detected: {UNSUPPORTED_FILE_NAME} (.mp4). Only "
TOAST_TEXT_SUFFIX = " files are allowed."


class TestAttachUnsupportedFileFormatError:
    """ELITEA-2200: Chat – File Error States – Verify Unsupported File
    Format Displays Error Message (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2200_chat-file-error-states-unsupported-format-displays-error-message.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1121",
        "Known defect — toast severity is 'info', not 'error'",
    )
    @pytest.mark.p3
    def test_attach_unsupported_file_shows_error_toast(self, page, conversation_id, tmp_path):
        """Attach a .mp4 file; verify the rejection toast, dismiss, and non-attachment."""
        # Dual console/pageerror listener registered BEFORE step 1 (AFS side
        # -channel check — "no console errors" wording -> errors only).
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        unsupported_file = tmp_path / UNSUPPORTED_FILE_NAME
        unsupported_file.write_bytes(b"placeholder content for ELITEA-2200 (unsupported file type)")

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Steps 2-3 — Click + > Attach Files, select the unsupported "
            "file — verify a notification toast appears"
        ):
            chat.attach_files_via_menu(str(unsupported_file), timeout=UI_ELEMENT_TIMEOUT)
            chat.wait_for_toast(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Verify banner text: stable prefix (filename + "
            "extension) and suffix, dynamic allowed-extensions middle not "
            "hardcoded"
        ):
            toast_text = chat.get_toast_text()
            assert toast_text.startswith(TOAST_TEXT_PREFIX), (
                f"Expected toast text to start with {TOAST_TEXT_PREFIX!r}, got {toast_text!r}"
            )
            assert toast_text.endswith(TOAST_TEXT_SUFFIX), (
                f"Expected toast text to end with {TOAST_TEXT_SUFFIX!r}, got {toast_text!r}"
            )

        with allure.step(
            "Step 5 — Verify banner severity styling (KNOWN DEFECT #1121 — "
            "soft-asserted; expected severity is 'error', live currently "
            "returns 'info')"
        ):
            # Known defect: #1121 — displayErrorMessages() calls toastInfo()
            # for the invalid-file-types branch instead of an error-level
            # toast. RED-by-design until the product fix ships (see this
            # AFS's step-5 implementer amendment).
            #
            # Short timeout is deliberate, not a weakening: the toast is
            # ALREADY visible (step 4 just read its text), so a correctly-
            # severity'd toast would match instantly. A long timeout here
            # would burn into the info-toast's own 3s auto-hide
            # (TOAST_DURATION_DEFAULTS.info) and race step 6's dismiss click.
            error_severity_alert = chat.get_toast_alert("error")
            expect.soft(error_severity_alert).to_have_count(1, timeout=1000)

        with allure.step("Step 6 — Dismiss the banner via its X icon"):
            chat.dismiss_toast(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.toast_message).to_have_count(0)

        with allure.step(
            "Step 7 — Verify the unsupported file was never added to the "
            "attachment area (checked AFTER dismiss so the toast's own "
            "text can't false-positive the check)"
        ):
            total_attached = chat.get_total_attached_file_count()
            assert total_attached == 0, (
                f"Expected 0 attached files after rejecting an unsupported "
                f"type, got {total_attached}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
