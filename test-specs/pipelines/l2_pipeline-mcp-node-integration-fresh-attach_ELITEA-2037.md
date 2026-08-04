# Test Case: Pipeline — MCP Node Integration (fresh attach → add node → configure → persist)

## Metadata
- **TMS ID**: ELITEA-2037
- **Linked Story**: EliteaAI/elitea-testing-public#474
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths; sidebar showed "Elitea is connected")
- **Analyst**: qa-engineer (agent), session 2026-08-04
- **Status**: ready-for-automation
- **surface_key**: pipeline-mcp-node

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- An existing MCP toolkit is available in the project, with a **real, non-empty tool list** — see Test Data (a placeholder-URL MCP returns zero tools and cannot demonstrate steps 8–9).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A **fresh, empty pipeline** (no nodes/edges pre-seeded — this case IS the "from scratch" flow: attach MCP to Tools, add the node, configure it). Recommend `PipelineAPI.create_pipeline(name, description)` (empty `pipeline_settings`) rather than `create_pipeline_with_mcp_node()` — the latter pre-configures an MCP node and defeats the point of this case (contrast with ELITEA-1954, whose precondition is an *already-configured* node).
- An MCP toolkit with a real, working tool list. **Reuse the existing `mcp_toolkit_with_tools` fixture** (`automation/fixtures/data_fixtures.py:916`) — provisions a throwaway Remote MCP against the public, auth-free `https://mcp.deepwiki.com/mcp` endpoint (3 tools: `read_wiki_structure`, `read_wiki_contents`, `ask_question`; `ask_question` needs 2 required params `repoName`/`question`, matching this session's live run and ELITEA-1954's precedent). Do NOT reuse the manually-created `autotest_deepwiki_mcp_1954` toolkit this session (and ELITEA-1954's session) left in the environment — it is leftover analysis residue, not a fixture; the implementer's test must provision (and tear down) its own toolkit via the fixture.
- This session's own exploration created a persistent pipeline (`autotest_pipeline_mcp_2037`, id `7467`, project 399) via the UI create flow, attached the pre-existing residue `autotest_deepwiki_mcp_1954` toolkit to it, and fully configured + saved an MCP node (Toolkit=`autotest_deepwiki_mcp_1954`, Tool=`ask_question`, Input=`input`, Output=`messages`, Input mapping `repoName`=`EliteaAI/elitea-testing-public`, `question`=`What is this repository about?`). **Not deleted by this session** — analyst has no cleanup authority (`.agents/workflow.md`); flagged to the lead. Implementer teardown for its OWN test data: `PipelineAPI.delete_pipeline(pipeline_id)` + `ToolkitAPI.delete_toolkit(toolkit_id)` (via the `mcp_toolkit_with_tools` fixture's own teardown).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Navigate to a fresh, empty pipeline's configuration page (`${BASE_URL}/pipelines/all/{pipeline_id}?destTab=configuration&name={pipeline_name}&viewMode=owner`, reached after the initial create-Save).
   - **Verify**: Configuration panel (General/Tools/... accordion) is visible; canvas loads with only the `END` node.
2. In the left/config panel's "Tools" accordion, click the "+ MCP" button (`agent-add-mcp-button`, inside `agent-toolkits-section`).
   - **Verify**: an MCP-picker popup (search input + listbox of project MCPs) opens.
3. From the popup, select an existing MCP toolkit with a real tool list (e.g. the `mcp_toolkit_with_tools` fixture's toolkit).
   - **Verify**: the popup's listbox item (`[data-testid="select-option-{mcp_name}"]`) is clicked; the popup stays open (multi-attach pattern) — dismiss with `Escape` or a click outside.
4. Verify the MCP appears attached in the Tools section.
   - **Verify**: an attached-item card (`agent-toolkit-card`) renders with the MCP's name and a "Show tools" affordance. **CLARIFICATION (case-text drift, filed EliteaAI/elitea-testing-public#1149, sibling of #530)**: the case text says "listed under the MCP sub-tab" — the live product has **no MCP sub-tab**. The Toolkit/MCP/Agent/Pipeline buttons are 4 independent ADD triggers, not view-filter tabs; every attached item (any type) renders in ONE flat list sharing the single testid `agent-toolkit-card` (confirmed via `document.querySelectorAll('[data-testid="agent-toolkit-card"]')` → exactly 1 after attaching 1 MCP). Assert the card's presence/name, not a "sub-tab active" state that doesn't exist.
   - **Also confirmed (network)**: unlike the AGENT-level Tools section (#530: MCP attach auto-saves via an immediate `PATCH`), the PIPELINE-level Tools attach does **not** auto-persist — no persistence request fires on attach (only `GET .../toolkits/…` / `GET .../tools/…` listing calls). The attachment is persisted together with the rest of the pipeline's changes by the pipeline-level Save (step 11) — so case step 11 correctly covers the Tools-section attachment too; only step 4's "sub-tab" wording is stale.
5. Click "Add node" on the canvas (`pipeline-add-node-button`), then select "MCP" from the menu (`pipeline-add-node-menu-item-mcp`).
   - **Verify**: an "MCP 1" node appears on the canvas (ReactFlow wrapper `[data-testid="rf__node-MCP 1"]`), auto-wired as the pipeline's entry point (it is the first/only node) with no auto-created edge to `END` (matches the digest's confirmed "adding a node never auto-wires an edge" finding).
6. Observe the MCP node's config fields, inline/expanded on the canvas card (no click-to-open action — same always-expanded pattern as every other node type).
   - **Verify — confirmed live, BEFORE any Toolkit is selected**: Trigger (entry-point-only, "Chat Message"), **Toolkit** select (empty), **Input** (multi-select state-var), **Output** (multi-select state-var), **Interrupt before** (switch, `disabled` — disabled because this node is the entry point; matches `CommonInterruptSettings.jsx`'s `entry_point === id` gating), **Interrupt after** (switch, `disabled` — disabled because the node's default `transition` is `END`), **Structured output** (switch, enabled) are ALL present immediately. **Tool select and both INPUT MAPPING (REQUIRED N)/(OPTIONAL N) accordions are conditionally rendered and are ABSENT from the DOM until a Toolkit with ≥1 tool is selected** — same conditional-rendering behavior already documented for the sibling Toolkit node type (`.agents/testing.md` cross-ref / `_surface.md` "Toolkit node" section, ELITEA-2010). This is a partial mismatch with the case text's step 6 wording ("MCP node panel shows: Toolkit dropdown, Tool dropdown, ... All listed sections are present") if read as "all present simultaneously on a freshly-added, unconfigured node" — not a defect (product behavior is correct and consistent with the sibling node type), but the assertion must be split: static sections assert immediately after step 5; Tool + Input-mapping sections assert after step 8 (Tool selected).
7. Click the Toolkit select; choose the attached MCP.
   - **Verify**: Toolkit combobox shows the selected MCP's name; the Tool select field appears (was absent, now rendered).
8. Click the Tool select; choose a tool with required parameters (e.g. `ask_question`).
   - **Verify**: Tool combobox shows the selected tool name; an "Input mapping (required 2)" accordion appears below Input/Output, containing one row per required parameter (`RepoName`/`Question` display labels, raw schema keys `repoName`/`question`), each with its own Type (`Fixed`/other) select and Value text field.
9. Fill the required Input-mapping Value fields (Type left at its default `Fixed`).
   - **Verify**: typed values are reflected in the Value fields.
10. Set the tool-agnostic Input and Output state-variable selects (e.g. Input=`input`, Output=`messages` — the only two options on a fresh pipeline).
    - **Verify**: both comboboxes show the selected values. **Note (analyst addition)**: the Input select is a `role="listbox" aria-multiselectable="true"` control (multi-select capable, same as the HITL node's Input field per the digest) even though this flow only selects one value — implementer should assert the selected-value text, not assume single-select semantics.
11. Click the pipeline's Save button (`agent-save-button`).
    - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` returns `201 Created`; zero console errors across the whole flow (steps 2–11, confirmed via `page.on("console")` capture in this session — 0 errors).
12. Reload the page at the same canonical URL (captured after the initial navigate — see ELITEA-1954's Known Defects for why a bare `/pipelines/all/{id}` URL 404s).
    - **Verify**: after reload, the MCP node shows the persisted state — Tools-section attachment card still present, node's Toolkit/Tool/Input/Output/Input-mapping (including the typed Value text) all match what was configured in steps 3–10, byte-for-byte.

## Expected Results
- An MCP toolkit can be attached to a pipeline's Tools section via the "+ MCP" button, rendering as a flat-list attached card (no "sub-tab", see Coverage Map).
- A fresh MCP node can be added via the canvas "Add node" → "MCP" menu; its config panel is always-expanded inline with no click-to-open step.
- The static config fields (Toolkit, Input, Output, Interrupt before/after, Structured output) are present immediately on an unconfigured node; Tool select and INPUT MAPPING accordions render conditionally once a Toolkit with tools is selected.
- Selecting a Toolkit populates the Tool dropdown with exactly that toolkit's own tools; selecting a Tool reveals a per-tool Input-mapping section with the tool's actual parameter names.
- Filling Input-mapping values, setting Input/Output, and saving persists everything; a full page reload with the canonical URL confirms all of it survives unchanged.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; an existing MCP available in the project | setup exists | steps 1–2 | step 1: panel visible; step 2: popup opens | asserted |
| 1 Open a pipeline (or create new one) | Pipeline is open and ready for editing | step 1 | step 1: config panel + canvas visible | asserted |
| 2 Click "+ MCP" button | MCP picker popup opens | step 2 | step 2: popup listbox visible | asserted |
| 3 Select an existing MCP from the popup | MCP is selected | step 3 | step 3: option clicked | asserted |
| 4 Verify MCP appears in Tools list under MCP sub-tab | "WebSearch" listed under MCP sub-tab | step 4 | step 4: `agent-toolkit-card` presence + name | asserted — **CLARIFICATION filed EliteaAI/elitea-testing-public#1149 (sibling of #530): no "MCP sub-tab" exists live; one flat attached-items list shared across all attachment types. Asserted the live flat-list contract instead of the stale "sub-tab" wording.** |
| 5 Add node → select "MCP" | MCP node added to canvas | step 5 | step 5: `rf__node-MCP 1` present | asserted |
| 6 Verify MCP node panel shows: Toolkit, Tool, Input, Output, INPUT MAPPING (REQUIRED N/OPTIONAL N), Interrupt before/after, Structured output | All listed sections present | steps 6, 8 | step 6: static sections present pre-Toolkit-select; step 8: Tool + Input-mapping sections present post-Tool-select | asserted — **CLARIFICATION (not filed as a separate ticket, documented here + in `_surface.md`): Tool select and both INPUT MAPPING accordions are conditionally rendered (absent from DOM, not just hidden/disabled) until a Toolkit with ≥1 tool is selected — same product behavior already established for the sibling Toolkit node type (ELITEA-2010). "All sections present" is true across steps 6+8 combined, not simultaneously on an unconfigured node. This is a live-confirmed UI contract, not a defect — mirrors the reverse-masking guard's spirit without being case-text-wrong enough to warrant its own ticket (the case's literal step ordering already puts step 6's verify ahead of step 7's Toolkit-select, so a careful reading is consistent; flagging for implementer clarity only).** |
| 7 Select attached MCP from "Toolkit" dropdown | MCP selected in Toolkit dropdown | step 7 | step 7: combobox value | asserted |
| 8 Select a tool — INPUT MAPPING sections populate with tool-specific parameters | INPUT MAPPING appears with tool parameters | step 8 | step 8: "Input mapping (required 2)" with repoName/question | asserted |
| 9 Configure required INPUT MAPPING fields (Type + Value) | INPUT MAPPING values set | step 9 | step 9: typed Value text | asserted |
| 10 Set Input/Output comboboxes | Input/Output configured | step 10 | step 10: combobox values | asserted |
| 11 Save pipeline | Pipeline saves without errors | step 11 | step 11: 201 + zero console errors | asserted |
| 12 Reload — verify Toolkit, Tool, and INPUT MAPPING values persist | All MCP node configuration persists after reload | step 12 | step 12: full field-by-field re-read | asserted |
| Expected Final State: MCP node fully configured, all persisting after save+reload; MCP appears in Tools section under MCP sub-tab | — | steps 4, 11–12 | steps 4, 11–12 | asserted (with the sub-tab clarification from step 4) |
| Pass/Fail: all steps complete without errors; MCP node config persists after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 6 additionally asserts the **absence** of Tool select and Input-mapping accordions on the freshly-added, unconfigured node (`to_have_count(0)` / not-in-DOM check) before step 7 — *added because a naive implementer might assert only presence-after-configuration and silently skip verifying the pre-Toolkit-select empty state, which is exactly the state a future regression (e.g. Tool select rendering with stale/wrong options before a Toolkit is chosen) would need to be caught by.*
- Step 10 notes the Input select's `aria-multiselectable="true"` nature — *added because assuming plain single-select semantics could produce a brittle locator/assertion if the implementer copies patterns from a genuinely single-select field elsewhere in the codebase.*
- No console-error assertion was in the original case text; added it to step 11 and throughout as a side-channel check — *standard practice per this project's `test-case-analysis` skill; zero console errors were observed across the whole flow (steps 2–12), no defect to report.*
- Network-behavior note on step 4 (no auto-save-on-attach for pipelines, unlike agents) — *added because the sibling AGENT-level case (ELITEA-1950/#530) documents different persistence timing; an implementer reading that precedent without re-verifying live for pipelines could wrongly assert an immediate PATCH that never fires here.*

## Cleanup

1. This session created a persistent pipeline (`autotest_pipeline_mcp_2037`, id `7467`) on project 399, using the pre-existing `autotest_deepwiki_mcp_1954` toolkit (left over from ELITEA-1954's session, id `1266`). **Neither newly created nor deleted by this analysis session** — analyst has no automation authoring/cleanup authority (`.agents/workflow.md`); flagged to the lead. Pipeline 7467 is net-new residue from THIS session and should be deleted by the lead or left as harmless `Private`-project-scoped residue.
2. Implementer teardown for its OWN test data: `PipelineAPI.delete_pipeline(pipeline_id)` for the fixture-created pipeline, and rely on the `mcp_toolkit_with_tools` fixture's own `ToolkitAPI.delete_toolkit()` teardown for the toolkit — do NOT reuse or delete the residue `autotest_deepwiki_mcp_1954` (id 1266), it is out of scope for this case's test data and may still be in use by ELITEA-1954's implemented test.

## Concrete Handles (discovered during exploration)

**PROVENANCE — verified this session via `cd ../EliteaUI && git fetch origin` + `git grep` against BOTH `origin/main` and `origin/automation/testids` (2026-08-04). All MCP-node-scoped testids below use a runtime-constructed template (`` `${testIdPrefix}-toolkit-select` `` in `BaseToolNode.jsx`'s `TEST_ID_PREFIX_BY_NODE_TYPE` map) — a literal bare-substring grep for the full testid string finds nothing; verified instead via the constituent prefix (`pipeline-mcp-node`) and the mechanism (`TEST_ID_PREFIX_BY_NODE_TYPE`), both confirmed present ONLY on `automation/testids`, absent from `main`.**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| MCP node on canvas | `[data-testid="rf__node-{node_display_name}"]` (dynamic, e.g. `rf__node-MCP 1`) | on-automation/testids only (ReactFlow's own convention — sanctioned #579 third-party-widget exception, not app-added) | none — testid-only |
| Add-node button (canvas) | `[data-testid="pipeline-add-node-button"]` — confirmed working live | on-automation/testids only (`main:no`) | none needed |
| Add-node menu "MCP" item | `[data-testid="pipeline-add-node-menu-item-mcp"]` — confirmed working live; the Add-node "+" menu's items now ALL carry testids (`pipeline-add-node-menu-item-{type}`, lowercase type) — supersedes the `_surface.md` "zero testids on any menu item" note from the 2026-08-03 session (ELITEA-2018/2030), which is now stale — testids were added since | on-automation/testids only, `AddNodeMenu.jsx` (`main:no`) | none needed |
| MCP node Toolkit select | `mcp_node_toolkit_select` / `[data-testid="pipeline-mcp-node-toolkit-select"]` — already a `LocatorDescriptor` field on `PipelineDetailPage` (`pipeline_detail_page.py:128`), confirmed working live | on-automation/testids only (`main:no`) — `TEST_ID_PREFIX_BY_NODE_TYPE` map in `BaseToolNode.jsx` | none needed |
| MCP node Toolkit select — inner combobox (for `aria-expanded` reads) | `mcp_node_toolkit_select_combobox` / `[data-testid="pipeline-mcp-node-toolkit-select-combobox"]` — existing field, confirmed working live | on-automation/testids only — `SingleSelect.jsx`'s generic `${dataTestId}-combobox` auto-derivation | none needed |
| MCP node Tool select (+ its `-combobox` variant) | `mcp_node_tool_select` / `[data-testid="pipeline-mcp-node-tool-select"]` — existing field; combobox variant `pipeline-mcp-node-tool-select-combobox` also confirmed working live (needed to open the dropdown reliably — same `-combobox` auto-derivation) | on-automation/testids only | none needed |
| MCP node Input select (+ `-combobox`) | `mcp_node_input_select` / `[data-testid="pipeline-mcp-node-input-select"]`, combobox `pipeline-mcp-node-input-select-combobox` — existing field, confirmed working live; the underlying control is `role="listbox" aria-multiselectable="true"` | on-automation/testids only | none needed |
| MCP node Output select (+ `-combobox`) | `mcp_node_output_select` / `[data-testid="pipeline-mcp-node-output-select"]`, combobox `pipeline-mcp-node-output-select-combobox` — existing field, confirmed working live | on-automation/testids only | none needed |
| Select dropdown option (Toolkit/Tool/Input/Output share this pattern) | `[data-testid="select-option-{value}"]` — confirmed working, e.g. `select-option-autotest_deepwiki_mcp_1954`, `select-option-ask_question`, `select-option-input`, `select-option-messages` | on-automation/testids only (same generic `SingleSelect` mechanism) | none needed |
| Input-mapping "Value" text field (per param) | `MCP_NODE_INPUT_MAPPING_VALUE` class constant / `[data-testid="pipeline-mcp-node-input-mapping-value-{param}"]` — already exists on `PipelineDetailPage` (`pipeline_detail_page.py:664`), confirmed working live for `repoName`/`question` | on-automation/testids only | none needed |
| Input-mapping "required N" accordion heading | `mcp_node_input_mapping_required_heading` / `[data-testid="pipeline-mcp-node-input-mapping-heading"]` — existing field | on-automation/testids only | none needed |
| **Input-mapping "optional N" accordion heading** | **NO testid — `add-data-testid` gap.** `InputMapping.jsx`'s `optionalHeadingTestId` prop is only wired for the Toolkit node type in `BaseToolNode.jsx` (`nodeType === Toolkit ? ... : undefined`); MCP nodeType always passes `undefined`. Recommend widening the existing conditional (or adding a parallel `pipeline-mcp-node-input-mapping-optional-heading`) — the plumbing already exists, it's a 1-line change mirroring the Toolkit call site. NOT live-exercised this session (`ask_question` has 0 optional params) — confirmed via source read only (`BaseToolNode.jsx:217-220`). | needs-adding | none — brittle without it; no tool in this session's data had optional params to probe a fallback |
| **Input-mapping row "Type" select** | **NO testid — `add-data-testid` gap.** Same pattern: `InputMapping.jsx`'s `typeTestIdPrefix` prop is Toolkit-only in `BaseToolNode.jsx` (line 208); MCP passes `undefined`. Recommend `pipeline-mcp-node-input-mapping-type-{param}` (dynamic, mirrors the existing Value-field naming). Confirmed via live DOM: currently only reachable via `id="simple-select-Type"` (duplicated per row — NOT unique, positional `.nth()` only). | needs-adding | Positional `nth()` only — brittle, do not ship without the testid. This case's steps only require the Type select's DEFAULT value (`Fixed`), never changing it — if the implementer's test only reads/asserts the default and never interacts with Type, the positional risk is lower but still non-compliant with policy; recommend filing the testid work regardless since the row is on the test's executed code path. |
| **MCP node "Interrupt after" toggle** | **NO testid — `add-data-testid` gap.** `CommonInterruptSettings.jsx`'s `interruptAfterTestId` prop is Toolkit-only in `BaseToolNode.jsx` (line 232); MCP passes `undefined` (confirmed via source AND live DOM — the switch renders with no `data-testid` attribute at all, unlike the sibling "Interrupt before" toggle which has an unconditional dynamic testid). Recommend `pipeline-mcp-node-interrupt-after-toggle`, mirroring the existing `pipeline-toolkit-node-interrupt-after-toggle`. | needs-adding | Confirmed only reachable by DOM structure/visible-label text (`switch[aria-label="Interrupt after"]` role query) — fragile, positional among 2 near-identical unlabeled MUI switches. |
| **MCP node "Structured output" toggle** | **NO testid — `add-data-testid` gap.** Same gap as Interrupt after — `structuredOutputTestId` is Toolkit-only. Recommend `pipeline-mcp-node-structured-output-toggle`. | needs-adding | Reachable via `switch[aria-label="Structured output"]` role query — fragile, same caveat. |
| MCP node "Interrupt before" toggle | `NODE_INTERRUPT_BEFORE_TOGGLE` class constant / `[data-testid="pipeline-node-interrupt-before-toggle-{node_id}"]` (dynamic, keyed by node id, NOT node type — unconditional for every node type) — already exists on `PipelineDetailPage` | on-automation/testids only (`main:no` — confirmed by the ELITEA-2034 session's correction; not yet promoted) | none needed |
| Add-MCP button (Tools section) | `agent_add_mcp_button` / `[data-testid="agent-add-mcp-button"]` — already exists, confirmed working live | **on-main** (pre-existing, shared with agent forms) | none needed |
| Tools-section container | `[data-testid="agent-toolkits-section"]` | **on-main** | none needed |
| Attached toolkit/MCP card (shared, both types) | `[data-testid="agent-toolkit-card"]` — confirmed exactly 1 rendered after attaching 1 MCP, via `document.querySelectorAll` | **on-main** | none needed |
| MCP-in-search-popper option | `[data-testid="select-option-{mcp_name}"]` — same pattern as node dropdowns, confirmed working | on-automation/testids only (generic `SingleSelect` mechanism) | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed, shared with agent/pipeline create-and-edit forms | **on-main** | none needed |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on the pipeline Save click (step 11); `201 Created` on success; this single request persists BOTH the Tools-section MCP attachment AND the node's Toolkit/Tool/Input/Output/Input-mapping state — wait for this response before asserting reload persistence, not a fixed timeout.
- No request fires immediately on the MCP-attach popup selection (step 3/4) — only `GET .../toolkits/prompt_lib/{project}` / `GET .../tools/prompt_lib/{project}?...&mcp=true` (listing calls that populate the popup). Contrast with the AGENT-level Tools section (#530), which auto-persists via an immediate `PATCH`.
- `GET ${ELITEA_API_BASE}/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires once the attached MCP toolkit is selected in the node's Toolkit dropdown; returns the toolkit's tool list that populates the Tool dropdown.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on page load/reload (step 12); confirms persisted node config is what the Flow-view canvas renders from.

## Known Defects Found During Exploration

**None found in the MCP-node fresh-attach/add/configure/persist flow itself.** All 12 case steps produced the expected result once the two documented CLARIFICATIONs (Tools "sub-tab" wording, conditional Tool/Input-mapping rendering) are accounted for: attach, add-node, Toolkit/Tool selection, Input-mapping fill, Input/Output selection, save, and full-reload persistence all worked correctly with zero console errors across the entire flow.

One clarification filed:
- **[INFO] Pipeline Tools section has no "MCP sub-tab"** — filed as `EliteaAI/elitea-testing-public#1149` (label `question`, sibling of `#530` which covers the same pattern on the AGENT-level Tools section). See step 4 and Coverage Map above for full detail.

## Blocked Steps

None. All 12 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`). **Most of the MCP node's config-field testids ALREADY EXIST** (added during ELITEA-1954/1955's `add-data-testid` passes) and are already wired as `PipelineDetailPage` fields/methods (`mcp_node_toolkit_select`, `select_mcp_node_toolkit()`, `select_mcp_node_tool()`, `fill_mcp_node_input_mapping_value()`, `is_input_mapping_section_visible()`, etc. — see `automation/pages/pipeline_detail_page.py:1964+`). Reuse these directly; do not re-derive.
- **New `add-data-testid` work needed for 4 elements** this case's steps touch (all confirmed via source read of `BaseToolNode.jsx`/`InputMapping.jsx`/`CommonInterruptSettings.jsx` — the prop plumbing already exists generically, it's Toolkit-nodeType-only today):
  1. MCP node's "Interrupt after" toggle → wire `interruptAfterTestId` for `nodeType === Mcp` too, e.g. `pipeline-mcp-node-interrupt-after-toggle`.
  2. MCP node's "Structured output" toggle → wire `structuredOutputTestId` similarly, e.g. `pipeline-mcp-node-structured-output-toggle`.
  3. MCP node's Input-mapping row "Type" select → wire `typeTestIdPrefix` similarly, e.g. `pipeline-mcp-node-input-mapping-type-{param}`.
  4. MCP node's Input-mapping "optional N" accordion heading → wire `optionalHeadingTestId` similarly, e.g. `pipeline-mcp-node-input-mapping-optional-heading` (not live-exercisable with this session's tool data — no optional params on `ask_question` — but the case's own "INPUT MAPPING (OPTIONAL N)" line item requires it to exist for full coverage of a tool that HAS optional params; consider picking a tool/mock with an optional param for full exercise, or leave as a documented, testid-ready-but-unexercised gap and note it in the Run Report).
- No page-object method exists yet for the fresh-attach flow (attach via `agent-add-mcp-button` popup + Add-node → MCP) as a single reusable helper — `PipelineDetailPage.add_node(node_type)` and the Tools-section `add_mcp_button`/toolkit-search/`toolkit-menu-item` popper methods already exist independently (reused from Agent/Toolkit-node precedent); this case just composes them in sequence, no new page-object surface beyond the 4 testid-gap wirings above.
- Test-data fixture: reuse `mcp_toolkit_with_tools` (real MCP, auto torn down) + `PipelineAPI.create_pipeline()` (empty pipeline) — do NOT use `create_pipeline_with_mcp_node()` (that's for the ALREADY-CONFIGURED precondition case, ELITEA-1954).
- Wait strategy: wait for `PUT .../application/prompt_lib/{project}/{pipeline_id}` (`201`) before reloading/asserting persistence — not a fixed timeout. Also wait for `[data-testid="toolkit-menu-item"]`/`select-option-{name}` to appear in the MCP-attach popper (can take several seconds per the digest's documented popper-loading timing) rather than a fixed sleep.
- Console-error capture: register `page.on("console", ...)` BEFORE step 2 (not just before Save) — this session's assertion covers the whole flow, matching ELITEA-1954's precedent.
