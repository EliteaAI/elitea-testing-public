---
name: AFS can be the source of a locator violation
description: A raw non-testid locator can enter a PR because the AFS's own "Concrete Handles" table specced it as the recommended handle, not because the implementer improvised — check the AFS's handle table itself as an item-1 artifact, not just the final diff, and don't assume "reviewer approved, testid scoping clean" means the mechanical grep was actually run against page-object diff lines
type: feedback
---

## What happened

Control audit of issue #133 (ELITEA-1887, PR #601) — the first FAIL I've
issued after a long PASS streak. Re-running the item-1 locator grep on the
merge-commit diff found a genuine hit: a new `AgentDetailPage` method,
`get_agent_picker_menuitem()`, returns
`popper.get_by_role("menuitem", name=agent_name, exact=True)` — a raw
role+accessible-name locator, no `data-testid`, no UPPER_CASE class
constant.

This was not implementer freelancing. Tracing it back, the **analyst's own
AFS** (`test-specs/agents/l2_agent-cannot-be-added-to-own-toolkit-picker_ELITEA-1887.md`
§ Concrete Handles) specced this exact `get_by_role` call as the
"Recommended Locator" for the picker's menu item, reasoning "no per-item
testid... same established pattern as `components.mui.Popper.select_menuitem`."
Per `.agents/role-overrides.md` § Analyst slot, that's backwards: an element
without a testid should be specced as `testid needed: {section}-{element}-{type}`,
never a role/CSS handle as primary — and "the surrounding code is NOT
precedent" applies exactly as much to an analyst citing an existing shared
helper as to an implementer doing so. The implementer then correctly
followed the AFS's own work order, and the reviewer's round-2 APPROVED
verdict explicitly said "testid scoping clean" — missing the violation
entirely (or not applying the mechanical grep carefully to new page-object
methods).

It also didn't qualify as a declared improvisation (which would have
prevented a solo-FAIL): the protocol requires declaration "in the Run
Report and the PR description," and PR #601 has none — the only reasoning
lived in the method's docstring, which isn't the declared channel.

## Why it matters

Every prior audit (mine and this project's) implicitly treated item 1's
grep as sufficient once run against the diff — assuming any violation
would be an implementer-introduced deviation from a compliant AFS. This
case shows the AFS itself can be the origin of the violation, and once
it's in the AFS, it looks "sanctioned" all the way down the pipeline:
implementer compliance reads as correct, and a reviewer skimming for
implementer-introduced handles may not think to re-check the AFS's own
handle table against the same rule.

## Rule going forward

- When auditing item 1, if a raw-locator grep hit shows up, don't stop at
  "implementer violation" — check whether the AFS's own Concrete Handles /
  Automation Hints section specced that exact locator. If it did, the
  finding traces to the analyst slot, and the audit language should say so
  (it changes where the fix needs to land — the AFS needs amending, not
  just the page-object method).
- When dispatching an analyst (orchestrator side), the AFS quality gate
  should itself reject a Concrete Handles row that recommends a
  role/text/CSS locator as primary for any NEW element the case's test
  touches — this is exactly as much a gate failure as an implementer
  shipping the same thing later.
- Don't take "reviewer said testid scoping clean" as proof the mechanical
  grep actually ran cleanly against page-object diff lines — the audit's
  own re-run grep is the only reliable check (this is the same evidence
  principle already established for merge-gate/promotability rows, now
  confirmed to also apply to the reviewer's substantive locator finding).
