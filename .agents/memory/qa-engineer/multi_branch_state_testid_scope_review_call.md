---
name: Multi-branch state-attribute testid — scope call for reviewers
description: N-branch (not just 2) conditional renders sharing ONE testid + varying data-* state — treat as one handle, not per-value "touches" scoping
type: feedback
---

Seen on ELITEA-2280 (`TokensTable.jsx`'s `ExpiryInDays`, 4 mutually-exclusive
`return` branches: `active`/`warning`/`never`/`expired`). The implementer
added the SAME `data-testid="token-expiration-status"` to all 4 branches'
outer `Box`, varying only `data-expiration-state`, per the project's
"testid = stable identity, state via `data-*`" ruling
(`.agents/testing.md`) — but this test's own steps only assert the `active`
state; the other 3 values are unexercised by this test's code path.

**Tension:** `.agents/role-overrides.md` § "touches" scoping (canon #511)
says a testid not invoked on the test's executed path is not "touched" —
normally grounds for `CHANGES_REQUESTED`. But #511/#277 were written about
*distinct elements/testids* (a sibling button, a same-element ternary
VALUE), not about attribute-VALUE variance on ONE static, always-present
testid across N mutually-exclusive branches of a single conceptual state
machine.

**Call made (non-blocking):** treated this as extending the existing
stable-identity/state-attribute pattern from its documented 2-branch example
to a 4-branch one, not as 4 independently-scoped testid requests — the
*testid itself* is genuinely touched (`get_row_expiration_status(row,
state="active")` resolves through it), only the attribute VALUE differs
across untested branches, which is closer to "data variance" than "untested
sibling element." The AFS declared this explicitly (Automation Hints
section) with citation to the ruling it extends — treat as a declared
improvisation (verify reasoning, don't block solely for the canon gap), and
recommend the PR description echo the same declaration next time (this one
only had it in the AFS, not the PR body).

**If this recurs:** if a future case's testid is on a container that has
MORE than 2 mutually-exclusive branches and the test only touches one
value, this call is the reviewer precedent — approve if (a) the testid
string itself is static/identical across all branches (not state-switched),
and (b) the AFS/PR explicitly declares the reasoning. Push back if the
testid VALUE itself differs per branch with no attribute doing the
disambiguation (that's the plain PR #581 anti-pattern, no ambiguity).
