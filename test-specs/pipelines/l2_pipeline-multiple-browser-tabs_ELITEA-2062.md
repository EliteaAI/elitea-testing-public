# Test Case: Pipeline — Multiple Tabs

## Metadata
- **TMS ID**: ELITEA-2062
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w5`
- **Status**: ready-for-automation

## Case-text interpretation (load-bearing — read before implementing)

The case text's "tab"/"tablist"/"close button (X)" describes **real browser
tabs**, not an in-app tab-bar widget. Confirmed by source read
(`../EliteaUI/src/pages/Pipelines/Pipelines.jsx` → `PipelinesListPage.open_pipeline_by_name()`
→ `card.click()` — a plain SPA route push, no `target="_blank"`, no anchor) —
**there is no in-app UI feature that keeps multiple pipelines "open as tabs"
simultaneously inside one browser tab.** The product has no such widget to
test. What DOES exist and matches the case's exact language (tablist,
switch, close-X) is the browser's own tab strip, driven here via
`BrowserContext.new_page()` / `Page.bring_to_front()` / `Page.close()` — the
same idiom already merged in
`automation/tests/ui/agents/test_agent_hub_my_liked_reload_cross_tab_sync.py`
(Tab A / Tab B pattern) and in `pipeline_detail_page.py:6917-6923`'s
`context.expect_page()` (toolkit "open in new tab" button). The case is
really testing: (a) `document.title` is set correctly and independently per
browser tab for two different pipelines (the app's own
`useBrowserPageTitle()` hook, `../EliteaUI/src/hooks/useBrowserPageTitle.js`,
sets `Pipeline: ${name} - ${projectName}` per route), and (b) one tab's
navigation/close has zero effect on a sibling tab's state (each `Page` is an
independent document — no app-level cross-tab state leak to test for on
THIS particular flow, unlike ELITEA-2365's Redux-store case).

## Preconditions
- User is logged in (`auth_state` on localhost).
- Two disposable pipelines exist, created via `pipeline_api.create_pipeline()`
  for isolation (same pattern as ELITEA-2025's pin-to-top test) — no
  nodes/config needed, the tab/title flow doesn't depend on pipeline content.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- **Pipeline 1** and **Pipeline 2**, `pipeline_api.create_pipeline(name=..., description=...)`.
  Any two distinct names work — the case's own Test Data table says "MCPNode
  (or any second pipeline)", i.e. the specific name is not load-bearing.
  Both cleaned up via `pipeline_api.delete_pipeline(pid)` in a `finally` block.

## Test Steps

(Live-executed and confirmed this session against `/pipelines/all`, project
`Private`/399, Playwright MCP `browser_tabs` (list/new/select/close) driving
real browser tabs sharing the SAME authenticated `BrowserContext` — using
pre-existing pipelines `AutoTest_Pipeline_probe_2020` id `8056` and
`probe-pipeline` id `6934` as the two pipelines for this analyst-session
probe, since no disposable pipelines were created for it; the AFS below
specs the isolated-data shape per the project's standard pattern.)

1. **Tab A** (the test's `page` fixture): navigate to the dashboard
   (`PipelinesListPage.navigate()`), open Pipeline 1
   (`open_pipeline_by_name()`). **Verify**: `page.title() ==
   f"Pipeline: {pipeline_1_name} - {project_name}"` — confirmed live
   (`"Pipeline: AutoTest_Pipeline_probe_2020 - project_user_659"`); capture
   `project_name` dynamically (see Automation Hints — do not hardcode it,
   it is environment-specific, not "Private").
2. Open a **second, brand-new browser tab** (`page.context.new_page()`) and
   navigate it to the dashboard (`/pipelines/all`). **Verify**: Tab A is
   UNAFFECTED — `page.title()` (Tab A) is still the Step-1 pipeline title,
   and `len(page.context.pages) == 2` — confirmed live (case Step 2: "Tab A
   remains in the tablist").
3. In the new tab (**Tab B**), open Pipeline 2
   (`open_pipeline_by_name()`). **Verify**: `tab_b.title() ==
   f"Pipeline: {pipeline_2_name} - {project_name}"` — confirmed live
   (`"Pipeline: probe-pipeline - project_user_659"`).
4. **Verify** both tabs coexist with their own correct, independent titles:
   Tab A still shows Pipeline 1's title, Tab B shows Pipeline 2's title —
   confirmed live via `browser_tabs` `list` (case Step 4).
5. **Switch to Tab A** (`page.bring_to_front()`). **Verify**: Tab A still
   shows Pipeline 1 — both `page.title()` AND the detail page's own Name
   field (`name_input.input_value() == pipeline_1_name`) — confirmed live
   (case Step 5; the stronger DOM-level check catches a case the title
   alone wouldn't: a tab that kept its OLD title but silently
   navigated/reset its content).
6. **Close Tab B** (`tab_b.close()`). **Verify**: Tab A remains open and
   fully functional — `len(page.context.pages) == 1`, `page.title()` and
   `name_input.input_value()` still both correct for Pipeline 1 — confirmed
   live (case Step 6).
7. **Side-channel check** — zero console errors across the whole flow —
   confirmed live (`browser_console_messages`, `all=true` → 0 errors across
   both tabs' full lifecycle).

## Expected Results
- Each browser tab's `document.title` is set independently and correctly
  per its own current route (`Pipeline: <name> - <project>` /
  `Pipelines: all - <project>`), confirmed via the app's
  `useBrowserPageTitle()` hook.
- Opening a pipeline in one tab has zero effect on a sibling tab's title or
  loaded content (no shared/leaked navigation state across tabs).
- Closing one tab leaves every other tab's state (title + DOM content)
  completely intact.
- Zero console errors across the whole multi-tab flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline — verify tab shows "Pipeline: <Name> - <Project>" in the tablist | Tab is labeled with pipeline name and project name | step 1 | `page.title() == f"Pipeline: {name1} - {project_name}"` | asserted |
| 2 Navigate back to dashboard without closing the tab | Dashboard loads; pipeline tab remains in tablist | step 2 | new Tab B navigates to dashboard; Tab A's `page.title()` unchanged, `len(context.pages) == 2` | asserted — see § Case-text interpretation for why "dashboard" opens in a NEW tab, not Tab A itself |
| 3 Open a different pipeline (e.g. MCPNode) | Second pipeline opens | step 3 | `tab_b.title() == f"Pipeline: {name2} - {project_name}"` | asserted (uses a disposable "Pipeline 2" instead of the case's literal "MCPNode" example — case text says "or any second pipeline") |
| 4 Verify second tab appears in the tablist alongside first | Both pipeline tabs are visible in the tablist | step 4 | `browser_tabs list` shows both titles; test asserts `len(context.pages) == 2` + both titles independently | asserted |
| 5 Click the first tab — verify it switches back to that pipeline | First pipeline is loaded when its tab is clicked | step 5 | `page.bring_to_front()` then `page.title()` + `name_input.input_value()` both match Pipeline 1 | asserted |
| 6 Click the close button (X) on one tab — verify it closes and the other remains | Closed tab is removed; the other tab remains open | step 6 | `tab_b.close()`; `len(context.pages) == 1`; Tab A's title + Name field still correct | asserted |
| Expected Final State: Multiple pipeline tabs coexist; switching loads correct pipeline; closing removes only that tab | — | steps 1-6 | steps 1-6 | asserted |
| Pass/Fail: all steps complete without errors; tabs switch/close correctly | — | all steps | all steps + step 7 console-error check | asserted |

### Axis 2 — Analyst additions

- **Project-name suffix must be captured dynamically, never hardcoded** —
  *added: unlike `test_agent_hub_page_loads_private_project.py`'s
  `EXPECTED_PROJECT_NAME = "Private"` constant, THIS environment's active
  project's `useSelectedProjectName()` resolves to the real DB `name` field
  (confirmed live: `"project_user_659"`, not the sidebar's static "Project:
  Private" badge text — read `../EliteaUI/src/hooks/useSelectedProject.jsx`:
  `useSelectedProjectName = () => useSelectedProjectProperty('name',
  'Private')`, defaulting to `"Private"` ONLY before the project object
  loads). Hardcoding `"Private"` here would be a silent false-negative risk
  the moment this project's real name diverges further from the sidebar
  label. Capture it once from the dashboard's own title
  (`"Pipelines: all - {project_name}"`, split on `" - "`) and reuse for both
  pipeline-title assertions.*
- **DOM-level content check on tab-switch-back, not just the title** —
  *added: the case's Step 5 says "verify it switches back to that pipeline";
  the title string alone is a necessary but not sufficient proof (a tab
  could theoretically retain a stale title while its content silently
  changed underneath, e.g. an in-place SPA route change that doesn't
  trigger the title hook's `useEffect` deps). Asserting
  `name_input.input_value() == pipeline_1_name` on top of the title closes
  that gap at zero extra cost — confirmed live, both match.*
- **Console-error check across the full 2-tab lifecycle** — *added:
  zero-cost given the live session was already open; silent errors are the
  worst bugs per skill discipline. Confirmed 0 errors across open-tab1 →
  open-tab2-dashboard → open-pipeline-in-tab2 → switch → close.*

## Cleanup
- `pipeline_api.delete_pipeline(pipeline_1_id)` and
  `pipeline_api.delete_pipeline(pipeline_2_id)` in a `finally` block.
- `tab_b.close()` is a case step, not cleanup — but the `finally` block
  must tolerate it already being closed (call is idempotent/no-op on an
  already-closed `Page`, or wrap in a guarded `if not tab_b.is_closed()`).
- This analyst session's own probe used two pre-existing pipelines
  (`AutoTest_Pipeline_probe_2020` id `8056`, `probe-pipeline` id `6934`)
  rather than creating fresh ones — neither was modified, nothing to clean
  up from this session.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. **This
case needs NO new testids** — the "tabs" under test are the browser's own
tab strip (native Playwright `Page`/`BrowserContext` API, not app DOM), and
every app-side handle it touches already exists.

| Element | Testid | LocatorDescriptor field | Provenance |
|---|---|---|---|
| Pipeline card name (dashboard) | `entity-card-name` | `entity_card_name` (existing field, `pipelines_list_page.py`) | on-main ✓ — confirmed live |
| Pipeline detail Name input | `agent-name-input` (shared with Agent form) | `name_input` (existing field, `pipeline_form_page.py:30`) | on-main ✓ — confirmed live |
| Browser tab title | N/A — native `document.title` / `Page.title()` | N/A | N/A — no testid concept applies to a browser tab's title |
| Browser tab list/select/close | N/A — native `BrowserContext.new_page()` / `Page.bring_to_front()` / `Page.close()` | N/A | N/A — no app DOM involved |

## Network Behavior
- No new network shape beyond the pipeline dashboard's existing list fetch
  (`GET /api/v2/elitea_core/applications/prompt_lib/{project}?...agents_type=pipeline...`)
  and the existing detail fetch (`GET /application/{id}`) — both already
  exercised by every other pipeline-detail AFS in this suite. Opening a
  second browser tab triggers its own independent instance of these same
  calls; no cross-tab request coupling observed.

## Known Defects Found During Exploration
None. The multi-tab flow (per the § Case-text interpretation reading)
automates cleanly against the live product — `document.title` is correctly
and independently set per tab, and closing one tab has zero observable
effect on a sibling tab's title or DOM content. Zero console errors across
the whole flow.

## Blocked Steps
None. All 6 case steps automate cleanly against the live product with
zero new testids — no `add-data-testid` work needed for this case.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches every other pipeline spec).
- Reuse `pipeline_api.create_pipeline()` / `pipeline_api.delete_pipeline()` for
  test data (same pattern as ELITEA-2025's pipeline test).
- **Cross-tab pattern**: mirror
  `test_agent_hub_my_liked_reload_cross_tab_sync.py`'s Tab A (`page` fixture)
  / Tab B (`page.context.new_page()`) shape exactly — same `finally`-block
  discipline (`if tab_b is not None: tab_b.close()`), same
  `page.bring_to_front()` for switching back to Tab A.
- **Capture the project name once, dynamically** (see Axis 2), e.g.:
  ```python
  pipelines_list_page.navigate()
  project_name = page.title().split(" - ", 1)[1]  # "Pipelines: all - {project_name}"
  ```
  then assert every subsequent pipeline title as
  `f"Pipeline: {name} - {project_name}"`.
- **Verify tab-switch-back with the Name field, not just the title**
  (`name_input.input_value() == pipeline_1_name`) — see Axis 2.
- No new page-object methods needed — `PipelinesListPage.navigate()` /
  `open_pipeline_by_name()`, `PipelineDetailPage.wait_for_detail_page_load()`,
  and the shared `name_input` field cover every DOM interaction; the
  tab-level operations are plain `playwright.sync_api.Page`/`BrowserContext`
  calls, not page-object methods.
