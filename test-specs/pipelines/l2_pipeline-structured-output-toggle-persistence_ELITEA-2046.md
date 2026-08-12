# Test Case: Pipeline — Structured Output Toggle Persistence

## Metadata
- **TMS ID**: ELITEA-2046
- **Linked Story**: none
- **Priority**: l2 (source TMS case: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline with a node supporting structured output exists — created by this
  case's own step 1 (fresh empty pipeline via the `pipeline_id` fixture + an LLM
  node added via the canvas "+" menu, same convention as
  `l2_llm-node-system-task-chat-history-config_ELITEA-2004.md`). The case text
  lists "LLM, Code, Toolkit, etc." as example node types carrying the toggle;
  this AFS automates the LLM node as the representative instance — its
  `pipeline-llm-node-structured-output-toggle` is wired identically to the
  Code/MCP/Toolkit/Custom nodes' own toggles (same shared
  `CommonInterruptSettings.jsx` component, confirmed via source and the
  existing pipelines digest), so one node type exercises the shared
  persistence mechanism the case is actually about. Choosing a specific node
  type is a disposition, not scope narrowing — see Coverage Map row 1.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- `pipeline_id` fixture (fresh, empty pipeline; deleted at test end).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's active browser project was
  "Private" (id 399), matching `.env.test`.

## Test Steps
1. Open a pipeline with a node supporting structured output (LLM node).
   **Expected**: pipeline is open with the node visible. Confirmed live via
   `pipeline_id` fixture + `add_node("LLM")` + `wait_for_node_on_canvas("llm")`
   — identical mechanism to ELITEA-2004/ELITEA-2045.
2. Verify "Structured output" switch is disabled by default.
   **Expected**: toggle shows disabled (unchecked) state. Confirmed live this
   session on a freshly-added LLM node, before any interaction:
   `pipeline-llm-node-structured-output-toggle`'s inner `<input>` reports
   `checked === false`.
3. Toggle to enabled (checked) — save — reload — verify switch remains checked.
   **Expected**: after reload, Structured output switch is enabled. Confirmed
   live this session end-to-end: click → `checked === true` →
   `save_and_wait_for_update()` → `201 Created` → full page reload (navigate
   to the canonical pipeline URL) → toggle re-queried, still `checked ===
   true` (also independently confirmed via the accessibility tree:
   `switch "Structured output" [checked]`).
4. Toggle to disabled (unchecked) — save — reload — verify switch remains
   unchecked.
   **Expected**: after reload, Structured output switch is disabled.
   Confirmed live this session, same mechanism as step 3 in reverse: click →
   `checked === false` → save → `201 Created` → full page reload → toggle
   re-queried, still `checked === false`.
5. Verify in YAML: `structured_output` field toggles between `true`/`false`.
   **Expected**: YAML shows `structured_output: true` when enabled, `false`
   when disabled. Confirmed live this session via the on-screen
   `pipeline-yaml-editor` tab directly (this pipeline's YAML is short — 19
   lines — well under the ~32-34-line truncation threshold documented for
   `EliteaAI/elitea-testing-public#1025`, so the on-screen tab is safe to
   read here, unlike ELITEA-2045's 40-line document): after the step-4
   disabled+save+reload cycle, the tab rendered `structured_output: false`;
   after re-enabling+saving, it rendered `structured_output: true` — both
   read directly off `.cm-content` text, no truncation observed in either
   state.

## Expected Final State
The LLM node's Structured output toggle starts disabled by default, and both
directions of the enable/disable → save → reload cycle correctly persist —
the on-screen state and the persisted YAML's `structured_output` field agree
at every checkpoint (`false` initially, `true` after enabling, `false` again
after disabling).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline with a node supporting structured output (LLM, Code, Toolkit, etc.) | Pipeline open, node visible | step 1 | step 1 | asserted — **node-type disposition**: LLM chosen as the representative instance (see Preconditions); the toggle is wired via the same shared `CommonInterruptSettings.jsx` component across all listed node types, so this is not a scope reduction, it is a representative-instance choice |
| 2 Verify Structured output switch disabled by default | Shows disabled state | step 2 | step 2 | asserted |
| 3 Toggle enabled → save → reload → verify still checked | Enabled after reload | step 3 | step 3 | asserted |
| 4 Toggle disabled → save → reload → verify still unchecked | Disabled after reload | step 4 | step 4 | asserted |
| 5 Verify in YAML: structured_output toggles true/false | YAML matches toggle state both directions | step 5 | step 5 | asserted — this pipeline's YAML document is short enough that the on-screen `pipeline-yaml-editor` tab is safe to read directly (confirmed live, no truncation at 19 lines); unlike ELITEA-2045's 40-line document, no `pipeline_api.get_pipeline()` workaround is needed here |

### Axis 2 — Assertions beyond the case

- No unexpected console errors across the full flow (node add, toggle
  clicks, both saves, both reloads, both YAML-tab reads) — *added: this is
  the standing convention for every pipeline-node-configuration case in this
  family (ELITEA-2004/2009/2035/2036/2039/2045), and a save/reload
  regression is exactly the kind of silent breakage this case exists to
  catch.*
- The pipeline's URL is captured before the first reload and reused for
  both reloads (a bare `/pipelines/all/{id}` with no query params 404s per
  the ELITEA-1954 AFS Known Defects, already documented in every sibling
  reload-based case in this family) — *added: reload mechanics are a
  first-class part of "survives save + reload", not an incidental detail.*

## Cleanup
1. Delete the pipeline via `pipeline_id` fixture teardown (automatic).

## Concrete Handles (discovered during exploration — ALL PRE-EXISTING, zero new testids needed)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| LLM node Structured output toggle | `pipeline-llm-node-structured-output-toggle` | **on-`automation/testids` only**, reused unmodified from ELITEA-2004/2045 — already wired as `PipelineDetailPage.llm_node_structured_output_toggle`. Confirmed live this session: default unchecked; `click()` toggles `checked` both directions; state survives save+reload both directions. | none needed |
| Save button | `agent-save-button` | reused unmodified, already wired as `PipelineDetailPage.save_and_wait_for_update()`. | none needed |
| Pipeline YAML tab | `pipeline-yaml-editor` (CodeMirror `.cm-content`) | reused unmodified, already wired as `PipelineDetailPage.switch_to_yaml_view()` / `.get_yaml_content()` (per `test_pipeline_yaml_editor_invalid_syntax.py` / `test_pipeline_llm_structured_output_state_variables.py` precedent). Safe to read directly here — this pipeline's YAML is short (19 lines), well under the `#1025` truncation threshold (~32-34 lines) confirmed live this session (no truncation observed reading both the `structured_output: true` and `structured_output: false` states). | none needed |
| Canvas node add (LLM) | `pipeline-add-node-button`, `pipeline-add-node-menu-item-llm` | reused unmodified, already wired as `PipelineDetailPage.add_node("LLM")`. | none needed |

## Network Behavior
- `PUT /elitea_core/application/prompt_lib/{project}/{id}` — fires on Save,
  `201 Created`, confirmed live for both the enable and the disable save
  (two separate saves in this test). No other endpoint involved — this case
  never executes the pipeline (unlike ELITEA-2045), so there is no
  Socket.IO/execution traffic to account for.

## Known Defects Found During Exploration
None. All 5 case steps ran cleanly and matched the case's expected results
exactly — no case-text drift, no product defect. (One inert artifact was
observed and is NOT a product issue: a manual out-of-band `fetch()` probe
issued directly from the browser console during this exploration session,
without the app's own auth header, triggered a CORS-blocked
`forward-auth/auth_oidc/login` redirect and 2 console errors — this was the
exploration tooling's own unauthenticated request, not a request the
application itself ever issues; the app's own real network calls throughout
the flow were 100% 200/201 with zero errors.)

## Blocked Steps
None. All 5 case steps are fully automatable as described, with no
workaround needed (this case's YAML document is short enough that the
on-screen tab reads correctly, unlike the longer-document `#1025` cases).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Zero new testids needed — every handle is already wired on
  `automation/testids`, reused from ELITEA-2004/2045.
- Reuse `pipeline_id` fixture (fresh empty pipeline) + `add_node("LLM")` +
  `wait_for_node_on_canvas("llm")`, same as ELITEA-2004/2045 — no new
  fixture needed.
- Capture the canonical pipeline URL once after the first navigate and
  `page.goto()` it for BOTH reloads (steps 3 and 4) — same convention as
  every reload-based case in this family (ELITEA-1954 AFS Known Defects: a
  bare `/pipelines/all/{id}` 404s).
- Toggle via `pipeline_page.llm_node_structured_output_toggle.click()` +
  `expect(...).to_be_checked()` / `expect(...).not_to_be_checked()` —
  same pattern `test_llm_structured_output_parses_into_state_variables.py`
  (ELITEA-2045) already uses for the enable direction.
- Read the YAML tab directly via `switch_to_yaml_view()` /
  `get_yaml_content()` (or an equivalent `.cm-content` text read) — this
  case's document is short enough that `#1025`'s truncation does not apply;
  do NOT default to the `pipeline_api.get_pipeline()` workaround here
  unless a future run shows truncation (it would only trigger on a
  much-longer document than this single-node, no-extra-fields pipeline
  produces).
- Wait discipline: `save_and_wait_for_update()` already waits on the PUT's
  `201` network response, not a fixed timeout; reload waits on
  `wait_for_detail_page_load()` + `wait_for_canvas()` +
  `wait_for_node_on_canvas("llm")`, matching ELITEA-2004's reload step.
