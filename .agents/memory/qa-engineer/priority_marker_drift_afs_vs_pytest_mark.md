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

## Recurrence variant (PR #1175/ELITEA-2284, 2026-08-05) — module-level pytestmark

Same defect class, different mechanism: `test_personal_token_create_and_verify.py`
declares priority as a **module-level** `pytestmark = [..., pytest.mark.p2, ...]`
(fine while the module held only ELITEA-2280, priority medium). The ELITEA-2284
extension appended a second test method to the SAME module — case frontmatter
says `priority: high` — with no per-function marker override, so it silently
inherits the module's `p2`. Confirmed against convention: `pytest.ini` defines
`p1: Priority 1 (high)`; other `l2 (high)`-labelled cases (ELITEA-2114, ELITEA-1866,
ELITEA-2166, ELITEA-2168, ELITEA-2075) all compile to `@pytest.mark.p1` as a
**per-function decorator**, precisely because module-level priority markers don't
survive a second case with a different priority landing in the same file. The
AFS itself was also internally self-contradictory (Priority line opened "l3
(medium...)" then concluded "so l2 is used here") and its Gap-assertions section
asserted "both cases share module/priority" — false, and the root cause of the
drift. **Check extended**: when an `extend-existing` AFS adds a sibling test to a
file whose priority is set via **module-level** `pytestmark` (not a per-function
decorator), diff the new case's own frontmatter priority against that shared
marker explicitly — module-level priority is a trap once a second, differently-
prioritized case lands in the same file. Flagged CHANGES_REQUESTED.

## Recurrence variant (PR #1186/ELITEA-2310, 2026-08-05) — fresh AFS, plain module-level pytestmark, no sibling to compare against

Third occurrence, simplest mechanism yet: a brand-new (not `extend-existing`)
AFS/test — no covering test in the same file to eyeball against. Case
frontmatter: `priority: high`. AFS metadata: `**Priority**: l2` (correct per
convention, just missing the usual `(high — as authored...)` annotation).
`test_analytics_default_load.py` declares `pytestmark = [pytest.mark.ui,
pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]` — `p2` (medium),
should be `p1` (high) per `pytest.ini` (`p1: Priority 1 (high)`) and the
established `l2(high)→p1` mapping confirmed across `test-specs/artifacts/`,
`test-specs/chat-interface/`, etc. (8+ sibling AFS/tests, zero exceptions).
**Check generalizes**: don't wait for a sibling test in the same file to
compare against — grep the AFS's own `Priority:` line against its own
compiled `pytest.mark.p*`/`pytestmark` every time, sibling or not; a solo
fresh AFS drifts just as easily as an extended one. Flagged CHANGES_REQUESTED
(one-line fix: `pytest.mark.p2` → `pytest.mark.p1` in the module-level
`pytestmark` list).

## Recurrence variant (PR #1242/ELITEA-2377, 2026-08-06) — module marker wrong for BOTH cases from the outset, not exposed by a priority difference

Fourth occurrence, a new sub-shape: `test_context_management_toggle.py`'s
module-level `pytestmark` carries `pytest.mark.p3` (low). The covering test
(ELITEA-2374) AND the new extend-existing sibling (ELITEA-2377) **both**
have TMS case `priority: medium` (l3) — unlike the ELITEA-2284 variant, this
isn't "a second, differently-prioritized case lands in the file" exposing a
marker that was correct for the first case; the marker (`p3`) was **already
wrong for the first case** when ELITEA-2374 merged, and the second case just
inherits/perpetuates the same error. Confirmed against convention via a
clean, unambiguous sibling: `test_secret_delete_via_three_dot_menu.py`
(ELITEA-2338, case `priority: medium`, AFS `l3`) compiles to
`pytest.mark.p2` — l3(medium)→p2 holds. **Check extended again**: even when
a module-level marker is *internally consistent* across every case sharing
the file (no priority drift to compare against a sibling), it can still be
wrong against the suite-wide `l{n}→p{n-1}` convention — verify against an
**external** sibling test in a different file/feature with the same case
priority, not just against the file's own existing test. Flagged
CHANGES_REQUESTED even though the root cause predates this PR (inherited
from the already-merged ELITEA-2374 test) — the fix is a live, CI-relevant
correctness gap for the case THIS PR delivers (a `-m p2` selection run
silently misses it), so it's in scope regardless of origin.

## Recurrence variant (PR #1262/ELITEA-2438, 2026-08-06) — implementer likely pattern-matched off a pre-existing WRONG sibling in the same file

Sixth occurrence, same `l3(medium)→p3` mis-mapping, but with a new twist:
the new test (`test_import_skill_missing_frontmatter_shows_validation_error`,
class `TestSkillImportMissingFrontmatter`) was appended to
`test_skill_export_import.py` — a file that ALREADY contains a pre-existing,
unfixed instance of this exact bug: `TestSkillImportNonBaseVersion.
test_import_skill_non_base_version` (ELITEA-1738) has AFS `Priority: l3
(medium, per case)` — byte-identical wording to ELITEA-2438's own AFS line —
and compiles to `@pytest.mark.p3`, also wrong (should be `p2`), but never
caught because no prior review diffed it against pytest.ini's scale (it
predates this recurring-bug check's discovery). The FIRST test in the same
file, `TestSkillExportImport.test_export_and_import_skill_base_version`
(ELITEA-1737, same `l3 (medium, per case)` wording), correctly compiles to
`p2` — so the file has one right and one wrong example of the identical
label, and the new (third) test copied the wrong one.

**Check extended once more**: when a same-file sibling exists, don't assume
"matches an existing test in this file" is sufficient verification — a file
can carry its OWN pre-existing unfixed instance of this bug. Compare against
pytest.ini's scale + the AFS's own `Priority:` line directly, every time,
even when a same-file precedent is available; a matching neighbor may itself
be wrong. Flagged CHANGES_REQUESTED (round 1, static review, one-line fix:
`test_skill_export_import.py`'s new `@pytest.mark.p3` → `@pytest.mark.p2`
on the ELITEA-2438 test only — did not expand scope to also fix the
pre-existing ELITEA-1738 instance, which is out of this PR's diff; flagged
separately as a non-blocking pre-existing-debt note instead).

## Recurrence variant (PR #1256/ELITEA-2435, 2026-08-06) — brand-new file, both module `pytestmark` AND per-function decorator wrong

Fifth occurrence, same `l3(medium)→p3` mis-mapping as recurrence 4, but a
fresh single-test file (not extend-existing, no sibling in the same file to
compare against) — closest in shape to recurrence 3. AFS
`l3_skill-pin-unpin-flow_ELITEA-2435.md` states `Priority: l3 (case
frontmatter: medium, case body header also says medium — no drift)`.
`test_skill_pin_unpin.py` declares **both** the module-level `pytestmark`
list (`pytest.mark.p3`) and a **redundant per-function** `@pytest.mark.p3`
decorator on the single test — both wrong, should be `p2`. Confirmed against
convention with an 11-sibling sweep of `test-specs/skills/l3_*.md` vs their
compiled `automation/tests/ui/skills/*.py` markers: 11/13 `l3(medium)`
skills cases compile to `p2` with zero exceptions among directly-comparable
ones. Flagged CHANGES_REQUESTED (round 1, static review — no fix visible
yet). **Nothing new to extend in the check itself** — this is pure repeat
volume (5th hit in ~2 weeks) confirming the gap is systemic, not a one-off:
the implementer's own preflight check
(`.agents/memory/test-automation-engineer/afs_priority_vs_pytest_mark_preflight_check.md`)
documents the exact grep to run BEFORE handoff, and this PR shows it still
isn't being run reliably pre-handoff, only caught at review.

## Recurrence variant (PR #1366/ELITEA-2044, 2026-08-09) — combined analyst+implementer slot, `high`-priority sibling in the same file this time

Seventh occurrence, back to the ELITEA-2284 shape (a second, differently-
prioritized case lands in a file whose module-level `pytestmark` was correct
for the FIRST case) but with the priorities flipped: covering test
ELITEA-2042 (case `priority: high`) correctly compiles to the module-level
`pytest.mark.p1` in `test_pipeline_state_panel_default_and_custom_variables.py`.
The new sibling `test_state_panel_delete_custom_variable` (ELITEA-2044, case
frontmatter `priority: medium`, AFS itself mislabels this "l2 (medium...)" —
should be l3 per the `l{n}→p{n-1}` filename convention, a second small
authoring slip) has no per-function marker override, so it silently inherits
the module's `p1` (high) instead of `p2` (medium). Confirmed against
convention with 3 external siblings in the SAME `pipelines` feature area,
all case `priority: medium`, all compiling to `p2` with zero exceptions:
`test_pipeline_canvas_zoom_and_pan.py` (ELITEA-2019), `test_pipeline_collapse_left_panel.py`
(ELITEA-2072), `test_pipeline_custom_node_configuration.py` (ELITEA-2036).
Notable: this PR's own body documents two mechanical greps (locator-ladder,
additive-only) in detail and both are genuinely clean — the priority-marker
class of bug is invisible to both, exactly as the original entry predicts.
Flagged CHANGES_REQUESTED — one-line fix: add a per-function
`@pytest.mark.p2` decorator on `test_state_panel_delete_custom_variable`
(cannot change the shared module-level `pytestmark` without demoting the
correctly-`p1` ELITEA-2042 test).
