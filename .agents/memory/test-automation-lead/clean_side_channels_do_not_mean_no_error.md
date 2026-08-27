---
name: Clean console and clean HTTP do not mean no error
description: On this stack the error can be in the WebSocket frames; a "silent failure" verdict is not verified until the frames were read.
type: feedback
aliases: [silent failure, socket_validation_error, websocket error channel, turn dies silently, instrumentation gap]
tags: [area/chat, type/instrumentation]
created: 2026-08-27
updated: 2026-08-27
---

## The correction

Three independent passes (ELITEA-2212, ELITEA-2213, ELITEA-2214's first pass) all concluded
the HITL resume "dies silently, no error". Each verified it honestly: console clean, no failed
HTTP request, no `pageerror`. All three were **wrong about the characterisation** — the backend
was rejecting the resume the whole time, over the **Socket.IO error channel nobody was reading**
(3 × `socket_validation_error`, `"llm_settings with model_name is required"`).

The observations were true. The verdict was not. That gap survived three analyst passes, two
implementer passes, three fresh-session adversarial reviews and multiple merge gates — because
every gate checked the same two channels.

## The rule for me as orchestrator

**"No error anywhere" is a claim about instrumentation coverage, not about the system.** Before
accepting a `silent` / `dies quietly` / `no error` finding from any slot, ask which channels were
actually observed, and whether the transport under test has one that was not. If a slot reports
silence, that is the cue to ask for one more channel — not to write it into a docstring as fact.

Cheap and general: a "silent" verdict should name the channels checked. If the list is
`console + HTTP` and the feature runs over WebSocket, it is incomplete by construction.

## Consequence

Corrected at module level and in `.agents/testing.md`; #1834's title rewritten so the next reader
does not re-derive it a fourth time. Shared collector now exists
(`automation/utils/websocket_frames.py`, `ChatPage.capture_websocket_frames()`); assert on the
**event name**, never the message text.

Related: [[assertions_behind_a_failing_step_never_ran]]
