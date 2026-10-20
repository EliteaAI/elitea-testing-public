---
name: Chat Ask User module toggle silent degradation
description: ask_user module toggle is per-conversation OFF by default; omitting it silently degrades to a plain-text follow-up instead of failing visibly.
type: feedback
---

## Finding (ELITEA-3369, 2026-10-17)

The `ask_user` Chat Modules toggle (`modules-toggle-ask_user`) is OFF by
default on EVERY new conversation, same per-conversation mechanism already
documented for `project_context_builder`/other module keys
(`GET /api/v2/social/module_settings/{project_id}` →
`default_ask_user_enabled: false`).

**The dangerous part: omitting it does NOT fail visibly.** When a case
expects the structured `ClarifyingQuestionControl` HITL card (stepper,
option rows, custom-text input, "Ask User: ask_user" tool chip) but
`ask_user` is left disabled, the assistant silently falls back to asking a
plain follow-up question as ordinary chat TEXT — no tool chip, no card, no
stepper, nothing a `wait_for(state="visible")` on the card's own elements
will ever catch except a timeout. If a case/module combo involves BOTH
`project_context_builder` (or any other tool-invoking module) AND
`ask_user`, enable BOTH explicitly via
`ChatPage.ensure_module_toggle_checked(key)` before sending the triggering
message — the existing (toast-less) method works unchanged for `ask_user`
too.

## ClarifyingQuestionControl card itself (zero testids)

- Whole card: plain `<Box>`, no testid/role/aria-label anywhere. Detect via
  its custom-text input's `placeholder="Your option"` (no `aria-label`/
  `<label>` either — `get_by_label` returns 0 matches; use a `css=`
  attribute selector).
- Stepper (`"N/M"`) only renders when the live question set has >1 entry —
  don't assert its presence as an invariant; a single-question run (observed
  when the Q1 answer itself resolves enough) shows none.
- Submit button's ACCESSIBLE NAME toggles `"Skip"` ⇄ `"Continue"` based on
  whether the current question is answered — no state attribute, name is the
  only differentiator (genuine state-dependent-name case, flagged as a
  `question`, not a locator violation with a cleaner alternative available).
- Selecting an option auto-advances the stepper UNLESS it's the LAST
  question — on the last question, Continue must still be clicked manually
  (`handleSelectSingle`'s auto-advance is `if (!isLastStep)` only). A test
  that assumes the last click submits will hang.
- Question COUNT for a given ambiguous prompt is NOT a fixed invariant — a
  fuller first-answer can resolve the whole tool call in one question
  instead of two. Scope any question-count assertion to the specific test's
  own reproducible answer sequence, not to the tool in general.

Full AFS: `test-specs/chat-interface/l1_project-context-ambiguous-request-ask-user-clarification_ELITEA-3369.md`.
Digest: `test-specs/chat-interface/_surface.md` § Ask User clarifying-question card.
