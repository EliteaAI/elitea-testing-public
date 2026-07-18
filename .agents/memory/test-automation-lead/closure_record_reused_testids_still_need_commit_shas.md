---
name: Reused-testid closure records still need per-testid commit SHAs
description: "no new testid, reused from a prior case" is not an exemption from item 4's clickable-commit-link requirement — cite the ORIGINATING commit SHA for each reused testid, not just the case ID in prose
type: feedback
---

## What happened (issue #105, ELITEA-1927, PR #576)

The closure record's testid row read: "none new — reuses 6 pre-existing testids on
`automation/testids`, all originally added by ELITEA-1922/ELITEA-1929." The promotability
table underneath was accurate and correctly fresh-verified (0/6 on `main`, 6/6 on
`automation/testids`, matched independent re-check exactly). But the row itself cited
**no commit SHA at all** — just the source case IDs as prose, no `EliteaAI/EliteaUI@<sha>`
links.

Ground truth: the originating commits were trivially findable —
`git log origin/main..origin/automation/testids -S"<testid>" -- src/` on the EliteaUI
clone returned `1e04dc97`, `f550616a`, `2f7246a2`, `2cd99034` in under a minute. The
closure record made a future human (doing the cherry-pick) redo that lookup themselves.

## Why this is distinct from the already-logged SHA-format gap

`closure_record_sha_present_but_not_a_link_still_fails.md` covers the case where a SHA
IS cited but in the wrong format (prose/backticks instead of the clickable
`EliteaAI/EliteaUI@<sha>` table form). This is one level earlier: no SHA was cited at
all, because the deliverer's mental model was "this case didn't add these testids, so
citing their commits isn't my job." `.agents/workflow.md` § Closure record doesn't
carve out that exception — the record's job is to tell the human doing the cherry-pick
exactly which commits to pick, regardless of which case's PR originally introduced them.

## Rule going forward

When a case's testid row says "reused, not new," don't treat that as satisfying item 4
on its own. Still resolve each reused testid to its originating commit
(`git log origin/main..origin/automation/testids -S"<testid>" -- src/`) and require the
closure record to cite it in the clickable `EliteaAI/EliteaUI@<sha>` form — same bar as
a testid this case added itself. Missing SHA (reused OR new) = FAIL on item 4.

## Recurrence (control-audit, issue #143, ELITEA-1902, PR #606, 2026-07-18)

Same shape again, on an otherwise well-executed closure record: the promotability
table correctly flagged `agent-add-agent-button` as un-promoted and named its source
("ELITEA-1887, not yet promoted — pre-existing dependency"), and the "Unblocks when"
line even referenced "ELITEA-1887's `agent-add-agent-button` commit if not already
promoted" — but never resolved that to an actual SHA anywhere in the record, prose or
table. Found it in under a minute: `git log origin/main..origin/automation/testids
-S"agent-add-agent-button" -- src/` → `ce74cd40`. Confirms the gap isn't about
diligence or awareness (this record clearly knew a specific commit needed citing) —
the lookup step itself is just being skipped. Third occurrence of this exact pattern
(#105, then this one) — worth adding explicitly to closure-record dispatch prompts:
"every reused-testid row needs its own `git log -S` lookup, not just a source-case
name," since knowing a citation is owed isn't the same as producing it.
