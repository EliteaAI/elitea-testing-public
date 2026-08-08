---
name: CustomHandle testId prop — not a #579 exception
description: ReactFlow node handles via CustomHandle.jsx forward testId to data-testid; a raw .react-flow__handle DOM query is not a valid #579 exception
type: feedback
---

## The trap

`.react-flow__handle` LOOKS like the same sanctioned #579 library-internal-DOM
class that `PipelineDetailPage.get_node_count()` legitimately uses for
`.react-flow__node` (the node container CSS class, which has no app-authored
testid hook). It is NOT the same case for connection **handles**.

`EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/CustomHandle.jsx`
(the wrapper every pipeline node type uses for its target/source connection
points) accepts a `testId` prop and forwards it straight to `data-testid` on
the underlying `<Handle>` (`CustomHandle.jsx:104-111`). That means a real
testid CAN always be placed on a handle — it's an app-owned hook, not
library-internal DOM. A raw `page.evaluate()` querying `.react-flow__handle`
(or any CSS-class handle count) is a #579 misclassification, exactly like the
MUI-`SingleSelect`-auto-id trap (see
`mui_simple_select_auto_id_is_not_a_579_exception.md`) — same root cause,
different component.

## Precedent already in the codebase

`NormalDecisionNode.jsx` already wires `testId="pipeline-decision-node-output-handle"`
/ `testId="pipeline-decision-node-default-output-handle"` on two of its three
`CustomHandle` calls (it needed to disambiguate two source handles). Its
`target` handle, and every OTHER node type's `CustomHandle` calls (LLM, Code,
Default, Printer as of ELITEA-2039 round 1, MCP, Agent, etc.) had NO `testId`
before ELITEA-2039 fix round 2 — this is untested ground, not "handles can't
carry testids."

## The fix pattern (ELITEA-2039 fix round 2, PR #1324)

1. Add `testId="pipeline-<node>-node-<target|source>-handle"` to the specific
   node type's `CustomHandle` call site(s) actually touched by the test
   (scope discipline — don't blanket-add to every node type).
2. Page object: a `LocatorDescriptor(testid=...)` field per handle, scoped
   page-wide under the same "single node instance on canvas" assumption the
   other Printer-node locators already use (unless the test genuinely has
   multiple same-type nodes, in which case scope under the node's
   `rf__node-{id}` testid container).
3. Rewrite any raw-DOM handle-count helper to sum `.count()` across the
   dedicated testid locators.
4. Add an explicit `.is_visible()` assertion on each handle locator — an
   aggregate count alone doesn't prove the count came from a testid rather
   than the old raw query; the regression guard needs the testid-scoped
   assertion.

## When you hit this again

Any AFS/implementation touching a pipeline node's ReactFlow connection
handles: check whether `CustomHandle.jsx`'s call site for that node type
already has `testId=` wired (grep the node's `.jsx` file for `CustomHandle`
and `testId`). If not, it's `add-data-testid` work on that specific node
type's call site — never a `.react-flow__handle` DOM query, and never a
blanket add across unrelated node types.
