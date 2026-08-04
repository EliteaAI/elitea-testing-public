# Test Case: Configure LLM Node — System, Task, Chat History

## Metadata
- **TMS ID**: ELITEA-2004
- **Priority**: l2 (high — as authored in the source TMS case; see `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md` — implementer should use `@pytest.mark.p1`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend `dev.elitea.ai`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2010 — same live session, shared login/navigation/discovery; steps executed and observed independently)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A project exists with access to the Pipelines feature (satisfied by the default localhost dev project, id `399`).
- No pre-existing LLM node or attached toolkit is required — the case starts from a bare empty pipeline.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A fresh empty pipeline (`autotest_<test_name>`), created via `PipelineAPI.create_pipeline()` — same pattern as the existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py:119`). No API-seeded node is needed; the LLM node is added live via the UI per the case's own step 1.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).
- Exact case Test Data table values, all confirmed to work as typed with no substitution needed:
  - SYSTEM Type=`Fixed`, Value=`You are a helpful assistant`
  - TASK Type=`F-String`, Value=`User Input: {input}`
  - CHAT HISTORY Type=`Fixed`, Value=`[]`
  - Input=`input`, Output=`messages` (case says "desired output variables" without naming one — `messages` is the only sensible existing pipeline-state variable besides `input` itself; see Coverage Map)

## Test Steps

1. Create a pipeline via `PipelineAPI.create_pipeline()` (empty, no instructions), then navigate to `${BASE_URL}/pipelines/all/{pipeline_id}?destTab=configuration&viewMode=owner`.
   - **Verify**: Configuration panel loads (`GENERAL`/`TOOLS`/... accordion visible); canvas loads past "Preparing the flow editor..." placeholder (`[data-testid="rf__wrapper"]` visible).
2. Click the canvas "+" button (`button.MuiIconButton-colorPrimary`, first match — same locator `PipelineDetailPage.add_node()` already uses) then click the `LLM` menu item (`role=menuitem`, name `LLM`, exact).
   - **Verify**: an LLM node appears on canvas (`.react-flow__node-llm`, `data-id="LLM 1"`).
3. Read the LLM node's config fields directly from the node body — **no separate click-to-open action is needed**, same always-expanded-inline pattern already confirmed for the MCP node (ELITEA-1954) and the HITL node (ELITEA-2014/2015).
   - **Verify**: all of Trigger, SYSTEM, TASK, CHAT HISTORY, Input, Output, Toolkits, Interrupt before/after, Structured output are present inline on the node body (confirmed via a full-text dump of the node's labels — exact match to the case's step-3 list). This differs from the case text's step 2 wording ("Click on the LLM node to open its configuration panel opens on the right") — see Coverage Map CLARIFICATION.
4. In the SYSTEM section: Type defaults to `Fixed` already (no change needed); fill the Value textarea (`#system-value`, scoped inside the node) with `You are a helpful assistant`.
   - **Verify**: the textarea's `input_value()` reflects the typed text.
5. In the TASK section: open its Type select (positional — see § Concrete Handles for why), select `F-String`; fill the Value textarea (`#task-value`) with `User Input: {input}`.
   - **Verify**: Type select shows `F-String`; Value textarea reflects the typed text.
6. In the CHAT HISTORY section: Type defaults to `Fixed` already (no change needed); fill the Value textarea (`#chat_history-value`) with `[]`.
   - **Verify**: the textarea's `input_value()` is `[]`.
7. Open the node's `Input` combobox (`#simple-select-Input`) and select `input`.
   - **Verify**: combobox shows `input`. (Dropdown options observed: exactly `input`, `messages` — the pipeline's only two state variables at this point.)
8. Open the node's `Output` combobox (`#simple-select-Output`) and select `messages`.
   - **Verify**: combobox shows `messages`.
9. Click the pipeline's Save button (`[data-testid="agent-save-button"]` — confirmed present via visible-text `Save`).
   - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` returns `201 Created`; zero console errors at any point in the flow (checked from before step 1 through after step 9).
10. Reload the page at the same canonical URL (with all query params — see the ELITEA-1954 AFS's Known Defects entry re: bare `/pipelines/all/{id}` 404ing; reuse `page.url()` captured after the initial navigation, not a hand-built bare URL).
    - **Verify**: after reload, the LLM node shows SYSTEM Type=`Fixed`/Value=`You are a helpful assistant`, TASK Type=`F-String`/Value=`User Input: {input}`, CHAT HISTORY Type=`Fixed`/Value=`[]`, Input=`input`, Output=`messages` — all fields persisted exactly as configured.

## Expected Results
- The LLM node's config renders fully inline on the canvas card the instant it's added — no modal, no side panel, no click-to-open action.
- SYSTEM, TASK, and CHAT HISTORY each accept an independent Type (Fixed/F-String/Variable) and Value.
- Input/Output comboboxes list the pipeline's current state variables (`input`, `messages` on a fresh pipeline) and accept a selection.
- Saving persists everything; a full page reload with the pipeline's canonical URL confirms Type + Value for all three sections, and Input/Output, survive unchanged.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, project with Pipelines access | setup exists | step 1 | step 1: panel visible | asserted |
| 1 Create a pipeline and add an LLM node via "Add node" → "LLM" | LLM node appears on canvas | steps 1–2 | step 2: `.react-flow__node-llm` visible | asserted |
| 2 Click on the LLM node to open its configuration panel | Configuration panel opens on the right | step 3 | step 3 | asserted — **CLARIFICATION: live product has no click-to-open action; the node's ENTIRE config (SYSTEM/TASK/CHAT HISTORY/Input/Output/Toolkits/Interrupt/Structured output) is always rendered inline/expanded on the canvas card itself, confirmed via a live full-text dump of the node body immediately after adding it (no click performed). This is the same reverse-masking pattern already documented for the MCP node (ELITEA-1954 AFS) and the HITL node (ELITEA-2014/2015 digest) — case text describing a "click to open" step or "panel on the right" is stale relative to the live UI. Not a defect: the observable ("panel/fields are visible") is still true and asserted.** |
| 3 Verify panel shows sections: Trigger, SYSTEM, TASK, CHAT HISTORY, Input, Output, Toolkits, Interrupt before/after, Structured output | All listed sections present | step 3 | step 3: exact label-text dump matched the case's list 1:1 | asserted |
| 4 In SYSTEM: set Type to "Fixed", enter Value | SYSTEM accepts the value | step 4 | step 4: `input_value()` | asserted — Type was already `Fixed` by default; confirmed the default rather than performing a no-op click (see Axis 2) |
| 5 In TASK: set Type to "F-String", enter Value | TASK accepts the f-string value | step 5 | step 5: Type select text + `input_value()` | asserted |
| 6 In CHAT HISTORY: set Type to "Fixed", enter Value | CHAT HISTORY accepts the value | step 6 | step 6: `input_value()` | asserted — Type was already `Fixed` by default, same as SYSTEM |
| 7 Set Input combobox to include "input" | "input" variable added to Input | step 7 | step 7: combobox text | asserted |
| 8 Set Output combobox to include desired output variables | Output variables set | step 8 | step 8: combobox text (`messages`, the only other available option) | asserted — case doesn't name a specific output variable; `messages` chosen as the one non-`input` option available (see Test Data) |
| 9 Save pipeline | Pipeline saves without errors | step 9 | step 9: `201` + zero console errors | asserted |
| 10 Reload page — verify SYSTEM, TASK, CHAT HISTORY types and values persisted | All values and types restored | step 10 | step 10: all 3 sections' Type+Value re-read | asserted |
| Expected Final State: SYSTEM/TASK/CHAT HISTORY/Input/Output all persist after reload | — | step 10 | step 10 | asserted |
| Pass/Fail: all steps complete without errors; all fields persist after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Steps 4 and 6 explicitly confirm SYSTEM's and CHAT HISTORY's Type is already `Fixed` by default rather than silently assuming it and skipping straight to the Value fill — *added because the case's own step wording ("set Type to Fixed") implies an action; asserting the pre-click default state first makes it visible in the AFS/test that no click was actually necessary here (unlike TASK, which does require an explicit Type change to F-String), so a future reader isn't left wondering why steps 4/6 look thinner than step 5.*
- No console-error assertion was in the original case text; added it to step 9 (checked across the whole flow) — *standard practice per this project's `test-case-analysis` skill; zero console errors were observed, no defect to report.*
- Step 10 additionally re-reads Input/Output combobox text (not just SYSTEM/TASK/CHAT HISTORY, which is all the case's own Expected Final State names) — *added because a regression where Input/Output silently reset to empty on reload while the three text sections persisted correctly would otherwise go undetected; this is the same class of gap the ELITEA-1954 AFS flagged for MCP node Input-mapping values.*

## Cleanup

1. This session created several throwaway pipelines during exploration (ids `6912`–`6914`, names `autotest_explore_llm_node` / `autotest_explore_llm2`) on the local DEV backend (project `399`) and **deleted all of them itself** via `PipelineAPI.delete_pipeline()` before ending the session — confirmed via a final terminal check (all three IDs return no data). No residue left behind.
2. Implementer teardown: the `pipeline_id`-style fixture pattern already handles this — `PipelineAPI.create_pipeline()` in setup, `PipelineAPI.delete_pipeline(pid)` in teardown (`automation/fixtures/data_fixtures.py:119`, no new fixture needed — this case's precondition is simpler than ELITEA-1954's since no toolkit/MCP is involved).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| LLM node on canvas | `.react-flow__node-llm` / `[data-testid="rf__node-LLM 1"]` (dynamic per node display name — ReactFlow's own testid convention) | none — third-party ReactFlow widget, testid-only |
| SYSTEM Value textarea | `#system-value` scoped to the node's `rf__node-*` container — **confirmed STABLE, unique `id`, unlike the Type selects below** | **NO `data-testid` — flag to `add-data-testid`.** Recommended: `pipeline-llm-node-system-value`. |
| TASK Value textarea | `#task-value` scoped to the node container — stable, unique | **NO `data-testid`.** Recommended: `pipeline-llm-node-task-value`. |
| CHAT HISTORY Value textarea | `#chat_history-value` scoped to the node container — stable, unique | **NO `data-testid`.** Recommended: `pipeline-llm-node-chat-history-value`. |
| SYSTEM / TASK / CHAT HISTORY Type selects | **DOM `id="simple-select-Type"` is DUPLICATED 3× inside one node (one per section) — confirmed live via `node.locator('#simple-select-Type').count() == 3`.** Positional targeting only: `.nth(0)`=SYSTEM, `.nth(1)`=TASK, `.nth(2)`=CHAT HISTORY, confirmed by DOM-order + nearby-label-text cross-check this session. Same duplicate-id anti-pattern already documented for the HITL node's 3 Router-mapping Route selects (ELITEA-2014/2015 digest) and now confirmed on a second node type. | **NO `data-testid` on any of the 3 — flag to `add-data-testid`.** Recommended dynamic names: `pipeline-llm-node-system-type-select`, `pipeline-llm-node-task-type-select`, `pipeline-llm-node-chat-history-type-select` (three distinct static names, not one dynamic template — there are always exactly 3 and they're semantically fixed, unlike e.g. per-tool-parameter Input-mapping rows). |
| Type select dropdown options (Fixed/F-String/Variable) | `[role="listbox"] li:has-text("F-String")` (or `page.get_by_role("option", name="F-String")`) — confirmed options are exactly `F-String`, `Variable`, `Fixed` for all 3 sections | Consider `[data-testid="select-option-{value}"]` once the Type selects themselves get testids — same pattern already confirmed working for the MCP/Toolkit node's Toolkit/Tool selects (`select-option-{value}`). |
| Input combobox (tool-agnostic state var) | `#simple-select-Input` scoped to the node container — stable, unique (only ONE Input select per node, unlike the 3 Type selects) | **NO `data-testid`.** Recommended: `pipeline-llm-node-input-select`. |
| Output combobox | `#simple-select-Output` scoped to the node container — stable, unique | **NO `data-testid`.** Recommended: `pipeline-llm-node-output-select`. |
| Input/Output dropdown options | `li:has-text("input")` / `li:has-text("messages")` inside the open `[role="listbox"]` | Consider `[data-testid="select-option-{value}"]` once testid'd, matching the MCP node's already-confirmed pattern. |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed, shared with agent/pipeline create-and-edit forms (reused from ELITEA-1954) | none needed |
| Canvas "+ Add node" button | `button.MuiIconButton-colorPrimary` (first match) — same locator `PipelineDetailPage.add_node()` already uses in production code, confirmed still correct | none needed — already exercised by `test_pipeline_nodes.py` |

**Implementation status (fix-round amendment — closes the "AFS never amended with the implemented handles" review finding):** every testid `Recommended` above (SYSTEM/TASK/CHAT HISTORY Type selects + Value fields, Input/Output selects) was implemented exactly as named — confirmed via `automation/pages/pipeline_detail_page.py`'s `llm_node_*` `LocatorDescriptor` fields. The 5 rows below cover the remaining case-list elements (Trigger, Toolkits, Interrupt before/after, Structured output) whose testids were added in the fix-round-1 commit, not the original implementation, and were never previously recorded here:

| Element | Recommended Locator | Fallback |
|---|---|---|
| Entry-point Trigger select (shown for whichever node is the pipeline's current entry point) | `[data-testid="pipeline-entry-point-trigger-select"]` — pre-existing testid from the ELITEA-2005/06/07/08 prep work (`EliteaAI/EliteaUI@b43fbce0`); first *consumed* by this case's test in the fix-round-1 commit (`e4511214`) | none needed |
| LLM node Toolkits multi-select | `[data-testid="pipeline-llm-node-toolkits-select"]` — added fix-round-1 (`EliteaAI/EliteaUI@37b0598b`), `ToolkitsSelect.jsx`, LLM-only call site | none needed |
| Node Interrupt-before toggle (dynamic, node-id-keyed, shared across node types) | `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` — pre-existing from the ELITEA-2008 prep work (`EliteaAI/EliteaUI@a2ce4732`); first *consumed* by this case's test in fix-round-1 (`e4511214`) | none needed |
| LLM node Interrupt-after toggle | `[data-testid="pipeline-llm-node-interrupt-after-toggle"]` — added fix-round-1 (`EliteaAI/EliteaUI@37b0598b`), `CommonInterruptSettings.jsx` caller-supplied `interruptAfterTestId` prop | none needed |
| LLM node Structured-output toggle | `[data-testid="pipeline-llm-node-structured-output-toggle"]` — added fix-round-1 (`EliteaAI/EliteaUI@37b0598b`), `CommonInterruptSettings.jsx` caller-supplied `structuredOutputTestId` prop | none needed |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on Save click; `201 Created` on success; this is the single request that persists the LLM node's SYSTEM/TASK/CHAT HISTORY/Input/Output state — wait for this response before reloading/asserting persistence, not a fixed timeout. Confirmed via live network capture this session.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on page load/reload; the reloaded canvas renders from this response.

## Known Defects Found During Exploration

**None.** All 10 case steps produced the expected result end-to-end: LLM node adds cleanly, SYSTEM/TASK/CHAT HISTORY each independently accept Type+Value, TASK's Type correctly switches to F-String, Input/Output comboboxes list and accept the pipeline's state variables, Save returns `201`, and every configured value (Type + Value for all 3 sections, Input, Output) persists byte-for-byte through a full page reload. Zero console errors throughout. Zero failed (≥400) network requests throughout.

One case-text CLARIFICATION (not a defect, not newly filed — an instance of the already-tracked pattern):
- Case step 2 ("Click on the LLM node to open its configuration panel opens on the right") does not match the live product — the config is always inline/expanded, no click-to-open exists. This is the identical pattern already surfaced for the MCP node (ELITEA-1954) and the HITL node (ELITEA-2014/2015); no new ticket filed since the pattern (and its resolution as a non-defect UX simplification, not a regression) is already on record across three now-confirmed node types (MCP, HITL, LLM). Resolved directly in the Coverage Map per the reverse-masking guard.

## Blocked Steps

None. All 10 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`) — **this case requires `add-data-testid` work before implementation**: none of the LLM node's interactive fields (3× Type select, 3× Value field, Input select, Output select) carry a `data-testid` today. See § Concrete Handles for exact recommended names — 8 new testids total, all gated to `nodeType === "llm"` the same way the MCP node's testids are gated to `nodeType === "mcp"` (`BaseToolNode.jsx` / the LLM node's own component — grep `../EliteaUI/src` for the LLM node's render function to find the exact call site).
- The 3 Value textareas (`#system-value`/`#task-value`/`#chat_history-value`) already have STABLE, semantically-named DOM ids — unlike the Type selects (duplicated `#simple-select-Type` ×3, positional-only) or the Toolkit node's Input-mapping Value fields (fully unstable React-generated ids, see the sibling ELITEA-2010 AFS). Recommend the implementer's interim (pre-testid) locators use `#system-value`/`#task-value`/`#chat_history-value` directly rather than a positional `nth()` scheme, since they're already unique and stable — only the 3 Type selects need positional targeting until testid'd.
- No existing page object covers the LLM node's inline config fields — `automation/pages/pipeline_detail_page.py` has generic node methods (`add_node`, `wait_for_node_on_canvas`, `delete_node`) and the MCP-node-specific methods from ELITEA-1954, but nothing for the LLM node's SYSTEM/TASK/CHAT HISTORY/Input/Output fields. Recommend new methods on `PipelineDetailPage`, e.g. `set_llm_node_section(section: str, type_: str, value: str)` (section ∈ {"system","task","chat_history"}) plus `get_llm_node_section_value(section)` / `get_llm_node_section_type(section)`, following the existing `get_mcp_node_*`/`fill_mcp_node_*` naming pattern.
- Test-data fixture: none needed beyond the existing `pipeline_id` fixture — this case builds its LLM node entirely through the UI starting from an empty pipeline (unlike ELITEA-2010's sibling case, which needs a pre-existing toolkit attached).
- Wait strategy: wait for the `PUT .../application/prompt_lib/{project}/{pipeline_id}` response (`201`) before reloading/asserting persistence — not a fixed timeout.
- Suggested pytest markers: `@pytest.mark.p1` (case priority `high` → project convention, see Metadata), `@pytest.mark.pipelines`, `@pytest.mark.regression`.
