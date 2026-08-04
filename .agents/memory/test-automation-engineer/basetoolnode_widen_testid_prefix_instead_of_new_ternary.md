---
name: BaseToolNode.jsx widen testIdPrefix instead of a new node-type ternary
description: When a Toolkit-only-gated testid prop in BaseToolNode.jsx (or CommonInterruptSettings/InputMapping) needs to also cover MCP once a new test exercises it, widen the ternary to `testIdPrefix` truthiness rather than adding a second node-type branch
type: feedback
---

`BaseToolNode.jsx` (EliteaUI, `src/[fsd]/features/pipelines/flow-editor/ui/nodes/`)
shares one component across the MCP and Toolkit pipeline nodes, keyed by a
`TEST_ID_PREFIX_BY_NODE_TYPE` map (`{Mcp: 'pipeline-mcp-node', Toolkit:
'pipeline-toolkit-node'}`). Several sub-props (`interruptAfterTestId`,
`structuredOutputTestId`, `typeTestIdPrefix`, `optionalHeadingTestId`) were
originally wired ONLY for the Toolkit node (ELITEA-2010), each via its own
explicit `nodeType === FlowEditorConstants.PipelineNodeTypes.Toolkit ? ... :
undefined` ternary — a deliberate scoping choice (comment: "only the node
type this PR's test exercises gets a testid") to keep testid presence ==
tested per `.agents/testing.md` § Locator policy.

**When a later case (e.g. ELITEA-2037) needs that same prop for the MCP node
too**, the correct edit is NOT a second `nodeType === Mcp ? ... :` branch
stacked next to the Toolkit one — it's collapsing to `testIdPrefix ? ... :
undefined`, since `testIdPrefix` already resolves to a real value for
*exactly* the node types present in `TEST_ID_PREFIX_BY_NODE_TYPE` (today:
Mcp + Toolkit) and `undefined` for every other node type sharing the
component (Agent/Function/etc. stay untagged automatically). This is less
code, keeps the "only referenced node types get a testid" invariant intact
without hand-maintaining N per-prop ternaries, and matches how the sibling
`toolkit-select`/`tool-select`/`input-select`/`output-select` props already
use `testIdPrefix` directly (only the interrupt/type/optional props still
had the old Toolkit-only ternary at the time ELITEA-2037 touched them).

**Do NOT widen `typeTestIdPrefix` / `optionalHeadingTestId` reflexively**
just because you're in the file — only widen the specific props your new
test's assertions actually reference on its executed code path (canon #511).
ELITEA-2037 widened `interruptAfterTestId`/`structuredOutputTestId` (both
asserted) but left `typeTestIdPrefix`/`optionalHeadingTestId` alone (neither
touched — Type stayed at its default, the tool used had 0 optional params).

Commit precedent: `EliteaAI/EliteaUI@00768a44` on `automation/testids`.
