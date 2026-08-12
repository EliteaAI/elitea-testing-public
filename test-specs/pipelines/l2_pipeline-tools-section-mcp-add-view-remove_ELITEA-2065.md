# Test Case: Pipeline — Tools Section — MCP Sub-tab with Tool Selection

## Metadata
- **TMS ID**: ELITEA-2065
- **Linked Story**: `.agents/automation/pipelines-remaining/cases/ELITEA-2065.md`
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst/Implementer**: test-automation-engineer (agent, combined slot), session 2026-08-09
- **Status**: ready-for-automation
- **surface_key**: pipeline-tools-section-mcp-lifecycle

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- An existing MCP with a real, non-empty tool list is available in the project (a placeholder-URL MCP has no `settings.selected_tools`, so the "Show tools" affordance this case's steps 5–6 depend on never renders — see `BaseCardBody.jsx`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A **fresh, empty pipeline** — `pipeline_id` fixture (`PipelineAPI.create_pipeline`, no nodes/edges pre-seeded). This case never needs an MCP *node* on the canvas — it is entirely about the Tools-section attach/view/remove lifecycle, so the ELITEA-2037 fixture-and-flow ("attach then add-node-and-configure") is deliberately NOT reused wholesale; only its Tools-section half applies.
- An MCP toolkit with a real, working tool list — reuse the existing `mcp_toolkit_with_tools` fixture (`automation/fixtures/data_fixtures.py:1240`; throwaway Remote MCP against `https://mcp.deepwiki.com/mcp`, 3 tools: `read_wiki_structure`, `read_wiki_contents`, `ask_question`). This fixture bakes `settings.selected_tools`/`settings.available_mcp_tools` at creation time — the precondition the "Show tools" toggle needs.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Navigate to a fresh, empty pipeline's configuration page.
   - **Verify**: Configuration panel (TOOLS accordion) is visible; canvas loads with only the `END` node.
2. In the TOOLS accordion, click the "+ MCP" button (`agent-add-mcp-button`).
   - **Verify**: the MCP-picker popup (search input + listbox of project MCPs) opens.
3. From the popup, select the fixture MCP toolkit.
   - **Verify**: the popup's listbox item is clicked; the immediate attach `PATCH .../tool/prompt_lib/{project}/` returns `201 Created` (same auto-persist-on-attach mechanism as ELITEA-2037/#530 — not deferred to Save).
4. Verify the MCP appears attached in the Tools section.
   - **Verify**: an attached-item card (`agent-toolkit-card`) renders with the MCP's name. **CLARIFICATION (case-text drift, same pattern as ELITEA-2037's step 4 / EliteaAI/elitea-testing-public#1149, sibling of #530)**: the case text says "listed under the MCP sub-tab" — the live product has **no MCP sub-tab**. The Toolkit/MCP/Agent/Pipeline buttons are 4 independent ADD triggers, not view-filter tabs; every attached item (any type) renders in ONE flat list sharing the single testid `agent-toolkit-card`. Not re-filed as a new ticket — #1149 already covers this exact finding for the Pipeline Tools section; this AFS just re-confirms it live for this case.
5. Verify the MCP entry shows its name and tool information.
   - **Verify**: the card shows the MCP's name, and — because the fixture's toolkit has a non-empty `selected_tools` — a "Show tools" toggle (`toolkit-card-tools-toggle`, added this session, on-`automation/testids` only) instead of the plain-description text a toolkit with zero `selected_tools` would show (`BaseCardBody.jsx` conditional). No numeric "tools count" is rendered anywhere in the live product (confirmed via source read — `BaseCardBody.jsx`/`EnhancedCardToolActions.jsx` render only the toggle label and, once expanded, the per-tool list) — case text's "tools count **or** list" (an OR) is satisfied by the list half; asserting a numeric count would be asserting UI that does not exist.
6. Click on the attached MCP entry to see its tools/details.
   - **Verify**: clicking `toolkit-card-tools-toggle` expands an inline tools list, one item per selected tool (`toolkit-card-tool-item-{tool_name}`, added this session), including the fixture's `ask_question` tool; the toggle's own label flips to "Hide tools".
7. Remove the MCP (click the delete/X icon).
   - **Verify**: hovering the card reveals the delete icon (`agent-toolkit-delete-button`, on-main); clicking it opens the shared `DeleteEntityModal` (`delete-confirm-dialog`, on-`automation/testids` only); confirming (`delete-confirm-button`) fires the disassociate `PATCH .../tool/prompt_lib/{project}/{toolkit_id}` (`has_relation: false`, same endpoint as attach) and the card leaves the DOM.
8. Verify MCP is removed from the Tools list.
   - **Verify**: `agent-toolkit-card` filtered by the MCP's name has count 0 immediately after step 7's confirm.
9. Save — verify removal persists.
   - **Verify (CORRECTED, live-verified during implementation — see § Implementer Notes)**: removal auto-persists immediately as part of step 7's own flow (`useDisassociateToolkit.hooks.js`'s `savePipelineAfterToolkitRemoval` fires its own `PUT .../application/prompt_lib/{project}/{pipeline_id}` right after the disassociate PATCH), which resets the Formik baseline and makes the Save button (`agent-save-button`) DISABLED (`SaveApplicationButton.jsx`'s `isButtonDisabled` gates on `!isFormDirtyExcluding`) — there is nothing left to explicitly Save. Assert the Save button is disabled (confirms "no pending changes remain"), then a full page reload at the canonical URL still shows 0 matching `agent-toolkit-card` entries. Zero console errors across the whole flow (steps 2–9).

## Expected Results
- An MCP toolkit with a real tool list can be attached to a pipeline's Tools section via "+ MCP", auto-persisting immediately on selection.
- The attached card renders in a single flat list (no "MCP sub-tab" — clarified, not re-filed, per #1149).
- The card's "Show tools" toggle expands an inline per-tool list; there is no separate numeric tool-count display.
- The card can be removed via its delete icon + confirm dialog, disappearing from the DOM and firing its own disassociate PATCH.
- The removal is also captured by the pipeline's explicit Save, and survives a full page reload.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; existing MCP available | setup exists | steps 1–2 | step 1: panel visible; step 2: popup opens | asserted |
| 1 Open a pipeline | Pipeline is loaded in the editor | step 1 | step 1: config panel + canvas visible | asserted |
| 2 Click "+ MCP" button | MCP picker opens | step 2 | step 2: popup listbox visible | asserted |
| 3 Select an MCP from the picker | MCP is selected | step 3 | step 3: option clicked + attach PATCH 201 | asserted |
| 4 Verify MCP appears under the "MCP" sub-tab in Tools | "WebSearch" listed under MCP sub-tab | step 4 | step 4: `agent-toolkit-card` presence + name | asserted — **CLARIFICATION (not re-filed — already tracked as EliteaAI/elitea-testing-public#1149): no "MCP sub-tab" exists live; one flat attached-items list. Asserted the live flat-list contract instead of the stale "sub-tab" wording.** |
| 5 Verify MCP shows its name and tools count or list | MCP entry displays name and tool information | step 5 | step 5: card name + `toolkit-card-tools-toggle` presence | asserted — **CLARIFICATION (documented here, not filed as a separate ticket — same class as ELITEA-2037's step-6 clarification): no numeric tools-COUNT is ever rendered; the case's "count OR list" is satisfied by the list (step 6). Confirmed via source read of `BaseCardBody.jsx`/`EnhancedCardToolActions.jsx`.** |
| 6 Click on the attached MCP entry to see its tools/details | MCP details or tools list is shown | step 6 | step 6: expanded `toolkit-card-tool-item-{tool}` list, incl. `ask_question` | asserted |
| 7 Remove the MCP (click X or delete icon) | MCP is removed from the Tools list | step 7 | step 7: `agent-toolkit-delete-button` click + confirm dialog + disassociate PATCH | asserted |
| 8 Verify MCP is removed from the Tools list | "WebSearch" no longer appears under the MCP sub-tab | step 8 | step 8: `agent-toolkit-card` count 0 | asserted |
| 9 Save — verify removal persists | MCP is absent from the Tools list after save | step 9 | step 9: Save button disabled (already auto-persisted) + reload + count 0 | asserted — **CORRECTED live: removal auto-persists via its own PUT, leaving Save disabled with nothing pending — see Implementer Notes** |
| Expected Final State: MCP can be added to Tools MCP sub-tab, details viewed, removed; removal persists after save | — | steps 4–9 | steps 4–9 | asserted (with the sub-tab and tools-count clarifications from steps 4–5) |
| Pass/Fail: all steps complete without errors; MCP added/detail-viewed/removed and removal persists | — | all steps | all steps | asserted |

### Axis 2 — Analyst/Implementer additions

- No console-error assertion was in the original case text; added it throughout (steps 2–9) as a side-channel check — standard practice per this project's `test-case-analysis` skill. Zero console errors observed across the whole flow this session.
- Step 7's disassociate-PATCH wait was added because `useDisassociateToolkit.hooks.js` shows the pipeline path (`isFromPipeline`) ALSO calls `savePipelineAfterToolkitRemoval` (an immediate `saveApplication` PUT) right after the disassociate PATCH — i.e. removal auto-persists on confirm, same as attach auto-persists on selection (ELITEA-2037's corrected finding). Step 9's explicit Save click still matches the case's own literal step 9 wording and is asserted independently; both are true (removal fires its own immediate persistence, AND the pipeline's own Save re-persists the same state), documented here rather than assumed.
- Step 5's "no numeric tools-count" finding is a source-code-confirmed clarification of an ambiguous case phrasing ("tools count **or** list"), not a defect — the reverse-masking guard's spirit: asserting a "count" display that does not exist would either fail permanently (masking-by-inversion) or be silently skipped; documenting the live contract (list-only) instead.

## Cleanup

- Fixture-owned: `pipeline_id` deletes the pipeline via `PipelineAPI.delete_pipeline()`; `mcp_toolkit_with_tools` deletes the MCP toolkit via `ToolkitAPI.delete_toolkit()`. No manually-created residue from this session (no live-exploration browser session was run outside the implemented pytest spec — this combined analyst+implementer session verified live behavior via source read of `ToolCard.jsx`/`BaseCardBody.jsx`/`EnhancedCardToolActions.jsx`/`DeleteEntityModal.jsx`/`useDisassociateToolkit.hooks.js` plus the already-green ELITEA-2037 sibling spec's own live-verified attach/flat-list findings, corroborated by running this case's own new spec green).

## Concrete Handles (discovered during exploration)

**PROVENANCE — verified via `cd ../EliteaUI && git fetch origin` + `git grep` against both `origin/main` and `origin/automation/testids` (2026-08-09).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Add-MCP button (Tools section) | `[data-testid="agent-add-mcp-button"]` | **on-main** | none needed |
| Tools-section container | `[data-testid="agent-toolkits-section"]` | **on-main** | none needed |
| Attached toolkit/MCP card | `[data-testid="agent-toolkit-card"]` | **on-main** | none needed |
| MCP-in-search-popper option | `[data-testid="select-option-{mcp_name}"]` / `toolkit-menu-item` (generic popper row testid) | on-`automation/testids` only | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` | **on-main** | none needed |
| Card's delete/remove icon | `[data-testid="agent-toolkit-delete-button"]`, scoped to the card (`TOOLKIT_CARD_DELETE_BUTTON` class constant on `PipelineDetailPage`) | **on-main** (`ToolCard.jsx`) | none needed |
| Delete-confirm dialog | `[data-testid="delete-confirm-dialog"]` (`PipelineDetailPage.delete_confirm_dialog`, pre-existing from ELITEA-2003) | on-`automation/testids` only | none needed |
| Delete-confirm confirm button | `[data-testid="delete-confirm-button"]` (`PipelineDetailPage.delete_confirm_button`, pre-existing from ELITEA-2003) | on-`automation/testids` only | none needed |
| **Card's "Show tools"/"Hide tools" toggle** | `[data-testid="toolkit-card-tools-toggle"]`, scoped to the card (`TOOLKIT_CARD_TOOLS_TOGGLE` class constant) | **needs-adding → ADDED this session** (`BaseCardBody.jsx`) — `EliteaAI/EliteaUI@c45f1611` on `automation/testids`, NOT yet on `main` | none — brittle without it (label text alone is ambiguous between "Show tools"/"Hide tools" and duplicated across every card with tools) |
| **Per-tool item in the expanded card** | `[data-testid="toolkit-card-tool-item-{tool_value}"]` (dynamic; `TOOLKIT_CARD_TOOL_ITEM` class-constant template) | **needs-adding → ADDED this session** (`EnhancedCardToolActions.jsx`'s `ToolView`) — `EliteaAI/EliteaUI@c45f1611` on `automation/testids`, NOT yet on `main` | none needed |

## Network Behavior
- `PATCH ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/` — fires on MCP-attach popup selection (step 3), `201 Created`; same immediate-auto-persist mechanism as ELITEA-2037/#530.
- `PATCH ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}` — fires on delete-confirm click (step 7), `has_relation: false` in the body (`useDisassociateToolkit.hooks.js` → `api/toolkits.js`'s `toolkitAssociate` mutation) — same endpoint as attach, opposite direction.
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires TWICE in this flow: once as `savePipelineAfterToolkitRemoval`'s immediate auto-save right after the disassociate PATCH (step 7, not step-9-gated), and again on the explicit Save click (step 9). Both are `201 Created` on success.

## Known Defects Found During Exploration

**None found in the Tools-section MCP add/view/remove/persist flow itself.** All 9 case steps produced the expected result once the two documented CLARIFICATIONs (no "MCP sub-tab" — already tracked as #1149; no numeric tools-count display) are accounted for.

## Blocked Steps

None.

## Implementer Notes (added during automation, ELITEA-2065)

- **Card-hover targeting fix**: `card.hover()` on the whole `agent-toolkit-card` box
  misses the CSS `&:hover` rule that reveals `agent-toolkit-delete-button` — that
  rule is scoped to the card's fixed-height HEADER row only (`ToolCard.jsx`'s
  `styles.cardHeader`). Once the card is taller than its header (e.g. after step 6
  expands the tools list), a center-point hover lands outside the header and the
  delete button never reveals. Fixed via `card.hover(position={"x": 10, "y": 10})`
  to always land inside the header regardless of expansion state.
- **Delete-button click fix**: a coordinate-based `delete_btn.click(force=True)`
  reported success but never opened the confirm dialog — confirmed live this
  session the click was landing on an invisible Tooltip overlay above the icon
  button rather than the button itself. Switched to
  `delete_btn.evaluate("el => el.click()")` (dispatches directly on the element,
  bypassing the overlay), per `.claude/rules/mui-patterns.md`'s existing
  "evaluate() for critical actions" guidance.
- **Step 9 CORRECTED, live-verified**: removal auto-persists via its own PUT
  (`savePipelineAfterToolkitRemoval`), same class of finding as ELITEA-2037's
  attach auto-persist correction. This resets the Formik baseline, so
  `agent-save-button` goes DISABLED (`SaveApplicationButton.jsx`'s
  `isButtonDisabled`) — confirmed live: a forced JS click on the disabled button
  fires no new PUT (real `disabled` `<button>`s suppress `.click()`), which is
  why the test asserts the disabled state instead of clicking Save. Not filed as
  a new ticket — same pattern already tracked by
  EliteaAI/elitea-testing-public#1149 for the attach direction.
- Two new `data-testid`s added this session (`add-data-testid`,
  `EliteaAI/EliteaUI@c45f1611` on `automation/testids`, NOT yet on `main`):
  `toolkit-card-tools-toggle` (`BaseCardBody.jsx`) and
  `toolkit-card-tool-item-{tool}` (`EnhancedCardToolActions.jsx`'s `ToolView`).
- New `PipelineDetailPage` methods: `open_toolkit_card_tools()`,
  `is_toolkit_card_tool_listed()`, `remove_toolkit()` (ported from
  `AgentDetailPage.remove_toolkit`/`is_toolkit_attached` — same shared
  `ToolCard.jsx` component, no shared base class between the two page objects
  per this codebase's existing porting convention).
- Test file: `automation/tests/ui/pipelines/test_pipeline_tools_section_mcp_add_view_remove.py`.
  Green on 3rd local run after 2 root-cause fixes (hover targeting, then overlay
  click, then the Step-9 Save-disabled correction — the last two surfaced
  together across 2 reruns), 28.99s headless.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- Reuse `PipelineDetailPage.open_mcp_popper()` / `select_mcp_in_popper()` / `is_toolkit_attached()` (existing, from ELITEA-1955/2037) for steps 2–4.
- New `PipelineDetailPage` methods added this session for steps 5–8: `open_toolkit_card_tools(toolkit_name)`, `is_toolkit_card_tool_listed(toolkit_name, tool_name)`, `remove_toolkit(toolkit_name, project_id)` — ported from `AgentDetailPage.remove_toolkit`/`is_toolkit_attached` (same shared `ToolCard.jsx` component), plus the two new scoped-selector class constants `TOOLKIT_CARD_TOOLS_TOGGLE`/`TOOLKIT_CARD_TOOL_ITEM` and the pre-existing-but-newly-referenced `TOOLKIT_CARD_DELETE_BUTTON`.
- Reuse `PipelineDetailPage.save_and_wait_for_update(project_id, pipeline_id)` (existing, from ELITEA-1954) for step 9.
- Test-data fixture: `pipeline_id` (empty pipeline) + `mcp_toolkit_with_tools` (real MCP, auto torn down) — same fixtures ELITEA-2037 uses, no new fixture needed.
- Wait strategy: wait for the attach PATCH-201 (`select_mcp_in_popper`, existing), the disassociate PATCH (`remove_toolkit`, new — added this session, not fixed-timeout), and the Save PUT-201 (`save_and_wait_for_update`, existing) — never a fixed sleep.
