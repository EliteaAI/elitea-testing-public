---
name: Support Assistant context payload (support_predict frame)
description: The widget ships project/page/entity context on the outbound socket frame — the honest oracle for any "assistant knows X" case
type: reference
aliases: [support_assistant_context, support_predict, assistant page context, assistant project context]
tags: [area/support-assistant, type/handle]
created: 2026-08-22
updated: 2026-08-22
---

## What it is

EliteaUI builds the assistant's context client-side and hands it to the widget as a prop; the
widget emits it with every message on its Socket.IO connection.

- Builder: `EliteaUI/src/[fsd]/widgets/support-assistant/lib/hooks/useAssistantContext.hooks.js`
- Prop hand-off: `EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:43`
- Type: `elitea_assistant/src/lib/types/assistant.types.ts:4` (`TSupportAssistantContext`)
- Emit: `elitea_assistant/src/lib/hooks/chat.hook.ts:527`

Event name is **`support_predict`**, not `predict`. Frame: `42["support_predict",{…,"support_assistant_context":{…}}]`.
`chat_enter_room` carries the assistant's OWN deployment project (536), which is not in the user's
selector list — the inequality with `support_assistant_context.project_id` is the mechanical form of
"not the internal deployment project".

Fields: `project_id`, `project_name`, `current_page`, `meta.browser` always; entity fields per
`pageType`. `filterDefined` drops undefined keys — always `ctx.get(...)`. `current_entity_name`
comes from the RTK-Query cache, so the detail query must have resolved before sending.

## Why it matters

It is a **system-produced** observable, captured passively (`page.on("websocket")` +
`ws.on("framesent")`, registered before the first navigation). That makes "the assistant knows the
current X" testable deterministically without mocking the LLM: assert the frame against live UI
state, then assert the LLM reply against values read out of the frame.

Related: [[support_assistant_reply_ready_signal]]
