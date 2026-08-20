---
name: Pipeline canvas Discard gated on Flow graph dirty too
description: pipeline-canvas-discard-button enables on Flow-graph edits (add-node), not just Formik form fields; reverts via client-side Redux reset with zero network calls.
type: reference
---

`PipelineEditor.jsx`'s header `Discard` button (`pipeline-canvas-discard-button`,
ELITEA-2076) is enabled by `totalDirty = isDirty || isYamlDirty`, NOT only the
Formik Name/Description fields ELITEA-2076's own AFS documented. `isYamlDirty`
comes from `EditorPanel`'s `useIsPipelineYamlCodeDirty()` hook via a
`setYamlDirty` prop — so adding/removing a node on the Flow Editor tab flips
it too, enabling the SAME header Discard button (no separate Flow-editor-local
Discard control exists).

`handleDiscard()` on confirm:
- `fileReaderEnhancerRef.current?.restoreValue(...)` — resets instructions text
- `dispatch(actions.resetPipeline())` + `dispatch(editorActions.resetPipelineEditor())`
  — reverts the FLOW GRAPH (nodes/edges), not just form fields
- Fires **zero** `POST`/`PUT` — purely client-side Redux reset, confirmed live
  via network capture (ELITEA-2078)

Page-object support already exists end-to-end, no new work needed for a
"dirty the flow graph then discard" case: `PipelineCanvasPage.is_discard_enabled()`
/ `.click_discard()` / `.confirm_discard()` (ELITEA-2076) work unchanged whether
the dirt came from the header form OR from `PipelineDetailPage.add_node()` /
`select_add_node_menu_item()` on the Flow tab. Confirmed live: node count/ids
revert to the exact pre-add state (`get_node_ids() == ["END"]`) after confirm.

Also confirmed live (ELITEA-2078): the Add Node menu's visible set is exactly
11 types — Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer,
Router, State modifier, Toolkit — source-traced to `AddNodeMenu.jsx`'s
`getVisibleNodeTypes()` filtering `FlowEditorConstants.PipelineNodeTypes` by
`DeprecatedConstants.DeprecatedOrInvisibleNode` (excludes Tool, Function,
Pipeline, Condition, Loop, LoopFromTool, End, Ghost, Default). Prefer the
testid-based `get_add_node_menu_items()`/`select_add_node_menu_item(internal_type)`
(ELITEA-2030) over the older raw-CSS `add_node(display_name)` helper in new tests.
