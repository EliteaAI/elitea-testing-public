---
name: Pipeline canvas zoom-out collides with ReactFlow controls; YAML tab silently truncates long node YAML
description: ELITEA-2010 (Toolkit node) findings — a freshly-added node's default zoomed-out state can position lower fields under the ReactFlow Controls panel (fixed bottom-left), causing click interception that looks like a stale-overlay race but isn't; and the YAML tab's CodeMirror editor silently truncates long node YAML with zero reported scroll overflow (filed EliteaAI/elitea-testing-public#1025).
type: feedback
---

## Zoomed-out canvas collides with ReactFlow's own Controls panel

`test-specs/pipelines/_surface.md` already documents "canvas is heavily
zoomed-out by default" for LLM-node fields; ELITEA-2010 (Toolkit node) hit
the SAME root cause from a different angle and it's worth generalizing:

- A freshly-added node's lower fields (e.g. an Input-mapping row's Type
  select, several rows down the card) can render at a screen position that
  literally overlaps ReactFlow's own fixed bottom-left **Controls panel**
  (zoom in/out/fit-view buttons, `.react-flow__controls-*`, no testid —
  #579 third-party exception territory).
- Playwright's actionability retry loop on a `.click()` there looks
  EXACTLY like a transient-overlay race (retries cycling through different
  intercepting elements — first a still-open sibling dropdown's menu
  items, then a fading toast, then finally `react-flow__controls-fitview`)
  — don't reach for `force=True` first. Confirm with
  `document.elementFromPoint(cx, cy)` at the click target's center; if it
  resolves to a `react-flow__controls-*` button, it's the persistent
  zoom-panel collision, not a fading overlay.
- **Fix: zoom in before interacting**, per `_surface.md`'s existing
  guidance — but the existing `zoom_in()` page-object method blindly
  clicks without checking `disabled` state, wasting the full default
  action timeout (10s) per call once max zoom is reached. Added
  `PipelineDetailPage.zoom_in_up_to(times)` (additive sibling, checks
  `is_disabled()` before each click, stops early) — reuse this, not a bare
  loop of `zoom_in()`.
- `fit_view()` after zooming re-centers; call both right after
  `wait_for_node_on_canvas(...)`, before any field interaction below the
  Toolkit/Tool selects.

## YAML tab CodeMirror silently truncates long node YAML — EliteaAI/elitea-testing-public#1025

For a Toolkit node configured with a tool that has ~10 Input-mapping
params, the YAML tab's rendered content stops dead partway through
(confirmed: `.cm-line` count = 32, but the real document is 41 lines) —
and `.cm-scroller.scrollHeight === .cm-scroller.clientHeight` (both
`984px`), meaning **the editor itself believes there's nothing more to
scroll to**. This is NOT the standard "CodeMirror virtualizes long docs,
scroll to reveal more" case — scrolling programmatically (`scroller.
scrollTop = scroller.scrollHeight`) is a no-op here, confirmed live.

- Ground-truth check: fetch the pipeline via `PipelineAPI.get_pipeline()`
  and read `versions[0]["instructions"]` directly — this is complete and
  correct even when the UI tab isn't. Use this to confirm persistence
  independently of the YAML tab for any node with many optional params.
- `[data-testid="pipeline-yaml-lines"]` (referenced by
  `PipelineDetailPage.get_yaml_content()`'s primary per-line-join path)
  **does not exist anywhere in EliteaUI/src** — it has always silently
  fallen back to `yaml_editor.text_content()` (which also concatenates the
  gutter's line-number text, e.g. a leading `"99123456789..."` blob before
  the real content — cosmetic noise, harmless for simple substring checks
  on SHORT yaml, but confusing to debug). Didn't touch this shared method
  (other merged tests depend on its behavior for short YAML) — worth a
  dedicated fix-only pass someday.
- Filed EliteaAI/elitea-testing-public#1025; test asserts what genuinely
  renders (`type`, `fstring`, the literal mapping value) as hard asserts,
  and defers `tool`/`toolkit_name`/`output` to their own side-channel
  `allure.step` at the end (matching `test_agent_management.
  test_edit_agent_instructions`'s #538 deferred-known-defect shape) so the
  test goes RED only there, deterministically, 2/2 local runs.

## BaseToolNode.jsx generalization pattern (MCP + Toolkit node, shared component)

`BaseToolNode.jsx` gated ALL its testid props behind a single `isMcpNode`
boolean. Generalized to `nodeTestIdPrefix` (`'pipeline-mcp-node'` /
`'pipeline-toolkit-node'` / `undefined`) for the props BOTH node types'
existing tests exercise (Toolkit/Tool/Input/Output selects, required
Input-mapping heading) — but kept the two NET-NEW props
(`optionalHeadingTestId`, `typeTestIdPrefix`) gated on `isToolkitNode`
specifically, NOT the shared prefix, since no current MCP test exercises
them — broadening them to MCP too would've silently inflated the
presence-based coverage metric with untested MCP-node testids (canon
#511). If a future MCP case needs the optional-heading/Type-select
testids, broaden those two props' gate to `nodeTestIdPrefix` at that
point (their OWN test will then exercise the MCP side too).
