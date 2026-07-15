---
name: Reviewer full-recheck catches new findings on rework
description: A fresh reviewer re-reviewing a fix pass should re-run the FULL standing checklist, not just verify the named delta — round 2 can legitimately surface findings round 1 missed
type: feedback
---

## What happened (ELITEA-1954, issue #61, PR #513)

Round-1 fresh reviewer found 4 locator-policy violations in the page object
(raw role/listbox locators where a testid-based `select-option-*` alternative
already existed, plus a genuinely-missing testid on an accordion heading).
Implementer fixed exactly those 4.

Round-2 fresh reviewer was dispatched to verify the fix — but the dispatch
prompt explicitly said "also re-check the rest of the PR (don't rubber-stamp
just the delta)". It confirmed the 4 fixes were real, AND caught 2 new
Important findings the round-1 reviewer had missed entirely:

1. Raw `page.locator()` calls built **inside the spec file itself** (not the
   page object) — a testid-based selector constructed in the wrong layer is
   still a POM-discipline violation, and round-1's grep/attention was
   apparently scoped to the page object where the original 4 findings lived.
2. A console-error listener registered mid-test (Step 9) that silently
   missed steps 1-8, despite the AFS claiming the check ran "throughout."

Neither finding is a re-litigation of the same root cause as round 1 (so the
R2 cap rule doesn't apply here — these were each fixed once, not refought).
A third fresh reviewer then re-ran the full checklist again, found nothing
new, and approved.

## Why this matters

A reviewer dispatch that only asks "did the named fix land" will typically
get exactly that answer and stop looking — the fix pass itself is a new
diff, and touching a file to fix one thing is a normal moment to introduce
or overlook something adjacent. The round-1 reviewer's attention was
anchored on the locator layer (page object); it didn't notice the spec file
had its own instance of the same anti-pattern, or that the console-error
claim in the AFS wasn't actually being honored end-to-end.

## Rule going forward

Every re-review dispatch prompt (after any fix round) must explicitly
instruct the fresh reviewer to re-run the ENTIRE standing checklist, not
just confirm the named delta. Frame it as: "verify the fix is real AND
re-check the rest of the PR — don't rubber-stamp just the delta." This cost
one extra round here but caught 2 real findings that would otherwise have
merged silently.
