---
name: Pipeline Custom node shares Toolkit node's component tree
description: DefaultNode.jsx (Custom/defaultType) reuses BaseToolNode.jsx's exact field set + testid-wiring props — no shared-component changes needed to testid it
type: feedback
---

`DefaultNode.jsx` renders both the `custom` and `defaultType` pipeline node
types (`FlowEditor.jsx`'s `nodeTypes` map). For `custom` it renders the
IDENTICAL component tree `BaseToolNode.jsx` uses for the Toolkit/MCP nodes:
`ToolSelect` → conditional `Tool` `SingleSelect` → `InputSelect` →
`OutputSelect` → `InputMapping` (Type+Value, REQUIRED/OPTIONAL accordions)
→ `CommonInterruptSettings`. All the testid-forwarding props
(`data-testid`/`dataTestId` on the selects, `valueTestIdPrefix`/
`typeTestIdPrefix`/`requiredHeadingTestId`/`optionalHeadingTestId` on
`InputMapping`, `interruptAfterTestId`/`structuredOutputTestId` on
`CommonInterruptSettings`) were ALREADY supported by these shared
components (proven by `BaseToolNode.jsx`'s own `TEST_ID_PREFIX_BY_NODE_TYPE`
map for Toolkit/MCP) — testid-ing a NEW node type sharing one of these
trees is a pure DefaultNode/BaseToolNode-call-site wiring exercise, zero
shared-component API changes, when the target node type is already in this
family. Only genuinely-unique node fields (Custom's own raw-JSON
`CustomNodeInput.jsx` editor) need a new prop — and even that reused an
existing generic mechanism (`Field.CodeMirrorEditor`'s `contentTestId`).

Precondition gotcha carries over too: Tool select + INPUT MAPPING sections
are absent from the DOM until a Toolkit (with `settings.selected_tools`
set) is attached to TOOLS and selected in the node — same two-stage reveal
already documented for the Toolkit (ELITEA-2010) and Router (ELITEA-2033)
node cases. Any future case for a node type sharing `BaseToolNode`/
`DefaultNode` will hit this same precondition; check the case text for it
before assuming "(none required)" test data is accurate.

Full worked example: `test-specs/pipelines/l2_pipeline-custom-node-configuration_ELITEA-2036.md`.
