---
name: AFS Priority line vs pytest.mark — implementer preflight check
description: Before handing off any new test, grep the AFS's own "Priority: lN" line against the new test's @pytest.mark.pN decorator — a mismatch silently excludes a self-declared high-priority case from the "p0 or p1" CI gate and is invisible to every other check (locators, additive-only diff, live green run). Caught by review on ELITEA-1846/PR #678 (own p2), ELITEA-2284/PR #1175 (inherited module p2), ELITEA-2310/PR #1186 (own p2, missed a full round), ELITEA-2377/PR #1242 (module-level, l3->p2 not p3, same-round miss), ELITEA-2435/PR #1256 (both module + per-function p3 not p2, fresh single-test file, same-round miss), ELITEA-2438/PR #1262 (round-1 fix-round dispatch NAMED this exact finding and it still had no visible diff attempt — fixed round 2), and ELITEA-2045/PR #1325 (own p2 not p1, l2/high, no fix attempt visible into round 1 review — fixed round 1's own fix-round dispatch).
type: feedback
---

## Recurrence 8 — ELITEA-2044/PR #1366 (fix round found the missing per-function override; first time a regression test was added for this class)

Same root shape as recurrence 2 (module-level `p1` correct for the covering
ELITEA-2042/high test, new sibling `test_state_panel_delete_custom_variable`
ELITEA-2044/medium silently inherits it, no marker of its own). New this
time: added a dedicated unit regression test
(`tests/unit/test_pipeline_state_panel_priority_markers.py`) that introspects
`getattr(test_func, "pytestmark", [])` — the function's OWN decorator
markers, separate from the module-level list pytest merges in at collection
— and asserts `p2` is present on the sibling and absent (no competing
priority mark) on the covering test. Verified it goes RED on the pre-fix
state (removed the decorator locally, reran, confirmed the exact failure
message, restored the fix) and GREEN with it. This walks back recurrence
4/6's "no precedent, static metadata isn't testable" conclusion — it IS
testable via the function object's own `pytestmark` attribute, just not via
a live pytest run of the test itself.

**Gotcha hit while writing it:** importing the two live UI test functions by
their real names into the unit-test module caused pytest's
`python_functions = test_*` collector to re-discover and RE-EXECUTE them
(with real `page`/`pipeline_id` browser fixtures) as a side effect of the
import — "collected 4 items" instead of 2, ~36s instead of ~0.02s. Fix:
alias the import (`as _delete_test_func` / `as _covering_test_func`) so the
bound names don't match `test_*`. Confirmed via `--collect-only` before/after.
Any future test that imports a live test function by name (not just for this
marker check) should alias it the same way, or check `--collect-only` count
first.

## Recurrence 7 — ELITEA-2045/PR #1325 (own p2 not p1, no fix attempt visible into round 1's own review)

Same lesson, recurrence-3 shape again: `test_pipeline_llm_structured_output_state_variables.py`
declared module-level `pytest.mark.p2` while its own AFS `Priority: l2 (high)`
maps to `p1` — confirmed against two l2/high siblings already in the same
`tests/ui/pipelines/` directory (`test_pipeline_llm_node_system_task_chat_history_config.py`
ELITEA-2004, `test_pipeline_yaml_flow_sync.py` ELITEA-2028 — both `p1`). Reviewer
flagged it going into round 1's own review with no visible fix attempt. Fixed in
the round-1 fix dispatch: one-line `pytestmark` edit, re-ran the spec green once
(`1 passed in 42.56s`), no other diff. Nothing new about the mechanism — logging
the 7th hit because the entry's own index line undercounts recurrences past #6
and a compaction pass should collapse these into a count, not read every narrative.

## Recurrence 5 — ELITEA-2435/PR #1256 (fresh single-test file, module AND per-function both wrong, same-round miss)

Same lesson, 5th hit in ~2 weeks: brand-new `test_skill_pin_unpin.py`
(not `extend-existing`, no sibling in the file) declared **both**
the module-level `pytestmark` list AND a redundant per-function
`@pytest.mark.p3` decorator on its single test — both `p3` (low) while
the AFS `Priority: l3 (medium)` maps to `p2`. Reviewer flagged it in round
1; **no fix attempt was visible in the diff going into round 1's own
review** — this preflight check existed on disk the whole time and still
wasn't run before the original handoff. Fixed both sites in one commit
(one-line edits each). No dedicated regression test (same reasoning as
recurrence 4). Verified via fresh-process green run + `pytest --collect-only
-m p2 <file>` now collecting the test (0 before) + `ruff check` clean.
**Reinforces recurrence 2/3's lesson harder**: the check must run BEFORE
Phase 6 handoff, every single time, not just after it's been named once —
knowing the check exists is not the same as running it.

## Recurrence 4 — ELITEA-2377/PR #1242 (module-level pytestmark, low-vs-medium direction)

Same lesson, another direction: module-level `pytestmark` for
`test_context_management_toggle.py` (covering both the pre-existing
ELITEA-2374 test and the ELITEA-2377 `extend-existing` addition) carried
`pytest.mark.p3` (low) while both cases' AFS `Priority: l3` maps to `p2`
(medium) per `pytest.ini`'s own documented scale (`p2: Priority 2
(medium)`). Reviewer flagged it in round 1 with no visible fix attempt in
the diff — the exact recurrence-3 failure mode repeating. Fixed in round 2
by editing the single module-level `pytestmark` list (one line) plus its
docstring comment — since it's module-level, one edit satisfied both
covering cases at once. No dedicated regression test exists or was added
for this class of finding: it's static pytest-marker metadata, not product
behavior, and this suite has no precedent for testing marker-priority
mappings (checked `automation/tests/unit/`, `conftest.py` — none). The
mechanical proof-of-fix instead: `pytest --collect-only -m p2 <file>`
collecting the previously-`p3` tests confirms the marker actually flipped.

## Recurrence 3 — ELITEA-2310/PR #1186 (finding raised R1, no fix attempt visible until R2)

Same lesson, a new failure mode: `pytestmark` module list declared
`pytest.mark.p2` while the AFS `Priority: l2` (high, → `p1`). The reviewer
flagged this **in round 1**, but the round-1 fix pass left it untouched — no
attempt was visible in the diff — so it recurred as an "unaddressed" finding
into round 2, costing a full extra review round for a one-line fix. Lesson
compounding recurrences 1–2: it's not enough to know the check exists — a fix
round must **verify every named finding was actually applied**, not just the
ones that felt like the "real" work (here, the marker line is easy to skip
past when the round's other findings look more substantive). Treat a
reviewer-named priority-marker finding as equally mandatory as a locator or
assertion finding — it is a one-grep, one-line fix with zero excuse to slip
a round.

## Recurrence 2 — ELITEA-2284/PR #1175 (module-level inheritance variant)

Same lesson, different mechanism: `extend-existing` appended
`test_expired_token_shows_expired_icon_and_label` (AFS priority `high`/`l2`,
→ `p1`) into a file whose module-level `pytestmark` already carried `p2`
(correct for the *original* `p2`/medium covering test). Because the new
`test()` has no marker of its own, it silently **inherits** the module's
`p2` — there's no "wrong marker" to spot in a diff, just an *absent* one,
which is even easier to miss than recurrence 1's explicit-but-wrong `p2`.
Reviewer caught it in round 1; I hadn't run the preflight check below before
the initial handoff either. **Fix:** a per-function `@pytest.mark.p1` on the
new test only — module-level `pytestmark` (and the original test) stay
untouched. Also fix the AFS itself if its own reasoning claims "shares
module/priority with the covering test" — that claim is the root cause, not
just the missing decorator: an AFS that asserts a false priority-sharing
premise will keep producing this exact miss on every future
`extend-existing` case in the same file. **Run the preflight check below
BEFORE writing the test, not just before Phase 6 handoff** — that's the gap
both recurrences share.

## What happened

Landed `test_delete_multiple_files_partial_selection` (ELITEA-1846,
`extend-existing` into `test_artifacts_delete_subfolder_checkbox.py`) by
copying the AFS's own § Gap assertions code block verbatim, including its
`@pytest.mark.p2`. The AFS's own metadata block declared
`Priority: l2 (high — as authored in the source TMS case)` — the same label
as the covering test's `@pytest.mark.p1`, and the same label every other
artifacts AFS with "l2 (high)" resolves to `p1`. A fresh reviewer caught it;
I didn't, because the test ran green either way — a marker mismatch has zero
signal in a pass/fail run.

## Why it's easy to miss

None of the standard implementer checks touch markers: locator-identity
grep, `git diff | grep '^-[^-]'` additive-only verification, and the live
2/2 clean-process run all pass regardless of which `pN` marker is attached.
The only way to catch it is a deliberate side-by-side read of the AFS's
`Priority:` field against the compiled `@pytest.mark.pN` — a check that
isn't part of the six-phase loop's Phase-4 "run it green" gate.

## The reusable check — do this before Phase 6 handoff, every time

```bash
grep -m1 "Priority" test-specs/<feature>/l*_<case>.md
grep -n "@pytest.mark.p[0-9]" automation/tests/ui/<feature>/<file>.py
```

Map: AFS `l0`→`p0`, `l1`→`p1` or `l2 (high)`→`p1`, `l3`(medium)→`p2`,
`l4`(low)→`p3` — confirm against 2-3 sibling tests in the same feature
directory if the mapping is ambiguous, don't assume. For `extend-existing`
AFS specifically, the new sibling test sits in the same file/class as an
already-merged covering test — the two markers are directly comparable
line-by-line, so this is a 10-second check with no ambiguity once you know
to run it.

## Outcome

One-line fix (`p2`→`p1`) in a fix-only round, PR #678, commit `e765a0b7`.
Cost nothing to fix; the miss itself would have silently excluded a
self-declared high-priority case from `pytest -m "p0 or p1"`, the
documented CI high-priority run — a real gap that a green test run alone
can never surface. See the companion entry in
`.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
for the reviewer-side version of this same lesson.

## Recurrence 6 — ELITEA-2438/PR #1262 (round-1 fix dispatch named it explicitly, still no diff attempt; fixed round 2)

Worst variant yet: this wasn't a fresh miss at handoff — a prior fix round's
dispatch prompt named this exact finding verbatim ("Priority marker
mismatch: … uses @pytest.mark.p3 but AFS Priority l3(medium) + pytest.ini
scale require @pytest.mark.p2 — fix the one-line decorator") and the
resulting diff going into the next review still showed no attempt. Fixed
now: `test_skill_export_import.py:583`, `TestSkillImportMissingFrontmatter.
test_import_skill_missing_frontmatter_shows_validation_error`, `@pytest.mark.
p3` → `@pytest.mark.p2`. Verified via `pytest --collect-only -m p2 <file>`
(the test now collects, was 0 before), a fresh-process live GREEN run of the
single test, and `ruff check` on the touched file (the one `I001` hit is
confirmed pre-existing on `HEAD` before this edit, not introduced by it — no
dedicated regression test added, consistent with recurrence 4's reasoning:
this is static pytest-marker metadata, not product behavior, and the suite
has no precedent for testing marker-priority mappings).

**The gap this closes:** knowing the check exists (it's been in this file
since recurrence 1) and having it *named explicitly in the dispatch prompt*
are still not sufficient — the check has to actually run as a literal step
before claiming "done" on ANY round, fix round included. If a fix-round
dispatch names a specific finding, grep for that literal line/pattern in the
diff BEFORE calling the round complete, not just after implementing the
"felt more substantive" findings.
