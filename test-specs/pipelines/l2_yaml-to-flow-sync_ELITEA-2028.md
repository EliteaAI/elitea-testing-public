# Test Case: Pipeline — YAML to Flow Sync

## Metadata
- **TMS ID**: ELITEA-2028
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case; sibling `high`
  pipeline cases in this folder use `l2_` + `@pytest.mark.p1`, e.g.
  `l2_hitl-node-configuration-and-router-mapping_ELITEA-2014.md` — same
  mapping applied here)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: none — API-token auth (`ELITEA_API_TOKEN`) for pipeline
  seeding/cleanup; localhost `auth_state` bypass for the UI session (no
  Keycloak login involved)
- **Analyst**: qa-engineer (analyst slot), batch `approved-next50`
- **Status**: ready-for-automation

## Preconditions
- A pipeline exists with **two non-END nodes and a SAVED canvas layout**
  (`pipeline_settings.nodes`/`edges` populated, not left empty) — this is
  load-bearing, see § Automation Hints "Seeding gotcha". Concretely: seed via
  the existing `pipeline_with_llm_id` fixture (`create_pipeline_with_llm_node`
  — LLM 1 → END, `transition: END`), then in the test itself add a second
  node (Code) via the UI and Save once before the case's own steps begin, so
  the dirty-state baseline (Save/Discard buttons) is clean when the case
  starts. This setup block is NOT part of the TMS case's 5 numbered steps —
  it exists only to satisfy the case's own precondition ("a pipeline with at
  least two nodes exists") in a way that doesn't confound the case's own
  Step 5 assertion (see Coverage Map + Automation Hints for why).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline seeded via `PipelineAPI.create_pipeline_with_llm_node()` (the
  fixture-backing method for `pipeline_with_llm_id`) — unique name per test
  function, deleted in teardown via `PipelineAPI.delete_pipeline()`.
- Second node ("Code 1") added via UI during the test's own setup block —
  no separate API call, see § Automation Hints.

## Test Steps
(Numbered to match the TMS case's own 5 steps; the fixture + "add second
node + Save + reload" precondition-setup happens BEFORE step 1, see
§ Preconditions.)

1. Navigate to the pipeline's detail page (`/pipelines/all/{id}`); confirm
   default view is Flow, then switch to Yaml view.
   - **Verify**: `pipeline-yaml-editor` (YAML CodeMirror) becomes visible.
2. Edit the YAML: locate the LLM node's `transition: END` line and replace
   it with `transition: Code 1` (the second node's id) via a scoped,
   per-line CodeMirror edit (see § Concrete Handles — new method needed).
   - **Verify**: `get_yaml_content()` (or equivalent read) contains
     `"transition: Code 1"` and no longer shows the LLM node's `transition:
     END` as its first occurrence (Code 1's own trailing `transition: END`
     line is untouched and still present — see Handles note on ambiguity).
3. Switch back to Flow view.
   - **Verify**: `pipeline-flow-view`'s canvas (`rf__wrapper`) is visible.
4. Verify the canvas reflects the updated edge.
   - **Verify**: `edge_exists("LLM 1", "Code 1")` is `True` (edge now
     connects LLM 1 → Code 1) AND the previous `LLM 1 → END` edge testid
     (`rf__edge-xy-edge__LLM 1---EliteAPipelineEnd`) is gone — confirmed
     live: the SAME edge DOM element's `data-testid` changes in place from
     `rf__edge-xy-edge__LLM 1---EliteAPipelineEnd` to
     `rf__edge-xy-edge__LLM 1---Code 1` (edge count stays 2 throughout: this
     edge plus the untouched `Code 1 → END` edge).
5. Verify the Save button is enabled.
   - **Verify**: `save_button.is_enabled()` is `True` — AND (Axis-2
     addition) was `False` immediately before this edit, at the clean
     post-setup baseline, to prove the enabling is caused by the YAML edit
     and not a pre-existing always-on state (see Automation Hints —
     confirmed live that an improperly-seeded pipeline can show Save
     permanently enabled regardless of edits, which would make this
     assertion pass for the wrong reason).

## Expected Results
- YAML editor is visible after switching to Yaml view, and its content
  contains valid pipeline YAML (`entry_point`, `nodes`, per-node
  `transition` fields).
- Editing the LLM node's `transition` value in the YAML editor is reflected
  live in the underlying YAML content (readable via `get_yaml_content()`).
- Switching back to Flow view re-renders the ReactFlow canvas; the edge
  between the LLM node and END is gone and a new edge between the LLM node
  and the newly-targeted node (Code 1) exists, with node count and total
  edge count unchanged (structure re-wired, not re-created).
- The Save button (`agent-save-button`) transitions from disabled (clean,
  saved baseline) to enabled once the YAML edit is applied — confirming the
  app's dirty-state detection recognizes a YAML-editor-driven change, not
  just a Flow-canvas-driven one (drag-connect, node add, etc., which were
  already known to dirty the form per `discard_button`'s existing docstring).
- Zero console errors, zero failed network requests, throughout.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| precond: pipeline with ≥2 nodes exists | — | setup (pre-step-1) | fixture + UI add-node + Save, before step 1 | asserted |
| 1 Open pipeline, switch to Yaml view | YAML editor displayed | step 1 | `step 1`: `pipeline-yaml-editor` visible | asserted |
| 2 Modify YAML transition target (END → existing node) | YAML content edited with new value | step 2 | `step 2`: `get_yaml_content()` contains new value | asserted |
| 3 Switch back to Flow view | Flow view displayed | step 3 | `step 3`: `rf__wrapper` canvas visible | asserted |
| 4 Verify canvas reflects updated edge | Canvas shows edge to new target | step 4 | `step 4`: `edge_exists("LLM 1", "Code 1")` True | asserted |
| 5 Verify Save button enabled | Save button active/enabled | step 5 | `step 5`: `save_button.is_enabled()` True | asserted |

**Axis 2 — Analyst additions:**
- `step 5` also asserts Save/Discard are **disabled** at the clean post-setup
  baseline, immediately before the YAML edit — *added: live exploration
  showed that a pipeline seeded via multi-node raw-YAML `create_pipeline_
  with_nodes()` (no pre-populated `pipeline_settings` layout) renders with
  Save/Discard **already enabled on first load, with zero edits made** — a
  seeding artifact that would make a bare "Save is enabled after the edit"
  assertion pass even if the YAML-edit-triggers-dirty-state behavior were
  broken. Asserting the disabled→enabled transition (not just the enabled
  end-state) is what actually exercises the case's stated intent
  ("indicating unsaved changes detected").*
- `step 4` also asserts edge/node COUNTS are unchanged (2 edges, 3 nodes)
  across the edit — *added: rules out "canvas re-created from scratch"
  false positives where an edge simply disappearing and a different one
  appearing elsewhere could coincidentally look like "updated".*
- Zero console errors / zero failed requests, asserted across the whole
  flow — *added: standard side-channel discipline per the skill's Phase 3
  step 3; none observed in 3 live runs of this exact sequence.*

## Cleanup
1. Delete the seeded pipeline via `PipelineAPI.delete_pipeline(pipeline_id)`
   in fixture teardown (standard `pipeline_with_llm_id`-pattern cleanup —
   the test never creates anything the fixture doesn't already own).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/role-overrides.md`,
`.agents/testing.md` § Locator policy) — no role/text/CSS ladder. All of the
following testids are CONFIRMED present and already wired as
`LocatorDescriptor` fields on `PipelineDetailPage` (`automation/pages/
pipeline_detail_page.py`) / inherited from `PipelineFormPage` — **no new
testid work needed for this case**:

| Element | Testid | Page-object field | Notes |
|---|---|---|---|
| Switch to Yaml view button | `pipeline-yaml-view` | `yaml_view_button` | existing |
| Switch to Flow view button | `pipeline-flow-view` | `flow_view_button` | existing |
| YAML editor container | `pipeline-yaml-editor` | `yaml_editor` | existing; wraps CodeMirror |
| Save button | `agent-save-button` | `save_button` (inherited from `PipelineFormPage`) | existing; `is_save_enabled()` helper already exists |
| Discard button | `discard-button` | `discard_button` (inherited) | existing; `disabled` toggles with dirtiness (confirmed live) — use for the baseline-disabled assertion alongside Save |
| ReactFlow canvas wrapper | `rf__wrapper` | `canvas_wrapper` | existing; sanctioned #579 third-party-widget exception |
| Canvas edge (per-edge) | `rf__edge-xy-edge__{source}---{target}` (ReactFlow-generated, on `.react-flow__edge`) | `edge_exists()` / `get_edge_count()` (existing methods) | sanctioned #579 exception (ReactFlow internal); **see caveat below** |

**New page-object method needed** — editing a single YAML line (no existing
method does this; `get_yaml_content()` is read-only):

- Add `PipelineDetailPage.edit_yaml_line(current_line_text: str,
  new_line_text: str)` — a **DECLARED IMPROVISATION**, closely mirroring the
  already-approved pattern in `McpFormPage.fill_raw_json_line()`
  (`automation/pages/mcp_form_page.py:597`, lead-approved 2026-07-16
  DECLARED IMPROVISATION for the sanctioned #579 "third-party editor library
  internal render nodes" exception): CodeMirror's per-line `<div class="cm-
  line">` nodes are library-internal render nodes, not app JSX — no testid
  can be placed on them. The compliant shape (confirmed live, identical
  mechanics to the MCP precedent):
  ```python
  line = self.yaml_editor.get_by_text(current_line_text, exact=True).first
  line.click()
  self.page.keyboard.press("Home")
  self.page.keyboard.press("Shift+End")
  # (settle wait / stability check, mirroring fill_raw_json_line's
  #  _wait_for_line_selection_applied)
  self.page.keyboard.type(new_line_text)
  ```
  Scoped inside the `yaml_editor` testid-anchored `LocatorDescriptor` field
  (same "parent MUST have a real testid" discipline as the MCP precedent).
  Docstring must declare the exception explicitly, same as
  `fill_raw_json_line`'s docstring does.
  **Ambiguity caveat (confirmed live):** `get_by_text(exact=True)` matches
  by DOM/document order, not by node association. In this case's own YAML,
  BOTH the LLM node AND the Code node end with a literal `transition: END`
  line — `.first` correctly resolves to the LLM node's occurrence only
  because it appears earlier in the document (LLM node is listed before
  Code node under `nodes:` — entry-point ordering). This is fine for THIS
  case's fixed topology, but the method itself is not disambiguation-safe
  for a caller with multiple identical target lines in unpredictable order
  — flag this limitation in the method's docstring, don't silently assume
  callers know the ordering.

**Existing-method caveat — `edge_exists()` is unreliable for an `END`
target** (confirmed live, `automation/pages/pipeline_detail_page.py:1557`):
its own docstring's worked example (`rf__edge-xy-edge__LLM 1source-ENDtarget`)
does not match the real DOM. The actual observed pattern is
`rf__edge-xy-edge__{source_id}---{target_id}`, and the END node's real
`target_id` is `EliteAPipelineEnd`, NOT the literal string `"END"` — so
`edge_exists("LLM 1", "END")` returns `False` even when that edge visibly
exists on the canvas (the substring check `f"-{target_id}"` never matches
`"-END"` against `"---EliteAPipelineEnd"`). This case is unaffected because
it only needs `edge_exists("LLM 1", "Code 1")`, which **is** reliable
(non-END targets match the method's assumption correctly, confirmed live) —
but flag this as a pre-existing page-object gap for a separate fix, not
something to touch in this case's own diff.

## Network Behavior
- No network request fires on switching YAML ⇄ Flow view, or on the
  in-editor YAML edit itself — this is all client-side state (CodeMirror +
  ReactFlow), confirmed via `wait_for_network()`/idle checks between steps
  showing no new requests. The only network activity in the whole flow is
  the ONE-TIME setup `PUT .../application/prompt_lib/{project}/{id}` (201)
  used to persist the second node before the case's own steps begin — not
  part of the case's own 5 steps.

## Known Defects Found During Exploration
None found. All 5 case steps executed cleanly against the live product with
the properly-seeded precondition (see Automation Hints); no bug filed.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, project standard).
- Page object: extend `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`) — reuse `switch_to_yaml_view()`,
  `switch_to_flow_view()`, `get_yaml_content()`, `save_button`/
  `is_save_enabled()`, `discard_button`, `edge_exists()`, `get_node_count()`,
  `get_edge_count()`, `add_node()` as-is. Add the new `edit_yaml_line()`
  method described above.
- Fixture: `pipeline_with_llm_id` (`automation/fixtures/data_fixtures.py:159`)
  is the correct starting seed (LLM 1 → END, clean saved layout, confirmed
  Save/Discard disabled on load).
- **Seeding gotcha (load-bearing, confirmed live 3×):** do NOT seed this
  case's 2-non-END-node precondition via a raw multi-node YAML API call
  (e.g. `PipelineAPI.create_pipeline_with_nodes()` with a hand-built 2-node
  `nodes` list). That leaves `pipeline_settings.nodes`/`edges` empty (no
  saved canvas layout) while the YAML `instructions` already describes 2
  nodes — the frontend auto-lays out the mismatched canvas on first render
  and marks the form dirty immediately, so **Save/Discard are already
  enabled on load with zero edits made**. This silently defeats step 5's
  entire point (disabled→enabled transition). The reliable path (used in
  this AFS and confirmed live): start from `pipeline_with_llm_id` (single
  saved node), add the second node via the UI's own `add_node("Code")`
  (existing method), **Save once, then reload** — THEN the case's own 5
  steps begin from a genuinely clean baseline. Recorded in
  `test-specs/pipelines/_surface.md` for future analysts on this surface.
- Wait strategy: no explicit network wait needed between YAML edit and
  Flow-view re-render (client-side only) — but DO wait ~500ms–1s after the
  `keyboard.type()` call before switching views (matches
  `fill_raw_json_line`'s `_wait_for_text_content_stable` discipline) and
  ~1–1.5s after `switch_to_flow_view()` before reading edges (ReactFlow
  layout/edge re-render is not instant, confirmed via live timing).
- `get_yaml_content()`'s existing fallback path (when the `pipeline-yaml-
  lines` testid — `yaml_lines` field — resolves 0 matches, which IS the
  case in this environment, confirmed live: CodeMirror's actual `.cm-line`
  divs carry no `pipeline-yaml-lines` testid at all) returns a
  newline-stripped concatenated blob. Substring assertions
  (`"transition: Code 1" in yaml_content`) work fine against this; do not
  rely on line-by-line indexing of `get_yaml_content()`'s return value.
