---
name: Make the analyst disprove the convenient answer
description: A hypothesis that explains the evidence is not a root cause — ask what symptom the rival cause would have produced instead
type: feedback
aliases: [root cause, disproof, convenient answer, hypothesis, ELITEA-0143, toolkit not available]
tags: [area/analysis, type/process]
created: 2026-08-27
updated: 2026-08-27
---

## The move that worked

#1814 (ELITEA-0143) arrived with a confident card: agent reports "no GitHub toolkit tool available",
`GIT_HUB_TOKEN` is known-expired (#1673) → obviously the credential. Two further plausible causes
appeared during analysis. **All three were false**, and each was killed by the same question:

> *What symptom would this cause actually produce — and is that the symptom we have?*

| Candidate | Killed by |
|---|---|
| Toolkit registers zero tools (fixture omits `selected_tools`) | The product's own tool chip renders on a local run. The cited ELITEA-2010 finding is scoped to the *pipeline Toolkit node dropdown*, not agent runtime. |
| Expired credential | Produces `401 Bad credentials` *after* the tool is called — a different sentence entirely. And CI's token was valid. |
| Wrong agent added as participant | Real, reproducible defect (→ #1855) — but a wrongly-picked agent sorts earlier *because its name differs*, so the composer chip would have shown that other name. It showed the right one. |

The third is the instructive one: it was **verified live as a genuine bug** and still was not *this*
bug. "I reproduced a defect" and "I found the root cause" are different claims.

## How to get this from a dispatch

- State rival hypotheses explicitly and say **"do not assume either; consider that neither may be it."**
- Ask for **the symptom each cause produces**, not just whether the cause exists.
- Say plainly that the negative result is as valuable as the positive: *"if the opposite is true I want
  it stated just as plainly, because it sends the cause back to open."* Both analysts on #1814 volunteered
  the caveat that killed their own finding — because they were told that was a wanted outcome.
- Then **accept "undetermined"** when that is the honest answer. Parking on a named blocker beats
  shipping a fix aimed at a disproved cause.

## It generalizes past the first blocker

Same case, resumed 2026-08-28: a 4th candidate (per-project model/guardrails/stale-agent state) was
cleared the same way — live-checked against a real project — only to discover the checks had run
against the WRONG project (CI uses per-executor masked secrets `.env.test` doesn't have). Clearing a
hypothesis against the wrong target is not clearing it at all; verify you're even looking at the thing
that produced the original evidence before trusting a clean result.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]] · [[dev_only_red_check_the_screenshot_first]] · [[human_status_move_without_comment_verify_dont_guess]]
