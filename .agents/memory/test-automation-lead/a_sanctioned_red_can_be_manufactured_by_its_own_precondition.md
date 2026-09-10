---
name: A sanctioned RED can be manufactured by its own precondition
description: Before accepting any sanctioned RED, ask whether the TMS case asks for the condition that makes it fail
type: feedback
aliases: [manufactured sanctioned red, sanctioned red validity, fake known defect, wrong-interface precondition]
tags: [area/merge-gate, area/fidelity, type/check]
created: 2026-09-10
updated: 2026-09-10
---

## The check

A sanctioned RED passes its own criteria — real linked defect, deterministic,
single-cause — and can still be **wrong**, because none of those criteria ask
*who created the failing condition*.

**Ask of every sanctioned RED: does the TMS case ask for the condition under
which this fails?** If the failing condition is something the TEST introduced
for convenience, the RED is manufactured: it is a wrong-interface precondition
under `.agents/testing.md` § Fidelity policy, and the disposition is to fix the
precondition, not to sanction the failure.

Conditions a test commonly invents:

| Test does | Case says |
|---|---|
| `page.goto()` to a detail page | user got there by clicking, in-app |
| API-seeds an object | user creates it through the UI |
| fresh browser context | a continued session |
| reuses `auth_state` | the case's subject IS login |

## Worked case — ELITEA-2022 / card #2139 (2026-09-10)

`test_delete_pipeline_via_ui_menu` was RED in CI for weeks as a declared
sanctioned RED against product bug #1332 (post-delete redirect `navigate(-1)`
no-ops on deep-link arrival). The defect is real and still open. But the case
has the user **create → save → delete without leaving the page**, and the
product redirect is *history-back* — so arrival path IS the observable's
producer, and the test's own `page.goto()` (empty history) manufactured the
failure. Measured on DEV: in-app 3/3 redirect, deep link 0/3.

Fix was the precondition, not the assertion: arrive in-app, assert the redirect
HARD. Green 3/3. #1332 stayed open with its coverage gap filed as #2162.

## Counter-example — ELITEA-1899 / card #2146 (2026-09-10): the sanction SURVIVES

The check is discriminating, not a one-way trigger. Do not read "API-seeded
object" off the table above and conclude *manufactured*.

`test_agent_icon_change_persists_on_list_card` is sanctioned RED on #2055 (agent
header `<img>` never updates in place after an icon pick) and **does** seed its
agent via `agent_api.create_agent_full()` — row 2 of the table, in form. It is
still a legitimate sanction:

- The case's precondition is only *"an existing agent is available"*; it does not
  require a pre-existing icon, and a UI-created agent has none either. Same
  pre-state, so the seed does not move the observable.
- Decisive: #2055 fails the same step on **both** pre-state branches (no icon →
  `<img>` absent; existing icon → present with a stale `src`). The precondition
  cannot select a branch that hides or manufactures the defect.

**The question that separates the two cases is not "did the test invent the
precondition" but "can the precondition change the observable".** In ELITEA-2022
it could — the product behaviour under test *was* history-back, so arrival path
was the producer. Here it cannot. Ask that second question before repairing a
precondition, or you will churn honest tests.

## Why it matters to the lead specifically

Two silent costs, both mine to catch:
1. A permanent false red that nobody re-examines — the artifacts all agree
   (case, AFS, test, gate), which is exactly the triangulation blind spot.
2. A recurring `[FIX]` intake card **every CI run**, forever.

The re-examination is cheap — read the case's step list and ask where the user
is standing. Do it whenever a `[FIX]` card lands on a test that is *already*
declared sanctioned RED; that shape is the trigger.

Related: [[a_fix_card_can_have_no_work_in_it]] · [[afs_gate_rulings]] · [[a_green_gate_does_not_prove_an_assertion_is_sound]]
