# Pipelines — exploration digest

> Handle cache from live sessions against `http://localhost:5173`. Verify a handle as
> you use it — this is a cache, not a source of truth. One writer at a time; update in
> place, don't append duplicate entries. Last updated: 2026-08-08 (ELITEA-2013 analysis).

## Pipeline tags — Categories.jsx tag filter panel + CardTagSectionItem chips are FULLY shared with Skills, zero new testid work (confirmed live, 2026-08-08, ELITEA-2013)

The Pipelines dashboard's right-side "Tags" panel (`PrivatePipelinesList.jsx` →
`RightInfoPanel.jsx` → `Categories.jsx`, same component tree for the
`cardContentType !== ApplicationAdmin` case that every non-admin private
pipeline view uses) is the identical shared component
`SkillsListPage`'s tag filter already drives (ELITEA-1740). Confirmed by
source read AND live DOM: `Categories.jsx` hardcodes
`data-testid={\`tags-panel-chip-${name}\`}` (line 336) and
`data-testid="tags-panel-clear-all"` (line 299) directly — entity-agnostic,
no per-caller prop gating. Same for card-level tag chips:
`CardTagSectionItem.jsx` hardcodes `entity-card-tag-chip`/
`entity-card-tag-overflow` (line 22), rendered by the shared `Card.jsx` for
Pipelines exactly as for Skills.

- **`PipelinesListPage` has NO tag-filter methods yet** (unlike
  `SkillsListPage`) — this is pure page-object-plumbing work for whoever
  implements ELITEA-2013, not testid work. Mirror
  `SkillsListPage.filter_by_tag()`/`clear_tag_filter()`/`get_card_tags()`
  (`automation/pages/skills_list_page.py:127-141,230-265,519-578`)
  line-for-line; only the grid-refetch URL substring changes:
  `/elitea_core/applications/prompt_lib/` (pipelines, `agents_type=pipeline`)
  vs `/elitea_core/skills/prompt_lib/` (skills).
- **Tag input/chip on the create/edit form** (`pipeline-tags-input`/
  `pipeline-tags-chip`, pre-existing from ELITEA-2021) confirmed live and
  reused as-is — `PipelineFormPage.add_tag()` (type + Enter) already exists
  and is sufficient for BOTH new and pre-existing-tag-by-exact-name cases;
  no `select_existing_tag()` analog is needed for Pipelines (unlike Skills'
  `SkillFormPage.select_existing_tag()`) because `TagEditor.jsx`'s
  `handleOnChangeTags` transparently reuses an existing tag id on exact-name
  match regardless of whether it was typed or clicked from the dropdown.
- **No `getOptionTestId` wired for the Pipeline branch's Tags autocomplete
  dropdown** (`ApplicationEditForm.jsx:174-188` only threads `inputTestId`/
  `chipTestId`, not `getOptionTestId` — unlike some other consumers of the
  shared `AutoCompleteDropDown.jsx`). Not a gap for THIS case (type+Enter
  reuse covers it, see above) — would be a genuine testid-needed escalation
  only if a future case specifically needs to click an existing-tag option
  out of the dropdown listbox for Pipelines.
- Full case detail: `test-specs/pipelines/l2_pipeline-tags-add-and-filter_ELITEA-2013.md`.

## Dashboard view toggle (Card vs Table) — `entity-card-name` count + `?view=` URL param are the layout-format proof, no new testid needed (confirmed live, 2026-08-08, ELITEA-2024)

`PipelinesListPage.table_view_button`/`card_view_button` (testids
`pipeline-table-view`/`pipeline-card-view`, wired in `Pipelines.jsx` on the
shared `ViewToggle.jsx` component — same component Agents/MCPs/etc. use with
their own testid overrides) both resolve correctly live and are **on
`automation/testids` but NOT yet on `main`** (fresh `git fetch origin` this
session: `git grep` hit on `origin/automation/testids` only, at
`src/pages/Pipelines/Pipelines.jsx:274-275`).

- **Default view is Card list view** — confirmed live: fresh `/pipelines/all`
  load renders the Card list view button `[pressed]` (`aria-pressed="true"`),
  Table view button unpressed. `PipelinesListPage` has NO method asserting
  this default state — `is_card_view_active()`/`is_table_view_active()` exist
  but the merged test (`test_view_toggle_table_and_card`,
  `test_pipeline_management.py:87`) never calls them before its first click.
- **View state lives in the URL, not just component state**: `ViewToggle.jsx`
  writes `SearchParams.View` (`?view=table`/`?view=cards`) via
  `useSetUrlSearchParams`; `useIsTableView.js` reads it back
  (`searchParams.get(SearchParams.View) === ViewOptions.Table`) to drive
  `CardList.jsx`'s `shouldRenderTable` ternary between `DataTable` (table) and
  `DataCards` (card grid). Pure client-side, no XHR fires on toggle click.
- **Strongest layout-format proof, testid-only, no new testid work**: the
  `entity-card-name` testid (`Card.jsx:210`, existing `LocatorDescriptor`
  field) is rendered ONLY by the card-view `Card` component — `DataTable`
  (table view) never renders it. Confirmed live:
  `document.querySelectorAll('[data-testid="entity-card-name"]').length` was
  `12` in card view (matching the 12 visible pipelines) and dropped to `0`
  immediately after switching to table view, back to `12` on switching back.
  Combine with the `?view=table`/`?view=cards` URL param for a
  belt-and-braces layout assertion — neither needs a new testid.
- **Testid gap that's genuinely NOT needed for this case** (flag for a future
  table-specific case only): table view's column headers ("Name &
  Description"/"Authors"/"Created"/"Actions", `GridTableHeader.jsx`) carry NO
  `data-testid` for Pipelines — `DataTable.jsx` only passes
  `columnTestIdPrefix` for `isMCPs`, `undefined` otherwise. The
  `entity-card-name`-absence + URL-param combo above is sufficient without it.
- Full gap analysis + exact patch: `test-specs/pipelines/lextend_pipeline-dashboard-view-toggle-default-and-layout_ELITEA-2024.md`.

## Three-dot Actions menu — full live-confirmed testid map, both groups (confirmed live, 2026-08-08, ELITEA-2049)

Full DOM query of `[data-testid="agent-actions-menu"] [role="menuitem"]` on a
pipeline detail page (`FullDetailsPipe_probe2`, id 6754, base version). Two
groups, both rendered by the SAME shared `ApplicationControls.jsx` component
Agent detail pages use — testid keys mostly carry the literal `agent`/`share-agent`
naming regardless of entity type (tech debt, not a bug):

| Group | Label | Testid | Notes |
|---|---|---|---|
| VERSION | Set as a default | `set-as-a-default-menuitem` | disabled (always, for the currently-open version) |
| VERSION | Export | `agent-actions-export-menuitem` | shared Agent/Pipeline testid |
| VERSION | Share (version-specific link) | `share-version-menuitem` | shared testid, NOT case-text's "Copy link" target |
| VERSION | Fork | `pipeline-actions-fork-menuitem` | **entity-scoped** — differs from Agent's `agent-actions-fork-menuitem` (`ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map) |
| VERSION | Delete ("Delete version") | `delete-version-menuitem` | disabled while open version is `base` |
| PIPELINE | Share (generic link — **this is "Copy link"**) | `share-agent-menuitem` | same literal key as Agent's PIPELINE-analog item — testid does NOT rename per entity |
| PIPELINE | Pin to top | **none — testid gap** | `usePinMenu.hooks.jsx`'s menu-item object has no `key` field at all (only shared hook without one); needs an optional `key` param threaded from each of its 4 callers (`ApplicationControls`/`SkillControls`/`ToolkitsControls`/`CredentialsControls`) — see AFS for the exact minimal-scope fix |
| PIPELINE | Delete pipeline | `delete-agent-menuitem` | same testid as Agent's "Delete agent" — only the LABEL switches per `isFromPipeline` |

**Case-text drift, 3rd occurrence of the same pattern**: no case that says
"Copy link" as a menu-item label will ever find one literally — it's always
"Share" (`useCopyLinkMenu({ label: 'Share', ... })` overrides the hook's own
default `'Copy link'` label at every call site observed so far). Filed as a
sibling clarification each time a new surface hits it: #1288 (Agent Detail),
#1218 (Agent Hub modal), #1337 (Pipeline Detail, this session) — all
cross-linked. If a 4th surface hits this (e.g. Skill/Toolkit/Credential
three-dot menus), the same treatment applies: sibling, not duplicate, cross-link.

**Clipboard-read via MCP browser hangs — use the pytest pattern instead.** A
raw `page.evaluate("async () => await navigator.clipboard.readText()")` call
through the Playwright MCP browser (no test-context permission grant, no
interactive-dialog handler) hung indefinitely (~30 min) waiting on a
permission prompt that can never resolve outside a real Playwright test
process. The suite's own established pattern — `page.context.grant_permissions
(["clipboard-read","clipboard-write"])` once, then `page.wait_for_function
("async () => { const t = await navigator.clipboard.readText(); return
t.length > 0; }")` — works fine inside pytest (already proven by
`test_agent_copy_version_link.py`, ELITEA-1898) because the test-context
permission grant pre-authorizes it; there is no equivalent MCP-side grant
call. Don't reattempt the direct call in a future MCP exploration session —
confirm toast text/visibility live instead, and defer clipboard-content
verification to the implementer's pytest run.

## Pipeline Export — downloaded `.pipeline.md` frontmatter shape confirmed on TWO pipelines; no `nodes`/`state` verified by the existing spec (confirmed live, 2026-08-08, ELITEA-2050)

Extends `test_pipeline_import_via_file.py` (ELITEA-2012) rather than a fresh spec — that
test already exports+downloads+parses the file but only asserts `name`/`description`/
`agent_type`/`conversation_starters`, never `nodes`/`entry_point`/`pipeline_settings`.
Details + exact gap patch: `test-specs/pipelines/lextend_pipeline-export-verify-structure_ELITEA-2050.md`.

- **Export top-level YAML shape depends on whether the pipeline has any non-END node.**
  A pipeline with only an `END` node (`FullDetailsPipe_probe2`, id 6754) exports WITHOUT
  a top-level `entry_point`/`nodes` key at all — only `pipeline_settings.nodes` (canvas,
  containing just the `END` entry) is present. A pipeline with a real node (LLM, per
  ELITEA-2012's own pipeline) exports WITH `entry_point: <node id>` and a top-level
  `nodes:` list (each entry: `id`/`type`/`input`/`input_mapping`/`output`/`transition`).
  Any case asserting "nodes" in the export must use a pipeline with a real node — an
  empty/bare pipeline makes a "non-empty nodes list" assertion meaningless.
- **No literal `state` top-level key exists anywhere in the export** — confirmed via
  source read (`EliteaUI/src/pages/Common/Components/useExport.js`: pipelines/
  applications export is a server-rendered `GET .../export_import/prompt_lib/{project}/{id}
  ?format=md` fetch, blob-downloaded client-side, no client "state" concept at all). A
  case asking to verify "state" in the export should be read as `pipeline_settings`
  (canvas nodes/edges/positions) — the closest structural analogue — not a literal key
  match.
- **Case-text drift "JSON file" reconfirmed on a SECOND TMS case (ELITEA-2050) via the
  SAME underlying mechanism** as ELITEA-2012's already-filed
  [#1334](https://github.com/EliteaAI/elitea-testing-public/issues/1334) — commented on
  the existing issue rather than filing a duplicate (same object: `useExport.js`'s
  `doExport` hard-codes `format=md` for `pipelines`/`applications`, no `format=json` path
  exists at all).

## Pipeline Import via File — Export downloads Markdown (not JSON), Import shares Agent/Skill's ImportWizardModal wholesale, one new testid needed (confirmed live, 2026-08-08, ELITEA-2012)

Full round trip (create → export → delete → import → verify → execute) confirmed live end-to-end,
no product defect. Details in `test-specs/pipelines/l2_pipeline-import-via-file_ELITEA-2012.md`.

- **Export format is Markdown YAML-frontmatter (`.pipeline.md`), never JSON** — the case text
  says "JSON file downloads"; live product's `ExportApplicationButton.jsx` always calls
  `doExport({ format: ExportFormat.MD })()` (same for Agents). Filed as case-text drift:
  `EliteaAI/elitea-testing-public#1334`. Filename pattern:
  `<slugified-pipeline-name>.pipeline.md`. Content is a `---`-fenced YAML block:
  `name`/`description`/`model`/`max_tokens`/`agent_type: pipeline`/`step_limit`/
  `conversation_starters`/`entry_point`/`nodes` (each with `input_mapping`/`output`/
  `transition`)/`pipeline_settings` (canvas edges + node positions).
- **Import (`useImport.hooks.js`) accepts ONLY `.md`/`.zip`** (`fileInput.accept =
  '.md,.zip,text/markdown,application/zip'`) — exactly what Export produces, so the round trip
  works even though the case's "JSON" wording doesn't match. Import button click
  (`ToolbarImportButton.jsx`'s `openFileDialog`) opens a native OS file chooser DIRECTLY, no
  intermediate menu — same pattern as `AgentsListPage.import_agent()`.
- **Testid gap — `pipelines-import-button` needed.** `ToolbarImportButton.jsx` already accepts
  an optional `testId` prop and forwards it to `data-testid`; the Agents call site
  (`src/pages/Applications/Applications.jsx:113`) already wires
  `testId="agents-import-button"` (ELITEA-1795, EliteaUI draft PR #552) but the Pipelines call site
  (`src/pages/Pipelines/Pipelines.jsx:272`, `<ToolbarImportButton />`) passes NO prop at all —
  confirmed on both `origin/main` and `origin/automation/testids`. Low-risk mechanical fix:
  thread `testId="pipelines-import-button"`, same mechanism.
- **Everything downstream of the click already works for pipelines with ZERO new testid work** —
  the Import parameters preview dialog, its confirm button, and the Import Complete dialog +
  "Got it" button are the SAME shared `ImportWizardModal`/`IWModal*` component tree Agent and
  Skill import already use (`agent-import-preview-dialog`, `agent-import-confirm-button`,
  `agent-import-complete-dialog`, `agent-import-complete-got-it-button` — all `agent-` prefixed
  by existing convention despite being entity-agnostic). Confirmed live: used all four directly
  with zero add-data-testid work.
- **Pipeline-specific addition to the shared preview dialog**: a "Pipeline Diagram" section
  (Start → {node names} → END, mermaid-like) that the Agent import preview does NOT render (Agent
  shows Skills/Nested-entities cards instead). Not required by any of ELITEA-2012's assertions
  (text fields + post-import canvas state suffice) — no testid added, per the "touches" scoping
  rule.
- **Execution gotcha, NOT an import defect**: an LLM node with Task field left at its default
  (`Type=Fixed`, empty Value) 400s on chat send
  (`"messages.0: user messages must have non-empty content"`) — reproduced BEFORE any
  export/import involvement (same config existed on the original pipeline). Fixed by mapping
  `Type=Variable, Value=input` via the existing shared `select-option-{}` dynamic-testid
  convention. Any pipeline case that needs a working chat execution assertion must configure the
  LLM node's Task field this way — not an import-specific requirement.
- **Minor, already-tracked, non-blocking**: the Import Complete dialog's `IWModalSucceedContent.jsx`
  emits a benign React `validateDOMNesting` (`<div>` in `<p>`) console warning — tracked at
  `EliteaAI/elitea-testing-public#570` (originally filed against Agent/Skill import); this session
  added a comment confirming it also fires for Pipeline import (same shared component, no new
  issue filed).
- **Delete pipeline via three-dot menu** reused for cleanup — `delete-agent-menuitem` (NOT
  `delete-pipeline-menuitem`, per the existing gotcha below) + auto-redirect to `/pipelines/all`
  reconfirmed live.

**Resolved/added during ELITEA-2012 implementation (2026-08-08):** `pipelines-import-button`
testid added — `EliteaAI/EliteaUI@257cd359` on `automation/testids` (awaiting human promotion to
`main`). `test_pipeline_import_via_file.py` (full create → export → delete → import → verify →
execute round trip) green on first local run — confirmed live, matches this digest entry exactly:
the auto-redirect after delete DOES fire correctly when the detail page was reached entirely via
in-app SPA navigation (dashboard → "+ Pipeline" → Save → detail page), unlike ELITEA-2022's own
test (`test_delete_pipeline_via_ui_menu`, sanctioned-RED #1332) whose setup reaches the detail page
via a direct `page.goto()` (no prior in-app history entry) — the redirect defect is specifically a
browser-history no-op, not a general product break. **Confirmed via source read:** the shared
`IWModalEntityCard.jsx`/`IWModalEntityCardWrapper.jsx` preview-dialog fields (Type/Description/
Chat-starters/Step-limit) carry NO `data-testid` at this call site (the wrapper's `subtitleTestId`
prop is unwired here) — full config-equivalence verification was done on the imported pipeline's
detail page (UI fields + `pipeline_api.get_pipeline()` API readback for node structure) instead of
inside the preview dialog; see the AFS's own implementer-amendment note on Step 5 for detail. New
page-object surface: `PipelinesListPage.import_pipeline()`/`confirm_pipeline_import()`/
`confirm_import_complete()` (mirrors `AgentsListPage`'s import trio) + `PipelineDetailPage.
export_pipeline_via_menu_and_download()` (testid-based, `page.expect_download()` — distinct from
the pre-existing raw-handle `export_pipeline_via_menu()`, left unmodified for its own caller).

## Delete pipeline via three-dot menu — auto-redirect confirmed correct; existing merged spec masks the redirect assertion by navigating manually (confirmed live, 2026-08-08, ELITEA-2022)

`test_delete_pipeline_via_ui_menu` (`test_pipeline_management.py:391`, merged to
`origin/automation/base`) already drives the full delete flow correctly (three-dot
menu → "Delete pipeline" → type-to-confirm dialog → `DELETE .../application/
prompt_lib/{project}/{id}` → `204`), but its own Step 4 calls
`list_page.navigate()` instead of asserting the app's automatic redirect — so a
future regression to the auto-redirect would go undetected. Live-reconfirmed this
session: after clicking the confirm dialog's "Delete" button, the URL transitions
on its own from `/pipelines/all/{id}?...` to `/pipelines/all` with zero manual
navigation and zero console errors. Classified `extend-existing`, not a defect —
see `test-specs/pipelines/lextend_delete-pipeline-via-actions-menu_ELITEA-2022.md`
for the gap assertion + exact patch shape.

**Testid gotcha for "Delete pipeline"**: the PIPELINE-group menu item's testid is
`delete-agent-menuitem`, NOT `delete-pipeline-menuitem` — `ApplicationControls.jsx`
reuses one shared `deleteApplicationMenuItem` object (key `delete-agent`) for both
Agent and Pipeline entities; only the visible label switches
(`Delete ${isFromPipeline ? 'pipeline' : 'agent'}`). Confirmed live via
`page.getByTestId('delete-agent-menuitem')` resolving correctly on a pipeline
detail page. Both `open_actions_menu()` and `delete_pipeline_via_menu()` in
`PipelineDetailPage` still use bounding-box/text-role fallbacks internally
(pre-existing tech debt, unchanged by this case) despite the real testids
existing and resolving correctly — same situation ELITEA-2003's AFS already
flagged for the three-dot button itself.

## Interrupt before/after — pause works, plain-chat resume is a CONFIRMED DEFECT (`#1327`), pipeline-level YAML field (confirmed live, 2026-08-08, ELITEA-2047)

`interrupt_before`/`interrupt_after` (`CommonInterruptSettings.jsx`, every node type
sharing it — LLM/Code/MCP/Toolkit/Custom/Decision/Agent, NOT the HITL **node type**) is
a genuine LangGraph-checkpoint feature, distinct from HITL's dedicated
approve/edit/reject resume wiring (ELITEA-2015, `#1103`). Confirmed on pipeline id 8159
(`Code 1 -> Printer 1 -> END`):

- **YAML shape — pipeline-level, NOT per-node.** `interrupt_after` is a TOP-LEVEL
  pipeline YAML key holding a list of node ids (`entry_point: Code 1\ninterrupt_after:\n
  - Code 1\nnodes:\n  ...`), unlike `structured_output` which nests under the node.
  Don't assert `nodes[0].interrupt_after` — it isn't there.
- **Disabled-state gating (same `CommonInterruptSettings.jsx` logic already documented
  for every node type)**: "Interrupt before" disabled while the node is the entry
  point; "Interrupt after" disabled while the node has no outgoing transition
  (`transition: END` or none) — a LONE freshly-added node always has both disabled; a
  real 2-node pipeline with an edge is required to exercise "Interrupt after".
- **Pause DOES work correctly, live-confirmed**: executing via embedded chat runs the
  interrupted node, THEN pauses — `interrupt` pill on the canvas edge right after the
  node; the WHOLE node config panel goes `disabled`/locked; chat header shows a
  "Run is in progress" spinner + clickable "Run N details" + "Stop run"; chat
  auto-posts *"How to proceed? To resume the pipeline - type anything..."*.
- **Resume via plain chat is BROKEN — `EliteaAI/elitea-testing-public#1327`,
  reproduced independently in TWO sessions** (an earlier `test-automation-engineer`
  implementation attempt, then this analysis session, same pipeline). Sending a plain
  message (e.g. `"continue"`) — the UI's OWN advertised instruction — does NOT resume:
  it spawns a **second, distinct Run History entry** (different duration — i.e. a new
  run, not a resumed one) rather than continuing the checkpointed run; the SAME "How to
  proceed?" hint re-appears verbatim; Printer 1 never executes; the `interrupt` pill and
  locked panel persist. "Run is in progress"/"Stop run" vanish from the header (a
  half-cleanup, neither a clean resume nor a clean failure). Zero console errors —
  silent behavioral defect, not a crash. **Distinct from `#1103`** (that's HITL-node-
  specific `chat_continue_predict{hitl_resume:true, hitl_action}`; this toggle has no
  action buttons at all, only the "type anything" text hint, and that hint doesn't work).
- **Testid gaps (not yet added)**: the "Run is in progress" header banner, the "Run N
  details" trigger label, the "Stop run" button, and the `interrupt` canvas edge pill
  all have ZERO `data-testid` — confirmed via live DOM/innerText checks, no stable
  selector isolated beyond coarse text/accessible-name matching this session. Left as
  gaps for whichever implementer needs them (recommended names in the AFS's Concrete
  Handles table) rather than guessed/added blind.
- **WebSocket-frame capture not attempted this session** — `PipelineDetailPage.
  capture_websocket_frames()` (pytest-fixture-level, same pattern as ELITEA-2015's HITL
  test) can't be retrofitted onto an already-open Playwright-MCP browser session; the
  implementer automating step 8's soft-assert doesn't strictly need it (DOM/Run-History
  evidence is sufficient), but a future deep-dive into WHY resume fails (never sends a
  resume-shaped frame vs. sends one the backend ignores) should use it.
- Full flow, handles, and Coverage Map:
  `test-specs/pipelines/l2_pipeline-interrupt-before-after-toggles_ELITEA-2047.md`.

## Structured output toggle — default disabled, correctly persists both directions through save + reload, YAML matches (confirmed live, 2026-08-08, ELITEA-2046)

Confirmed live end-to-end on the LLM node's `pipeline-llm-node-structured-output-toggle`
(chosen as the representative instance — the toggle is wired via the same shared
`CommonInterruptSettings.jsx` component on every node type that renders it: LLM/Code/
MCP/Toolkit/Custom, per the existing digest entries below): a freshly-added node's
toggle reads `checked === false` before any interaction (no click needed to observe the
default); click → `checked === true` → Save (`PUT .../application/prompt_lib/{project}/{id}`
→ `201`) → full page reload (canonical URL, per the ELITEA-1954 404-on-bare-URL gotcha) →
toggle still `checked === true`; click again → `checked === false` → Save → reload →
still `checked === false`. YAML's `structured_output` field matched at both checkpoints
(`true` then `false`) — read directly via the on-screen `pipeline-yaml-editor` tab, NOT
`pipeline_api.get_pipeline()`: this single-node, no-extra-fields pipeline's YAML is only
19 lines, well under the ~32-34-line truncation threshold documented below for `#1025`
(confirmed live — no truncation observed at either state), so the API-readback workaround
ELITEA-2045's 40-line document needed does not apply here. No product defect — case text
matched live behavior exactly on all 5 steps. Full flow + page-object gap list (none — zero
new testids needed): `test-specs/pipelines/l2_pipeline-structured-output-toggle-persistence_ELITEA-2046.md`.

## LLM node Output multi-select drops a selection if you don't close-then-reopen between picks (confirmed live, 2026-08-08, ELITEA-2045)

Selecting more than one variable in the LLM node's Output combobox **inside a
single open popover** silently drops selections beyond the first one or two —
confirmed live this session: `name` then `age` (still inside one open/close
cycle, immediately back-to-back) registered correctly, but adding `hobbies`
immediately after in the SAME open popover did not register at all (the Save
payload's `output:` list came back with only `[name, age]` until `hobbies`/
`metadata` were each selected in their OWN open→select→Escape→reopen cycle).
This matches (and reconfirms) the existing `_select_multi_select_option_and_close()`
helper's own docstring warning — **the fix is already the default behavior of
`select_llm_node_output_variable(name)`, which performs one full open/select/
close cycle per call**; the bug only bites a caller who manually opens the
popover once and clicks multiple `select-option-*` targets before closing.
Automation implication: always call `select_llm_node_output_variable(name)`
once per variable, never batch clicks inside one manually-held-open popover.

## Pipeline YAML tab silently truncates long documents — reconfirmed on a DIFFERENT node/pipeline shape (2026-08-08, ELITEA-2045, `EliteaAI/elitea-testing-public#1025`)

Already filed during ELITEA-2010 (Toolkit node, 41-line document, cutoff at
line 32) — reproduced again this session on a single-LLM-node pipeline with
4 typed custom output variables + `structured_output: true` (40-line
document, cutoff at line 34, i.e. right after `output:\n      - name`,
before `- age`/`- hobbies`/`- metadata`/`structured_output: true`/
`transition: END`). Confirmed **display-only**: the PUT-save response body's
`version_details.instructions` field has the full, correct YAML; only the
`pipeline-yaml-editor` CodeMirror DOM (and thus `get_yaml_content()`) is
truncated. `.cm-scroller.scrollHeight === .cm-scroller.clientHeight` in both
cases — the editor believes there's nothing more to scroll to, so there is
**no UI-reachable workaround** (confirmed: resizing the browser viewport
taller, e.g. 1400×2200, makes the full document render — the root cause is
viewport-height-driven, not a hard line-count cap). **Automation
implication, reconfirmed**: for any pipeline whose full node YAML is likely
to exceed ~32-34 rendered lines at a normal test viewport, verify content via
`pipeline_api.get_pipeline(pipeline_id)["version_details"]["instructions"]`
(parsed with `yaml.safe_load`) instead of `switch_to_yaml_view()` +
`get_yaml_content()` — the same pattern `test_pipeline_yaml_editor_invalid_syntax.py`
(ELITEA-2068) and `test_pipeline_advanced.py` already use for server-truth
readback. Full case detail:
`test-specs/pipelines/l2_llm-node-structured-output-state-variables_ELITEA-2045.md`.

## Printer node — SimpleLLMInputs (PRINTER section) + standalone Final Message field, NO Input/Output selects, NO Interrupt/Structured-output controls (confirmed live, 2026-08-08, ELITEA-2039)

`PrinterNode.jsx` renders the SAME shared `FlowEditorSettings.SimpleLLMInputs`
component as the Code node (single mapping key `printer`, default
`{type: 'fixed', value: ''}` via `usePrinterInputMapping.js`) plus a
standalone `AIAssistantInput` for `final_message` — confirmed via source AND
live DOM. **Unlike every other configurable node type in this suite
(LLM/Code/HITL/MCP/Toolkit/Router/Decision/State-modifier/Custom/Agent),
Printer has NO `FlowEditorSelect.InputSelect`/`OutputSelect` and NO
`FlowEditorSettings.CommonInterruptSettings` at all** — confirmed via source
read (`PrinterNode.jsx` imports neither) and live DOM (`#simple-select-Input`/
`#simple-select-Output` both resolve to 0 matches inside the node; no
"Interrupt"/"Structured output" substrings in the node's text content). Only
the two generic ReactFlow `CustomHandle` connection points (`target` top,
`source` bottom) exist — the case's own step 8 wording ("Printer node has
only Output handle (no Input combobox visible in panel)") already correctly
anticipates this, no case-text drift.

- **Zero testids existed on `PrinterNode.jsx` before this session** — added a
  `PRINTER_NODE_INPUT_TEST_IDS` map (same shape as `CODE_NODE_INPUT_TEST_IDS`
  in `CodeNode.jsx`, ELITEA-2009) wiring `testIdsByKey={{printer: {...}}}` on
  the `SimpleLLMInputs` call site, plus `inputProps={{'data-testid': ...}}`
  directly on the `AIAssistantInput` call site for Final Message (MUI
  `TextField`'s `htmlInput` slot — the "needs `inputProps`, not a bare
  `data-testid` prop" pattern already documented elsewhere in this digest for
  the Webhook/Schedule modal fields) — `EliteaAI/EliteaUI@955f88b9` on
  `automation/testids`.
- **Type select's 3 options are Fixed/F-String/Variable, default `Fixed`** —
  same `TYPE_OPTION_VALUE_BY_LABEL` mechanism as every other SimpleLLMInputs
  call site in this suite, confirmed live.
- **PRINTER Value and Final Message are both plain MUI textareas, NOT
  CodeMirror** — confirmed live via `tagName === 'TEXTAREA'`, same pattern as
  every other `AIAssistantInput`/`SimpleLLMInputItem` field in this suite.
  Embedded literal `\n` (backslash+n, not a real newline) types and reads
  back exactly via `press_sequentially()`, same convention as the Code node's
  Python-code Value field.
- **Save + full page reload correctly persists** PRINTER Type, Value, and
  Final Message (confirmed live round-trip this session, zero console errors
  at every checkpoint). Same `PUT .../application/prompt_lib/{project}/{id}`
  → 201 mechanism as every other pipeline-node-configuration case in this
  family.
- Full flow, handles, and page-object gap list:
  `test-specs/pipelines/l2_pipeline-printer-node-configuration_ELITEA-2039.md`.

**Resolved/added during ELITEA-2039 fix round 2 implementation:** the two
generic `CustomHandle` connection points (target/source, line 21 above) also
now carry real testids — `CustomHandle.jsx` (EliteaUI
`src/[fsd]/features/pipelines/flow-editor/ui/nodes/CustomHandle.jsx:104-111`)
forwards a `testId` prop straight to `data-testid`, so this is an app-owned
hook, NOT a #579 library-internal-DOM exception (round-1 code incorrectly
treated `.react-flow__handle` as the sanctioned class `get_node_count()` uses
for the ReactFlow node-container CSS class — that class has no such hook,
these handles do). `PrinterNode.jsx`'s two `CustomHandle` call sites now pass
`testId="pipeline-printer-node-target-handle"` /
`testId="pipeline-printer-node-source-handle"` —
`EliteaAI/EliteaUI@b65756af` on `automation/testids` (awaiting human
promotion to `main`). Same mechanism `NormalDecisionNode.jsx` already uses
for `pipeline-decision-node-output-handle`. Any future node type wiring a
`CustomHandle` testid should follow this same `testId` prop, not a raw DOM
query.

## Agent node — own component (NOT a `BaseToolNode.jsx` caller), single-select-as-toolkit, TASK-only input mapping, DIFFERENT attach endpoint (confirmed live, 2026-08-08, ELITEA-2038)

`AgentNode.jsx` is its OWN standalone component — unlike Toolkit/MCP (which
share `BaseToolNode.jsx`'s `TEST_ID_PREFIX_BY_NODE_TYPE` map), it renders its
own JSX tree directly: `FlowEditorSelect.ToolSelect` (label "Agent",
`filterTypes: tool => tool.type === ToolTypes.application.value`) →
`FlowEditorSelect.InputSelect` → `FlowEditorSelect.OutputSelect` →
`FlowEditorSettings.InputMapping` (gated `{!isOrphan && ...}`, same
two-stage-reveal as Toolkit/MCP) → `FlowEditorSettings.CommonInterruptSettings`
with `showStructuredOutput={false}` (so Structured output NEVER renders for
this node type — permanent, not a testid gap). Confirmed live: **zero testids
existed on this component before this session** — added a local
`AGENT_NODE_TESTID_PREFIX = 'pipeline-agent-node'` constant (same shape as
`BaseToolNode.jsx`'s prefix, but as a standalone const since AgentNode has no
map to key into) wiring 6 fields (Agent select, Input/Output selects,
Input-mapping value/type/required-heading, Interrupt-after toggle) —
`EliteaAI/EliteaUI@2859a9d0` on `automation/testids`.

- **Attaching an Agent to the Tools section uses a DIFFERENT endpoint from
  Toolkit/MCP**, despite sharing the same `ToolMenu.jsx` UI and the same
  `toolkit-menu-item`-testid popper rows. Toolkit/MCP attach fires
  `PATCH .../tool/prompt_lib/{project}/`; Agent attach fires
  `PATCH .../application_relation/prompt_lib/{project}/{agent_id}/{agent_version_id}`
  (`useAgentPipelineAssociation.hooks.js`'s `updateApplicationRelation`
  mutation) — confirmed via source read AND live network capture, both
  return `201 Created` and both auto-persist immediately on popper
  selection (same *behavior*, different *mechanism* — a test asserting the
  wrong endpoint string would silently never resolve its
  `page.expect_response()` wait and time out instead of failing fast on a
  wrong assertion).
- **The Agent-as-tool's Input-mapping schema has exactly ONE required key,
  `task` (displayed "Task"), and ZERO optional keys** — confirmed live:
  "Input mapping (required 1)" renders with no sibling "optional" accordion.
  Its Type select's **default value is already "F-String"** (`fstring`), NOT
  "Fixed" like every sibling node's tool-parameter Input-mapping fields —
  confirmed live via DOM read before any interaction. A case describing "set
  Type to F-String" is describing the pre-existing default, not an action;
  document as a clarification, don't treat as a defect.
- **Same custom-state-var precondition as every other node-config case in
  this family** (Code/2009, State modifier/2035, Custom/2036, MCP/2037):
  Input/Output combos list only `input`/`messages` on a fresh pipeline —
  variables the case's Test Data table implies as pre-existing must be added
  via the STATE panel's "+" control first (`add_state_variable()`).
- **Save + full page reload correctly persists** Agent selection, Input (both
  multi-select variables), Output, and TASK Type+Value (confirmed live
  round-trip this session, zero console errors at every checkpoint). Same
  `PUT .../application/prompt_lib/{project}/{id}` → `201` mechanism as every
  other pipeline-node-configuration case in this family.
- Full flow, handles, and page-object gap list:
  `test-specs/pipelines/l2_pipeline-agent-node-integration_ELITEA-2038.md`.

## Custom node — SAME component tree as Toolkit node + a unique raw-JSON dual view (confirmed live, 2026-08-08, ELITEA-2036)

`DefaultNode.jsx` renders BOTH the `custom` and `defaultType` node types
(`FlowEditor.jsx`'s `nodeTypes` map) — confirmed via source. For `custom`
specifically, the rendered fields are the EXACT same component tree
`BaseToolNode.jsx` uses for the Toolkit/MCP nodes: `ToolSelect` (Toolkit
select) → conditional `Tool` `SingleSelect` (absent from DOM until a
Toolkit with `selected_tools` is chosen) → `FlowEditorSelect.InputSelect` →
`FlowEditorSelect.OutputSelect` → `FlowEditorSettings.InputMapping`
(Type+Value per parameter, REQUIRED/OPTIONAL accordions once a Tool is
selected) → `FlowEditorSettings.CommonInterruptSettings` (Interrupt
before/after, Structured output). **Additionally**, Custom uniquely renders
`FlowEditorSettings.CustomNodeInput` at the bottom — a raw-JSON CodeMirror
view/editor of the node's own full YAML body (id/type/description/settings/
input_mapping/...), present on NO other node type in this suite. Same
always-expanded-inline pattern (no click-to-open) as every other node type.

- **Precondition case-text drift, same class as Toolkit/Router nodes.** The
  case ELITEA-2036 doesn't mention attaching a toolkit as a precondition,
  but "Type + Value for input mapping" is unreachable until a Toolkit (with
  `selected_tools`) is attached to TOOLS and selected in the node — same
  two-stage reveal already documented for ELITEA-2010 (Toolkit node) and
  ELITEA-2033 (Router node). Filed as a CLARIFICATION in the AFS, not a bug.
- **Zero testids existed on `DefaultNode.jsx`/`CustomNodeInput.jsx` before
  this session** — added a `TEST_ID_PREFIX_BY_NODE_TYPE` map (mirrors
  `BaseToolNode.jsx`'s, gated to `type === 'custom'`) wiring 8
  ALREADY-SUPPORTED props (`data-testid` on `ToolSelect`/`SingleSelect`,
  `dataTestId` on `InputSelect`/`OutputSelect`, 4 props on `InputMapping`, 2
  on `CommonInterruptSettings`) — zero shared-component changes needed. The
  raw-JSON view needed ONE new prop (`contentTestId`, forwarded to
  `Field.CodeMirrorEditor`'s pre-existing `contentTestId` support — same
  mechanism as `toolkit-raw-json-editor-content`/`skill-instructions-editor-content`
  elsewhere in the codebase). Full testid list: `test-specs/pipelines/l2_pipeline-custom-node-configuration_ELITEA-2036.md`
  § Concrete Handles.
- **Raw-JSON view reading convention**: `text_content()` on the
  `[data-testid="pipeline-custom-node-json-editor-content"]` `.cm-content`
  div, NOT `input_value()` — CodeMirror is not a native input/textarea,
  same convention as this project's other CodeMirror-content-reading code.

## State modifier node — inline config panel, zero Interrupt/Structured-output controls (confirmed live, 2026-08-08, ELITEA-2035)

Same always-expanded-inline pattern as every other node type. Node body, in
DOM order (confirmed via source, `StateModifierNode.jsx`): Trigger (only if
entry point) → **Jinja Template** (`AIAssistantInput`, `label="Jinja
Template"`, `name="template"`, `language="jinja"` — same "language prop ≠
CodeMirror" trap already documented 3× for this node family, plain textarea
confirmed live via `fill()`) → **Variables to clean** (`FlowEditorSelect.InputSelect`,
`inputFieldName="variables_to_clean"`) → **Input** (`FlowEditorSelect.InputSelect`,
`inputFieldName="input"`) → **Output** (`FlowEditorSelect.OutputSelect`,
`outputFieldName="output"`). Unlike Code/LLM, this node type has **NO**
`CommonInterruptSettings`/structured-output controls at all — confirmed via
source, no such import/usage in `StateModifierNode.jsx`.

- **"Variables to clean" is NOT an expandable/accordion section — case-text
  drift, filed as a CLARIFICATION.** It is the exact SAME
  `FlowEditorSelect.InputSelect` component as Input, just a different
  `inputFieldName`/`label` — a plain multi-select combobox, confirmed live
  via DOM inspection (no accordion, no expand icon, no collapsed state
  anywhere in the node body). The case's step 4 ("Expand 'Variables to
  clean' section (if applicable)") describes a mechanism that doesn't
  exist; the AFS instead asserts the field is present and openable as a
  dropdown. Same class of finding as the Decision-outputs/Routes
  clarifications already filed for sibling pipeline-node cases.
- **Zero testids anywhere inside the node body before this session**
  (confirmed via `git grep` for `state-modifier`/`state_modifier` on
  `automation/testids` — only non-UI hits: i18n prompt-template key, node
  type constant, icon import, palette color). Added this session:
  `pipeline-state-modifier-node-template-input` (on `AIAssistantInput`'s
  `inputProps`, same mechanism as the Decision AFS's Description field),
  `pipeline-state-modifier-node-variables-to-clean-select` /
  `-input-select` / `-output-select` (on the 3 `FlowEditorSelect` call
  sites' pre-existing `dataTestId` prop — zero new component code, matches
  the Code/Decision node testid-plumbing pattern exactly).
- **State variables are NOT built-in** — same pattern as every other node
  type in this family (Decision/Code/Router): a fresh pipeline's Input/
  Output combos on the State modifier node list only `input`/`messages`
  until custom vars are added via the `STATE` panel's "+" control. The
  case's own Test Data table names `issue_details` (Input) and
  `normalized_issue` (Output) as if pre-existing; live-confirmed neither is
  built-in.
- **Save + full page reload correctly persists** Jinja Template text,
  Input, and Output (confirmed live round-trip this session, zero console
  errors at every checkpoint). `PUT .../application/prompt_lib/{project}/{id}`
  returns 201, same as every other pipeline-node-configuration case in this
  family.
- Full flow, handles, and page-object gap list: `l2_pipeline-state-modifier-node-configuration_ELITEA-2035.md`.

## Save As Version (`agent-save-as-version-button` + dialog) works on Pipelines exactly like Agents (confirmed live, 2026-08-07, ELITEA-2002)

- **`ApplicationTabBar.jsx` (which renders `SaveNewVersionButton.jsx`) is shared by
  `EditPipeline.jsx` too** — same shared component `AgentDetailPage` already wires as
  `save_as_version_button`/`create_version_*` fields. Confirmed live end-to-end on a
  pipeline detail page: `agent-save-as-version-button` (enabled only when the form is
  dirty — e.g. after adding a canvas node via `pipeline-add-node-button` →
  `pipeline-add-node-menu-item-llm`), `agent-version-dialog-name-input`,
  `agent-version-dialog-save-button` (disabled while Name is empty), and the dynamic
  `[data-testid="version-option-{name}"]` (`VERSION_OPTION` template, same mechanism as
  `AgentDetailPage.VERSION_OPTION`) all resolve and behave identically to the Agents
  side. **`PipelineDetailPage` has none of these as fields yet** (only
  `version_selector`/`get_version_display()` for READING existed before this session) —
  zero `add-data-testid` work needed, purely a page-object-generator gap; port
  `AgentDetailPage`'s method shapes (`open_save_as_version_dialog()`,
  `confirm_new_version()`, `select_version_by_name()`, etc.) rather than reinventing.
- **Switching versions swaps canvas node state independently per version** — confirmed
  live: added 1 LLM node (`[data-testid^="rf__node-LLM"]`, sanctioned #579 ReactFlow
  wrapper handle) → Save As Version as `v1_test` → switch to `base` → 0 LLM nodes on
  canvas → switch back to `v1_test` → 1 LLM node again, config intact. No leakage either
  direction. The VERSION selector's URL also changes its version-id path segment
  (`/pipelines/all/{pipeline_id}/{version_id}`) on every switch/create — a second,
  independent signal beyond the trigger's `textContent`, cheap to assert alongside it.
- **`discard-button` IS live-wired on the Pipeline detail page** (present, correctly
  reflects dirty state) — a divergence from the digest's existing Agents note that this
  same testid is NOT rendered on `AgentDetailPage` (pre-existing, unrelated gap noted
  there, not this session's concern).
- **Seeding for a clean baseline**: `PipelineAPI.create_pipeline()` (zero-node, real
  empty `pipeline_settings`) loads with Save/Discard correctly **disabled** — confirmed
  live. Reconfirms the existing "Seeding gotcha" entry below (avoid
  `create_pipeline_with_nodes()` for any case needing a clean dirty-state baseline) from
  the version-flow angle specifically. **See the CORRECTION below on Save As Version's
  OWN enabled state — it does NOT join Save/Discard in this disabled baseline.**
  **CORRECTION (2026-08-07, ELITEA-2002 implementation) — "Save As Version enabled
  only when the form is dirty" (two bullets above, and the original "Save/Save-As-
  Version/Discard all correctly disabled" baseline claim just above) is FALSE for
  `agent-save-as-version-button`.** Re-verified live against a fresh zero-node pipeline
  (`ApplicationTabBar.jsx` source read + live DOM check, both agree): `ApplicationTabBar.jsx`
  renders `<SaveNewVersionButton onSuccess={onSuccess} />` with **no `disabled` prop
  passed at all** — `SaveNewVersionButton.jsx`'s own `disabled={isSavingNewVersion ||
  disabled}` therefore only ever reflects `isSavingNewVersion` (a mid-request state),
  never form dirtiness. Confirmed on a clean, zero-node pipeline immediately after
  navigate (and again after a 3s settle, to rule out a load-race): Save = disabled,
  Discard = disabled, **Save As Version = enabled**. This is a shared-component fact
  (`ApplicationTabBar.jsx` is the same component `AgentDetailPage` wires), not a
  pipeline-only quirk — `test_agent_save_as_version.py` never actually asserted the
  pre-edit disabled state either (only "enabled once dirty", which stays true — dirty
  is a superset of "always enabled", so that assertion doesn't contradict this). The
  correct clean-baseline assertion is: Save disabled, Discard disabled, **Save As
  Version enabled** (available at any time, not gated on dirtiness) — see
  `l2_create-pipeline-version_ELITEA-2002.md` for the corrected AFS text and
  `test_pipeline_create_version.py` for the corrected assertions.
- **Resolved during ELITEA-2002 implementation (2026-08-07) — version-switch needs the
  SAME reload-based belt-and-braces `select_version_by_name()` already uses on
  `AgentDetailPage`, not a simplified single-poll.** A single DOM-only poll (trigger
  text == target name AND Information-panel version-id == URL's version-id path
  segment) is NOT sufficient: the VERSION trigger's text can flip to the target name a
  beat before the Information panel's version-id / URL catch up, and that panel/URL
  pair can be transiently self-consistent (equal to EACH OTHER) while BOTH still show
  the PREVIOUS version's id — satisfying the same-value check without actually being on
  the target version yet (observed live: switching to "base" resolved the poll while
  `copy-version-id` and the URL segment both still read the just-created `v1_test`
  version's id). `PipelineDetailPage.select_version_by_name()` now ports the Agent
  method's full select+reload-cycle shape (2 attempts) to force a fresh server refetch,
  which clears it. Not the Agent-specific #614 Publish bug (different trigger flow —
  dropdown switch here, not Publish) but the same underlying staleness class.
- Full flow, handles, and page-object gap list: `l2_create-pipeline-version_ELITEA-2002.md`.

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
  **CORRECTION (2026-08-07, review fix round 1) — ITSELF CORRECTED (2026-08-07,
  review fix round 2):** round 1 claimed the original "renders TWO testids,
  `agent-version-selector-trigger` (outer wrapper) +
  `agent-version-selector-trigger-combobox` (inner combobox)" line was
  **fabricated**, based on a literal-string `git grep` for
  `agent-version-selector-trigger-combobox` returning zero hits on both
  `main` and `automation/testids`. **That "fabricated" verdict was itself
  wrong.** The `-combobox` variant IS real: `SingleSelect.jsx:661`
  (`../EliteaUI`, `automation/testids` ref) applies
  `SelectDisplayProps={dataTestId ? { 'data-testid': \`${dataTestId}-combobox\` } : undefined}`
  — a template literal MUI spreads onto the nested `role="combobox"` display
  div (a real, different DOM node from the outer wrapper `data-testid`).
  The literal-string grep is the wrong check for a template-constructed
  testid: the concatenated string never appears verbatim in source, so it
  ALWAYS greps to zero regardless of whether the mechanism exists — the
  correct check is `git grep -n -- "-combobox" <ref> -- src/`, which finds
  the `SelectDisplayProps` line. Ref-specific: **0 hits on `main`, 1 hit on
  `automation/testids`** (re-verified 2026-08-07 with a fresh `git fetch
  origin` on both refs) — `needs-adding to main` / `on-automation/testids
  only`, not non-existent.
  **The page-object choice is unaffected**: `version_selector` still uses
  the NO-suffix `agent-version-selector-trigger` testid, because it's
  confirmed on BOTH refs and DOM `textContent` on the outer wrapper already
  includes the inner `-combobox` div's text (returns "base" either way) —
  not because the suffixed variant doesn't exist. Full trace:
  `.agents/memory/test-automation-engineer/
  afs_testid_can_name_a_real_but_wrong_component.md` (ELITEA-2020 addenda).
  Shared component — same one Agents' detail page uses via
  `AgentDetailPage.version_selector_trigger` (`_surface.md` doesn't need a
  duplicate Agents entry; behavior is identical).
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

## Code node — inline config panel, single CODE section (confirmed live, 2026-08-08, ELITEA-2009)

Same always-expanded-inline pattern as every other node type. Shares the SAME
`SimpleLLMInputs`/`SimpleLLMInputItem` components as the LLM node
(ELITEA-2004), but with exactly ONE input-mapping key (`code`, not
system/task/chat_history) — `useCodeInputMapping.js`'s `getDefaultCodeInputMapping()`
returns `{ code: { type: 'fixed', value: '' } }`.

- **Node body, in DOM order**: Trigger (only if entry point) → **CODE**
  section (Type select + Value field) → **Input** (tool-agnostic state-var
  multi-select) → **Output** (same) → Interrupt before/after → Structured
  output. Matches the case text's step-3 list EXACTLY, no case-text drift on
  section presence — confirmed live via full node `innerText` dump.
- **CODE section's displayed heading is CSS-uppercased "Code", not a
  literal "CODE" string** — `Chip.HeadingChip label={capitalizeFirstChar(variableName.replaceAll('_',
  ' '))}` renders `variableName="code"` as `"Code"`; the visual all-caps is
  `text-transform` styling. Same pattern as every other `SimpleLLMInputItem`
  section heading (SYSTEM/TASK/CHAT HISTORY on the LLM node render "System"/
  "Task"/"Chat history" as literal text content too).
- **Value field is a plain MUI textarea (`#code-value`, stable unique DOM
  id), NOT CodeMirror/Monaco** — despite `SimpleLLMInputItem.jsx` passing
  `language="python"` when `variableName.toLowerCase() === 'code'` (and Type
  ∈ {fixed, fstring}). Confirmed via source (`AIAssistantInput.jsx`: `language`
  only feeds `detectedLanguage`/`specifiedLanguage`, consumed ONLY by the
  separate full-screen `AIAssistantModal`, never by the inline
  `Input.InputBase`/`StyledInputEnhancer` field itself) AND live DOM
  (`document.querySelector('#code-value').tagName === 'TEXTAREA'`). Same
  "language prop ≠ CodeMirror" trap already documented for the Router node's
  `Condition` field (`language="jinja"`) and the Decision node's
  `Description` field — a THIRD confirmed instance of this pattern in this
  node-type family. Multi-line text (embedded `\n`) types and reads back
  correctly via `press_sequentially()`/`.input_value()` — no CodeMirror
  per-line-scoping technique needed.
- **Output combobox uses the SAME `useInputOptions()` hook as Input** — both
  `InputSelect.jsx` and `OutputSelect.jsx` only ever list EXISTING pipeline
  state variables (`input`/`messages` on a fresh pipeline); neither is a
  freeform/creatable field. A case wanting to set Output to a
  not-yet-existing name (e.g. `result`) must first create it as a custom
  state variable via the `STATE` panel's "+" control
  (`open_state_panel()` + `add_state_variable(name)`, pre-existing methods
  from ELITEA-2034, reused unmodified) — confirmed live: the Output option
  list was `["input", "messages"]` before creating `result`, and
  `["input", "messages", "result"]` (with a live `select-option-result`)
  immediately after. Same "state vars not built-in" pattern already
  documented for the Decision node's Input select (ELITEA-2034) — this is
  now confirmed on THREE separate node types' Input/Output-family selects.
- **Interrupt before/after disabled-state**: Interrupt before is `disabled`
  while the Code node is the pipeline's entry point (true for the first node
  on an empty pipeline); Interrupt after is `disabled` while the node's
  `transition` is `END` (also true for a single freshly-added node with no
  outgoing edge) — identical `CommonInterruptSettings.jsx` logic already
  confirmed for every other node type in this family.
- **Testid gap — zero testids anywhere inside the node body before this
  session** (only `node-menu-menu-button` + the unconditional dynamic
  `pipeline-node-interrupt-before-toggle-{node_id}` + the entry-point
  Trigger select pre-existed). **Closed in this session**: `dataTestId`/
  `testIdsByKey`/`interruptAfterTestId`/`structuredOutputTestId` props wired
  at `CodeNode.jsx`'s call sites (all prop plumbing already existed
  generically, same mechanism ELITEA-2004 used for the LLM node) —
  `pipeline-code-node-type-select`, `pipeline-code-node-value`,
  `pipeline-code-node-input-select`, `pipeline-code-node-output-select`,
  `pipeline-code-node-interrupt-after-toggle`,
  `pipeline-code-node-structured-output-toggle`. Single commit
  `EliteaAI/EliteaUI@92fc6ec4` on `automation/testids` (awaiting human
  promotion to `main`). No further `add-data-testid` work needed for this
  node type's config fields.
- Save persists everything correctly; full-reload round-trip confirmed for
  CODE (Type+Value), Input, and Output. Save returns `PUT
  .../application/prompt_lib/{project}/{id}` → `201`. Zero console
  errors/warnings, zero failed requests, across every checkpoint.
- Full flow, handles, and page-object gap list:
  `l2_pipeline-code-node-configuration_ELITEA-2009.md`.

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

## Interrupt before/after toggles — implementation-time facts (ELITEA-2047, 2026-08-08)

**Resolved/added during ELITEA-2047 implementation:**

- **Two back-to-back `add_node()` calls place the second node fully
  overlapping the first** — ReactFlow spawns every freshly-added node at the
  SAME default canvas position (confirmed live via screenshot: Printer 1
  landed directly on top of Code 1, handles inaccessible to
  `connect_nodes()`'s bounding-box-based drag). Added
  `PipelineDetailPage.move_node(node_id, dx, dy)` — a generic drag-to-
  reposition helper (locates via the exact `rf__node-{id}` testid, new
  class constant `RF_NODE_TESTID`) — call it on the second node BEFORE
  `fit_view()` + `connect_nodes()` whenever two UI-added nodes need
  connecting. `dx=450, dy=100` (horizontal separation, clear of the taller
  Code node's expanded height) was sufficient; a smaller vertical-only
  offset (`dy=250`) was NOT (Code node's filled Value field makes it too
  tall).
- **A drag-created (pre-Save) edge's testid carries the ReactFlow
  source/target HANDLE ids as a suffix, with NO `---` separator** —
  confirmed live: `rf__edge-xy-edge__Code 1source-Printer 1target`, not the
  clean post-reload `rf__edge-xy-edge__Code 1---Printer 1` shape
  `EDGE_TESTID`/`wait_for_edge()` expect. Use `wait_for_edge_present()`
  (already existed for this exact reason — see its own Decision-node
  docstring) for any edge-existence wait BEFORE Save; `wait_for_edge()`
  only becomes valid after Save + a reload re-parses the pipeline from its
  saved YAML.
- **The "interrupt" edge-label pill (`CustomEdge.jsx`'s `EdgeLabelRenderer`
  `Typography`, rendering `data.label`) had NO testid** — this is APP JSX,
  not ReactFlow-internal (it just happens to render inside the `rf__wrapper`
  subtree via a portal), so the AFS's proposed #579 third-party exception
  did not apply. Added `data-testid={`pipeline-edge-label-${id}`}` (same
  `id` prop as the edge's own `EDGE_TESTID`, confirmed live to match 1:1),
  `EliteaAI/EliteaUI@94d190c9` on `automation/testids`. New
  `PipelineDetailPage.EDGE_LABEL` constant + `get_edge_label_locator()`.
  This same label renders route names on Router/Decision/HITL edges too —
  the testid is generic, not interrupt-specific.
- **The AFS's "Chat auto-posts a distinct 'How to proceed?...' hint message"
  claim does NOT reproduce** — re-checked on a fresh pipeline (2 independent
  test runs + a manual probe on the AFS's own exploration pipeline, id
  8159) with a further 10s settle wait beyond normal response
  stabilisation: the chat shows exactly 2 messages (trigger + Code 1's
  execution-result bubble), never a 3rd hint bubble. Not a defect — the
  pause mechanism itself (edge pill, locked config panel, run-in-progress
  node label) is unaffected and was NOT asserted via this hint text in the
  shipped test. See the AFS's own Step 6 for the full correction.
- **Config-panel "locked while paused" verification differs by field type**:
  the Value textarea and the Interrupt-after/Structured-output Switches
  expose a real native `disabled` HTML attribute (readable via
  `.is_disabled()`); the Type/Input/Output MUI Selects do NOT — they only
  gain the `Mui-disabled` CSS class (no `disabled`/`aria-disabled`
  attribute), so `.is_disabled()` on those returns a false negative. Assert
  via `"Mui-disabled" in locked_select.get_attribute("class")` instead
  (established pattern elsewhere in this suite, e.g.
  `test_pipeline_edge_deletion.py`'s `edge.get_attribute("class")` check).

## Delete pipeline version via three-dot menu — falls back to base cleanly; one benign console 400 (confirmed live, 2026-08-08, ELITEA-2003)

The VERSION-group "Delete" menu item (`delete-version-menuitem`, under the SAME
`agent-actions-menu-button` three-dot menu `delete_pipeline_via_menu()` already uses
for whole-pipeline delete — `ApplicationControls.jsx`, shared by Agents AND
Pipelines via `isFromPipeline`) deletes only the currently-open NON-base version and
correctly falls back the app to `base` — confirmed live end-to-end: create
`ver_to_delete` via Save As Version → open actions menu → click `delete-version-
menuitem` → `Modal.DeleteEntityModal` confirm dialog (`delete-confirm-dialog` /
`delete-confirm-message` / `delete-confirm-button` / `delete-confirm-cancel-button`)
→ click Delete → `DELETE .../version/prompt_lib/{project}/{pipeline}/{version}` →
`200` → VERSION dropdown no longer lists the deleted version, selector/URL/
Information-panel Version ID all agree on `base`'s original id.

- **`agent-actions-menu-button` is a REAL testid, on `origin/main` already** — the
  existing `PipelineDetailPage.open_actions_menu()` uses a bounding-box JS hack
  instead (`pipeline_detail_page.py:1606-1634`, predates this session) but doesn't
  need to: `DotMenu.jsx:354` renders `data-testid={id ? \`${id}-menu-button\` :
  undefined}` and `ApplicationControls.jsx:233` passes `id="agent-actions"` →
  `agent-actions-menu-button` resolves cleanly via Playwright's `getByTestId` (self-
  confirmed this session). **Bare-substring `git grep "actions-menu-button"` gives a
  FALSE NEGATIVE** here (it's a template literal, not a literal string) — verify by
  reading `DotMenu.jsx`'s template directly, same two-stage-grep caveat
  `workflow.md`'s closure-record section already documents for other testids.
- **The VERSION-group "Delete" item is DISABLED when the open version is `base`**
  (`ApplicationControls.jsx`'s `disableDelete`: gates on `default_version_id` match
  OR `name === LATEST_VERSION_NAME` i.e. `'base'`) — confirmed via source
  (`VersionDelete.jsx` also returns `null` outright for `type='button'` in that
  case). Not exercised this session (case always deletes a non-base version) — a
  future case could assert the disabled state directly.
- **Delete triggers a `check_version_in_use` GET first** (before the confirm dialog
  even renders): `{in_use: false}` (this session's case — a fresh, unreferenced
  version) shows the simple `Modal.DeleteEntityModal`; `{in_use: true}` would instead
  show `AgentDetails.VersionReplacementModal` (source-read only, not exercised) —
  worth a dedicated future case for the in-use/referenced-version path.
- **`delete-confirm-dialog`/`delete-confirm-message`/`delete-confirm-button`/
  `delete-confirm-cancel-button` (shared `DeleteEntityModal.jsx`) are on
  `automation/testids` only, NOT yet on `origin/main`** — confirmed via fresh
  `git fetch origin` + direct file read of `origin/main`'s `DeleteEntityModal.jsx`
  (only `delete-confirm-name-input` exists there; the other four attributes are
  testids-branch-only). Several ALREADY-MERGED page objects
  (`artifacts_page.py`, `secrets_page.py`, `chat_page.py`, `personal_tokens_page.py`,
  `mcp_form_page.py`, `admin_users_page.py`) already reference this same testid
  family for their OWN delete flows — this is pre-existing, not a gap introduced by
  this case. `delete-version-menuitem` itself (`ApplicationControls.jsx`'s
  `key: 'delete-version'` + `DotMenu.jsx`'s `testId: item.key` mechanism) IS already
  on `origin/main`, unlike the confirm-dialog testids.
- **Known defect, filed
  [EliteaAI/elitea-testing-public#1330](https://github.com/EliteaAI/elitea-testing-public/issues/1330):**
  after the `DELETE` succeeds, the client fires exactly one stale `GET` against the
  just-deleted version id (`400 {"error": "Application[{id}] version[{deleted_id}]
  not found"}`, visible in `browser_console_messages`) before settling on the
  fallback `base` version — deterministic 1/1 this session, benign (final UI state
  is always correct, no toast/visible error), but a genuine client-side state-
  sequencing race worth a soft-assert/comment in the implemented test rather than
  ignoring. Full network sequence + AFS:
  `test-specs/pipelines/l2_delete-pipeline-version-falls-back-to-base_ELITEA-2003.md`.

## Fork wizard — full live-confirmed handle map (ELITEA-2051, 2026-08-08)

Executed the FULL Fork flow (menu → wizard → target-project select → confirm →
complete → navigate → cleanup) for a Pipeline, not just menu-item visibility
(ELITEA-2049 only confirmed the menuitem exists). Source `Pipeline UI Testing`
(id 4, project `UI Testing`/400) → forked into `Private`/399 → new id `8243`.
Every Fork-wizard testid is **shared verbatim with the Agent-entity Fork flow**
(`ImportWizardModal`/`IWModal*` component family — same testids ELITEA-1893's
AFS documented for Agents, all reconfirmed live here for Pipelines): the
literal `agent-` prefix in these testids is naming tech debt, NOT
entity-scoped — do not expect a `pipeline-` variant for any of these:

| Element | Testid | Notes |
|---|---|---|
| Fork menuitem (entity-scoped, unlike the rest) | `pipeline-actions-fork-menuitem` | the ONE Fork-flow testid that IS entity-scoped (`ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map) |
| Fork wizard dialog (pre-fork / post-fork) | `agent-import-preview-dialog` / `agent-import-complete-dialog` | same container swaps testid in place |
| Wizard Project selector trigger | `agent-import-wizard-project-select-combobox` | shared with Agent Fork |
| Wizard project dropdown option | `select-option-{projectId}` | numeric, project-id-keyed |
| Main-entity preview name / toggle | `agent-import-preview-name` / `agent-import-preview-card-toggle` | toggle count() == number of entity cards |
| **Pipeline Diagram mermaid preview (Pipeline-only, no Agent equivalent)** | `chat-mermaid-diagram-svg-container` | showed "Diagram syntax error detected" for THIS session's source pipeline — not filed (not isolated as a general defect vs this pipeline's own data) — see AFS § Known Defects |
| Fork confirm button | `agent-fork-confirm-button` | same component regardless of entity — `IWModalForkButton.jsx`'s `forkFuncMap` has no `pipelines` key; pipelines are backend-classified as `agents`/`agent_type=pipeline`, dispatched via the same `forkAgent` mutation |
| Fork-complete list (entity-keyed) | `agent-import-complete-list-pipelines` | the **pipelines** variant of `agent-import-complete-list-{entityKey}` — confirms the family ELITEA-1893's AFS predicted but never itself confirmed |
| "Got it" button | `agent-import-complete-got-it-button` | drives navigation into the target project, onto the forked pipeline |
| **"Forked from" link — Pipelines LIST page card (Card view)** | **none — testid needed** | `<a aria-label="Forked from - Original pipeline" href=".../pipelines/all/{sourceId}/{sourceVersionId}?viewMode=owner">`, no `data-testid`. Source: `EliteaUI/src/components/Fork/IconLinkWithToolTip.jsx` (SHARED — also used by `DataTableNameCell`/`DataTableRow` for Table view, and by Agents/Skills list cards, not just Pipelines). **This is the element the case text's "dashboard card" step actually names** — do not confuse with the next row. |
| Forked-pipeline DETAIL page — "Forked from:" row (Information accordion) | none observed | inside `agent-information-section`; a SEPARATE, also-correct rendering of the same fact — NOT what the case's "dashboard card" step means |
| Network — fork data-fetch (menu click, before target selected) | `GET /elitea_core/export_import/prompt_lib/{sourceProject}/{sourceId}?fork=true&follow_version_ids={versionId}` → 200 | populates the wizard preview |
| Network — fork confirm | `POST /elitea_core/fork/prompt_lib/{targetProjectId}` → 201 | body: `{main_entity:'agents', applications:[...]}` |

**Known defect #570 (validateDOMNesting `<p>`-in-`<p>` on the Fork/Import Complete
dialog) reproduces for Pipeline Fork too** (1/1 this session) — same root cause,
same filed issue, not re-filed.

Full AFS: `test-specs/pipelines/l2_pipeline-fork-to-different-project_ELITEA-2051.md`.

## Pipelines dashboard — card "Pin to top" toggle, distinct from ELITEA-2049's detail-page menu item (confirmed live, 2026-08-08, ELITEA-2025)

**Two completely different "Pin to top" surfaces exist for Pipelines — do not
conflate them:**
1. **Dashboard card hover icon** (this entry) — a standalone `PinButton.jsx`
   icon button rendered directly on each `Card.jsx` (visible on hover or when
   already pinned), driven by the `usePin()` hook. **Has a working testid.**
2. **Pipeline detail page's three-dot Actions menu item** — a menu item inside
   `DotMenu.jsx`, driven by the SEPARATE `usePinMenu.hooks.jsx` hook, which has
   **no testid at all** (see `l2_pipeline-three-dot-menu-actions_ELITEA-2049.md`
   § Concrete Handles — that gap is real and still open; unrelated to this entry).

**Dashboard card testid, confirmed live**: `pipelineall-pin-toggle-button-{id}`
(`[data-testid]` on the `IconButton` inside `PinButton.jsx`) — on
`automation/testids` only (origin `EliteaAI/EliteaUI@b54bc281`, "[EL-1974] add
data-testid for credential pin/unpin controls"), **NOT yet on `main`**
(`git grep -- "pin-toggle-button" origin/main -- src/` → 0 hits this session).
The `pipelineall` prefix is a naming-convention leak, not a functional issue:
`PinButton.jsx`'s local `getPinTestIdSlug()` has no `isPipelineCard` branch, so
it falls through to `String(entityType).toLowerCase()` on
`ContentType.PipelineAll` (`'PipelineAll'` → `'pipelineall'`). Stable and
unique for the `/pipelines/all` dashboard specifically — **but a DIFFERENT
pipeline card view (Top/Latest/Trending/Draft/etc.) would get a DIFFERENT
testid for the SAME pipeline**, since none of those `ContentType.Pipeline*`
values route through `isPipelineCard` either. Untested by ELITEA-2025 (scoped
to `/pipelines/all` only); a future case touching another pipeline card view
should re-verify before assuming this same testid shape.

**Reorder timing is ASYMMETRIC — confirmed live, 3 pin/unpin cycles this
session**: pinning re-sorts the grid **instantly, client-side, no reload
needed**. Unpinning does **not** — the just-unpinned card stays at the top of
the grid (even though its own button label flips back to "Pin to top"
immediately) until a fresh navigate/re-fetch happens. This is the SAME shape
the merged `test_credential_pin_unpin.py` already codifies (its Step 7b
explicitly re-navigates before asserting the reverted order) — evidently a
platform-wide `usePin`/social-pin-endpoint behavior, not a pipeline-specific
one. Any future pin/unpin test on any entity should follow the same
re-navigate-before-asserting-reverted-order shape; asserting order immediately
after an unpin click will flakily fail against genuinely-correct behavior.

Network: `POST /api/v2/social/pin/prompt_lib/{project}/application/{id}` → `201`
(pin), `DELETE .../application/{id}` → `204` (unpin) — pipelines share the
`application` API path segment with agents (same as `PipelineAPI`'s own
docstring already notes for CRUD).

Full AFS: `test-specs/pipelines/l2_pipeline-dashboard-pin-to-top_ELITEA-2025.md`.
