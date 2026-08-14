---
name: Pipeline Run Details Before/After is per-step scoped
description: STATES panel Before/After values key off the SELECTED timeline step's own input/output, not the whole run — a variable absent from that step renders both empty even when genuinely set elsewhere
type: feedback
---

Confirmed live 2026-08-09, ELITEA-2444 analysis. The Pipeline Run Details panel's
STATES accordion (`pipeline-run-details-state-row-{var}` /
`get_run_details_state_before_value()` / `get_run_details_state_after_value()`)
does **not** show a run-level Before/After snapshot — it shows the Before/After
for whichever **timeline step is currently selected**, scoped to THAT step's own
node input/output declaration.

Symptom: reading a variable's Before/After at the "wrong" step (e.g. the LAST
timeline entry, per the convention ELITEA-2443's test uses) returns **empty
strings for BOTH Before and After**, even when the variable demonstrably holds a
non-empty value elsewhere in the run (confirmed: a parent-only `state_2`, set by
the parent's own CODE1 node to `"parent_only_value"`, read as `""`/`""` at the
child's own final timeline step, but correctly `""`/`"parent_only_value"` at
timeline step 0 — the parent CODE1 step itself).

Why ELITEA-2443 never hit this: its child pipeline declared/touched BOTH common
variables (`state_1` AND `state_2`), so every timeline step had both in scope.
ELITEA-2444's child declares only `state_1`/`state_3` (not `state_2`), exposing
the per-step scoping the first time a variable is genuinely absent from some
steps' own input/output.

**Rule going forward:** for a variable NOT touched by every node in the run,
select the timeline step whose OWN input/output actually includes it — the step
right AFTER the writing node (for After) or right BEFORE (for Before) — never
assume "select the last step" is a safe universal read. A ROW's mere EXISTENCE
(`get_run_details_state_row_locator(var).count()`), by contrast, IS a clean
run-level fact, stable across every timeline step — that's the mechanism used to
prove a variable never declared in the parent's own `state:` block (e.g. a
child-only var) never appears at all.

Also: read via `page.evaluate()`/`textContent`, not the accessibility-tree
snapshot — the snapshot silently omits empty-text value boxes (looks identical
to "not found").

Full worked example: `test-specs/pipelines/l2_pipeline-subgraph-non-common-state-isolation_ELITEA-2444.md`
Test Step 12; correction recorded in `test-specs/pipelines/_surface.md`.
