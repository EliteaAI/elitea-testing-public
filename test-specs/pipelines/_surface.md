# Pipelines — exploration digest

> Handle cache from live sessions against `http://localhost:5173`. Verify a handle as
> you use it — this is a cache, not a source of truth. One writer at a time; update in
> place, don't append duplicate entries. Last updated: 2026-08-03 (ELITEA-2018/2030/2031/2032 analysis).

## Canvas node/edge CRUD (Add-node menu, node delete, edge create/delete) (confirmed live, 2026-08-03, ELITEA-2018/2030/2031/2032)

- **Add-node "+" menu lists exactly 11 types, in DOM order**: Agent, Code,
  Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State
  modifier, Toolkit — matches TMS case data exactly, confirmed live via
  `role="menuitem"` text dump. Zero testids on the "+" button or any menu
  item (plain MUI `MenuItem`, confirmed via `inner_html()`). Escape closes
  the menu (`role="menu"` count → 0) without adding a node.
- **No node type has a click-to-expand config panel** — every node type
  (LLM/HITL/MCP/Toolkit, and now confirmed generically via Code/Printer)
  renders its full config always inline/expanded the moment it's added.
  "Verify config panel is open" style case steps are trivially satisfied by
  the node simply existing on canvas.
- **Adding nodes via the "+" menu does NOT auto-wire any edge** — confirmed
  live: empty pipeline (`END` only, 0 edges) → add LLM → still 0 edges →
  add Code → still 0 edges. Each newly added node lands fully disconnected
  regardless of add order. Any precondition needing "N nodes connected by
  edges" must seed edges explicitly (API `transition` fields, or an
  explicit UI drag-connect step) — do not assume node-adding implies
  wiring. Filed as clarification `EliteaAI/elitea-testing-public#1137`
  against ELITEA-2018's case text, which assumed otherwise.
- **`transition` field default when OMITTED from a node dict passed to
  `PipelineAPI.create_pipeline_with_nodes()`**: a node with no explicit
  `transition` key auto-defaults to the NEXT node in the YAML `nodes:`
  list (not to END) — confirmed live: two nodes with no `transition` key
  at all produced 2 edges on first load (`node[0]→node[1]`,
  `node[1]→END`), i.e. an implicit sequential chain. **This is a
  false-positive trap for any "edge creation" test**: if you want a clean
  not-yet-connected starting state between two specific nodes, you MUST
  set `transition: "END"` explicitly on the earlier node — omitting it
  silently pre-wires the very edge you're about to test creating.
- **No "transition"/"routes" field exists in ANY non-HITL node's config
  panel** — confirmed via live DOM text read (LLM node's full visible text
  has no "Transition"/"Route" substring) AND via source
  (`LLMNode.jsx`/`PrinterNode.jsx` render no such control; the node's
  3-dot menu offers only "Make Entrypoint"/"Delete", no "Set transition").
  Only the HITL node type has a visible "Route" concept (its ROUTER
  MAPPING accordion), unrelated to LLM/Printer/Code/etc. The real,
  confirmed mechanism for wiring/re-wiring any non-HITL node's
  `transition` is dragging a canvas connection
  (`PipelineDetailPage.connect_nodes()`). Case texts describing a
  "transition/routes field in the node configuration panel" for a
  non-HITL node are stale — filed as clarification
  `EliteaAI/elitea-testing-public#1136` (covers ELITEA-2031 + ELITEA-2032,
  same root cause).
- **Edge testid format is INCONSISTENT depending on whether the target is
  the literal END node**, confirmed live in the SAME pipeline
  simultaneously: edges TO `END` render as
  `rf__edge-xy-edge__{source}---EliteAPipelineEnd` (`---` separator, no
  handle suffix — matches `PipelineDetailPage.EDGE_TESTID`); edges between
  two non-END nodes render as
  `rf__edge-xy-edge__{source}source-{target}target` (no `---`, explicit
  `source`/`target` suffixes — matches `edge_exists()`'s own docstring
  pattern instead). Use `edge_exists()` (handles both shapes via
  prefix+substring matching) rather than `edge_testid_present()`/
  `EDGE_TESTID` for any target that isn't literally END.
- **Deleting a node removes exactly that node's edges — no
  auto-reconnect.** Confirmed live: `LLM 1 → Code 1 → END`, delete
  `Code 1` → both `LLM 1→Code 1` and `Code 1→END` are gone, edge count 0,
  `LLM 1` is left with NO outgoing edge (not auto-rewired to `END`). Node
  deletion is registered as an unsaved change (Save button flips enabled)
  and persists correctly through Save + full reload.
  `PipelineDetailPage.delete_node()` (3-dot menu → Delete → confirm
  dialog) already exists and works as documented — reused unmodified,
  pre-existing raw-handle tech debt (positional `MuiIconButton-colorTertiary`
  + `get_by_role("menuitem", name="Delete")`), not newly introduced.
- **Deleting an EDGE**: click the edge (`.react-flow__edge`, gains a
  `selected` CSS class), press the `Delete` keyboard key → a
  `role="dialog"` confirmation appears ("Delete confirmation — Are you
  sure to delete the  node? It can't be restored." — **note the dialog's
  copy says "node" even for an edge deletion, a MINOR cosmetic
  discrepancy, not filed as its own ticket**) → confirm via
  `components.mui.Dialog.click_button(dialog, "Delete")`. After
  confirming: the edge is gone, and the SOURCE node's `transition`
  property does NOT become empty/absent — it resets to the literal value
  `END` (confirmed via the YAML editor view; matches
  `deletionOperations.helpers.js::clearNodePropertyAndSetEnd` in the
  source). No dedicated page-object method exists yet to CLICK a specific
  edge by source/target (only boolean existence checks) — needs a small
  `get_edge_locator(source_id, target_id) -> Locator` extending
  `edge_exists()`'s own matching logic to return the Locator instead of a
  bool (testid-based, not a new raw-handle class).

## Entry point node — Trigger control (Chat Message/Schedule/Webhook) (confirmed live, 2026-08-03, ELITEA-2005/2006/2007/2008)

Rendered by the shared, node-type-agnostic `NodeCard.jsx` base component
(`{isEntrypoint && <TriggerTypeSelector .../>}`) — appears on ANY node type set as the entry
point, always as the FIRST field inside the node body, ahead of the node-type-specific fields
(SYSTEM/TASK/CHAT HISTORY for LLM, etc.). Source: `EliteaUI/src/[fsd]/features/pipelines/
flow-editor/ui/settings/TriggerTypeSelector.jsx` + `PipelineWebhookModal.jsx` +
`PipelineScheduleModal.jsx`.

- **Trigger combobox**: `node.locator('[id^="simple-select-"]').first` — confirmed always the
  FIRST such element (the SYSTEM/TASK/CHAT HISTORY Type selects on LLM nodes also match
  `id="simple-select-Type"`, further down). **Zero testids** — same "shared `SingleSelect`
  already accepts `dataTestId`, just needs wiring at the call site" gap as the HITL/LLM/Toolkit
  node fields documented below. The 3 OPTION elements already have testids for free:
  `select-option-chat_message`/`select-option-schedule`/`select-option-webhook` (inherited from
  `SingleSelectMenuItem.jsx`'s existing auto-derivation — same mechanism as every other
  `SingleSelect` in this codebase).
- **Persistence mechanism is its OWN dedicated endpoint**, NOT the pipeline's general Save:
  `PUT ${API}/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{pipeline_id}/trigger`
  fires immediately on every trigger-type selection (including Chat Message) and on Modal Apply.
  The pipeline-level `[data-testid="agent-save-button"]` stays DISABLED after a trigger-only
  change — confirmed live, repeatedly. Any case whose text says "Save pipeline — reload" for a
  trigger change is describing a persistence mechanism that doesn't exist for this control; the
  underlying observable (survives reload) is still true via the dedicated endpoint.
- **Webhook modal timing gap (confirmed live, reproducible 3/3 runs)**: selecting "Webhook" opens
  the modal IMMEDIATELY (before its own data has loaded) — only Webhook-Type radios + description
  + Payload Format + Cancel/Apply are present at first paint. The "Webhook URL" / "Secret Value" /
  "Example Request" sections are entirely ABSENT from the DOM (not hidden) for ~1.5–4.5s while a
  secondary `GET .../trigger` populates the RTK-Query cache the modal's props read from. No
  loading indicator shown for the gap. **Automation must wait for the "Webhook URL" text/testid to
  appear, never assert the field inventory immediately after the dialog becomes visible.**
- **Schedule modal has NO such timing gap** — all fields present immediately (no secret/URL
  generation involved).
- **Schedule modal's hour/minute pickers are MULTI-SELECT checkbox grids** (third-party
  `react-js-cron` library, `.react-js-cron-select` for Every/on, a SEPARATE non-ant-select popover
  for hour/minute), not simple dropdowns — clicking a new value ADDS to the selection rather than
  replacing it. To set a single specific hour/minute: click the currently-checked cell to UNCHECK
  it FIRST, then click the target cell. Naive "just click the new value" produces a multi-valued
  cron and an inline "Frequency cannot be less than every hour" validation message. Both Default
  and Advanced mode share the same underlying `cronExpression` string state — switching modes
  loses no data either direction.
- **Restriction logic (Printer/HITL/interrupt → Chat-Message-only) is gated on the pipeline's
  LAST-SAVED YAML, not the live/unsaved canvas** — confirmed live: adding a Printer node to the
  canvas has ZERO effect on the Trigger dropdown's option set until the pipeline is Saved. Once
  Saved, the restriction applies immediately (no reload needed — re-derives from Formik `values`
  updated by the Save response) and survives reload. This precondition is NOT mentioned in any of
  the case texts that test it — a naive "add node → immediately assert restriction" sequence will
  find all 3 options still present and get a false negative.
- **Immediate post-click/post-Cancel combobox text reads can be STALE for ~1–2s** — the displayed
  value is driven by an RTK-Query GET (`useGetPipelineTriggerQuery`) that doesn't always settle
  synchronously with a mutation. Clicking "Cancel" in either modal does NOT revert the trigger
  TYPE (it was already committed by the PUT that fired on mere selection) — Cancel only discards
  in-modal-only edits (webhook sub-type / secret regen / unapplied cron). Always assert
  persistence via reload or by waiting for the specific network response, never via an immediate
  DOM read after Cancel.
- **Testid gaps, all confirmed via source read (prop plumbing already exists — zero new component
  code, just wire the prop at the call site), full list + exact recommended names in the
  ELITEA-2005/2006/2007 AFS § Concrete Handles**: Trigger combobox (`SingleSelect`'s existing
  `dataTestId` prop), Webhook-Type radio group + Schedule Mode radio group (`Checkbox.
  RadioButtonGroup`'s existing `testId` prop, auto-derives per-item), Webhook URL/Secret inputs +
  Schedule cron-text input (`FormInput`/MUI `TextField` needs `inputProps={{'data-testid':...}}`,
  NOT a bare `data-testid` prop — lands on the wrapper otherwise), modal roots + Cancel/Apply
  buttons (`Modal.BaseModal`'s existing `data-testid`/`cancelButtonTestId`/`confirmButtonTestId`
  props), copy/eye/refresh `IconButton`s (plain `data-testid`, no existing prop needed).
- **Minor prop-drop, not filed as a defect**: `PipelineScheduleModal.jsx` passes `label="Schedule
  Type"` to `Checkbox.RadioButtonGroup`, which does not consume/render a `label` prop at all — the
  Mode radio group has no visible heading. Locate by the two option labels ("Default"/"Advanced")
  instead.

## YAML editor ⇄ Flow canvas sync (confirmed live, 2026-08-03, ELITEA-2028)

- **`yaml_view_button`/`flow_view_button`/`yaml_editor` testids all work as
  documented** (`pipeline-yaml-view`, `pipeline-flow-view`,
  `pipeline-yaml-editor`). Editing a node's `transition:` value in the YAML
  editor and switching back to Flow view correctly re-renders the ReactFlow
  edge in place (confirmed: the SAME edge DOM node's `data-testid` changes
  from `rf__edge-xy-edge__LLM 1---EliteAPipelineEnd` to
  `rf__edge-xy-edge__LLM 1---Code 1` after editing `transition: END` →
  `transition: Code 1`) — no defect, matches product intent.
- **`yaml_lines` (testid `pipeline-yaml-lines`) resolves to 0 matches in this
  environment** — the real CodeMirror `.cm-line` divs carry no such testid.
  `get_yaml_content()`'s existing fallback (`yaml_editor.text_content()`)
  handles this gracefully already, but returns a newline-stripped
  concatenated blob — fine for substring assertions, not for line-indexed
  reads.
- **No page-object method edits YAML content** — only reads it
  (`get_yaml_content()`). For per-line edits, the sanctioned pattern is the
  same #579 exception already used for `McpFormPage.fill_raw_json_line()`
  (CodeMirror internal per-line divs, no testid possible): click the line via
  `yaml_editor.get_by_text(current_text, exact=True)`, `Home`/`Shift+End` to
  select, then `keyboard.type()` the replacement. Confirmed working live for
  the pipeline YAML editor, same mechanics as the MCP Raw Json editor.
  `.first` on `get_by_text()` resolves by DOM/document order — fine when the
  target line is uniquely positioned (e.g. entry-point node listed first),
  NOT safe when multiple nodes share identical transition text in
  unpredictable order.
- **`edge_exists(source, "END")` is unreliable — pre-existing page-object
  gap** (`automation/pages/pipeline_detail_page.py:1557`, not caused by this
  session). The real ReactFlow edge testid pattern is
  `rf__edge-xy-edge__{source_id}---{target_id}`, and END's real `target_id`
  is the literal string `EliteAPipelineEnd`, not `"END"` — the method's own
  docstring example (`...LLM 1source-ENDtarget`) doesn't match live DOM at
  all (no `source`/`target` suffixes, `---` separator instead of a bare
  concatenation). `edge_exists(source, "END")` therefore always returns
  `False` even when that edge is visibly present. Non-END targets (e.g.
  `edge_exists("LLM 1", "Code 1")`) DO work correctly — the target-id
  substring check just happens to be right for anything that isn't END.
  Flag for a dedicated fix; out of scope for any case that doesn't touch it.
- **Seeding gotcha — dirty-state baseline depends on HOW the pipeline was
  seeded.** A pipeline created via `PipelineAPI.create_pipeline_with_llm_node()`
  (single node, matches `pipeline_with_llm_id` fixture) loads with Save/Discard
  correctly **disabled** (clean baseline) — confirmed 2× (fresh load + reload).
  A pipeline created via `PipelineAPI.create_pipeline_with_nodes()` with a
  hand-built **multi-node** list loads with Save/Discard **already enabled**
  on first render, zero edits made — because `pipeline_settings.nodes`/`edges`
  is left empty by that helper (no saved canvas layout), so the frontend's
  auto-layout-on-first-render is itself treated as an unsaved change. Any case
  whose assertion depends on a disabled→enabled transition (e.g. "Save becomes
  enabled after X") MUST seed via a single-node API call + UI-driven
  node-add + Save + reload, never via a raw multi-node
  `create_pipeline_with_nodes()` call, or the assertion passes trivially for
  the wrong reason.

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
