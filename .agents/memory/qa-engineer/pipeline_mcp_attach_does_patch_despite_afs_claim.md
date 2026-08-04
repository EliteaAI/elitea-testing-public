---
name: Pipeline MCP-attach DOES fire a persisting PATCH, despite an AFS claiming otherwise
description: ELITEA-2037's AFS said "pipeline Tools MCP-attach has no auto-persist, only GET calls" — contradicted by the implementation's own select_mcp_in_popper, which blocks on a PATCH /tool/prompt_lib/{project}/ 201 and is proven by the already-merged ELITEA-1955 sibling test using the identical wait in the identical pipeline context
type: feedback
---

## What happened

Reviewing PR #1150 (ELITEA-2037, `tests/2037-pipeline-mcp-node-fresh-attach`), the
AFS (`test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`)
states, in Test Steps step 4 and § Network Behavior:

> "the PIPELINE-level Tools attach does not auto-persist — no persistence
> request fires on attach (only GET .../toolkits/... / GET .../tools/...
> listing calls)"

But the implementation's Step 3 calls `PipelineDetailPage.select_mcp_in_popper()`
(`automation/pages/pipeline_detail_page.py:2730`), a **pre-existing** method
(from ELITEA-1955) that wraps the click in
`page.expect_response(... method == "PATCH" and status == 201 ...)` on
`/tool/prompt_lib/{project_id}/` — i.e. it hard-requires a PATCH 201 to
return at all; if none fired, the step would time out and the test would
fail, not silently pass.

The already-merged sibling `test_pipeline_mcp_node_empty_toolkit_before_attach.py`
(ELITEA-1955, `automation/base-merged`) calls the exact same method in the
exact same pipeline-Tools-attach context, at its own Step 8 — corroborating
that a PATCH really does fire on pipeline MCP-attach.

So the AFS's "no persistence request, only GET calls" claim is directly
contradicted by the very implementation that (per the PR body) went green.
The just-filed clarification issue #1149 also repeats this incorrect network
claim as supporting evidence (its "no MCP sub-tab" finding itself is still
valid and independent of this error).

## Lesson for next review / next analysis session

- **A network-behavior claim in an AFS is a first-class assertion, not
  color commentary — triangulate it against a sibling spec exercising the
  same endpoint before trusting it**, especially when a same-surface sibling
  case (ELITEA-1954/1955 here) already automated the identical popper/attach
  flow. `grep` the existing suite for the same page-object method the new
  test will call and check what network wait it already depends on.
- A page-object method's docstring citing "AFS § Network Behavior" as its
  own justification is not independent verification — if the CURRENT case's
  AFS disagrees with what the REUSED method actually depends on, that's the
  drift to catch, not confirmation.
- When an implementer reuses a pre-existing method whose behavior contradicts
  the AFS's own stated network finding, that's a mandatory "AFS amendments in
  the same PR" case (`.agents/testing.md` / reviewer-contract standing
  check) — silently reusing the method without reconciling the doc is
  `CHANGES_REQUESTED`.
