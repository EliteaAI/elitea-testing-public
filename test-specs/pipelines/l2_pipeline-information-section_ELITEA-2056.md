# Test Case: Pipeline — Information Section

## Metadata
- **TMS ID**: ELITEA-2056
- **Linked Story**: none (tracking issue TBD — filed by the orchestrator on PR open)
- **Priority**: l2 (source TMS case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent), combined analyst+implementer session, 2026-08-09
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- An existing pipeline is open, with at least one node so it has a real
  entry point (needed for the Trigger row to render — see Concrete Handles).

## Test Data

### generate-per-test (fixture, cleaned up in its own teardown)
- `pipeline_with_llm_id` (existing fixture, `automation/fixtures/data_fixtures.py`)
  — a fresh pipeline with a single LLM node connected to `END`. Confirmed live
  this session (probe pipeline id 8669/8670/8671, same `instructions` YAML
  shape as this fixture): the LLM node auto-becomes the entry point, which is
  what makes the Information section's Trigger row render at all
  (`ApplicationInformation.jsx`'s `isPipeline && triggerData?.type` guard —
  `triggerData` comes from `useGetPipelineTriggerQuery`, keyed on the entry
  point). Default trigger type is "Chat Message" (matches the case's own
  step-5 example) — also independently confirmed by the merged
  `test_entry_point_trigger_types_persist.py` ("Chat Message default").

## Test Steps
1. Navigate to the pipeline (`PipelineDetailPage.navigate(pipeline_id)`).
   - **Verify**: pipeline loads (canvas/editor visible).
2. Locate the "Information" section in the left panel.
   - **Verify**: `information_section` (testid `agent-information-section`)
     is visible — confirmed live: expanded by default on the detail page, no
     click needed (matches the existing ELITEA-2020 digest finding).
3. Read "Pipeline ID:" row.
   - **Verify**: `copy_id_button` (testid `copy-id`) is visible and its text
     is the pipeline's own numeric id (`get_pipeline_id() == str(pipeline_id)`).
4. Read "Version ID:" row.
   - **Verify**: `copy_version_id_button` (testid `copy-version-id`) is
     visible and its text is a non-empty numeric string
     (`get_version_id().isdigit()`).
5. Read the "Trigger:" row.
   - **Verify**: `information_trigger_row` (testid `information-trigger-row`)
     is visible with text `"Trigger:Chat Message"` — same no-literal-space
     DOM shape the ELITEA-2041 AFS already documented (CSS flex `gap`, not a
     text character).
6. Locate the "Pipeline:" row's "Show" link.
   - **Verify**: `information_show_link` (testid
     `pipeline-information-show-link`, added this session — see Concrete
     Handles) is visible with text `"Show"`.
7. Click `copy_id_button`.
   - **Verify**: the app-wide toast (`toast-alert`, `data-severity="info"`)
     becomes visible with text `"The ID has been copied to the clipboard."`
     (confirmed live, `get_toast_alert("info")`/`get_toast_text()`), AND
     `navigator.clipboard.readText()` returns the pipeline's own id (safe —
     the real pytest `context` fixture grants `clipboard-read`/`-write`, per
     the ELITEA-2026 precedent).
8. Click `copy_version_id_button`.
   - **Verify**: the toast becomes visible with text `"The Version ID has
     been copied to the clipboard."`, AND the clipboard content equals the
     version id read in step 4.
9. Click `information_show_link`.
   - **Verify**: a modal opens (`role="dialog"`, title "Pipeline") rendering
     the pipeline as a Mermaid diagram (**not** a navigation — see § Known
     Defects Found During Exploration for the case-text-vs-live-product
     clarification). Confirmed live: the modal's mermaid content resolves
     via the pre-existing `chat-mermaid-diagram-svg-container` testid
     (shared `MermaidDiagramOutput/DiagramOutput.jsx` component, same one
     the chat surface already uses — tracked naming tech debt, not
     introduced by this case) and renders ≥1 `<svg>` node.
   - **Known defect** (filed this session, see below): opening this modal
     deterministically (2/2) throws an uncaught console `InvalidStateError`
     from `svg-pan-zoom`'s `resetZoom` on a single-node diagram. Assert this
     step's outcome (modal + diagram visible) with `expect.soft()` for the
     console-cleanliness portion only — the modal-open/diagram-visible
     assertions themselves are NOT masked; only the "zero console errors"
     side-channel check is scoped to exclude this known, filed defect.

## Expected Results
- The Information section (expanded by default) shows Pipeline ID, Version
  ID, Trigger type, and the "Pipeline: Show" row.
- Copy ID / Copy Version ID both produce an info-severity toast AND write
  the correct value to the clipboard.
- Clicking "Show" opens a modal rendering the pipeline as a Mermaid diagram
  (the live-contract "visual representation" branch — see clarification
  below on the case text's "navigates to... YAML or visual representation"
  wording).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing pipeline | Pipeline is loaded in the editor | step 1 | `step 1`: canvas/editor visible | asserted |
| 2 Expand "Information" section | Information section is visible | step 2 | `step 2`: `information_section` visible | asserted *(no click needed — expanded by default, confirmed live)* |
| 3 Verify "Pipeline ID:" with numeric value + Copy ID button | Pipeline ID shown with copy button | step 3 | `step 3`: `copy_id_button` visible, text == pipeline id | asserted |
| 4 Verify "Version ID:" with numeric value + Copy version ID button | Version ID shown with copy button | step 4 | `step 4`: `copy_version_id_button` visible, text is numeric | asserted |
| 5 Verify "Trigger:" shows trigger type (e.g. "Chat Message") | Trigger type correctly displayed | step 5 | `step 5`: `information_trigger_row` text == `"Trigger:Chat Message"` | asserted |
| 6 Verify "Pipeline:" shows a "Show" link | "Show" link visible | step 6 | `step 6`: `information_show_link` visible, text == "Show" | asserted |
| 7 Click "Copy ID" — verify copied to clipboard | Pipeline ID copied (toast/clipboard) | step 7 | `step 7`: toast text + `navigator.clipboard.readText()` | asserted |
| 8 Click "Copy version ID" — verify copied to clipboard | Version ID copied (toast/clipboard) | step 8 | `step 8`: toast text + clipboard content | asserted |
| 9 Click "Show" link — verify it navigates to pipeline YAML or visual representation | Navigation occurs to the pipeline representation | step 9 | `step 9`: modal opens, Mermaid diagram renders | asserted *(live-contract correction — see clarification below: the product does NOT navigate; it opens a modal with a Mermaid-rendered "visual representation" branch of the case's own either/or wording)* |

**Axis 2 — Analyst additions.**
- `step 9` also captures a genuine, deterministic console-error defect
  (filed `EliteaAI/elitea-testing-public#1368`) as a scoped `expect.soft()`
  — *added: side-channel check per skill discipline; confirmed 2/2
  reproducible this session, sibling to the pre-existing `#1045`.*
- (nothing else added beyond the case.)

## Cleanup
1. Delete the fixture pipeline via `pipeline_api.delete_pipeline(pid)`
   (`pipeline_with_llm_id` fixture teardown, automatic).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Information section | `PipelineDetailPage.information_section` (testid `agent-information-section`) | pre-existing |
| Pipeline ID + copy button | `PipelineDetailPage.copy_id_button` / `get_pipeline_id()` (testid `copy-id`) | pre-existing |
| Version ID + copy button | `PipelineDetailPage.copy_version_id_button` / `get_version_id()` (testid `copy-version-id`) | pre-existing |
| Trigger row | `PipelineDetailPage.information_trigger_row` (testid `information-trigger-row`) | pre-existing (ELITEA-2041) |
| "Show" link | **testid needed** — confirmed live via `document.querySelectorAll`: the "Show" `Typography` (`ApplicationInformation.jsx`, `showPipeline` conditional block, same guard shape as the pre-existing `information-trigger-row`) had NO `data-testid` at all. | **Resolved during ELITEA-2056 implementation:** added `data-testid="pipeline-information-show-link"` to `EliteaUI/src/pages/Applications/Components/Applications/ApplicationInformation.jsx`, committed + pushed to `automation/testids` (`EliteaAI/EliteaUI@22184211`). `PipelineDetailPage.information_show_link` added. |
| Show-link modal's diagram | **No new testid needed** — the modal (`StyledShowContextModal.jsx`, shared with Agents' AgentModal) has no testid of its own, but its Mermaid content reuses the pre-existing `chat-mermaid-diagram-svg-container` testid (hardcoded inside the shared `MermaidDiagramOutput/DiagramOutput.jsx` — same tech-debt naming already flagged by the ELITEA-2053 digest entry for chat starters; not fixed opportunistically here). Confirmed live: resolves to exactly 1 element inside the opened dialog, containing 6 `<svg>` nodes. | `PipelineDetailPage.show_context_diagram_container` added (same testid literal already used by `ChatPage.diagram_svg_container` — cross-page duplication precedent already exists for `copy-id`/`copy-version-id`/`agent-information-section` between `AgentDetailPage` and `PipelineDetailPage`). |
| Copy success toast | `PipelineDetailPage.get_toast_alert("info")` / `get_toast_text()` (testid `toast-alert` + `data-severity="info"`) | pre-existing, shared app-wide toast |

## Network Behavior
- Reading the Information section's fields fires no additional request
  beyond the page's own load (`triggerData` comes from
  `useGetPipelineTriggerQuery`, already resolved by the time the section
  renders on a fixture pipeline).
- Both Copy ID / Copy Version ID clicks are pure client-side
  `navigator.clipboard.writeText()` calls — confirmed no network request
  fires (same class as the ELITEA-2026 YAML-copy button).
- Clicking "Show" fires no network request either — `pipelineInstructions`
  (the YAML fed to the Mermaid parser) is already in the Formik form state
  from the initial page load.

## Known Defects Found During Exploration
1. **CLARIFICATION (case-text drift, not a product defect)** — the case's
   step 9 says clicking "Show" "navigates to pipeline YAML or visual
   representation." Confirmed live: the product does **not** navigate
   anywhere (no URL change) — it opens a `Dialog` modal
   (`StyledShowContextModal`, `contextLabel="Pipeline"`,
   `renderContextAsMermaid`) showing the pipeline's YAML rendered as a
   Mermaid diagram, i.e. the "visual representation" branch of the case's
   own either/or wording, via a modal rather than a page navigation. Not
   filed as a bug — the reverse-masking guard applies: asserting a literal
   "navigation" would fail on a non-defect. This AFS asserts the
   live-contract behavior (modal + diagram) instead.
2. **BUG, filed [`EliteaAI/elitea-testing-public#1368`](https://github.com/EliteaAI/elitea-testing-public/issues/1368)**
   — opening the Show-link's Mermaid preview modal deterministically (2/2,
   reproduced twice this session on two different single-node pipelines)
   throws an uncaught console `InvalidStateError: Failed to execute
   'inverse' on 'SVGMatrix': The matrix is not invertible.` from
   `svg-pan-zoom`'s `resetZoom`, called by the shared
   `MermaidDiagramOutput/DiagramOutput.jsx`'s `renderDiagram`. The diagram
   still renders visually (SVG present) — functionally non-blocking, but a
   real, deterministic console error every time. Sibling of the
   pre-existing `#1045` (same library, different call site: #1045 is the
   in-chat Mermaid **canvas editor**, this is the Information section's
   **read-only preview**) — filed separately per the dedup policy, not
   merged into #1045.

## Blocked Steps
- None. All 9 case steps were executed live and are covered above.

## Automation Hints
- Framework: Playwright/pytest, `PipelineDetailPage`
  (`automation/pages/pipeline_detail_page.py`) — reuse `copy_id_button`/
  `get_pipeline_id()`, `copy_version_id_button`/`get_version_id()`,
  `information_section`, `information_trigger_row`, `get_toast_alert()`/
  `get_toast_text()` unmodified; only `information_show_link` and
  `show_context_diagram_container` are genuinely new fields.
- **Fixture**: `pipeline_with_llm_id` — do NOT use the plain empty
  `pipeline_id` fixture (`pipeline_settings.nodes: []`, no entry point) —
  confirmed live this session that an empty pipeline with zero nodes has no
  entry point, so `useGetPipelineTriggerQuery` would have nothing to key on
  and the Trigger row (step 5) would not render at all.
- **Clipboard verification is SAFE inside the real pytest test** —
  `automation/conftest.py`'s `context` fixture already grants
  `permissions=["clipboard-read", "clipboard-write"]` (same precedent
  `test_pipeline_yaml_editor_view.py` already documents/relies on). Do
  **not** call `navigator.clipboard.readText()` from an ad-hoc/scratch
  browser session without an explicit permission grant — it hangs
  indefinitely (existing `qa-engineer` role memory,
  `clipboard_read_hangs_without_permission_grant.md`).
- **Close the Show-link modal via `Escape`** (`StyledShowContextModal`'s own
  `onKeyDown` handler) rather than adding a testid to its close button —
  the close `IconButton` has no testid either, and the case doesn't need to
  assert closing, only opening.
- Toast text for Copy ID: `"The ID has been copied to the clipboard."`;
  for Copy Version ID: `"The Version ID has been copied to the clipboard."`
  (both confirmed live, distinct wording — do not assume they're the same
  string).
