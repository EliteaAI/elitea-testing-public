---
name: Credential/toolkit create-form goto pitfalls (slow mount + beforeunload)
description: A direct goto to a schema-driven create form mounts seconds late, and a dirty one arms a native beforeunload dialog that blocks every later Playwright call.
type: feedback
aliases: [beforeunload dialog, create-ai-provider, toolkit-field-label-input not found, form mounts late, does not handle the modal state]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## Two pitfalls on any schema-driven create form (`/settings/create-ai-provider/<type>`, credential + toolkit forms)

Both hit live on 2026-08-29 while analysing ELITEA-2395/2396/2408/2409.

**1. The form mounts SECONDS after navigation.** The route resolves first, then
the toolkit schema is fetched, and only then do the `toolkit-field-*` inputs
exist. A `fill()` issued right after `goto` fails with
`"[data-testid=\"toolkit-field-label-input\"]" does not match any elements`.
Always wait on the first field, never on navigation alone.

**2. A dirty form arms a native `beforeunload` dialog.** Reloading or `goto`-ing
away mid-edit raises it, and every subsequent Playwright MCP call then errors
with `Tool "browser_evaluate" does not handle the modal state` until
`browser_handle_dialog` is called. Prefer leaving through the app (Save /
Cancel), or register a dialog handler up front. Cost one recovery turn.

Related: [[settings_ai_providers_llm_model_form]] — full handle inventory lives in
the committed digest `test-specs/settings-ai-providers/_surface.md`.
