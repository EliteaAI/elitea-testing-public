# Pipelines — exploration digest

> Handle cache from live sessions against `http://localhost:5173`. Verify a handle as
> you use it — this is a cache, not a source of truth. One writer at a time; update in
> place, don't append duplicate entries. Last updated: 2026-08-02 (ELITEA-2021 analysis).

## Two distinct pipeline form surfaces — don't conflate them

- **`/pipelines/create?viewMode=owner`** — minimal create form. Renders ONLY: GENERAL
  (name `agent-name-input`, description `agent-description-input`, tags `#tags` — no
  testid), WELCOME MESSAGE (`agent-welcome-message-input`), CHAT STARTERS
  (`agent-conversation-starter-add` / `agent-conversation-starter-input`), ADVANCED
  (step limit — numeric input, no testid, default `"25"`, `min=0 max=999`). **Does NOT
  render** a Tools/toolkit-attach section, an Editor Notes section, or an Information
  section — those require the entity to already have an id.
- **`/pipelines/all/{id}?destTab=configuration&viewMode=owner`** (detail/edit page,
  reached after the first Save) — full `PipelineConfigurationForm.jsx` via
  `GeneralFormPanel`/`ConfigurationTab` (`pipeline-config-tab`): re-renders
  General/Welcome/Chat-starters/Advanced from the same shared components, PLUS
  TOOLS (`agent-toolkits-section`, "+ Toolkit" = `agent-add-toolkit-button`, "+ MCP" =
  `agent-add-mcp-button`, attached card = `agent-toolkit-card`), EDITOR NOTES
  (accordion titled "EDITOR NOTES", field labeled "Notes" — **no testid on either the
  accordion header or the textarea**), and an Information section
  (`agent-information-section`).
- **Implication for any "create pipeline with X" case**: if X is Tools/Editor-Notes/
  Information, the flow is create → Save (gets an id) → THEN fill X on the detail page
  → Save again. This is NOT documented in most TMS case texts for pipelines (confirmed
  case-text drift on ELITEA-2021) — expect it on siblings too.

## Confirmed testids (provenance-checked on `origin/main`, 2026-08-02)

All of the following are on `main` already (not just `automation/testids`):
`agent-name-input`, `agent-description-input`, `agent-save-button`,
`agent-welcome-message-input`, `agent-conversation-starter-add`,
`agent-conversation-starter-input`, `agent-toolkits-section`,
`agent-add-toolkit-button`, `agent-toolkit-card`, `toolkit-search-input`,
`toolkit-menu-item`, `agent-add-mcp-button`, `pipeline-config-tab`, `discard-button`,
`agent-canvas-section-advanced` / `-general` / `-welcome-message` / `-chat-starters`,
`agent-information-section`, `agent-actions-menu-button`, `pipeline-flow-view`,
`pipeline-yaml-view`, `pipeline-history-tab`.

Most of these already exist as `LocatorDescriptor` fields on `PipelineFormPage` /
`PipelineDetailPage` (`automation/pages/pipeline_form_page.py`,
`pipeline_detail_page.py`) — check there first. The ones NOT yet wired as page-object
fields despite the testid existing in the DOM: `agent-welcome-message-input`,
`agent-conversation-starter-add`, `agent-conversation-starter-input`,
`agent-add-toolkit-button`, `pipeline-config-tab`.

## Confirmed testid gaps (need `add-data-testid`, as of 2026-08-02)

- **Tags input** — MUI Autocomplete, `id="tags"`, placeholder `"Type a tag and press
  comma/enter"`. No testid on the input or on rendered `MuiChip` tags.
- **Step limit input** — `ApplicationAdvanceSettings.jsx`. React-generated unstable id
  (`:rXX:`-style). `input[inputmode="numeric"][max="999"]` is a usable scoped fallback
  only until fixed.
- **Editor Notes accordion header + textarea** — `ApplicationEditorNotes.jsx`. The
  `BasicAccordion` item never passes a `testId`, and `Input.StyledInputEnhancer` never
  forwards `data-testid` to the underlying textarea. Label text `"Notes"` is the only
  current handle.

## Quirks observed live

- Toolkit-picker search (`toolkit-search-input`) did not visibly filter the
  `toolkit-menu-item` listbox in a scripted probe (same 14 rows before/after typing a
  full unique toolkit name, headless). Not filed as a defect (single headless probe,
  not cross-checked manually per the interaction-discovery ladder) — but don't build a
  test around search narrowing the list; select by exact visible text among the
  unfiltered rows instead (`has_text` matching at click-time was reliable even when an
  immediate `.count()` after opening the popper under-reported — add a settle wait).
- ADVANCED section is expanded by default (`aria-expanded="true"` on load) — no click
  needed to reveal Step limit.
- The dev project has ~30 leaked `AutoTest * Toolkit *` rows from prior sessions —
  don't hardcode one of these names as "the" existing toolkit; use the `github_toolkit`
  fixture (`automation/fixtures/data_fixtures.py:243`) to provision a real one per test.
