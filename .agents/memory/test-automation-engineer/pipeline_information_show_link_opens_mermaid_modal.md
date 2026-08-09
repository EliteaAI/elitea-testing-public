---
name: Pipeline Information "Show" link opens a Mermaid modal, not navigation
description: ApplicationInformation.jsx's pipeline "Show" link opens StyledShowContextModal (Mermaid diagram), no URL change; deterministic console defect #1368 on single-node pipelines.
type: project
---

`ApplicationInformation.jsx`'s Information section, when rendered with
`showPipeline` (pipeline detail page only), shows a "Pipeline: **Show**"
row. Clicking it does **not** navigate anywhere — it opens
`StyledShowContextModal` (`contextLabel="Pipeline"`, `renderContextAsMermaid`)
rendering the pipeline's `instructions` YAML as a Mermaid diagram. ELITEA-2056's
case text says "navigates to pipeline YAML or visual representation" — only the
"visual representation" branch is true, via a modal. Filed as a case-text
CLARIFICATION in the AFS, not a bug.

The "Show" link had no testid — added `pipeline-information-show-link`
(`EliteaAI/EliteaUI@22184211`, `automation/testids`).

The modal's Mermaid content resolves via the PRE-EXISTING
`chat-mermaid-diagram-svg-container` testid (hardcoded inside the shared
`MermaidDiagramOutput/DiagramOutput.jsx`, same component the chat surface
uses) — no new testid needed for the diagram itself, just duplicate the
`LocatorDescriptor` field into `PipelineDetailPage` (precedent: `copy-id`/
`copy-version-id`/`agent-information-section` are already duplicated the
same way between `AgentDetailPage` and `PipelineDetailPage`).

**Deterministic (2/2) console defect**: opening this modal on a single-node
pipeline throws `InvalidStateError: Failed to execute 'inverse' on
'SVGMatrix': The matrix is not invertible.` from `svg-pan-zoom`'s
`resetZoom` (`DiagramOutput.jsx:298 renderDiagram`). Diagram still renders
visually. Filed
[EliteaAI/elitea-testing-public#1368](https://github.com/EliteaAI/elitea-testing-public/issues/1368),
sibling of pre-existing `#1045` (same library, different call site — #1045
is the in-chat Mermaid canvas editor). Any future case opening this modal
on a minimal pipeline should expect it and soft-assert with
`# Known defect: #1368`, not assert zero console errors unscoped.

**Fix round (review, ELITEA-2056 PR #1369):** the spec originally asserted
`show_context_diagram_container.locator("svg").count() >= 1` — a raw
selector chained off a `LocatorDescriptor` field in a spec file, not
compliant. Mirrored `ChatPage`'s already-#579-sanctioned
`MERMAID_NODE = ".node"` class constant + `get_diagram_node_count()` onto
`PipelineDetailPage` instead. **Gotcha found while fixing:** the diagram
container becomes `visible` before Mermaid actually populates it with
`.node` elements — a `get_diagram_node_count()` call right after only the
container-visible wait raced to 0. `click_information_show_link()` now also
waits for `.locator(MERMAID_NODE).first` to reach `attached`, mirroring
`ChatPage.wait_for_diagram_rendered` (ELITEA-2088). Any other caller of
`show_context_diagram_container` in this modal should route through
`click_information_show_link()` rather than re-deriving the wait.
