---
name: The AFS is a work order, not gospel — verify its claims, amend the file, never silently re-scope
description: An AFS row can be confidently wrong (a real testid on the wrong component, a false "doesn't exist" from a narrow viewport, a Priority/marker mismatch, a Coverage-Map cell describing the analyst's observation not the shipped assertion). Verify before building on it — and when you correct one, edit the AFS file itself and grep the WHOLE document.
type: feedback
---

## Rule

**Verify, then amend the file.** An AFS claim is a starting hypothesis. But
correcting one is never a licence to re-scope: a `testid needed:` row is
satisfied by a testid or escalated to the lead — never downgraded to a role
handle "for now."

## Four claim types that have shipped wrong

1. **"testid X, on-main ✓".** The string existing is not the claim. Confirm
   the OWNING component renders on your surface:
   `grep -rln "<Component>" src/ | grep -v "<Component>.jsx"` to list
   importers, then live `document.querySelector('[data-testid="X"]')` on the
   actual page. Same check one level up for PROVENANCE:
   `git grep -n "X" origin/main -- src/` must hit the **matching file**, not
   just any file — a hit in a look-alike component produces a false
   "promotable" row in the closure record.
2. **"element/column doesn't exist" ⇒ CLARIFICATION, not asserted.** Can be a
   narrow-viewport artifact. Re-verify at 1600×900 before accepting it —
   neither the headed (`no_viewport=True`) nor headless (1366×768) context
   default guarantees width. Often the observable is already sitting inside a
   whole-row `text_content()` read, unasserted: check before reaching for
   `add-data-testid`.
3. **`Priority: lN` vs `@pytest.mark.pN`.** Invisible to locator greps,
   additive-only diffs and green runs alike. Preflight, every handoff:
   `grep -m1 "Priority" test-specs/<f>/l*_<case>.md` against
   `grep -n "@pytest.mark.p[0-9]" <spec>`. Map l0→p0, l1/l2(high)→p1,
   l3→p2, l4→p3; confirm against 2–3 siblings if ambiguous.
4. **Coverage-Map "Asserted where" cells** habitually describe the analyst's
   richest live observation, not the coarser proxy the code actually asserts.

## The sweep rule (the expensive half)

One bad cell is a property of the document, not a typo. The moment you correct
ANY claim — handle name, count, absence, assertion description — grep that
string across the WHOLE AFS before calling the round done. Same when a Phase-2
round adds N handles: grep all N before writing the PR description; narrating
only the top-of-mind ones is exactly how a partial amendment bounces.

**Declaring an improvisation ≠ amending the AFS.** Commit message, PR body
and docstring are read once and archived; the AFS is what the next
implementer opens. When you're about to declare a canon-gap improvisation,
open the AFS file in the SAME commit and fix the row that named the old
handle. Self-check: `grep <old-handle> test-specs/**/*.md` returns nothing
(or only an explicit "corrected from X" note) — the moral equivalent of
`git diff | grep '^-[^-]'`.

## Seen 4×

- ELITEA-2166 → PR #710 → ELITEA-2167/PR #988 F3 — `agent-version-selector-trigger` real but on `ApplicationVersionSelect.jsx` (detail-page tab bar), not the composer; a companion absence-check needed a testid that didn't exist; declared in 3 places, AFS never touched; then the same failure via provenance (`chat-participants-*` on main, wrong component).
- ELITEA-1839 / PR #639 R1→R3 — fixed the one named Coverage-Map row; 3 siblings had it, a full sweep found a 4th. Addendum ELITEA-1824/PR #653: own partial amendment left 3 of 5 handles stale across 9 spots.
- ELITEA-1846 / PR #678 — landed `p2` for an AFS-declared "l2 (high)" case next to a `p1` covering test; green either way.
- …plus 1 earlier occurrence(s) — full per-case detail in the source entries below.

See also: afs_testid_can_name_a_real_but_wrong_component.md ·
afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row.md ·
afs_priority_vs_pytest_mark_preflight_check.md ·
analyst_absence_claims_need_normal_viewport_reverification.md ·
artifacts_context_viewport_defaults_too_narrow_for_last_update_column.md
