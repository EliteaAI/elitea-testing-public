---
name: ask_user ClarifyingQuestionControl — question count AND content both vary run-to-run
description: Never hardcode a question count or an option label for ask_user's clarifying card — answer every question via free text, read the stepper first to learn the total
type: feedback
---

Live-confirmed 2026-10-17 (ELITEA-3369 implementation, 10+ live runs,
project 575, identical ambiguous message + identical Q1 answer every time):
the `ask_user` tool's `ClarifyingQuestionControl.jsx` card is non-deterministic
on TWO independent axes, both wider than ELITEA-3369's own analyst-time AFS
(3 runs) found:

1. **Question COUNT**: roughly HALF the runs resolve after a single
   question; the rest ask a second. The AFS's "deterministic 3/3" framing
   for its own exact message+answer combination did not survive a larger
   sample — it was a small-sample artifact, not a real invariant.
2. **Question/option CONTENT on a 2-question run** (new finding, not in
   the AFS): the second question itself is NOT fixed either. Observed:
   the "when to load" Always/When-relevant select (what the AFS specs),
   AND an unrelated "Activation"/"Setup Mode" question with 2-3
   differently-worded options (once including a free-text "Custom
   instruction" branch). An option LABEL that was "stable verbatim across
   3 runs" in one session is not safe to hardcode across more.

**Working pattern (confirmed, test green on both axes):**
- Read `clarifying_question_stepper`'s text BEFORE answering anything — the
  question SET (and so the stepper's "N/total") is fixed at the card's own
  render time (`ClarifyingQuestionControl.jsx`'s `specs` derives once from
  the `questions` prop), so this tells you the run's own total up front,
  race-free. Empty string = single-question run (no stepper renders at
  all when `total <= 1`).
- Loop that many times, answering EVERY question (first and any follow-up)
  via the card's own free-text input (`clarifying_question_custom_input`,
  `placeholder="Your option"`) — NEVER by clicking an option row. The
  component accepts free text as a valid answer to a select-type question
  too: `handleCustomChange` clears any radio selection and the typed text
  becomes the submitted value instead. This sidesteps axis 2 entirely
  without weakening the test (the card still has to be answered to
  completion; the submitted free text still has to show up in the created
  entity's content for the assertion to pass).
- `ChatPage.answer_clarifying_question(custom_text=...)` /
  `get_clarifying_question_stepper_text()` /
  `wait_for_clarifying_question_card[_closed]()` (added ELITEA-3369) already
  implement this loop-until-stepper-says-done pattern — reuse them on any
  future `ask_user` case rather than re-deriving.
- `CLARIFYING_QUESTION_OPTION_ROW` / `get_clarifying_question_option_row()`
  also exist (declared, resolves by exact option label) for a case that
  genuinely needs to exercise the option-select interaction itself — just
  don't rely on a SPECIFIC option label being present across runs.

See `test-specs/chat-interface/_surface.md` § Ask User clarifying-question
card and the ELITEA-3369 AFS's amended Blocked Steps section for the full
writeup.
