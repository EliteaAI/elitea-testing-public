---
name: DEV repro without secrets in context
description: Playwright MCP cannot log into Keycloak on DEV without printing the password — use a throwaway script on config.settings + the suite's page objects instead
type: feedback
aliases: [keycloak mcp login, dev repro script, secrets in context]
tags: [type/feedback, area/dev-env]
created: 2026-09-14
updated: 2026-09-14
---

## The constraint
`browser_type` needs the credential value IN the prompt, and CLAUDE.md forbids printing `.env.test`. So a
Playwright-MCP walk of `https://dev.elitea.ai` dead-ends at `input[name="username"]`.

## The route that works (#2282, 2026-09-14)
A throwaway script run from `automation/` with `../.venv/bin/python`: `from config import settings` (never
echoed), inline Keycloak fill, then `AgentAPI(browser_cookies=ctx.cookies())` for fixtures and the suite's page
objects (`AgentDetailPage`, `GenerateSkillModalPage`) for the flow — page objects that call `navigate()` resolve
`settings.app_base_url` (localhost), so `page.goto` the DEV URL directly and call the non-navigating methods.
Capture `page.on("response")` for the endpoint; print status/body/URL only. Same real system, no substitution.

## Two DEV gotchas met on the way
- The "Release 2.0.5 - Deployment" maintenance banner overlays the header and intercepts the Build-with-AI click —
  call `BasePage.dismiss_banner_if_present()` after each goto (pytest runs get this from conftest's
  `dismiss_banner_after_navigation`).
- Read `request.post_data` from a `page.on("request")` listener; it is `null` when read off the response later.

Related: [[project_briefing]] · [[ci_login_failure_becomes_skip]]
