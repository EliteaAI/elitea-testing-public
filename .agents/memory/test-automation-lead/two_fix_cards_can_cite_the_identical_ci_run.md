---
name: Two FIX cards can cite the IDENTICAL CI run id — dedup on (run id, node id) first
description: The failure-intake pipeline re-filed run 34331579791 twice for one test (#2081 and #2113); the cheapest first triage command is a grep of sibling card bodies for this card's own run id, before any git or gate work
type: feedback
aliases: [duplicate fix card, same run id, re-detection, intake refiled, sibling card same run]
tags: [area/triage, type/convention]
created: 2026-09-09
updated: 2026-09-09
---

## What happened (#2113, ELITEA-1899)

ELITEA-1899 produced **four** `[FIX]` cards: #2043 (Promoted), #2051 (Ready — the
card that actually produced the repair), #2081 (Ready, `duplicate`) and #2113
(Ready, `duplicate`).

The part that was new: **#2081 and #2113 cite the SAME CI run id
(`34331579791`) and the same test node id.** This is not the familiar
"a later nightly re-detected an unpromoted fix" case — the intake pipeline
filed one run twice. #2081 had already been fully worked, closure-recorded and
labelled `duplicate` about 4.5 hours before #2113 was dispatched.

## The check that would have front-run everything

Existing notes cover *related* traps — `a_fix_card_can_have_no_work_in_it.md`
(sanctioned-RED cards), `fix_card_may_already_be_fixed_by_a_sibling_pr.md`
(sha-vs-fix + matched control). Both are more expensive than this one. Do this
one FIRST:

```bash
# 1. this card's run id
env -u GITHUB_TOKEN gh issue view <N> --repo <repo> --json body \
  --jq '.body|capture("Run ID: (?<r>[0-9]+)").r'
# 2. every other card citing the same run id (and/or the same TMS id)
env -u GITHUB_TOKEN gh issue list --repo <repo> --state all --limit 400 \
  --json number,title,state --jq '.[]|select(.title|test("<TMS-ID>"))|"\(.number) [\(.state)] \(.title)"'
# 3. read the highest-numbered sibling's closure record BEFORE any git work
```

Two `gh` calls. If a sibling with the same run id is already `Ready`, the
correct outcome is almost certainly `duplicate` + a re-verification, not a repair.

## What "duplicate" still owes you — do NOT rubber-stamp

`.agents/workflow.md`'s closure-record rule ("verified facts, never a copy")
applies in full to a duplicate. Copying the sibling's conclusion is exactly the
#35/#36/#37 failure mode. What I re-derived independently, none of it from #2081:

- `git show origin/main:<spec>` — pasted the pre-repair hard assert whose
  message is *verbatim* the CI failure string. That single command proves
  "unpromoted repair", and is stronger than any amount of prose.
- Promotion PR still OPEN (`gh pr view`, `updatedAt` unchanged) and the linked
  product defect still OPEN.
- My own 3× re-certification gate on current `automation/base` + a 4th run on
  the card's mandated env (DEV). 4/4 byte-identical ⇒ the sanctioned-RED
  signature has not rotted since the sibling certified it.
- Fresh-fetch testid promotability, pasted.

That is ~5 minutes and it converts "presumably still true" into "verified today".

## Second lesson — grep the PREFIX of a runtime-composed testid

#2081's promotability block had to print `agent-icon-picker-option-3 main:no
testids:no` and then explain it away in prose as a stage-1 bare-substring blind
spot (the page object holds the template `[data-testid="agent-icon-picker-option-{}"]`;
the UI composes the index at runtime). Querying the **static prefix**
`agent-icon-picker-option` instead returns a clean `YES/YES` with no caveat.
Generalises `dynamic_testid_promotability_grep.md`: for any templated testid,
grep the literal prefix the template contributes, never an instantiated value —
a row that needs a paragraph of exculpation is a row a reader will misread.

## Don't file what's already filed

Both process observations this card raised were already tracked: #2064 (intake
files sanctioned-RED tests as `[FIX]` cards) and #2096 (the card template's
"use role/text locators" instruction inverting this project's testid-only
policy). Per `.agents/profile.md` § Bug filing, a real duplicate found BEFORE
filing means **comment the new occurrence on the existing issue**, not a new
card. Added the four-card tally + the same-run-id evidence to #2064 instead.

## Confirmed systemic — it happened again the same day, on a DIFFERENT case (#2114)

Run `34331579791` was also filed **twice for ELITEA-2448**: #2076 (the card that
produced the real repair, closure-recorded 11:45Z) and **#2114** (dispatched
18:47Z, `duplicate`, zero code changed). So one run id produced duplicate pairs
for **two unrelated tests** — the double-filing is a property of the RUN, not of
any one test or of sanctioned-RED status. Treat a `[FIX]` card citing a run id a
sibling already cites as a duplicate until proven otherwise.

This note front-ran the whole of #2114: two `gh` calls before any git or gate
work. It is the cheapest triage in the file — keep it first.

## The variant that is WORSE than #2081's — check where the repair is staged

#2081's repair had an OPEN promotion PR (#2056) merely awaiting a human merge.
#2114's had **nothing staged at all**. Distinguish them explicitly, because the
report a human needs is different (merge the PR vs. promote from scratch):

```bash
git merge-base --is-ancestor <repair-sha> origin/main && echo "ON MAIN" || echo "NOT on main"
git branch -r --contains <repair-sha>          # base + unrelated siblings only == nothing staged
env -u GITHUB_TOKEN gh pr list --repo <repo> --state open --base main --limit 30   --json number,title,headRefName
```

On #2114 the repair had merged to `automation/base` **seven hours** before the
duplicate card was dispatched, and would have re-filed again on the next
nightly. Do NOT open the promotion PR to stop the loop — promotion is
human-triggered only (`.agents/workflow.md` § Promotion). Report it and name the
human as owner.

## Derive the testid set yourself — the sibling's list is usually short

#2076's closure record listed 11 testids. Resolving the 20 page-object methods
the spec actually calls, one hop into the page object, produced **19**. Copying
the sibling would have shipped an under-specified promotability row — the
#35/#36/#37 failure mode wearing a different hat.

## Occurrence log — this is now a PATTERN, not an incident (updated 2026-09-09 evening)

Run `34331579791` was carded in **two full passes**: 09:32–09:42 (#2074–#2084) and
15:36–15:48 (#2111–#2123). Confirmed duplicate pairs worked so far:

| Case | survivor | duplicate | code changed by the duplicate |
|---|---|---|---|
| ELITEA-1899 | #2051 | #2081, #2113 | none |
| ELITEA-2448 | #2076 | #2114 | none |
| ELITEA-2367 | #2079 | **#2115** | none |
| ELITEA-1740 | #2074 | #2116 | none |

**Five sessions, zero code** (all four pairs now worked; #2116 closed out 2026-09-09 evening). Now carded as a process defect: **#2135** (`question`) —
recommends dedup on *test node id* plus a `main`-vs-`automation/base` divergence check
at intake, because the second half of this loop is permanent: the nightly runs `main`,
`automation/base` is 399 commits ahead, so every merged-but-unpromoted repair re-cards
on EVERY subsequent nightly, not just on a double-filed one.

Second-order lesson: a duplicate session is not wasted budget — see
`a_duplicate_card_is_where_you_pay_the_originals_evidence_gap.md`.

## All four pairs now worked — the tally is closed (2026-09-09 late)

#2116 (ELITEA-1740) was the last unworked duplicate and confirmed the pattern
without deviation: same run id, same node id, same assertion, **zero code**.

The half of this that a node-id dedup would NOT fix, measured on #2116:
`47e8a475b` (the repair, PR #2088) is **not** an ancestor of `origin/main`,
`origin/main..origin/automation/base` = **400**, and no open PR targets `main`
with it — escalation rung **3 (nothing staged)**. The nightly runs `main`, so
this card re-files on every subsequent nightly regardless of double-filing.
Both halves of #2135 are load-bearing; shipping only the cheap dedup half
suppresses the twin but not the recurrence.

Reinforced on #2116: **derive the testid set yourself.** #2074's record listed 8;
resolving all 17 page-object methods the spec calls across three page objects
gave **13** on the executed path. The sibling's list was short by 5 second-hop
handles — the third time in this note's history that copying would have shipped
an under-specified promotability row.
