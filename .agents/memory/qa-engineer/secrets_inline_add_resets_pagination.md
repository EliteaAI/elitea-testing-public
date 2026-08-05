---
name: Settings → Secrets inline "+" resets pagination to page 1
description: Clicking "+" on Settings → Secrets always jumps to page 1 and inserts the new row there, regardless of current page — case text said "current pagination position" (drift, filed #1202).
type: feedback
---

## What happened

ELITEA-2336 analysis (2026-08-05, localhost → DEV backend). The TMS case's
step 3 expected result claims the inline-create row "appears at the current
pagination position". Live behaviour is different: `SecretsContent.jsx`
`addSecretRow()` unconditionally calls `resetPaginationRef.current?.()` every
time "+" is clicked — confirmed live by navigating to page 2 first ("11 - 20
of 103"), then clicking "+": pagination snapped back to page 1 ("1 - 10 of
104") with the new row as the first entry.

## Why it matters

This is exactly the reverse-masking shape (case text stale, product
correct): the reset-to-page-1 behaviour is deliberate application code (not
a rendering glitch) and reads as intentional UX (new row should always be
immediately visible, never off-screen on another page). Classified as
`ready-for-automation` + filed a CLARIFICATION
(`EliteaAI/elitea-testing-public#1202`), not a defect. The AFS asserts the
actual behaviour (pagination resets to page 1, count includes the pending
unsaved row) rather than the case's literal wording.

## Reusable check

Any TMS case using vague pagination language ("current position", "same
page", "where you were") on a table with an add/insert action — don't trust
it; drive to page ≥2 first, then trigger the action, and observe where the
new row actually lands before writing the AFS's Test Steps.
