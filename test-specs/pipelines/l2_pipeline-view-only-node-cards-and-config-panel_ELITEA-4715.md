# Test Case: Pipeline — View-Only Node Cards and Node Configuration Panel

## Metadata
- **TMS ID**: ELITEA-4715 (priority: high -> l2; use `@pytest.mark.p1`)
- **Linked Story**: EliteaAI/elitea_issues#7157
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted Python Playwright probes, headless, viewport 1600x1400; Playwright MCP browser unavailable — no Chrome binary). Source cross-checked on `EliteaUI origin/main` (`NodeNameField.jsx`, `NodeConfigFooter.jsx`).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation
- **surface_key**: pipelines-node-cards-and-config-panel

## Preconditions (seed via API — no UI building)
Three-node pipeline `Agent 1 (entry) -> Toolkit 1 -> Code 1 -> END`, created with `pipeline_api.create_pipeline_with_nodes(...)` (verified end to end on DEV):
- Fixtures: `agent_id` + `agent_api` (agent name = `agent_api.get_agent(agent_id)["name"]`), `github_toolkit_with_selected_tools` (selected_tools `["search_issues"]`), `toolkit_api.get_toolkit(id)`.
- **LOAD-BEARING**: the pipeline version's `tools=[...]` MUST carry BOTH the full toolkit object AND an application entry for the agent, else the panel shows "Toolkit not found / Agent not found — select a replacement or delete this node" and the Basic section is empty of names (reproduced live). Application entry that works:
  `{"type":"application","name":<agent name>,"description":"d","settings":{"application_id":<agent_id>,"application_version_id":agent_api.get_agent(agent_id)["versions"][0]["id"]}}`.
- Nodes (YAML dicts): 
  - `{"id":"Agent 1","type":"agent","input":["input"],"output":["messages"],"input_mapping":{"task":{"type":"fixed","value":"Say hello"},"chat_history":{"type":"fixed","value":[]}},"tool":<agent name>,"transition":"Toolkit 1"}`
  - `{"id":"Toolkit 1","type":"toolkit","toolkit_name":tk["toolkit_name"],"tool":"search_issues","input":["input"],"output":["messages"],"input_mapping":{"search_query":{"type":"fixed","value":"bug"}},"transition":"Code 1"}` (`toolkit_name` key from `get_toolkit()`, NOT a regex of the display name)
  - `{"id":"Code 1","type":"code","code":{"type":"fixed","value":"{\"x\": 1}"},"input":["input"],"output":["messages"],"transition":"END"}`; `entry_point="Agent 1"`.
- Open `https://dev.elitea.ai/app/pipelines/all/<id>?viewMode=owner` (bare URL without `viewMode` can 404); `dismiss_banner_if_present()`; viewport height >=1400 (the `platform-banner-corner` otherwise intercepts the panel footer click; "Make Entrypoint" click timed out on it at default height).
- Cleanup: `pipeline_api.delete_pipeline(id)`; fixtures clean agent/toolkit/credential.

## Test Steps (executed live; every step observed)
1. Open pipeline. Cards `pipeline-node-card-Agent 1`, `-Toolkit 1`, `-Code 1` present; End node is `pipeline-end-node` (inside `rf__node-END`), text "End". Case's `pipeline-node-card-<Name>` naming confirmed (3 cards; END is NOT a `pipeline-node-card-*`).
2. Inside each `rf__node-{name}`: input/select/textarea/contenteditable count = 0 on all four nodes. Card testids inside: `pipeline-node-icon-tile`, `pipeline-node-name`, `pipeline-node-type` (Agent/Toolkit/Code), `pipeline-node-summary` (+ `-primary`, `-secondary` when configured), `pipeline-node-add-from-output-{name}-source` (a 16px connection handle, not an editable field). Toolkit 1 has primary only (no secondary).
3. `pipeline-node-entrypoint-badge` count on page = 1, inside `rf__node-Agent 1` ("Entrypoint").
4. Toolkit 1 `pipeline-node-summary-primary` = `"<toolkit name> › search_issues"` (U+203A separator; toolkit name is truncated on the card to ~28 chars, e.g. `autotest_gh_tk_tools_test_scratc`). Click card (`force=True`; wait `pipeline-node-panel-name-input` value == "Toolkit 1") -> panel (`pipeline-node-panel`, drawer). `pipeline-node-panel-basic-section` text contains `Toolkit`, the toolkit name (`autotest_gh_tk_tools_...`) and `Tool / search_issues` as separate fields -> assert each half of the card text (split on " › ") is contained in the panel text (partial match; truncation means compare card-half `in` panel, never panel in card). **Panel settles asynchronously** — poll the basic section until it no longer contains "not found" (0-1.5 s with the seed above).
5. Click Agent 1 card -> panel name input value "Agent 1"; Basic section contains the agent name (card primary = agent name, exact).
6. `pipeline-node-panel-close` -> `pipeline-node-panel-name-input` detached.
7. Click Code 1 card; `pipeline-node-panel-make-entrypoint` ("Make Entrypoint", footer) click -> button is replaced by `pipeline-node-panel-entrypoint-state` ("Entrypoint"). Badge now only inside `rf__node-Code 1` (badge count 1). Existing `PipelineDetailPage.make_node_entrypoint("Code 1")` does exactly this.
8. Clear panel Name (`fill("")`): helper text "Name is required" (MUI `p.MuiFormHelperText-root.Mui-error`, no testid; locate via `get_by_text("Name is required", exact=True)`), name input `aria-invalid="true"`. **Case-text drift: Save is NOT disabled** (`agent-save-button` stays enabled; enabled because step 7 made the pipeline dirty — the draft name is local to the field and is never committed while invalid). Card title unchanged ("Code 1").
9. `fill("Code renamed")`: error disappears immediately (0). **Card title does NOT update on typing** — `NodeNameField` commits on blur or Enter (`onBlur=commit`, `Enter -> blur`). After `press("Enter")` (or Tab): card `pipeline-node-card-Code renamed` exists and `Code 1` card is gone; panel name input shows "Code renamed".
10. Click `agent-save-button`; wait for the PUT/save to settle; reload (same canonical URL): `pipeline-node-card-Code renamed` present, entrypoint badge only on `rf__node-Code renamed`, card text "Code renamed / Code / {"x": 1} ...". Persisted. Console errors 0 observed.

## Expected Results
As the case, with the two clarifications below (Save not disabled; rename commits on Enter/blur).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open pipeline | cards Agent 1 / Toolkit 1 / Code 1 + End | step 1 | 3 `pipeline-node-card-*` + `pipeline-end-node` | asserted |
| 2 view-only cards | no editable inputs/selects/textareas; header + summary | step 2 | per node: 0 `input,select,textarea,[contenteditable=true]`; name/type/summary present | asserted |
| 3 entry badge | only Agent 1 | step 3 | badge count 1, inside Agent 1 | asserted |
| 4 Toolkit card -> panel | panel opens; card text also in Basic section (partial) | step 4 | panel visible; both halves of primary in basic-section text | asserted |
| 5 Agent card -> panel switches | panel shows agent name | step 5 | name input == "Agent 1"; agent name in basic section | asserted |
| 6 close | panel closes | step 6 | name input detached | asserted |
| 7 Make Entrypoint | Code 1 badge, Agent 1 none | step 7 | badge locators per node | asserted |
| 8 clear Name | "Name is required"; Save disabled | step 8 | message visible + aria-invalid | asserted for message; **"Save is disabled" = clarification (not true on DEV)** |
| 9 type new name | message gone; card title updates | step 9 | message count 0; card title after Enter | asserted (needs Enter/blur — clarification) |
| 10 Save + reload | card renamed + badge persists | step 10 | post-reload card + badge | asserted |

### Axis 2 — Analyst additions
- Step 2: also assert END node has no `pipeline-node-card-*` and no editable input (grounded: it is rendered by `pipeline-end-node`).
- Step 8: assert the card title still reads "Code 1" while the draft is invalid (grounded: observed; proves invalid draft is not committed).
- Step 10: assert badge count == 1 after reload on the renamed card (grounded: observed).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Node card | 1 | `pipeline-node-card-{name}` | — | testid on DEV ✓ |
| Canvas node wrapper | 1 | `rf__node-{id}` (existing `RF_NODE_TESTID`) | — | testid on DEV ✓ |
| Card name/type | 1 | `pipeline-node-name`, `pipeline-node-type` | — | testid on DEV ✓ |
| Summary | 1 | `pipeline-node-summary`, `-primary`, `-secondary` (existing `NODE_SUMMARY*` consts) | — | testid on DEV ✓ |
| Entry badge | 1 | `pipeline-node-entrypoint-badge` (existing `NODE_ENTRYPOINT_BADGE`, `node_entrypoint_badge()`) | — | testid on DEV ✓ |
| End node | 1 | `pipeline-end-node` | — | testid on DEV ✓ (not yet a field? grep before adding) |
| Panel / basic section | 1 | `pipeline-node-panel`, `pipeline-node-panel-basic-section` (existing `NODE_PANEL_BASIC_SECTION`) | — | testid on DEV ✓ |
| Panel name input | 1 | `pipeline-node-panel-name-input` (existing field) | — | testid on DEV ✓ |
| Panel close | 1 | `pipeline-node-panel-close` (existing) | — | testid on DEV ✓ |
| Make Entrypoint / state | 1 | `pipeline-node-panel-make-entrypoint` (existing), `pipeline-node-panel-entrypoint-state` | — | testid on DEV ✓ |
| Save | 1 | `agent-save-button` | — | testid on DEV ✓ |
| "Name is required" helper | 3/2 | `get_by_text("Name is required", exact=True)` scoped to the panel (`pipeline-node-panel`) | `pipeline-node-panel-name-error` | ladder — no testid on DEV (MUI FormHelperText `id=":r..:-helper-text"`, generated; do not use). Verified unique in panel scope. |

Reuse: `PipelineDetailPage.make_node_entrypoint`, `close_node_panel`, `_select_node`, `node_panel_*` fields, `node_entrypoint_badge`, `dismiss_banner_if_present`, `wait_for_canvas`. New page-object work: card-field helpers (`pipeline-node-card-{}` ScopedLocator, editable-control count), name-error field.

## Network Behavior
Save = PUT application version; no failing requests observed; console errors 0.

## Known Defects Found During Exploration
- none.

## Case-text clarifications (soft, not defects)
- Step 8: "Save is disabled" does not hold — Save stays enabled when the Name is invalid (draft is local, nothing committed). Assert the message + `aria-invalid`, and that the card title is unchanged; do NOT assert Save disabled. (Ask the lead whether to open a clarification on the TMS case.)
- Step 9: card title updates on commit (Enter/blur), not per keystroke (source: `NodeNameField.jsx` onBlur/Enter).
- Step 4/5: summary text is `<toolkit> › <tool>` and truncated; compare per half.
- Precondition seed needs the application/toolkit entries in the version `tools` (above), otherwise "not found" banners.

## Blocked Steps
- none.
