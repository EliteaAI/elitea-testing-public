---
name: A brand-new testid can be missing on the FIRST test run after the JSX edit
description: Vite dev server served the pre-edit module to the first fresh page load; identical re-run passed — re-run once before debugging the JSX
type: feedback
aliases: [testid not found, HMR stale, vite stale module, first run fails after add-data-testid]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## What happened (ELITEA-2251, 2026-08-24)

Added `{sectionTestId}-loading` to `ConfigurationSection.jsx` on `automation/testids`,
committed + pushed, then ran the new spec. It failed: `get_by_test_id(
"ai-providers-section-llms-loading")` not found — although the failure's own aria
snapshot showed all 7 `Loading...` nodes rendered, and
`curl http://localhost:5173/src/.../ConfigurationSection.jsx` showed the *transformed*
module already carrying the attribute.

The **identical re-run passed** (6.4 s, 0 reruns). So the first fresh page load after
the edit got the pre-edit module from the running dev server; nothing about the JSX,
the prop threading, or MUI prop-forwarding was wrong.

## Rule

If a testid you JUST added is "not found" on the first run after adding it, **re-run
once** before debugging the JSX, restarting the dev server, or doubting prop
forwarding. Only if the second run fails identically is it a real wiring problem —
then check the served transform with `curl` (it is authoritative for what the server
has, not for what the browser already fetched).
