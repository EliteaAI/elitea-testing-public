# Test Case: Pipeline — Tools Selected in Nodes: Auto-Attach and Read-Only TOOLS Section

## Metadata
- **TMS ID**: ELITEA-4718 (priority: critical -> l1; use `@pytest.mark.p0`)
- **Linked Story**: EliteaAI/elitea_issues#7159 (epic 7093)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted Python Playwright, headless, viewport 1600x1400; Playwright MCP browser unavailable: no Chrome binary). Source cross-checked on `EliteaUI origin/main` (`features/pipelines/tool-picker/ui/*`).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation
- **surface_key**: pipelines-node-tool-picker-tools-section

## Preconditions
- Non-MCP toolkit in the project: the artifact toolkit works with no secrets (`toolkit_api.create_artifact_toolkit`, or POST `/elitea_core/tools/prompt_lib/{pid}` with `type: artifact`, `selected_tools: [list_files, create_file, read_file]`; needs a bucket name string only - bucket need not exist). Use `artifact_toolkit` fixture or `github_toolkit_with_selected_tools` (skips without GIT_HUB_TOKEN). Prefer artifact (always runnable).
- MCP: `mcp_toolkit_with_tools` fixture (case step 2 "no MCPs" - NOT observed live: DEV project had no other toolkit; source `ProjectToolkitPicker.jsx` filters MCP out; assert the MCP name is absent from the picker).
- DEV account project (575 "Private") had ZERO toolkits before the probe: picker then shows `pipeline-toolkit-node-toolkit-select-menu-empty` "No toolkits in this project yet". Fixture-created toolkit is the only row -> picker rows are deterministic.
- Pipeline is created through the UI (case step 1 is "create a new pipeline"): `/pipelines/create?viewMode=owner`. Cleanup: delete pipeline (id from URL after Save) + toolkit via API.

## Test Steps (executed live; every step observed)
1. Open `/pipelines/create?viewMode=owner`. `pipeline-tools-section` text = "TOOLS / Tools you select in nodes will appear here. / MODULES / Attachments"; `pipeline-tools-section-empty` = "Tools you select in nodes will appear here." Buttons inside section: only the accordion header "TOOLS" (1 button). `agent-add-toolkit-button`, `agent-add-mcp-button`, `agent-add-agent-button`, `agent-add-pipeline-button` all count 0.
2. `pipeline-empty-state-add-node-button` -> `pipeline-add-node-menu-item-toolkit` -> Toolkit 1 node, panel opens. Click `pipeline-toolkit-node-toolkit-select` -> `pipeline-toolkit-node-toolkit-select-menu` with `-menu-search` (placeholder "Search toolkits..."), `-create-new` ("Create new"), rows `pipeline-toolkit-node-toolkit-select-option` (text = name + description). Rows lists only the project's non-MCP toolkits (see Preconditions).
3. Click the row of the fixture toolkit -> combobox shows name with `-clear` X (`pipeline-toolkit-node-toolkit-select-clear`). Tool select `pipeline-toolkit-node-tool-select`; options `select-option-{tool}` (create_file, list_files, read_file); pick one. **TOOLS is HIDDEN while the node panel is open** (left config panel collapses): `pipeline-tools-section` count 0 until `pipeline-config-collapse-button` is clicked (or the node panel closed). Then TOOLS has ONE `pipeline-tool-card`: text "<toolkit> / Show tools / Used by / Toolkit 1"; `pipeline-tool-card-used-by` chip text "Toolkit 1"; `pipeline-tool-card-show-tools` "Show tools" (renders only when the toolkit has selected_tools).
4. Close panel (`pipeline-node-panel-close`), add second Toolkit node (`pipeline-add-node-button` -> menu item toolkit; name "Toolkit 2"), open its picker: the fixture row contains `pipeline-toolkit-node-toolkit-select-option-in-use` (child of the row; count 1); the row text includes "In use".
5. Click that row: toolkit select shows it; (expand TOOLS) still ONE `pipeline-tool-card`, `used-by` chips ['Toolkit 1','Toolkit 2'].
6. Click chip `pipeline-tool-card-used-by` with text "Toolkit 1" then "Toolkit 2": the node panel opens with `pipeline-node-panel-name-input` value == that node name (panel opening collapses TOOLS again -> re-expand before the next click).
7. With Toolkit 2 panel open click `pipeline-toolkit-node-toolkit-select-clear`: (expand TOOLS) one card, chips ['Toolkit 1'].
8. Click card `pipeline-node-card-Toolkit 1`, clear it: `pipeline-tool-card` count 0 and `pipeline-tools-section-empty` count 1. Header `discard-button` enabled (was DISABLED right after Save). **The Discard button does not exist on an unsaved new pipeline (count 0 before first Save)** -> the test MUST fill name (`agent-name-input`, only reachable with TOOLS panel expanded via `pipeline-config-collapse-button`) and click `agent-save-button` once BEFORE step 8-9 (URL becomes `/pipelines/all/{id}?...`). Do the save after step 5 (attach persists to Save); steps 6-9 then run on the saved pipeline - verified: after save card still ['Toolkit 1','Toolkit 2'] and clearing behaves identically.
9. Click `discard-button` (use `evaluate("e=>e.click()")`, banner can overlay; `PipelineFormPage.click_discard`) -> dialog "Are you sure you want to discard changes?" with Cancel / `discard-confirm-button` ("Discard"). Confirm -> TOOLS card back with chips ['Toolkit 1','Toolkit 2']; clicking cards Toolkit 1 and Toolkit 2 both show the toolkit name in `pipeline-toolkit-node-toolkit-select` (observed text = toolkit name).
10. For both nodes: click card, `-select-clear`. Click `agent-save-button` (Save becomes disabled = persisted). Click `pipeline-yaml-view`; **wait for `.cm-line` count > 5** (the editor first renders only 4 lines "state:/entry_point:/nodes:" - reading too early gives a false "clean" YAML, I was fooled by this once). YAML after clear (verbatim) for node: `- id: Toolkit 1 / type: toolkit / input: [] / input_mapping: {} / output: [] / structured_output: false / transition: END` - NO `toolkit_name`, NO `tool`, NO mapped params. Before clear (control, with tool create_file + filename mapped): `input_mapping: {filename: {type: fixed, value: a.txt}, ...}, tool: create_file, toolkit_name: <toolkit>`. CASE-TEXT DRIFT: the empty key `input_mapping: {}` remains -> assert no `toolkit_name:`, no `tool:` line, and `input_mapping: {}` (no entries) rather than "no input_mapping".
11. New pipeline (or same) -> add Agent node (`pipeline-add-node-menu-item-agent`), click `pipeline-agent-node-agent-select`: menu `pipeline-agent-node-agent-select-menu` with `-menu-search`, `-create-agent`, `-create-pipeline`, rows `pipeline-agent-node-agent-select-option` (scroll-loaded, ~76 rows on DEV). Group titles "Agents" and "Pipelines" are plain MUI `span.MuiTypography-labelSm` WITHOUT testid (rendered only when both groups non-empty; source `PickerMenu.jsx:49`) - `menu.get_by_text("Agents", exact=True)` count 1 each (ladder: no role; `suggested_testid=pipeline-agent-node-agent-select-group-title-{}`; scoped under the menu testid).
12. Click a row: panel Agent 1; TOOLS card text "<agent name> / base / Used by / Agent 1"; `pipeline-tool-card-version` = "base". (Seed the agent: use `agent_id` fixture, pick row by `filter(has_text=agent name)` + search `-menu-search`.)

Console: only a 503 `Failed to load resource` (unrelated asset) across the run.

## Existing page-object handles (reuse; verified on DEV)
`PipelineDetailPage`: `toolkits_section`, `toolkit_card`, `TOOLKIT_CARD_USED_BY`, `is_toolkit_card_used_by_node`, `open_toolkit_node_picker`, `select_toolkit_node_toolkit` (search then click row), `toolkit_node_toolkit_select`, `toolkit_node_tool_select`, `clear_mcp_node_toolkit` (MCP variant, the toolkit clear `pipeline-toolkit-node-toolkit-select-clear` has no helper yet), `agent_node_agent_select`, `agent_node_agent_select_clear`, `AGENT_NODE_PICKER_OPTION/SEARCH`, `add_node`, `switch_to_yaml_view`, `get_yaml_content` (add the cm-line wait), `toggle_config_panel_collapse`; `PipelineFormPage`: `click_save`, `click_discard`, `name_input`.
New handles needed (class-level): `pipeline-tools-section-empty`, `-in-use` suffix, `pipeline-toolkit-node-toolkit-select-clear/-create-new/-menu-search`, `pipeline-agent-node-agent-select-create-agent/-create-pipeline`, `pipeline-tool-card-version`, `pipeline-tool-card-name`, group titles (ladder), dialog confirm `discard-confirm-button`. All testids above exist on DEV (rung 1) except group titles.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| TOOLS section / empty text | testid | `pipeline-tools-section`, `-empty` | - | testid on DEV ✓ |
| Add buttons absent | testid | `agent-add-{toolkit,mcp,agent,pipeline}-button` count 0 | - | testid on DEV ✓ (absence) |
| Tool card / used-by / show-tools / version / name | testid | `pipeline-tool-card[-used-by|-show-tools|-version|-name]` | - | testid on DEV ✓ |
| Toolkit picker trigger/menu/search/create/option/in-use/clear | testid | `pipeline-toolkit-node-toolkit-select[-menu|-menu-search|-create-new|-option|-option-in-use|-clear]` | - | testid on DEV ✓ |
| Agent picker (same suffixes + `-create-agent`, `-create-pipeline`) | testid | `pipeline-agent-node-agent-select*` | - | testid on DEV ✓ |
| Group titles Agents/Pipelines | ladder - no testid | text-exact scoped under `pipeline-agent-node-agent-select-menu` | `pipeline-agent-node-agent-select-group-title-{}` | ladder - no testid on DEV; unique within menu |
| Discard / confirm | testid | `discard-button`, `discard-confirm-button` | - | testid on DEV ✓ |
| Config panel collapse | testid | `pipeline-config-collapse-button` | - | testid on DEV ✓ |
| YAML view / editor | testid | `pipeline-yaml-view`, `pipeline-yaml-editor` + `.cm-line` | - | testid on DEV ✓ (cm-line third-party) |

## Coverage Map
### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 | empty text, no 4 add buttons | step 1 | text + counts 0 | asserted |
| 2 | picker lists toolkits (no MCP), search, Create new | step 2 | row names, search/create-new visible, MCP name absent | asserted (MCP absence by fixture, not live-observed) |
| 3 | toolkit in TOOLS, Used by Toolkit 1, Show tools | step 3 | card text/chip/toggle | asserted |
| 4 | "In use" marker | step 4 | in-use testid | asserted |
| 5 | one entry, Used by both | step 5 | card count 1, chips | asserted |
| 6 | click Used-by name selects node + opens panel | step 6 | panel name input | asserted ("selected on canvas": panel opens; canvas-selected class not asserted) |
| 7 | clear on Toolkit 2 keeps entry w/ Toolkit 1 | step 7 | chips | asserted |
| 8 | clear on last removes entry, Discard enabled | step 8 | count 0, discard enabled | asserted - **drift: pipeline must be saved once first (Discard absent on unsaved new pipeline)** |
| 9 | Discard restores both | step 9 | selects + chips | asserted |
| 10 | clear both, Save, YAML clean | step 10 | no toolkit_name/tool lines, `input_mapping: {}` | asserted - **drift: empty `input_mapping: {}` key remains** |
| 11 | picker grouped Agents / Pipelines | step 11 | group titles | asserted |
| 12 | agent in TOOLS with version "base", Used by Agent 1 | step 12 | card text + version testid | asserted |
| Note: orphan "Not used by any node" | - | - | `pipeline-tool-card-not-used` exists in source | out-of-scope (author: covered manually) |
### Axis 2
- No console-error check beyond known 503 (optional soft check). Save disabled after save (persistence signal). YAML control read before clear to prove the keys WERE present (otherwise a clean-YAML assertion is vacuous - the early-render trap).

## Known Defects
None. Case-text clarifications: Discard needs a saved pipeline (step 8-9); `input_mapping: {}` remains (step 10); TOOLS hidden while node panel open (steps 3,6,7); toolkit card appears on toolkit selection alone (tool not required) but "Show tools" needs selected_tools.

## Blocked Steps
None. Not observed live: MCP absence from toolkit picker (no MCP fixture exercised).

## Cleanup
Delete pipeline via `pipeline_api.delete_pipeline(id)` (id parsed from URL after Save); toolkit/credential via fixtures. Probe residue already deleted (pipelines 4167-4172, toolkits 976-979 returned 204).

## Automation hints
- Sandbox lacks `automation/.env.test`; `dev_storage_state.py` login failed on the 2nd run (cookies from the first run still valid).
- After attaching via node, pre-Save the attachment is unsaved (that is what Discard reverts).
- Use viewport height >=1400 and dismiss banners.
