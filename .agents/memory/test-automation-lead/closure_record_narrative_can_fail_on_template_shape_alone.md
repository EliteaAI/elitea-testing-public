---
name: A content-correct closure record can still solo-FAIL on template shape / AFS omission
description: The control audit checks closure-record FORMAT (artifact table, AFS path/row) independently of content correctness — a record with impeccable evidence (pasted 3x gate, correct sanctioned-RED, verified promotability) still fails if it's a narrative recap instead of the `.agents/workflow.md` artifact table, or if it never states the AFS path
type: feedback
---

## What happened

Control-audit of issue #79 (ELITEA-1872, PR #540). Six of seven checklist
items passed with reproduced evidence — locator policy clean, testid
promotability independently re-verified true (fresh `git fetch` + grep on
both `origin/main` and `origin/automation/testids`), merge gate correctly
invoked the sanctioned-RED exception with 3 pasted identical failures tied
to an OPEN linked defect, reviewer gate evidenced, AFS existed and TMS
back-write had all 4 required fields in dotted form.

The closure record still FAILED item 4 (closure-record format) because it
was written as prose/narrative rather than the mandated
`.agents/workflow.md` § Closure record artifact table (`| Artifact | Where
| State |`), and — the substantive gap, not just a stylistic one — **the
AFS path (`test-specs/agents/lcritical_...ELITEA-1872.md`) was never
mentioned anywhere in the closure record itself**, only in an earlier
"Analyst done" work-log comment. A reader who opens only the closure
record (the artifact index the canon says nobody re-reads the narrative
past) cannot find the AFS from it alone.

## Why it matters

It's tempting, as the orchestrator, to treat a closure record as "done"
once every fact it asserts is independently verifiable and true — that's
necessary but not sufficient. The canon prescribes a specific *shape*
(table, explicit AFS row, explicit testid/integration rows,
unblocks/owner) precisely so the record works as a standalone index
months later, not just as a currently-true summary. Content quality does
not get credited against format compliance in a control audit — they are
separate checklist items and a FAIL on the format item stands even when
every fact checks out.

## Rule going forward

When authoring closure records (as the delivering session):
1. Always use the literal `.agents/workflow.md` template shape — the
   `| Artifact | Where | State |` table, not free prose, even when every
   fact could be conveyed either way.
2. Always include the AFS path as its own explicit row/line — it's easy to
   omit because it was already mentioned earlier in the work-log, but the
   closure record must be self-sufficient.
3. Include "Testids" / "Testids (integration)" rows even when the answer
   is "already merged, no new testid" — state it in row form, not folded
   into a promotability paragraph.

When auditing (as control): don't let a strong content pass on items
1/2/3/5/6/7 soften the format check on item 4 — verify the record actually
contains an AFS reference and matches the table shape, independently of
whether its claims are true.
