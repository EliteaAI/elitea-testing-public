---
name: Toolkit tool_output shapes must be captured per toolkit, never inferred
description: Each Elitea toolkit's success AND failure tool_output shape is unrelated to its siblings' — and drifts with the SDK; infer one and you ship a wrong oracle
type: feedback
aliases: [tool_output shape, toolkit oracle capture, agent_tool_end capture, EL-6532 json drift]
tags: [area/toolkits, area/oracle]
created: 2026-08-27
updated: 2026-09-18
---

## Why capture-only

ELITEA-1140 / #1817 proved it twice (github's `^Branches in \S+:` was LLM narration; confluence's
failure is prose, not github's `Failed to list …: 401`). #2362 added a third lesson: **shapes drift
with the SDK** — EliteaAI/elitea-sdk@fe3377278 (EL-6532, 2026-09-07) switched ~45 tool methods from
Python-repr / prose to JSON, and Jira's `list_projects` went from `Found <n> projects:\n[{'id': …}]`
to a pretty-printed JSON array. A capture-derived pattern is only as current as its capture date —
keep the date in the config comment and re-capture on drift, never "fix" by loosening.

## Shapes as of 2026-09-18 (all real calls, localhost:5173 → DEV)

| toolkit | success | failure |
|---|---|---|
| github `list_branches_in_repo` | `[{"name": …, "protected": false}, …]` | `Failed to list branches: 401 {...}` (inside tool_output) |
| jira `list_projects` | `[\n  {\n    "id": "10165",\n    "key": "AIPSDLC",\n    "name": …` | **no `list_projects` frame at all** — see below |
| confluence `list_pages_with_label` | `[]` or `[{"id": …, "title": …}]` | `Tool execution error!\n\nPossible root causes: …` |

## Jira rejects credentials at toolkit CONSTRUCTION

`JiraClient.__init__ → _validate_credentials → ToolException: Authentication failed: Invalid username
or API key.` fires while the agent builds its tools, so the tool never runs. Wire: `agent_tool_start`,
`agent_tool_end` with `tool_name: "Agent Exception Stacktrace"` and **no `tool_output` key** (traceback
in `content`), then `agent_exception` (`human_readable: "An unexpected error occurred…"`). The chat
spec dies at Step 4 (`AI response did not complete … Copy button appeared but content was transient`)
before Tier 1 even reports `0 of N`. So for Jira the success/failure discrimination is **Tier 1**
(frame absence), not the Tier-2 pattern — don't loosen Tier 1 to "fix" a Jira `0 of N`.

## How to capture (~40 s, no tooling)

Temp-edit the spec (never commit): inside `capture_socketio_frames`, wrap Step 4 in `try/finally`
and dump in the **finally** — a failing turn otherwise dies before a dump placed at Step 5:
```python
finally:
    import json as _json, os as _os
    if _os.environ.get("DUMP"): _json.dump(list(frames), open(_os.environ["DUMP"], "w"), indent=2)
```
Run: `cd automation && DUMP=/tmp/f.json HEADLESS=true ../.venv/bin/pytest "tests/ui/toolkits/test_toolkit_parameterized.py::TestChatWithToolkit::test_chat_with_toolkit[<tk>]" -q -p no:cacheprovider --reruns 0`
Failure capture: in `managed_credential`, `if os.environ.get("BOGUS_KEY"): token += "-INVALID"` —
the remote really rejects it (observation, not simulation); the fixture deletes the credential itself.
Store the WHOLE frame under `tests/unit/data/elitea1140_agent_tool_end_<tk>_<kind>.json` (run_id +
timestamps = provenance) and derive the pattern from it, anchored, naming only observed keys.

## Cross-toolkit distinctness is a proxy, not the property

Since EL-6532 github's and confluence's patterns admit Jira's array (it has `"id"` first and `"name"`
later). Harmless: Tier 1 pins the frame to tool + toolkit display name first. The invariant that
matters is *every shipped pattern rejects every captured failure payload* — the unit suite's 12-cell
matrix. Never tighten a sibling row without a capture of ITS output.

Related: [[toolkit_tool_success_oracle_on_agent_tool_end]] · [[websocket_frame_collector_not_on_main]]
