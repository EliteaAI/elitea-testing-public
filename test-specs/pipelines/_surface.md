# Surface digest: Pipeline Flow Editor — LLM node fields & AI Assistant modal

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during GAP-007 analysis, 2026-07-24,
project `Bugs & Features`, local `http://localhost:5173`, pipeline
`GetUserName` id `690`/version `1251`).

## Reaching an LLM node's inline config fields

The Flow-view canvas (`[data-testid="rf__wrapper"]`, ReactFlow) renders each
node's config **always inline/expanded** on the card — no click-to-expand
step needed (same finding as ELITEA-1954 for MCP nodes). An LLM node
(`[data-testid="rf__node-{id}"]`, e.g. `rf__node-LLM 1`) shows **System**,
**Task**, **Chat History** sub-fields (each: a "Type" select + a "Value"
field), then `Input`/`Output` state-variable selects, then Toolkits/
Interrupt-before/Interrupt-after/Structured-output.

**Canvas is heavily zoomed-out by default** — a freshly-opened pipeline's
node bounding rect can be as small as ~52×72px, with content clipped by the
ReactFlow pane's `overflow`. Zoom in first: click `.react-flow__controls-zoomin`
~7× (no testid on ReactFlow's own controls — third-party widget, `rf__wrapper`
sanctioned-exception territory per `.agents/testing.md` §579), then
`.react-flow__controls-fitview` to re-center. A 1600×1000 viewport gives
enough room to see 2–3 stacked nodes without further panning.

## STATE drawer — zero testids

The "State" button (top-right of the canvas toolbar, opens/closes a right-side
drawer listing `input`/`messages`/custom vars with rename input, type badge
("Abc"), `+`/delete icons, and per-var enable toggles) has **no `data-testid`
anywhere** — button, drawer container, row inputs, icons, toggles, close (X)
button. Confirmed via full testid enumeration of the open drawer (zero hits).
If a case needs state seeded and doesn't specifically test the STATE-drawer
UI itself, **seed via the pipeline's own YAML/API PUT instead** — the `state:`
block shape is:
```yaml
state:
  input:
    type: str
  messages:
    type: list
  <custom_name>:
    type: str
    value: ''
```
(confirmed live via the Yaml-view tab). This avoids needing any STATE-drawer
testids for cases whose actual assertions live elsewhere (e.g. GAP-007's
f-string autocomplete). A future case that specifically exercises the STATE
drawer's own CRUD/toggle behavior is a separate coverage-gap scope and should
request its own testids then.

## Duplicate DOM id on every "Type" select — use testid, never the id

`SingleSelect.jsx` (`src/[fsd]/shared/ui/select/SingleSelect.jsx:657`)
defaults to `id={id || 'simple-select-' + label}` when no explicit `id` prop
is passed. `SimpleLLMInputItem.jsx` renders `<SingleSelect label="Type" .../>`
for System/Task/Chat-History without ever passing one, so **all three (and
any sibling node's own "Type" field) share the literal `id="simple-select-Type"`**
— confirmed `document.querySelectorAll('#simple-select-Type').length === 5`
on one canvas view. Filed `EliteaAI/elitea-testing-public#1006` (MINOR, not
blocking). **Never locate by this id in new code** — always testid + container
scope. `SingleSelect` already supports a `data-testid` prop (wires
`SelectDisplayProps={{'data-testid': \`${dataTestId}-combobox\`}}`) — same
mechanism already used for `pipeline-mcp-node-toolkit-select-combobox`
(ELITEA-1954/1955); a per-`variableName` dynamic testid
(`pipeline-llm-node-{variableName}-type-select`) is the correct shape if a
case needs to select this field's Type value directly rather than going
through `select-option-{value}` alone.

## AI Assistant modal (System/Task/Code/Printer/User-message fields, Type=F-String)

Opens via a fullscreen icon in the Value field's hover-toolbar
(`aria-label="AI Assistant"`, no testid — 3-icon toolbar order is
Copy / **AI Assistant** / Expand, only appears `showFullScreenAction &&
isHovering`). The modal (`role="dialog"`, no testid) hosts a CodeMirror
editor (`.cm-content`, no testid) preloaded with the field's current value,
plus a separate bottom "Describe your idea to generate or rewrite the value"
AI-generation prompt input (a DIFFERENT feature, not the f-string
autocomplete) and a Copy/Close icon pair top-right (`aria-label="Close"`, no
testid).

**All of these have a trivial existing wiring point — zero shared-component
edits needed, only a prop passed at the feature call site:**

| Element | File to touch | Prop already available |
|---|---|---|
| Modal root | `AIAssistantModal.jsx` → `<Modal.ExpandedViewerModal>` | `data-testid` (destructured as `dataTestId` in `ExpandedViewerModal.jsx:30`, applied line 136) |
| Editor content (`.cm-content`) | `AIAssistantCodeMirrorInput.jsx` → `<Field.CodeMirrorEditor>` | `contentTestId` (`CodeMirrorEditor.jsx:82`, applies via `EditorView.contentAttributes` — same mechanism as `skill-instructions-editor-content`/`toolkit-raw-json-editor-content`; **use the `-editor-content` suffix convention**, not a bare `-editor` guess) |
| Fullscreen/"AI Assistant" icon button | `SimpleLLMInputItem.jsx`'s `NodeFieldInput` `commonProps` | `fullScreenButtonProps` (threaded `InputBase.jsx` → `InputActionsToolbar.jsx`, spread onto the `IconButton`) |

## F-string autocomplete popper — mechanism confirmed fully working (one exception)

`useCodeMirrorFStringAutocomplete.hooks.js` (AI-Assistant/modal path) and
`useFStringInputAutocomplete.hooks.js` (plain inline-field path, no modal)
are TWO DIFFERENT HOOKS feeding the SAME shared `FStringAutocompletePopper`
UI component (`fstring-autocomplete/ui/FStringAutocompletePopper.jsx` — bare
`Popper`/`Paper`/`MenuList`/`MenuItem`, zero testids). Confirmed live,
end-to-end, on the modal path (GAP-007):

- Typing `{` opens the popper listing every current state variable, first
  option `Mui-selected` by default.
- Typing a prefix filters case-insensitively (`filterFStringAutocompleteOptions`).
- **ArrowUp/ArrowDown wrap at both ends** (`getNextAutocompleteIndex`) —
  confirmed both directions.
- **Enter** and **mouse click** both insert `{value}` with cursor after the
  closing brace, and close the popper. Mouse click additionally leaves the
  parent modal OPEN (confirmed) — this is the control case that isolates the
  next finding to the keyboard path specifically.
- **Escape is BROKEN**: closes the entire AI Assistant modal (not just the
  popper) and commits the in-progress value — filed `#1003` (MAJOR),
  reproduced in a fresh isolated session too. Root cause: the CodeMirror
  keymap's Escape handler doesn't stop the native keydown from bubbling to
  MUI's Modal-level Escape-to-close listener.
- Typing a literal `}` right after an auto-closed `{}` (cursor between) is a
  **type-over** of the auto-inserted brace (standard CodeMirror bracket
  matching, not part of this feature) and correctly closes the popper
  (`getFStringAutocompleteState` sees the closing brace already present).

**Typing-simulation gotcha:** simulate every character as its OWN keypress
(`page.keyboard.press()` per char / `press_sequentially()`), never a bulk
`fill()`/single-insert — a bulk insert of `"user"` after an auto-closed `{}`
landed as `{}user` (wrong) instead of `{user}` (correct) during exploration.
Per-character `press()` calls produced the correct result every time.

## Console — clean

Zero `error`-level console messages across the full GAP-007 session
(popper open/filter/navigate/insert/dismiss, both defect reproductions,
modal open/close cycles).

## LLM node — Input/Output selects and default STATE vars (ELITEA-2004, 2026-07-24)

Confirmed live: **`input` and `messages` are available in the Input/Output
comboboxes on ANY pipeline, even with NO explicit top-level `state:` block in
its YAML at all.** A pipeline created purely by clicking the canvas UI (no
custom state vars ever added via the STATE drawer or an API `state:` PUT) still
listed exactly these two options, each carrying the existing
`select-option-{value}` testid (`select-option-input`, `select-option-messages`
— same shared family already used everywhere else). These are implicit
built-ins (the user's message / the running conversation), not something a case
needs to seed — only CUSTOM additional vars need the `state:` YAML block (per
GAP-007's finding above).

`LLMNode.jsx` renders `<FlowEditorSelect.InputSelect id={id} label="Input" .../>`
and `<FlowEditorSelect.OutputSelect id={id} label="Output" .../>` — the SAME
shared components `BaseToolNode.jsx` uses for MCP nodes' Input/Output selects,
which already receive a `dataTestId` prop there
(`dataTestId={isMcpNode ? 'pipeline-mcp-node-input-select' : undefined}`,
`InputSelect.jsx`/`OutputSelect.jsx` line ~9 destructure + forward it straight
to the shared `Select.SingleSelect`'s `data-testid`). `LLMNode.jsx`'s own call
sites are simply missing this prop today (confirmed zero `data-testid` inside
an LLM node's DOM except ReactFlow's own `node-menu-menu-button`) — trivial
fix: `dataTestId="pipeline-llm-node-input-select"` /
`"pipeline-llm-node-output-select"`, no ternary needed since `LLMNode.jsx` is
already LLM-specific. Same mechanism yields a `-combobox` suffix testid
(carries `aria-expanded`) for free, exactly like
`pipeline-mcp-node-toolkit-select-combobox`.

Native id today (exploration-only, NOT policy-compliant, and NOT
multi-node-safe): `#simple-select-Input` / `#simple-select-Output` /
`#simple-select-Toolkits` (all label-derived, same root cause as the
duplicate `#simple-select-Type` bug `#1006` below).

## SYSTEM/TASK/CHAT HISTORY Value-field wiring point (ELITEA-2004, 2026-07-24)

Confirmed via source read (`SimpleLLMInputItem.jsx`'s `NodeFieldInput.
commonProps`, `id: `${variable}-value``) AND live DOM read: the three inline
Value fields render as real `<textarea>` elements with dev-only ids
`#system-value` / `#task-value` / `#chat_history-value` — directly editable
inline, no modal needed (the AI-Assistant fullscreen-icon/modal is an
OPTIONAL enhancement on top, only for `system`/`task`/`code`/`printer`/
`user_message` fields when Type is Fixed/F-String; Chat History never gets it).
**Zero `data-testid` on any of the three today.**

Wiring point (source-confirmed, no shared-component edits needed): add
`inputProps: {'data-testid': `pipeline-llm-node-${variableName}-value-input`}`
to `NodeFieldInput.commonProps` (`SimpleLLMInputItem.jsx` line ~48). This
flows through either branch (`AIAssistantInput`'s `...leftProps` spread, or
directly `Input.StyledInputEnhancer`) into `InputBase.jsx`'s
`slotProps={{ htmlInput: inputProps }}` (line ~267), which MUI applies
straight onto the native `<textarea>` — a first-class, already-supported
`InputBase` prop, confirmed by reading the full prop-flow chain.

## Duplicate `#simple-select-Type` id — re-confirmed live (ELITEA-2004, 2026-07-24)

Re-confirmed the `#1006` bug this session on a fresh single-LLM-node canvas:
`document.querySelectorAll('#simple-select-Type').length === 3` (System/Task/
Chat History). Still not fixed, still non-blocking, still routes around via
testid (once added) rather than the native id — see the Type-select wiring
point documented above (GAP-007 section) for the exact `add-data-testid` fix.

## Save/reload persistence — YAML view is a strong second verification source

For any case asserting "config persists after Save + reload", read BOTH the
Flow-view inline fields AND the `Yaml` tab (`pipeline-yaml-editor`/
`pipeline-yaml-lines`, pre-existing testids, `PipelineDetailPage.
get_yaml_content()` already implemented) — confirmed live this session that
both sources agree exactly after a hard reload (`input_mapping.system/task/
chat_history.type`/`.value`, top-level `input:`/`output:` arrays). This is
the SAME pattern the merged `test_yaml_content_reflects_pipeline` test
already uses; prefer it over scraping Input/Output multi-select chip text
(chips carry no testid at all — `SingleSelect.jsx`'s `renderMultipleValue`,
bare MUI `<Chip>`).

## Tooling gotcha cross-reference

`browser-verify`/`cdp.mjs`'s `--clear` flag and a synthetic Ctrl+A+Backspace do
NOT reliably clear these MUI multiline textareas (analyst-tooling-only, not a
product defect — full writeup:
`.agents/memory/qa-engineer/browser_verify_cdp_clear_backspace_does_not_clear_mui_textarea.md`).
Workaround used this session: a native-setter + `dispatchEvent(new
Event('input', {bubbles:true}))` via `evaluate()` to force-set the value
directly, confirmed to correctly trigger React's controlled-input `onChange`
(the app's own dirty-state indicator reacted correctly). Does not affect the
real Playwright/pytest suite (`fill()`/`press_sequentially()` are unaffected).

## Entry Point node — Trigger select & Webhook settings modal (ELITEA-2006, 2026-07-24)

**A fresh pipeline has NO entry-point node at all** — only an `End` node. Adding
ANY node via "Add node" (LLM used here) makes it the `entry_point`
(`entry_point: LLM 1` in YAML) the instant it's added — no separate
"make entrypoint" step for a single-node pipeline (`make_node_entrypoint()` is
for re-designating a DIFFERENT node in a multi-node pipeline). The Trigger
field (`Chat Message` / `Schedule` / `Webhook`) only renders on whichever node
IS the entry point (`NodeCard.jsx:42`, `isEntrypoint && <TriggerTypeSelector>`).
`pipeline_with_llm_id` fixture (`create_pipeline_with_llm_node`) already
produces byte-identical entry-point YAML — use it, skip manual node-adding.

**Trigger select — duplicate native id, route around via testid.** The Trigger
`SingleSelect` passes no `label` prop, so its native id is the literal
`id="simple-select-undefined"` — confirmed LIVE to collide with the sidebar's
"Project: Private" switcher (`document.querySelectorAll('#simple-select-undefined').length
=== 2`; clicking by this id landed on the PROJECT SWITCHER, not the Trigger
select). Filed `EliteaAI/elitea-testing-public#1009` (MINOR, distinct from the
already-filed `#1006` — different id, broader cross-feature collision).
**Never locate by this id** — use `[data-testid^="rf__node-"] [role="combobox"]`
scoped to the entry-point node's own testid container to click the closed
select, then `[data-testid="select-option-{chat_message|schedule|webhook}"]`
for the option (existing shared `SELECT_OPTION` family, confirmed working).

**Selecting "Webhook" fires a PUT immediately, before the modal even opens** —
`updateTrigger` (`PUT .../pipeline_trigger/prompt_lib/{projectId}/pipeline/{versionId}/trigger`)
generates the secret server-side first, THEN `PipelineWebhookModal` opens. The
Trigger select's own displayed label does NOT flip to "Webhook" until Apply is
clicked inside the modal — this is correct product behavior (source-confirmed
sequencing), not a defect; don't assert the label change at step-2 time.

**Trigger/webhook config is NOT in the pipeline's YAML at all** — it's a
separate server-side entity (`GET`/`PUT
.../pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger`,
`applications.js:857-876`). Confirmed live: after configuring + saving +
reloading, the `Yaml` tab still showed ONLY `entry_point`/`nodes` — zero
`trigger`/`webhook` keys anywhere. **A persistence check for this feature must
re-open the Trigger select or the webhook modal after reload — grepping the
YAML view (the pattern the LLM-node-fields digest section above recommends for
THOSE fields) will never see trigger state.**

**`PipelineWebhookModal` (Webhook settings dialog) has ZERO `data-testid`
anywhere** — confirmed via full dialog enumeration
(`[...dialog.querySelectorAll('[data-testid]')]` returned only MUI's own icon
component names like `ContentCopyIcon`, never a real app testid). Every
element — Webhook Type radios, URL field+copy, Secret field+eye+copy+refresh,
Example Request block+copy, Cancel/Apply — needs `add-data-testid`. ALL have a
trivial existing extension point, zero shared-component internals need
touching:
- `Checkbox.RadioButtonGroup` already supports `testId` → `${testId}-${value}`
  per item (`RadioButtonGroup.jsx:36-38`) — just pass `testId=` at the
  `PipelineWebhookModal.jsx` call site.
- `Modal.BaseModal` already supports `data-testid`/`titleTestId`/
  `closeButtonTestId` (`BaseModal.jsx:32-38`) — BUT `PipelineWebhookModal.jsx`
  uses a custom `actions={...}` render prop instead of `onConfirm`, so
  `cancelButtonTestId`/`confirmButtonTestId` do NOT apply to its Cancel/Apply
  buttons — those need their OWN direct `data-testid` prop (same-file native
  `<Button>` elements, trivial).
- The URL/Secret fields (`FormInput`, a thin `TextField` wrapper) accept
  `data-testid` as a plain forwarded prop (lands on the `MuiFormControl-root`,
  standard MUI unrecognized-prop forwarding) — sufficient to scope a nested
  `input` locator.
- Every icon button (copy ×3, eye, refresh) is a plain same-file `IconButton`
  — direct `data-testid` prop, no threading.

Full wiring points (exact line numbers, proposed names) are in
`test-specs/pipelines/l3_webhook-trigger-settings-modal_ELITEA-2006.md`'s
Concrete Handles table — don't re-derive, read that AFS first if implementing
this case.

**Tooling caveat (analyst-only, not a product issue):** `browser-verify`'s
`cdp.mjs` CLI spawns a fresh Node process per shell command — its
`consoleMessages`/`networkRequests` capture arrays are module-level and RESET
every invocation. A `get-console`/`get-network` call issued as a separate shell
command from the triggering action only sees a ~500ms freshly-opened window,
not real session history. Treat "zero errors" reads from THIS tool as
spot-checks, not exhaustive guarantees, unless the action and the read happen
inside the literal same `node cdp.mjs` process invocation (rare in practice
given the one-command-per-call shell workflow). Does not affect the real
Playwright/pytest suite (`page.on('console')`/`page.on('response')` listeners
run inside one long-lived context for the whole test).

## Entry Point node — Schedule settings modal internals (ELITEA-2007, 2026-07-24)

**`pipeline-trigger-select` landed on `automation/testids` mid-batch** — as of
this session it's confirmed present (added by the ELITEA-2006 implementer's
in-flight PR; observed live via Vite HMR). Reuse it, don't re-add. Its sibling
"Edit webhook settings" icon (`pipeline-trigger-webhook-edit-button`) also
landed; the analogous "Edit schedule" icon (`TriggerTypeSelector.jsx:312-320`,
`aria-label="Edit schedule"`, mounted only when `currentTriggerType ===
TRIGGER_TYPES.schedule`) is a separate, still-open gap — `testid needed:
pipeline-trigger-schedule-edit-button`.

**`PipelineScheduleModal.jsx` — zero app testids, but the Default-mode
period/day/hour/minute selects need ZERO `add-data-testid` work at all.** They
render via the third-party `react-js-cron` npm package (`^5.2.0`, the `<Cron>`
component), which ships its OWN stable, semantic testids baked into the
library: `select-period` ("Every"), `custom-select-week-days` ("on", only
present when period=`week`), `custom-select-hours`, `custom-select-minutes`.
These are as reliable as an app-owned testid (stable across the app's own
commits, only changes if the npm package version bumps) — treat them as
`on-main ✓ (third-party npm dependency)` provenance, not a #579 raw-handle
exception (no scoping/docstring discipline needed — they're proper
`data-testid` attributes, just library-owned rather than app-owned).

**Everything else in this modal is a genuine gap** (same shape as the sibling
Webhook modal, ELITEA-2005/2006's already-specced names below): modal root
(`Modal.BaseModal`, no `dataTestId` passed → `pipeline-schedule-modal`), close
button (`closeButtonTestId` unused → `pipeline-schedule-modal-close-button`),
the dynamic summary `Typography` (`cronState.message` →
`pipeline-schedule-modal-summary-text`), the Default/Advanced mode radio
(`Checkbox.RadioButtonGroup`, no `testId` passed →
`pipeline-schedule-mode-radio` → per-item `-default`/`-advanced`), the
Advanced-mode cron text input (`FormInput`, plain prop →
`pipeline-schedule-modal-cron-input`), and the custom Cancel/Apply buttons
(custom `actions` render prop bypasses `BaseModal`'s built-in
`cancelButtonTestId`/`confirmButtonTestId` — same reason as the Webhook modal
— → `pipeline-schedule-cancel-button` / `pipeline-schedule-apply-button`).

**`RadioButtonGroup.jsx`'s `testId` prop is STILL `automation/testids`-only,
not on `main`** as of this session (re-confirmed via a fresh
`git diff origin/main origin/automation/testids -- RadioButtonGroup.jsx`) —
same caveat ELITEA-2005/2006 already flagged for the Webhook Type radio; not a
blocker, just note the shared-dependency promotion gap in any closure record
that uses it.

**Default-mode hour/minute selects are ant-design MULTI-selects — the default
value is ADDED to, not replaced.** Clicking `09` on the hour select (default
`00`) produces `00,09`, not `09` — a second click on `00` is required to
deselect it. Leaving >1 value on either field while the other is narrow
triggers a real, correct validation message ("Frequency cannot be less than
every hour") — not a bug. **Scoping gotcha this surfaced**: antd `Select`
dropdown option-lists stay mounted (class-hidden) after closing rather than
unmounting, so a blind cross-page `.ant-select-item-option` text-match can hit
a STALE, already-closed list instead of the one that's actually open — always
scope to `.ant-select-dropdown:not(.ant-select-dropdown-hidden)` (or the
Playwright-equivalent "is this specific combobox `aria-expanded`" check)
before clicking an option.

**Escape closes the WHOLE Schedule modal, not a nested dropdown** — confirmed
live; pressing Escape while a period/hour/minute dropdown was open discarded
the entire modal (reverting the Trigger select to its pre-open value, since
Apply had not been clicked). Never use Escape as a "close this dropdown"
action inside this modal.

**Summary text omits the day-qualifier clause for the `day` period** — reads
plain `At HH:MM` (e.g. `At 09:30`), not `At HH:MM, every day`. The `week`
period's default DOES carry a qualifier (`At 00:00, only on Saturday`) since it
needs one to disambiguate. A TMS case asserting the literal string
`"At 09:30, every day"` is asserting stale text — CLARIFICATION filed:
`EliteaAI/elitea-testing-public#1013`.

**Advanced↔Default round-trip preserves values exactly** — switching to
Advanced shows the exact cron string matching the Default-mode state (e.g.
`30 9 * * *` for day/09:30), and switching back to Default restores the
identical dropdown values, confirmed live (no silent reset to the package's
own default cron).

**Already-filed `#694` (`BaseModal` `aria-labelledby`/id mismatch) reproduces
in this modal too** — same `BaseModal`-wide defect, not schedule-specific, not
re-filed.

## Entry Point node — all 3 Trigger types + Schedule modal + cross-node-type (ELITEA-2005, 2026-07-24)

Sibling findings to the ELITEA-2006 section above (same `TriggerTypeSelector.jsx`/
`NodeCard.jsx` surface) — read that section first for the Webhook-modal-specific
detail and the `pipeline-trigger-select` naming (reused here verbatim, confirmed
independently to the same name by this session too).

**Schedule modal — NOT previously documented here.** `PipelineScheduleModal.jsx`
defaults to "At 00:00, only on Saturday" (`Default` radio checked, `Every [week]
on [SAT] at [00]:[00]`, cron `0 0 * * 6`). Unlike Webhook, selecting "Schedule"
from the Trigger select does **NOT** auto-save before the modal opens — the
Trigger select still shows its PREVIOUS value behind the just-opened Schedule
modal, and only the modal's own Apply click persists `type=schedule` (confirmed
live, source-consistent with `handleTriggerTypeChange`'s `schedule` branch only
calling `setIsScheduleModalOpen(true)`, no `updateTrigger` call, unlike the
`webhook` branch). Zero testids anywhere in this modal either — same
`Modal.BaseModal`/custom-`actions`-button shape as `PipelineWebhookModal.jsx`,
same fix shape: `dataTestId` on the `Modal.BaseModal` call (~line 46, recommend
`pipeline-schedule-modal`), a bare `data-testid` on the summary
`<Typography>{cronState.message}</Typography>` (~line 54-59, recommend
`pipeline-schedule-modal-summary-text`), and a bare `data-testid` on the
same-file custom Apply `<Button>` (~line 116-124, recommend
`pipeline-schedule-apply-button`, matching the `-apply-button` suffix style
already used for `pipeline-webhook-apply-button`, not
`-modal-apply-button`).

**Toast-vs-display-update lag — confirmed asymmetric across all 3 types.**
The success toast (`"Webhook/Schedule configured successfully"`, `"Trigger
updated to Chat Message"`) fires BEFORE the Trigger select's own displayed text
updates, by roughly 1-2s, for the **Schedule Apply** and **direct
Chat-Message-reselect** flows (RTK-query cache-invalidation + refetch
round-trip) — confirmed by re-reading the select's text a couple of seconds
after the toast appeared and seeing it flip only then. The **Webhook** flow did
NOT show this lag in this session (likely because its own auto-save + refetch
already completed earlier, before Apply was even clicked — see the ELITEA-2006
section above). Automation implication: never assert the Trigger select's text
on the same tick as an Apply/select click for ANY of the 3 types — poll/retry
(Playwright's `expect(...).to_have_text(...)` handles this natively). Not a
product defect — final state was correct every time, only the visual-update
timing varies.

**Trigger UI works identically on a non-LLM entry-point node type.** Promoted a
`Code` node to entry point via the existing `make_node_entrypoint()` (three-dot
menu → "Make entrypoint") on a 2-real-node pipeline: the PREVIOUS entry-point
node's own Trigger field disappeared the instant it stopped being the entry
point (`NodeCard.jsx:42`'s `isEntrypoint &&` gate re-evaluated correctly), and
the `Code` node showed the identical Trigger field + all 3 options
(`select-option-chat_message`/`-schedule`/`-webhook`). No node-type-specific
gating found anywhere in `TriggerTypeSelector.jsx` beyond the already-documented
HITL/Printer/interrupts restriction (unrelated to node TYPE, related to node
CONTENT — see that case's own AFS Preconditions).

**Node-graph changes (add node / change entry point) need the pipeline's own
"Save" click — separate from the Trigger dropdown's own dedicated auto-save.**
Making a node the entry point and navigating away without clicking pipeline
Save silently discards that change (confirmed live this session — had to redo
the "Code node as entrypoint" step after an unrelated browser-instance restart
mid-session lost the unsaved state). Same as any other node-graph edit
(add/delete/rename) — not specific to the Trigger feature, not a defect. The
Trigger *value* itself persists via its own separate endpoint regardless of
whether pipeline Save is ever clicked (see ELITEA-2006 section's Network
Behavior) — the two persistence mechanisms are fully independent.

Full Concrete Handles table (exact line numbers, all 3 trigger types, both
modals, cross-referenced against ELITEA-2006's already-specced names) is in
`test-specs/pipelines/l3_entry-point-node-trigger-types_ELITEA-2005.md` — read
that AFS first if implementing either this case or ELITEA-2006, since the two
share several testids and should NOT be wired twice under different names.

## Toolkit node — zero testids today, same shared component as the MCP node (ELITEA-2010, 2026-07-24)

**`BaseToolNode.jsx` renders BOTH the MCP node (already testid'd, ELITEA-1954)
and the Toolkit node (this case) — but every testid prop is explicitly gated
to `isMcpNode` only** (`const isMcpNode = nodeType ===
FlowEditorConstants.PipelineNodeTypes.Mcp;`, line 37, with a code comment
stating the exclusion of other node types is intentional). Confirmed live via
full DOM enumeration inside `[data-id="Toolkit 1"]`: **zero** app testids on
Toolkit/Tool/Input/Output/Input-mapping/Interrupt/Structured-output — only
`node-menu-menu-button` and (incidentally, because this session's pipeline had
only one real node so it auto-became the entry point) `pipeline-trigger-select`/
`-combobox`. Full wiring points (exact line numbers, recommended names) are in
`test-specs/pipelines/l2_pipeline-toolkit-node-configuration-persistence_ELITEA-2010.md`'s
Concrete Handles table — read that AFS first before touching this component,
since a Toolkit-node testid pass and any future MCP-node rework will collide
on the same file.

**`rf__node-{id}` is free for every node type — ReactFlow's own convention,
not app code.** Confirmed live: a fresh Toolkit node got `data-testid="rf__node-Toolkit 1"`
with zero EliteaUI source touching that string anywhere (`grep -rn "rf__node"
src/` returns no hits) — it's `@xyflow/react`'s own built-in behavior, keyed by
the node's `id` prop. Don't flag this as a gap for any node type; it already
works.

**Two sub-gaps exist even within the already-testid'd MCP node — worth fixing
in the same pass as the Toolkit-node broadening:**
- `InputMapping.jsx`'s "Input mapping (optional N)" accordion heading has
  **no testid mechanism at all**, unlike its "required N" sibling
  (`requiredHeadingTestId` prop exists and is wired; no `optionalHeadingTestId`
  equivalent exists yet, for ANY node type). Needs a new prop, not a broadened
  gate.
- Each Input-mapping row's own "Type" select (`InputMappingItem.jsx` ~line
  318-327) has **no testid prop threaded at all** — unlike the sibling "Value"
  field 15 lines below it, which already has `dataTestId`. It also shares the
  literal duplicate `id="simple-select-Type"` already filed as
  `EliteaAI/elitea-testing-public#1006` for the LLM node's System/Task/Chat-History
  fields — confirmed this session that EVERY Input-mapping row's Type select
  (any node type) reproduces the identical id collision. Needs a new
  `typeTestIdPrefix`-style prop, mirroring `valueTestIdPrefix`'s existing shape.

**`CommonInterruptSettings.jsx` (Interrupt before/after, Structured output) has
zero testid support for ANY node type** — unlike everything else in
`BaseToolNode.jsx`, it isn't even `isMcpNode`-gated; it's simply never been
given a `data-testid` prop at all. Since it's already universally shared,
recommend adding GENERIC testids directly inside the component (not threaded
per-caller) — no test has asserted these fields yet for any node type, so this
is genuinely new ground, not a broadened gate.

**Multi-select gotcha — Input/Output tool-agnostic state-variable selects
accept MULTIPLE values (chips), confirmed live.** Clicking an option in the
popper ADDS it rather than replacing the current selection; clicking an
already-selected option in the (re-opened) popper toggles it back off.
Clicking the combobox's own displayed chip does NOT remove it (tried this
session — no-op). A stale snapshot ref reused across two different
combobox interactions can silently select the WRONG combobox's option list
(this session's own mistake: reusing an Input-select popper's option ref
after intending to open Output) — always re-snapshot between opening one
combobox and the next, never reuse a ref across them.
