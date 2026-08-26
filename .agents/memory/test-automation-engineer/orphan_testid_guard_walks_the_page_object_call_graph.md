---
name: Orphan-testid guard walks the page-object call graph
description: How to pin canon #511 mechanically — reachability from spec entry points, not a flat grep
type: feedback
aliases: [orphan testid, "#511 guard", loading indicator orphan, testid reachability]
tags: [area/locators, type/guard]
created: 2026-08-26
updated: 2026-08-26
---

## The defect it catches

ELITEA-2269 shipped `generate-project-context-loading-indicator` to EliteaUI and
declared it as a `LocatorDescriptor` field — but the only readers were the
*inherited* `wait_for_loading_visible()` / `wait_for_loading_hidden()`, which no
spec called. Canon #511 calls that an orphan: wired, never invoked, inflating the
presence-based coverage metric. Three artifacts agreed it was fine (AFS claim,
EliteaUI commit message, page object); only reachability disagreed.

## Why a flat grep does not find it

`grep 'loading_indicator' automation/` returns plenty of hits — the page-object
field, the base-class methods, other entities' specs. "Referenced" per #511 means
**invoked on a spec's executed path**, which is a call-graph property:
`click_apply()` in a spec DOES reference `approve_button`, one hop away.

## The shape that works

`automation/tests/unit/test_project_context_modal_testids_referenced.py`:

1. AST-parse the page object → `LocatorDescriptor` class fields (name → testid).
2. AST-parse each driving spec → resolve the page-object variable **from its
   construction site** (`X = GenerateProjectContextModalPage(page)`), then collect
   every `X.<attr>` — those are the entry points.
3. Build `method -> {self.<name> it touches}` over the subclass **merged over the
   base** (subclass overrides win), then take the transitive closure from the
   entry points.
4. Every declared locator must land in that closure.

Two things keep it honest: a `test_analysis_is_not_vacuous` companion (an empty
locator set or empty entry-point set would pass silently), and resolving the
variable name instead of hardcoding `modal`.

Red-green verified: RED naming exactly `loading_indicator` before the fix, green
after. Cost: ~0.02 s, no browser.

Related: [[shared page-object base placeholders]] · [[build_with_ai_shared_generate_entity_modal]]

## The other half of the fix

The orphan was resolved by *referencing* it, not deleting it: the dialog's
INPUT → LOADING → REVIEW transition is a real product observable, so the spec now
asserts the loading step **inside** an explicit `expect_generate_response()` block —
`click_generate_and_wait_for_response()` cannot be used, because it blocks until the
response, by which time the transient step is gone. On a live generation (5–20 s)
this is not flaky; it also pins the shared modal's `entityLabel="project context"`
via the `Generating project context draft...` text.
