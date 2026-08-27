---
name: A docs-only fix is not done until the runtime message literals agree
description: Correcting docstrings while leaving assert/pytest.fail message strings stale ships a file that contradicts itself at the worst possible moment.
type: feedback
aliases: [pytest.fail message stale, assertion message documentation, docs-only change, gate owner reads the failure message]
tags: [area/review, type/docs]
created: 2026-08-27
updated: 2026-08-27
---

## The catch

On PR #1844 (ELITEA-2215) I corrected a module docstring and a gate marker to
say the known defect was NOT sanctioned on this trigger. The reviewer blocked
it: both `pytest.fail(...)` message literals still read *"Non-deterministic
known defect observed this run (see module docstring 'Fix round 1' note)"*.

That string is what a gate owner reads **at the exact moment the test goes
red** — i.e. precisely when the corrected `GATE_EXCLUDED_REASON` is telling
them "NOT sanctioned, treat it as a blocker". The file contradicted itself,
and the contradiction was visible only at failure time, where it does the most
damage.

## The rule

Message literals inside `assert`, `pytest.fail`, `raise`, and log calls are
**documentation that executes**. They are the last documentation a human reads
and the first they believe. A "docs-only" change is not scoped to docstrings:

- Grep the whole file for the claim you are correcting, not just the prose:
  `grep -n "<the stale phrase>" <file>` — docstrings, comments, AND string
  literals.
- Also grep for the stale *number* (`7/7`, `2/5`) — mine appeared in five
  places across two classes.
- A pointer inside a message (`"see 'Fix round 1' note"`) rots the moment a
  later round supersedes that section. Point at the current section.

## The companion technique

Changing message literals means "no behavioural change" is no longer provable
by eyeballing the diff. Prove it mechanically — parse both versions, strip
docstrings, dump the AST, diff:

```
ast.parse -> walk -> drop body[0] where it is a str Constant Expr -> ast.dump
```

On #1844 this returned exactly 3 differing nodes, all `Constant` string values,
zero structural change — which is a far stronger claim than "the diff looks
like docs to me", and it is what the reviewer used to clear the direction.

Related: [[aggregate_flake_rate_can_hide_deterministic_populations]]
