# Test Case: MCP Integration in Pipeline — Change MCP Toolkit and Tool Selection

## Metadata
- **TMS ID**: ELITEA-1954
- **Linked Story**: EliteaAI/elitea-testing-public#61
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend `dev.elitea.ai`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths; sidebar showed "Elitea is connected")
- **Analyst**: qa-engineer (agent), session 2026-07-15
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with an MCP node already configured with a Toolkit and Tool.
- At least two MCP toolkits are attached in the pipeline's TOOLS section, and both actually expose a non-empty tool list (a "Load Tools"-populated MCP, not one pointed at a placeholder/fake URL) — this is required for steps 4–8 to be meaningfully observable, and was NOT explicit in the original case text but is necessary to execute it (see Coverage Map / Test Data).
- **CLARIFICATION on case-gate `status: draft`**: this case's TMS frontmatter carries `status: draft`, matching every sibling case in `tests/automated-full-regression-ui/mcp/` except `ELITEA-1922` (which flips to `status: ready` / `execution_type: automated` once picked up). This is the project's convention for "not yet automated," not an author signal to skip — confirmed by cross-checking the whole `mcp/` directory. Proceeded to Phase 1 rather than returning `out-of-scope-by-author`. Recorded to memory so future dispatches don't re-litigate this.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline (`autotest_pipeline_mcp_<unique>`) with an MCP node.
- A second Remote MCP toolkit with a **real, working tool list** — the two pre-existing test MCPs in this environment (`autotest_remote_mcp_full`, `verify_ttl_*`, `verify_secret_*`) all point at placeholder URLs (e.g. `mcp.example.com`) and return **zero tools**, and the "Remote Github" / "f" (Figma) MCPs require an OAuth login this session couldn't complete. The implementer needs at least one MCP that both (a) is already attached to the pipeline and (b) returns tools without an interactive OAuth step. This session created `autotest_deepwiki_mcp_1954` pointing at the public, auth-free `https://mcp.deepwiki.com/mcp` (3 tools: `read_wiki_structure`, `read_wiki_contents`, `ask_question`) specifically to satisfy this. **Recommend the implementer's fixture do the same** — provision a throwaway Remote MCP against a known auth-free public MCP endpoint (or a project-controlled mock MCP server if one exists) rather than reusing the existing placeholder-URL MCPs, which cannot demonstrate the Tool-dropdown-repopulation behavior this case is actually testing.
- A first MCP toolkit that already had tools (this session reused the pre-existing `Remote Github` MCP, id `3`, whose Tools list is pre-cached with 38 GitHub tool names even though its live OAuth session shows "disconnected" — the cached tool list still renders and is selectable client-side without a live connection).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Navigate to `${BASE_URL}/pipelines/all/{pipeline_id}?destTab=configuration&name={pipeline_name}&viewMode=owner` for a pipeline with an MCP node already configured with a Toolkit and Tool.
   - **Verify**: Configuration panel (General/Tools/... accordion) is visible; canvas loads past "Preparing the flow editor..." placeholder.
2. Locate the MCP node on the ReactFlow canvas (`[data-testid="rf__node-{node_display_name}"]`, e.g. `rf__node-MCP 1`).
   - **Verify**: node's config fields (Trigger, Toolkit, Tool, Input, Output) are visible directly inline on the node body — **no separate click-to-open action is needed**; the config panel is always-expanded on the canvas card itself (this differs from the case text's step 2 wording "Click on the MCP node to open configuration panel" — see Coverage Map).
3. Read the current Toolkit and Tool combobox values from the node.
   - **Verify**: values match what was configured (in this session: Toolkit=`RemoteGithub`, Tool=`search_repositories`).
4. Click the Toolkit combobox (`#simple-select-Toolkit`, scoped inside the node's `rf__node-*` container).
   - **Verify**: the opened `listbox` lists exactly the MCP toolkits attached in the pipeline's TOOLS section — both `autotest_deepwiki_mcp_1954` and `RemoteGithub` appeared, the currently-selected one marked `[selected]`.
5. Click the other MCP option in the listbox (`[data-testid="select-option-{mcp_name}"]`, e.g. `select-option-autotest_deepwiki_mcp_1954`).
   - **Verify**: Toolkit combobox now shows the newly selected MCP name.
6. Observe the Tool combobox (`#simple-select-Tool`) immediately after the Toolkit change, then click it to open its `listbox`.
   - **Verify**: Tool field visibly reset to empty the instant Toolkit changed (confirmed via snapshot: Tool combobox had no accessible name / empty textbox right after step 5, before any further interaction). Then, on open, the `listbox` shows exactly the 3 tools belonging to the newly selected MCP (`ask_question`, `read_wiki_contents`, `read_wiki_structure`) — **no stale tools from the previous MCP (`RemoteGithub`'s 38 GitHub tools) leaked through.**
7. Click a tool from the new MCP's list (`[data-testid="select-option-ask_question"]`).
   - **Verify**: Tool combobox shows `ask_question`.
8. Observe the node body for an "Input mapping (required N)" section that appears below the generic Input/Output state-variable selectors.
   - **Verify**: a new collapsible section titled `Input mapping (required 2)` appeared, containing one row per the new tool's actual parameters — `RepoName` and `Question` for `ask_question` — each with its own `Type` (`Fixed`/other) selector and `Value` text input. **This IS the "Input/Output variables update according to new tool" behavior the case describes** — it is per-tool-parameter mapping, not a change to the separate, tool-agnostic `Input`/`Output` state-variable dropdowns (`#simple-select-Input` / `#simple-select-Output`, which stay fixed to whatever pipeline-state keys — e.g. `input`/`messages` — were already selected and are NOT tool-schema-driven; see Coverage Map for why this needed correcting from a literal reading of the case).
9. Fill the new required Input-mapping fields (e.g. `RepoName` = `EliteaAI/elitea-testing-public`, `Question` = `What is this repository about?`) and click the pipeline's Save button (`[data-testid="agent-save-button"]`).
   - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` returns `201 Created`; no new console errors after save.
10. Reload the page at the same URL (query params included — see Known Defects for why the bare `/pipelines/all/{id}` URL 404s).
    - **Verify**: after reload, the MCP node shows the persisted new state — Toolkit=`autotest_deepwiki_mcp_1954`, Tool=`ask_question`, Input-mapping section still present with `RepoName`/`Question` fields and the previously-typed values (`EliteaAI/elitea-testing-public` / `What is this repository about?`) intact.

## Expected Results
- Toolkit dropdown on an MCP node lists every MCP attached in the pipeline's TOOLS section.
- Selecting a different Toolkit immediately resets the Tool field to empty and repopulates the Tool dropdown with exactly that toolkit's own tools (no stale entries from the previous toolkit).
- Selecting a new Tool reveals a per-tool "Input mapping (required N)" section with the new tool's actual parameter names — this is the observable "Input/Output variables update" behavior.
- Saving persists all of the above; a full page reload with the pipeline's canonical URL (including its query params) confirms the new Toolkit, Tool, and Input-mapping values survive reload unchanged.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with MCP node configured with Toolkit+Tool; ≥2 MCPs in TOOLS | setup exists | steps 1–3 | step 3: read current values | asserted — **case's precondition additionally requires the ≥2 MCPs to have real (non-empty) tool lists for steps 4–8 to be observable; this was not stated but is load-bearing — flagged in Test Data** |
| 1 Open a pipeline with an MCP node already configured with a Toolkit and Tool | Configuration panel loads | step 1 | step 1: panel visible | asserted |
| 2 Click on the MCP node to open configuration panel | Panel is visible | step 2 | step 2 | asserted — **CLARIFICATION: live product has no click-to-open action; the node's config fields (Toolkit/Tool/Input/Output) are always rendered inline/expanded on the canvas card. Case text describing a "click to open" step is stale relative to the live UI (reverse-masking guard) — the panel doesn't need opening because it's never collapsed. Not a defect: this is a UX simplification, and the observable ("panel is visible") is still true and asserted.** |
| 3 Note current Toolkit selection and Tool | Current selections observed | step 3 | step 3 | asserted |
| 4 Click "Toolkit" dropdown — verify it lists all MCPs attached in TOOLS section | All attached MCPs listed | step 4 | step 4: listbox options | asserted |
| 5 Select a different MCP | New Toolkit selected | step 5 | step 5: combobox value | asserted |
| 6 Verify "Tool" dropdown resets and repopulates with tools from the newly selected MCP | Tool dropdown shows tools from new MCP | step 6 | step 6: empty-then-repopulated, exact 3-tool set | asserted |
| 7 Select a tool from the new MCP | New tool selected | step 7 | step 7: combobox value | asserted |
| 8 Verify Input/Output variables update according to new tool | Variable chips reflect new tool's parameters | step 8 | step 8: "Input mapping (required 2)" section with RepoName/Question | asserted — **CLARIFICATION: the case's "Input/Output variables" language maps to a distinct UI element than the always-present `Input`/`Output` state-variable dropdowns (which do NOT change with tool selection — they select which pipeline-state key feeds/receives the node, orthogonal to the tool's own parameter schema). The tool-parameter-driven element is the separate "Input mapping (required N)" accordion. Asserting the literal `Input`/`Output` dropdowns for a change would be a false expectation against the live product; asserting the Input-mapping section is the correct, live-observed contract.** |
| 9 Save pipeline | Pipeline saved successfully | step 9 | step 9: 201 + no console errors | asserted |
| 10 Reload — verify new Toolkit and Tool selections persisted | Selections unchanged after reload | step 10 | step 10: all fields + mapping values persisted | asserted |
| Expected Final State: new selections persisted after save, confirmed on reload | — | steps 9–10 | steps 9–10 | asserted |
| Pass/Fail: all steps complete without errors; Toolkit change resets Tool dropdown; new selections persist | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 10 additionally asserts the Input-mapping **values** (`RepoName`/`Question` text) persist, not just the Toolkit/Tool selectors — *added: the case only mentions "Toolkit and Tool selections" persisting, but since step 8/9 introduced per-tool parameter values, an implementer who only re-asserts Toolkit+Tool would miss a real regression where the tool changes correctly but its filled-in parameter values are silently dropped on save/reload.*
- No console-error assertion was in the original case text; added it to steps 9 and throughout as a side-channel check — *standard practice per this project's `test-case-analysis` skill; zero console errors were observed across the whole flow, no defect to report.*
- Flagged the bare-URL reload 404 as a CLARIFICATION-worthy environment quirk (see Known Defects) rather than folding it into the case's Pass/Fail — *added because a naive implementer reload via `page.reload()` after `page.goto(bare_url)` would intermittently 404 depending on which URL variant the test harness used to first navigate; worth calling out explicitly so the implementer's reload step reuses the full canonical URL (with `destTab`/`name`/`viewMode` query params), consistent with what this session observed working.*

## Cleanup

1. This session created a persistent pipeline (`autotest_pipeline_mcp_1954`, id `4825`) and a persistent Remote MCP toolkit (`autotest_deepwiki_mcp_1954`, id `1266`) on the local DEV backend (`dev.elitea.ai`, project `399`). **Neither was deleted by this analysis session** (analyst does not have automation authoring/cleanup authority — per `.agents/workflow.md`; the implementer's test + teardown is the durable cleanup mechanism, matching the precedent set in `l1_create-remote-mcp-all-fields-populated_ELITEA-1922.md`).
2. Implementer teardown: delete pipeline `4825` via `PipelineAPI` (existing client, confirms via `DELETE {ELITEA_API_BASE}/elitea_core/application/prompt_lib/{PROJECT_ID}/{pipeline_id}` per the `pipeline_id` fixture's existing pattern in `automation/fixtures/data_fixtures.py`), and delete toolkit `1266` via `ToolkitAPI.delete_toolkit(1266)` (`automation/api/client.py`, confirmed present from ELITEA-1922 precedent).
3. Flag to the lead: either delete pipeline `4825` / toolkit `1266` manually before the automated test's own data starts accumulating, or treat as harmless manual-exploration residue (both are `Private`-project-scoped with unique-enough names).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| MCP node on canvas | `[data-testid="rf__node-{node_display_name}"]` (dynamic, e.g. `rf__node-MCP 1`; ReactFlow's own testid convention, matches existing `rf__wrapper`) | none — third-party ReactFlow widget, testid-only |
| Toolkit select (inside node) | `#simple-select-Toolkit` scoped to the node's `rf__node-*` container (`getByRole('combobox', { name: <current value> })` also works but the accessible name changes with the value — prefer the stable `id`) | **NO `data-testid` exists on this element — flagged to `add-data-testid`.** Recommended name: `pipeline-mcp-node-toolkit-select`. |
| Tool select (inside node) | `#simple-select-Tool` scoped to the node container | **NO `data-testid` — flag to `add-data-testid`.** Recommended: `pipeline-mcp-node-tool-select`. |
| Input select (inside node, tool-agnostic state var) | `#simple-select-Input` scoped to the node container | **NO `data-testid` — flag to `add-data-testid`.** Recommended: `pipeline-mcp-node-input-select`. |
| Output select (inside node, tool-agnostic state var) | `#simple-select-Output` scoped to the node container | **NO `data-testid` — flag to `add-data-testid`.** Recommended: `pipeline-mcp-node-output-select`. |
| Select dropdown option (Toolkit/Tool/Input/Output all share this pattern) | `[data-testid="select-option-{value}"]` (e.g. `select-option-RemoteGithub`, `select-option-ask_question`, `select-option-input`, `select-option-messages`) — **confirmed present and reliable**, dynamic per option value | none needed |
| Input-mapping "Value" text field (per tool parameter, e.g. RepoName/Question) | **NO stable handle** — confirmed via DOM inspection: no `data-testid`, no unique `name`/`id` distinguishing one parameter row from another (`name="value"` on every row, auto-generated MUI `id`). Located this session via `getByRole('textbox', {name:'Value'}).nth(i)`, which is positional and WILL break if the tool's parameter order or count changes. **Flag to `add-data-testid`**: recommend `pipeline-mcp-node-input-mapping-value-{param_name}` (dynamic per parameter key, e.g. `pipeline-mcp-node-input-mapping-value-RepoName`), matching this project's dynamic-testid convention (`.agents/testing.md` § Locator policy). | Positional `nth()` only — brittle, do not ship without the testid. |
| Add-MCP button (pipeline Tools section) | `page.getByTestId('agent-toolkits-section').getByRole('button', { name: 'MCP' })` — the **container** has testid `agent-toolkits-section`, but the 4 tab buttons inside (Toolkit/MCP/Agent/Pipeline) only the "Toolkit" one has its own testid (`agent-add-toolkit-button`); MCP/Agent/Pipeline tabs have none. **Flag to `add-data-testid`**: recommend `agent-add-mcp-button`, `agent-add-agent-button`, `agent-add-pipeline-button` for parity. | Role-based, works today but inconsistent with policy |
| MCP-in-search-popper option | `[data-testid="select-option-{mcp_name}"]` — same pattern as node dropdowns, confirmed working for attaching MCPs to the pipeline's TOOLS section (e.g. `select-option-RemoteGithub`) | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed, shared with agent/pipeline create-and-edit forms | none needed |
| Remote MCP type-selector card (for provisioning the test-data MCP) | `[data-testid="toolkit-type-card-mcp"]` — confirmed working (known click-locator-ambiguity gotcha from prior sessions: a naive `getByText('Remote MCP')` resolves to the wrong ancestor; use the testid) | none — testid-only per policy |
| Toolkit Name / Url inputs (MCP create form) | `[data-testid="toolkit-form-name-input"]` / `[data-testid="toolkit-field-url-input"]` — confirmed reused from `l1_create-remote-mcp-all-fields-populated_ELITEA-1922.md` | none |
| "Load Tools" button (MCP create/detail form) | confirmed clickable via `page.locator('div').filter({ hasText: /^Load Tools$/ }).click()` — **NO testid found**; flag to `add-data-testid` as `toolkit-load-tools-button` | text-filter locator, brittle |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on the pipeline Save click; `201 Created` on success; this is the single request that persists the MCP node's Toolkit/Tool/Input/Output/Input-mapping state — wait for this response before asserting reload persistence, not a fixed timeout.
- `GET ${ELITEA_API_BASE}/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires per attached MCP toolkit on pipeline load/save; returns the toolkit's tool list that populates the Tool dropdown.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on page load/reload; confirms persisted node config (Toolkit/Tool/Input/Output/Input-mapping) is what the Flow-view canvas renders from.

## Known Defects Found During Exploration

**None found in the MCP-node Toolkit/Tool-switching feature itself.** All 10 case steps produced the expected result: Toolkit dropdown correctly lists all attached MCPs, switching Toolkit correctly resets and repopulates the Tool dropdown with exactly the new MCP's own tools (no stale leakage), the per-tool Input-mapping section correctly updates to the new tool's actual parameters, and all of Toolkit/Tool/Input/Output/Input-mapping-values correctly persisted through save + full reload.

Two environment/case-text observations were filed as CLARIFICATIONs (not bugs), consistent with the reverse-masking guard:

- **[INFO] Direct navigation to `/pipelines/all/{id}` (no query params) shows "Page not found"** — filed as `EliteaAI/elitea-testing-public#512` (label `question`). Confirmed during this session: `http://localhost:5173/pipelines/all/4825` (bare) renders a 404-style "Page not found" page, while `http://localhost:5173/pipelines/all/4825?destTab=configuration&name=<pipeline_name>&viewMode=owner` (the URL the app itself navigates to after Save) loads correctly. This affects how the implementer scripts the reload step in Test Steps §10 — reusing `page.url()` (captured after the initial navigate/save) rather than constructing a bare `/pipelines/all/{id}` URL avoids the issue. Filed as a question/clarification rather than a defect because this may be intentional routing (the app may rely on client-side state carried via those query params rather than being a true deep-link bug) — recommend the team confirm intent.
- No defect filed for the case-text step 2 ("Click on the MCP node to open configuration panel") not matching the live always-expanded-inline UI — resolved directly as a CLARIFICATION in the Coverage Map (case text is stale relative to a UI simplification, not a product regression).

## Blocked Steps

None. All 10 case steps were executed to completion against the live local environment. (Test-data precondition — a second MCP with a real, non-empty tool list — required provisioning a new MCP toolkit mid-session since no pre-existing environment MCP satisfied it without an OAuth login this session couldn't complete; documented in Test Data, not a blocker to the case itself.)

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`) — **this case requires `add-data-testid` work before implementation**, since 5 of the 6 interactive elements central to this case (Toolkit select, Tool select, Input select, Output select, Input-mapping Value fields) have no `data-testid` today. See Concrete Handles for exact recommended names.
- No existing page object covers the MCP node's inline config fields — `automation/pages/pipeline_detail_page.py` has generic node methods (`add_node`, `wait_for_node_on_canvas`, `delete_node`, `edit_node_name`, `get_node_name`) but nothing for reading/writing an MCP node's Toolkit/Tool/Input/Output/Input-mapping fields. This is new page-object surface, e.g. `configure_mcp_node(node_id, toolkit, tool, input_mapping={...})` methods on `PipelineDetailPage`.
- Test-data fixture: needs a new "MCP toolkit with real, auth-free tools" fixture (see Test Data) — recommend `automation/fixtures/data_fixtures.py` gain an `mcp_toolkit_with_tools` fixture that provisions against a known-stable public/mock MCP endpoint, parallel to the existing `github_toolkit` pattern, rather than reusing the placeholder-URL MCPs already in the environment.
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}` response (`201`) before reloading/asserting persistence — not a fixed timeout.
- The pipeline's own `Save` button testid (`agent-save-button`) and the MCP-attach search-popper's `select-option-{name}` pattern are both already proven and reusable from the ELITEA-1922 precedent and this session.
