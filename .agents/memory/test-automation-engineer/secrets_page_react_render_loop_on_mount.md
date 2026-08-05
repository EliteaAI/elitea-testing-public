---
name: Secrets page React render-loop defect fires on plain mount
description: SecretsContent.jsx triggers "Maximum update depth exceeded" on every /settings/secrets navigation, before any interaction — filed #1203, sibling of #538 not a dupe
type: feedback
---

## The defect (elitea-testing-public#1203)

Navigating to `/settings/secrets` (via `SecretsPage.navigate()` — plain
`page.goto()` + wait for the row) reliably triggers a React console warning
(17-46 occurrences observed per mount across runs):

```
Warning: Maximum update depth exceeded. This can happen when a component
calls setState inside useEffect, but useEffect either doesn't have a
dependency array, or one of the dependencies changes on every render.
```

Stack trace pins `SecretsContent.jsx`. Confirmed via a standalone repro
script (`page.goto()` + wait for `secret-row`, zero clicks/typing) — errors
are already present in `capture_console_errors()`'s buffer before any
interaction happens. 100% reproducible (3/3 across 2 full pytest runs + 1
isolated script) with a properly authenticated `page` fixture (proper
`auth_state`/DEV-token session).

**Sibling of #538** (Agent Instructions field — `Maximum update depth
exceeded` fires only on TYPING, not on navigation) — same warning class,
different trigger/component. Don't conflate: #538's isolation notes
explicitly say "does NOT fire on plain page navigation/load" — #1203 is the
opposite (fires on navigation alone, before typing). Different object +
different trigger = sibling, not duplicate, per the dedup rule.

**Gotcha — a raw unauthenticated Playwright script will NOT show this.** My
first repro attempt used a hand-rolled `sync_playwright()` script without
wiring `auth_state`/`VITE_DEV_TOKEN` and saw zero errors — misleading, since
that page never actually reached the authenticated Secrets view. Always
reproduce via the project's own `page` fixture (or an equivalent that wires
`auth_state`) before concluding "not reproducible" — an unauthenticated
diff can silently mask a defect that only manifests on the real data-loaded
page.

Soft-asserted via `soft_failures`/`pytest.fail()` (see
`agent_instructions_react_render_loop_quirk.md` for the generic pattern) —
filter unexpected console errors from the known signature so a genuinely
NEW error still hard-fails.

(from ELITEA-2336)
