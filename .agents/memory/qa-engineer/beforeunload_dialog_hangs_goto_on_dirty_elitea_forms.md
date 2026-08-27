---
name: beforeunload dialog hangs page.goto() on any dirty Elitea form
description: A dirtied credential / AI-provider form raises a native beforeunload dialog; a bare page.goto() blocks until it is handled — looks like an app hang, costs a 60s timeout each time.
type: feedback
aliases: [beforeunload, unsaved changes dialog, goto timeout, navigation hangs, dirty form]
tags: [area/credentials, area/settings, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The symptom

`mcp__playwright__browser_navigate` (and a plain `page.goto()`) fails with
`TimeoutError: navigating to "<url>", waiting until "domcontentloaded"` — with **no
error in the app**. The page never changes. Hit twice in one session (ELITEA-2345,
2026-08-27), 60 s each.

## The cause

Elitea's credential form (`/credentials/create-credential/<type>`,
`/credentials/all/<id>`) and AI-provider form (`/settings/create-ai-provider/<type>`)
register a `beforeunload` handler once the form is **dirty**. Merely flipping the
`SecretField` mode toggle (`toolkit-field-<key>-input-toggle-secret`) dirties it — no
typing required. The browser raises a native dialog and Playwright blocks on it.

Playwright MCP reports it as
`Modal state: ["beforeunload" dialog with message ""]: can be handled by browser_handle_dialog`
— but only when a *subsequent* tool call runs, so the navigation call itself just looks hung.

## What to do

- Live exploration: call `browser_handle_dialog(accept=true)` after the timeout, then
  continue — the navigation completes.
- In a spec: register `page.on("dialog", lambda d: d.accept())` before leaving any form
  you touched, or click the form's own discard control
  (`credential-form-discard-button`) first.

Do NOT treat the timeout as a product hang or a flaky route — it is a real, deliberate
guard.

Related: [[priority_marker_drift_afs_vs_pytest_mark]]
