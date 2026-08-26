---
name: Legacy add_toolkit_participant silently leaves the toolkit unattached
description: The name-search attach flow can no-op without erroring; the model then hallucinates the tool result and any tool-dependent assertion fails misleadingly
type: feedback
aliases: [add_toolkit_participant, toolkit participant attach, hallucinated tool result, plus menu toolkits]
tags: [area/chat, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## What happened (ELITEA-2211, 2026-08-27)

`ChatPage.add_toolkit_participant(toolkit_name)` types into the plus-menu's
**non-debounced** search field and clicks `li[role="menuitem"]:has-text(name[:15])`.first.
In 3 of 3 automated runs it left the toolkit **UNATTACHED** — no exception, no timeout.

The symptom was NOT "attach failed". It was: the model answered
*"The file ... has been successfully deleted"* while `ArtifactAPI.list_bucket_files`
showed the file still present, no `chat-answer-tool-chip` rendered, and the HITL
Sensitive Action card never appeared. I spent ~30 min suspecting backend config
caching before checking the bucket.

## The fix, and the tell

Use `add_toolkit_participant_via_slash_menu(project_id, toolkit_id)` (resolves the row
by its dynamic testid — also the locator-policy-compliant shape), then
`close_plus_menu_popper()`, then ASSERT `is_participants_badge_visible(section="toolkits")`
before sending. `artifact_toolkit` already yields `project_id`.

**Tell:** a response that claims a tool succeeded with **no tool chip** means no tool call
happened. Verify the backend side effect (or the chip) before believing the prose — and
before blaming the environment.

`test-specs/chat-interface/_surface.md` already said the legacy flow is "NOT reusable" for
the toggle-switch Toolkits rows; four merged specs outside ELITEA-2211's module still call it
(`test_direct_toolkit_call_complete_flow.py` ×2, `test_toolkit_parameterized.py`,
`test_github_toolkit.py`) — suite-health debt, flagged to the lead.

Related: [[afs_is_a_work_order_not_gospel]]
