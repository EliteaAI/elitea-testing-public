"""Support Assistant — attach a file by dragging and dropping it on the composer.

TMS case ELITEA-2420 · AFS
``test-specs/support-assistant/l2_drag-and-drop-file-attachment_ELITEA-2420.md``

Opens the Support Assistant widget, drags a small text file over the composer,
asserts the drag-over affordance appears and reverts, drops the file, and
verifies the dropped file made it all the way to the model: an attachment chip
is staged, Send stays disabled until a prompt is typed, the upload request
succeeds, the outbound ``support_predict`` WebSocket frame carries the uploaded
filepath, and the assistant's reply contains a token that exists ONLY inside the
dropped file.

Why a separate spec from ``test_support_assistant_attachment_send.py``
(ELITEA-2421): that one attaches through the FILE PICKER. It never dispatches a
drag event, never touches the drop zone, and cannot fail if ``handleDrop`` /
``handleDragEnter`` regress or if the drop overlay disappears — a different
entry point is not covered by the same screen. That spec is also sanctioned-RED
by design (#1653), and mixing a green case into it would muddy every gate run's
signal. Its module-level constants are deliberately re-stated here rather than
shared, so a green spec is not coupled to a red one.

Two case-text imprecisions, filed as clarification #1655 — the PRODUCT is
correct in both, so the live contract is what is asserted (reverse-masking
guard):

1. Only the COMPOSER accepts drops, not the "chat area" of the case text.
   ``onDrop`` lives on the input-area div (``MessageInput.tsx``); the message
   list is a sibling and was probed live as completely inert.
2. An attachment alone does NOT enable Send — text is still required
   (``isSendDisabled = disabled || isUploading || !attachmentsValid ||
   !text.trim()``). This spec asserts Send DISABLED with the chip staged and
   the composer empty, then enabled after typing.

The oracle: the test plants a per-run fact (a randomly chosen mascot word) in
the file it drops and asks for it back. The case's literal content
(``"Drag and drop test"``) has no assertable observable — any assertion over a
free-form reply to it is vacuous or flaky. Asking for a token the model can
only know by reading the dropped file is strictly STRONGER than the case's own
bar (AFS § Declared improvisation). The SHAPE of the planted fact matters: the
assistant's guardrail refuses to relay opaque IDENTIFIERS out of an attachment,
so the fact is planted as ordinary prose.

Fidelity: ONE substitution, TRANSIT ONLY, and it is the input GESTURE — never an
observable. Playwright cannot drive a native OS-level file drag, so
``SupportAssistantPage.drag_file_over_composer`` / ``drop_file_on_composer``
build a ``DataTransfer`` in-page holding a REAL ``File`` reconstructed from the
bytes this test just wrote to ``tmp_path``, and dispatch real ``DragEvent``s at
the drop zone. From ``handleDragEnter``/``handleDrop`` onward the product code
path is byte-identical to a human drag, and EVERY asserted value is
product-produced: the overlay render, the chip and its filename, the Send
disabled/enabled state, the upload HTTP status, the ``support_predict`` frame's
``attachments[]``, and the assistant's reply. Nothing is mocked, injected, or
seeded through a different interface — in particular the file is NOT attached
through the file picker, which is ELITEA-2421's interface and would substitute
the very subject of this case. The identical technique is already merged and
reviewed as ``ChatPage.drag_and_drop_file()``. Typing uses real input events
(``fill``) — a synthetic ``value`` write does not update the React controlled
textarea and manufactures a false "Send never enables" defect (#1581).

Known defect #1653 (the sent user message carries no attachment indicator)
reproduces here identically but is deliberately NOT asserted: ELITEA-2421's spec
already owns it as a linked ``expect.soft()`` red, and duplicating it would add a
second permanent red for one defect with zero new information. This case's "the
attachment was submitted" claim is proved more strongly by the upload status, the
predict frame carrying the filepath, and the assistant answering from the file's
content.

Synchronisation without sleeps: ``handleSend`` awaits ``startUpload`` first, then
pushes the user message, then ``emitPredict``, and only then ``clearAttachments``
(``chat.hook.ts``). So the composer chip count returning to 0 is a DOM signal that
both the upload response and the predict frame have already happened — which is
why the collected network/socket evidence is read after that assertion, never
behind a timer.

Baselines, not absolutes: the widget restores whatever conversation the test user
already has and this spec deliberately leaves its messages behind (no teardown —
the widget has no delete-conversation affordance), so message-item and copy-button
counts are DELTAS against a baseline captured right after the widget opens, the
filename is case-id-prefixed so it cannot collide with ELITEA-2421's file in the
shared conversation, and the reply token is regenerated per run.

Markers:
    - p2 / support_assistant / ui / regression (not smoke — a live reply puts the
      runtime around 60-90 s)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_drag_drop_attachment.py -v
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
# measured 70.7 s in analysis, so it sits at the slow end of that band.
REPLY_TIMEOUT = 200_000

ATTACHMENT_FILENAME = "ELITEA-2420-drag-test.txt"

# The FULL API fragment, deliberately not the bare "/attachments/": the Vite dev
# server serves the widget's own module URLs from
# ``src/components/chat/attachments/`` and those 200s match the short fragment,
# so a collector keyed on it can be non-empty with ZERO real uploads (observed
# live during analysis — AFS § Known Defects).
UPLOAD_URL_FRAGMENT = "/api/v2/support_assistant/attachments/"
PREDICT_EVENT = "support_predict"

DROP_OVERLAY_TEXT = "Drop files here"

# The planted fact is a project MASCOT — an ordinary, plainly non-sensitive
# detail. The assistant's guardrail refuses to relay opaque IDENTIFIERS out of an
# attachment ("I can't help extract or repeat secret codename values from
# attachments"), not the word "secret", so the oracle is planted as a normal
# English fact instead. Strength is unchanged: the word is chosen per run and
# appears ONLY inside the dropped file, so the reply can contain it only by
# reading the upload.
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
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2420_drag-and-drop-file-attachment.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantDragDropAttachment:
    """ELITEA-2420 — drag and drop file attachment."""

    def test_drag_and_drop_file_attachment(self, page, tmp_path):
        """A dropped file is staged, uploaded, reaches the model, and is read by it."""
        # The token exists ONLY inside the file this run drops, so the reply
        # containing it proves drop -> upload -> model -> response end to end.
        # Generated per run: the conversation is never cleaned up, so a fixed
        # token would be satisfiable by a previous run's answer on runs 2..N
        # (digest quirk 24).
        token = MASCOT_WORDS[uuid.uuid4().int % len(MASCOT_WORDS)]

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

        with allure.step("Step 2 — Prepare a small test file on disk"):
            attachment = tmp_path / ATTACHMENT_FILENAME
            attachment.write_text(FILE_CONTENT_TEMPLATE.format(token=token), encoding="utf-8")
            assert attachment.is_file(), f"Test file was not written: {attachment}"

        with allure.step(
            "Step 3 — Drag the file over the composer: the drop affordance appears"
        ):
            # The overlay is the only DOM proof the drop zone RECEIVED the drag.
            # Without it, a drop that silently did nothing is indistinguishable
            # from a drop that worked.
            support_page.drag_file_over_composer(str(attachment), timeout=EXPECT_TIMEOUT)
            expect(support_page.drop_overlay).to_be_visible(timeout=EXPECT_TIMEOUT)
            expect(support_page.drop_overlay).to_have_text(
                DROP_OVERLAY_TEXT, timeout=EXPECT_TIMEOUT
            )

        with allure.step(
            "Step 3b — Dragging away reverts the affordance (it is driven by the drag)"
        ):
            # Proves the overlay is a drag-driven affordance and not a permanent
            # element that happens to be visible.
            support_page.drag_leave_composer(str(attachment), timeout=EXPECT_TIMEOUT)
            expect(support_page.drop_overlay).to_have_count(0, timeout=EXPECT_TIMEOUT)

        with allure.step("Step 3c — Drop the file onto the composer"):
            support_page.drop_file_on_composer(str(attachment), timeout=EXPECT_TIMEOUT)
            expect(support_page.drop_overlay).to_have_count(0, timeout=EXPECT_TIMEOUT)

        with allure.step(
            "Step 4 — The file is accepted: an attachment chip appears in the input area"
        ):
            expect(support_page.attachment_chips).to_have_count(1, timeout=EXPECT_TIMEOUT)
            expect(support_page.attachment_chips.first).to_contain_text(
                ATTACHMENT_FILENAME, timeout=EXPECT_TIMEOUT
            )

        with allure.step("Step 5 — Send enables once a prompt is typed"):
            # Live contract, clarification #1655: an attachment ALONE does not
            # enable Send — isSendDisabled = disabled || isUploading ||
            # !attachmentsValid || !text.trim() (MessageInput.tsx:105-108).
            # Asserting the case text's "Send becomes enabled" here would be
            # reverse-masking a correct product behaviour.
            expect(support_page.send_message_button).to_be_disabled(timeout=EXPECT_TIMEOUT)

            support_page.set_message_text(MESSAGE)
            expect(support_page.message_input_field).to_have_value(
                MESSAGE, timeout=EXPECT_TIMEOUT
            )
            expect(support_page.send_message_button).to_be_enabled(timeout=EXPECT_TIMEOUT)

        with allure.step("Step 6 — Click Send: the message and its attachment are submitted"):
            support_page.send_message_button.click(timeout=EXPECT_TIMEOUT)

            # clearAttachments() runs last in handleSend, after the awaited
            # upload and after emitPredict — so this single DOM assertion is the
            # sleep-free proof that both have already happened, and it also
            # distinguishes "chip cleared by design" from "chip never existed".
            expect(support_page.attachment_chips).to_have_count(0, timeout=REPLY_TIMEOUT)
            expect(support_page.user_message_items()).to_have_count(
                baseline_user_items + 1, timeout=EXPECT_TIMEOUT
            )

            # The dropped file really left the browser. This is the exact claim
            # false bug #1584 got wrong: the upload fires on Send, not on drop,
            # so a capture armed around the drop sees nothing (digest quirk 37).
            assert upload_statuses, (
                f"No request to {UPLOAD_URL_FRAGMENT!r} was observed — "
                "the dropped attachment never left the browser"
            )
            assert all(status < 300 for status in upload_statuses), (
                f"Attachment upload did not succeed: statuses={upload_statuses}"
            )

            # The filepath reached the model. Sending is a WebSocket frame, not
            # a POST (digest quirks 8/38) — this is the causal link between the
            # upload above and the assistant's answer below.
            sent_paths = _predict_attachment_paths(predict_frames)
            assert any(ATTACHMENT_FILENAME in path for path in sent_paths), (
                f"The {PREDICT_EVENT!r} frame did not carry {ATTACHMENT_FILENAME!r}: "
                f"attachments={sent_paths}"
            )

        with allure.step(
            "Step 6b — The assistant processes the dropped file and answers from its content"
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

        with allure.step("Step 7 — No console errors across the flow"):
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
