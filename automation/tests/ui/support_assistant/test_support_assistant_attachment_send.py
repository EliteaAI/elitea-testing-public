"""Support Assistant — send a message with an attached file.

TMS case ELITEA-2421 · AFS
``test-specs/support-assistant/l2_send-message-with-attached-file_ELITEA-2421.md``

Opens the Support Assistant widget, attaches a small text file through the real
file picker, types a prompt, sends it, and verifies the file made it all the way
to the model: the upload request succeeds, the outbound ``support_predict``
WebSocket frame carries the uploaded filepath, and the assistant's reply contains
a token that exists ONLY inside the uploaded file.

The oracle: the test plants a per-run fact (a randomly chosen mascot word) in the file
it uploads and asks for it back. A *"summarize this file"* prompt — the case's
literal wording — has no deterministic observable; any assertion over a free-form
summary is either vacuous or flaky. Asking for a token the model can only know by
reading the upload is strictly STRONGER than the case's own bar, and it keeps the
product as the producer of every asserted value (AFS § Declared improvisation).
The SHAPE of the planted fact matters: see ``MASCOT_WORDS`` below — asking the
assistant to relay an opaque identifier out of an attachment is refused by its
guardrail, so the fact is planted as ordinary prose instead.

Fidelity: no substitutions. The upload status comes from the real HTTP response,
the attachments array from the real outbound WebSocket frame, and the reply text
from the live model. Nothing is fabricated, injected, or seeded through a
different interface. Typing uses real input events (``fill``) — a synthetic
``value`` write does not update the React controlled textarea and manufactures a
false "Send never enables" defect (#1581).

Known defect #1653 (Step 6) — **this test is RED BY DESIGN until the product
ships the fix.** The sent user message carries no attachment indicator:
``TMessage`` has no attachment field and ``MessageItem`` renders none, so the
file leaves no trace in the conversation once the composer chip clears. The
CORRECT expected behaviour is asserted with ``expect.soft()`` per this project's
no-masking policy (sanctioned-RED exception, ``.agents/testing.md`` § Merge
gate), so the rest of the flow still runs and the assertion flips green the day
the indicator lands. Every other step hard-asserts and passes.

Synchronisation without sleeps: ``handleSend`` awaits ``startUpload`` first, then
pushes the user message, then ``emitPredict``, and only then ``clearAttachments``
(``chat.hook.ts:483-540``). So the composer chip count returning to 0 is a DOM
signal that both the upload response and the predict frame have already happened
— which is why the collected network/socket evidence is read after that
assertion, never behind a timer.

Baselines, not absolutes: the widget restores whatever conversation the test user
already has and this spec deliberately leaves its messages behind (no teardown),
so message-item and copy-button counts are DELTAS against a baseline captured
right after the widget opens, and the reply token is regenerated per run.

Markers:
    - p2 / support_assistant / ui / regression (not smoke — an upload plus a
      document-grounded live reply puts the runtime around 90-120 s)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_attachment_send.py -v
"""

import json
import uuid

import allure
import pytest
from pages.chat_page import ChatPage
from pages.support_assistant_page import SupportAssistantPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.ui,
    pytest.mark.support_assistant,
    pytest.mark.regression,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# The widget renders its restored conversation lazily; never read a baseline
# before the message list has rendered (surface digest quirk 35).
SETTLE_TIMEOUT = 60_000

# Observed reply latency on this surface: 31-135 s (surface digest quirks
# 5/15/22). This case waits for an upload PLUS a document-grounded answer and
# measured 73.7 s in analysis, so it sits at the slow end of that band.
REPLY_TIMEOUT = 200_000

ATTACHMENT_FILENAME = "ELITEA-2421-attachment.txt"
UPLOAD_URL_FRAGMENT = "/attachments/"
PREDICT_EVENT = "support_predict"

# The planted fact is a project MASCOT — an ordinary, plainly non-sensitive
# detail. Two earlier shapes were refused outright by the assistant's guardrail:
# the AFS's "the secret project codename is <TOKEN>" ("I can't help extract or
# repeat secret codename values from attachments") and a neutral-worded
# "Build identifier: <TOKEN>" ("...repeat secret identifiers from attachments").
# The guardrail keys on relaying opaque IDENTIFIERS out of an attachment, not on
# the word "secret", so the oracle is planted as a normal English fact instead.
# Strength is unchanged: the word is chosen per run and appears ONLY inside the
# uploaded file, so the reply can contain it only by reading the upload.
MASCOT_WORDS = (
    "platypus", "narwhal", "capybara", "pangolin", "axolotl",
    "wombat", "lemur", "ibex", "puffin", "okapi",
)

FILE_CONTENT_TEMPLATE = (
    "Project handbook — team facts\n\n"
    "The project mascot is the {token}.\n"
    "The team meets on Tuesdays.\n"
)

MESSAGE = (
    "According to the attached file, what is the project mascot? "
    "Answer with the single word."
)

# Vite HMR and the dev server's own polling socket log ERR_CONNECTION_REFUSED
# entries unrelated to the app (surface digest quirk 6/23). Only these two are
# excluded — every other console error still fails the test.
_DEV_SERVER_NOISE = ("@vite/client", "/socket.io/")


def _is_dev_server_noise(text: str) -> bool:
    """Whether *text* is a Vite/dev-server connection error, not an app error."""
    return "ERR_CONNECTION_REFUSED" in text and any(p in text for p in _DEV_SERVER_NOISE)


def _predict_attachment_paths(frames: list[str]) -> list[str]:
    """Extract every filepath the captured ``support_predict`` frames carried.

    Socket.IO frames arrive as ``42["support_predict",{...}]`` — an engine.io
    numeric prefix followed by a JSON array. Frames that do not parse, or that
    carry no ``attachments``, contribute nothing.

    Args:
        frames: Raw outbound WebSocket frame payloads

    Returns:
        Flattened list of the filepaths sent to the model
    """
    paths: list[str] = []
    for frame in frames:
        start = frame.find("[")
        if start < 0:
            continue
        try:
            parsed = json.loads(frame[start:])
        except ValueError:
            continue
        if not (isinstance(parsed, list) and len(parsed) > 1 and isinstance(parsed[1], dict)):
            continue
        if parsed[0] != PREDICT_EVENT:
            continue
        paths.extend(parsed[1].get("attachments") or [])
    return paths


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2421_send-message-with-attached-file.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantAttachmentSend:
    """ELITEA-2421 — send a message with an attached file."""

    def test_send_message_with_attached_file(self, page, tmp_path):
        """An attached file is uploaded, reaches the model, and is read by it."""
        # The token exists ONLY inside the file this run uploads, so the reply
        # containing it proves upload -> model -> response end to end. Generated
        # per run: the conversation is never cleaned up, so a fixed token would
        # be satisfiable by a previous run's answer on runs 2..N (digest quirk 24).
        token = MASCOT_WORDS[uuid.uuid4().int % len(MASCOT_WORDS)]
        attachment = tmp_path / ATTACHMENT_FILENAME
        attachment.write_text(FILE_CONTENT_TEMPLATE.format(token=token), encoding="utf-8")

        console_errors: list[str] = []
        upload_statuses: list[int] = []
        predict_frames: list[str] = []

        def _capture_socket(websocket) -> None:
            websocket.on(
                "framesent",
                lambda payload: predict_frames.append(payload)
                if isinstance(payload, str) and PREDICT_EVENT in payload
                else None,
            )

        # All three collectors are armed BEFORE navigation: page.on("websocket")
        # only fires for sockets opened after it is attached (digest quirk 8),
        # and the upload is an XHR that page.on("response") sees but a
        # fetch-scoped expectation would not (quirk 37).
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and not _is_dev_server_noise(msg.text)
            else None,
        )
        page.on(
            "response",
            lambda response: upload_statuses.append(response.status)
            if UPLOAD_URL_FRAGMENT in response.url
            else None,
        )
        page.on("websocket", _capture_socket)

        support_page = SupportAssistantPage(page)

        with allure.step("Step 1 — Open the Support Assistant widget"):
            ChatPage(page).navigate_to_chat()
            support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
            expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)

            # The restored conversation renders asynchronously; a baseline read
            # before it lands returns 0 and poisons every delta below. Every
            # conversation holds at least the assistant greeting, whose copy
            # button renders only once the message is complete (quirks 9/10/35).
            expect(support_page.message_copy_buttons).not_to_have_count(
                0, timeout=SETTLE_TIMEOUT
            )
            baseline_copies = support_page.get_copy_button_count()
            baseline_user_items = support_page.get_user_message_item_count()

        with allure.step("Step 2 — Click Attach file and select a small text file"):
            support_page.attach_file_via_testid(str(attachment), timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 3 — An attachment chip appears in the input area before sending"
        ):
            expect(support_page.attachment_chips).to_have_count(1, timeout=EXPECT_TIMEOUT)
            expect(support_page.attachment_chips.first).to_contain_text(
                ATTACHMENT_FILENAME, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 4 — Type the prompt in the input field"):
            support_page.set_message_text(MESSAGE)
            expect(support_page.message_input_field).to_have_value(
                MESSAGE, timeout=EXPECT_TIMEOUT
            )
            # Text is required even with an attachment staged: isSendDisabled =
            # disabled || isUploading || !attachmentsValid || !text.trim()
            # (MessageInput.tsx:105-108, digest quirk 41).
            expect(support_page.send_message_button).to_be_enabled(timeout=EXPECT_TIMEOUT)

        with allure.step("Step 5 — Click Send"):
            support_page.send_message_button.click(timeout=EXPECT_TIMEOUT)

            # clearAttachments() runs last in handleSend, after the awaited
            # upload and after emitPredict — so this single DOM assertion is the
            # sleep-free proof that both have already happened, and it also
            # distinguishes "chip cleared by design" from "chip never existed".
            expect(support_page.attachment_chips).to_have_count(0, timeout=REPLY_TIMEOUT)
            expect(support_page.user_message_items()).to_have_count(
                baseline_user_items + 1, timeout=EXPECT_TIMEOUT
            )

            # The file really left the browser. This is the exact claim the
            # superseded 2026-08-18 analysis got wrong (false bug #1584): the
            # upload fires on Send, not on attach, so a capture armed around the
            # attach click sees nothing (digest quirk 37).
            assert upload_statuses, (
                "No request to "
                f"{UPLOAD_URL_FRAGMENT!r} was observed — the attachment never left the browser"
            )
            assert all(status < 300 for status in upload_statuses), (
                f"Attachment upload did not succeed: statuses={upload_statuses}"
            )

            # The filepath reached the model. Sending is a WebSocket frame, not
            # a POST (digest quirks 8/38) — this is the causal link between the
            # upload above and the assistant's answer in Step 7.
            sent_paths = _predict_attachment_paths(predict_frames)
            assert any(ATTACHMENT_FILENAME in path for path in sent_paths), (
                f"The {PREDICT_EVENT!r} frame did not carry {ATTACHMENT_FILENAME!r}: "
                f"attachments={sent_paths}"
            )

        with allure.step(
            "Step 6 — The sent message shows an attachment indicator (known defect #1653)"
        ):
            # Known defect: #1653 — TMessage (chat.types.ts:1-11) has no
            # attachment field and chat.hook.ts:492-495 pushes only
            # {id, role, content, timestamp}, so MessageItem renders no
            # attachment element. Asserting the CORRECT behaviour softly so this
            # flips green when the product ships it; it blocks no other step.
            # Asserted on the already-testid'd user item — no locator is invented
            # for an element that does not exist.
            expect.soft(
                support_page.last_user_item(),
                "Known defect: #1653 — the sent message should show an "
                "attachment indicator naming the attached file",
            ).to_contain_text(ATTACHMENT_FILENAME, timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 7 — The assistant returns a response that processes the file content"
        ):
            # The copy button renders only on a COMPLETED assistant message
            # (MessageItem.tsx: content && !isStreaming && !isAnimating), which
            # makes its count the accurate reply-finished signal (quirks 9/17).
            expect(support_page.message_copy_buttons).to_have_count(
                baseline_copies + 1, timeout=REPLY_TIMEOUT
            )
            expect(support_page.last_assistant_item()).to_contain_text(
                token, ignore_case=True, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 8 — No console errors across the flow"):
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
