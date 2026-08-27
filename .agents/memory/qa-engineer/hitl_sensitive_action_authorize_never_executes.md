---
name: Chat HITL Authorize closes the card but never executes the tool
description: Sensitive-action Authorize is a silent no-op on DEV — card closes, tool never runs, no error (#1834)
type: project
aliases: [sensitive action authorize, HITL authorize, chat guardrails approve, "#1834"]
tags: [area/chat, area/guardrails, type/defect]
created: 2026-08-27
updated: 2026-08-27
---

## The defect (#1834, ELITEA-2212, found 2026-08-27)

With `sensitive_tools: {"artifact": ["delete_file"]}` set, the Sensitive Action Authorization
card renders correctly and **Authorize closes it in 0.1 s** — then nothing happens. The tool
never executes (file still in the bucket after 90 s, backend-verified), no model chip renders,
the assistant turn ends as bare `Thought for less than a second`, persists **empty** after
reload, and the app keeps firing `beforeunload` as if a response were in flight.
**Zero console errors, zero failed HTTP requests.** Deterministic 4/4 across two harnesses.

Control: same toolkit + message with guardrails off completes normally and renders
`Anthropic Claude 4.5 Sonnet` in the model chip. So the tool and the toolkit are fine — only
the HITL approve/resume path is broken.

## Three observation traps this flow sets

1. **The tool chip is NOT execution evidence.** `chat-answer-tool-chip`
   (`{toolkit}: delete_file`) renders **while the card is still pending**, before any click.
   Asserting it "proves the tool ran" is a guaranteed false green. The **model chip** is the
   turn-completed signal.
2. **The Playwright MCP browser swallows the first click on every card action** (Authorize
   *and* Block, 4/4) in its long-lived context, while clean Playwright contexts work
   first-click (3/3). Do not sanity-check this flow in MCP — and do not file that as a bug.
3. **A silently unattached toolkit looks like a product bug.** If the "Toolkits in this
   conversation" badge is not asserted before sending, the LLM answers *"has been successfully
   deleted"* with the file untouched, no tool chip, and no card. Reproduced twice.

## Precondition (works, no Admin UI)

`PUT {api}/admin/plugin_config_values/administration/guardrails` with the **full** values
object, `sensitive_tools` mutated additively → `200 {"saved": true, "requires_restart": []}`,
live immediately. Restore the captured original verbatim in a `finally`. Org-wide, toolkit-TYPE
scoped.

Related: [[expect_poll_is_not_a_python_playwright_api]]
