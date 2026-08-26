---
name: Popup-opening flows — console capture and the surviving /{project_id} URL segment
description: Two gotchas for any Elitea spec whose flow opens a new tab (target="_blank" links)
type: feedback
aliases: [popup console errors, expect_page, new tab, project prefix, target blank, notification link]
tags: [area/playwright, area/elitea-routing]
created: 2026-08-26
updated: 2026-08-26
---

## Console capture must bind to the CONTEXT, not the page

`collect_console_errors(page)` (`automation/utils/console_errors.py`) binds
`page.on("console")`. When the flow's second half runs in a POPUP the listener never
sees it — the popup does not exist when the listener is bound. Use
`collect_console_errors(page.context)`: `BrowserContext.on("console")` covers every
page in the context, popups opened later included. Same for response monitoring —
`page.context.on("response", ...)` before the click catches the popup's own requests.

Verified 2026-08-26 on ELITEA-2261/2263 (`tests/ui/admin/test_notification_link_*.py`).

## The `/{project_id}` URL segment survives when no switch is needed

EliteaUI hrefs built by `resolveHref()` carry the entity's own `/{projectId}` prefix.
The project switcher consumes that segment **only when it actually has to switch
projects**. Measured 2026-08-26:

| Notification project | Selected project | Landing URL |
|---|---|---|
| 406 | 399 | `/chat/5883?name=Hello` — consumed |
| 399 | 399 | `/399/artifacts?bucket=…` — survives |

Any landing-path assertion must accept BOTH `{prefix}/<route>` and
`{prefix}/{project_id}/<route>` — exactly those two. Asserting only the stripped form
is a guaranteed red whenever the target happens to live in the selected project.
Cost one rerun.

Related: [[project_briefing]]
