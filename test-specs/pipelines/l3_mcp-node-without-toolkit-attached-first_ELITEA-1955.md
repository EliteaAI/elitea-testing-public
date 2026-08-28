# Test Case: MCP Integration in Pipeline — MCP Node Without Tool Attached First

## Metadata
- **TMS ID**: ELITEA-1955
- **Linked Story**: EliteaAI/elitea-testing-public#162
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend `dev.elitea.ai`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths; sidebar showed "Elitea is connected")
- **Analyst**: qa-engineer (agent), session 2026-07-18
- **Status**: ready-for-automation
- **Repair (2026-08-28)**: red on DEV at Step 7 (issue #1890) — triaged **class D (timing/race)**, not a product bug. See § Adjustment at the end of this file.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- **CLARIFICATION on the case's stated precondition "a Remote MCP (e.g., Web Search) is available in the project"**: verified live this session — no MCP literally named "Web Search" exists in project `399` (`Private`). The project's MCP inventory (via the TOOLS section's "+ MCP" search popper) is: `autotest_deepwiki_mcp_1954`, `autotest_remote_mcp_full`, `f`, `RemoteGithub`, `verify_secret_1784105552`, `verify_ttl_1784105621` — "Web Search" is illustrative case-text ("e.g."), not a literal environment requirement, consistent with the same finding already recorded in `l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md` § Test Data (that session found the placeholder-URL MCPs return zero tools and provisioned a real one instead). This session reused that same persistent, real-tooled MCP (`autotest_deepwiki_mcp_1954`, toolkit id `1266`, 3 tools: `ask_question`, `read_wiki_contents`, `read_wiki_structure`) rather than re-provisioning — it was still present and working. **Automation must not depend on a literal "Web Search" MCP existing** — use the `mcp_toolkit_with_tools` fixture (self-provisioning, self-cleaning; see Automation Hints) instead of hardcoding a shared/reused toolkit id.
- **Case-gate note**: this case's TMS frontmatter carries `status: draft`, matching the project's convention for "not yet automated" (same as every sibling case in `tests/automated-full-regression-ui/mcp/`, per the precedent already recorded in ELITEA-1954's AFS) — not an author signal to skip. Proceeded to Phase 1 rather than returning `out-of-scope-by-author`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline with **no MCP node and no MCP attached in TOOLS** (`autotest_mcp_empty_toolkit_<unique>`), created fresh so the "before attach" empty-dropdown state is genuinely unconfigured, not just visually reset.
- A Remote MCP toolkit with a real, non-empty tool list, via the existing `mcp_toolkit_with_tools` fixture (`automation/fixtures/data_fixtures.py:730`) — provisions against the public, auth-free `https://mcp.deepwiki.com/mcp` endpoint and self-deletes in teardown. Do **not** reuse the hardcoded `autotest_deepwiki_mcp_1954` (id `1266`) this analysis session reused manually — that toolkit is ELITEA-1954's leftover test-data residue, not a fixture, and has no owner guaranteeing its continued existence.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Create a new pipeline (via `pipeline_api.create_pipeline(name, description)` — API-seeded shell, consistent with ELITEA-1954's precedent of bypassing the already-covered generic "create pipeline" UI flow to focus the test on MCP-node behavior). Navigate to it in the UI.
   - **Verify**: Configuration panel (General/Tools accordion) is visible; canvas loads past "Preparing the flow editor..." placeholder; an "End" node is present with no other nodes.
2. Confirm the TOOLS section carries no attached MCP/Toolkit before proceeding.
   - **Verify**: TOOLS section (`agent-toolkits-section`) shows only the 4 add-buttons (Toolkit/MCP/Agent/Pipeline) and the MODULES sub-section — no toolkit/MCP card is rendered.
3. Click "Add node" (green `+` button above the canvas) and select "MCP" from the type menu.
   - **Verify**: A node named "MCP 1" appears on the canvas. Its config fields (Trigger, Toolkit, Input, Output) render **inline on the node body immediately** — no separate click-to-open action is needed (same live-product simplification already documented in ELITEA-1954's AFS Coverage Map row 2; the case text's step 4 "Click on the MCP node to open configuration" does not correspond to any actual click in the live UI).
4. Click the MCP node's "Toolkit" combobox (`pipeline-mcp-node-toolkit-select`).
   - **Verify**: The combobox's `aria-expanded` flips to `true` and a MUI listbox opens.
5. Inspect the open listbox's contents.
   - **Verify**: The listbox contains **zero** elements matching the real-option testid family (`[data-testid^="select-option-"]`) — the only rendered row is MUI's own placeholder `<MenuItem value=""><em>None</em></MenuItem>`, which carries **no `data-testid`** (see Concrete Handles — this is a first-party component, `SingleSelect.jsx`, but the empty-placeholder row is not currently instrumented). Confirmed visually: `test-results/screenshots/ELITEA-1955-step6-empty-toolkit-dropdown.png`.
6. Close the dropdown without selecting anything (Escape).
7. Click "+ MCP" in the TOOLS section (`agent-add-mcp-button`).
   - **Verify**: A search popper opens (`toolkit-search-input` search field, `toolkit-menu-item` result rows) listing the project's available MCPs.
8. Select the test-data MCP (the `mcp_toolkit_with_tools` fixture's toolkit, e.g. `autotest_deepwiki_mcp_1954` this session) from the popper.
   - **Verify**: `PATCH ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` returns `201 Created`. The TOOLS section now shows a card for the attached MCP (with a "Show tools" link). No console errors.
9. Click the MCP node's "Toolkit" combobox again (same handle as step 4).
   - **Verify**: The listbox now contains exactly one `[data-testid="select-option-{mcp_name}"]` row — the just-attached MCP. Confirmed visually: `test-results/screenshots/ELITEA-1955-step10-toolkit-dropdown-after-attach.png`.
10. Select that option.
    - **Verify**: The Toolkit combobox's display value becomes the MCP's name; a new "Tool" combobox (`pipeline-mcp-node-tool-select`) renders on the node.
11. Open the Tool combobox and select a tool from the fixture MCP's tool list (this session: `ask_question`, one of 3 real tools the fixture MCP exposes).
    - **Verify**: The Tool combobox shows the selected tool. An "Input mapping (required N)" accordion (`pipeline-mcp-node-input-mapping-heading`) appears below, with one `Type`/`Value` row per the tool's actual required parameters (this session, `ask_question`: `repoName`, `question` — 2 rows, matching ELITEA-1954's precedent for the same MCP/tool).
12. Fill each Input-mapping "Value" field (`pipeline-mcp-node-input-mapping-value-{param}`) and click the pipeline's Save button (`agent-save-button`).
    - **Verify**: `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` returns `201 Created`; no console errors. Reload via the canonical URL (the one carrying `destTab`/`name`/`viewMode` query params — a bare `/pipelines/all/{id}` 404s, per the already-filed EliteaAI/elitea-testing-public#512 clarification) and confirm the Toolkit, Tool, and Input-mapping values all persisted unchanged. Confirmed visually: `test-results/screenshots/ELITEA-1955-step12-persisted-after-reload.png`.

## Expected Results
- An MCP node's Toolkit dropdown, opened before any MCP is attached in the pipeline's TOOLS section, shows zero real options (MUI's own "None" placeholder renders, with no selectable toolkit).
- Attaching a Remote MCP to TOOLS immediately makes it available in that same node's (already-rendered) Toolkit dropdown — no node re-creation or page reload needed.
- The newly-available toolkit is selectable, its Tool dropdown populates with the toolkit's own tools, and Input-mapping fields render per the selected tool's schema.
- Saving persists the full configuration (Toolkit + Tool + Input-mapping values) through a page reload.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; a Remote MCP (e.g. Web Search) available in the project | setup exists | steps 1, 7–8 | step 1 (auth), step 8 (real MCP attached) | asserted — **CLARIFICATION: no MCP literally named "Web Search" exists in this project; case text is illustrative, a substitute real-tooled MCP was used, same finding as ELITEA-1954 — see Preconditions** |
| 1 Create a new pipeline | Pipeline canvas loads | step 1 | step 1: config panel + canvas visible | asserted |
| 2 Do NOT attach any MCP in the TOOLS section | TOOLS section has no MCP | step 2 | step 2: no toolkit/MCP card present | asserted |
| 3 Click "Add node" and select "MCP" | MCP node is added to the canvas | step 3 | step 3: "MCP 1" node visible | asserted |
| 4 Click on the MCP node to open configuration | Configuration panel opens | step 3 | step 3 | asserted — **CLARIFICATION: live product has no click-to-open action; the node's config fields are always rendered inline/expanded, same reverse-masking finding already recorded in ELITEA-1954's AFS. Not a defect — the observable ("configuration is visible") is still true.** |
| 5 Click "Toolkit" dropdown | Dropdown opens | step 4 | step 4: `aria-expanded="true"` + listbox visible | asserted |
| 6 Verify dropdown is empty or shows message indicating no MCP tools are attached | Dropdown is empty or shows appropriate message | step 5 | step 5: 0 `select-option-*` matches; MUI "None" placeholder renders | asserted |
| 7 Go back to left panel TOOLS section and click "+ MCP" | MCP selection appears | step 7 | step 7: search popper opens | asserted |
| 8 Attach a Remote MCP (e.g., "Web Search") | MCP is attached in TOOLS section | step 8 | step 8: 201 Created, card renders | asserted |
| 9 Click on MCP node again — open "Toolkit" dropdown | Dropdown opens | step 9 | step 9 | asserted |
| 10 Verify newly attached MCP now appears in the dropdown | "Web Search" is listed in the dropdown | step 9 | step 9: exactly 1 `select-option-{mcp_name}` row | asserted *(decomposed: case step 10's "verify" and step 9's "open" are the same AFS step since the option is visible immediately on open)* |
| 11 Select it and configure a tool | Tool is selected | steps 10–11 | step 10: Toolkit combobox value; step 11: Tool combobox value + Input-mapping rows | asserted *(decomposed)* |
| 12 Save pipeline — verify configuration persists | Pipeline is saved and configuration is correct | step 12 | step 12: 201 Created + reload persistence | asserted |
| Expected Final State: MCP node configured with Toolkit and Tool, pipeline saved successfully | — | step 12 | step 12 | asserted |
| Pass/Fail: dropdown empty before attach, populates after; configuration persists | — | steps 5, 9, 12 | steps 5, 9, 12 | asserted |

### Axis 2 — Analyst additions

- Step 5 additionally asserts the exact mechanism of "empty" (zero `select-option-*` matches + the specific MUI placeholder `<MenuItem value=""><em>None</em></MenuItem>`) rather than only the generic case text "empty or appropriate message" — *added: gives the implementer an unambiguous, testid-anchored assertion instead of a vague visual check; also documents that this specific placeholder row carries no `data-testid` today (see Concrete Handles), which is load-bearing for how the implementer must write the assertion.*
- Step 8 additionally asserts the `PATCH .../tool/prompt_lib/{project}/{toolkit_id}` network call and its 201 status — *added: standard side-channel verification per this project's `test-case-analysis` skill; confirms the attach is a real, persisted API action and not merely a client-side render.*
- Console-error checks were added at every step (none observed throughout) — *added: standard practice per this project's skill; zero console errors were observed across the whole flow, no defect to report.*
- Step 12's reload uses the pipeline's canonical URL (with `destTab`/`name`/`viewMode` query params) rather than a bare `/pipelines/all/{id}` — *added: avoids the already-filed EliteaAI/elitea-testing-public#512 404 clarification affecting the reload step, same as ELITEA-1954's AFS.*

## Cleanup

1. This session created one persistent pipeline (`autotest_mcp_empty_toolkit_1955`, id `5288`) on the local DEV backend (`dev.elitea.ai`, project `399`). **Not deleted by this analysis session** (analyst has no automation authoring/cleanup authority — per `.agents/workflow.md`; the implementer's test + teardown is the durable cleanup mechanism, matching the precedent set in `l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md`).
2. This session did **not** create a new MCP toolkit — it reused the pre-existing `autotest_deepwiki_mcp_1954` (id `1266`, ELITEA-1954's leftover residue, itself already flagged there as undeleted). No new toolkit cleanup obligation from this session.
3. Implementer teardown: delete pipeline `5288` via `PipelineAPI.delete_pipeline(5288)` (`automation/api/client.py:672`, confirmed present). The automated test's own fixture-created pipeline should use the same teardown pattern.
4. Flag to the lead: pipeline `5288` and the still-undeleted toolkit `1266` (from ELITEA-1954) are both harmless, uniquely-named, `Private`-project-scoped manual-exploration residue — clean up opportunistically before automated fixtures start accumulating alongside them.

## Concrete Handles (discovered during exploration)

Provenance verified via `cd ../EliteaUI && git fetch origin` (fresh, this session) then `git grep -qF "<testid>" origin/<ref> -- src/` against both `origin/main` and `origin/automation/testids`.

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Pipeline create form Name input | `[data-testid="agent-name-input"]` (`CreateAgentForm.jsx` / `ApplicationEditForm.jsx`, shared) | on-main ✓ | none needed |
| Pipeline create form Description input | `[data-testid="agent-description-input"]` | on-main ✓ | none needed |
| Pipeline Save button (create form and node-config Save both) | `[data-testid="agent-save-button"]` | on-main ✓ | none needed |
| TOOLS section container | `[data-testid="agent-toolkits-section"]` (`ApplicationTools.jsx`, shared by Agent AND Pipeline forms — confirmed via `PipelineConfigurationForm.jsx` import) | on-main ✓ | none needed |
| "+ MCP" button (TOOLS section) | `[data-testid="agent-add-mcp-button"]` (`ToolMenu.jsx:597`) | on-main ✓ | none needed |
| MCP-search-popper search input | `[data-testid="toolkit-search-input"]` (`UnifiedDropdown.jsx:225`) | on-main ✓ | none needed |
| MCP-search-popper result row | `[data-testid="toolkit-menu-item"]` (`UnifiedDropdown.jsx:302,339`) — **shared testid for every row regardless of entity type (toolkit/MCP/agent/pipeline); disambiguate by filtering on visible text, e.g. `popper.locator('[data-testid="toolkit-menu-item"]').filter(has_text=mcp_name)`.** **CORRECTION to `l2_...ELITEA-1954.md` § Concrete Handles**, which claimed this popper's rows carry `[data-testid="select-option-{mcp_name}"]` — verified live this session via `document.querySelectorAll('[data-testid="toolkit-menu-item"]')` (5 rows returned, each literally `toolkit-menu-item`); the `select-option-{value}` pattern belongs to a different component (`SingleSelectMenuItem.jsx`, used by the node's own Toolkit/Tool comboboxes, not this popper). Root cause of the prior AFS's error: the browser-automation tool's auto-generated Playwright code defaults to a role-based locator (`getByRole('menuitem', {name})`) even when a testid exists, which is easy to mistake for "no testid present." | none needed |
| MCP node on canvas | `[data-testid="rf__node-{node_display_name}"]` (ReactFlow's own convention, e.g. `rf__node-MCP 1`) | third-party widget — testid-only, no first-party file | none — third-party ReactFlow |
| MCP node Toolkit select | `[data-testid="pipeline-mcp-node-toolkit-select"]` (`BaseToolNode.jsx:156`) | **on-automation/testids only** (awaiting human promotion to main) | none — first-party, use as-is |
| MCP node Tool select | `[data-testid="pipeline-mcp-node-tool-select"]` (`BaseToolNode.jsx:169`) | **on-automation/testids only** | none |
| MCP node Input-mapping heading | `[data-testid="pipeline-mcp-node-input-mapping-heading"]` (`BaseToolNode.jsx:193`) | **on-automation/testids only** | none |
| MCP node Input-mapping Value field (dynamic per param) | `[data-testid="pipeline-mcp-node-input-mapping-value-{param}"]` (dynamic template, e.g. `...-value-repoName`) | **on-automation/testids only** | none |
| Toolkit/Tool dropdown real option (dynamic) | `[data-testid="select-option-{value}"]` (`SingleSelectMenuItem.jsx:117`) | on-main ✓ | none needed |
| Toolkit/Tool dropdown **empty-state placeholder** (`<MenuItem value=""><em>None</em></MenuItem>`) | **NO `data-testid` — confirmed via source (`SingleSelect.jsx` `renderMenuItems`, the `key="__empty__"` branch) and live DOM.** This is a first-party shared component (`src/[fsd]/shared/ui/select/SingleSelect.jsx`), not a third-party widget, so per policy this is `add-data-testid` work if the team wants to assert the placeholder text directly — but see the recommended assertion below, which does **not** require it. | **Recommended assertion instead: zero-count check.** `page.locator('[data-testid^="select-option-"]').count() == 0` after opening the dropdown is a fully testid-anchored, no-new-testid-needed way to assert "empty" per case step 6 — it doesn't locate the placeholder itself, it asserts the absence of real options (the same testid family already used for populated dropdowns). If the team later wants an explicit assertion on the "None" text, flag `add-data-testid` with a generic name (e.g. `select-empty-placeholder`) since `SingleSelect.jsx` is shared across many features — never a pipeline/MCP-scoped name. |
| Add-node "+" button (canvas toolbar) | existing `PipelineDetailPage.add_node(node_type)` method (`pipeline_detail_page.py:507`) already implements this via `button.MuiIconButton-colorPrimary` + role-based menuitem — **pre-existing tech debt, not introduced by this AFS; reuse as-is, do not duplicate.** | n/a (pre-existing raw-handle method) | — |

## Network Behavior
- `PATCH ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires when attaching an MCP via the "+ MCP" popper; `201 Created` on success. Wait for this before asserting the Toolkit dropdown repopulated.
- `GET ${ELITEA_API_BASE}/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires after attach, fetches the toolkit's tool list that populates the node's Tool dropdown.
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on pipeline Save; `201 Created` on success; persists Toolkit/Tool/Input-mapping state. Wait for this before reloading to assert persistence.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on page load/reload; confirms persisted node config is what the canvas renders from.

## Known Defects Found During Exploration

**None found in the MCP-node empty-Toolkit-before-attach / populate-after-attach behavior itself.** All 12 case steps produced the expected result: the Toolkit dropdown correctly shows zero selectable options (MUI's own empty-state placeholder) before any MCP is attached, attaching an MCP via the TOOLS section "+ MCP" button immediately makes it available in the already-rendered node's Toolkit dropdown (no re-creation or reload needed), the toolkit is selectable, its Tool dropdown populates with its own tools, the Input-mapping section renders per-tool parameters, and the full configuration (Toolkit + Tool + Input-mapping values) persists through save and a full page reload. Zero console errors observed across the entire flow.

One environment observation, already filed by a prior session and reconfirmed here (not re-filed):
- **[INFO] Direct navigation to `/pipelines/all/{id}` (no query params) shows "Page not found"** — already filed as `EliteaAI/elitea-testing-public#512` (label `question`) during ELITEA-1954's analysis. Reconfirmed this session: the reload step must reuse the canonical URL (with `destTab`/`name`/`viewMode` query params), not a bare `/pipelines/all/{id}`.

One AFS-accuracy correction (not a product defect, see Concrete Handles for the full detail):
- `l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md`'s Concrete Handles table misidentified the MCP-search-popper's result-row testid as `select-option-{mcp_name}`; it is actually the shared `toolkit-menu-item` testid, disambiguated by text filter. No tracker issue filed for this — it's a documentation correction within this AFS, not a product or process defect; recorded to memory so future sessions don't propagate the error.

## Blocked Steps

None. All 12 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`). Reuse the MCP-node page-object methods already on `PipelineDetailPage` from ELITEA-1954 (`get_mcp_node_toolkit_value`, `get_mcp_node_tool_value`, `open_mcp_node_toolkit_select`, `open_mcp_node_tool_select`, `get_open_listbox_option_names`, `select_open_listbox_option`, `select_mcp_node_toolkit`, `select_mcp_node_tool`, `fill_mcp_node_input_mapping_value`, `is_input_mapping_section_visible`) — no MCP-node-specific new page-object surface is needed for the Toolkit/Tool/Input-mapping interactions this case touches.
- **`open_mcp_node_toolkit_select()` needs a small fix (or a variant) for the empty-dropdown case.** Its current implementation (`pipeline_detail_page.py:798`) clicks the Toolkit select, then blocks on `self.page.locator(SELECT_OPTION_PREFIX).first.wait_for(state="visible")` — which times out when the dropdown is genuinely empty (confirmed this session: the empty-state placeholder carries no `select-option-*` testid, see Concrete Handles). Recommend either (a) a new `open_mcp_node_toolkit_select_allow_empty()` that instead waits on `mcp_node_toolkit_select`'s own `aria-expanded="true"` attribute (confirmed live: the combobox correctly flips `aria-expanded` on open regardless of option count), or (b) changing the existing method's wait condition to the same `aria-expanded` check universally (works for both empty and populated cases, and is still testid-anchored since it's waiting on the SAME `pipeline-mcp-node-toolkit-select` element, just a different attribute).
  - **IMPLEMENTER AMENDMENT (Phase 2 exploration, this PR):** the analyst's assumption that `aria-expanded` lives on the `pipeline-mcp-node-toolkit-select` element itself was **incorrect** — confirmed live via a CDP scratch probe that `data-testid="pipeline-mcp-node-toolkit-select"` lands on MUI's outer `MuiInputBase-root`/`MuiSelect-root` wrapper `<div>`, while `aria-expanded`/`role="combobox"` live on a NESTED child `<div class="MuiSelect-select">` (MUI's own "display" element) that carried no testid at all. Went with option (a) — added `open_mcp_node_toolkit_select_allow_empty()` (additive, `open_mcp_node_toolkit_select()` untouched) — but it required a genuinely new testid via `add-data-testid`: `SingleSelect.jsx`'s `<Select>` now also sets `SelectDisplayProps={dataTestId ? {'data-testid': `${dataTestId}-combobox`} : undefined}`, opt-in only for callers that already pass `data-testid` (EliteaUI `automation/testids` commit `301d131c`). New locator: `pipeline-mcp-node-toolkit-select-combobox` (`PipelineDetailPage.mcp_node_toolkit_select_combobox`) — reads `aria-expanded` regardless of option count. `close_mcp_node_toolkit_select()` (Escape-key close, AFS step 6) uses the same new element.
- **No existing `PipelineDetailPage` method attaches an MCP/Toolkit via the TOOLS section "+ MCP" UI flow** (unlike `AgentDetailPage.add_mcp()`, `agent_detail_page.py:1108`, which already implements this exact flow using the same testids this AFS confirmed work on the pipeline page too — `agent-add-mcp-button`, `toolkit-search-input`, `toolkit-menu-item`, `components.mui.Popper.select_menuitem`). Since `ApplicationTools.jsx`/`ToolMenu.jsx` is a shared component reused by both Agent and Pipeline detail forms (confirmed via `PipelineConfigurationForm.jsx` import), recommend either porting `AgentDetailPage.add_mcp()`'s implementation onto `PipelineDetailPage` verbatim, or (better, avoids the page-objects "no method duplication" rule) extracting it into a shared mixin/component both detail pages compose — flag this architectural call to the lead if the mixin route is preferred over a pipeline-local duplicate.
  - **IMPLEMENTER AMENDMENT:** went with the straightforward port, split into an open/select pair (`PipelineDetailPage.open_mcp_popper()` / `select_mcp_in_popper()`) rather than one combined `add_mcp()` call — mirrors the existing `open_mcp_node_toolkit_select()` / `get_open_listbox_option_names()` / `select_open_listbox_option()` three-step pattern already used for the node's own Toolkit/Tool selects, and lets the test assert the popper's contents (AFS step 7) as its own step before selecting (AFS step 8), matching the Coverage Map's per-step assertion requirement. Also used the testid-anchored `Popper.select_menuitem_by_testid` helper (already present in `components/mui.py`, added for ELITEA-1735) instead of the role-based `Popper.select_menuitem` that `AgentDetailPage.add_mcp()` itself uses — no mixin extraction; a shared-mixin refactor of `AgentDetailPage`/`PipelineDetailPage` is a bigger architectural question than this case's scope warrants.
- Test-data fixtures: reuse `mcp_toolkit_with_tools` (self-provisioning/self-cleaning, `automation/fixtures/data_fixtures.py:730`) for the attached-MCP; use the plain `pipeline_api.create_pipeline(name, description)` (`automation/api/client.py:606`) for the pipeline shell — deliberately **not** `create_pipeline_with_mcp_node` (that helper pre-configures the node's Toolkit/Tool and pre-attaches 2 MCPs, which is exactly the state this case must NOT start from).
- Wait strategy: wait for `PATCH .../tool/prompt_lib/{project}/{toolkit_id}` (201) after the MCP-attach step before opening the Toolkit dropdown again; wait for `PUT .../application/prompt_lib/{project}/{pipeline_id}` (201) before reloading to assert persistence — not fixed timeouts.
- Minor, out-of-scope observation (not blocking, not filed as a defect): `BaseToolNode.jsx:176,182` pass the MCP-node Input/Output select testids via a prop literally named `dataTestId`, which `.agents/testing.md` § Locator policy calls out as the specifically-forbidden prop-naming shape (`testId` / `<part>TestId` only, never a `data` prefix). This predates this AFS (added during ELITEA-1954's implementation) and doesn't affect this case's own handles (Toolkit/Tool/Input-mapping use the correctly-shaped `data-testid={...}` JSX attribute directly, not a `testId`-family prop) — noted for a future cleanup pass, not filed as a fresh defect since it's pre-existing, already-reviewed code with no functional impact.

---

## Adjustment — 2026-08-28 (repair triage, issue #1890)

**Analyst:** qa-engineer (analyst slot, `adjust-automated-test` Steps 2/5/6)
**Environment re-explored:** `https://dev.elitea.ai` (`/app` prefix) **and** `http://localhost:5173` — both.
**Triage class: D — timing/race in the test's reach. NOT a product bug. Expected-result changes: none.**

### What went red

`test_mcp_node_empty_toolkit_before_attach.py:113` on DEV, GHA run 33066098636
("UI Tests DEV Stable [main] [all]", 2026-08-27), **Step 7**:

```
assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0
E   AssertionError: '+ MCP' popper should list at least one toolkit-menu-item result row
E   assert 0 > 0
```

The two preceding asserts in the same step (`popper.is_visible()`,
`get_mcp_popper_search_input_count(popper) > 0`) both passed. The allure failure
screenshot shows the correct popper open (its "Search mcps…" field and "+ Create new"
row are rendered) with a partially-occluded **"Loading…"** row where the results belong.

### Root cause — stated as fact from the product source

`src/pages/Applications/Components/Tools/ToolMenu.jsx` (identical on `origin/main` and
`origin/automation/testids`) wires the "+ MCP" dropdown as:

```js
const { menuItems: libraryMCPs, isFetching: isFetchingMCPs, ... } =
  useLibraryToolkits(handleSelectToolkitFromLibrary, applicationId, versionId,
                     formik, true, debouncedMCPSearch, !mcpOpened.current);
                                                    // ^^^ forceSkip
```

`mcpOpened.current` only flips to `true` on the render caused by the click that sets
`mcpAnchor` — so **RTK Query's toolkit-list request is skipped until the "+ MCP" button
is first clicked, and only starts firing at that moment.** Meanwhile the popper opens
synchronously (`open={Boolean(mcpAnchor)}`) with `items = []`.

`src/components/UnifiedDropdown.jsx` (also byte-identical on both refs) then renders,
in this order:

| Product state | What is in the DOM | Testid |
|---|---|---|
| `isLoading === true` | one disabled `MenuItem` reading `Loading...` | **none** |
| `!isLoading && items.length === 0` | one disabled `MenuItem` reading `No mcps available` / `No mcps found` | **none** |
| `items.length > 0` | one `MenuItem` per row | `toolkit-menu-item` |
| always, from the first frame | the search `TextField` | `toolkit-search-input` |

So `toolkit-search-input` is present in the popper's **first rendered frame**, while
`toolkit-menu-item` rows only exist after the network round-trip resolves *and*
`useLibraryToolkits`' `menuItems` memo un-gates (it also requires `realToolkitSchemas`,
a second query — `useLibraryToolkits.js`: `if (!libraryToolkits?.rows || !realToolkitSchemas || isLibraryLoading) return []`).

`PipelineDetailPage.get_mcp_popper_menu_item_count()` is a bare synchronous
`popper.locator(...).count()` — **Playwright's auto-waiting does not apply to `.count()`**
— and `open_mcp_popper()` returns the moment `.MuiPopper-root` is visible, adding no
settle. The assertion therefore samples the popper during the guaranteed-empty window.

**The product is behaving correctly.** A loading placeholder followed by populated rows
is the intended, designed behaviour. No defect filed.

### Live evidence (this session, both environments)

Instrumented probe driving the **real** `PipelineDetailPage.open_mcp_popper()` /
`get_mcp_popper_*_count()` methods against a throwaway API-created pipeline:

**DEV (`https://dev.elitea.ai`), 3 fresh browser contexts:**

```
run 1: immediate menu=0 search=1 | items after 536 ms | final=21 | .MuiPopper-root=1
run 2: immediate menu=0 search=1 | items after 550 ms | final=21 | .MuiPopper-root=1
run 3: immediate menu=0 search=1 | items after 560 ms | final=21 | .MuiPopper-root=1
```

State timeline for the first open (ms from click): `103 → LOADING (0 rows)`,
`559 → ITEMS (21 rows)`.

**Populating request** (fires *on* the click, at +22 ms; 200 at +325 ms):

```
GET https://dev.elitea.ai/api/v2/elitea_core/tools/prompt_lib/399
      ?query=&sort_by=name&sort_order=asc&mcp=true&limit=50&offset=0   → 200
```

**Second open in the same context is instant** (`immediate menu=21`, 25 ms) — RTK Query
serves the cached page. The race is therefore **first-open-only**, which is exactly why a
warm/short reproduction can look green and why #1776's "ran 4/4 standalone, no fix needed"
conclusion was wrong.

**The exact Step-7 call sequence, current vs. proposed, on DEV:**

```
current   run1: popper_visible=True search_count=1 menu_count=0  -> step7 FAIL
current   run2: popper_visible=True search_count=1 menu_count=0  -> step7 FAIL
proposed  run1: popper_visible=True search_count=1 menu_count=21 -> step7 PASS
proposed  run2: popper_visible=True search_count=1 menu_count=21 -> step7 PASS
```

**localhost is NOT immune — it is slower.** Same probe against `http://localhost:5173`
(`EliteaUI@automation/testids`), 3 fresh contexts: `menu_at_assert=0` every time, rows
visible only at **1899 / 1917 / 1905 ms**. And the merged spec itself, run unmodified
against localhost this session, fails **byte-identically**:

```
tests/ui/pipelines_2/test_pipeline_mcp_node_empty_toolkit_before_attach.py:113
E   AssertionError: '+ MCP' popper should list at least one toolkit-menu-item result row
E   assert 0 > 0
```

⇒ This is an unconditional latent race, not a DEV-shard-load artifact. **The implementer's
local gate reproduces it and will verify the fix** — do not treat a localhost run as
out-of-scope for this repair.

Screenshots: `test-results/screenshots/ELITEA-1955-dev-popper-loading.png` (popper open,
search field rendered, zero rows) and `ELITEA-1955-dev-popper-loaded.png` (21 rows).

### Recommended repair — a wait, not an assertion change

**What to wait on:** the popper's first `[data-testid="toolkit-menu-item"]` row reaching
`visible`. It is the only testid that distinguishes "loaded" from "loading" — both the
`Loading...` and the `No mcps available` placeholders are untestid'd disabled `MenuItem`s
(see the table above), so "wait for Loading to disappear" is not expressible with handles
that exist on `main`.

**Where it goes:** a **new, additive** page-object method on `PipelineDetailPage`,
alongside the existing count methods:

```python
def wait_for_mcp_popper_items(self, popper: Locator, timeout: int = 10000) -> None:
    """Wait until the "+ MCP" popper's result rows have finished loading. ..."""
    popper.locator(self.TOOLKIT_MENU_ITEM_SELECTOR).first.wait_for(
        state="visible", timeout=timeout
    )
```

`TOOLKIT_MENU_ITEM_SELECTOR` is the **already-existing** class-level constant
`'[data-testid="toolkit-menu-item"]'` (`pipeline_detail_page.py:1566`) — no new locator,
no new testid, no new raw handle.

**Where it is called:** in the spec, inside the existing `allure.step("Step 7 — …")`
block, **between** the search-input assertion and the menu-item assertion:

```python
assert pipeline_page.get_mcp_popper_search_input_count(popper) > 0, (...)   # unchanged
pipeline_page.wait_for_mcp_popper_items(popper, timeout=UI_ELEMENT_TIMEOUT)  # NEW
assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0, (...)      # unchanged
```

That ordering is deliberate: the search-input assertion keeps its current meaning
(the popper renders its search field synchronously — a real, still-verified property),
and only the row-count assertion gets the settle it always needed.

**Timeout:** the module's existing `UI_ELEMENT_TIMEOUT = 10_000`. Measured worst case is
1.92 s (localhost), 0.56 s (DEV) — >5× headroom. Do not invent a new constant, and do not
raise it; if 10 s is ever exceeded the correct response is investigation, not a longer wait.

**Rejected alternatives, with reasons:**

- *Put the wait inside `get_mcp_popper_menu_item_count()`* — rejected. A method named
  `get_..._count()` is a query; making it block for 10 s silently changes the semantics of
  5 merged call sites and becomes a foot-gun for any future case that legitimately asserts
  an **empty** popper (an MCP-less project), which would then hang instead of returning 0.
- *Put the wait inside `open_mcp_popper()`* — rejected **for this card's scope**, not on
  merit. It would fix all three affected specs at once, but `open_mcp_popper()` is shared
  with the two sibling failures owned by separate cards (#1891, #1892), so changing it here
  silently repairs work under other ownership. Recommend the lead consider consolidating
  into `open_mcp_popper(..., wait_for_items: bool = True)` once all three land — see
  *Notes for the lead*.
- *A fixed settle (`page.wait_for_timeout`)* — rejected: `.agents/conventions.md` § Hard
  don'ts. (`AgentDetailPage.add_mcp()`'s `wait_for_timeout(1000)` is the sibling that
  happens to pass on DEV; it is pre-existing tech debt, **not** the pattern to copy.)

**Precedent for the chosen shape already exists in-repo:** `Popper.select_menuitem_by_testid`
(`components/mui.py:264-267`) already does `option.wait_for(state="visible", timeout=timeout)`
on the same `toolkit-menu-item` testid — which is precisely why Step 8 (select) never flaked
while Step 7 (count) did. The repair makes the count path consistent with the select path.

### Preserve-the-nature check (`adjust-automated-test` Step 3)

| Case element | Before | After |
|---|---|---|
| Step 7 — popper opens | `popper.is_visible()` | unchanged |
| Step 7 — search field renders | `get_mcp_popper_search_input_count(popper) > 0` | unchanged |
| Step 7 — result rows listed | `get_mcp_popper_menu_item_count(popper) > 0` | **unchanged** (same method, same `> 0`, same message) |
| Steps 1–6, 8–12 | — | untouched |

**Expected-result changes: none.** No assertion is weakened, dropped, made conditional, or
lowered; the § Expected Results block above is unchanged. Only *how the test reaches* the
already-loaded popper changes.

### Handles Reference — provenance re-verified 2026-08-28

`cd ../EliteaUI && git fetch origin`, then the two-stage closure grep from
`.agents/workflow.md` § Closure record (`-i` + `[:=]` filter):

```
toolkit-search-input                           main:YES  testids:YES
toolkit-menu-item                              main:YES  testids:YES
agent-add-mcp-button                           main:YES  testids:YES
agent-toolkits-section                         main:YES  testids:YES
agent-toolkit-card                             main:YES  testids:YES
agent-save-button                              main:YES  testids:YES
```

Hits behind the two popper-internal rows:

```
origin/main:src/components/UnifiedDropdown.jsx:229:  data-testid="toolkit-search-input"
origin/main:src/components/UnifiedDropdown.jsx:308:  data-testid="toolkit-menu-item"
origin/main:src/components/UnifiedDropdown.jsx:344:  data-testid="toolkit-menu-item"
```

**Every handle the repair depends on is on `origin/main`. The repair adds no testid, so it
opens no promotion gap.**

The `pipeline-mcp-node-*` rows in § Concrete Handles above still read
"on-automation/testids only" — that row is now **stale, and the correction is recorded
here rather than rewritten in place** (this Adjustment section is the newer record): those
testids are **runtime-composed** (`typeTestIdPrefix={...}` → `` typeTestId={`${typeTestIdPrefix}-${key}`} ``
in `flow-editor/ui/settings/InputMappings/InputMapping.jsx:62`), which the bare-substring
stage-1 grep cannot see at all — the exact false-negative class `.agents/workflow.md`
§ Closure record warns about. Verified two other ways instead:
`git diff origin/main origin/automation/testids -- src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseToolNode.jsx`
is **empty** (file identical on both refs), and the DEV GHA run reached Step 7, which is
only possible if Steps 3–6's node handles resolved on the deployed build.

### Known defect / product-observation note (not filed)

`UnifiedDropdown.jsx`'s loading and empty-state `MenuItem`s carry **no `data-testid`**, so
automation cannot distinguish *"still loading"* from *"this project has no MCPs"*. That is a
**testid gap, not a product bug**, and it is deliberately **out of scope for this repair**: a
new testid would land on `automation/testids` only, which is unusable for a fix shipping to
`main` and running on DEV. Worth a follow-up `add-data-testid` card (generic names on a
shared component — e.g. `dropdown-loading-item` / `dropdown-empty-item`, never a
`toolkit-`/`mcp-`-scoped name, per `.agents/testing.md` § Locator policy's shared-component
rule). Raised to the lead; not filed as a `bug`.

### Notes for the lead

- **Same root cause, two sibling cards.** `test_pipeline_tools_section_mcp_add_view_remove.py:77`
  (#1892) fails the *identical* `get_mcp_popper_menu_item_count(popper) > 0` assertion and is
  fixed by the identical one-line call. `test_pipeline_mcp_node_fresh_attach.py` has **three**
  `open_mcp_popper()` sites (lines 106, 356, 555), two of which assert the row count.
- **#1891 is probably NOT the same bug.** It failed one assertion *earlier* —
  `get_mcp_popper_search_input_count(popper) > 0` returned 0 — and the search field is in the
  popper's first rendered frame, so a *load* race cannot explain it. The likelier mechanism is
  `Popper.wait_for()` matching the wrong node: it returns `page.locator(".MuiPopper-root").first`,
  and the "+ MCP" button is wrapped in a `Tooltip` (`ToolMenu.jsx:603-615`,
  `data-testid="agent-add-mcp-button-tooltip"`) whose MUI tooltip **also** renders a
  `.MuiPopper-root`. My probe measured `.MuiPopper-root count == 1` on every open (the tooltip
  `title` is `''` when the entity is saved and unlocked, so MUI renders nothing), so I could not
  reproduce it — flagging it as a hypothesis for whoever takes #1891, not a finding.
- **Consolidation opportunity:** if #1890/#1891/#1892 are worked together, moving the wait into
  `open_mcp_popper(..., wait_for_items: bool = True)` is the cleaner end state than three call
  sites. Keeping it additive here is a scope decision, not a technical preference.
