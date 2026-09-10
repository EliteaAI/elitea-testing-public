---
name: ToolkitAPI list endpoint — two contradictory "confirmed" truths in the suite
description: Four merged MCP specs call list_all_toolkits() CONFIRMED-BROKEN (always empty); two toolkit specs use it as a passing oracle. Verify per surface, never cite either as settled.
type: feedback
aliases: [list_all_toolkits, list_toolkits, tools/prompt_lib empty, toolkit listing quirk]
tags: [area/toolkits, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

## The contradiction

`GET /elitea_core/tools/prompt_lib/{project}` (`ToolkitAPI.list_toolkits()` /
`list_all_toolkits()`) is documented **both ways** in merged, reviewed code:

- **"CONFIRMED BROKEN — always `{"rows": [], "total": 0}` regardless of params or
  auth method"** — `test_mcp_cancel_during_creation.py`, `test_mcp_delete_remote.py`,
  `test_mcp_edit_*.py` (four+ specs) and
  `.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md`
  (re-verified 2026-08-24). Those specs deliberately use a UI list check or a passive
  request observer instead, calling any absence assertion against it **vacuous**.
- **Working oracle** — `test_toolkit_creation_create_bucket_verify_list_files.py:169`
  (`params={"query": name}`) and, since #2123/PR #2159,
  `test_toolkit_parameterized.py` Step 9 (`assert match is not None`), which gated
  3x green on 2026-09-10.

Both cannot be unconditionally true. The likely discriminator is toolkit **type**
(MCP-created toolkits absent from the list) or params, not auth — but nobody has
isolated it.

## What to do about it as a reviewer or implementer

- **Never cite either claim as settled** for a new spec on this surface — it is the
  § precedent-is-not-authority case in its purest form: two merged neighbours,
  opposite conclusions.
- A **presence** assertion against the listing is safe-ish (it reds loudly if the
  endpoint is empty). An **absence** assertion against it is vacuous — block it.
- The quirk-immune read-back is `GET /elitea_core/tool/prompt_lib/{project}/{id}`
  (singular `tool`), which the memory entry above confirms works even when listing
  does not. Prefer it when the id is already in hand from a create response.
