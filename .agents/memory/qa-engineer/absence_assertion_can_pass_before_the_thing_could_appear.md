---
name: An absence assertion can pass before the thing could have appeared
description: "\"No duplicate row / no second entry\" assertions are already-satisfied at evaluation time — without a refetch anchor they cannot fail."
type: feedback
aliases: [absence assertion, no duplicate row, to_have_count unchanged, negative assertion race, already-satisfied expect]
tags: [area/review, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

A case whose expected result is an ABSENCE ("no duplicate entry appears in the
table", "the item is not added", "the count is unchanged") is normally
implemented as `expect(rows).to_have_count(<the count captured a moment ago>)`.

That assertion is **already true when it is evaluated**, so Playwright's
auto-retry returns on the first poll. It therefore proves nothing about the
absence — it proves the UI has not *yet* changed. If the product regressed and
DID create the duplicate, the row would appear only after the list refetch
lands, i.e. possibly after the assertion already passed green.

Positive assertions do not have this shape: `to_have_count(N+1)` cannot pass
until the thing actually arrives, so the retry loop does the waiting for you.

## What to require in review

The absence step must be anchored to the event after which the absence is
meaningful — typically the product's own refetch:

- `page.expect_response(<list GET>)` around the action, then assert; or
- assert after an explicit reload / navigation that re-reads server state; or
- at minimum, order the step AFTER another assertion that provably waits
  (an error toast render, the driving response resolving) and say so.

Worked example: ELITEA-2309 (`test_users_invite_existing_member_error.py`,
settings-w09) — the duplicate-invite POST 400 and the error-toast assertion do
buy real time before the row-count step, so it is not a live flake, but the
"no duplicate" step itself has no refetch anchor and could not fail fast if the
product regressed.

Related: [[short_lived_toast_capture]]
