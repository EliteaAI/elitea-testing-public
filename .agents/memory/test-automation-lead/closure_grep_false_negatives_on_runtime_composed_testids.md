---
name: Closure grep false negatives on runtime-composed testids
description: Worked example where every closure-record testid row said "not on main" and every one was wrong
type: reference
---

`.agents/workflow.md` § Closure record warns that stage-1 bare-substring grep
"cannot see runtime-composed testids at all". Here is the worked case, so the
next lead recognises the shape instead of writing a false row (#19's failure).

**ELITEA-2037 / #1776, 2026-08-26.** The documented two-stage grep reported:

```
pipeline-mcp-node-toolkit-select     main:no   testids:no
pipeline-mcp-node-tool-select        main:no   testids:no
pipeline-mcp-node-input-select       main:no   testids:no
pipeline-mcp-node-output-select      main:no   testids:no
pipeline-mcp-node-input-mapping-*    main:no   testids:no
agent-add-mcp-button                 main:YES  testids:YES
```

Every `no` was **wrong**. The real wiring, `origin/main`
`src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseToolNode.jsx`:

```jsx
const TEST_ID_PREFIX_BY_NODE_TYPE = {
  [FlowEditorConstants.PipelineNodeTypes.Mcp]: 'pipeline-mcp-node',
  [FlowEditorConstants.PipelineNodeTypes.Toolkit]: 'pipeline-toolkit-node',
};
const testIdPrefix = TEST_ID_PREFIX_BY_NODE_TYPE[nodeType];
data-testid={testIdPrefix ? `${testIdPrefix}-toolkit-select` : undefined}
```

No file contains the literal string, so no grep can ever match it.

**Tell.** All-`no` for one feature family while unrelated ids in the same list
say `YES` — that pattern means composition, not absence.

**What to do.** Grep the *suffix* (`-toolkit-select`), open the component, read the
prefix map, and cite the JSX in the closure record. If the test also passes against
a deployed env, say so — a deployed env serves `main`, so a green run there is a
stronger promotability oracle than the grep.
