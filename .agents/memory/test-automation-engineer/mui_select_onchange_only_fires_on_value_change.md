---
name: MUI Select onChange only fires when the clicked value differs
description: "Re-select the currently-displayed value" AFS steps can hit a real product no-op — MUI's SelectInput.js skips onChange if clicked value === current value prop
type: feedback
---

## The pattern (confirmed defect: #1036, ELITEA-2033)

Several AFS steps intentionally test "select the value that's already shown" to
prove the control itself works, not just its initial state (e.g. Router node's
Default output field defaults to displaying "END" via a client-side fallback
`yamlNode?.default_output || 'END'`, and the case wants you to click "END" anyway).

MUI's own `SelectInput.js` (`handleItemClick`) only calls `onChange` when the
clicked option's value **differs** from the Select's current `value` prop. If the
field's DISPLAYED value already equals the target (via a fallback default, or a
prior selection), clicking it again is a **silent no-op** — no onChange, no
downstream state update, no side effect (e.g. no canvas edge in a ReactFlow
pipeline node).

## Why this is easy to miss

The field's own DISPLAY doesn't change (it already showed the target value), so
a naive `get_*_value() == target` assertion passes regardless of whether the
click actually did anything. Only a side-effect that's absent-by-default (a new
edge, a new API payload field, a toast) actually distinguishes "genuinely
selected" from "was already showing this via fallback."

## What to do when you hit it

1. Verify via a genuine side effect (not the field's own display text) — an edge
   testid, a YAML/API field read, anything that starts absent and should appear.
2. If deterministic (reproduces every attempt): this is a real product defect,
   not a test issue. File it, then isolate via this project's `soft_failures` +
   `pytest.fail()` shape (NOT `expect.soft()` — see
   `sanctioned_red_soft_assert_traps.md`, since a bool-returning helper like
   `edge_testid_present()` isn't a Locator).
3. Don't "fix" it by pre-selecting a different value first then re-selecting the
   target — that changes what the AFS step is actually testing (re-confirming an
   already-selected option) into something else. Assert the literal case
   behavior and let the known-defect path absorb the failure.

## Where seen

ELITEA-2033 (Router node pipeline config), Default output field — filed as
EliteaAI/elitea-testing-public#1036. Worth checking for on ANY "re-select
already-shown value" step across other node types / forms in this suite.
