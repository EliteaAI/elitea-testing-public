"""Oracle for a toolkit tool execution, read off the ``agent_tool_end`` frame.

Why this exists
---------------
Elitea publishes **no structural marker** for a failed toolkit tool execution.
A GitHub 401 and a clean Jira project list render through byte-identical DOM,
the same testids, the same Socket.IO event sequence, and
``finish_reason: "stop"`` on both; a recursive key-path diff of the two
``agent_tool_end`` frames found *zero* differences, and the only error-ish keys
anywhere on the wire (``chat_message_sync.meta.error`` / ``.is_error``) read
``""`` / ``false`` even on a genuine 401. The failure exists only as the
*string the tool returned* — ``response_metadata.tool_output`` — which the LLM
then re-narrates in freshly generated prose
(ELITEA-1140 AFS §§ Finding 1-2, Q2; card #1817).

Two consequences shape this module:

1. **Never scan free text for the word "error".** The tool's own success
   payload legitimately contains it — this repository's branch list carries
   ``tests/ELITEA-1980-credential-error-states`` — so a negative substring scan
   is a race against the repository's own branch names. That scan is exactly
   the defect #1817 exists to remove; it broke CI on a *successful* run
   (GHA ``32931571484``). It is equally wrong on the wire channel, because the
   same branch names travel in ``tool_output``.
2. **Never scan the chat message either.** It is LLM prose, different on every
   run: three real 401s produced three phrasings, none containing the literal
   the old guard looked for, and all three containing the word ``branches`` —
   i.e. they satisfied ``chat_response_keywords`` while the toolkit was
   provably broken.

The honest oracle is therefore **positive and anchored**: the expected tool of
the expected toolkit produced exactly one ``agent_tool_end``, and its
``tool_output`` matches that toolkit's *captured* success shape.

**This is observation, not substitution** (``.agents/testing.md`` § Fidelity
policy). Every value read here is produced end to end by the real system and
merely observed on the wire, the same class of evidence as reading a response
body. Nothing is routed, fulfilled, injected or fabricated.

The functions are pure and browser-free on purpose, so the classification is
pinned by ``tests/unit/test_toolkit_chat_error_oracle.py`` against real
captured payloads.
"""

import re
from typing import Any

#: Frame ``type`` carrying a finished tool execution and its ``tool_output``.
AGENT_TOOL_END = "agent_tool_end"


def find_tool_end_frames(
    frames: Any,
    tool_name: str,
    toolkit_display_name: str | None = None,
) -> list[dict]:
    """Return the received ``agent_tool_end`` frames for *tool_name*.

    *frames* is the live list yielded by
    :func:`utils.websocket_frames.capture_socketio_frames`.

    When *toolkit_display_name* is given, only frames whose
    ``response_metadata.metadata.display_name`` equals it are returned — that
    is the toolkit's human name, i.e. what ``managed_toolkit["name"]`` holds,
    so a test never accepts some *other* participant's tool call as evidence
    that its own toolkit ran.

    Malformed or unrelated frames are skipped rather than raising: the stream
    also carries LLM chunks, sync frames and protocol noise.
    """
    matched: list[dict] = []
    for frame in frames or ():
        if not isinstance(frame, dict):
            continue
        if frame.get("_direction") != "received":
            continue
        if frame.get("type") != AGENT_TOOL_END:
            continue
        metadata = frame.get("response_metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("tool_name") != tool_name:
            continue
        if toolkit_display_name is not None:
            inner = metadata.get("metadata")
            if not isinstance(inner, dict):
                continue
            if inner.get("display_name") != toolkit_display_name:
                continue
        matched.append(frame)
    return matched


def get_tool_output(frame: Any) -> str:
    """Return ``response_metadata.tool_output`` of *frame*, or ``""``.

    ``""`` means "the frame carried no tool output" — a caller asserting the
    tool ran should treat that as a failure, never as a pass.
    """
    if not isinstance(frame, dict):
        return ""
    metadata = frame.get("response_metadata")
    if not isinstance(metadata, dict):
        return ""
    output = metadata.get("tool_output")
    return output if isinstance(output, str) else ""


def tool_output_matches_success(output: str, pattern: str) -> bool:
    """Return whether *output* matches this toolkit's captured success shape.

    *pattern* is an **anchored** regex applied with :func:`re.match`, so it
    describes how the toolkit's own successful output *starts* — a positive
    statement about a shape that was observed live, never a blocklist of words
    that must be absent.

    Raises:
        ValueError: if *pattern* is empty. An empty
            ``ToolkitConfig.tool_output_success_pattern`` means "this toolkit's
            success shape has never been captured", and the caller must then
            apply the fallback rule (assert the tool ran and that the UI
            carried a result through, and classify nothing) — silently
            treating an empty pattern as a pass would invent the very verdict
            this module refuses to guess.
    """
    if not pattern:
        raise ValueError(
            "tool_output_success_pattern is empty — no success shape has been "
            "captured for this toolkit; the caller must skip the "
            "success/failure classification instead of calling this."
        )
    if not isinstance(output, str):
        return False
    return re.match(pattern, output) is not None


def observed_frame_kinds(frames: Any) -> list[tuple[str, str]]:
    """Return the distinct ``(type, tool_name)`` pairs among *received* frames.

    A triage aid for a failed Tier-1 assertion, which otherwise reports
    identically for three unrelated causes:

    * **harness** — the capture itself produced nothing (the context manager
      was entered after the socket opened, the transport fell back to
      ``/socket.io/?EIO=4&transport=polling``, the env never connected). Tell:
      the *total* frame count is 0.
    * **product** — frames flowed but none is an ``agent_tool_end`` for this
      tool: the model answered without calling it. Tell: a large total with no
      ``agent_tool_end`` pair, or one naming a different tool/toolkit.
    * **double call** — more than one matching frame.

    ``type`` falls back to the Socket.IO event name for frames whose payload
    carries none, so protocol traffic stays identifiable; ``tool_name`` is
    ``""`` when the frame carries none. Sorted, so the message is stable.
    """
    kinds: set[tuple[str, str]] = set()
    for frame in frames or ():
        if not isinstance(frame, dict) or frame.get("_direction") != "received":
            continue
        kind = frame.get("type") or frame.get("event") or ""
        metadata = frame.get("response_metadata")
        tool_name = metadata.get("tool_name", "") if isinstance(metadata, dict) else ""
        kinds.add((str(kind), str(tool_name or "")))
    return sorted(kinds)
