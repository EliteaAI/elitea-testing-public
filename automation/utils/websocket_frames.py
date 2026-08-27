"""Passive Socket.IO frame capture for UI specs.

Why this exists
---------------
Some product behaviour is only observable on the wire. The HITL resume path
(``chat_continue_predict``) is the canonical example: the browser sends the
user's decision as a Socket.IO event and the backend may answer with a
``socket_validation_error`` that the frontend swallows entirely — no console
error, no toast, no message-state change. Read from the DOM alone, such a turn
looks *silent*; read from the frames, it is plainly *rejected*
(ELITEA-2214 AFS § REWORK, Q1).

``PipelineDetailPage.capture_websocket_frames()`` (ELITEA-2015) derived this
shape first, for the pipeline HITL Approve/Reject diagnosis. This module is
that pattern's shared home so a third consumer does not re-derive it again;
:meth:`pages.chat_page.ChatPage.capture_websocket_frames` delegates here.

**This is observation, not substitution** (``.agents/testing.md`` § Fidelity
policy). Nothing is routed, fulfilled, intercepted, delayed, rewritten or
fabricated — it is the same class of evidence as reading a response body. The
values a spec asserts on are still produced end to end by the real system.

Usage::

    from utils.websocket_frames import capture_socketio_frames

    with capture_socketio_frames(page) as frames:   # BEFORE any navigation
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)
        ...
        before = len(frames)
        chat.sensitive_action_block_button.first.click()   # a page-object field
        window = frames[before:]

**Waiting for a frame requires a Playwright call.** The sync API dispatches
``framesent`` / ``framereceived`` only while the calling thread is inside a
Playwright call, so a ``time.sleep`` poll starves the dispatcher and this list
cannot grow while it runs (measured 2026-08-27: frozen for a full 15 s, then
every queued frame arrived at once on the next Playwright call). Step such a
poll with ``page.wait_for_timeout(...)``, or simply do the frame reads after a
step that already waits on the page.
"""

import json
from contextlib import contextmanager
from typing import Any

#: Engine.IO ``4`` (message) + Socket.IO ``2`` (event) — the ``42["name", {...}]``
#: wire shape that carries application-level events. Everything else on the
#: socket (ping/pong, connect acks, raw keepalives) is protocol noise.
SOCKETIO_EVENT_PREFIX = "42"


def parse_socketio_event(payload: Any) -> tuple[str, Any] | None:
    """Return ``(event_name, event_payload)`` for a ``42[...]`` frame, else ``None``.

    Non-event frames don't match the prefix and are skipped. An optional
    namespace prefix (``42/ns,[...]``) is tolerated.
    """
    if not isinstance(payload, str) or not payload.startswith(SOCKETIO_EVENT_PREFIX):
        return None
    rest = payload[len(SOCKETIO_EVENT_PREFIX):]
    if rest.startswith("/"):  # optional namespace prefix, e.g. "/ns,"
        comma = rest.find(",")
        if comma == -1:
            return None
        rest = rest[comma + 1:]
    try:
        data = json.loads(rest)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, list) or not data:
        return None
    return data[0], (data[1] if len(data) > 1 else None)


@contextmanager
def capture_socketio_frames(page: Any):
    """Capture Socket.IO event frames on *page* for the duration of the block.

    **Must be entered BEFORE the page navigates.** Playwright's ``"websocket"``
    page event fires once, at connection-open time; a listener attached after
    the connection is already open never fires (confirmed live on the pipeline
    HITL work: entering the capture mid-test yielded zero frames for the rest
    of the test). Enter it once per test, keep the whole flow inside it, and
    slice a specific step's window with ``before = len(frames)`` — do NOT
    re-enter it mid-test expecting a fresh window.

    Yields a **live** list that accumulates one dict per application-level
    event frame, in arrival order. Each dict is the event's payload (or
    ``{"_value": payload}`` when the payload isn't a dict) plus:

    * ``event`` — the Socket.IO event name (``"chat_continue_predict"``,
      ``"socket_validation_error"``, …)
    * ``_direction`` — ``"sent"`` or ``"received"``
    """
    frames: list[dict] = []

    def _record(direction: str):
        def _handler(payload: Any) -> None:
            parsed = parse_socketio_event(payload)
            if parsed is None:
                return
            event_name, event_payload = parsed
            record = dict(event_payload) if isinstance(event_payload, dict) else {"_value": event_payload}
            record["event"] = event_name
            record["_direction"] = direction
            frames.append(record)

        return _handler

    def _on_websocket(ws: Any) -> None:
        ws.on("framesent", _record("sent"))
        ws.on("framereceived", _record("received"))

    page.on("websocket", _on_websocket)
    try:
        yield frames
    finally:
        page.remove_listener("websocket", _on_websocket)
