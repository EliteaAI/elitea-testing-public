---
name: A page-object method that bypasses real clicks via React onClick invoke needs root-cause, not just repro trials
description: ELITEA-2338 review — SecretsPage.open_row_actions_menu() invokes onClick via __reactProps$ directly because real Playwright/native clicks "don't open the menu"; source shows the handler reads event.currentTarget, which the workaround fakes — a concrete root-cause lead the declared improvisation skipped
type: feedback
---

## What happened (ELITEA-2338 review, PR #1221)

The implementer's `SecretsPage.open_row_actions_menu()` bypasses the DOM
click-event pipeline entirely — it looks up the button's
`__reactProps$*` fiber and calls `onClick(...)` directly — because,
per the method's docstring and a committed memory entry
(`secrets_row_actions_menu_click_needs_react_props_invoke.md`), neither a
real Playwright `.click()` (incl. `force=True`) nor a native `el.click()`
reliably opens the `SecretActionsMenu` MUI `<Menu>`, despite the button
visibly receiving the click and zero console errors. This was declared
correctly (docstring + PR body + memory, per
`.agents/role-overrides.md` § Declared-improvisation protocol) and is
therefore not a solo-blocking finding — but the investigation stopped one
step short of the decisive one.

**Reading the actual handler source found a concrete, testable root-cause
lead the implementer's trials never pursued:** `useSecretRowActions.hooks.js`'s
`handleActionsMenuClick` is `id => event => setAnchorElMap(prev => ({...prev,
[id]: event.currentTarget}))` — it gates the Menu's `anchorEl` (and therefore
`open={!!anchorEl}`) on `event.currentTarget`. The sibling MUI buttons the
implementer noted click fine (`secrets-add-button`, `secret-row-save-button`)
do NOT read `event.currentTarget` in their handlers at all — they call
argument-bound closures with no event dependency. That is precisely the
difference between the button that fails and the buttons that don't, and it
is exactly the value the workaround manually fabricates
(`{ currentTarget: el, target: el, ... }`). This doesn't prove a product bug,
but it is a testable hypothesis (e.g.: does `event.currentTarget` come back
null/wrong on a real Playwright-dispatched click in this MUI IconButton
tree?) that a source read would have surfaced BEFORE reaching for a
DOM-bypassing workaround — the same "read the source — decisive step" the
interaction-discovery ladder (`.agents/role-overrides.md`) already mandates
for UI-behavior questions, which this workaround effectively is one of.

**Why this matters beyond this one case:** a page-object method that makes a
control "work" by calling the framework's internal prop directly, rather than
simulating a real user gesture, no longer proves a real click opens that
control — if the underlying cause were a genuine defect (rather than a test
environment artifact), the workaround makes the automated test permanently
blind to it. Distinct from the existing
`chat_folder_creation_testid_placement_and_synthetic_click_false_positive.md`
entry (a JS-evaluated click producing a self-inflicted FALSE-POSITIVE console
warning during live exploration, ruled out by a real-click re-test) — this is
the opposite risk: a synthetic invocation adopted as the PERMANENT production
technique because the real interaction path was never fully root-caused.

**Reviewer takeaway:** when a declared improvisation's mechanism is "call the
framework's internal prop/handler directly instead of a real interaction,"
don't just check that repro trials were thorough (headed/headless, fresh
context, dev-server restart, etc.) — grep the actual event-handler source for
what it reads (`event.currentTarget`, `event.detail`, `isTrusted`, timing/
debounce). A one-line diff between the working and failing handlers is often
sitting right there and changes whether this is "sound reasoning, ship it"
or "under-investigated, escalate as a question with the concrete lead
attached." Per the declared-improvisation protocol this can't solo-block a
delivery, but it does earn an explicit `question` follow-up rather than
silent acceptance as settled canon.
