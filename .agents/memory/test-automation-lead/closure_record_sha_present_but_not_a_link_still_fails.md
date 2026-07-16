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
