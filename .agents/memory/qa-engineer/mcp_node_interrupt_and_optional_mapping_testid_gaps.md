---
name: MCP node Interrupt/Structured-output/optional-mapping testid gaps
description: BaseToolNode.jsx wires 4 testids Toolkit-nodeType-only; MCP passes undefined for them despite rendering the same fields
type: project
---

`BaseToolNode.jsx` (shared by the MCP and Toolkit pipeline node types) wires
`interruptAfterTestId`, `structuredOutputTestId`, `typeTestIdPrefix`
(Input-mapping row Type select) and `optionalHeadingTestId` (Input-mapping
"optional N" accordion) ONLY for `nodeType === Toolkit` — MCP nodes render
the exact same fields (confirmed live: MCP node shows Interrupt
before/after + Structured output switches, and would show an "optional N"
accordion for any tool with optional params) but get `undefined` for these
4 testids specifically. The other 5+ MCP-node fields (Toolkit/Tool/Input/
Output selects + their `-combobox` variants, Input-mapping Value fields,
Input-mapping "required N" heading) ARE wired for MCP (from earlier
ELITEA-1954/1955 `add-data-testid` passes) — only these 4 are the gap.

Fix is a 1-line-per-field widen of the existing
`nodeType === Toolkit ? ... : undefined` ternaries in `BaseToolNode.jsx`
(lines ~206-241) to also cover `nodeType === Mcp` — the prop plumbing
already exists generically in `InputMapping.jsx`/`CommonInterruptSettings.jsx`.

Also: all `pipeline-mcp-node-*`/`pipeline-toolkit-node-*` testids are
runtime-constructed via `` `${testIdPrefix}-toolkit-select` `` string
templates (`TEST_ID_PREFIX_BY_NODE_TYPE` map) — a literal bare-substring
`git grep` for the full testid string finds ZERO hits even when the testid
works live. Verify provenance via the constituent prefix
(`pipeline-mcp-node` / `pipeline-toolkit-node`) or the
`TEST_ID_PREFIX_BY_NODE_TYPE` mechanism name instead.

Full writeup: `test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`
Concrete Handles table + `_surface.md` § MCP node.
