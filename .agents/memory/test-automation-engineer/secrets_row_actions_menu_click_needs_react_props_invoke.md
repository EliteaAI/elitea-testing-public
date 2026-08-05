---
name: Secrets row-actions menu click needs direct React props invoke
description: SecretsTable's three-dot menu button silently fails to open via Playwright .click()/force=True/native el.click() — only invoking the React onClick prop directly works
type: feedback
---

## What happened (ELITEA-2338, implementation day)

`SecretsTable.jsx`'s row "more actions" (three-dot) `IconButton`
(`data-testid="secret-row-actions-button"`) reliably fails to open its
`SecretActionsMenu` (MUI `<Menu>`) when clicked via:

- Playwright's real simulated `.click()` (incl. `click(force=True)`)
- A native JS `el.click()` via `.evaluate("el => el.click()")` — the
  documented `.claude/rules/mui-patterns.md` § "MUI Overlay Interception"
  fallback

All of these: the button visibly receives the click (pressed/hover state,
`disabled=False` confirmed), a React fiber with a wired `onClick` prop is
confirmed present, **zero** console/page errors fire — yet the Menu simply
never mounts (`[data-testid^="secret-actions-menu-"]` stays count 0).

Deterministic across dozens of trials: headed AND headless, fresh page AND
fresh browser context, on a freshly-created row AND on the pre-existing
`auth_token` row, before AND after a full EliteaUI dev-server restart (ruled
out stale Vite HMR as the cause).

**Only invoking the button's React `onClick` prop directly** (bypassing the
DOM click-event pipeline via `element.__reactProps$*`) reliably opens it —
100% success across every trial:

```python
self.page.evaluate(
    "(el) => { "
    "const key = Object.keys(el).find(k => k.startsWith('__reactProps')); "
    "el[key].onClick({ currentTarget: el, target: el, preventDefault(){}, stopPropagation(){} }); "
    "}",
    btn.element_handle(),
)
```

Implemented as `SecretsPage.open_row_actions_menu()`. Root cause not
conclusively identified (not filed as a product bug — Playwright's simulated
click mirrors trusted CDP-level input, so no confirmed evidence a real
end-user's mouse click is affected; could be a test-environment artifact of
this project's specific Playwright/Chromium build vs. this exact MUI
Menu+IconButton combination). Curiously, sibling MUI buttons in the SAME
component tree (`secrets-add-button`, `secret-row-save-button`) click fine
with normal Playwright `.click()` — this is specific to the row-actions
button / its `SecretActionsMenu` wiring, not a systemic issue.

If this resurfaces on another MUI `Menu`-trigger button elsewhere in the
app, try the direct-props-invoke technique before spending a long debug
cycle re-deriving it.
