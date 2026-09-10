---
name: Reviewing a REMOVED wait — the question is the caller's read, not the missing wait
description: how to judge a "#1847 settle removed, nothing added" diff statically: retrying read + monotone convergence + fail-loud, in that order
type: feedback
aliases: [removed settle review, no replacement wait, "#1847 review", vacuous settle review, transient count satisfaction]
tags: [area/waits, area/review, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The reflex to resist

A diff that DELETES a wait and adds none reads as a weakening, and the reflex is to
demand a replacement. That reflex is wrong when the deleted wait was **vacuous** — and
"is there still a wait?" is the wrong question. Ask three, in order, and all three are
answerable statically:

1. **Is the caller's next read auto-retrying?** `expect(loc).to_have_count(n, timeout=)`
   yes; `locator.count()`, `text_content()`, `input_value()`, `is_visible()` no
   (`is_visible(timeout=)` is deprecated AND ignored — it never retries).
2. **Is the retrying wait TERMINAL, not just satisfiable?** A wait that the state can
   pass THROUGH and leave is a race even though it retries. The check is convergence:
   if the observable grows **monotonically** from a subset toward the asserted value and
   stops there, count-equality implies set-equality and the wait is terminal. If it can
   overshoot or oscillate, it is not.
3. **If the wait is wrong, does it fail LOUD?** A racy read that ends in a strict
   equality assertion (`restored == baseline`) produces a red, not a silent green. That
   is acceptable residual risk. A racy read feeding a weak/absence assertion is not —
   `to_have_count(0)` is satisfied by a not-yet-rendered container.

## Where the vacuity claim can be verified WITHOUT executing

A settle's vacuity is usually structural, so do not take the measurement on trust —
re-derive it from the locator. `#2168`: `SEARCH_RESULTS_SETTLED`'s
`[data-testid^="catalog-agent-card-"]` branch is matched by the **pre-clear filtered**
cards, which are the same kind of element, so after a clear it has nothing to wait for.
That reading needs one grep of the class constant, not a browser — and it is stronger
evidence than the implementer's 4.72 ms datapoint, because it says *why*.

The generalisation: **a terminal-render settle is direction-specific.** Valid for
A -> B, vacuous for B -> A when B's DOM already matches it.

## The doc-edit half of such a review

A wait-removal PR ships its justification as prose in a docstring / `_surface.md` / AFS.
Those are review surface, not decoration: check each measured claim is at least
internally consistent, and that the digest bullet the change **falsifies** was actually
rewritten (a stale "still carries the settle — left as a follow-up" bullet left behind is
a finding).

Related: [[a_positive_assertion_guarding_an_absence_only_by_ordering_is_fragile]]
