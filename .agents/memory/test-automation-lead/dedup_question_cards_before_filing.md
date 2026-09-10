---
name: Grep memory + open `question` cards BEFORE filing a process card — the gap you just found is probably already filed
description: Filing a systemic finding costs nothing to check first; #2157 re-raised #2135 from scratch because the recorded pattern was never read
type: feedback
aliases: [duplicate question card, process card already filed, before filing a question, re-raised the same gap, dedup question cards]
tags: [area/triage, type/convention]
created: 2026-09-10
updated: 2026-09-10
---

## What happened (#2122, ELITEA-1866)

Triaged a `[FIX]` card, found a real systemic gap — the failure-intake pipeline
files duplicate cards and never checks whether `automation/base` already carries
the repair — and filed it as `question` **#2157**, with options and a
recommendation.

It was already **#2135**, filed ~5 hours earlier, with a richer four-pair
occurrence tally. Worse: my own role memory
(`two_fix_cards_can_cite_the_identical_ci_run.md`) **names #2135 explicitly**.
The note was on disk the whole session. I never read it.

## Why this is easy to get wrong

A systemic finding *feels* like a discovery, and dispatch rule 7 says
"discoveries become new issues". Both are true — and neither licenses skipping
dedup. `.agents/profile.md` § Bug filing already rules it: **a real duplicate
found BEFORE filing means comment the new occurrence on the existing issue**, so
evidence consolidates instead of splitting. That rule is written for `bug`, and
it applies verbatim to `question`.

The tell: **if the finding is systemic, you are probably not the first to hit
it.** A one-off belongs to your card; a *pattern* has by definition recurred, so
someone before you was in this exact seat. Let that reasoning trigger the check
rather than the filing.

## The check — two commands, before you write any card body

```bash
# 1. your own memory first — cheapest, and it names the card number directly
grep -ril '<the pattern in your own words>' .agents/memory/test-automation-lead/
# 2. open process cards
env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public \
  --label question --state open --limit 100 --json number,title
```

Do (1) even when you think you remember the session. The `.agents/memory/<role>/`
vault is **not** the small index prepended at dispatch — that is a different,
host-level file. The 24 KB role index and ~200 entries are on disk and reach you
**only if you read or grep them**. Assuming they were injected is the whole bug.

## When you find the survivor

Do not quietly drop your finding — that is the failure mode dedup is not allowed
to have. **Consolidate:** comment your occurrence onto the survivor, keeping
whatever is genuinely new. On #2122 the new part was real and changed the
recommendation: the three cards cited **two different run ids**, so the survivor's
proposed `(run id, node id)` dedup key would have missed the pair that actually
cost the sessions — node id has to be the primary key. That belonged on #2135,
not on a second card nobody would read next to it.

If you already filed: label yours `duplicate`, comment "Duplicate of #M — why",
leave it **OPEN** (agents never close), move the evidence to the survivor, and
correct any closure record that cited the wrong number.

Related: [[two_fix_cards_can_cite_the_identical_ci_run]] · [[a_duplicate_card_is_where_you_pay_the_originals_evidence_gap]] · [[fix_card_may_already_be_fixed_by_a_sibling_pr]]
