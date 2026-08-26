---
name: Pipeline MCP-node execution — the tool-chip is the observable
description: Proving a pipeline MCP node actually ran the SELECTED tool needs chat-answer-tool-chip, not a non-empty answer
type: reference
aliases: [mcp node execution, chat-answer-tool-chip, pipeline tool chip, mcp pipeline run]
tags: [area/pipelines, area/mcp]
created: 2026-08-24
updated: 2026-08-24
---

## The observable

When a saved pipeline whose MCP node has a Toolkit + Tool is run from the embedded
chat, the assistant message contains:

- `chat-answer-thought-accordion` → **`chat-answer-tool-chip`** with text exactly
  `"{toolkit_name}: {tool_name} (MCP1)"` (e.g. `autotest_mcp_w05: ask_question (MCP1)`)
- `skill-test-last-response` — the real tool output

**Assert the chip, not just a non-empty answer.** A silent LLM-only fallback (MCP node
never invoked) still produces a plausible non-empty answer, so "response arrived" is
not evidence the MCP node ran the selected tool. The chip correlates the configured
toolkit+tool with the executed one.

`chat-answer-tool-chip` is on `origin/main` and wired on `ChatPage` /
`AgentDetailPage`; as of 2026-08-24 it is NOT on `PipelineDetailPage` — page-object
work only, no EliteaUI change.

Timing observed live (DeepWiki MCP, `ask_question`): ~11 s "Thought" + streaming,
~40 s end to end. Budget 180 s; wait on the last message's `chat-delete-button`
(response-complete marker), never a sleep.

## Two traps in the same flow

- **Enter does NOT send** in the embedded chat composer. Filling `chat-message-input`
  and pressing Enter leaves the text in the field and posts nothing —
  `chat-send-button` must be clicked. `PipelineDetailPage.send_message_in_embedded_chat()`
  already does this; do not "simplify" it to a keypress.
- **There is no `START` node** on the pipeline canvas. A fresh pipeline shows only
  `END`; "start" is the node's Trigger/entry-point property. The `X → END` edge is
  auto-created from the node's default `transition`. Case texts saying
  "connect START → X → END" are drift with nothing to drag.

Related: [[project_briefing]] · full handle map in `test-specs/pipelines/_surface.md`
§ MCP node — … ELITEA-1952/1953.
