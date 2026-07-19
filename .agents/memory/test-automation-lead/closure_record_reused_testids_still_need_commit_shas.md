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

## Recurrence 4 (control-audit only, issue #181, ELITEA-1901, PR #629, 2026-07-19) — 6th occurrence, canon-fix issue finally filed

Sixth occurrence, identical shape to recurrence 3: "none new — all 14 handles
pre-existing, confirmed on BOTH `automation/testids` AND main" + a correct,
independently-reconfirmed 14-row YES/YES table, zero SHA anywhere. Mechanically
confirmed absence via `grep -oE 'EliteaUI@[0-9a-f]+'` on the posted comment
body (no match) rather than eyeballing. Traced 7 of the 14 originating commits
in under 2 minutes to prove the citation was cheaply available and simply
skipped: `f9a1c8b7` (agent-name-input/model-selector-name/agents-page-header),
`2d98830a` (agents-import-button/agent-import-confirm-button), `9cb837f4`
(entity-card-name), `76c60fed` (agent-information-section). Filed the
overdue canon-fix issue this time: EliteaAI/elitea-testing-public#637,
proposing (A) a hard mechanical presence-check gate for `EliteaUI@[0-9a-f]{7,}`
in the closure-record authoring flow, and (B) amending `.agents/workflow.md`'s
template to explicitly cover the "already fully on `main`, nothing pending"
shape — the current template's framing ("points at the commits the human
**will cherry-pick**") reads as conditional on a pending action, which may be
exactly why the "nothing pending" shape keeps getting exempted in practice
even though the canon text doesn't actually carve out that exception. Until
#637 resolves one way or the other, treat every testid row — new, reused, or
fully pre-existing on both branches — as owing a `EliteaUI@<sha>` citation;
missing it is a solo item-4 FAIL regardless of how well-verified the
promotability conclusion underneath it is.

## Recurrence 5 (control-audit only, issue #197, ELITEA-1921, PR #634, 2026-07-19) — 7th occurrence, and `1e04dc97` is now a 3x repeat offender

Seventh occurrence overall. Otherwise an unusually clean closure record — the
9-testid promotability table was independently re-verified testid-for-testid
against the merged test's own call chain with zero discrepancy, the best match
seen across these audits so far. But the same gap: cited
`EliteaAI/EliteaUI@750d72f7` correctly for the ONE new testid, then dismissed
the other 5 as "5 pre-existing testids reused from `automation/testids` (added
in earlier ELITEA-1922 session)" — prose, zero commit links. Traced in <3 min:
`1e04dc97` (`toolkit-type-card-mcp`, `toolkit-form-name-input`,
`toolkit-field-url-input`, `toolkit-form-save-button`) and `2cd99034`
(`toolkit-detail-title`).

**`1e04dc97` specifically has now caused this exact citation-gap class three
times on three different downstream cases**: #160/PR#617 (SHA missing
entirely — this file's Recurrence 2), #166/PR#621 (SHA present but wrong
format, bare-backticked — `closure_record_sha_present_but_not_a_link_still_fails.md`'s
recurrence), and now #197/PR#634 (SHA missing entirely again). It is the
single highest-value target for human cherry-pick promotion among all
still-pending `automation/testids`-only commits — promoting it to `main`
would retroactively resolve the promotability gap on 3+ cases at once and
remove this specific recurring citation risk. Flagged as a standing-watch
item in the #197 verdict comment. Any closure record citing `1e04dc97` (or
seeing `toolkit-form-name-input`/`toolkit-form-save-button`/
`toolkit-type-card-${itemKey}`/`toolkit-field-${k}-input`/`toolkit-detail-title`
in its testid set) should treat that as a known, pre-resolved lookup — the SHA
is `1e04dc97` (+ `2cd99034` for `toolkit-detail-title`), no fresh trace needed.

## Recurrence 6 (control-audit only, issue #240, ELITEA-1827, PR #658, 2026-07-19/20) — 8th occurrence, plus a new sub-shape: phantom source case in the prose list

Eighth occurrence, same root gap — canon-fix issue #637 (filed at recurrence 4)
is still open and unanswered as of this audit. The Testids row read "none newly
added — 100% reuse of testids already pushed to `automation/testids` by prior
cases (ELITEA-1824/1809/1832/1808)" with the 4 real commit SHAs relegated to a
plain fenced code block further down (confirmed via `body_html`: renders as
`<pre><code>`, no `<a href>` — not even the "SHA present but wrong format"
shape, since it's inside a code fence rather than prose/backticks).

**New wrinkle**: the prose case-ID list named 4 sources ("1824/1809/1832/1808")
but the 4 actual cited commits only trace to 3 distinct cases — 1824 (×2
commits), 1808, and 1832. **ELITEA-1809 was not a real dependency at all** —
its own testid commit (`3d2edf53`, bucket search-input/clear-button) isn't
part of this test's call chain anywhere. This is a new failure sub-shape
worth watching for on future recurrences: once a closure record stops
resolving reused testids to their actual commits and instead names "the
cases I remember touching this area," the case list itself can silently drift
from the real dependency set — a second, independent risk stacked on top of
the missing-link format violation, both fixed by the same discipline (always
run `git log -S"<testid>" origin/main..origin/automation/testids -- src/`
per testid, never reconstruct the source-case list from memory).
