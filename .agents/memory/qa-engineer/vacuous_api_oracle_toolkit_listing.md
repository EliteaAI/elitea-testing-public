---
name: Vacuous API oracle — toolkit listing always returns empty
description: list_all_toolkits() returns [] on this env, so any absence assertion or pre-flight guard built on it can never fail — check it at review
type: feedback
aliases: [list_all_toolkits, vacuous assertion, absence oracle, pre-flight guard, ELITEA-1960]
tags: [area/mcp, type/review-check]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`ToolkitAPI.list_all_toolkits()` / `list_toolkits()` returns `{"rows": [], "total": 0}`
on this environment regardless of params or auth method (Bearer AND cookie) — a
confirmed environment quirk, documented in
`.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md`
and in four merged MCP specs (`test_mcp_delete_remote.py:53`,
`test_mcp_edit_name.py:57`, `test_mcp_edit_timeout_cache_ttl.py:179`, …).

**Consequence for review:** any assertion of the shape
`assert NAME not in [t["name"] for t in toolkit_api.list_all_toolkits()]` is
**vacuously true** — it can never fail, so it proves nothing while reading like an
independent server-side oracle. Same for a "pre-flight guard" that asserts a named
toolkit does not pre-exist: it never fires, so a fixed-literal fixture name it was
meant to protect is in fact unprotected.

Caught in ELITEA-1960 (PR #1748), where both shapes shipped *and* the surface digest
recorded "pre-flight guard is worth keeping" as a verified fact.

## The review question

For every API-based *absence* assertion ask: **has this listing path ever returned a
non-empty result in this suite?** If the only uses are absence checks, it is
unfalsifiable. The working substitutes on this project:

- UI list discovery (`McpListPage.has_any_mcp()` / `get_card_names()`) — the
  precedent `test_mcp_delete_remote.py` adopted for exactly this reason.
- A passive `page.on("request")` observer proving no mutating request fired.
- `GET tool/prompt_lib/{project}/{id}` by id (that endpoint works fine).

Generalisation: an assertion whose *negative* branch is unreachable in the current
environment is not evidence — a green run says nothing about it, and no gate,
however many times it runs, can see the difference.
