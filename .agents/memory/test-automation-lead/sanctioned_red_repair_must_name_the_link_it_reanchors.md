---
name: A sanctioned-RED repair that re-anchors an assertion drops a cross-check that never comes back
description: Soft-demote + transit + re-anchor is the standard repair shape, and its re-anchoring step silently deletes coverage the defect fix does NOT restore — name the link in the dispatch
type: feedback
aliases: [sanctioned red repair shape, re-anchor assertion, transit reload, soft demote, coverage loss in a repair, repair dispatch checklist]
tags: [area/orchestration, area/gating, type/trap]
created: 2026-09-09
updated: 2026-09-09
---

## The shape and its hidden cost

The standard repair for a case blocked by an isolated product defect is three
moves at once:

1. **soft-demote** the assertions the defect breaks (`# Known defect: #N`),
2. add a **declared transit** step to get past the defect (a reload, a refetch),
3. **re-anchor** the downstream assertions onto the value that transit produced.

Steps 1 and 2 are self-reversing — they flip green when the product is fixed.
**Step 3 is not.** Re-anchoring silently deletes whatever the *old* anchor was
proving, and the defect fix does not bring it back.

## The worked case (ELITEA-1899 / #2051, 2026-09-09)

Pre-repair: `card_src == new_src`, where `new_src` was the **immediately
rendered header** — one line proving *the icon the header shows at once is the
icon that reaches the list card*.

Post-repair: `card_src == persisted_src` (the post-reload value). `immediate_src`
was now compared to nothing but "non-empty and changed". So this passes:

> the optimistic patch renders icon **0** in the header while the PUT persisted
> icon **3** — soft check passes, transit check passes, card check passes. **Green
> on a real bug**, forever, in the exact defect class the card was about.

The reviewer caught it; neither the implementer nor I did. Fix was four lines —
the old link restored as a **hard assert guarded on the demoted value**
(`if immediate_src:`), unreachable during the defect window so it cannot pollute
the single-cause signature, and a raw red the moment the product misbehaves.

## Two rules this gives

**Dispatching a repair:** ask explicitly, *"what was the old anchor proving, and
what proves it now?"* Put the question in the implementer's prompt. It is invisible
from the diff — every individual assertion still looks strong.

**Reviewing one:** enumerate the OLD hard assertions from `origin/main` and tick
each off against the new file. `git show origin/main:<path> | grep -nE '^\s+assert '`
is the whole technique. Counting (9 in / 9 out) catches what reading cannot.

**Guarded asserts:** a guarded hard assert is safe only when the guard's FALSE
branch is provably covered by the soft assertion it pairs with — the two must be
total over the guard value. Otherwise it is a bypass wearing a guard's clothes.
State the totality argument so a reviewer can check it rather than infer it.

And: a guard makes it easy for an aggregated failure MESSAGE to over-claim, because
the skip is invisible where you write the summary sentence. That message is what a
human triages from — it carries the same honesty bar as an assertion.

Related: [[sanctioned_red_closed_set_variant]] · [[sanctioned_red_is_never_back_written_automated]] · [[a_green_gate_does_not_prove_an_assertion_is_sound]]
