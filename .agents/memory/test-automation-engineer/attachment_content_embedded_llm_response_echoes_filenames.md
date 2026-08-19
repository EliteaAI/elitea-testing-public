---
name: Attachment content is embedded in the prompt — LLM response reliably echoes filenames
description: Small distinctly-named .txt attachments + a plain "analyze these" message make the model quote filenames verbatim (no tool call) — a real, non-fabricated way to assert "response references attached files".
type: feedback
---

## Finding

When a chat message with attached files is sent, the attachment CONTENT
is embedded directly in the message payload sent to the LLM — the model's
own "Thinking" trace confirms this explicitly ("The content has been
embedded directly in the messages, so I don't need to use file reading
tools"). No toolkit/file-read call happens; the model reasons over the
literal text it was given.

**Consequence for automation:** to honestly assert a case's "response
references/acknowledges the attached files" expected-result (e.g.
ELITEA-2201) without fabricating a payload (`.agents/testing.md` §
Fidelity policy), attach several small `.txt` files with DISTINCT names
and short, distinguishable bodies, send a plain analysis-style message
("Please analyze these files" — reuse the case's own verbatim text where
given), wait for the real response
(`ChatPage.wait_for_ai_response()` + `get_last_message_text()`), and
assert each attached FILENAME appears in the response text as a
substring. Live-confirmed reliable (Claude 4.5 Sonnet, this session): all
4 attached filenames were quoted back verbatim in both the model's
"Thinking" trace and its final Markdown answer.

This is the project's documented "capture the real response and assert
against it" pattern applied to attachments specifically — the assertion
reads real generated output, it doesn't hand-author one.

## Caveats

- Keep files small and plain-text (`.txt`) — exotic/binary formats are a
  different, unrelated code path (ELITEA-2200's unsupported-format case)
  and don't need to be reachable via this technique.
- Filename-echo is a content-dependent (LLM) invariant, not a DOM
  structural one — if this ever proves flaky across gate runs, it's a
  console/AI-content flake candidate, log an occurrence in
  `.agents/testing.md` § Unconfirmed rather than assuming a code bug.
- Same-viewport gotcha as ELITEA-2196/2197 applies when attaching >2
  files: use the wide `1700×1100` viewport so all chips render as
  VISIBLE (not overflow) before counting them.

## Seen 1×

- ELITEA-2201, `test_send_message_with_attachments_verify_included.py`
  (implementation, 2026-08-19). 4 files (`report_alpha.txt`,
  `notes_beta.txt`, `summary_gamma.txt`, `plan_delta.txt`) all echoed
  verbatim in the AI response on first live exploration and first test run.
