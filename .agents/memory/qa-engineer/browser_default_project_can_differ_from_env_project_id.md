---
name: Persistent MCP browser's active project can differ from ELITEA_PROJECT_ID
description: A persistent Playwright MCP profile can default to a different project than .env.test — API-seeded test data lands invisible until you confirm/select the matching project in the UI first
type: feedback
---

## Context

Found during ELITEA-2177/2178/2465 analyst cluster pass (chat conversation
starters), localhost:5173.

## Finding

`.env.test`'s `ELITEA_PROJECT_ID=399` (project `Private`) is the config
default automation fixtures target — but the Playwright MCP browser's
persistent profile can independently be sitting on a DIFFERENT active
project (this session: 471, "Elitea Testing Team") carried over from
whatever it last navigated to. Confirmed via the sidebar's project-selector
textbox and via network capture:
`GET .../applications/prompt_lib/471?...` vs `.../399?...` return genuinely
different agent lists.

Consequence: an agent created via `AgentAPI`/Bearer-token calls against
project 399 (the config default) was **invisible** in the live UI's own
"+ → Agents" composer search until the project switcher was used to select
"Private" (399) to match. The `participants`-add endpoint also targets the
CONVERSATION's project (`.../participants/prompt_lib/{conv_project}/{conv_id}`),
so a cross-project mismatch between where you seeded data and where the
browser/conversation actually lives silently produces "agent not found in
search" — not an error, just an empty result that looks like the agent
wasn't created at all.

## For future sessions

Before seeding test data via an API client for a LIVE UI verification step
(not just standalone API-only checks), confirm the browser session's actual
active project first — read the sidebar's project-id textbox (or the
project-selector's `data-testid="select-option-{project_id}"` value), don't
assume `${ELITEA_PROJECT_ID}` is what a persistent local browser profile is
currently scoped to. If it doesn't match, either force-select the intended
project via the UI switcher before seeding, or seed against whichever
project the browser is actually on.
