# Test Case: Pipeline — Collapse Left Panel

## Metadata
- **TMS ID**: ELITEA-2072
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, pipelines-remaining wave-04
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline exists and is open in editor view. Reused the existing
  `pipeline_llm_code_end` fixture (`LLM 1 -> Code 1 -> END`, 3 nodes / 2
  edges) rather than adding a new fixture — Rule 7 (reuse before create);
  this case makes no assertion about node type/count, so any already-proven
  pipeline satisfies it.

## Test Data
### reuse-existing
- none required beyond the seeded pipeline above.

## Test Steps
1. Navigate to the pipeline's canvas (`PipelineDetailPage.navigate()` +
   `wait_for_canvas()`).
   - **Verify**: left configuration panel (`configuration_tab`, testid
     `pipeline-config-tab`) is visible with its expanded width (320px,
     confirmed live) and its collapse toggle button is visible.
2. *(Folded into step 1 — "locate the collapse button" and "verify panel
   fully visible" are the same observable this session confirmed together;
   see Coverage Map.)*
3. Click the collapse toggle button
   (`toggle_config_panel_collapse()` — new method).
   - **Verify**: the panel's rendered width strictly decreases from its
     step-1 baseline (confirmed live: 320px -> 28px).
4. Verify the configuration sections are no longer present.
   - **Verify**: `agent-toolkits-section` (Tools), `pipeline-step-limit-input`
     (Advanced/Step limit), `pipeline-editor-notes-section` (Editor Notes),
     and `agent-information-section` (Information) all have
     `to_have_count(0)` — confirmed live these sections literally UNMOUNT
     (`{!collapsed && (...)}` in `GeneralFormPanel.jsx`), not merely
     `display:none`.
5. Verify the canvas area expands to fill the freed space.
   - **Verify**: `canvas_wrapper`'s (testid `rf__wrapper`) rendered width
     strictly increases vs. its step-1 baseline — confirmed live this
     session: 765px -> 1057px on a fixed viewport after collapsing.
6. Click the same toggle button again to restore the panel
   (`toggle_config_panel_collapse()`).
   - **Verify**: the panel's rendered width returns to (`pytest.approx`) its
     exact step-1 baseline (320px) — confirmed live this is a deterministic
     round trip (no drift/animation-settled offset observed).
7. Verify the configuration sections are visible again.
   - **Verify**: the same four section testids from step 4 are all visible
     again (`to_be_visible()`), and the panel's width matches step 1
     exactly.

## Expected Results
- The left configuration panel starts expanded (320px) with a visible
  collapse toggle button.
- Clicking the toggle collapses the panel to a 28px strip; every
  configuration section (Tools, Advanced/Step limit, Editor Notes,
  Information) unmounts from the DOM.
- Collapsing the panel measurably grows the canvas area's rendered width.
- Clicking the same toggle again restores the panel to its exact original
  width and remounts every configuration section.
- No console errors, no network requests fire for either click (pure
  client-side React state — confirmed live, see Network Behavior).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline in editor view | panel loads fully visible | step 1 | `step 1`: panel width == 320px | asserted |
| 2 Locate the collapse button at top of left panel | collapse button visible | step 1 | `step 1`: `config_panel_collapse_button` visible | asserted *(folded — one observable with case step 1, confirmed both together live)* |
| 3 Click the collapse button | left panel collapses | step 3 | `step 3`: panel width decreases | asserted |
| 4 Verify left panel collapses (sections hidden) | panel minimized, sections not visible | step 4 | `step 4`: 4 section testids `to_have_count(0)` | asserted |
| 5 Verify canvas/chat area expands | canvas/chat takes more horizontal space | step 5 | `step 5`: `canvas_wrapper` width increases | asserted |
| 6 Click expand button to restore left panel | left panel expands | step 6 | `step 6`: panel width returns to baseline | asserted |
| 7 Verify configuration sections visible again | all sections (Tools, Advanced, etc.) restored | step 7 | `step 7`: same 4 testids visible again | asserted |

### Axis 2 — Analyst additions

- step 3/6 assert zero console errors and zero pipeline-persist network
  requests (`prompt_lib` substring) across the whole collapse -> expand
  sequence — *added: confirmed live via source read
  (`GeneralFormPanel.jsx`'s `onClickCollapsed` is pure `useState`, no API
  call; `ConfigurationTab.jsx`'s `onCollapsed` callback only recomputes a
  CSS `maxWidth` string) and via a live browser probe (no new console
  entries after either click) — this is the same "pure client-side
  operation" class as the canvas zoom/pan/control-panel cases in this
  surface (ELITEA-2019/2057), and guards against a regression that
  accidentally wires a persist call onto this purely visual toggle.*
- step 7 additionally asserts the panel's width is an EXACT match
  (`pytest.approx`) to its step-1 baseline, not just "some non-collapsed
  width" — *added: confirmed live the round trip is deterministic (28px <->
  320px, no intermediate/settled value observed), same "exact restore"
  pattern as ELITEA-2019's Fit View determinism.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` — handled by the `pipeline_llm_code_end`
   fixture's teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Left configuration panel container | `PipelineDetailPage.configuration_tab` (existing `LocatorDescriptor`, testid `pipeline-config-tab`) | — |
| Collapse/expand toggle button | **NEW** `PipelineDetailPage.config_panel_collapse_button` (testid `pipeline-config-collapse-button`) — testid added via `add-data-testid` onto `GeneralFormPanel.jsx`'s `IconButton` (had none before this case); one static testid serves both directions, only the icon (`DoubleLeftIcon`/`DoubleRightIcon`) swaps visually — no state-switched testid value, so no #277/state-ternary concern. | — |
| Panel width getter | **NEW** `PipelineDetailPage.get_config_panel_width()` — `self.configuration_tab.bounding_box()["width"]`. | — |
| Toggle action | **NEW** `PipelineDetailPage.toggle_config_panel_collapse()` — `self.config_panel_collapse_button.click()`. | — |
| Tools section | `PipelineDetailPage.toolkits_section` (existing `LocatorDescriptor`, testid `agent-toolkits-section`) | — |
| Advanced section (Step limit field) | `PipelineDetailPage.step_limit_input` (existing `LocatorDescriptor`, testid `pipeline-step-limit-input`) | — |
| Editor Notes section | `PipelineDetailPage.editor_notes_section` (existing `LocatorDescriptor`, testid `pipeline-editor-notes-section`) | — |
| Information section | `PipelineDetailPage.information_section` (existing `LocatorDescriptor`, testid `agent-information-section`) | — |
| Canvas wrapper (for the "canvas expands" observable) | `PipelineDetailPage.canvas_wrapper` (existing `LocatorDescriptor`, testid `rf__wrapper`) | — |

## Network Behavior
- **None** — confirmed live via source read (`GeneralFormPanel.jsx`'s
  `onClickCollapsed` is pure `useState`) and a live browser probe (no new
  console entries, no XHR/fetch after either click). Collapsing/expanding
  the panel is not persisted state — a page reload always restores the
  expanded default (out of scope for this case's steps, noted for
  awareness only).

## Known Defects Found During Exploration
- None. Collapse/expand behaves exactly as the case describes, confirmed
  live: the panel shrinks from 320px to a 28px strip, every configuration
  section unmounts, the canvas area's rendered width grows to fill the
  freed space, and clicking the same toggle again restores the exact
  original width with every section remounted.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Fixture: `pipeline_llm_code_end` (existing, `automation/fixtures/data_fixtures.py`)
  — reused unmodified.
- Page object: `automation/pages/pipeline_detail_page.py`. Three NEW members
  shipped: `config_panel_collapse_button` (`LocatorDescriptor`),
  `toggle_config_panel_collapse()`, `get_config_panel_width()` — all
  additive, one new testid (`pipeline-config-collapse-button`, added via
  `add-data-testid` onto `GeneralFormPanel.jsx`, committed + pushed to
  `EliteaAI/EliteaUI@automation/testids`). Every other handle this case
  needs (the four section testids, `canvas_wrapper`) already existed.
- `helpers._navigate_to_canvas(page, pipeline_id)` is the existing shared
  navigation helper — reuse it, don't re-navigate manually.
- Live-confirmed numeric example (2026-08-09, `AutoTest_Pipeline_probe_2020`
  pipeline, default MCP viewport): panel width 320px -> click -> 28px (4
  section testids: 15 -> 1 buttons total inside the panel, i.e. only the
  toggle itself remains) -> canvas wrapper width 765px -> 1057px -> click
  again -> panel back to 320px, all 4 sections remounted. Use
  before/after relative assertions in the test (don't hardcode the canvas
  wrapper's exact px values — they depend on viewport size and other panes'
  state); the panel's own 320px/28px pair IS a static CSS value
  (`GeneralFormPanel.jsx`'s `maxWidth`/`minWidth` ternary), safe to assert
  exactly.
