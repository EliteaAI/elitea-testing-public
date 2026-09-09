---
name: A FIX card can have no work in it
description: A sanctioned-RED test failing in CI generates a [FIX] card whose only correct outcome is no code change — verify, don't fix
type: feedback
aliases: [sanctioned red fix card, null delta card, nothing to fix, CI red that is correct, expected red]
tags: [area/triage, type/convention]
created: 2026-09-09
updated: 2026-09-09
---

## The situation

The failure-intake pipeline files a `[FIX]` card for **every** CI failure, including
a test that is deliberately red to surface an open product defect. #2062
(ELITEA-2022, sanctioned RED on #1332) was one: the intake card's own body correctly
said *"the failure is expected behavior under the current defect state"* — and filed
it as To Fix anyway.

The only correct delivery is a **null code delta**. Changing the test to go green is
defect masking, which is forbidden. `.agents/testing.md` § Merge gate: *"staying red
in CI is the correct signal until the product fix ships."*

## What the card still owes — verification, not repair

Do not close it on the intake card's say-so; the card's prose is not the signature
(same lesson as #2053). Establish four things and paste the evidence:

1. **Root cause still unfixed** on the ref the env actually deploys — `git fetch
   origin` first, then read the source line. On #2062: `navigate(-1)` still in
   `DeleteApplicationButton.jsx:29` on `EliteaAI/EliteaUI@origin/main`.
2. **Deterministic** — 3/3 identical local reproductions, `--reruns 0`.
3. **Single-cause** — only the soft assertion fires, nothing else.
4. **Real coverage still enforced** — the spec's *hard* assertions still pass, so the
   defect is isolated and not masking the rest of the case.

Then: TMS back-write so the case stops claiming coverage it does not provide, closure
record, card → `Ready`. Issue stays OPEN; it unblocks when the product fix ships.

## The recurring cost is itself a finding

This card regenerates on every CI run while the defect is open, and each one costs a
full session to reach the same null result. Worse, it trains readers to skim `[FIX]`
cards — which is when a real regression gets missed. Filed as `question` #2064
(recommendation: a `@pytest.mark.known_defect` marker plus an intake filter).

Related: [[fix_card_may_already_be_fixed_by_a_sibling_pr]] · [[env_outage_page_is_a_fix_card_root_cause]] · [[sanctioned_red_tms_backwrite_shape]]
