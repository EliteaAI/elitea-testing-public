---
name: A transit substitution can silently CHANGE the observable — check the arrival path before filing a defect
description: Before classifying a case-step failure as a product defect, ask whether the test's own precondition manufactured the condition.
type: feedback
aliases: [wrong-interface precondition, manufactured defect, arrival path, navigate(-1), page.goto precondition, false sanctioned RED]
tags: [area/fidelity, type/analysis-discipline]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

`.agents/testing.md` § Fidelity policy splits substitutions into **transit** (allowed, declare it)
and **terminal** (forbidden). The split is usually read as being about *what you assert*. It is
also about *what the system can produce*: a substitution taken purely to "reach the step under
test" can be the direct cause of the step failing — and then it is terminal in effect while
looking transit on paper.

Worked case (ELITEA-2022, board card #2139, 2026-09-10): the case's Step 6 asserted an
auto-redirect after deleting a pipeline. The test seeded the pipeline via the API and reached the
detail page with `page.goto()`. The product's redirect is `navigate(-1)` — go back one *history*
entry. A `goto` leaves no history, so the redirect could not fire. A defect was filed (#1332),
the assertion was soft-tagged sanctioned RED, and the case was recorded as blocked — **for a
scenario the case never described.** Live on DEV: in-app arrival redirected 3/3, deep link
stranded 3/3. The bug is real, but it was not this case's.

## The check, before you classify anything as `defect-found`

1. Re-read the case for what it says about **how the user got there**. Absence of a navigation
   step between "Save" and the next action is itself a statement: the user is already there,
   in-app.
2. Ask: **would this still fail if I reached the step the way the case describes?** Run it. Two
   arrival paths is a five-minute probe.
3. Only if both paths fail is it the case's defect. If only your path fails, your precondition is
   the bug — file/keep the product issue on its own merits, and fix the precondition.

## Smells that this is happening

- The AFS justifies the substitution with "faster, equally valid way to reach the precondition"
  or "test isolation, not testing X" — plausible, and exactly the sentence that hides this.
- The defect's own repro steps have to *specify* the substituted precondition to reproduce.
- A whole spec is sanctioned RED for one step, and that step is about navigation/history/focus/
  session state — i.e. anything the arrival path can carry.

Related: [[verify_handles_against_main_not_working_tree]]
