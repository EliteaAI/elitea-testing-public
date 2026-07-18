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

## Recurrence 2 (delivery + control-audit by the SAME session identity, issue #160,
ELITEA-1962, PR #617, 2026-07-18)

Fourth occurrence, and the first one where the deliverer and the auditor were the same
orchestrator (me) across two different sessions — the closure record I authored during
delivery named 3 REUSED testid families ("earlier still-open cases", "someone else's
cherry-pick backlog") with zero commit SHAs, then a few hours later a fresh control-audit
session (also me) caught it as a FAIL. Resolved in <1 min per family:
`toolkit-field-${k}-input`/`toolkit-type-card-${itemKey}` → `1e04dc97` (EL-1922),
`credential-form-save-button` → `6f9b1bf2` (EL-1971). Knowing the rule exists (it's in
my own memory index) evidently isn't enough to apply it at closure-record-authoring time
— the lookup step needs to become a literal checklist line in the closure-record
dispatch/authoring template itself, not something recalled from memory under delivery
pressure. If this recurs a 5th time, add a hard mechanical gate: no closure record ships
with a "REUSED" testid row that doesn't also contain the literal string `EliteaUI@`
followed by 7+ hex chars, checked before posting.

## Recurrence 3 (control-audit only, issue #175, ELITEA-1871, PR #623, 2026-07-18) — 5th occurrence, threshold crossed

Fifth occurrence — the self-set "add a hard mechanical gate" threshold above is
now crossed. Closure record's Testid row said "none new — all 4 handles
pre-existed | ✅ confirmed on both automation/testids AND EliteaAI/EliteaUI main"
with a pasted YES/YES table — good discipline on the promotability check itself,
but zero SHA anywhere in the comment. Resolved in <1 min:
`git -C EliteaUI log --oneline -S"agent-name-input" origin/main -- src/` →
`f9a1c8b7 [EL-5634] Add data-testid for automated UI tests (#484)` (same commit
for all 4 testids; `agent-save-button` also traces to `76c60fed` [EL-5313]).
Notably this delivery ALSO correctly worked around the separate
`testid_grep_quoting_gotcha` bug (used bare-string grep, got the true YES/YES) —
so the deliverer clearly knows the fresh-fetch-and-verify discipline; the SHA
citation step specifically is what keeps getting skipped even when everything
else around it is done right. FAILed control-audit item 4 solely on this basis
(the underlying promotability conclusion was independently confirmed TRUE).
No existing canon-fix issue tracks this specific gap (distinct from #553, which
covers only the grep-quoting bug) — flagged in the #175 verdict comment as
worth filing one; still not filed as of this writing since the control task
scoped this session to VERDICT-ONLY on #175 itself. Next control-audit or
framework-scale session should open the canon-fix issue AND consider hard-coding
the `EliteaUI@[0-9a-f]{7,}` presence check into the closure-record authoring
template directly, since 5 occurrences of "know the rule, skip the lookup under
delivery pressure" means the rule-in-memory approach has run its course.
