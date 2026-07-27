---
name: Priority marker drift — AFS declares "high" but pytest.mark says p2
description: PR #678/ELITEA-1846 reviewer pass — an extend-existing AFS's own Gap-assertions code block specified @pytest.mark.p2 for a case its own metadata declares "Priority l2 (high)", identical to the covering test's @pytest.mark.p1 and to 100% of sibling artifacts AFS/tests with the same label. Real, CI-relevant, and easy to miss because it never shows up in a green/red run.
type: feedback
---

## The situation

ELITEA-1846's `lextend_delete-flow-multiple-files-partial-selection_ELITEA-1846.md`
AFS metadata states `**Priority**: l2 (high — as authored in the source TMS case)`
— the exact same label as its own covering test, ELITEA-1847
(`@pytest.mark.p1` on `test_delete_subfolder_via_checkbox`, same file, same
class). But the AFS's own § Gap assertions code block specified
`@pytest.mark.p2` for the new sibling method, and the implementer copied it
verbatim (faithful-to-AFS, so not an implementer error — an AFS-authoring
slip).

## Why it matters

`automation/CLAUDE.md` documents `pytest -m p0` as the deploy gate and
`pytest -m "p0 or p1"` as the high-priority CI run. A case whose own metadata
says "high" but whose compiled marker says `p2` is silently excluded from
that gate — a real, CI-relevant consequence, even though the test itself
runs green and proves nothing wrong at the assertion level. This class of
bug is invisible to every other review technique (mechanical locator grep,
additive-only diff, live re-run) because none of them touch markers.

## The reusable check

Grep every artifacts AFS's `Priority:` line against its compiled test file's
`@pytest.mark.p*` decorator — same-label cases should carry the same marker.
At review time this run: `grep -m1 "Priority" test-specs/artifacts/*.md` vs
`grep -n "@pytest.mark.p[0-9]" automation/tests/ui/artifacts/*.py` — 8/9
`l2 (high)` cases used `p1`; only the new ELITEA-1846 sibling method broke
the pattern with `p2`.

Do this specifically when reviewing an `extend-existing` AFS's new sibling
`test()` method sitting next to an already-merged covering test in the same
file/class — the two tests' priority markers are directly comparable
line-by-line, so a mismatch is cheap to catch and easy to miss (nothing in
the assertions, selectors, or Coverage Map surfaces it).

## Outcome

Flagged as the sole Important finding, verdict CHANGES_REQUESTED (one-line
fix: `p2` → `p1`). Everything else in the PR (triangulation, additive-only
contract, live 2/2 whole-file run, Coverage Map against all 17 source-case
steps) held up clean.

## Resolution (round 2, fresh session, APPROVED)

Fix landed as commit `e765a0b7` — verified directly (`git show <branch>:<file>
| grep "pytest.mark.p"`), both the covering test and the new sibling method
now read `p1`. Full standing-checklist re-run from scratch (not delta-only)
found nothing else: mechanical locator grep clean, additive-only diff clean,
independent live whole-file run GREEN 2/2, `ruff check` claim reproduced
against a fresh `automation/base` copy of the file (genuinely pre-existing
`I001`), Coverage Map ticked complete against all 17 fetched case steps with
a real per-step assertion at each row. Two new non-blocking Nits surfaced on
this full pass (neither was checked in round 1, which only re-verified the
marker): (1) case step 10's full modal detail (warning icon / X icon /
Cancel button / blue-highlighted text) is only partially asserted — heading
substring + message text only — but this is byte-identical to the
already-merged covering test's own established pattern, not a regression
this PR introduces; (2) `EXPECTED_CONFIRM_MESSAGE`/`EXPECTED_SUCCESS_TOAST`
are re-declared as class-level attributes with values IDENTICAL to the
module-level constants of the same name ~270 lines above (used directly by
the first test) — harmless (class attr shadows the module global via
`self.`), but a real DRY violation on wording that's a documented
CLARIFICATION target (#659/#660): a future wording fix now needs two call
sites updated instead of one. Verdict: **APPROVED**.
