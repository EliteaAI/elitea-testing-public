---
name: Pipeline STATE panel — ambiguous add-button role name + input[name="name"] collision
description: get_by_role("button", name="Context") is ambiguous; input[name="name"] hits the pipeline Name field too
type: feedback
---

Confirmed live 2026-08-04 (ELITEA-2034 analysis, flow editor's `STATE` side
panel, "+" add-variable control).

**Trap 1 — the "+" add-variable button's Playwright-computed accessible name
resolves to `"Context"`, and is unreliable/ambiguous.** It has no
`aria-label`/`title`. `get_by_role("button", {name: "Context"})` resolved to
DIFFERENT actual click targets across 3 separate attempts in the same
session (one of them ended up toggling the whole STATE panel closed instead
of opening a new variable row). Do not rely on this locator. Until a
`data-testid` is added (flag via `add-data-testid`), locate it structurally
(e.g. the last `<button>` inside the STATE panel's variable-list container,
re-derived fresh each time — don't cache a ref/selector across a re-render).

**Trap 2 — the new-row name input's raw CSS `input[name="name"]` ALSO
matches the pipeline's own unrelated General "Name" field.** That field
carries a literal `id="name" name="name"` and precedes the STATE panel in
DOM order, so `document.querySelector('input[name="name"]')` (or any
non-role-scoped Playwright locator built the same way) silently resolves to
the WRONG field. This overwrote the pipeline's own Name field with the
state-variable name being typed — **twice** in one session, both times
requiring a manual fix-up.

**What worked reliably all 3 times:** take a FRESH snapshot immediately
before each interaction (never reuse a ref/selector captured before the
row re-rendered), and target the input via its ACCESSIBLE NAME, not a raw
attribute selector: `get_by_role("textbox", {name: "name", exact: True})`
scoped to the post-click snapshot.

Applies to any future pipeline-node case whose setup needs custom state
variables (Decision's `Input` combobox, and likely any other node type's
`Input`/variable selects — none of them ship built-in custom vars, only
`input`/`messages`).

Full writeup: `test-specs/pipelines/l2_pipeline-decision-node-configuration_ELITEA-2034.md`
§ Automation Hints; digest: `test-specs/pipelines/_surface.md`.
