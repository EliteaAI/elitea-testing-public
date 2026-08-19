"""UI Test for ELITEA-2201 — Chat: File Attachments, Send Message with
Attached Files and Verify Files Are Included.

Verifies that sending a message with attached files (a) includes the file
references in the sent message, (b) the AI/agent produces a real response
that engages with the attached content and references the filenames, and
(c) the composer's attachment chips are cleared after send.

Spec: test-specs/chat-interface/l3_send-message-with-attachments-verify-included_ELITEA-2201.md

No new testids required — every handle this case touches
(``sidebar-create-button``, ``plus-menu-button``, ``chat-attach-menuitem-button``,
``chat-attachment-chip-{index}``, ``chat-message-input``, ``chat-message-item``,
``send-button``) is pre-existing and already on ``main`` (AFS § Concrete Handles).

Response-content assertion (case step 4) is NOT a fidelity substitution: it
reads ``ChatPage.get_last_message_text()`` AFTER ``wait_for_ai_response()`` —
the real, live-generated response text — and checks the response engages
with each attached file. This is the "capture the real response and assert
against it" pattern (``.agents/testing.md`` § Fidelity policy) — the
assertion is a structural invariant over real output, not a hand-authored
payload.

Per-file check technique (relaxed 2026-08-19, ELITEA-2201 fix round): the
case's own Step 4 expected result is only "Verify LLM/agent acknowledges and
begins processing the files" / "Response references attached files" — it
does NOT require every filename to appear verbatim. Three independent live
observations during the fix showed the model varies its engagement style
run to run: (1) naming 3 files by full filename and the 4th only via its
embedded content token inside a closing summary sentence (e.g. "...all four
files contain unique identification tokens (alpha, beta, gamma,
delta)..."); (2) never naming ANY filename or token, instead quoting every
file's distinct business-content line close to verbatim (e.g. "Revenue
grew 12% in Q1", "Action items: review budget") while organizing the whole
answer by content instead of by source file; (3) paraphrasing that same
content line mid-phrase on a THIRD run ("Revenue grew 12% in Q1" → "12%
growth in Q1" — same number/topic, different word order), which broke an
initial longer-exact-phrase marker. All three are real, substantive
engagement with every attached file's content — just different, and at
times word-order-varying, prose strategies. The assertion now accepts, per
file, ANY ONE of several markers (full filename / embedded greek-letter
token / a short, paraphrase-resistant keyword drawn from that file's own
business-content line — a number, single word, or tightly-bound 2-word
phrase, never a long exact phrase), case-insensitive, as satisfying "the
response references this attachment" — still a real, per-file, non-trivial
check (never weakened to "response is non-empty"), just tolerant of the
model's observed legitimate ways — and observed paraphrase variance — of
identifying a given file.

Usage:
    cd automation
    pytest tests/ui/chat/test_send_message_with_attachments_verify_included.py -v
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# AFS § Automation Hints — a wide, fixed viewport keeps all 4 attachments as
# visible chips (FileList.jsx's visible/overflow split is container-width-
# dependent; same viewport ELITEA-2196/ELITEA-2197 use for the same reason).
VIEWPORT_WIDTH = 1700
VIEWPORT_HEIGHT = 1100
# The AI response involves real generation over the embedded attachment
# content (AFS § Network Behavior — no toolkit call is made, but generation
# itself still takes real wall-clock time; live-confirmed ~20s this session).
AI_RESPONSE_TIMEOUT = 60_000

FIRST_MESSAGE = "Please analyze these files"

# 4 distinctly-named, small .txt files (AFS § Test Data — case Test Data
# table: "3-4 supported files"; .txt is a well-supported format, ELITEA-2200).
# Third element = a list of MARKERS for that file — the AI response
# assertion (Step 4) accepts ANY one marker per file as evidence the model
# engaged with that specific attachment (see module docstring "Per-file
# check technique"). Each list is [filename, embedded greek-letter token,
# ...short paraphrase-resistant keyword(s) drawn from that file's own
# business-content line]. Keywords are deliberately SHORT (a number, a
# single word, or a 2-word phrase whose words are never separated by a
# paraphrase) — an exact longer phrase ("12% in Q1") broke on a live run
# that paraphrased to "12% growth in Q1"; a short keyword ("12%") survives
# word-order/insertion variance while staying a real, file-specific signal.
ATTACHMENT_SPECS = [
    ("report_alpha.txt", "ELITEA-2201 attachment report_alpha.txt unique-token-alpha content.\n"
                         "Revenue grew 12% in Q1.",
     ["report_alpha.txt", "alpha", "12%", "revenue"]),
    ("notes_beta.txt", "ELITEA-2201 attachment notes_beta.txt unique-token-beta content.\n"
                       "Action items: review budget.",
     ["notes_beta.txt", "beta", "budget"]),
    ("summary_gamma.txt", "ELITEA-2201 attachment summary_gamma.txt unique-token-gamma content.\n"
                          "Summary: project on track.",
     ["summary_gamma.txt", "gamma", "on track"]),
    ("plan_delta.txt", "ELITEA-2201 attachment plan_delta.txt unique-token-delta content.\n"
                       "Next step: schedule review.",
     ["plan_delta.txt", "delta", "schedule"]),
]


class TestSendMessageWithAttachmentsVerifyIncluded:
    """ELITEA-2201: Chat – File Attachments – Send Message with Attached
    Files and Verify Files Are Included (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2201_chat-file-attachments-send-message-with-attached-files-and-verify-files-are-included.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_send_message_with_attachments_verify_included(self, page, _browser_cookies, tmp_path):
        """Attach 4 files, send a message, verify the AI response engages
        with the files and the composer's attachment chips clear after send.

        Steps (AFS
        test-specs/chat-interface/l3_send-message-with-attachments-verify-included_ELITEA-2201.md):
        1. +Chat -> plus-menu -> Attach Files -> select 4 files in one
           chooser action; verify chips + counter.
        2. Type the message; verify it appears.
        3. Send; verify the message + all 4 attachments in the thread, URL.
        4. Wait for the AI response; verify it engages with each attached
           file (via any one marker — filename, embedded token, or
           distinguishing content phrase — see module docstring "Per-file
           check technique").
        5. Verify the composer's attachment chips are cleared after send.
        """
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id = None
        chat = ChatPage(page)

        # Registered before Step 1 so console errors from every step are
        # captured (AFS § Expected Results — side-channel discipline).
        console_errors = []
        page_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        file_names = [name for name, _, _ in ATTACHMENT_SPECS]
        file_paths = []
        for name, content, _markers in ATTACHMENT_SPECS:
            f = tmp_path / name
            f.write_text(content)
            file_paths.append(str(f))

        try:
            with allure.step(
                "Step 1 — +Chat -> plus-menu -> Attach Files -> select 4 "
                "files in ONE chooser action; verify chips + counter"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                assert chat.message_input.is_visible(), (
                    "Message input should be visible in the new blank conversation"
                )

                chat.attach_files_via_menu(file_paths, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_attachment_chip_count(len(file_names), timeout=UI_ELEMENT_TIMEOUT)

                attach_text = chat.attach_files_button.text_content() or ""
                assert "6 left" in attach_text, (
                    f"'Attach Files' counter should read '6 left' after "
                    f"attaching 4 of 10, got: {attach_text!r}"
                )

                attached_names = chat.get_all_attached_file_names()
                for name in file_names:
                    assert name in attached_names, (
                        f"Expected attachment {name!r}, got: {attached_names}"
                    )

            with allure.step("Step 2 — Type the message into the input; verify it appears"):
                chat.message_input.fill(FIRST_MESSAGE)
                assert (chat.message_input.input_value() or "").strip() == FIRST_MESSAGE, (
                    "Message input should show the typed text"
                )

            with allure.step(
                "Step 3 — Send (Enter); verify the message + all 4 "
                "attachments appear in the thread, URL updates"
            ):
                initial_count = chat.get_message_count()
                chat.message_input.press("Enter", timeout=60000)

                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL, got: {page.url}"
                conv_id = int(match.group(1))
                assert "name=" in page.url, (
                    f"URL should carry a '?name=...' query param after send, got: {page.url}"
                )

                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                sent_message_text = chat.get_message_text_at(initial_count)
                assert FIRST_MESSAGE in sent_message_text, (
                    "The sent user message should carry the typed text"
                )
                for name in file_names:
                    assert name in sent_message_text, (
                        f"Expected attachment {name!r} listed under the "
                        f"sent message, got: {sent_message_text!r}"
                    )

            with allure.step(
                "Step 4 — Wait for the AI response; verify it engages with "
                "each attached file (by filename or distinguishing content "
                "token)"
            ):
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

                ai_response_text = chat.get_last_message_text()
                assert ai_response_text, "AI response should be non-empty"
                # Case Step 4 only requires "Response references attached
                # files" — not that every filename appear verbatim. Accept
                # ANY ONE of a file's markers (filename / embedded
                # greek-letter token / distinguishing business-content
                # phrase, case-insensitive) as evidence the model engaged
                # with that specific attachment. This tolerates the
                # legitimate prose-variance styles observed across repeat
                # live runs (naming the file outright; citing its token in
                # a closing summary sentence; or quoting/paraphrasing its
                # content line without naming the file or token at all)
                # without weakening the check into a tautology — every one
                # of the 4 attachments must still be individually
                # accounted for in the real, live-generated response text.
                ai_response_lower = ai_response_text.lower()
                for name, _content, markers in ATTACHMENT_SPECS:
                    assert any(marker.lower() in ai_response_lower for marker in markers), (
                        f"Expected the AI response to reference attachment "
                        f"{name!r} via one of its markers {markers!r} "
                        f"(filename / embedded token / content phrase, "
                        f"case-insensitive), got: {ai_response_text!r}"
                    )

            with allure.step(
                "Step 5 — Verify the composer's attachment chips are "
                "cleared after send"
            ):
                chat.wait_for_attachment_chip_count(0, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_attachment_overflow_count() == 0, (
                    "No residual overflow attachment bucket should remain "
                    "in the composer after send"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors or "
                "uncaught exceptions across the full flow"
            ):
                assert not console_errors and not page_errors, (
                    f"Unexpected side-channel errors: "
                    f"console={[m.text for m in console_errors]!r} "
                    f"page_errors={page_errors!r}"
                )

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
