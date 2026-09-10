---
name: A near-perfect precedent makes a WRONG root cause feel settled — dispatch it as a hypothesis
description: My #1897-based triage of #2123 was confidently wrong; the analyst refuted it because the dispatch said "confirm or refute", not "implement this"
type: feedback
aliases: [precedent trap, wrong root cause, sibling test precedent, confirm or refute, analyst refuted the lead, triage hypothesis, dispatch framing]
tags: [area/triage, area/orchestration, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## What happened

On #2123 I found what looked like a decisive precedent: the **sibling test in the
same file** (`test_create_credential`) had been repaired by `6566b9968` for an
apparently identical CI signature, and its commit message named the cause —
*"a JS `evaluate('el => el.click()')` on a DISABLED Save is a silent no-op"*.
`test_create_toolkit` still had both defects verbatim: the `evaluate` click and a
vacuous `not in page.url` guard. The failure screenshots showed a greyed Save.

Everything fit. **It was wrong.** The real cause was a 3-second fixed budget for the
create POST (see [[identical_step_duration_across_pass_and_fail_is_a_fixed_budget]]);
the click fired fine and the toolkit was created.

## Why the precedent was seductive — and how it was broken

Same file, same author, same test family, same assertion shape, same screenshot
symptom. Five matching signals, one wrong conclusion.

The analyst broke it with an observation I had looked straight at and not read:
**Save AND Cancel were BOTH greyed.** Cancel is disabled by `isLoading` alone, so
the pair can only mean *a mutation is pending* — never *validation failed*. A single
greyed button is ambiguous; **the button PAIR is the discriminator.**

## The rule

**Precedent is authority on CONVENTION, never on DIAGNOSIS** — the generalisation of
`.agents/role-overrides.md` § "precedent is not authority". A matching prior incident
raises a hypothesis; only fresh evidence closes one.

So write the dispatch to be falsifiable:

- State the hypothesis, then say **"confirm or refute against the source; do not
  assert it on the strength of my observation"** — that exact framing is what let the
  analyst overturn it instead of building my error.
- Quote the **observation** and label the **inference** separately.
- Never phrase triage as a work order (*"apply the #1897 fix"*). Per the orchestrator
  slot rule, my dispatch prompt is the strongest signal in the pipeline: an IC treats
  it as settled and the reviewer then judges work **I** ordered — which removes the
  last independent axis.

Cost of being wrong this way: **zero**, because the framing held. Cost if I had
ordered the fix: a repair that makes the real failure *more* invisible, shipped past
three gates that all agreed with me.

Related: [[sibling_fix_cards_do_not_share_a_root_cause]] · [[identical_step_duration_across_pass_and_fail_is_a_fixed_budget]] · [[two_fix_cards_can_cite_the_identical_ci_run]]
