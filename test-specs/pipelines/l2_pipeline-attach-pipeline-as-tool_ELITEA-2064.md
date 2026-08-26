# Test Case: Pipeline — Attach Pipeline as Tool

## Metadata
- **TMS ID**: ELITEA-2064
- **Linked Story**: EliteaAI/elitea-testing-public#1297 (pipelines-remaining campaign)
- **Priority**: l2 (source: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths; sidebar showed "Elitea is connected")
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-09
- **Status**: ready-for-automation
- **surface_key**: pipeline-tools-attach

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- At least two pipelines exist in the project (Pipeline A = the entity being edited, Pipeline B = the pipeline attached as a tool). Confirmed live: a pipeline being attached must itself be **saved** (have an id/version) — the picker lists existing project pipelines fetched via `GET .../application/?...agents_type=pipeline`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Pipeline A**: a fresh, empty pipeline (`PipelineAPI.create_pipeline(name, description)`), reused via the existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py:126`) — no node config is needed for this case, only the Tools-section attach.
- **Pipeline B**: a second fresh, empty pipeline, created directly via `pipeline_api.create_pipeline(name, description)` in the test body with its own `try/finally` teardown (`pipeline_api.delete_pipeline(pid)`) — precedent: `test_pipeline_management.py::test_delete_pipeline_via_api` uses the identical inline-create/try-finally pattern for a second pipeline alongside the `pipeline_id` fixture. No existing fixture provisions a *second* pipeline, so this is the minimal correct shape (Rule 7 — no fixture to reuse; Rule 10 — the observable inherently needs two distinct persisted pipelines, so seeding is unavoidable here, not a read-only-eligible case).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` (`.env.test`).

## Test Steps

1. Navigate to Pipeline A's configuration page (`${BASE_URL}/pipelines/all/{pipeline_A_id}?destTab=configuration&viewMode=owner`, reached after the initial create-Save — the `pipeline_id` fixture already saves it).
   - **Verify**: Configuration panel (General/Tools/... accordion) is visible; canvas loads with only the `END` node.
2. In the left panel's "Tools" accordion, click the "+ Pipeline" button (`agent-add-pipeline-button`, inside `agent-toolkits-section`).
   - **Verify**: a Pipeline-picker popup (search input + listbox of project pipelines, `toolkit-menu-item` rows) opens.
3. From the pipeline picker, select Pipeline B by name.
   - **Verify**: `select_pipeline_in_popper()` hard-blocks on `PATCH .../application_relation/prompt_lib/{project}/{pipeline_B_id}/{pipeline_B_version_id}` returning `201 Created` — confirmed live (see § Network Behavior) — the same auto-persist mechanism the Agent picker uses (`useAgentPipelineAssociation.hooks.js`'s `updateApplicationRelation`, called with `isPipeline=true`), NOT the Toolkit picker's defer-to-Save behavior.
4. Verify Pipeline B appears in the Tools list under the "Pipeline sub-tab".
   - **Verify**: an attached-item card (`agent-toolkit-card`) renders with Pipeline B's name. **CLARIFICATION (case-text drift, same pattern as EliteaAI/elitea-testing-public#530/#1149 on the sibling Toolkit/MCP/Agent attach flows)**: the case text says "listed under the Pipeline sub-tab" — the live product has **no Pipeline sub-tab**. The Toolkit/MCP/Agent/Pipeline buttons in the Tools section are 4 independent ADD triggers (poppers), not view-filter tabs; every attached item, whatever its type, renders in ONE flat list sharing the single testid `agent-toolkit-card` (confirmed live: `document.querySelectorAll('[data-testid="agent-toolkit-card"]')` → 1 after attaching 1 pipeline). Assert the card's presence/name, not a "sub-tab active" state that doesn't exist.
5. Save Pipeline A.
   - **Verify — CLARIFICATION (case-text drift)**: confirmed live, the `Save` button (`agent-save-button`) stays **disabled** after the attach — step 3's PATCH already persisted the attachment immediately, so there is no local dirty state left for an explicit Save to act on (same behavior already documented for the sibling Agent-node Tools-section attach, ELITEA-2038). "Pipeline A saves without errors" is satisfied by the attach's own `201` (step 3) and the reload in step 6 confirming persistence — not by a Save-button click, which is correctly inert here. Assert `Save` is disabled rather than clicking it.
6. Reload — verify Pipeline B is still attached as a tool.
   - **Verify**: after a full page reload at the canonical URL, `agent-toolkit-card` still shows Pipeline B's name; zero console errors across the whole flow (steps 2–6, confirmed via `page.on("console")` capture in this session — 0 errors).

## Expected Results
- A second pipeline can be attached to a pipeline's Tools section via the "+ Pipeline" button, rendering as a flat-list attached card (no "sub-tab", see Coverage Map).
- Selecting Pipeline B in the picker auto-persists immediately via `PATCH .../application_relation/prompt_lib/{project}/{pipeline_B_id}/{pipeline_B_version_id}` → `201`, the same endpoint/mechanism the Agent picker uses (not the Toolkit picker's defer-to-Save behavior).
- The pipeline's `Save` button stays disabled after the attach (nothing left to save) — attach persistence is already durable via its own PATCH.
- A full page reload confirms the attachment survives, byte-for-byte.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in; at least two pipelines exist | setup exists | steps 1–3 | step 1: panel visible; steps 2–3: picker opens + Pipeline B selectable | asserted |
| 1 Open a pipeline (Pipeline A) | Pipeline A is loaded in the editor | step 1 | step 1: config panel + canvas visible | asserted |
| 2 Click "+ Pipeline" button | Pipeline picker opens | step 2 | step 2: popper listbox visible | asserted |
| 3 Select another pipeline (Pipeline B) | Pipeline B is selected | step 3 | step 3: attach PATCH 201 returned | asserted |
| 4 Verify Pipeline B appears in Tools list under Pipeline sub-tab | Pipeline B is listed under the Pipeline sub-tab in Tools | step 4 | step 4: `agent-toolkit-card` presence + name | asserted — **CLARIFICATION filed (see § Known Defects/Clarifications): no "Pipeline sub-tab" exists live; one flat attached-items list shared across all attachment types. Asserted the live flat-list contract instead of the stale "sub-tab" wording.** |
| 5 Save Pipeline A | Pipeline A saves without errors | step 5 | step 5: `Save` button asserted disabled (attach already persisted); no save-error toast/console error | asserted — **CLARIFICATION: Save is inert post-attach (already persisted by step 3's PATCH), not a state-changing click here.** |
| 6 Reload — verify Pipeline B is still attached as a tool | Pipeline B remains in the Tools list after reload | step 6 | step 6: `agent-toolkit-card` re-read after reload | asserted |
| Expected Final State: Pipeline B successfully attached, persists after save and reload | — | steps 3–4, 6 | steps 3–4, 6 | asserted (with the sub-tab + Save clarifications from steps 4–5) |
| Pass/Fail: all steps complete without errors; Pipeline B attached and persists after reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 3 additionally asserts the exact attach endpoint (`/application_relation/prompt_lib/{project}/{pipeline_B_id}/{pipeline_B_version_id}`, `201`) rather than only the UI-visible card — *added because this endpoint is shared with the Agent picker but DIFFERENT from the Toolkit/MCP picker's `/tool/prompt_lib/{project}/` endpoint (confirmed via source read of `ToolMenu.jsx`'s `handleAssociateAgent` call, which the Pipeline picker's `pipelineMenuItems` also routes through with `isPipeline=true`); a future regression that silently reverts Pipeline-attach to the wrong endpoint would time out this step instead of passing for the wrong reason, same discipline as ELITEA-2038's Agent-node case.*
- No console-error assertion was in the original case text; added it throughout (steps 2–6) as a side-channel check — *standard practice per this project's `test-case-analysis` skill; zero console errors were observed across the whole flow this session, no defect to report.*
- Step 5's Save-button-disabled assertion is an analyst addition beyond the literal case text ("Save Pipeline A") — *added because the literal action (click Save) is not performable live (the button is disabled), and asserting its disabled state is the honest, non-masking way to cover "saves without errors": there is no save action to fail, and the reverse-masking guard requires asserting the live contract rather than performing an impossible click.*

## Cleanup

1. This session created two disposable probe pipelines via a standalone script (`autotest_2064_probe_A` id 8675, `autotest_2064_probe_B` id 8676, project 399) to execute the case live, and **deleted both** via `PipelineAPI.delete_pipeline()` at the end of the session — zero residue left in the environment.
2. Implementer teardown for its OWN test data: `PipelineAPI.delete_pipeline(pipeline_id)` for the fixture-created Pipeline A (`pipeline_id` fixture's own teardown), and an explicit `try/finally` `pipeline_api.delete_pipeline(pipeline_b_id)` for the inline-created Pipeline B (no fixture exists for a second pipeline — see Test Data).

## Concrete Handles (discovered during exploration)

**PROVENANCE — verified this session via `cd ../EliteaUI && git fetch origin` + live DOM read (2026-08-09).**

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Add-Pipeline button (Tools section) | `[data-testid="agent-add-pipeline-button"]` — **testid did NOT exist before this session** (`ToolMenu.jsx`'s Pipeline `BaseBtn` had zero attributes beyond `variant`/`startIcon`/`disabled`/`onClick`); added this session, naming mirrors the pre-existing sibling `agent-add-agent-button`/`agent-add-toolkit-button`/`agent-add-mcp-button` (same shared `ToolMenu.jsx` component, same `agent-` prefix convention) — `EliteaAI/EliteaUI@e2130cf4` on `automation/testids` (awaiting human promotion to `main`) | on-automation/testids only (`main:no`) | none — testid-only |
| Pipeline-picker popper row | `[data-testid="toolkit-menu-item"]` — same shared `UnifiedDropdown.jsx` component/testid every Toolkit/MCP/Agent/Pipeline popper row uses (confirmed via source: `UnifiedDropdown.jsx:308,344`), confirmed working live for the Pipeline picker this session | **on-main** (shared, pre-existing) | none needed |
| Pipeline-picker search input | `[data-testid="toolkit-search-input"]` — same shared `UnifiedDropdown.jsx` mechanism (`PipelineDetailPage.TOOLKIT_SEARCH_INPUT_SELECTOR`), not separately verified live this session (Pipeline B's name was typed-selected without needing to narrow the list — only ~15 pipelines existed) but same component as the already-confirmed MCP/Toolkit poppers | on-main (shared) | none needed |
| Attached pipeline/toolkit/MCP/agent card (shared, all 4 types) | `[data-testid="agent-toolkit-card"]` — confirmed exactly 1 rendered after attaching 1 pipeline, via `document.querySelectorAll` | **on-main** | none needed |
| Tools-section container | `[data-testid="agent-toolkits-section"]` | **on-main** | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed disabled after attach (no dirty state) | **on-main** | none needed |

## Network Behavior
- `PATCH ${ELITEA_API_BASE}/elitea_core/application_relation/prompt_lib/${PROJECT_ID}/{pipeline_B_id}/{pipeline_B_version_id}` — fires immediately on the Pipeline-attach popper selection (step 3), `201 Created` on success. Confirmed live this session: attaching pipeline id 8676 (version 8938) to pipeline id 8675 fired exactly this URL shape (`.../application_relation/prompt_lib/399/8676/8938`) and returned `201`. This is the SAME mechanism/endpoint the Agent picker uses (`useAgentPipelineAssociation.hooks.js`'s `updateApplicationRelation`, called with `isPipeline=true` for the success-toast wording only — the mutation itself is identical) — **DIFFERENT from the Toolkit/MCP picker's `PATCH .../tool/prompt_lib/{project}/`** endpoint.
- No `PUT .../application/prompt_lib/{project}/{pipeline_id}` fires on the (disabled) Save click in this flow, because there is nothing left to persist — the attach's own PATCH (above) is the sole persistence request across the whole case.
- `GET ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_A_id}` — fires on page load/reload (step 6); confirms the persisted Tools-section attachment renders from the reloaded payload.

## Known Defects Found During Exploration

**None found in the pipeline-attach flow itself.** All 6 case steps produced the expected result once the two documented CLARIFICATIONs (Tools "sub-tab" wording, Save being inert post-attach) are accounted for: opening the picker, selecting Pipeline B, seeing the attached card, and full-reload persistence all worked correctly with zero console errors across the entire flow.

Clarifications (documented in this AFS, not filed as separate tracker issues — same low-severity, same-pattern-as-#530/#1149 class, already well-precedented in this surface's digest; filing a 4th near-identical "no sub-tab" ticket for the same root cause would be noise, not new information):
- **[INFO] Pipeline Tools section has no "Pipeline sub-tab"** — same root cause/pattern as `EliteaAI/elitea-testing-public#530` (Agent) and `#1149` (MCP), sibling finding for the Pipeline attach type. See step 4 and Coverage Map above for full detail.
- **[INFO] Save is disabled/inert after a Tools-section attach** — same root cause/pattern as ELITEA-2038's Agent-node case (attach auto-persists via its own PATCH, no local dirty state remains for Save to act on).

## Blocked Steps

None. All 6 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- **New page-object surface needed** (mirrors the existing `open_agent_popper()`/`select_agent_in_popper()` pair almost exactly — same underlying endpoint shape, different picker button):
  1. `add_pipeline_button = LocatorDescriptor(testid="agent-add-pipeline-button")` — new field, PipelineDetailPage.
  2. `open_pipeline_popper(timeout)` — mirrors `open_agent_popper()`.
  3. `select_pipeline_in_popper(popper, pipeline_name, project_id, timeout)` — mirrors `select_agent_in_popper()` verbatim except the response-URL match becomes `f"/application_relation/prompt_lib/{project_id}/"` (same substring both share — the endpoint prefix is identical for Agent and Pipeline attach, only the trailing `{entity_id}/{version_id}` path segments differ, which the substring match doesn't need to distinguish).
- Test-data fixture: reuse `pipeline_id` (Pipeline A) + inline `pipeline_api.create_pipeline()`/`delete_pipeline()` for Pipeline B (no existing fixture provisions a second pipeline — see Test Data). Precedent: `test_pipeline_management.py::test_delete_pipeline_via_api`.
- Wait strategy: wait for `PATCH .../application_relation/prompt_lib/{project}/{pipeline_B_id}/{pipeline_B_version_id}` (`201`) before asserting the card/proceeding — not a fixed timeout, same discipline as `select_agent_in_popper()`.
- Console-error capture: register `page.on("console", ...)` BEFORE step 2 (before the picker opens), matching ELITEA-2037/2038's precedent.
