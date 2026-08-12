---
name: Console/network assertion checks only up to its own step, not later ones
description: A page.on() listener registered at test start keeps collecting, but the assert runs once (usually at Save) — later steps (e.g. reload) are silently unchecked
type: feedback
---

Pattern found identically in two sibling pipeline-node tests
(`test_pipeline_toolkit_node_config_and_input_mapping.py` / ELITEA-2010,
`test_pipeline_custom_node_configuration.py` / ELITEA-2036) during PR #1322
review (2026-08-08).

**The shape:** `console_errors`/`failed_requests` lists are registered via
`page.on(...)` right after the page object is created, before Step 1 — so
they keep accumulating for the whole test. But the `assert not
console_errors` / `assert not failed_requests` pair runs exactly once,
inside the Save step (mid-test), immediately after `save_and_wait_for_update`.
Both AFSs' Expected Results say "no console errors, no failed network
requests, at any step" / "checked across the whole flow" — but the reload
step that follows (page.goto + persistence assertions) fires its own
console/network activity that is captured into the same lists and never
re-asserted. A regression introduced only on reload (a CodeMirror
re-hydration warning, a background 404 on the re-fetch) would pass green
despite the AFS's own claim.

**Why this wasn't blocking either PR:** it's systemic (identical code,
copy-pasted across sibling node-config tests, already merged once via
ELITEA-2010) rather than something newly introduced — flagging it doesn't
fix the earlier instance and diverging one test from its sibling's shape
mid-batch creates its own inconsistency. Filed as a review finding, not a
blocker.

**Fix, when someone picks this up (probably a suite-wide sweep across all
`test_pipeline_*_node_*.py` files):** either move the console/failed-request
assertion to the END of the test (after the reload block), or add a second
assertion pass there. Simplest: assert once, after the LAST step that
performs page activity — not at Save if Save isn't actually the last step.
