---
name: Closure record SHA present but not a link still fails item 4
description: item 4 requires the artifact table + clickable EliteaAI/EliteaUI@<sha> commit link form specifically — a closure record that states the right commit SHAs in prose/backticks (not missing) is still a FAIL, not a pass with a nitpick
type: feedback
---

## What happened (issue #103, ELITEA-1899, PR #567)

The closure record was informationally complete and honest — it named the exact
commit SHAs (`6bb6a23c`, `558160a6`), the right branch (`automation/testids`), and the
correct "not yet on main" state. Every fact in it was true. But it was written as prose
with backticked references (`` `EliteaAI/EliteaUI` `` , `` `6bb6a23c` ``) instead of the
canonical `| Artifact | Where | State |` table with commits in the clickable
`EliteaAI/EliteaUI@<sha>` link form that `.agents/workflow.md` § Closure record
mandates. No markdown table existed at all.

## Why this is not a nitpick

`.agents/workflow.md` is explicit that backticked cross-repo refs are wrong on two
independent grounds: (1) GitHub never auto-links inside code spans, so the "mentioned
in…" backlink on the EliteaUI side — which is how a human promoting the case actually
discovers it — never gets created; (2) it's the literal, named failure mode in
checklist item 4 ("not backticked"). Prior audits of mine had been treating "is the SHA
present and correct" as the bar and stopping there. It isn't — presence of the fact and
correctness of its delivery format are two separate checks, and the canon explicitly
gates on both.

## Rule going forward

When auditing item 4, don't just verify the commit SHAs/repo names are factually
correct — check the literal rendering: is it a markdown table, and are cross-repo refs
in `owner/repo@sha` / `owner/repo#N` form as plain text (not inside backticks, not
bare)? A prose closure record with 100%-correct facts in the wrong format still FAILs.

## Recurrence (control-audit, issue #166, ELITEA-1947, PR #621, 2026-07-18)

Same shape, but this time on a REUSED/dependency commit rather than the case's own
testid commit — and the closure record otherwise did everything right: it HAD a
proper markdown table, and it DID cite `c1fdd234` (this case's own commit) in the
correct clickable `EliteaAI/EliteaUI@c1fdd234` form. But the ELITEA-1922 dependency
commit `1e04dc97` — cited twice (once in the promotability table, once in the Status
line) — appeared both times as a bare backticked SHA (`` `1e04dc97` ``) with no repo
prefix at all, not even a bare `@1e04dc97`. So partial compliance within the same
record doesn't imply full compliance — check every cited commit independently, not
just the first one or the case's own.

Compounding find: the same record named the dependency's origin as "already-merged
case `#…`" — a literal, unfilled ellipsis placeholder standing in for a real issue
number. `gh search issues --repo EliteaAI/elitea-testing-public "ELITEA-1922"` resolved
it in under a minute: issue **#60**. A placeholder character left in a posted record is
a distinct, cheaply-checkable defect from the SHA-format gap — worth grepping for
non-numeric characters immediately after a bare `#` in closure records generally.

**Notable: this is the exact same dependency commit (`1e04dc97`, same two testid
families `toolkit-field-${k}-input`/`toolkit-type-card-${itemKey}`) that already
caused this identical FAIL once before**, on a different downstream case
(`closure_record_reused_testids_still_need_commit_shas.md`'s "Recurrence 2", #160/
PR#617). Two unrelated cases both depend on this same still-unpromoted EliteaUI
commit and both got its citation wrong the same way. Two implications: (1) whoever
eventually cherry-picks `automation/testids` → `main` should treat `1e04dc97`
specifically as high-priority — it keeps tripping up downstream closure records, and
promoting it removes the recurring citation risk entirely; (2) a closure-record author
citing `1e04dc97` (or any commit already flagged in this memory file) should treat that
as a specific extra-scrutiny trigger, not just apply the general rule fresh each time.
