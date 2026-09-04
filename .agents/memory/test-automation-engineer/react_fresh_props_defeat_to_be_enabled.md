---
name: to_be_enabled() cannot close a React handler-side gate
description: React delivers a synthetic handler from CURRENT fiber props, so a click the DOM permitted can still early-return — a pre-click state assertion narrows the window, never closes it.
type: feedback
aliases: [send button no-op, disabledSend, silent click, to_be_enabled insufficient, fiber props]
tags: [area/chat, type/race]
created: 2026-09-04
updated: 2026-09-04
---

## Mechanism (ELITEA-1886 / issue #1812 / product bug #2011)

A control gated twice — once in the DOM, once inside its own handler — cannot be
made safe by a pre-click assertion:

- DOM: `disabled={disabledSend || !question}` (`SendButton.jsx:79`)
- handler: `if (question.trim() && !disabledSend)` (`UserInput.jsx:238`)

React delivers the synthetic handler from the **current fiber props**, not from
the render the browser gated on. A commit landing between the browser
dispatching the click and React delivering it hands the handler a *fresher*
`disabledSend` — now `true` — and it early-returns: **no exception, no console
error, no request, no DOM change.** (Note the direction: it is a fresher value,
not a stale closure. The stale-closure story is the intuitive one and it is
wrong; saying it publicly cost a correction.)

Here `disabledSend` is `ChatBox.jsx:2747`'s **nine-term** `isInputDisabled`
disjunction, several terms network-bound (`isLoadingConversation`,
`isFetchingParticipant`, `isUploadingAttachments`,
`activeConversation?.isSending`, ...) — which is why the window is wide on a
deployed env and effectively absent on localhost (button goes
`absent -> enabled`, no observable DISABLED state at 5 ms sampling).

## What follows

1. `expect(btn).to_be_enabled()` **narrows** the window; it cannot close it. Do
   not report it as a fix.
2. The robust shape is a **bounded retry of the action**, keyed on a signal that
   proves whether the action took effect — same family as the canon-prescribed
   "bounded retry of the trigger message" for the HITL trigger-side flake
   (`.agents/testing.md` § Known issues).
3. **A local green proves non-regression only** for this whole class. The race
   does not exist on localhost. Never present N× local green as evidence the fix
   works.
4. Distinguishing an actionability block from a handler no-op is free: an
   actionability failure raises at the **context default** (`conftest.py`, 10 s)
   naming the *element*; a handler no-op raises at your own **response/event**
   timeout naming the *event*. Read which one fired before theorising.

## How to prove a retry is not masking

Force each branch deterministically and run it — the local green run cannot do
this for you:

- action suppressed on attempt 0 -> expect RETRY, test passes, run time up by
  ~one timeout;
- effect provably happened but the oracle misses it -> expect **immediate**
  re-raise (one timeout, not N);
- the "it happened" DOM signal present -> expect **immediate** re-raise.

Then revert the instrumentation and `diff` against a pristine copy saved to
`/tmp` before you started. Worth more than another green run.

Related: [[chatbox_composer_clear_is_a_lagging_signal]], [[chat_send_button_force_click_race]]
