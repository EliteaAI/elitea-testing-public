# Pipelines — exploration digest

> Handle cache from live sessions against `http://localhost:5173`. Verify a handle as
> you use it — this is a cache, not a source of truth. One writer at a time; update in
> place, don't append duplicate entries. Last updated: 2026-08-03 (ELITEA-2004/2010 analysis).

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

## HITL node — inline config panel (confirmed live, 2026-08-02, ELITEA-2014/2015)

The Human-in-the-loop node (`HITLNode.jsx`) renders its ENTIRE config always
inline/expanded on the ReactFlow canvas card — same "no click-to-open" shape as the
MCP node above. No modal, no side panel. Node wrapper carries ReactFlow's own
`data-testid="rf__node-{node_id}"` (e.g. `rf__node-HITL 1`) — confirmed present,
sanctioned third-party-widget handle per `.agents/testing.md` § Locator policy
stop+flag exception (same precedent as the MCP-node AFS).

Inside the node, in DOM order: **Input** (multi-select, tool-agnostic state vars) →
**USER MESSAGE** (Type select: Fixed/F-String/Variable; Value = textarea when
type∈{fixed,fstring}, or a select when type=variable) → **ROUTER MAPPING** accordion
(APPROVE/EDIT/REJECT, each a "Route" select listing every other node by name, END
included except for EDIT) → **EDIT STATE KEY** (a "Value" select listing pipeline
state vars, e.g. `input`/`messages`).

**Zero testids anywhere inside the node body** (only the ReactFlow wrapper and a
`node-menu-menu-button` for the node's own ⋮ menu have one) — confirmed via
`inner_html()` grep for `data-testid=`. All of Input/Type/Value/Route×3/EditStateKey
are `add-data-testid` gaps. The underlying shared components already support
threading a testid through (same pattern as the MCP node's
`pipeline-mcp-node-toolkit-select`):
- `FlowEditorSelect.InputSelect` already accepts a `dataTestId` prop → forwards as
  `data-testid` (just needs to be PASSED at the HITLNode.jsx call site — the prop
  plumbing already exists).
- `SingleSelect` (used for the Type select and the 3 Router-mapping Route selects and
  the Edit-state-key select) already accepts a `data-testid` prop → forwards to the
  trigger AND auto-derives `${data-testid}-combobox` on the `SelectDisplayProps`, and
  each option in the popper already carries `data-testid="select-option-{value}"` by
  default (no work needed there — same pattern as the MCP node's option locators).
- `BasicAccordion` already accepts a top-level `data-testid` AND a per-item `testId`
  — the Router-mapping accordion item just needs `testId: '...'` added to its `items`
  array entry.
- `SimpleLLMInputItem` (used for the USER MESSAGE Type+Value fields) has **NO** testid
  plumbing at all today (unlike the two above) — the implementer must ADD a new prop
  here. Per `.agents/testing.md` naming rule (`testId`/`<part>TestId`, never a `data`
  prefix), do NOT copy `InputSelect`'s pre-existing `dataTestId` prop name for this
  NEW prop — name it e.g. `typeSelectTestId` / `valueFieldTestId`. `InputMappingItem.jsx`
  (`inputProps={dataTestId ? { 'data-testid': dataTestId } : undefined}`) is the
  closest existing precedent for wiring the VALUE textarea's testid.
- Route-select DOM `id` attributes are **duplicated** across all 3 Router-mapping
  selects (`id="simple-select-Route"` ×3 — same `label="Route"` on each) and the
  Type/Edit-state-key selects also collide on generic ids (`simple-select-Type`,
  `simple-select-Value`) — these ids are NOT usable as locators even as a fallback;
  only positional (`nth()`) targeting works pre-testid, which is exactly why this is
  a hard `add-data-testid` requirement, not a nice-to-have.
- Chat-runtime HITL action buttons (Approve/Edit/Reject, `ChatHitlActions.jsx`, the
  non-sensitive-tool branch) ALSO carry zero testids — only the unrelated
  `sensitive_tool` guardrail branch has `sensitive-action-panel` /
  `sensitive-action-authorize-button`. Buttons are located by visible text only
  today (`BaseBtn` with no `data-testid`/`aria-label`). Needs `add-data-testid`:
  recommend `chat-hitl-approve-button` / `chat-hitl-reject-button` /
  `chat-hitl-edit-button` (from `EditControl.jsx`) + a container
  `chat-hitl-actions-panel`.

**Product behavior, live-confirmed:**
- The EDIT route select is `aria-disabled` until EDIT STATE KEY has a non-empty
  value (or an edit route is already configured) — confirmed via `aria-disabled`
  flipping from `"true"` to absent after setting EDIT STATE KEY. **Case texts that
  configure ROUTER MAPPING before EDIT STATE KEY are describing a sequence that
  doesn't work against the live UI for the EDIT route specifically** — EDIT STATE KEY
  must be set first. APPROVE/REJECT routes have no such gating.
- EDIT route options exclude `END` (can't edit-loop to a terminal node); APPROVE/
  REJECT route options include every other node plus `END`.
- Save + full page reload correctly persists APPROVE/REJECT/EDIT routes and EDIT
  STATE KEY (confirmed round-trip via UI interaction, not just an API-seeded read).
- **Runtime resume is broken — see `EliteaAI/elitea-testing-public#1103`.** Pause
  (arriving at HITL, showing the configured message + Approve/Edit/Reject buttons)
  works correctly. Clicking Approve or Reject sends the correct
  `chat_continue_predict {hitl_resume:true, hitl_action:"approve"|"reject"}` payload,
  but the backend does not resume to the configured route: Approve returns a static
  "How to proceed? To resume the pipeline - type anything..." hint with no Printer
  execution; Reject re-runs the pipeline from the entry point (`LLM 1`) instead of
  ending at END. Confirmed via live websocket capture, 2/2 fresh-conversation
  attempts. Any future HITL-runtime case will hit the same wall until #1103 ships.

## LLM node — inline config panel (confirmed live, 2026-08-03, ELITEA-2004)

Same always-expanded-inline pattern as MCP/HITL — no click-to-open, no side panel.
Node body shows, in DOM order: Trigger (read-only-ish "Chat Message" select) → SYSTEM
(Type select + Value textarea) → TASK (Type select + Value textarea) → CHAT HISTORY
(Type select + Value textarea) → Input/Output (tool-agnostic state-var selects) →
Toolkits (disabled — no toolkit attach mechanism on an LLM node) → Interrupt
before/after → Structured output.

**Zero testids anywhere inside the node body** (only `rf__node-{id}` wrapper +
`node-menu-menu-button`, same as HITL/MCP before their `add-data-testid` passes).

- **SYSTEM/TASK/CHAT HISTORY Value textareas have STABLE, unique DOM ids** —
  `#system-value` / `#task-value` / `#chat_history-value` — no positional targeting
  needed, unlike almost everything else on these node types. Good interim locators.
- **SYSTEM/TASK/CHAT HISTORY Type selects share a DUPLICATED DOM id** —
  `id="simple-select-Type"` × 3 inside one node, identical anti-pattern to the HITL
  node's 3 Router-mapping Route selects. Positional only: `.nth(0)`=SYSTEM,
  `.nth(1)`=TASK, `.nth(2)`=CHAT HISTORY (DOM-order confirmed). Options are always
  exactly `Fixed` / `F-String` / `Variable`. Default Type for all 3 sections on a
  freshly-added node is `Fixed`.
- Input/Output selects: `#simple-select-Input` / `#simple-select-Output` — stable,
  unique (only one each per node). On a fresh empty pipeline the only two options
  are `input` and `messages`.
- Save persists everything correctly; full-reload round-trip confirmed for all of
  SYSTEM/TASK/CHAT HISTORY (Type+Value) and Input/Output. Save returns `PUT
  .../application/prompt_lib/{project}/{id}` → `201`. Zero console errors, zero
  failed requests, across every run.

## Toolkit node — inline config panel, CONDITIONALLY rendered (confirmed live, 2026-08-03, ELITEA-2010)

Same always-expanded-inline pattern as MCP/HITL/LLM. Structurally very close to the
MCP node (Toolkit select → Tool select → per-tool-parameter INPUT MAPPING), but is a
**distinct node type** (`nodeType === "toolkit"`, not `"mcp"`) with its own,
currently-untestid'd DOM.

**Load-bearing precondition, not in most case texts**: the Tool select and BOTH
`INPUT MAPPING (REQUIRED N)`/`(OPTIONAL N)` accordions are **conditionally
rendered**, and their presence depends on the attached toolkit's
`settings.selected_tools`:
- A toolkit created WITHOUT `selected_tools` set (e.g. the plain
  `ToolkitAPI.create_github_toolkit()` helper / the existing `github_toolkit`
  fixture) attaches fine and shows the `Toolkit` select correctly, but the `Tool`
  select **never renders at all** (0 options, absent from the DOM, not just
  disabled) — confirmed live, reproduced twice. Not a bug: a toolkit with zero
  selected tools has zero tools to offer.
- A toolkit created WITH `selected_tools: [...]` (via `ToolkitAPI.create_toolkit()`
  with a raw `settings` dict, or `toolkit_factories.github_toolkit_settings()`)
  shows the Tool select with exactly those tools as options once a Toolkit is
  chosen. Selecting a Tool then reveals INPUT MAPPING split into REQUIRED/OPTIONAL
  accordions per the tool's actual parameter schema (e.g. `search_issues`:
  1 required `SEARCH QUERY`, 2 optional `MAX COUNT`/`REPO NAME`).
- **Any case/AFS building a Toolkit-node precondition must explicitly set
  `selected_tools` on the toolkit** — the existing `github_toolkit` fixture does
  NOT do this and cannot be reused as-is.

**Zero testids anywhere inside the node body**, same as LLM/HITL before their
`add-data-testid` passes:
- Toolkit select: `#simple-select-Toolkit` — stable, unique (one per node).
- Tool select: `#simple-select-Tool` — stable, unique, but conditionally rendered
  (see above).
- INPUT MAPPING Type selects: `id="simple-select-Type"` duplicated once per tool
  parameter (3× for `search_issues`) — same duplicate-id anti-pattern as LLM/HITL.
  Positional only, and unlike the LLM node's fixed count-of-3, **the count and
  required/optional split varies per tool** — don't hardcode `.nth()` indices
  without first counting REQUIRED vs OPTIONAL rows for the specific tool in use.
- INPUT MAPPING Value fields: **fully unstable** — React-generated `id` (e.g.
  `:r7l:`, changes between mounts), `name="value"` shared by every row, no
  distinguishing attribute. Same gap the MCP node had before ELITEA-1954's
  `add-data-testid` pass added `pipeline-mcp-node-input-mapping-value-{param}`
  (via `InputMappingItem.jsx`) — the Toolkit node needs the identical fix, likely
  the same shared component, just not yet wired for this node type's call site.
- Input/Output selects: `#simple-select-Input` / `#simple-select-Output` — same
  shape and same `input`/`messages` options as the LLM node (pipeline-wide state
  vars, not toolkit/tool-specific).

**Toolkit-attach popper timing** (attaching a toolkit to the pipeline's TOOLS
section before adding the node): the popper's toolkit list can sit on "Loading..."
for several seconds on this environment (dev project has ~30 pre-existing
toolkits) — a short fixed wait (~600ms) produced an EMPTY list in one run; an
explicit wait for `[data-testid="toolkit-menu-item"]` to appear (confirmed working
up to 15s) is required, not a fixed sleep. Same popper as the MCP node's TOOLS
attach flow (`agent-add-toolkit-button` / `toolkit-search-input` /
`toolkit-menu-item` — all confirmed working once waited for properly), reused
without change. Note: `[data-testid="toolkit-search-input"]` itself resolves to
the MUI `FormControl` wrapper `<div>`, not the `<input>` — descend one level
(`[data-testid="toolkit-search-input"] input`) or `.fill()` throws "Element is
not an <input>".

Save persists everything correctly; full-reload round-trip confirmed for
Toolkit/Tool selection AND the INPUT MAPPING Value text. Zero console errors, zero
failed requests, across every run (including the zero-`selected_tools` run, which
is a legitimate empty state, not an error state).

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
