# Test Case: Pipeline — YAML Edit Syncs to Flow View and Enables Save

## Metadata
- **TMS ID**: ELITEA-2028
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: N/A on localhost — `VITE_DEV_TOKEN` auto-auths, no login/credentials needed (`${TEST_USER}` only relevant on deployed envs)
- **Analyst**: qa-engineer (agent), session 2026-07-24 (browser lane: isolated `browser-verify` CDP instance, port 9223 — NOT the shared Playwright MCP)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with at least 2 non-`END` nodes (e.g. `LLM 1` + `Code 1`, both initially `transition: END`).
- **Mandatory setup normalization (see Test Data below) — the pipeline's Save/Discard baseline MUST read disabled before Step 1 begins**, or the case's own Step-5 assertion ("Save becomes enabled") is not meaningful.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline (`autotest_<test-name>`) with exactly 2 nodes, both transitioning to `END`: `LLM 1` (type `llm`) + `Code 1` (type `code`). Created via the **existing** `PipelineAPI.create_pipeline_with_nodes(name, description, entry_point="LLM 1", nodes=[...])` (`automation/api/client.py:759-815`) — no new API-client method needed. Teardown: `PipelineAPI.delete_pipeline(pid)`.

  ```python
  nodes = [
      {
          "id": "LLM 1", "type": "llm", "input": [],
          "input_mapping": {
              "chat_history": {"type": "fixed", "value": []},
              "system": {"type": "fixed", "value": ""},
              "task": {"type": "fixed", "value": ""},
          },
          "output": [], "structured_output": False,
          "transition": "END",
      },
      {
          "id": "Code 1", "type": "code", "input": [], "output": [],
          "source_code": "",
          "transition": "END",
      },
  ]
  ```

- **CRITICAL surface gotcha (confirmed live this session, applies to EVERY existing pipeline-creation helper — `create_pipeline_with_nodes()`, `create_pipeline_with_llm_node()`, and a raw crafted payload alike, since all three set `pipeline_settings: {"nodes": [], "edges": []}`):** a pipeline created this way has an EMPTY visual-layout record server-side. The very first time its Flow (or Yaml) view renders, the client auto-computes real canvas positions that differ from the stored empty array — and this diff alone is enough to flip Save/Discard from disabled to enabled, with **zero actual content edit**. Confirmed via a controlled A/B this session:
  - Pipeline created via a raw API POST with `pipeline_settings: {"nodes": [], "edges": []}` (id `5723`, deleted after analysis): fresh navigate → Save/Discard **enabled** already; switching Flow→Yaml→Flow with no edits made no difference (stayed enabled either way).
  - The SAME shape pipeline, but with ONE extra step — Add 2 nodes via the UI's own "+" button, then click **Save** once (id `5734`, deleted after analysis) — normalizes `pipeline_settings.nodes/edges` to match the rendered layout. After a hard reload: Save/Discard **disabled**, and switching Flow⇄Yaml repeatedly with no edits correctly stayed disabled. Only the real YAML content edit (Step 2) flipped it to enabled.
  - **Fix for the fixture/test setup: after creating the pipeline (via any of the API helpers above), perform ONE explicit `click_save()` / `save_and_wait_for_update()` BEFORE the test's own Step 1 begins**, and assert `is_save_enabled() == False` right after, as the test's own baseline check. Skipping this normalization makes "Save becomes enabled after the YAML edit" pass vacuously (it would already read enabled before the edit too) — it does not prove the feature under test actually works.
  - This is **not filed as a product defect** — the visual-layout diff is a real, if surprising, uncommitted change (arguably correct: the layout genuinely hasn't been persisted yet), and it only manifests via the API-creation path, not the normal "create via UI" user flow. Documented here (and in `_surface.md`) as a load-bearing setup gotcha for every future pipeline case that asserts a Save/Discard baseline, not as a Known Defect for THIS case.

### reuse-existing
- `${ELITEA_PROJECT_ID}` (`.env.test`).

## Test Steps

1. Navigate to the fixture pipeline's detail page (`PipelineDetailPage.navigate(pipeline_id)`, existing method — includes `?viewMode=owner`).
   - **Verify (added baseline, see Test Data gotcha)**: `is_save_enabled()` is `False` and `is_discard_enabled()` is `False` immediately after navigating (pipeline was normalized via one Save during setup) — this is what makes Step 6's "becomes enabled" assertion meaningful rather than vacuous.
2. Switch to Yaml view (`switch_to_yaml_view()`, existing method).
   - **Verify**: `is_yaml_view_active()` is `True`; `get_yaml_content()` contains `entry_point: LLM 1`, both node id blocks (`- id: LLM 1`, `- id: Code 1`), and `transition: END` appearing twice (once per node).
   - **Verify (added)**: `is_save_enabled()` is STILL `False` here — switching to Yaml view alone (no edit yet) must not flip the button. This is the direct regression guard for the Test Data gotcha above (confirms the fixture is correctly normalized and that the app's dirty-tracking is genuinely edit-triggered, not view-triggered).
3. Edit `Code 1`'s `transition: END` line to `transition: LLM 1` directly in the YAML editor (new method needed — see Concrete Handles / Automation Hints for the exact technique).
   - **Verify**: re-reading `get_yaml_content()` shows `Code 1`'s node block now ends with `transition: LLM 1`; `LLM 1`'s own `transition: END` line is unchanged (only the targeted line was touched).
4. Switch back to Flow view (`switch_to_flow_view()`, existing method).
   - **Verify**: `is_flow_view_active()` is `True`.
5. Verify the canvas reflects the updated edge.
   - **Verify**: `edge_exists("Code 1", "LLM 1")` is `True` (existing method — matches live, confirmed testid `rf__edge-xy-edge__Code 1---LLM 1`).
   - **Verify (added)**: the OLD edge is gone, not just the new one present — `edge_exists("Code 1", "END")` is `False` **and** `edge_exists("Code 1", "EliteAPipelineEnd")` is `False` (check both forms; see Concrete Handles for why the plain `"END"` check alone is not sufficient evidence on its own, per the ELITEA-2018 digest's aliasing finding — checking only the positive case would miss a defect class where the app ADDS an edge without removing the stale one).
   - **Verify (added)**: `LLM 1`'s own untouched edge is still present — `edge_exists("LLM 1", "END")` is still `True` (via `edge_exists("LLM 1", "EliteAPipelineEnd")`, same aliasing caveat) — confirms the edit was scoped to only the intended node, not a wholesale re-layout.
6. Verify the Save button is enabled.
   - **Verify**: `is_save_enabled()` is `True`.
   - **Verify (added)**: `is_discard_enabled()` is also `True` (case only names Save, but Discard is the natural complementary control and was confirmed live to track the same dirty-state).
7. **Verify (added, standard side-channel discipline)**: zero `error`-level console messages across the whole flow (confirmed clean live this session — filter to `level == "error"`; the ambient `warning`-level ReactFlow `nodeTypes/edgeTypes` message, if present, is unrelated per `_surface.md`).

## Expected Results
- Editing a node's `transition:` value directly in the YAML editor is reflected in the Flow view as an updated edge on the canvas the moment you switch back — no Save/reload needed to see it.
- The stale edge (old target) is gone from the canvas, not merely superseded by an additional one.
- Other nodes/edges not touched by the edit are unaffected.
- The Save (and Discard) button flips from disabled to enabled specifically because of the content edit — not merely from switching between Flow and Yaml views.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with ≥2 nodes exists | pipeline available for the test | Test Data (fixture) | step 1: navigate succeeds, `get_yaml_content()` shows both node blocks | asserted |
| 1 Open pipeline, switch to Yaml view | YAML editor displayed with pipeline definition | step 2 | `is_yaml_view_active()` + `get_yaml_content()` content check | asserted |
| 2 Modify YAML — change a transition target (END → another existing node) | YAML content edited with new transition value | step 3 | re-read `get_yaml_content()` shows new value | asserted |
| 3 Switch back to Flow view | Flow view displayed | step 4 | `is_flow_view_active()` | asserted |
| 4 Verify canvas reflects the updated edge | canvas shows edge connecting to new target | step 5 | `edge_exists("Code 1", "LLM 1")` True | asserted *(enriched — see Axis 2)* |
| 5 Verify Save button becomes enabled | Save button active/enabled | step 6 | `is_save_enabled()` True | asserted |
| Expected Final State: YAML edit reflected in Flow view as updated edge + Save enabled | — | steps 3–6 | as above | asserted |
| Pass/Fail: all steps complete without errors; edge updates correctly; Save enabled | — | all steps | steps above + step 7 console check | asserted |

### Axis 2 — Analyst additions

- **Baseline check that Save/Discard are DISABLED before the edit** (steps 1–2) — *added: without this, "Save becomes enabled after the edit" is not a meaningful assertion — a pipeline whose visual layout isn't normalized starts already-"dirty" for unrelated reasons (see Test Data gotcha), and the case's literal wording never requires checking the pre-edit state, which would let a real regression (e.g. dirty-tracking permanently broken/always-on) slip through undetected.*
- **Assert the STALE edge is gone, not just that the new edge exists** (step 5) — *added: the case's step 4 only says "canvas shows the modified edge connecting to the new target node," which a buggy implementation that ADDS an edge without removing the old one would also satisfy. Checking the old edge's absence closes that gap.*
- **Assert the untouched node's own edge is unaffected** (step 5) — *added: confirms the edit is scoped to the one line/node touched, not a side-effect of a wholesale YAML re-parse or re-layout.*
- **Zero console errors** (step 7) — *added: standard side-channel discipline; confirmed clean live.*
- **Discard button tracked alongside Save** (step 6) — *added: cheap, same dirty-state mechanism, natural complementary control; case doesn't ask for it but it's directly observable at zero extra cost.*

## Cleanup
1. This session created two throwaway pipelines directly via `PipelineAPI` (ids `5723`, `5734`, project `399`) — the first via a raw crafted payload to establish the initial (later-disproven) hypothesis, the second as the clean control. **Both were deleted by this analyst session** (`PipelineAPI.delete_pipeline`).
2. Implementer teardown: the fixture's own `PipelineAPI.delete_pipeline(pid)` teardown — no manual cleanup needed in the test body.

## Concrete Handles (discovered during exploration)

Provenance verified this session via `cd ../EliteaUI && git fetch origin` immediately before checking (`.agents/role-overrides.md` § Analyst slot). Command used per row: `git grep -- "<testid>" origin/main -- src/` vs `origin/automation/testids -- src/`. **Note:** two of the rows below are FALSE NEGATIVES under bare literal-string grep — the testid is assembled at runtime from a template/prop, not written as a literal in source. Verified instead by reading the constructing component's source AND matching it against the live DOM.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Yaml view toggle button | existing `PipelineDetailPage.yaml_view_button` (testid `pipeline-yaml-view`) | **on-main ✓** (verified live + by source) — literal `git grep` gives a **false negative**: the testid is built at runtime as `` `pipeline-${item.value}-view` `` in the shared `src/components/GroupedButton.jsx:57` (`data-testid={item.testid \|\| \`pipeline-${item.value}-view\`}`), not written as a literal string anywhere. Confirmed by reading that line AND clicking the live selector successfully. | Reused as-is |
| Flow view toggle button | existing `PipelineDetailPage.flow_view_button` (testid `pipeline-flow-view`) | **on-main ✓** — same `GroupedButton.jsx:57` mechanism as above (false negative under literal grep, confirmed by source + live match) | Reused as-is |
| YAML editor container | existing `PipelineDetailPage.yaml_editor` (testid `pipeline-yaml-editor`) | **on-main ✓** — literal string, `YamlCodeEditor.jsx:39` (`data-testid="pipeline-yaml-editor"`), confirmed by direct grep | Reused as-is |
| YAML per-line divs | existing `PipelineDetailPage.yaml_lines` (testid `pipeline-yaml-lines`) | **DEAD LOCATOR — confirmed 0 live DOM matches**, on neither `main` nor `automation/testids`. No source anywhere wires this testid onto CodeMirror's `.cm-line` nodes (`YamlCodeEditor.jsx` calls `Field.CodeMirrorEditor` with no per-line testid prop at all — only `contentTestId`, a single-node mechanism, exists on that shared component today). | **Not a blocker for this case** — `get_yaml_content()` already silently falls back to `yaml_editor.text_content()` whenever `yaml_lines.count() == 0` (which is every time), so reading the whole YAML still works; it just can't preserve line breaks. Flagging for whoever next touches this page object — this is a "dead page-object field" in `ui-testid-coverage` terms. **Do not use `self.yaml_lines` for the new edit method below** — it will silently match zero elements. |
| Target line for editing a `transition:` value | **NEW method needed** — e.g. `PipelineDetailPage.edit_yaml_line(current_line_text, new_line_text)`, mirroring `mcp_form_page.py::fill_raw_json_line()` exactly | Declared #579 improvisation (same shape, same precedent, lead-approved 2026-07-16): CodeMirror's per-line `<div>` nodes are library-internal render nodes; since `pipeline-yaml-lines` doesn't actually exist (see row above), no testid can be placed on an individual line today. Compliant pattern: scope `get_by_text(current_line_text, exact=True)` **inside the already-testid'd `self.yaml_editor` parent** (never a free-floating `page.locator`) — click it, `page.keyboard.press("Home")`, `page.keyboard.press("Shift+End")`, then a single `page.keyboard.type(new_line_text)` call. | Confirmed live end-to-end this session (see Automation Hints for the exact sequence and a CDP-vs-Playwright caveat). **Multiple lines can share identical text** (both nodes here started with `"transition: END"`) — disambiguate via `.last`/`.nth(k)`, or better, locate by node-block context (find `"- id: Code 1"` first, then the next `"transition:"` line after it) rather than assuming `get_by_text(...)` alone is unique. |
| Canvas edge (updated: Code 1 → LLM 1) | existing `PipelineDetailPage.edge_exists("Code 1", "LLM 1")` | **on-main ✓** — library-owned (`@xyflow/react`), not app JSX; testid `rf__edge-xy-edge__Code 1---LLM 1` (triple-dash, no handle suffix — YAML/transition-derived edge, per the ELITEA-2018 digest) confirmed live | Reused as-is |
| Old edge must be gone (Code 1 → END) | `edge_exists("Code 1", "END")` **and** `edge_exists("Code 1", "EliteAPipelineEnd")` | N/A (ReactFlow-owned) | Per the ELITEA-2018 digest, the END node's edge-endpoint id is the literal `EliteAPipelineEnd`, NOT `"END"` — the existing `edge_exists()` method's loose substring match makes `edge_exists(x, "END")` a **false negative** for a YAML-derived END edge. Check the `"EliteAPipelineEnd"` form to get a real answer; checking only `"END"` risks a false-negative "it's gone" read that isn't actually verified. |
| Save button | existing `PipelineFormPage.save_button` (testid `agent-save-button`) / `is_save_enabled()` | **on-main ✓** — shared with agent forms, used by multiple already-merged pipeline + agent tests | Reused as-is |
| Discard button | existing `PipelineFormPage.discard_button` (testid `discard-button`) / `is_discard_enabled()` | **on-main ✓** | Reused as-is |

## Network Behavior
- Switching Flow ⇄ Yaml view, and editing the YAML text directly, are both **100% client-side** — no request fires for either (confirmed live: `get-network` captured nothing during the whole edit+view-switch sequence). The pipeline's own **Save** button is the only action that would persist anything (`PUT /elitea_core/application/prompt_lib/{project}/{pipeline_id}`), and this case's steps never require clicking it (Step 5/6 only assert the button's enabled *state*, not its result) — so no network wait is needed anywhere in this test.

## Known Defects Found During Exploration

**None found in the YAML-to-Flow sync feature itself.** The edit-then-sync flow (YAML edit → Flow-view edge update) and the Save-button dirty-tracking both behaved correctly once test data was normalized (see Test Data gotcha — that finding is a setup/fixture nuance shared by every pipeline case using the existing API-creation helpers, not a defect in the feature under test, and is not filed as a ticket; it's documented here and in `_surface.md` so no future analyst mis-diagnoses it as a real bug in THIS feature).

## Blocked Steps

None. All case steps were executed to completion against the live local environment, including a full A/B control experiment to isolate a false lead from the real feature behavior.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). **No `add-data-testid` pass needed for this case** — every element it touches already has a working testid on `main` (the "dead" `pipeline-yaml-lines` field is routed around via the declared #579 pattern, not fixed, since fixing it is out of this case's scope).
- Suggested location: `automation/tests/ui/pipelines/test_pipeline_advanced.py`, near the existing `test_yaml_content_reflects_pipeline` / `test_flow_yaml_round_trip` tests (same file/class family — reuses the file's existing `_navigate_to_detail()` helper and imports; neither existing test edits YAML content or asserts Save-button state, so this is new coverage, not a duplicate — see merged-target check below).
- **Merged-target dedup check performed:** `test_yaml_content_reflects_pipeline` only *reads* YAML (no edit, no Flow-view check, no Save-button check). `test_flow_yaml_round_trip` adds a node and toggles Flow→Yaml→Flow with no content edit, asserting only node *count* is preserved (no edge check, no Save-button check). Neither covers editing YAML content, verifying the Flow view reflects an *edge* change, or the Save-button-enabled assertion — this case is genuinely new coverage (`ready-for-automation`, not `extend-existing`; the overlap is thin precondition-setup similarity only).
- **Exact YAML-line-edit technique confirmed live this session** (via `browser-verify`/CDP, not Playwright, but the underlying CodeMirror mechanics are identical): click the target line's div (scoped inside the testid-anchored editor container) → `Home` → `Shift+End` (selects from the first non-whitespace character to end-of-line — confirmed via `document.getSelection().toString()`, leading indentation is NOT included in the selection, so the replacement text should be just the line's logical content, e.g. `"transition: LLM 1"`, not `"    transition: LLM 1"`) → type the replacement. In Playwright, use `page.keyboard.type(new_line_text)` as ONE call (matching `fill_raw_json_line()`'s existing pattern) — do NOT call a helper that re-clicks the element first (e.g. a raw `type(selector, text)`-style API), since that collapses the selection you just made back to a single point before typing.
- **Test Data gotcha is the load-bearing finding of this whole case** — see Test Data section above; without the one-time normalizing Save, Step 1's/Step 2's added baseline checks (`is_save_enabled() == False`) will FAIL immediately (proving the gotcha is real, not hypothetical) rather than the test silently passing for the wrong reason. If the implementer sees this baseline check fail, the fix is the fixture setup, not the test's assertions.
- Wait strategy: no network wait needed anywhere in this test (see Network Behavior) — pure client-side, synchronous UI state checks throughout.
- Console-error check: filter to `level == "error"` only (per `_surface.md`'s existing ambient-warning guidance for this surface).
