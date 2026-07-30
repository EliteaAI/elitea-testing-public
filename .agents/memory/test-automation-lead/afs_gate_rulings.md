---
name: AFS gate rulings
description: The AFS is an auditable artifact, not a trusted input — it can originate a locator violation, carry a false provenance value, mis-declare its own status, and under-specify test data
type: feedback
---

## Rules

1. **A raw-locator hit may trace to the ANALYST, not the implementer.** When the
   item-1 grep fires, check the AFS's own Concrete Handles / Automation Hints
   section: if it specced that exact `get_by_role(...)` as the "Recommended
   Locator", the implementer complied correctly and the fix must land in the AFS
   too. "The surrounding code is not precedent" binds an analyst citing a shared
   helper exactly as it binds an implementer. Orchestrator-side: the AFS quality
   gate must reject a Concrete Handles row recommending role/text/CSS as primary
   for any new element the test touches — same bar as failing the implementer
   later. And never accept "reviewer said testid scoping clean" as proof the
   mechanical grep ran; only your own re-run is evidence. (Reasoning living solely
   in a method docstring is NOT a declared improvisation — the declared channels
   are the Run Report and the PR description.)
2. **A PROVENANCE cell can be false even when the testid SET is right.** This is a
   distinct failure from omitting/over-including a handle: the row names a real
   dependency but claims `on-main ✓` for something that is `main:no,
   testids:YES`. It matters because canon explicitly licenses downstream consumers
   to *inherit* provenance instead of re-deriving it — so a wrong cell is a live
   landmine for whichever future session follows the canon literally. When
   re-deriving a promotability table, diff the AFS's own provenance values against
   the same fresh ground truth, and treat a false "confirmed by fresh live
   interaction" claim as worse than a stale copy.
3. **`Status: defect-found` is a header, not a routing decision.** Read whether the
   analyst's own evidence describes the defect as *isolated* (rest of the flow
   works) or *blocking* (can't reach later steps). Isolated + mostly-already-covered
   routes as `extend-existing` + a soft-asserted Gap assertion, not a parked card.
   Cross-check the AFS's prescribed *handling* too — the header can be wrong on
   classification and handling at once.
4. **A systemic-class finding gets a whole-document SWEEP instruction.** When the
   reviewer's finding is an INSTANCE of a class (a Coverage Map cell describing the
   analyst's live observation rather than what the code asserts; a stale provenance
   value), the fix-only dispatch must say "sweep the WHOLE table for this pattern,
   not just the N named rows." A narrow "fix row X" dispatch is virtually
   guaranteed to need another bounce — the implementer correctly treats the named
   row as the literal ask. Tell: does the finding describe a CLASS or a SPECIFIC
   fact? When unsure, ask for the sweep.
5. **A mid-implementation TEST-DATA gap returns to the analyst.** If Phase-2
   exploration finds the AFS's prescribed data cannot exercise the case's core
   assertion (not a selector, not a wait — the DATA the pass/fail criteria depend
   on), that is a scope/coverage change → `needs-analyst-rerun`. Do not let the
   implementer substitute a well-reasoned replacement assertion. Red flag to act
   on, not merge around: the Run Report itself recommending "an analyst rerun if
   the original intent needs restoring."
6. **Commit ordering when a standalone analyst has no commit authority:** cut
   `tests/<CASE>-<slug>` from fresh `automation/base`, commit ONLY the AFS on it
   (`docs(afs): …`), then commit agent-memory files directly on `automation/base`
   and push, then rebase the short-lived unpushed feature branch. Memory files must
   never ride in the case's PR diff.

## Seen 6×

- #133 / ELITEA-1887 / PR #601 — AFS specced `popper.get_by_role("menuitem", …)` as the recommended handle; reviewer's round-2 APPROVED said "testid scoping clean".
- #183 / ELITEA-1895 / PR #630 — `agent-add-agent-button` marked `on-main ✓` while actually testids-only; #143's record had established the truth a day earlier.
- ELITEA-1799 / #148 / PR #608 — `defect-found` header, isolated defect, correctly routed as extend-existing + sanctioned RED.
- …plus 3 earlier occurrence(s) — full per-case detail in the source entries below.

See also: afs_can_be_the_source_of_a_locator_violation.md ·
afs_defect_found_can_be_extend_existing_shaped.md ·
afs_provenance_column_can_be_factually_wrong.md ·
afs_traceability_fix_dispatch_needs_full_sweep_instruction.md ·
afs_commit_ordering_when_analyst_has_no_commit_authority.md ·
mid_implementation_coverage_gap_needs_analyst_not_workaround.md
