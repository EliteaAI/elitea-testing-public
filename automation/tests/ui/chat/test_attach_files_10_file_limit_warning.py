"""UI Test for ELITEA-2197 — Chat: File Attachments, Upload Maximum 10 Files
and Verify Limit Warning.

Verifies selecting 11 files in a single native file-chooser action against
the 10-attachment limit: a warning toast appears with the exact configured
text and MUI ``warning`` severity styling, and exactly 10 files remain
attached (the 11th excluded) — asserted as visible-chip-count + parsed
overflow-("+N")-count == 10, plus an explicit absence check for the 11th
filename in both the visible chips and the opened overflow menu.

Spec: test-specs/chat-interface/l3_attach-files-10-file-limit-warning_ELITEA-2197.md

Case-text deviation (AFS § Coverage Map, filed EliteaAI/elitea-testing-public#1122):
the case's own two-action sequence ("attach 10, then separately attempt an
11th via + > Attach Files") is not reproducible live — the live product
DISABLES the "Attach Files" menu item once exactly 10 files are attached
(``isAtMaxAttachmentCapacity`` -> ``disabled``), so a disabled MUI button
never fires a second file-chooser. The corrected, live-confirmed trigger
(all 11 files selected in ONE chooser action) reaches the identical
observable state the case's Objective/Pass criteria require.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@38fdb119):
- ``chat-attach-menuitem-button`` — the ``showLabel`` ``AttachmentButton``
  instance rendered inside the plus-menu popper (``PlusChatButton.jsx``'s
  ``MenuList``), via a new ``testId`` prop threaded through
  ``AttachmentButton.jsx``. Re-points the pre-existing but dead
  ``ChatPage.attach_files_button`` field (its old testid,
  ``chat-attach-button``, never existed in EliteaUI source — the field only
  "worked" via its now-forbidden ``fallback=``).
- ``toast-alert`` (+ ``data-severity`` attribute) on ``Toast.jsx``'s MUI
  ``Alert`` root — testid is the stable identity, severity is state carried
  via ``data-severity`` per the "testid = identity, state via data-*"
  policy.
- ``chat-attachment-chip-{index}`` (dynamic) on ``FileList.jsx``'s per-item
  visible chip ``Box``.
- ``chat-attachment-overflow-button`` (static) +
  ``chat-attachment-overflow-item-{index}`` (dynamic) on ``FileList.jsx``'s
  "+N" control and its opened-menu items.

New page-object surface (``ChatPage``, all additive — no existing method
signature changed; ``attach_files_button`` re-pointed per above, and
``open_file_chooser()``/``attach_file()`` now route through the plus menu
first since the menu item only renders while the popper is open — neither
was previously called by any test):
- ``open_attach_menuitem()`` / ``attach_files_via_menu(file_paths)``
- ``wait_for_toast()`` / ``get_toast_text()`` / ``get_toast_alert(severity)``
- ``get_attachment_chip_count()`` / ``get_attachment_overflow_count()`` /
  ``get_total_attached_file_count()``
- ``get_visible_attachment_names()`` / ``get_overflow_attachment_names()`` /
  ``get_all_attached_file_names()``

Known defects: none for this case (see AFS § Known Defects Found).

Usage:
    cd automation
    pytest tests/ui/chat/test_attach_files_10_file_limit_warning.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# AFS § Automation Hints — a wide, fixed viewport makes FileList.jsx's
# width-driven visible/overflow split deterministic across CI runs. The
# TOTAL count (visible + overflow) is still what's asserted, never a
# hardcoded "N visible" number.
VIEWPORT_WIDTH = 1700
VIEWPORT_HEIGHT = 1100

MAX_ATTACHMENTS = 10
FILE_COUNT = MAX_ATTACHMENTS + 1  # 11 — one past the limit

# Confirmed live, verbatim (AFS § Test Data / ATTACHMENT_LIMITS in
# EliteaUI/src/common/constants.js:1084).
EXPECTED_WARNING_TEXT = "You've reached the 10-file limit. Only the first 10 will be processed."

LAST_FILE_NAME = f"testfile_{FILE_COUNT}.txt"  # testfile_11.txt — the excluded file


class TestAttachFiles10FileLimitWarning:
    """ELITEA-2197: Chat – File Attachments – Upload Maximum 10 Files and
    Verify Limit Warning (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2197_chat-file-attachments-upload-maximum-10-files-and-verify-limit-warning.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_attach_11_files_shows_10_file_limit_warning(self, page, conversation_id, tmp_path):
        """Select 11 files at once; verify the 10-file-limit warning + exactly 10 kept.

        Setup only (not a case step): 11 uniquely-named ``.txt`` files
        generated via ``tmp_path`` (AFS § Test Data — matches the existing
        ``test_attach_files_button_sends_file_with_message`` pattern).
        """
        # Dual console/pageerror listener registered BEFORE step 1 (AFS side
        # -channel check — "no console errors" wording -> errors only).
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        file_paths = []
        for i in range(1, FILE_COUNT + 1):
            f = tmp_path / f"testfile_{i}.txt"
            f.write_text(f"Content of testfile_{i}.txt for ELITEA-2197.")
            file_paths.append(str(f))

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Steps 2-3 — Click + > Attach Files, select all 11 files in a "
            "single file-chooser action — verify a warning toast appears"
        ):
            # AFS Coverage Map: the case's literal two-action sequence is
            # unreachable live (the menu item disables at max capacity,
            # issue #1122) — all 11 files are selected in ONE chooser
            # action, the corrected trigger that reaches the same
            # observable state.
            chat.attach_files_via_menu(file_paths, timeout=UI_ELEMENT_TIMEOUT)
            chat.wait_for_toast(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 4 — Verify the warning text is exact"):
            toast_text = chat.get_toast_text()
            assert toast_text == EXPECTED_WARNING_TEXT, (
                f"Expected warning text {EXPECTED_WARNING_TEXT!r}, got {toast_text!r}"
            )

        with allure.step(
            "Step 5 — Verify warning styling: MUI Alert severity=warning "
            "(amber/orange, warning-triangle icon)"
        ):
            warning_alert = chat.get_toast_alert("warning")
            assert warning_alert.count() > 0, (
                "Toast alert should carry data-severity='warning' for the "
                "10-file-limit warning"
            )

        with allure.step(
            "Step 6 — Verify exactly 10 files remain attached (visible "
            "chips + overflow) and the 11th file is not attached anywhere"
        ):
            total_attached = chat.get_total_attached_file_count()
            assert total_attached == MAX_ATTACHMENTS, (
                f"Expected exactly {MAX_ATTACHMENTS} attached files "
                f"(visible chips + overflow), got {total_attached}"
            )

            all_names = chat.get_all_attached_file_names()
            assert LAST_FILE_NAME not in all_names, (
                f"{LAST_FILE_NAME!r} (the 11th, over-limit file) should not "
                f"appear as an attachment — attached names: {all_names}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
