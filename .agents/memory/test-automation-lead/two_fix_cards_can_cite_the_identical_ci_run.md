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
