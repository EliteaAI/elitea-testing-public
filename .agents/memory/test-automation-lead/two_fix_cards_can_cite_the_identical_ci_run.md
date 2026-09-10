---
name: A FIX card is probably a duplicate — dedup on the TEST NODE ID before any git or gate work
description: Two gh calls settle it; the run id is NOT the key (cards for one drift can cite different runs), and a duplicate still owes independently re-derived evidence
type: feedback
aliases: [duplicate fix card, same run id, re-detection, intake refiled, sibling card same run, cross-run duplicate]
tags: [area/triage, type/convention]
created: 2026-09-09
updated: 2026-09-10
---

## The pattern

The failure-intake pipeline re-files `[FIX]` cards for a failure that is already
carded and often already fixed. Confirmed repeatedly: as of 2026-09-10, **8
sessions, zero code changed** (#2143 = ELITEA-1740, the **third** card off one run —
after #2074 which fixed it and #2116 which was already a duplicate). Running tally +
evidence lives on **#2135** (`question`, the process card) — add occurrences there, not here.

Two independent causes, both permanent until #2135 ships:

1. **Intake re-files** — the same run gets carded in multiple passes, and a
   workflow **re-run** cards again independently. **"Multiple" is unbounded, not two:**
   run `34331579791` was carded in **three** passes (09:32, 15:36, ~20:00), producing
   #2074 → #2116 → #2143 for one node id. Each pass **rewords the description**
   ("…skill 'skill-a-…'" → "…when filtering by tag"), so nothing in the title or body
   text is stable across passes — only the footer `Run ID:` and the node id are.
   *A third timing shape, from #2137:* the repair can be **on `main` already** and the
   card still lands, because the CI **run** predates it. Settle it with
   `git merge-base --is-ancestor <fix-sha> <ci-commit>` — one call, and it converts
   "is this fixed?" into a fact. On #2137: `NOT IN`, fix at 22:28, CI commit at 11:50.

2. **CI runs `main`; repairs land on `automation/base`.** `origin/main..origin/automation/base`
   is ~410 commits. Every merged-but-unpromoted repair re-cards on **every**
   subsequent nightly. Node-id dedup alone will not stop this half.

## Do this FIRST — before any git, gate, or dispatch work

```bash
# every card for this TMS id, any state — the key is the TEST/TMS id, NOT the run id
env -u GITHUB_TOKEN gh issue list --repo <repo> --state all --limit 400 \
  --json number,title,state --jq '.[]|select(.title|test("<TMS-ID>"))|"\(.number) [\(.state)] \(.title)"'
# then read the highest-numbered sibling's closure record
```

**The run id is not the key.** ELITEA-1866's three cards split across *two* run
ids (#2066 → `34325333015`; #2122/#2149 → `34331579791`), so a `(run id, node id)`
dedup would have missed the pair that actually cost the sessions. Key on the
node/TMS id.

**Read the body, never the title.** #2149 was titled "returns **non-empty**
result" while its own body reported `total:0/rows:[]` — intake's summary
inverted the finding. Triaging by title sends you after a phantom defect.

## Then locate the repair — the rung decides what the human must do

```bash
git log origin/main            --oneline -- <spec path>
git log origin/automation/base --oneline -- <spec path>   # a repair main lacks => card is stale
git merge-base --is-ancestor <repair-sha> origin/main && echo "ON MAIN" || echo "NOT on main"
env -u GITHUB_TOKEN gh pr list --repo <repo> --state open --base main --limit 30
```

Rung 2 = promotion PR open, awaiting a merge. Rung 3 = **nothing staged** — a
different report for the human. Never open the promotion PR yourself; promotion
is human-triggered (`.agents/workflow.md` § Promotion).

## A duplicate still owes independently re-derived evidence

Copying the sibling's closure record is the #35/#36/#37 failure mode. Re-derive:

- `git show origin/main:<spec>` — paste the pre-repair assert whose message is
  *verbatim* the CI failure string. One command, and it proves "unpromoted repair".
- Your own 3× gate on current `automation/base`.
- Fresh-fetch testid promotability — and **derive the testid set yourself**, one
  hop into each page-object method on the executed path. Sibling lists have been
  short three times running (8 listed vs 13 real; 11 vs 19).
- For a **templated** testid, grep the literal **prefix** the template
  contributes, never an instantiated value.

## Serialization drift: skip the matched control entirely

When the drift is a parse/format change, the real failure bytes settle it offline
in seconds — no browser, no revert-one-file control:

```bash
env -u GITHUB_TOKEN gh api repos/<repo>/actions/jobs/<job-id>/logs \
  --allow-escape-sequences > /tmp/job.log     # flag REQUIRED or gh errors out
grep -n "<assertion message>" /tmp/job.log
```

On #2122 this yielded `✅ list_files (0.388s) {   "total": 0,   "rows": [] }` —
tool ran, bucket *was* empty, only the serialization moved. Feeding that exact
string to the merged parser returned the expected dict. Root cause proven.

## Don't file what's already filed

The process observations these cards raise are already tracked: **#2135** (intake
double-filing + the `main`-vs-`base` check), #2064 (sanctioned-RED filed as
`[FIX]`), #2096 (card template's role/text-locator instruction inverting this
project's testid-only policy). Comment the occurrence on the existing card.

Related: [[dedup_question_cards_before_filing]] · [[fix_card_may_already_be_fixed_by_a_sibling_pr]] · [[a_duplicate_card_is_where_you_pay_the_originals_evidence_gap]] · [[a_fix_card_can_have_no_work_in_it]]
