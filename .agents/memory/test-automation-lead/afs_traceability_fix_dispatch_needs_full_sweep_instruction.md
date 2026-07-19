---
name: AFS traceability fix dispatch needs a full-sweep instruction
description: When routing a reviewer's AFS-Coverage-Map-accuracy finding back to the implementer, explicitly ask for a whole-document sweep — a dispatch scoped to "fix row X" predictably leaves sibling instances of the identical error class stale, costing an entire extra review round
type: feedback
---

## What happened (#211/ELITEA-1839, PR #639, rounds 1-3)

Round 1 reviewer found ONE Coverage Map row overclaiming what the shipped
test actually asserts (a phantom "breadcrumb" assertion). I dispatched a
fix-only round naming that one finding (plus the actual headline finding,
an undocumented discovered defect). The implementer fixed exactly what was
named — plus, on their own initiative, one adjacent nit.

Round 2's FRESH reviewer (correctly instructed to re-run the full standing
checklist, not just verify the named delta — `reviewer_full_recheck_catches_new_findings_on_rework.md`)
found the IDENTICAL overclaiming pattern surviving in 3 MORE rows the round-1
fix never touched. This is not a new failure mode — it's the same one,
present in multiple places, because round 1's fix dispatch was scoped to
"the row the reviewer named," not "every row with this defect class."

For round 2's fix dispatch, I explicitly asked for a full sweep of the
WHOLE Coverage Map (Axis 1 + Axis 2), not just the 3 rows round 2 named,
specifically to pre-empt a predictable round-3 bounce for a 4th missed row.
The implementer's sweep found and fixed exactly that — a 4th unflagged row
of the identical shape the reviewer hadn't even spotted. Round 3 (fresh
reviewer, full recheck) approved with zero new findings — the sweep
instruction closed the entire error class in one round instead of the
"discover one more instance per round" trickle rounds 1→2 had fallen into.

## The lesson

When a reviewer finding is an INSTANCE of a systemic documentation-accuracy
class (a Coverage Map "Asserted where" cell describing the analyst's live
observation instead of what the shipped code actually checks, a provenance
column that's stale, etc.) rather than a one-off typo, the fix-only dispatch
prompt must say "sweep the WHOLE document/table for this pattern, not just
the N named instances" — every time, not just after it's already bitten you
once. A narrowly-scoped "fix row X" dispatch is the efficient-looking choice
in the moment but is the one virtually guaranteed to need a second bounce,
because the implementer (correctly, per their own scope discipline) treats
the named row as the literal ask and doesn't proactively audit siblings
unless told to.

Distinguish this from a genuinely one-off finding (a single wrong SHA, a
single missing field) where a narrow fix is the right, minimal-scope
response — the tell is whether the reviewer's own finding describes a
CLASS ("the cell describes X instead of Y" — a pattern that could recur)
or a SPECIFIC fact (one wrong value). When in doubt, ask for the sweep; the
cost of an unnecessary full-document re-read is far smaller than a 3rd
review round.

## Cross-reference

Same finding class independently logged from the IC side:
`qa-engineer`'s `afs_coverage_map_narrow_fix_leaves_sibling_rows_stale.md`
and `test-automation-engineer`'s
`afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row.md`. This entry
is the orchestrator-side actionable: it's YOUR dispatch-prompt scope that
determines whether the implementer sweeps or not — don't rely on the
implementer volunteering it.
