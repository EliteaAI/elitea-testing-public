# Test Case: Pipeline - Duplicate Node End-to-End

## Metadata
- **TMS ID**: ELITEA-4719 (priority: medium -> l2; `@pytest.mark.p2`)
- **Linked Story**: EliteaAI/elitea_issues#7161, #7418 (epic 7093)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted pytest+Playwright probe, headless, viewport 1600x1400; Playwright MCP browser unavailable - no Chrome). Source cross-checked on `EliteaUI origin/main` (`NodeConfigFooter.jsx`, `FlowEditor.jsx:553`, `nodeOperations.helpers.js`, `NodeCard.jsx`).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation
- **surface_key**: pipelines-node-duplicate
- **Neighbours read**: ELITEA-4715/4716/4718 AFS + specs (cards, panel, TOOLS), `test_pipeline_tools_auto_attach_read_only.py` - none covers Duplicate (grep `pipeline-node-panel-duplicate` in automation/ = 0 hits). Not already-covered.

## Preconditions / seeding (API, no UI build)
- `mcp_toolkit_with_tools` fixture (DeepWiki MCP, public, no secrets; tools incl. `read_wiki_structure`, input `repoName` string). Case says "test-github-mcp / get_me" - drift: use the fixture MCP + a tool with a fixed-value mapping.
- `toolkit_api.get_toolkit(mt["id"])` -> full object; then
  `pipeline_api.create_pipeline_with_nodes(name, desc, "MCP 1", nodes, tools=[full])` with nodes:
  - `MCP 1`: `type: mcp, toolkit_name: mt["toolkit_name"], tool: read_wiki_structure, input: [input], output: [messages], input_mapping: {repoName: {type: fixed, value: facebook/react}}, structured_output: false, transition: LLM 1`
  - `LLM 1`: `_llm_node_dict("END")` shape (task "say ok").
- Open `https://dev.elitea.ai/app/pipelines/all/{pid}?viewMode=owner` (deep link OK here); wait `pipeline-node-card-MCP 1`. Cleanup: `pipeline_api.delete_pipeline(pid)` + fixture deletes toolkit.
- Viewport 1600x1400; `platform-banner-corner` intercepts clicks on footer/chat buttons -> use `evaluate("e=>e.click()")` for `pipeline-node-panel-duplicate`, `-make-entrypoint`, `discard-button`, `discard-confirm-button`, `chat-send-button` (or dismiss banner via `platform-banner-close`).

## Test Steps (all executed live)
1. Open "MCP 1" panel (`open_node_panel_by_card`), click `pipeline-node-panel-duplicate` (enabled; `aria-label="Duplicate node"`). Toast (`toast-message`, `PipelineDetailPage.get_toast_text`) = "MCP 1 duplicated as MCP 1_copy". Cards: MCP 1, LLM 1, `pipeline-node-card-MCP 1_copy`. Panel auto-opens on the copy (`pipeline-node-panel-name-input` value `MCP 1_copy`). `agent-save-button` was disabled before, ENABLED after.
2. Panel YAML view (`pipeline-node-panel-view-yaml` -> `-yaml-content`, wait cm-lines) of copy: `- id: MCP 1_copy / type: mcp / input: [input] / input_mapping: {repoName: {type: fixed, value: facebook/react}} / output: [messages] / structured_output: false / tool: read_wiki_structure / toolkit_name: <mcp>` - identical to original except id, and NO `transition`. (Compare against the same panel YAML of "MCP 1" read in the same way for the "same config" assertion; also Flow-view Toolkit/Tool selects.)
3. Canvas: `rf__edge-xy-edge__MCP 1---LLM 1` and `rf__edge-xy-edge__LLM 1---EliteAPipelineEnd` only - NO edge touching MCP 1_copy (`PipelineDetailPage.CANVAS_EDGE` / testid prefix `rf__edge`). `pipeline-node-entrypoint-badge` count inside `pipeline-node-card-MCP 1` = 1, inside `MCP 1_copy` = 0.
4. Expand TOOLS (`pipeline-config-collapse-button`; hidden while panel open): `pipeline-tool-card` count 1, `pipeline-tool-card-used-by` chips ['MCP 1','MCP 1_copy'].
5. Select "MCP 1" again, duplicate: toast "MCP 1 duplicated as MCP 1_copy_2"; cards MCP 1_copy and MCP 1_copy_2. **Selecting MCP 1 is a trap**: the copy is placed offset (+40,+40) and overlaps MCP 1; `open_node_panel_by_card` (force click at centre) hits the COPY (panel name stays `MCP 1_copy`; duplicating that gives `MCP 1_copy_copy`). Click the original at an uncovered point (`node_card("MCP 1").click(position={"x":10,"y":10})`) or `evaluate("e=>e.click()")` - JS click verified: panel name = `MCP 1`. Assert panel name before duplicating.
6. `discard-button` (exists: pipeline already saved; JS click) -> `discard-confirm-button`: cards back to exactly [MCP 1, LLM 1], Save disabled.
7. Duplicate MCP 1 again (toast `_copy` again - names are free after Discard). In copy's panel click `pipeline-node-panel-make-entrypoint` (JS click; then replaced by `-entrypoint-state`). `connect_nodes("MCP 1_copy","LLM 1")` (works with panel open here) + `wait_for_edge_present`. `agent-save-button` click -> Save disabled (persisted). Badge count on whole canvas = 1, inside `MCP 1_copy` card = 1 (original lost it).
8. `open_test_pipeline_panel()`, `chat_input.fill("go")` (`chat-input` testid is the wrapper div, `PipelineDetailPage.chat_input` handles it), send via JS click on `chat-send-button`. Poll `data-status` attr of `pipeline-node-card-{name}` (set to `running` by `NodeCard.jsx:77`, absent otherwise) every 250ms: observed sequence `all None -> {MCP 1_copy: running} -> {LLM 1: running} -> all None`; `MCP 1` NEVER `running`. Thinking chip (`PipelineDetailPage.get_embedded_chat_tool_chip_texts`) = "autotest_mcp_...: read_wiki_structure (MCP1_copy)- 2.9s" (**drift: the node name in parentheses is space-stripped, "MCP1_copy" not "MCP 1_copy"**; assert `"(MCP1_copy)" in chip` / regex `\(MCP\s?1_copy\)`). Run completes (Thought accordion + final answer; `wait_for_embedded_chat_run_completion`). Poll must start BEFORE the send click settles (status flips within ~1-3s); collect transitions in a loop, assert `"MCP 1_copy"` ever `running` and `"MCP 1"` never.

Console: no errors relevant. Resolved by source: duplicate disabled for non-duplicable types (END etc.) - n/a here.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Duplicate button | testid | `pipeline-node-panel-duplicate` | - | testid on DEV ✓ (NEW page-object field needed; no existing) |
| Make Entrypoint / delete / name input / close | testid | `pipeline-node-panel-make-entrypoint` (`node_panel_make_entrypoint_button`), `-name-input`, `-close` | - | testid on DEV ✓ (exist) |
| Node card + running state | testid + attr | `pipeline-node-card-{name}` + `[data-status="running"]` | - | testid on DEV ✓; state = DEV-rendered data-* attribute filter |
| Entrypoint badge | testid | `pipeline-node-entrypoint-badge` scoped in card | - | testid on DEV ✓ |
| Toast | testid | `toast-message` / `toast-alert` (`get_toast_text`) | - | testid on DEV ✓ |
| Tool card / used-by | testid | `pipeline-tool-card`, `pipeline-tool-card-used-by` | - | testid on DEV ✓ |
| Edges | testid | `rf__edge-xy-edge__{src}---{dst}` | - | testid on DEV ✓ (`CANVAS_EDGE`) |
| Discard / confirm / save | testid | `discard-button`, `discard-confirm-button`, `agent-save-button` | - | testid on DEV ✓ |
| Test panel chat | testid | `chat-input`, `chat-send-button`, `chat-answer-tool-chip` | - | testid on DEV ✓ (existing page-object helpers) |

## Coverage Map
### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 | toast text, copy card + panel open, Save enabled | step 1 | toast text, card present, name input, save enabled | asserted |
| 2 | same MCP/Tool/mapping | step 2 | panel YAML of copy vs original (minus id/transition) + Flow selects | asserted |
| 3 | copy no edges/no badge; original keeps both | step 3 | edge ids, badge counts | asserted |
| 4 | one TOOLS entry, Used by both | step 4 | count 1 + chips | asserted |
| 5 | `_copy_2` toast + card | step 5 | toast + cards | asserted (trap: selection under overlap) |
| 6 | Discard removes both copies | step 6 | cards == [MCP 1, LLM 1], Save disabled | asserted |
| 7 | duplicate, make entrypoint, connect, save | step 7 | badge, edge, Save disabled | asserted |
| 8 | copy highlighted running, not original; chip attribution; run completes | step 8 | data-status sequence, chip text, completion | asserted |
| Note: copy placement overlap | accepted, not asserted | - | - | out-of-scope (author); only used as a click trap |
### Axis 2
- Axis-2: original MCP 1 keeps `transition: LLM 1` edge after duplication (edge present); LLM 1 runs after the copy (status sequence) proves the wiring.

## Known Defects
None. Case-text clarifications: MCP fixture instead of test-github-mcp/get_me; chip name is space-stripped "MCP1_copy"; node selection after step 1 needs an uncovered click point; Discard must be reachable (saved pipeline, true here).

## Blocked Steps
None.

## Cleanup
`pipeline_api.delete_pipeline(pid)`; MCP toolkit via fixture. Probe pipeline already deleted.

## Automation hints
- Add to `PipelineDetailPage`: `node_panel_duplicate_button` (testid), helper `duplicate_selected_node()` (JS click), `node_card_status(name)` reading `data-status`, `node_entrypoint_badge_in(name)` ScopedLocator/testid-template constant.
- DeepWiki MCP dependency: `mcp_toolkit_with_tools` retries sync (503 pool saturation possible).
- Sandbox lacks `automation/.env.test`; export `APP_PREFIX=/app`.
