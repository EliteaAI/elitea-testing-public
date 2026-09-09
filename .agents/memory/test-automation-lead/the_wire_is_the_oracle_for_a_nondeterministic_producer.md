---
name: When the producer is nondeterministic, read the run's own state off the wire and make THAT the oracle
description: Socket.IO frames carry the state the UI renders; comparing UI to that state is observation, not substitution — and it diagnoses UI-vs-producer in one instrument
type: feedback
aliases: [wire oracle, socket.io state, agent_on_transitional_edge, nondeterministic producer, LLM content assertion, capture the real response, run state]
tags: [area/test-design, area/pipelines, type/pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The move

A test asserting a value produced by an LLM has three options, and only the
third is honest AND stable: fabricate the value (forbidden), assert its content
(flaky, and usually outside the case's contract), or **capture what the system
actually produced and assert the UI against that.**

On this stack the capture channel already exists:
`automation/utils/websocket_frames.py` (`capture_socketio_frames`), exposed as
`PipelineDetailPage.capture_websocket_frames()` / `ChatPage.…`.

For pipeline run state specifically (#2120 / ELITEA-2453):

- the frame is `agent_on_transitional_edge` with
  `response_metadata.next_step == "END"`;
- `parseRunsByEvent.helpers.js:263-278` assigns that frame's
  `response_metadata.state` to the **last** timeline entry;
- `StateItemView.jsx` renders
  `JSON.stringify(timeline[selectedStep].state[name])`.

So the frame's `state` is *exactly* the object the panel renders. Comparing them
is a real check of whether the UI carried the data through faithfully.

## Why it is not substitution

Nothing is routed, fulfilled, intercepted, delayed, rewritten or fabricated —
the frames are read passively off the live connection. Same class of evidence as
reading a response body. Say this explicitly in the docstring and the Fidelity
Declaration; a reviewer's grep will flag `capture_*` patterns for judgment.

## The bonus: it is also the diagnostic

The same comparison settles *"is this a display defect or a producer failure?"*
in one instrument — which is the question every `[FIX]` card of this shape opens
with. #2120: 30/30 UI == backend, including every empty run ⇒ the panel was
faithful and the card's "display regression" headline was refuted.

## Two operational gotchas

- **Compare PARSED values, never raw text.** `JSON.stringify` emits no separator
  spaces; Python's `json.dumps` does. (`json.dumps(v, separators=(",", ":"))` if
  a raw comparison is ever genuinely wanted.)
- **The chat answer is a DIFFERENT LLM call from the one that writes state, and
  they disagree** — observed live in a *passing* run. Anyone using the chat text
  as the oracle gets a false red.
- ⚠️ `time.sleep` cannot poll a frame list — Playwright's sync API only
  dispatches frame events while inside a Playwright call. Already in
  `.agents/testing.md`; it is a false-RED generator.

Related: [[entailment_test_separates_correction_from_masking]] ·
[[gate_on_the_environment_the_repair_is_FOR]]
