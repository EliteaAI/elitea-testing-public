# Pipelines — exploration digest

> Handle cache from live sessions against `http://localhost:5173`. Verify a handle as
> you use it — this is a cache, not a source of truth. One writer at a time; update in
> place, don't append duplicate entries. Last updated: 2026-08-07 (ELITEA-2020 combined
> analysis/implementation).

## Sidebar "+" create control and the VERSION selector (confirmed live, 2026-08-07, ELITEA-2020)

- **`sidebar-create-button`** (the shared `CreateEntityButton.jsx`, same
  testid already wired on `AgentsListPage`/`ToolkitsListPage`/
  `CredentialsListPage`/`ChatPage`) is exactly the "+" control next to the
  "Pipeline" label the case describes — confirmed live: while on
  `/pipelines/all`, the button's `currentLabel` resolves to "Pipeline" (per
  `RouteToLabelMap`) and clicking it navigates straight to
  `/pipelines/create?viewMode=owner` (no dropdown, per
  `isSimpleCreateRoute`). Not yet a `PipelinesListPage` field — added this
  session (`sidebar_create_button` + `click_create_pipeline()`).
- **VERSION selector on the pipeline detail page**: `data-testid` is
  threaded via a `testId` PROP (`ApplicationVersionSelect.jsx:228`,
  `testId="agent-version-selector-trigger"`), NOT a literal `data-testid=`
  string — a bare-substring `git grep` for `data-testid.*agent-version-
  selector` finds nothing; grep for the prop name
  (`testId="agent-version-selector-trigger"`) instead, same caveat as the
  MCP-node testids and the closure-record two-stage-grep note.
  **CORRECTION (2026-08-07, review fix round 1):** the prior claim on this
  line — "renders TWO testids, `agent-version-selector-trigger` (outer
  wrapper) + `agent-version-selector-trigger-combobox` (inner combobox)" —
  was **fabricated**; a repo-wide `git grep` for the literal string
  `agent-version-selector-trigger-combobox` returns **zero hits** on both
  `main` and `automation/testids`. Source trace: `VersionSelect.jsx:176`
  applies the prop as a SINGLE `data-testid={testId}` on the `SingleSelect`
  root (that root already carries `role="combobox"` itself — same element,
  not two; `SingleSelect.jsx` has no `-combobox`-suffix derivation anywhere).
  Only `agent-version-selector-trigger` exists — confirmed on `main` — no
  `add-data-testid` needed. Shared component — same one Agents' detail page
  uses via `AgentDetailPage.version_selector_trigger` (`_surface.md` doesn't
  need a duplicate Agents entry; behavior is identical).
- **Name field has a hard 32-char cap (`MAX_NAME_LENGTH`,
  `src/common/constants.js`), and typing beyond it silently truncates
  rather than erroring** — confirmed live: `pressSequentially`/`type()` of a
  41-char name left the field holding exactly the first 32 chars, no
  validation message. Same root cause as the `pipeline_id` fixture's own
  `[:32]` truncation noted in the ELITEA-2023 AFS, but this one bites ANY
  manually-generated name, not just the fixture. Keep generated pipeline
  names ≤32 chars total (e.g. `autotest_pipe_min_<8hex>` = 27 chars) —
  don't assume a longer descriptive prefix + suffix is safe.
- **Information section confirmed reachable without an explicit expand
  click** — `agent-information-section`'s accordion renders
  `Mui-expanded`/open by default on a freshly created pipeline's detail page
  (same as the ADVANCED section note elsewhere in this digest). "Pipeline
  ID:" sits next to the pre-existing `copy-id` button
  (`PipelineDetailPage.copy_id_button`/`get_pipeline_id()`, unmodified,
  confirmed still correct); a sibling "Version ID:" / `copy-version-id`-style
  button also exists in the same section (not needed by ELITEA-2020, noted
  for any future case that touches Version ID specifically).

## Dashboard search — typing alone does NOT filter the grid; Enter/send-icon required (confirmed live, 2026-08-07, ELITEA-2023)

- **`PipelinesListPage.search()` (as merged) never actually filters the
  dashboard grid.** It only does `search_input.fill(query)` — no Enter, no
  send-icon click. Per `SearchBar.jsx` (shared by Pipelines/Agents/MCP/
  Credentials/Toolkits/Skills): typing only updates local state + opens a
  real, API-backed **suggestions popover** (`SuggestionList.jsx`, 500ms
  debounce); the grid-narrowing dispatch (`onSearch()`) fires ONLY on
  `Enter` or a click on `data-testid="search-send-button"`. Confirmed live:
  typed "YAML" + waited past debounce → grid unchanged (still 11 pipelines);
  pressed Enter → grid narrowed to exactly 1 (`autotest_YAML_search_probe`).
  This means `test_search_pipeline_by_name`/`test_search_pipeline_no_results`
  (merged, `test_pipeline_management.py::TestSearchPipeline`) pass via the
  suggestions popover, not the grid filter — real grid-filter coverage is
  new (see `lextend_pipeline-dashboard-search-filter-and-clear_ELITEA-2023.md`).
  Sibling pages already fixed this correctly — reuse their pattern:
  `automation/pages/mcp_list_page.py::search()` (types, `press("Enter")`,
  waits network + ~1.5s settle) / `credentials_list_page.py`.
- **`search-clear-button` testid exists but has no `PipelinesListPage` field
  yet** — confirmed live (`page.getByTestId('search-clear-button')`
  resolves). Add `search_clear_button = LocatorDescriptor(testid="search-clear-button")`.
- **No sibling of the MCP/#585 · Credentials/#551 "clear-from-zero-match
  redirects to /create" defect on Pipelines** — reproduced the identical
  trigger (search a term with zero matches → empty state → click Clear) and
  the Pipelines dashboard correctly restores the full grid, stays on
  `/pipelines/all`. Confirmed clean; don't assume it needs fixing too.
- **Search-input placeholder**: exactly `Let's find something amazing!`
  (confirmed via live accessibility snapshot, matches `SearchBar.jsx`
  literal and the merged `search_input` LocatorDescriptor's dead `fallback=`
  string — testid `pipeline-search-input` is what actually resolves).
- **Case-text drift filed**: `EliteaAI/elitea-testing-public#1302` —
  ELITEA-2023 Steps 3–4 imply live-as-you-type filtering; live product
  needs explicit Enter/send-icon activation (same `SearchBar.jsx` mechanism
  as ELITEA-2162's `#1114` clarification for the Chats search folder-list
  behavior — recurring pattern across every dashboard using this component).

## YAML editor view — line numbers, copy button, `state:` key precondition (confirmed live, 2026-08-07, ELITEA-2026)

- **`state:` key requires a CUSTOM state variable — `input`/`messages` alone
  never produce it.** Confirmed both directions: a plain
  `pipeline_with_llm_id`-shaped pipeline's Yaml view shows ONLY
  `entry_point:`/`nodes:` (zero `state:` key, verified via
  `[data-testid="pipeline-yaml-editor"].textContent`); the identical shape
  plus an explicit `state:` block in `PipelineAPI.create_pipeline()`'s
  `instructions` param round-trips a `state:` section correctly. Filed as a
  clarification (case-text drift, not a defect):
  `EliteaAI/elitea-testing-public#1299` — any case whose Test Data implies
  "any pipeline with nodes" guarantees a `state:` keyword must instead seed
  a custom state var explicitly (same `instructions`-param technique
  ELITEA-2453's fixture uses).
- **Line-number gutter has ZERO testid, but IS a sanctioned #579 exception**
  — confirmed live via `document.querySelector('.cm-gutters')` →
  `data-testid: null`, AND confirmed the gutter is a DOM descendant of the
  `pipeline-yaml-editor` testid parent (`editorTestidEl.contains(gutter)` →
  `true`). Scoped raw handle: `.cm-gutters .cm-lineNumbers .cm-gutterElement`
  chained off `yaml_editor`, same precedent/shape as the existing
  `YAML_LINE_SELECTOR = ".cm-line"` class constant — add a sibling constant
  rather than a new page-object field.
- **"Copy yaml code to clipboard" button has NO testid** — only
  `aria-label="Copy yaml code to clipboard"` (confirmed via a full
  `document.querySelectorAll('button')` grep). Genuine `add-data-testid` gap,
  not previously flagged by another case. Recommend `pipeline-yaml-copy-button`.
- **Copy click produces the SAME shared `toast-alert` component every other
  page already uses** (`data-testid="toast-alert"`, `data-severity="info"`,
  text `"The code has been copied to the clipboard."`) — `PipelineDetailPage.
  get_toast_alert("info")` / `get_toast_text()` already exist and work
  unmodified, no new plumbing needed. Toast auto-dismisses fast (~1-2s
  observed) — wait for it immediately after the click, not a step later.
- **`navigator.clipboard.readText()` unprivileged HANGS INDEFINITELY, no
  error, no timeout** — confirmed live (ad-hoc MCP scratch session, no
  `context` fixture): a bare `page.evaluate(() =>
  navigator.clipboard.readText())` silently stalled the calling tool for the
  full idle timeout; the browser page itself stayed fully responsive
  throughout (confirmed via a snapshot immediately after recovery) — this is
  a permission-prompt stall, not a crash. **BUT the real pytest `context`
  fixture (`automation/conftest.py:281`) already grants
  `permissions=["clipboard-read", "clipboard-write"]` suite-wide** — so
  inside an actual test this call is safe and resolves immediately (see
  role memory `clipboard_read_hangs_without_permission_grant.md`, from
  ELITEA-2280). Only ad-hoc/scratch sessions need the explicit
  `context.grant_permissions(...)` workaround.
- **Toggling Flow⇄Yaml and clicking Copy are both pure client-side
  operations** — zero network requests for either, confirmed via
  `browser_network_requests` across both probe pipelines. Zero console
  errors/warnings throughout.

## Run Details panel (`RunStateNode`/`RunStateDialog`) — opened after pipeline execution (confirmed live, 2026-08-06, ELITEA-2450)

- **The click target is NOT "in chat history"** — a case-text trap (filed
  `EliteaAI/elitea-testing-public#1268`). Executing a pipeline via the
  embedded chat renders a separate `RunStateNode` element **above the Flow
  canvas** (next to the Flow/Yaml toggle and "Add node" button —
  `RunStateNodeGroup.jsx` → `RunStateNode.jsx`), showing a status icon +
  `"Run N details"` label + a delete icon. The embedded chat's own message
  list only ever contains the user message + AI response — confirmed live
  via full-page snapshot, zero run-related content there.
- **Accessible name ≠ visible text, same trap class as
  `pipeline-state-add-variable-button`**: the run label's Playwright
  accessible name is the Tooltip text `"View details"`, NOT the rendered
  `"Run N details"` text a human reads. Never `get_by_role("button", {name:
  ...})` here.
- **Data source is Socket.IO only — no REST endpoint backs the panel.**
  Confirmed via `browser_network_requests`: execute→open-panel produces only
  `socket.io/?EIO=4…` polling exchanges, no dedicated GET for
  run/timeline/state. `useRunEvent.hooks.js` derives everything client-side
  from socket events, held in `FlowEditor` local state, threaded down as
  `data`/`yamlJsonObject.state` props. Tests must wait on the DOM (the
  existing `wait_for_embedded_chat_response()` helper), never poll an
  endpoint for "run complete."
- **Panel header composition (confirmed live, exact structure)**: `"Run N
  details"` title, a `"Completed"`/etc. status badge (text content IS the
  status — use a `data-status` attribute for state, per the testid=stable-
  identity ruling, not a per-status testid), a Delete-or-Stop icon
  (same-element conditional pair, canon ruling #277 — only one branch mounts
  based on `data.status`), and a Close icon (`CollapseIcon` — visually a
  "compress" glyph). **There is no separate expand/fullscreen toggle in the
  header** (case-text drift, filed in the same `#1268` clarification as the
  chat-history trap above) — the dialog is already sized responsively (90%
  of the editor viewport) on open. A genuine `FullscreenOutlinedIcon` DOES
  exist, but scoped per-STATES-row (`StateItemViewHeader`'s Before/After
  expand icons), not in the panel header.
- **Body composition (fix round 2, ELITEA-2450: corrected from a stale
  ALL-CAPS paraphrase presented as confirmed-live fact — source-verified
  against `RunStateDialog.jsx:277`/`:452`, both sentence case)**: a
  `"Timeline step:"` label immediately followed by the node id with no
  separator (renders e.g. `Timeline step:LLM1`) + a `Stepper` (one filled
  circle + `HH:mm:ss` timestamp per timeline entry — one entry for a
  single-node pipeline), then a `"States"` section header with one
  accordion row per pipeline state variable (`input`/`messages` for a
  plain `pipeline_with_llm_id` pipeline), each expandable to Before/After
  value boxes with their own per-value expand (fullscreen) icons.
- **Testid gap — the ENTIRE feature has zero testids.** Confirmed via
  `grep -rn "data-testid"` across `RunStateNode.jsx`, `RunStateNodeGroup.jsx`,
  `RunStateDialog.jsx` — no hits at all. 8 testids needed for
  ELITEA-2450's own scope (run-node label, panel root, header, status badge,
  delete button, close button, timeline section, states section); finer
  per-timeline-step and per-state-variable testids are sibling cases'
  concern (ELITEA-2451/2452/2453/2454, tracked as `#959`/`#960`/`#961`/`#962`).
- **Known product defect (MINOR, filed `#1267`, sibling of `#611`)**: opening
  the panel logs one React console warning — the Timeline Stepper's
  `ProcessConnector` wrapper spreads unfiltered MUI-injected boolean props
  (`{...rest}`, likely `last`/`active`/`completed`) onto a raw DOM `<div>`.
  Cosmetic only — panel renders and functions correctly. Don't assert a
  blanket "zero console errors" through the panel-open step for this flow;
  scope around this one known signature.

## LLM/HITL node Type+Value field — `Variable` Type swaps the Value field's WIDGET, not just its behaviour (confirmed live, 2026-08-04, ELITEA-2040)

- **`SimpleLLMInputItem.jsx`** (shared across LLM node's SYSTEM/TASK/CHAT HISTORY and HITL's
  `user_message`) renders the Value field as ONE of two entirely different components depending
  on `type`: `type ∈ {fixed, fstring}` → a free-text `<textarea>` (`NodeFieldInput`, testid'd via
  the `valueFieldTestId` prop, e.g. `pipeline-llm-node-system-value`); `type === variable` → a MUI
  `Select` (`id="simple-select-Value"`, `role="combobox"`) whose options are the pipeline's own
  state variables (`input`/`messages` — same `select-option-{value}` mechanism as the node's
  `Input`/`Output` selects). Confirmed live via direct DOM `tagName`/`outerHTML` reads before/after
  switching Type.
- **The Select branch is MISSING its `data-testid` entirely** — the component already receives
  `valueFieldTestId` and correctly threads it to the textarea branch's `NodeFieldInput`, but the
  `else` branch's `<SingleSelect label="Value" ... />` never receives `data-testid={valueFieldTestId}`.
  One-line `add-data-testid` fix, reusing the SAME testid name (no new name, no call-site change)
  — same underlying gap likely affects HITL's `user_message` field and any future call site of this
  shared component, though only the LLM node's SYSTEM section was fixed/verified for ELITEA-2040.
- **Value is CLEARED on any Type transition involving `Variable`, but PRESERVED across Fixed↔F-String**
  — confirmed live both directions (F-String→Variable cleared the text; Variable→Fixed left the
  textarea empty, not the pre-Variable text) and via source
  (`SimpleLLMInputItem.jsx`'s `onChange`: `shouldPreserveValue = (fstring→fixed) || (fixed→fstring)`,
  else clears to `defaultValue`). Any test walking through multiple Types on one field must
  re-enter the Value after every Type change that touches `Variable` — do not assume the prior
  text survives.
- **Type select's 3 options are exactly `Fixed`/`F-String`/`Variable`**, testid'd
  `select-option-fixed`/`select-option-fstring`/`select-option-variable` (same
  `select-option-{value}` mechanism as everywhere else) — confirmed live, matches
  `TYPE_OPTION_VALUE_BY_LABEL` already in `pipeline_detail_page.py`.

## Canvas node/edge CRUD (Add-node menu, node delete, edge create/delete) (confirmed live, 2026-08-03, ELITEA-2018/2030/2031/2032)

- **Add-node "+" menu lists exactly 11 types, in DOM order**: Agent, Code,
  Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State
  modifier, Toolkit — matches TMS case data exactly, confirmed live via
  `role="menuitem"` text dump.
  **CORRECTION (2026-08-04, ELITEA-2037 analysis): "zero testids on the '+'
  button or any menu item" is now STALE — testids have since been added.**
  `[data-testid="pipeline-add-node-button"]` (the "+" trigger) and
  `[data-testid="pipeline-add-node-menu-item-{type}"]` (one per menu item,
  lowercase type, e.g. `pipeline-add-node-menu-item-mcp`) both confirmed
  working live this session (`AddNodeMenu.jsx`). Provenance: on
  `automation/testids` only, absent from `main` (fresh `git fetch` +
  `git grep`, 2026-08-04) — not yet promoted. Escape closes
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
- **No "transition"/"routes" field exists in LLM/Printer/Code/etc's config
  panel** — confirmed via live DOM text read (LLM node's full visible text
  has no "Transition"/"Route" substring) AND via source
  (`LLMNode.jsx`/`PrinterNode.jsx` render no such control; the node's
  3-dot menu offers only "Make Entrypoint"/"Delete", no "Set transition").
  The real, confirmed mechanism for wiring/re-wiring any of THESE node
  types' `transition` is dragging a canvas connection
  (`PipelineDetailPage.connect_nodes()`). Case texts describing a
  "transition/routes field in the node configuration panel" for one of
  these types are stale — filed as clarification
  `EliteaAI/elitea-testing-public#1136` (covers ELITEA-2031 + ELITEA-2032,
  same root cause).
  **CORRECTION (2026-08-04, ELITEA-2033 analysis) — the prior version of
  this entry over-generalized to "only HITL has a Route concept": that is
  FALSE. The dedicated Router node type ALSO has a first-class `Routes`
  field** (a multi-select of existing node ids/`END`, distinct from HITL's
  named APPROVE/EDIT/REJECT routes) **plus a `Default output` field that
  wires its own separate edge.** Router routes/default-output edges use
  the SAME `EDGE_PREFIX` id-construction mechanism (`xy-edge__{id}---{value}`
  for routes, `xy-edge__{id}default_output---{value}` for the default
  output — no separator before `default_output`, a HITL-style gotcha) so
  `edge_testid_present()`/`get_edge_locator()` work unmodified once the
  right string is passed. Full details: `l2_pipeline-router-node-configuration_ELITEA-2033.md`.
  The "no transition/routes field" claim stands ONLY for LLM/Printer/Code/
  MCP/Toolkit/State-modifier/Custom/Agent — i.e. every type except HITL and
  Router.
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

## MCP node — inline config panel, CONDITIONALLY rendered (confirmed live, 2026-08-04, ELITEA-2037)

Same always-expanded-inline pattern as every other node type. Shares the SAME
base component (`BaseToolNode.jsx`) as the Toolkit node (ELITEA-2010, below) —
`nodeType === "mcp"`, `TEST_ID_PREFIX_BY_NODE_TYPE['mcp'] = 'pipeline-mcp-node'`.
Most testids were added earlier (ELITEA-1954/1955's `add-data-testid` passes)
and are already wired as `PipelineDetailPage` fields — reuse directly, don't
re-derive.

- **Static fields present immediately on a freshly-added, unconfigured node**:
  Trigger (only if this node is the entry point), **Toolkit** select (empty),
  **Input** (multi-select, `role="listbox" aria-multiselectable="true"`,
  tool-agnostic state var), **Output** (same), **Interrupt before** (switch,
  dynamic testid `pipeline-node-interrupt-before-toggle-{node_id}`,
  unconditional across ALL node types — `disabled` when this node IS the
  entry point), **Interrupt after** (switch — `disabled` when the node's
  `transition` is `END`), **Structured output** (switch, enabled by default,
  MCP passes `showStructuredOutput` unconditionally unlike the generic
  Function-node default).
- **Tool select and BOTH INPUT MAPPING (REQUIRED N)/(OPTIONAL N) accordions
  are CONDITIONALLY rendered — absent from the DOM (not hidden) until a
  Toolkit with ≥1 tool is selected.** Same conditional-rendering contract as
  the Toolkit node below — a case-text step listing "Toolkit, Tool, Input,
  Output, INPUT MAPPING, Interrupt before/after, Structured output" as all
  simultaneously present on a fresh node is describing 2 UI states, not 1;
  split the assertion across "before Toolkit select" and "after Tool select".
- **Testid gap (4 elements), confirmed via BOTH source read
  (`BaseToolNode.jsx` lines ~206-238) AND live DOM this session — the prop
  plumbing already exists generically (shared with the Toolkit node, which
  DOES get these wired), it's a Toolkit-nodeType-only conditional today:**
  1. **"Interrupt after" toggle** — `interruptAfterTestId` prop passed
     `undefined` for `nodeType === Mcp`. No testid anywhere on this switch
     (confirmed live: `data-testid` attribute absent). Recommend
     `pipeline-mcp-node-interrupt-after-toggle`.
  2. **"Structured output" toggle** — same gap, `structuredOutputTestId`.
     Recommend `pipeline-mcp-node-structured-output-toggle`.
  3. **Input-mapping row "Type" select** — `typeTestIdPrefix` prop, MCP
     passes `undefined`. Only reachable via the duplicated, non-unique
     `id="simple-select-Type"` (positional `.nth()` only, same anti-pattern
     as LLM/HITL). Recommend `pipeline-mcp-node-input-mapping-type-{param}`
     (dynamic, mirrors the Value field's existing naming).
  4. **Input-mapping "optional N" accordion heading** — `optionalHeadingTestId`
     prop, MCP passes `undefined`. Recommend
     `pipeline-mcp-node-input-mapping-optional-heading`. Not live-exercisable
     without a tool that has optional params (`ask_question`, this session's
     test data, has 0 optional) — confirmed via source read only.
  All 4 are 1-line fixes mirroring the Toolkit node's own call site
  (`BaseToolNode.jsx` lines 208-241) — widen the existing
  `nodeType === Toolkit ? ... : undefined` ternaries to also cover
  `nodeType === Mcp`, or give MCP its own parallel testid.
- **Already-working, reused-from-ELITEA-1954/1955 testids** (all on
  `automation/testids` only, confirmed via `git grep` this session — NOT yet
  on `main`): `pipeline-mcp-node-toolkit-select` (+ `-combobox` variant),
  `pipeline-mcp-node-tool-select` (+ `-combobox`), `pipeline-mcp-node-input-select`
  (+ `-combobox`), `pipeline-mcp-node-output-select` (+ `-combobox`),
  `pipeline-mcp-node-input-mapping-heading`,
  `pipeline-mcp-node-input-mapping-value-{param}` (class constant
  `MCP_NODE_INPUT_MAPPING_VALUE` on `PipelineDetailPage`). **All are
  constructed at runtime via string-template concatenation
  (`` `${testIdPrefix}-toolkit-select` ``) — a literal bare-substring `git grep`
  for the FULL testid string finds nothing; verify provenance via the
  constituent prefix (`pipeline-mcp-node`) and the
  `TEST_ID_PREFIX_BY_NODE_TYPE` mechanism instead**, same caveat as
  `.agents/workflow.md`'s closure-record two-stage-grep note for prop
  indirection.
- **CORRECTED (2026-08-04, ELITEA-2037 fix round 2): pipeline-level "+MCP"
  attach (`agent-add-mcp-button`, Tools section) DOES auto-persist** — like
  the AGENT-level Tools section (`EliteaAI/elitea-testing-public#530`),
  selecting the MCP in the popper fires an immediate `PATCH
  .../elitea_core/tool/prompt_lib/{project_id}/` → `201 Created`, the SAME
  auto-persist mechanism as agents, not a pipeline-specific difference. `GET
  .../toolkits/…` / `GET .../tools/…?mcp=true` (listing calls that populate
  the popup) also fire, but are not the whole story. Re-verified live via 2
  foreground pytest runs of the case's own spec
  (`test_pipeline_mcp_node_fresh_attach.py::test_mcp_node_fresh_attach`, both
  green) — `PipelineDetailPage.select_mcp_in_popper()` (pre-existing, reused
  from ELITEA-1955) hard-blocks on `page.expect_response(... method ==
  "PATCH" and status == 201 ...)` before returning, so a passing run is
  itself proof the PATCH fired; corroborated by the already-merged
  ELITEA-1955 sibling test using the identical wait in the identical
  context. The pipeline's own Save (`PUT
  .../application/prompt_lib/{project}/{pipeline_id}` → `201`) still ALSO
  re-persists the Tools-section attachment as part of the whole
  node/pipeline payload — both true: attach fires its own immediate PATCH,
  AND Save's PUT re-persists the same state. Filed as a sibling
  clarification (unaffected by this correction — it only covered the
  missing MCP sub-tab, not persistence timing):
  `EliteaAI/elitea-testing-public#1149` (of `#530`); #1149 carries a
  follow-up comment correcting the network claim its body originally
  repeated. ~~Original (incorrect) claim, kept for audit trail: "does NOT
  auto-persist — unlike the AGENT-level Tools section (#530), no request
  fires on MCP-attach selection (only GET .../toolkits/… /
  GET .../tools/…?mcp=true listing calls). The attachment is persisted
  together with the rest of the node config by the pipeline's own Save."~~
  See `l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md` § Network
  Behavior for the full re-verification detail.
- **No "MCP sub-tab" exists** — the Toolkit/MCP/Agent/Pipeline buttons in the
  Tools section are 4 independent ADD triggers (poppers), not view-filter
  tabs. Every attached item, whatever its type, renders in ONE flat list
  sharing the single testid `agent-toolkit-card` (confirmed:
  `document.querySelectorAll('[data-testid="agent-toolkit-card"]')` → 1 after
  attaching 1 MCP). Same root cause/pattern as `#530`, different entity
  (pipeline Tools vs agent Tools) — same shared `ApplicationTools.jsx`/
  `ToolMenu.jsx` component.
  Full detail: `l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`.

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

## Router node — Condition/Routes/Input/Default output (confirmed live, 2026-08-04, ELITEA-2033)

- **Router has its own first-class `Routes` field** (distinct from HITL's
  named APPROVE/EDIT/REJECT routes) — a multi-select `RouteSelect`
  component whose options are **existing pipeline node ids + a synthetic
  `END` option**, NOT a freeform/creatable tag field. To route to targets
  named e.g. "approve"/"reject" (a Jinja condition's literal string
  outputs), those nodes must already exist with exactly those names —
  achieved live via the canvas inline node-rename (`edit_node_name()`),
  not via typing into the Routes field itself.
- **Selecting a Routes value wires a real canvas edge immediately, before
  Save** — confirmed live (`Router 1 → approve` edge appeared in the
  snapshot the instant "approve" was clicked in the dropdown, well before
  any Save click). Same is true of `Default output`.
- **`Default output` is a separate field/edge from `Routes`**, defaulting
  to `END` with its own dedicated ReactFlow source handle
  (`routerNode_default_output` vs `routerNode_routes`). Selecting it wires
  a THIRD edge distinct from the two routes edges.
- **Edge testid construction differs between Routes and Default-output
  edges** (both app-constructed via `FlowEditorConstants.EDGE_PREFIX =
  'xy-edge__'`, confirmed in `RouteSelect.jsx`/`RouterNode.jsx` source and
  live DOM):
  - Routes edge: `rf__edge-xy-edge__{router_id}---{target}` — matches the
    plain `EDGE_TESTID` template `PipelineDetailPage` already has; works
    unmodified with `edge_testid_present()`/`get_edge_locator()`.
  - Default-output edge: `rf__edge-xy-edge__{router_id}default_output---{target}`
    — **no separator between the router's id and the literal
    `default_output`** (same no-separator-concatenation gotcha as HITL's
    `HITL 1reject-ENDtarget`). Still usable with the existing
    `EDGE_TESTID`/`get_edge_locator()` machinery by passing the
    pre-concatenated string as the "source" arg
    (`get_edge_locator(f"{node_id}default_output", "END")`) — no new
    page-object method needed.
- **`Condition` is a plain MUI `TextField` (`<textarea>`), NOT a
  CodeMirror/Monaco editor**, despite `AIAssistantInput` receiving
  `language="jinja"` — that prop only affects the "AI Assistant" full-screen
  modal's syntax highlighting, not the inline field. Standard
  `.input_value()`-readable, no #579 CodeMirror-line-scoping needed.
- **Zero testids on any of the 4 interactive Router fields** (Condition,
  Routes, Input, Default output) as of this session. `Input` and `Default
  output`'s underlying shared components already accept a `dataTestId`/
  `data-testid` prop (one-line RouterNode.jsx wiring each); `Condition`
  needs an `inputProps={{'data-testid': ...}}` addition (same pattern as
  HITL's USER MESSAGE Value field); `Routes`'s `RouteSelect.jsx` has NO
  testid plumbing at all yet (needs a new prop, 2-line fix). Full detail +
  exact testid names: `l2_pipeline-router-node-configuration_ELITEA-2033.md`.
- **`PipelineDetailPage.edit_node_name()`'s docstring is stale/wrong**: it
  claims a rename retains the node-type prefix ("LLM 1" → "MyNode" becomes
  data-id "LLM MyNode"). Live-confirmed FALSE — renaming "Printer 1" to
  "approve" produces data-id exactly `approve`, no prefix. Also: pressing
  `Enter` after typing does NOT commit the rename; only clicking the canvas
  empty pane (`.react-flow__pane`, a real blur) commits it — the existing
  method already does this correctly via `_deselect_all()`, only the
  docstring's claimed resulting id is wrong. Needs a doc fix (not a
  behavior fix) at `pipeline_detail_page.py:1765-1767`.
- **Session/environment gotcha, not a product defect**: a localhost
  session's browser-active project (sidebar "Project:" selector) can
  differ from `.env.test`'s `ELITEA_PROJECT_ID` — this session's browser
  defaulted to "Elitea Testing Team" (id 471) while `.env.test` says `399`
  ("Private"). Creating a pipeline via a standalone `PipelineAPI` script
  using the default project id then opening it in that mismatched browser
  session produces a 400 (wrong project in the URL) or, if you also try to
  create directly against the mismatched project, a 403
  `access_denied`/`models.applications.applications.create` (the dev-token
  user lacks create rights on "Elitea Testing Team"). Fixtures using
  `browser_cookies`-based auth (the normal test pattern) don't hit this —
  they inherit whatever project is actually active. Only bites standalone
  token-auth scripts run outside a browser session (exactly what happened
  during this analysis). Fix: switch the sidebar project selector to
  "Private" (`select-option-399`) before creating pipelines by hand, or
  read the sidebar's active project id before scripting against the API.

## Decision node — config, DECISION OUTPUTS, edge-testid instability (confirmed live, 2026-08-04, ELITEA-2034)

- **Decision node's config is inline (same generic pattern as every other
  node type)**: `Input` multi-select, `Description` (plain multiline
  `AIAssistantInput`/`TextField`, NOT CodeMirror — same as Router's
  Condition field), `Decision outputs` (an initially-empty chip container,
  no typeable input inside it at all), `Interrupt before`/`Interrupt after`
  switches. Two source handles at all times: `Output` (`data-handleid="nodes"`)
  and `Default output` (`data-handleid="default_output"`) — case text for
  ELITEA-2034 matches the live UI's handle labels exactly (unlike its
  DECISION OUTPUTS wording, below).
- **DECISION OUTPUTS chips are added ONLY by drag-connecting a canvas edge
  from the `Output` handle to an existing, correctly-named target node** —
  confirmed via source (`DecisionNodeShared.jsx`'s `DecisionOutputs` renders
  zero interactive children when empty; `conditionDecisionBuilders.helpers.js`'s
  `buildNewDecision` appends `connection.target` to the node's `nodes` array
  on `onConnect`) and live DOM inspection. This is the SAME drag-connect
  mechanism as HITL's ROUTER MAPPING, **NOT** Router node's dropdown-picklist
  `Routes` field — despite both producing "output chips = existing node ids,"
  the interaction differs. Case text ("add target node names as chips") reads
  as freeform typing; filed as a CLARIFICATION, same pattern as
  `#1104`/`#1136`/`#1137`/`#1144`. Target nodes must be pre-renamed
  (`edit_node_name`) to match the desired output values before connecting.
- **Edge testid shape is UNSTABLE across save/reload for Decision node edges
  specifically — the most important trap in this session.** The SAME logical
  edge's `data-testid` differs between the live pre-save drag state and the
  post-reload (parsed-from-YAML) state:
  - `nodes`-handle (DECISION OUTPUTS) edge: pre-save
    `{source}nodes-{target}target` (e.g. `Decision 1nodes-bug_respondertarget`)
    → post-reload `{source}---{target}` (e.g. `Decision 1---bug_responder`,
    the `nodes` suffix DISAPPEARS).
  - `default_output` edge: pre-save `{source}default_output-{target}target`
    → post-reload `{source}default_output---{target}` (suffix STAYS, but the
    separator changes from concatenation to `---`).
  - **Use `edge_exists(source_id, target_id)` WITHOUT `handle_suffix`** for
    Decision node edge assertions in either state — its prefix+substring
    matching tolerates both shapes. Do NOT use `edge_testid_present()`/
    `EDGE_TESTID`/`get_edge_locator()` (exact-`---`-only match) for Decision
    edges — unlike Router's routes edges (ELITEA-2033), which use the `---`
    shape in BOTH states and so ARE safe with the exact-match helpers.
- **Custom state variables are NOT built-in** (unlike Router's `input`/
  `messages`, which are) — a fresh pipeline's Decision `Input` combobox lists
  only `input`/`messages` until added via the flow editor's `STATE` side
  panel "+" control. No existing fixture parameter seeds custom state vars;
  add them in-test via the `STATE` panel.
- **`STATE` panel's add-variable "+" button has an unreliable Playwright
  computed accessible name (`"Context"`)** — `get_by_role("button", {name:
  "Context"})` is ambiguous/unstable (confirmed: this session's tooling
  resolved multiple genuinely different click targets to the identical
  locator text across 3 separate attempts) and should not be used. Worse:
  the resulting new-row text input's accessible name is `"name"`
  (`get_by_role("textbox", {name: "name", exact: True})` — WORKS reliably),
  but the raw CSS selector `input[name="name"]` is a live trap — it ALSO
  matches the pipeline's own unrelated General "Name" field
  (`id="name" name="name"`, precedes the STATE panel in DOM order), and
  `querySelector`/`.locator()` without role-scoping silently overwrote the
  pipeline's Name field TWICE this session. Always take a fresh snapshot
  after opening the row and use the role-scoped locator, never a `name=`
  attribute CSS selector, for this panel.
- **CORRECTION to this digest's Router-session entry on
  `pipeline-node-interrupt-before-toggle-{id}`**: it is **NOT** yet
  "unconditional on main" — a fresh `git fetch origin` + `git grep` this
  session found it ONLY on `origin/automation/testids`
  (`CommonInterruptSettings.jsx`), absent from `origin/main`. Re-verify
  provenance per-session rather than trusting a prior session's "on-main"
  claim without re-fetching — testid promotion state changes between
  sessions. `Interrupt after` remains caller-opt-in and Decision's own call
  site (`NormalDecisionNode.jsx`) does not pass it — needs-adding.
  Full detail: `l2_pipeline-decision-node-configuration_ELITEA-2034.md`.

## STATE panel — default vs. custom variable rows (confirmed live, 2026-08-04, ELITEA-2042)

- **Default rows (`input`/`messages`) render ONLY name + toggle, no type
  indicator at all.** Full `outerHTML` capture: `<p>{name}</p>` + a MUI
  `<Switch>`, nothing else — no type badge/icon/text. The case text's
  "input (str, toggle on)" wording implies the type is visible on the row;
  it isn't. Type is only observable via the YAML `state:` section, or (for a
  non-default row) that row's own type-select icon. Filed as a CLARIFICATION,
  not a defect: `EliteaAI/elitea-testing-public#1154`.
- **No-delete-control on default rows is a STRUCTURAL guarantee, not just an
  observation** — `StateVariableItemActions.jsx`'s `showToggle` branch
  (toggle-only) is mutually exclusive with the delete-`IconButton` branch, so
  this is safe to assert directly rather than "not seen this session."
- **New-row commit is Enter/blur, no separate confirm button** —
  `StateVariableItem.jsx`'s `handleNameBlur`/`handleNameKeyDown`. The row's
  type-selector button is genuinely `disabled` while still in create-mode
  (`disableTypeSelector={isCreateMode || !editable}`) — don't click it before
  committing the name.
- **Type dropdown display label ≠ internal/YAML value for the 4th option:**
  `StateVariableTypes` (`flowEditor.constants.js`) maps String→`str`,
  Number→`number`, List→`list`, **Json→`dict`** (not `json`). Any test
  selecting "Json" must assert `type: dict` in the YAML.
- **Testid gaps (needs-adding via `add-data-testid`):** default/custom row
  name label, row toggle, row delete button (dynamic `-{name}` suffix), and
  the type-selector's 4 menu items + the type-select button itself — all in
  `StateVariableItem.jsx` → `StateVariableItemActions.jsx` →
  `StateTypeSelector.jsx` → `StateVariableIconButton.jsx`
  (`src/[fsd]/features/pipelines/flow-editor/ui/state/`). Already-wired STATE
  testids (drawer toggle/close, add-variable button/name-input) need no
  further work.
- **Literal-substring `git grep` false negative, confirmed twice more this
  session:** `pipeline-flow-view`/`pipeline-yaml-view`
  (`` `pipeline-${item.value}-view` ``, `GroupedButton.jsx`) and
  `pipeline-add-node-menu-item-llm` (`` `pipeline-add-node-menu-item-${item.type}` ``,
  `AddNodeMenu.jsx`) are JS template literals — grepping the fully
  interpolated string returns NO hits even though the testid genuinely
  renders. Grep the template PREFIX or read the source component directly.
  Full detail: `l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md`.

## Invalid YAML in the editor is rejected server-side with a clear error, and the app-wide toast testids need no EliteaUI work (confirmed live, 2026-08-04/05, ELITEA-2068)

- Editing a `transition: END` line to remove the colon and append random
  text (`transition END invalid_no_colon_xyz123`) via `edit_yaml_line()` and
  clicking Save fires `PUT .../application/prompt_lib/{project}/{id}`, which
  returns **400** with body containing `"Invalid pipeline YAML data"` (a
  Pydantic-style validation error from the backend's own YAML parse attempt).
- **`edit_yaml_line()`-via-real-keystrokes gotcha — an unterminated quote is
  NOT a reliable way to break YAML through this method.** CodeMirror's YAML
  mode has an auto-close-brackets/quotes extension: typing `transition:
  "END` through `edit_yaml_line()`'s real `keyboard.type()` call auto-inserts
  the matching closing `"`, silently producing the VALID quoted scalar
  `transition: "END"` — the pipeline then SAVES SUCCESSFULLY (200, success
  toast), not the expected 400. This was caught the hard way: an ad-hoc
  Playwright-MCP exploration session that typed the same text via a raw
  `.fill()` call (no real keystrokes → no auto-close) looked invalid, but the
  actual page-object method's `keyboard.type()` path auto-closed it —
  exploration technique and production code path disagreed. **Colon removal
  (no bracket/quote character) is not susceptible and is the reliable
  invalid-YAML technique for this editor** — matches the case text's own
  suggested example ("remove a colon, add random text").
- The Flow canvas does NOT error or blank out when switched to with invalid
  YAML pending — it keeps rendering the last-known-valid graph. The error only
  surfaces on Save attempt, via the app-wide toast, not on the view switch
  itself.
- The Flow canvas does NOT error or blank out when switched to with invalid
  YAML pending — it keeps rendering the last-known-valid graph. The error only
  surfaces on Save attempt, via the app-wide toast, not on the view switch
  itself.
- The app-wide toast (`Toast.jsx`, `src/components/Toast.jsx`) already carries
  `data-testid="toast-alert"` (root, + `data-severity` state attribute),
  `data-testid="toast-message"` (text body), and `data-testid=
  "toast-dismiss-button"` — confirmed pre-existing, used elsewhere (see
  `ChatPage.toast_alert`/`toast_message`/`TOAST_ALERT_SEVERITY`). No EliteaUI
  testid work needed to assert an error toast from ANY page — just declare a
  page-object field for the same testid on that page (repo precedent: each
  page declares its own field for this shared component, per
  `ChatPage`/`ArtifactsPage`/`SkillsListPage`/`SkillDetailPage`).
- After a failed save, Save/Discard remain enabled (edit stays pending,
  un-reverted) — confirming the user can fix the YAML and retry, or Discard to
  revert; the server genuinely rejects the write (verified via
  `PipelineAPI.get_pipeline()` — `instructions` unchanged post-attempt), it
  isn't a silent partial persist.
  Full detail: `l3_pipeline-yaml-editor-invalid-syntax_ELITEA-2068.md`.

## Run Details panel (RunStateNode/RunStateDialog) — implementation notes

**Resolved/added during ELITEA-2450 implementation:**
- Testids added (`EliteaAI/EliteaUI@fb66d978`, `automation/testids`): all 8
  from this feature's AFS Concrete Handles — `pipeline-run-node-label`,
  `pipeline-run-details-panel`, `pipeline-run-details-header`,
  `pipeline-run-details-status-badge` (+ `data-status` mirroring
  `data.status`), `pipeline-run-details-delete-button` (Completed-branch
  only — the mutually-exclusive Stop-branch IconButton was left untagged,
  this case only exercises Completed), `pipeline-run-details-close-button`,
  `pipeline-run-details-timeline-section`, `pipeline-run-details-states-section`.
  The last two wrap two pre-existing SIBLING `Box`es (header+Stepper /
  header+accordion-list — NOT a single existing wrapper) in a new
  `<Box sx={{ display: 'contents' }} data-testid="...">` — `display: contents`
  keeps the wrapper out of `contentContainer`'s flex layout while still being
  queryable; safe, no visual change, prettier/eslint clean.
- **The timeline section's node-id text renders WITHOUT the YAML id's space**:
  pipeline YAML `id: LLM 1` displays as `LLM1` in
  `data.timeline[selectedStep]?.id` (confirmed live — concatenated section
  text was `"Timeline step:LLM119:03:03"`, i.e. `"LLM1"` + timestamp
  `"19:03:03"`, no separator between the two sibling `Typography` elements).
  Assert `"LLM1" in text`, not `"LLM 1"`.
- `FlowEditorConstants.PipelineStatus.Completed === 'Completed'` — the
  `data-status` attribute value and the badge's visible text are both the
  literal string `"Completed"` for a completed run (no case transform needed).
- Confirmed live: the known `EliteaAI/elitea-testing-public#1267` Stepper
  prop-leak console warning fires exactly once per panel open, matched
  reliably by `"non-boolean attribute" in msg.text` alone (no location/stack
  needed) — same idiom as `_is_known_defect_611`.

## Run Details panel — State Before/After per node (confirmed live, 2026-08-06, ELITEA-2452)

- **KNOWN DEFECT, filed `EliteaAI/elitea-testing-public#1271`**: the panel's
  "Before" value for the FIRST timeline step (`selectedStep === 0`) is a
  hardcoded literal `''` (`RunStateDialog.jsx`: `selectedStep ?
  data.timeline[selectedStep - 1].state[variable] : ''`) — it never reads
  the variable's actual pre-run value, even when the variable has a
  non-empty starting default (STATE panel's "Add default value" feature,
  ELITEA-2042). Confirmed live: a `seed_var` pre-set to
  `'PRESET_DEFAULT_VALUE'`, untouched by the only node in a 1-node
  pipeline, showed Before=`""`/After=`"PRESET_DEFAULT_VALUE"` — a false
  "modified" read. **Any test asserting "unmodified variable ⇒
  Before=After" must use a NON-FIRST timeline step** (works correctly for
  `selectedStep > 0`, confirmed live) — never the pipeline's first node.
- **Default-selected timeline step on panel open is the LAST step, not
  index 0**, for an already-`Completed` run — confirmed live on 2
  independent 2-node executions (pipelines 7681/7682). Don't assert
  `selectedStep === 0` on open; explicitly click the desired step before
  reading Before/After.
- **`input`'s Before→After transition at the FIRST node is NOT caused by
  that node's own `input`/`output` mapping** — `input` is the pipeline's
  chat-message variable, populated at pipeline entry (concurrent with the
  first node's execution), independent of whether that node references
  `input` in its config at all. Don't assert "the node's output mapping
  caused this" in a test comment for `input` specifically; it's accurate
  for `messages` (explicit `output: [messages]`) but not for `input`.
- **Accordion row auto-expand**: `BasicAccordion`'s `defaultExpanded={!index}`
  means only the FIRST state-variable row (list index 0, typically `input`)
  starts expanded; every other row (`messages`, any custom variable) starts
  collapsed and needs an explicit click on its header to reveal Before/After.
- **Step-select / row-expand / fullscreen-open are pure client-side
  re-renders — zero new network activity.** Confirmed via
  `browser_network_requests`: no new requests after the initial
  run-completion Socket.IO exchange, across timeline-step clicks, accordion
  expands, and fullscreen-modal opens. Wait via `expect(locator).to_be_visible()`
  after each click (state updates are still React-async), not a network wait.
- **Fullscreen value modal (`PipelineStateViewModal.jsx`, `src/components/`)
  has ZERO testids** — confirmed via `grep -n "data-testid"`, no hits. Its
  heading shows ONLY the variable name (`selectedState.name`), NOT which
  direction (Before/After) was expanded — informational only, not filed as
  a defect (the case never requires the modal to distinguish direction).
- **Dynamic per-variable testid plumbing already exists for the accordion
  row** — `BasicAccordion.jsx`'s `items[].testId` prop is ALREADY threaded
  to `StyledAccordionSummary`'s `data-testid` (line 67); `RunStateDialog.jsx`
  just needs to pass `testId: `pipeline-run-details-state-row-${variable}``
  in its `items` array — no new shared-component plumbing required, unlike
  the Before/After value boxes and their expand icons (`StateItemView`/
  `StateItemViewHeader`), which need NEW `testId`-prop plumbing added.
  Full handle table: `l3_run-details-state-before-after-per-node_ELITEA-2452.md`.

## Run Details panel — Multiple typed custom state variables (confirmed live, 2026-08-06, ELITEA-2453)

- **KNOWN DEFECT, filed `EliteaAI/elitea-testing-public#1274`**: an LLM node with
  `structured_output: true` fails at execution — raw backend error surfaced directly
  in the chat response (`Error: sequence item 0: expected str instance, dict found`)
  — whenever its `output` mapping combines the built-in `messages` variable together
  with `list`/`dict`-typed custom state variables. Isolated via a live A/B: identical
  pipeline with `output: [custom_text, custom_num, custom_list, custom_json, messages]`
  failed; the SAME pipeline with `messages` removed from `output` (custom vars
  unchanged) succeeded cleanly. Any test needing structured-output custom variables
  populated must exclude `messages` from that node's `output` list.
- **`PipelineAPI.create_pipeline()` (generic, pre-existing) already supports a raw
  `state:` block** in its `instructions` YAML param — no new API method needed for a
  fixture that seeds custom typed state variables + a node in one call. Confirmed
  live: `state: {custom_text: {type: str}, custom_num: {type: number}, custom_list:
  {type: list}, custom_json: {type: dict}}` at the top level, sibling to `entry_point`/
  `nodes`, round-trips correctly (visible in the STATE panel and the node's Output
  select options). `create_pipeline_with_nodes()` does NOT support this (only
  `entry_point`+`nodes`) — use `create_pipeline()` directly for any fixture needing
  pre-seeded custom state.
- **Run Details STATES row "uppercase" display is CSS-only, not DOM text.**
  `RunStateDialog.jsx`'s per-variable accordion rows use `BasicAccordion`'s
  `uppercase` prop (default `true`, not overridden here) → `text-transform: uppercase`
  on the `StyledTypography` title. The actual `el.textContent` is the RAW variable
  name (lowercase, e.g. `"custom_json"`), confirmed via `browser_evaluate`
  (`getComputedStyle(el).textTransform === "uppercase"` while `el.textContent ===
  "custom_json"`). A test asserting the case's "displayed uppercase" wording must
  check the CSS property or accept the lowercase testid/text — `to_have_text` against
  the uppercase-looking string will NOT match the real DOM text.
- **Type-specific `After` value rendering is exactly `JSON.stringify`'s native
  type-preserving output** — no custom per-type renderer in `StateItemView`.
  Confirmed live, 4 distinct custom variables in the SAME panel simultaneously:
  `str` → quoted (`"state initialized"`), `number` → bare numeral (`42`, no quotes),
  `list` → bracketed JSON array (`["alpha","beta","gamma"]`), `dict` (display label
  "Json") → braced JSON object (`{"status":"ok","version":1}`). This directly proves
  case ELITEA-2453's steps 9-12 (String/Number/List/Json each render distinctly).
- **Accordion rows are independently expandable, non-exclusive** — expanding all 4
  custom-variable rows in sequence left all 4 visibly expanded simultaneously (not a
  single-open accordion). Confirms case step 13 ("each variable individually
  expandable") directly.
- **Informational, not filed**: a single-node structured-output pipeline's Run
  Details timeline shows TWO entries both labeled with the same node id (e.g. `LLM1`
  at two different timestamps ~2s apart), not one — not investigated further (no
  case step requires exactly 1 timeline entry); worth a closer look if a future case
  needs to assert exact timeline-entry counts for a structured-output node.
  Full handle table + fixture recipe: `l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md`.

## Pipelines dashboard — Search grid filter/clear (confirmed live, 2026-08-07, ELITEA-2023)

**Resolved/added during ELITEA-2023 implementation:**
- **`PipelinesListPage.pipeline_exists_in_list()` (legacy raw `text="..."` locator)
  does NOT reliably match a card name while the dashboard's active search is
  highlighting the matched substring.** Card.jsx's highlight renders the name
  split across nested `<span>` fragments (e.g. `<span>autotest_</span><span
  class="css-...">YAML</span><span>_search_...</span>`). `element.textContent`
  concatenates correctly (`"autotest_YAML_search_..."`), but Playwright's exact
  `text="..."` locator engine (`:text-is()`) does **not** match the parent on
  that concatenated text in the split-node case — confirmed via a live
  reproduction (`page.locator('text="<exact-name>"').count()` → `0` against the
  identical page state where `el.textContent` was correct). This is a Playwright
  quirk, not a DOM/app bug. **Fix:** added `PipelinesListPage.entity_card_name`
  (`LocatorDescriptor(testid="entity-card-name")`, the same shared `Card.jsx`
  testid used by `AgentsListPage`/`CredentialsListPage`/`McpListPage`/
  `SkillsListPage`) + `get_card_names()`, which reads each card's own
  `.text_content()` directly — robust to the split-node highlighting. Use
  `get_card_names()` (membership check) instead of `pipeline_exists_in_list()`
  whenever the grid may be in a filtered/highlighted state; `pipeline_exists_in_list()`
  remains correct for unfiltered/baseline and absence checks (no highlighting
  present there).
- **`PipelinesListPage.search()`/`clear_search()` were fill-only (no Enter, no
  Clear-icon click)** — confirmed the AFS's finding live: typing alone only opens
  the suggestions popover, never narrows the dashboard grid; the actual filter
  dispatch fires only on Enter or the send-icon click (shared `SearchBar.jsx`).
  Both methods now mirror `McpListPage.search()`/`clear_search()` — click + Enter
  for search, a new `search_clear_button` (`testid="search-clear-button"`) click
  for clear. The two pre-existing `TestSearchPipeline` tests
  (`test_search_pipeline_by_name`, `test_search_pipeline_no_results`) still pass
  unchanged after this fix — confirmed green alongside the new test in the same
  local run (determinism is the merge gate's job, not repeated local runs).
  Full handle table + AFS: `lextend_pipeline-dashboard-search-filter-and-clear_ELITEA-2023.md`.
