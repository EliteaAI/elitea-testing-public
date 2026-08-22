---
name: Synthetic typing on a React controlled input fabricates a "button never enables" bug
description: JS value-assignment + hand-dispatched InputEvent leaves React state unchanged — the guarded button stays disabled and looks like a product defect
type: feedback
aliases: [false disabled button, synthetic typing, InputEvent dispatch, controlled textarea, ELITEA-2418 send button, issue 1581]
tags: [area/support-assistant, type/anti-pattern, type/quirk]
created: 2026-08-22
updated: 2026-08-22
---

## What happened

ELITEA-2418 (Support Assistant "empty message cannot be sent") was first analysed as
`defect-found` and produced bug **#1581** — "Send button never enables when typing actual text".
It does not reproduce. The analyst had typed by assigning `input.value` and dispatching a
hand-made `InputEvent` via `page.evaluate`. A React **controlled** `<textarea value={text}
onChange=…>` ignores that: the DOM shows the text, `text` state never changes, and any
`disabled={!text.trim()}` guard stays true. The AFS even flagged the contradiction (an existing
smoke test sends messages fine) and shipped `defect-found` anyway.

## The rule

**Type for real, always** — `Locator.fill()`, `Locator.type()`, `pressSequentially()`. If a
control's enabled-state is the observable and it "never flips", the FIRST hypothesis is your
input method, not the product — check `input_value()` AND the component's guard in source
before writing the word "defect".

Corollary from `.agents/testing.md` § Fidelity policy: synthetic event dispatch is a
**substitution**, and here it substituted the very thing the case came to observe. It produced a
false bug that then justified a soft-assert + sanctioned-RED plan for a fully green case.

## Verified contract (Support Assistant, 2026-08-22)

`../elitea_assistant/src/components/chat/MessageInput.tsx:105-131` — `isSendDisabled =
!text.trim() || disabled || isUploading || !attachmentsValid`; Enter (no Shift) calls the same
`handleSend`, which early-returns on empty trim. Live: empty/`" "`/`"   "` → disabled and zero
POSTs on Enter; `"Hello"` and `"  hi  "` → enabled (the `disabled` attribute is removed).

Related: [[support_assistant_launcher_click_quirk]] · [[support_assistant_response_latency_and_no_streaming]]
