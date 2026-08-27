---
name: Failed toolkit tool execution has no structural marker
description: Elitea renders a failed toolkit tool call identically to a successful one; only agent_tool_end.tool_output discriminates
type: reference
aliases: [toolkit error oracle, tool execution failed, agent_tool_end, ToolActionStatus.error, chat tool chip error]
tags: [area/chat, area/toolkits, type/oracle]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

Verified live 2026-08-27 (localhost:5173, EliteaUI `automation/testids` @ `0277bb28`),
6 runs: a GitHub toolkit whose PAT returns 401 and a Jira toolkit that succeeds
render through **byte-identical structure**.

Identical in both: answer-body testid (`skill-test-last-response` /
`chat-answer-content`), `chat-answer-thought-accordion`, `chat-answer-tool-chip`,
absence of any error testid or `data-*` state attribute, Socket.IO sequence
(`agent_tool_start` → `agent_tool_end`), and `response_metadata.finish_reason == "stop"`.
There is **no `agent_tool_error` event** and **no `socket_validation_error` frame**.

- `ApplicationAnswer.jsx` renders `<ErrorTrace>` only on `!!exception` — a
  *conversation-level* exception. A failed tool call is not one. `ErrorTrace` also
  carries **zero testids**.
- `ActionView.jsx` builds the tool chip from `toolkitType` + `showProgress` only;
  `action.status` is never read for its appearance. `ToolActionStatus.error`
  (`src/common/constants.js:970`) is consumed only by
  `ApplicationThinkView.jsx:546`'s HITL sub-agent classification.

## The only discriminator

`response_metadata.tool_output` on the `agent_tool_end` Socket.IO frame — the
toolkit's own string, not LLM prose. Reachable via
`ChatPage.capture_websocket_frames()` (enter BEFORE navigating).

- failure: `Failed to list branches: 401 {"message": "Bad credentials", ...}`
- success: `Found 6 projects:\n[{...}]`

Also visible in the tool modal (click `chat-answer-tool-chip` → OUTPUT pane), but
`ToolModal.jsx` has **no testids** and the chip is click-unstable (10 s timeouts).

## Why it matters

Never scan the chat message text for `"error"`. It is LLM prose wrapped around
arbitrary user data — a GitHub branch list legitimately contains `error`-bearing
branch names (this is issue #1817 / GHA run 32931571484), while three real 401
failures never contained the literal `"authorization error"` (the model writes
*"authentication error"*). Assert the **positive, anchored** shape of `tool_output`
instead.

Corollary trap: `chat_response_keywords` do NOT discriminate — the GitHub failure
narration says *"…when trying to list the **branches**…"*, satisfying
`["branch","found","repository"]`. Removing an error guard without replacing it
turns a false-RED into a false-GREEN.

Related: [[expired_github_token_is_test_data_not_identity]] · brief at
`test-specs/toolkits/lfix_toolkit_chat_error_oracle_ELITEA-1140.md`
