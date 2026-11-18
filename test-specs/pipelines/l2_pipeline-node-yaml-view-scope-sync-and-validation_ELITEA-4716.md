# Test Case: Pipeline — Node YAML View (scope + two-way sync / validation + invalid YAML)

## Metadata
- **TMS IDs**: ELITEA-4716 (scope & two-way sync), ELITEA-4717 (validation & invalid YAML) — priority high -> l2, `@pytest.mark.p1`
- **Linked Story**: EliteaAI/elitea_issues#7158 (epic 7093)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` via scripted Python Playwright (pytest scratch probe; Playwright MCP has no Chrome binary). Source cross-checked on `EliteaUI origin/main` (`NodeYamlView.jsx`, `NodeConfigViewToggle.jsx`, `NodeYamlLeaveModal.jsx`, `useNodeYamlEditor.hooks.js`, `nodePanel.constants.js`).
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation (both cases)
- **family_afs**: false-in-spirit — TWO separate tests (steps differ), one AFS file covering both, shared seed + page-object work. Implementer: write two test functions sharing a fixture; do NOT merge assertions.
- **surface_key**: pipelines-node-yaml-view

## Environment gotcha (analyst session)
`automation/.env.test` was absent in this sandbox; `APP_PREFIX` unset -> app 404 ("Page Not Found") and every pipelines spec fails at `pipelines-page-header`. Export `APP_PREFIX=/app` (shell) when `.env.test` is missing. Also pass `--reruns 0` to disable pytest.ini reruns when probing.

## Preconditions (API seed — no UI building)
`pipeline_api.create_pipeline_with_nodes(name, description, entry_point="LLM 1", nodes=[...])`:
- `LLM 1`: `{"id":"LLM 1","type":"llm","input":["messages"],"output":["messages"],"input_mapping":{"system":{"type":"fixed","value":""},"task":{"type":"fixed","value":"Say hi"},"chat_history":{"type":"fixed","value":[]}},"transition":"Printer 1"}`
- `Printer 1`: `{"id":"Printer 1","type":"printer","input":["messages"],"output":["messages"],"input_mapping":{"printer":{"type":"fixed","value":"x"}},"transition":"END"}`
- `Code 1`: `{"id":"Code 1","type":"code","code":{"type":"fixed","value":"{\"x\":1}"},"input":["input"],"output":["messages"],"transition":"END"}`
- Case 4716 also wants pipeline-level `interrupt_before: [Printer 1]`. `create_pipeline_with_nodes` emits only `entry_point` + `nodes` (+`state`); the implementer must add an additive `extra_top_level` param (or post-edit instructions) — NOT verified live; the "no interrupt_* keys in node YAML" assertion is then meaningful. Raise as question if awkward.
- 4717 uses only LLM 1 + Code 1 (the same seed minus Printer works; reusing the 3-node seed is fine — LLM 1 -> Code 1 for 4717 is optional; nothing in 4717 depends on the transition target).
- Open with `PipelineDetailPage.navigate(id)` (adds `?viewMode=owner`), `dismiss_banner_if_present()`, `wait_for_canvas()`, viewport 1600x1400. Cleanup `pipeline_api.delete_pipeline(id)`.

## ELITEA-4716 — Steps (all executed live on DEV)
1. `pp.open_node_panel_by_card("LLM 1")`; click `pipeline-node-panel-view-yaml`; `pipeline-node-panel-yaml-content` visible. OK.
2. Node YAML (read via `.cm-line` under `pipeline-node-panel-yaml-content`, join "\n") is exactly the single-item list element:
```
- id: LLM 1
  type: llm
  input:
    - messages
  input_mapping: {chat_history, system, task (type: fixed, value)}
  output:
    - messages
  transition: Printer 1
```
 No `entry_point`, `nodes`, `state`, `interrupt_*` keys, no other node ids. NOTE: shown as a one-item YAML LIST (leading `- `), indentation 2 for child keys. Assert absence by line-prefix (`entry_point:`, `state:`, `interrupt_before:`, `interrupt_after:`) and absence of `id: Printer 1` / `id: Code 1`.
3. Page-level toggle: `pp.close_node_panel()`, `pp.switch_to_yaml_view()`, `pp.get_yaml_content()`. The page block is the same text with 4 extra leading spaces (nested under `nodes:` list: `  - id: LLM 1` / `    type: llm`). Compare after normalising: de-indent the page block lines (strip the common 2-space list indent; the node view's first line `- id:` equals page `  - id:` stripped). Verified by eye on all lines — identical content. Extract block = from `  - id: LLM 1` up to the next `  - id:`.
4. Back to Flow (`pp.switch_to_flow_view()`), reopen LLM 1 panel, YAML tab, edit line `value: Say hi` -> `value: Summarize the input` (`edit_yaml_line`-style: click the line via `get_by_text(exact=True)` under the content testid, `Home`, `Shift+End`, `insert_text`). Wait >400 ms debounce (`NODE_YAML_APPLY_DELAY_MS=400`; use expect polling, no sleep). Observed: card `pipeline-node-card-LLM 1` text becomes `LLM 1 | LLM | Entrypoint | Summarize the input | Input | Output`; `agent-save-button` flips from disabled (False initially) to enabled; Flow-view Task field `pipeline-llm-node-task-value` (textarea) holds the value (observed via card + Flow panel; assert `to_have_value`).
5. Page Yaml: `value: Summarize the input` present in LLM 1 block (observed).
6. YAML edit `transition: Printer 1` -> `transition: Code 1`: edge testid `rf__edge-xy-edge__LLM 1---Code 1` appears, `...LLM 1---Printer 1` gone; page Yaml shows `    transition: Code 1` for LLM 1 (observed). Existing helper `pp.edge_exists("LLM 1","Code 1")` / `edge_testid_present`.
7. Flow tab -> `pipeline-llm-node-system-value` (TEXTAREA, rung-1 testid on DEV) click + `insert_text("You are a helpful assistant")` -> YAML tab shows `system:` / `value: You are a helpful assistant`. Observed OK (no wait issues; node YAML re-renders from store).
8. **Canvas drag LLM 1 Output -> Printer 1: NOT reproduced in analysis.** After step 6 (LLM -> Code 1), `pp.connect_nodes("LLM 1","Printer 1")` raised "source handle not hittable" (LLM 1 card at y466-585, handle `[data-handlepos=bottom]` rect y571 is overlaid by the card's own Box; hover first did not help) and a hand-rolled real-mouse drag (down on handle centre, stepped move to Printer 1's `[data-handlepos=top]` centre, up) left the edge at LLM 1 -> Code 1 (no new edge, no connection menu). `drag_output_handle_to_empty_canvas` (16px `pipeline-node-add-from-output-{n}-source`) works for new-node creation only. In ELITEA-2031's seed (LLM and Printer disconnected, panel closed) `connect_nodes` works on the same layout, so the difference is likely the node-panel / saved-vs-unsaved state, or a replace-existing-transition constraint. **Implementer must probe this step first; if it cannot be driven with real mouse events in this layout, report as `blocked`/`question` for step 8 only — do not fake it with a YAML edit.** The downstream assertion is `transition: Printer 1` in the node YAML (only the YAML-reflects-canvas direction is new).
9. Append a child line `custom_note: keep_me` at 2-space indent (after `type: llm` / end). Select-all + `insert_text(ynode + "\n  custom_note: keep_me")` works; **do NOT append at column 0 — gives `Invalid YAML: end of the stream or a document separator is expected` (observed)**. No error; click `agent-save-button`; wait; reload; reopen LLM 1 -> YAML. Observed: `custom_note: keep_me` persisted (CodeMirror view places it second, after `type: llm`: the app re-dumps key order, so assert `"custom_note: keep_me" in text`, not position).

## ELITEA-4717 — Steps (all executed live on DEV)
1. Open LLM 1 panel -> YAML. OK.
2. Replace line `- id: LLM 1` with `- id: LLM main` (click via `get_by_text("- id: LLM 1", exact=True)`; the id line text includes the leading `- `). Result: `pipeline-node-card-LLM main` count 1, panel header unchanged (header shows type, the name lives in `pipeline-node-panel-name-input` — present only in Flow view; assert it after switching to Flow: value `LLM main`). Save becomes enabled. No error.
3. `- id: Code 1`: `pipeline-node-panel-yaml-error` text = `The name has been used by other nodes, please input a new name!`; card `LLM main` still exists (rename not applied); **Save enabled/disabled: see Save-state below**.
4. `- id: ''`: error text `Name is required`; card title unchanged (LLM main card count 1).
5. Restore `- id: LLM main` (error clears); `type: llm` -> `type: code`: error `Node type can't be changed in the node YAML.` (exact, with trailing period; matches `NODE_YAML_ERRORS.typeChange`).
6. Restore `type: llm`; break syntax (`input_mapping:` -> `input_mapping`): error starts with `Invalid YAML:` (observed `Invalid YAML: can not read a block mapping entry; a multiline key may not be an implicit key`). NB the case's literal "remove colon after `input`" edit was not used because `input:` is a block key followed by a `- messages` list; removing its colon is equally invalid, but I verified with `input_mapping`. Implementer should use whichever line is stable; assert `startswith("Invalid YAML:")`.
7. Page Yaml toggle while invalid: not executed as a standalone step (the page toggle is outside the panel; the panel stays open with the invalid draft). Equivalent verified by source: invalid edit is never written to `yamlJsonObject` (`applyDraft` returns on parse error before `setYamlJsonObject`) and by step 11 (after Discard the node reverts to `LLM main` block). Implementer: assert page Yaml still contains `- id: LLM main` and does not contain the broken text; if the page toggle is blocked by the open panel / leave guard, say so.
8. Click `pipeline-node-panel-view-flow` while invalid -> `pipeline-node-yaml-leave-dialog` visible; text "Invalid node YAML | The node YAML has errors, so it wasn't applied. Fix it, or discard your YAML changes to go back to the last valid version. | Fix | Discard YAML changes". **Button label is `Discard YAML changes` (lowercase "changes"), case text says "Discard YAML Changes" — case-text drift, assert the live text** (`pipeline-node-yaml-leave-fix`, `pipeline-node-yaml-leave-discard`).
9. `pipeline-node-yaml-leave-fix` click: dialog count 0; YAML editor visible and error still present (observed).
10. `pipeline-node-panel-close` click: dialog appears again (observed).
11. `pipeline-node-yaml-leave-discard` click: dialog gone, **panel closed (panel count 0 — the original action (close) completes)**; reopening LLM main -> YAML shows the last valid block, error absent. When Discard is clicked from the Flow-tab path instead, the panel stays and switches to Flow (observed: yaml content count 0, no error). Case wording "reverts; error disappears" holds in both.
12. Click in editor, `Control+f`: CodeMirror search panel `.cm-search` appears (text "next previous all match case regexp by word | replace replace all | ×" — the replace row is shown together with search, in this CM6 setup). Typing `transition` + Enter gives `.cm-searchMatch` count 1 within the node's editor (only one `transition` line exists in the node YAML). Scope: the search is CodeMirror-local — no cross-node possibility; assert match count == number of `transition` occurrences in `ynode()`.
13. `Control+h`: `.cm-search` panel with `button[name=replace]` and `button[name=replaceAll]` present (count 1 each). Both found via third-party CodeMirror internals (permanent css rung, #579 exception; scope under `pipeline-node-panel-yaml`).
14. `pipeline-node-panel-yaml-copy` click: `get_by_text("Copied", exact=True)` count 1 (message text from `copyMessage="Copied"`). Clipboard content not asserted (soft per case). Optional: grant clipboard permission and read, compare to ynode — NOT verified.

## Save-state (case-text drift, important)
Case 4717 says "Save is disabled" while any error is shown (steps 3,4,5,6). Live DEV: `agent-save-button` is **enabled** whenever the pipeline is dirty from a previously applied valid edit; with a CLEAN pipeline (nothing applied yet), a duplicate id / type change / empty id / invalid YAML leaves Save **disabled** (observed False through steps dup -> restore -> type -> restore -> empty). Once a valid edit was applied (rename `LLM main`, Save True) the subsequent invalid states keep Save enabled (the invalid draft is simply not part of the pipeline). So "Save disabled because of the error" is NOT a product behaviour — Save enablement reflects dirtiness only. Source check: `useNodeYamlEditor` has no save-blocking channel (only the leave guard). **Clarification** (not a defect): assert the error text + rename-not-applied; assert Save disabled ONLY in a variant that runs the validations on a clean pipeline (before step 2), or drop the Save assertion. Same pattern as the ELITEA-4715 Save drift. Recommend a clarification issue on the case text.

## Case-text clarifications (soft, none are defects)
- 4717 Save disabled (above); button label `Discard YAML changes`; step 6 "colon after input" edit.
- 4716 step 2: node YAML is a list item (`- id: ...`); node key order is app-controlled (custom_note moves to 2nd position after save/reload).
- 4716 Precondition `interrupt_before: [Printer 1]` — seed helper gap (see Preconditions).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 4716-1 open YAML tab | editor opens in panel | step 1 | `pipeline-node-panel-yaml-content` visible | asserted |
| 4716-2 scope | only LLM 1 block, no pipeline keys/other nodes | step 2 | line-prefix absence checks | asserted |
| 4716-3 matches page Yaml | identical | step 3 | normalised block compare | asserted |
| 4716-4 task edit -> Flow/card/Save | synced after debounce | step 4 | task textarea value, card text, Save enabled | asserted |
| 4716-5 page Yaml has task | contains | step 5 | page yaml substring | asserted |
| 4716-6 transition edit -> edge + page yaml | edge to Code 1 | step 6 | edge testid + page yaml | asserted |
| 4716-7 Flow System -> YAML | shows value | step 7 | yaml lines | asserted |
| 4716-8 canvas drag -> YAML transition | `Printer 1` | step 8 | node YAML transition | **open risk** — drag not reproducible in analysis layout; implementer probes, else blocked step 8 only |
| 4716-9 unknown key persists | survives Save+reload | step 9 | substring after reload | asserted |
| 4717-1..2 open + rename | card title + panel Name | steps 1-2 | card testid; name input after Flow switch | asserted |
| 4717-3 duplicate | exact error, rename not applied, Save disabled | step 3 | error text; card; Save = clarification | asserted (Save: clarification) |
| 4717-4 empty | "Name is required", card unchanged | step 4 | error text; card count | asserted (Save: clarification) |
| 4717-5 type change | exact error | step 5 | error text | asserted (Save: clarification) |
| 4717-6 invalid YAML | "Invalid YAML:" prefix | step 6 | startswith | asserted (Save: clarification) |
| 4717-7 page Yaml unchanged | last valid block | step 7 | page yaml | partially observed (source + step 11); implementer verifies |
| 4717-8 Flow-switch modal | title, text, Fix/Discard | step 8 | dialog text + buttons | asserted (label case drift) |
| 4717-9 Fix | modal closes, stays YAML w/ error | step 9 | dialog 0, error present | asserted |
| 4717-10 close X modal | same modal | step 10 | dialog visible | asserted |
| 4717-11 Discard | reverts, error gone | step 11 | yaml block, error absent | asserted |
| 4717-12 Ctrl+F scoped | find panel, matches within node | step 12 | `.cm-search`, match count | asserted |
| 4717-13 Ctrl+H | replace controls | step 13 | replace/replaceAll buttons | asserted |
| 4717-14 Copy | "Copied" shown | step 14 | "Copied" text | asserted (soft); clipboard unverified |

### Axis 2 — Analyst additions
- 4717: after Discard, assert `pipeline-node-yaml-leave-dialog` count 0 and card title unchanged (grounded: observed).
- 4716-2: assert `custom_note` is absent initially (baseline for step 9).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Flow / YAML toggle | 1 | `pipeline-node-panel-view-flow`, `pipeline-node-panel-view-yaml` | — | testid on DEV ✓ |
| Node YAML wrapper / editor / content | 1 | `pipeline-node-panel-yaml`, `-yaml-editor`, `-yaml-content` | — | testid on DEV ✓ |
| Editor lines | 4 | `.cm-line` under `pipeline-node-panel-yaml-content` | — (CodeMirror internal, #579 permanent css) | ladder — third-party |
| Error text | 1 | `pipeline-node-panel-yaml-error` (absent when no error) | — | testid on DEV ✓ |
| Leave modal / Fix / Discard | 1 | `pipeline-node-yaml-leave-dialog`, `-leave-fix`, `-leave-discard` | — | testid on DEV ✓ |
| Copy / Full screen | 1 | `pipeline-node-panel-yaml-copy`, `-yaml-full-screen` | — | testid on DEV ✓ |
| "Copied" confirmation | 2 | `get_by_text("Copied", exact=True)` | `pipeline-node-panel-yaml-copied-toast` | ladder — no testid (toast); unique on page when shown |
| Search / replace panel | 4 | `.cm-search`, `.cm-search button[name=replace]`, `[name=replaceAll]` scoped under `pipeline-node-panel-yaml` | — | third-party CodeMirror, permanent css rung |
| Search match | 4 | `.cm-searchMatch` | — | third-party |
| Panel name / close | 1 | `pipeline-node-panel-name-input` (Flow view only), `pipeline-node-panel-close` | — | testid on DEV ✓ |
| LLM system / task value | 1 | `pipeline-llm-node-system-value`, `pipeline-llm-node-task-value` (textarea) | — | testid on DEV ✓ |
| Card / save | 1 | `pipeline-node-card-{name}`, `agent-save-button` | — | testid on DEV ✓ |
| Edge | 1 | `rf__edge-xy-edge__{src}---{dst}` (existing `edge_exists`) | — | testid on DEV ✓ |

Reuse: `PipelineDetailPage.open_node_panel_by_card`, `close_node_panel`, `switch_to_yaml_view`/`switch_to_flow_view`/`get_yaml_content` (PAGE-level, uses `pipeline-yaml-editor`), `dismiss_banner_if_present`, `edge_exists`, `connect_nodes`. New page-object work: node-panel YAML fields (toggle buttons, content, error, leave dialog/fix/discard, copy), `node_yaml_text()`, `set_node_yaml_line()`, find/replace helpers. Typing: CodeMirror needs click + `insert_text` (fill() does not work), wait via `expect(error)`/card text — no sleeps; 400 ms debounce is the only timing.

## Network / console
Save = PUT application version; no failing requests seen in the probe; console not separately captured (scripted probe) — implementer checks.

## Known Defects Found During Exploration
- none. (Save-not-disabled is a case-text clarification; step-8 drag is unresolved, not a confirmed defect.)

## Blocked Steps
- 4716 step 8 pending implementer probe (see above).
- **Resolved during ELITEA-4716 implementation (Axel):** step 8 is NOT automatable with real mouse events in this layout. After step 6 LLM 1's Output handle (`pipeline-node-add-from-output-LLM 1-source`) is fully covered by the edge's `.react-flow__edgeupdater-source` (hover fails: "intercepts pointer events"), and `connect_nodes` finds the bottom sliver covered by the card's own Box. Dragging the edge's TARGET end onto Printer 1 draws a new edge visually, but the app's `onReconnect` only does `reconnectEdge` on edges (no `onConnect`), so node YAML `transition` stays `Code 1` after reload of the panel. Spec omits step 8 (commented in the test); not faked via YAML. Case 4716 coverage is therefore step 1-7 + 9; step 8 goes to the lead as a finding (possible product gap / case drift).
