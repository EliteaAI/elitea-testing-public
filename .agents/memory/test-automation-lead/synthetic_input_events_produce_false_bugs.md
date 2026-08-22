---
name: Synthetic input events produce false product bugs
description: A test-authored input event is a fidelity substitution on the INPUT side — it made 3 bugs and parked 9 cases for 4 days
type: feedback
aliases: [false bug, input.value, synthetic typing, controlled component, react controlled textarea, disabled button never enables]
tags: [area/fidelity, type/lesson]
created: 2026-08-22
updated: 2026-08-22
---

## The failure

Support Assistant cases ELITEA-2418/2424/2425 were parked four days on bugs
#1581 ("send button never enables"), #1585 and #1594 ("assistant only echoes").
All three were FALSE. One instrument error caused them: the repro drove the
input with a synthetic `input.value = "..."` assignment plus a hand-dispatched
`InputEvent`.

A React **controlled** component ignores that. The DOM shows the text, component
state never updates, so `disabled={!text.trim()}` correctly stays `true`. Real
typing (`fill`/`type`/`pressSequentially`) enables the button every time.
A fourth, #1584 ("file attachment not implemented"), came from the same pass and
was equally false — upload returns 201 and the filepath reaches the outbound frame.

## The generalisation

The fidelity policy (`.agents/testing.md`) is written almost entirely about
**assertions** — the observable must be produced by the system. This class hides
on the other end: **the value that drove the conclusion was produced by the test,
not the system.** A synthetic event is a substitution of the *user*, and it
produces false NEGATIVES (invented defects) where output-side substitution
produces false POSITIVES (invented passes).

## What to do

- A "control never enables / never responds" finding is **suspect by default**.
  Before filing, re-drive it with real `fill`/`type` and say in the issue which
  method was used.
- Cross-check against the suite: if a merged green test already exercises the
  same flow (here `test_send_message_and_receive_response` did), the bug
  contradicts known-good evidence — resolve that contradiction before filing.
  The 2026-08-18 AFS actually noticed this and shipped `defect-found` anyway.
- Test-enforce the refutation rather than arguing it: ELITEA-2418 now hard-asserts
  `expect(send_button).to_be_enabled()` after real typing.

Related: [[support_assistant_campaign_1400]]
