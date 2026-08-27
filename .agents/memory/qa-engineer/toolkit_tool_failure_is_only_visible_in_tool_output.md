---
name: A failed toolkit tool execution is invisible everywhere except agent_tool_end.tool_output
description: Success and failure share DOM, testids, event sequence, finish_reason and meta.is_error — only tool_output differs
type: reference
aliases: [agent_tool_end, tool_output, toolkit failure oracle, ToolActionStatus.error, chat_message_sync meta.is_error]
tags: [area/toolkits, area/chat, type/oracle]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

Verified at the **frame** level 2026-08-27 (ELITEA-1140 / #1817), across a real 401
failure and two real successes (github anonymous, jira):

- The `agent_tool_end` frame's recursive key-path set is **identical** on success and
  failure. `finish_reason == "stop"` on both. `content` duplicates `tool_output`.
- An exhaustive scan of **every key path of every frame** for
  `status|error|is_error|failed|success|exception|severity|level` finds exactly two:
  `chat_message_sync.meta.error` and `.meta.is_error` — and on a **genuine 401** they
  read `""` and `false`, byte-identical to a success. That channel is
  *conversation-level* (the `exception` gating `ErrorTrace` in
  `ApplicationAnswer.jsx:810`); a failed tool call never raises it.
- The event sequence around the call is identical too (`agent_llm_end` →
  `agent_tool_start` → `agent_tool_end` → `agent_llm_start` → chunks).

**Only `response_metadata.tool_output` discriminates.** Assert it POSITIVELY and
ANCHORED, per toolkit — never a negative scan for "error", which matches this repo's
own branch names.

## Two near-misses that are NOT oracles

- **frame count** — driven by `agent_llm_chunk` count = answer length; a jira success
  (32) came in *lower* than a github failure (34).
- **tool duration** (`timestamp_finish - timestamp_start`) — 0.23 s failure vs 2.26 s
  success is a latency heuristic, not a contract.

## Captured shapes (real, not fabricated)

| toolkit | outcome | `tool_output` head |
|---|---|---|
| github | success | `[{"name": "aqa/main-release-2.0.5", "protected": false}, ...]` — a JSON array |
| github | 401 | `Failed to list branches: 401 {"message": "Bad credentials", ...}` |
| jira | success | `Found 6 projects:\n[{'id': ...}]` |

⚠️ **The chat message text is NOT the tool output.** The LLM narrates it in fresh prose
each run — an earlier pass inferred `^Branches in \S+:` from CI *chat text* and it was
refuted by the real `tool_output`. Never derive a `tool_output` pattern from narration.

Related: [[github_anonymous_credential_unblocks_success_capture]]
