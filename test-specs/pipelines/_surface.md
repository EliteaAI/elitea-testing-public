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
f-string autocomplete). **Update (ELITEA-2042, 2026-07-24): the STATE drawer's
own CRUD behavior is now fully explored — see the dedicated section below.**

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

**Status update (2026-07-24, redispatch ground-truth check): all of the above
is now DONE, not just planned.** ELITEA-2006's implementer added all 15
`PipelineWebhookModal` testids (the ones enumerated above + 3 fix-round
gap-fills: `pipeline-webhook-type-description`,
`pipeline-webhook-payload-format-description`,
`pipeline-webhook-secret-helper-text`) — confirmed present on
`automation/testids` via a fresh `git fetch origin` + `git grep`
(none yet on `main`). A future case touching this modal should REUSE these,
not re-run `add-data-testid` against it — check the AFS's Concrete Handles
table for the full list before assuming any element here still lacks a
testid.

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

**UPDATE (ELITEA-2004 review fix pass R1, 2026-07-24) — `CommonInterruptSettings.jsx`
now HAS testid support, added directly inside the shared component (not
per-caller), exactly as this entry recommended below.** The claim in the
paragraph immediately below ("zero testid support for ANY node type") is now
STALE — corrected here rather than left to mislead the next reader. Three
GENERIC testids landed via `EliteaAI/EliteaUI@1289e746` (on `automation/testids`
only, confirmed live — NOT yet on `main`): `pipeline-node-interrupt-before-switch`,
`pipeline-node-interrupt-after-switch`, `pipeline-node-structured-output-switch`.
Deliberately node-type-agnostic (not LLM-scoped) since the component is shared
across 8+ node types (LLM/MCP/Code/Agent/Subgraph/Decision/deprecated Loop+Tool)
— per `.agents/testing.md` § Locator policy, a shared component gets a generic
testid, not a caller-threaded `testId` prop, when no per-caller disambiguation
is actually needed. First consumer/asserter: `ELITEA-2004`'s
`test_pipeline_llm_node_configure_system_task_chat_history.py` (fix-round R1,
commit `58a7be27`) — Case Step 3's "Interrupt before/after"/"Structured output"
section-presence checks. Full AFS detail:
`test-specs/pipelines/l2_configure-llm-node-system-task-chat-history_ELITEA-2004.md`
§ Concrete Handles → "Review fix pass R1 additions".

<details><summary>Original entry (now partially superseded by the update above — kept for history)</summary>

`CommonInterruptSettings.jsx` (Interrupt before/after, Structured output) has
zero testid support for ANY node type — unlike everything else in
`BaseToolNode.jsx`, it isn't even `isMcpNode`-gated; it's simply never been
given a `data-testid` prop at all. Since it's already universally shared,
recommend adding GENERIC testids directly inside the component (not threaded
per-caller) — no test has asserted these fields yet for any node type, so this
is genuinely new ground, not a broadened gate.

</details>

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

## Node delete — menu + keyboard, edge-id quirks, focus gotcha (ELITEA-2018, 2026-07-24)

**Both activation paths work and reach the identical confirmation dialog.**
Three-dot menu (`node-menu-menu-button`, shared/non-unique across nodes —
scope inside the node's own `rf__node-{id}` container) → "Delete" menu item
(no testid today, `NodeCardHeader.jsx` `menuItems` `useMemo` ~lines 208-253,
3 mutually-exclusive branches all missing `key:` on their `{label:'Delete'}`
object — `DotMenu.jsx`'s existing `testId: item.key` → `${testId}-menuitem`
mechanism means a one-line `key: 'pipeline-node-delete'` fix on all 3, zero
shared-component edits). Selecting the node then pressing the OS **Delete**
key also opens the same dialog (`useDeleteItems.hooks.js`,
`useKeyPress(['Delete'], {target:null})` from `@xyflow/react` — reacts to
ReactFlow's own `.selected` node state, not a bespoke listener).

**Focus gotcha (cost a full debugging pass — read before writing a
keyboard-delete test).** A chat-message `<textarea>` has default page-load
focus. Clicking a node's card at its bounding-box CENTER (Playwright/CDP
default click point) often lands on an INNER field (a Type/Input Select)
instead of the node's own container — this both risks opening an unrelated
dropdown AND leaves `document.activeElement` on that inner field or the
still-focused textarea, silently swallowing a subsequent Delete keypress
before ReactFlow's global listener ever sees it (confirmed: zero effect,
no dialog). The fix: click the node's TITLE/NAME LABEL specifically
(`NodeCardHeader.jsx:280-286`, bare `<Typography>{inputtedName}</Typography>`,
no testid today — `testid needed: pipeline-node-title-label`, generic/shared
naming since `NodeCardHeader` is common to every node type). Confirmed live:
only after clicking THIS specific element did `document.activeElement`
become the node's own `[data-testid="rf__node-{id}"]` div (`tabindex="0"`),
and only then did Delete correctly open the dialog.

**Delete-confirmation dialog is the shared `DeleteEntityModal.jsx`
(`role="dialog"`), rendered from `FlowEditor.jsx:614` via
`useDeleteItems.hooks.js`'s `showDeleteConfirmDlg`/`onConfirmDelete`/
`onCancelDelete` — NOT via `DotMenu`'s own per-item `onConfirm`/`entityName`
mechanism** (the "Delete" menu item here is a plain `onClick: handleDelete`,
no `entityName` — a DIFFERENT, node-deletion-specific confirmation flow than
DotMenu's generic delete-dialog wiring used elsewhere). Its 4 field-level
testids (`delete-confirm-title`, `delete-confirm-message`,
`delete-confirm-cancel-button`, `delete-confirm-button`) are confirmed
**on-automation/testids only — NOT yet on `main`** (verified via
`git grep` against both `origin/main` and `origin/automation/testids`,
2026-07-24). The dialog ROOT itself does NOT carry its own
`data-testid="delete-confirm-dialog"` on the actual `[role="dialog"]`
element live, despite `DeleteEntityModal.jsx` passing it to
`Modal.BaseModal` → `<Dialog data-testid={dataTestId}>` — MUI's `Dialog`
applies it to an ancestor wrapper, not the inner `Paper` carrying
`role="dialog"`. Use `get_by_role("dialog")` to scope (only one dialog is
ever open at a time in this flow) plus the 4 field-level testids directly.

**Edge-id quirk — auto-derived (YAML/transition) edges use a DIFFERENT id
shape than user-dragged connections, and END's edge-endpoint id is NOT
`"END"`.** For a pipeline whose edges come from the YAML `entry_point`/
`transition` graph on load (as opposed to a user manually dragging a
connection, which is what the existing `edge_exists()` docstring's
`{source}{handle}-{target}{handle}` format documents), the actual testid
is `rf__edge-xy-edge__{source}---{target}` (triple-dash separator, no
handle suffix) — confirmed live: `rf__edge-xy-edge__LLM 1---Code 1`,
`rf__edge-xy-edge__Code 1---EliteAPipelineEnd`. **The END node's own
edge-endpoint id is the literal string `EliteAPipelineEnd`**, distinct from
its `data-id`/node-testid (`rf__node-END`) — confirmed by direct string
check: `"-END" not in "rf__edge-xy-edge__Code 1---EliteAPipelineEnd"`. The
existing `edge_exists()` page-object method's loose `.startswith()`+`in`
matching happens to still work for non-END targets by coincidence, but
**`edge_exists(source, "END")` returns a false negative** — call it with
`edge_exists(source, "EliteAPipelineEnd")` instead, or fix the method to
alias `"END"` internally (recommended, since every future case asserting
"connects to END" on a YAML-derived pipeline will hit this identical trap).

**Deleting a middle node auto-rewires the upstream node's `transition` to
the deleted node's own downstream target** — confirmed live and via YAML:
deleting `Code 1` (whose own `transition: END`) flipped `LLM 1.transition`
from `Code 1` to `END` directly, client-side, BEFORE any Save click. The
entire select → menu/keyboard → confirm → node-and-edge-removal →
transition-rewire sequence is 100% client-side; only the pipeline's own
Save button fires a network request (`PUT .../application/prompt_lib/...`,
`201`) that persists it.

**Canvas-timing gotcha, confirmed during implementation (fix round R1):**
the underlying YAML/`transition` model updates INSTANTLY on delete (assert
this via `switch_to_yaml_view()` / `get_yaml_content()` right after the
confirm click), but **ReactFlow's own rendered `edges` array does not
recompute until a Flow/YAML view remount or a full page reload** — so the
NEW auto-rewired live canvas edge (e.g. `LLM 1 → END` after deleting
`Code 1`) will NOT yet be visible/queryable via `edge_exists()` immediately
after the delete+confirm click, only after Save + reload. Any case on this
surface asserting "the rewired edge now exists" must split the assertion:
YAML-model check right after delete, live-canvas-edge check only after a
reload. Asserting the live edge too early is not a defect, just a premature
read of a `ReactFlow` internal that hasn't re-rendered yet.

**Ambient console warning, not a delete-node regression.** `[React Flow]:
It looks like you've created a new nodeTypes or edgeTypes object...` fires
repeatedly (level: `warning`, not `error`) on canvas re-renders throughout
this whole surface (confirmed both during and unrelated to delete-node
actions) — a pre-existing dev-mode ReactFlow message from un-memoized
`nodeTypes`/`edgeTypes` props somewhere upstream. Don't file it as a
regression for any case on this surface; filter console checks to
`level == "error"`.

## HITL node — Input/USER MESSAGE/ROUTER MAPPING/EDIT STATE KEY (ELITEA-2014, 2026-07-24)

**Config is always inline/expanded, same as every other node type** — no
click-to-open, no accordion-click needed even for the "Router mapping"
sub-section (confirmed expanded by default on a freshly-added node).

**Two real execution-order dependencies, both source-confirmed, neither a
defect** — get these backwards and the target field is simply disabled
(`aria-disabled="true"`), not broken:
1. The top-level **Input** select is disabled until **USER MESSAGE Type** is
   set to **F-String** (`HITLNode.jsx:58`,
   `isInputSelectDisabledByMessageType = userMessageType !== 'fstring'`) — a
   tooltip on the Input label states this explicitly. Configure USER MESSAGE
   Type before Input, not after (case ELITEA-2014's own step numbering has
   this backwards).
2. The **ROUTER MAPPING → EDIT** Route select is disabled until **EDIT STATE
   KEY** has a non-empty value (`HITLNode.jsx:244-248`). Configure EDIT STATE
   KEY before the EDIT route, not after (same backwards-numbering pattern in
   ELITEA-2014's case text).

**REJECT defaults to `END` out of the box** — confirmed live via a
pre-interaction DOM read (`aria-disabled=null`, displayed text already
`"END"`) AND via the YAML view showing `routes: {reject: END}` on a
freshly-added HITL node with zero prior edits. No click is strictly required
to satisfy this part of a case asking for "REJECT → END".

**EDIT's route options deliberately EXCLUDE `END`** (source-confirmed,
`HITLNode.jsx:49-52`, `editRouteOptions` filters out
`FlowEditorConstants.PipelineNodeTypes.End`) — APPROVE and REJECT both offer
every node INCLUDING END; EDIT never does. This is correct product behavior
(an Edit route must lead somewhere that continues the flow), not a bug —
don't file it, don't expect END in EDIT's option list.

**Same shared `SimpleLLMInputItem` component as the LLM node's System/Task/
Chat History fields — testid prefix hardcoded to `pipeline-llm-node-`
regardless of caller.** `HITLNode.jsx:208` renders its USER MESSAGE field via
`FlowEditorSettings.SimpleLLMInputItem` with `variableName="user_message"` —
the SAME component `SimpleLLMInputs.jsx` uses for the LLM node. Because the
testid template (`pipeline-llm-node-${variableName}-type-select` /
`-value-input`) lives INSIDE the shared component rather than being passed by
the caller, the HITL node's USER MESSAGE fields get testids literally named
`pipeline-llm-node-user_message-type-select` / `-value-input` — misleading
(HITL is not an LLM node) but still unique and usable (scoped inside
`rf__node-HITL 1`). Filed `EliteaAI/elitea-testing-public#1017` (MINOR,
non-blocking). These two testids exist on `automation/testids` only
(confirmed via a fresh `git fetch origin` + `git grep -F` for the literal
template string — present on `origin/automation/testids`, absent on
`origin/main`) — pending human promotion, same as the rest of ELITEA-2004's
work.

**Three gaps identified at first analysis — since ADDED by the implementer,
now on `automation/testids` only (2026-07-24 redispatch, re-confirmed via a
fresh `git fetch origin` + `git grep` AND a real pytest rerun — `1 passed in
27.21s`; NOT yet on `main`, `EliteaAI/EliteaUI@4ccf24ac` "add HITL node
testids (ELITEA-2014)"):**
- HITL's own **Input select** (top of panel) — native id was the LITERAL
  STRING `simple-select-[object Object]` (worse than the ordinary
  duplicate-id case: `HITLNode.jsx:196-201` passes a JSX element as the
  `label` prop, and `SingleSelect.jsx`'s `id={id || 'simple-select-' + label}`
  default coerces it to `"[object Object]"` via string concatenation). Now
  carries `dataTestId="pipeline-hitl-node-input-select"` via
  `FlowEditorSelect.InputSelect` at `HITLNode.jsx:204`.
- The 3 **ROUTER MAPPING Route selects** (APPROVE/EDIT/REJECT) — previously
  shared the literal duplicate id `simple-select-Route` (same root-cause
  family as `#1006`/`#1009`, not re-filed). Now carry a DYNAMIC per-action
  testid at `HITLNode.jsx:253`:
  `` data-testid={`pipeline-hitl-node-router-${action.value}-select`} ``
  (inside the `HITL_ACTIONS.map(action => ...)` loop) — exactly the shape
  originally recommended.
- The **EDIT STATE KEY Value select** — previously native id
  `simple-select-Value` (same root-cause family, not re-filed). Now carries
  `data-testid="pipeline-hitl-node-edit-state-key-select"` at
  `HITLNode.jsx:275`.

**Case status (2026-07-24 redispatch):** fully implemented — PR
`EliteaAI/elitea-testing-public#1026`, OPEN against `automation/base`,
locator-compliant (mechanical grep: zero raw handles, all class-level
`[data-testid=` template constants), independently re-run green twice
(implementer's own 26.57s + this redispatch's 27.21s). A board bounce
(`implementing` → `parked` "R2 cap exceeded" → `analysis`) most likely fired
against an earlier in-progress state before two documented implementer
debugging rounds landed (a `multiple=True` MUI-select Backdrop leak;
`edge_exists()`'s stale `handle_suffix` format assumption — see the
implementer's own MEMORY.md for both). Correct next action is a reviewer
dispatch against PR #1026, not another analyst/implementer round.

**Not already-covered by the merged PIPE-031** (`test_pipeline_nodes.py::
test_add_human_in_the_loop_node_and_connect_to_end`) — that spec only adds a
HITL node and drags a canvas edge from its approve handle to END
(`connect_nodes(..., source_handle="approve")`); it has zero USER MESSAGE,
EDIT STATE KEY, or EDIT-route coverage, and reaches `routes.approve` through
ReactFlow's `onConnect` rather than the panel's Route-select `onValueChange`.
A case exercising the panel fields is a distinct code path, not a duplicate.

Full Concrete Handles table (exact line numbers, all field wiring points) is
in `test-specs/pipelines/l2_hitl-node-config-router-mapping_ELITEA-2014.md` —
read that AFS first if implementing this case.

## Create-Pipeline form vs Detail-page form are DIFFERENT components (ELITEA-2021, 2026-07-24)

**The `/pipelines/create` form and the `/pipelines/all/{id}` detail-page form
are not the same component with different props — they're genuinely
different JSX trees**, confirmed by full-page-text dump (zero occurrences of
"Tools"/"Editor Notes"/"Information" pre-save) and by source:

- **Create** (`CreatePipeline.jsx` → `CreateAgentForm.jsx`,
  `src/[fsd]/features/agent/ui/agent-details/configurations/form/CreateAgentForm.jsx`,
  shared with Agent create via `entityType` prop) renders only: General
  (Name/Description/Tags) → Instructions (hidden for pipeline) → Variables →
  Welcome message → Chat starters → Advanced (Step limit). **No Tools
  section, no Editor Notes, no Information section exist on this form at
  all** — not collapsed, not lazy, genuinely absent from the JSX.
- **Detail/edit** (`PipelineConfigurationForm.jsx`, reached only after the
  first Save assigns the pipeline an id) additionally renders:
  `ApplicationTools` (Tools section — toolkit/MCP/agent/pipeline attach),
  `ApplicationEditorNotes` (Editor Notes), `ApplicationInformation`
  (Pipeline ID / Version ID / Trigger / embedded chat preview).

**Any case whose steps interleave toolkit-attach or editor-notes with
create-time fields (Name/Description/Tags/Welcome/Starters/Step-limit)
cannot be executed in the case's literal order** — this is case-text drift
(written against the steady-state detail-page layout), not a defect: the
split is a deliberate, working design (an entity needs an id before it can
own toolkit associations). Re-sequence: create-time fields → Save → detail-
page-only fields → Save again → reload. Full worked example:
`test-specs/pipelines/l2_create-pipeline-full-details_ELITEA-2021.md`.

### Confirmed testids on the Create-Pipeline form (live DOM enumeration)

All of: `agent-name-input`, `agent-description-input`, `agent-save-button`,
`agent-canvas-section-general`, `agent-form-icon-button`,
`agent-canvas-section-welcome-message`, `agent-welcome-message-input`,
`agent-conversation-starters-section`, `agent-canvas-section-chat-starters`,
`agent-conversation-starter-add` (+ `agent-conversation-starter-input` once a
starter row exists), `agent-canvas-section-advanced`, `agent-step-limit-input`.

**Provenance (verified `git fetch origin` + `git grep`, 2026-07-24):** all
on-main ✓ **except** `agent-canvas-section-advanced` and
`agent-step-limit-input`, which are on `automation/testids` only (awaiting
human promotion to `main`).

### Two former testid gaps — RESOLVED 2026-07-24 (`EliteaAI/EliteaUI@7709ad97`)

Both landed on `automation/testids` (awaiting human promotion to `main`) during
an ELITEA-2021 redispatch, after a fix-round left them wired live in the shared
`../EliteaUI` working tree but uncommitted (isolated implementer worktrees
structurally can't commit to a sibling repo — the analyst-slot testid-commit
authority per `.agents/workflow.md` closed the gap instead). Live-functional-
confirmed on the running dev server (typed a tag + Enter → chip rendered;
typed into Editor Notes → value held).

- **Tags combobox** (`ApplicationEditForm.jsx`/`CreateAgentForm.jsx` →
  `TagEditor.jsx` → `AutoCompleteDropDown.jsx`): now wires `inputTestId`/
  `chipTestId`/`getOptionTestId` (mirrors Skills' own `CreateSkillForm.jsx`
  `skill-tags-input`/`skill-tag-chip`/`skill-tag-option-{name}` pattern one
  prefix over) → `agent-tags-input` (wrapper, `data-testid`),
  `agent-tags-input-field` (real `<input>`), `agent-tag-chip` (committed
  chip), dynamic `agent-tag-option-{name}` (suggestion option — **source/
  commit-confirmed only, not yet live-functionally exercised** — no case has
  opened the suggestion dropdown itself, only the type-new-tag+Enter path).
- **Editor Notes section** (`ApplicationEditorNotes.jsx`, detail-page only):
  now has `agent-editor-notes-section` (accordion `testId:`, mirrors sibling
  `agent-canvas-section-advanced`) and `agent-editor-notes-input` (Notes
  textarea, via `inputProps` `data-testid`).

Both used identically by Agent AND Pipeline forms (same shared components).
Full detail + the original declared-improvisation naming rationale: the
ELITEA-2021 AFS's Concrete Handles section and its Redispatch confirmations.

### Step limit: non-obvious default + a clearing gotcha

The Step-limit field defaults to `25` (not empty) on a **fresh create form**.
Its `onKeyDown` handler enforces `MAX_STEP_LIMIT` char-by-char as you type, so
a clear that doesn't properly fire the controlled `onChange` (e.g. a raw
synthetic select-all+Backspace key-event pair, as opposed to a real
Playwright `.clear()`) leaves the stale `25` in place — typing `50` over it
then produces a corrupted-looking `255` (then blocks at `2550`, over
`MAX_STEP_LIMIT`) instead of a clean `50`. Always use Playwright's native
`.clear()`, never a manual two-keystroke simulation.

### Toolkit attach: shared-project churn, not a product defect

Attaching a toolkit via "+ Toolkit" → `toolkit-menu-item` popper selection
uses the exact same `PATCH .../tool/prompt_lib/{project}/{toolkit_id}` → 201
mechanism ELITEA-2010 already proved reliable end-to-end (attach → save →
reload, verified via both Flow-view and YAML). In a project whose only
available toolkits are OTHER parallel batch sessions' ephemeral
create/delete-churned artifact toolkits, an attach attempt can transiently
fail with a toast "No such toolkit with id {n}" (stale toolkit reference,
already deleted by a concurrent session) — confirmed non-reproducible against
a fresh attempt seconds later (a *different* transient toolkit attached
successfully first try). **Always use a dedicated fixture toolkit**
(`automation/fixtures/data_fixtures.py:495`'s `artifact_toolkit`, exactly as
ELITEA-2010 already established) for any case that needs a stable toolkit —
never rely on "whatever exists in the shared project" for assertions that
must be deterministic.

### Chat-starter label rendering quirk (cosmetic, not a bug)

`document.body.innerText` shows the Chat-starters field's label text
("Starter") **twice** once a starter row exists — confirmed cosmetic (a MUI
floating-label rendering artifact); the field's actual `.value` correctly
holds exactly one string. Assert on the `agent-conversation-starter-input`
element's `.value`, never on raw `innerText` occurrence counts, for this
field.

## "Add node" menu — exhaustive 11-type enumeration, zero testids (ELITEA-2030, 2026-07-24)

**The menu's node-type list is source-derived, not a fixed hardcoded array —
confirmed to be exactly 11 entries by tracing the filter, not just by
counting DOM nodes once.** `AddNodeMenu.jsx`'s `getVisibleNodeTypes()`
(`src/pages/Pipelines/Components/AddNodeMenu.jsx:23-28`) takes
`Object.keys(FlowEditorConstants.PipelineNodeTypes)` (20 KEYS: Tool, Agent,
Pipeline, Function, LLM, Decision, Condition, Loop, LoopFromTool, Router,
StateModifier, Toolkit, Mcp, Code, Printer, Hitl, Custom, Ghost, End, Default)
and filters out `DeprecatedConstants.DeprecatedOrInvisibleNode` — which is
built from `DeprecatedNodes` (Function, Condition, Pipeline, Loop,
LoopFromTool, Tool — all deprecated per `deprecated.constants.js:39-46`) plus
End, Ghost, Default (internal/structural, never user-addable). What survives:
**Agent, Code, Custom, Decision, Human-in-the-loop (Hitl), LLM, MCP, Printer,
Router, State modifier, Toolkit — exactly 11**, alphabetically sorted by
display label (`menuItems.sort((a,b) => a.label.toLowerCase()
.localeCompare(b.label.toLowerCase()))`, line 45), then split into two
`<Menu>` columns via `slice(0,6)`/`slice(6)` (left: Agent, Code, Custom,
Decision, Human-in-the-loop, LLM; right: MCP, Printer, Router, State
modifier, Toolkit). Confirmed live: `document.querySelectorAll('[role=menuitem]').length
=== 11`, texts exactly `["Agent","Code","Custom","Decision",
"Human-in-the-loop","LLM","MCP","Printer","Router","State modifier","Toolkit"]`
in that DOM order (both columns render sequentially in the DOM, left first).

**Zero `data-testid` anywhere in this component** — the trigger `IconButton`
(`AddNodeMenu.jsx:75-90`) has only a native `id="pipeline-add-node-menu-action"`
+ `aria-label="Add node"` (already-working `aria-expanded` toggle, reusable
as a state read once the button itself has a testid); the `<Menu
id="pipeline-add-node-menu">` root (line 91) has only a native id too; each
`<MenuItem>` in both column loops (lines 115-134, 137-156) has `key={item.type}`
(a React key, not a DOM attribute) and otherwise nothing. `item.type` is
already the exact internal enum slug needed for a dynamic testid family
(`agent`, `code`, `custom`, `decision`, `hitl`, `llm`, `mcp`, `printer`,
`router`, `state_modifier`, `toolkit`) — trivial one-line `data-testid`
additions on the `IconButton` + both `MenuItem` loops, zero shared-component
edits (this whole file is feature-local, not `src/components/shared`).
Confirmed via `git diff origin/main origin/automation/testids -- <file>` =
empty — no other in-flight case in this batch has touched this file.
Full wiring points + recommended testid names are in
`test-specs/pipelines/l2_add-node-menu-lists-types-adds-node-and-dismisses_ELITEA-2030.md`'s
Concrete Handles table — read that AFS first before adding testids here.

**Selecting a type adds the node with its config panel already open — no
separate expand step, consistent with every other node type already
documented above.** Confirmed live for LLM: the instant the node appears
(`rf__node-{id}` present, e.g. `rf__node-LLM 2`), its own text content
already contains "System"/"Task"/"Chat history" (the field-group labels) —
readable off the node's existing `rf__node-{id}` testid without needing any
per-field testid, for a case that only needs to prove the panel is *open*
(not edit its fields).

**Tooling gotcha — clicking a full-viewport invisible backdrop by its own
selector-computed bounding-box CENTER can silently land on a foreground popup
item instead of "outside."** MUI's `Menu`/`Popover` backdrop
(`.MuiBackdrop-root.MuiBackdrop-invisible`) is a real, clickable, full-viewport
div — but a naive `clickElement(".MuiBackdrop-root")`-style helper that
computes "the element's own bounding-box center" as the click coordinate will
compute the VIEWPORT'S center, which is frequently exactly where the smaller
popup `Paper` is anchored (painted on top of the backdrop at that same
screen position). The click's real hit-target at that pixel is the
foreground popup content, not the backdrop underneath it — confirmed this
session: this exact mistake closed the Add-node menu AND simultaneously
added an "Agent" node, because the backdrop's naive center coincided with
the "Agent" `MenuItem`. Verified via `document.elementFromPoint(x, y)` that
a point genuinely outside the popup `Paper`'s own `getBoundingClientRect()`
correctly resolves to the true backdrop and produces a clean dismiss (no
node added). **For any future case testing "click outside to dismiss a
popup/menu/dialog": pick a coordinate confirmed outside the popup's own
rect (or just prefer Escape when the case allows either), never a
selector-center click on the backdrop element itself.**

Full test steps + Concrete Handles table:
`test-specs/pipelines/l2_add-node-menu-lists-types-adds-node-and-dismisses_ELITEA-2030.md`.

## Save/Discard dirty-tracking — a normalizing Save is required after ANY API-crafted pipeline (ELITEA-2028, 2026-07-24)

**Every existing pipeline-creation API helper produces a "phantom dirty"
pipeline on first UI touch.** `PipelineAPI.create_pipeline_with_nodes()`,
`create_pipeline_with_llm_node()`, and a raw crafted payload all set
`pipeline_settings: {"nodes": [], "edges": []}` (empty visual-layout data).
The FIRST time the Flow (or Yaml) view renders for such a pipeline, the
client auto-computes real canvas positions that differ from the stored empty
array — and that diff ALONE flips Save/Discard from disabled to enabled,
with **zero actual content edit**. Confirmed via a controlled A/B:

- Raw-API pipeline, never touched via UI: Save/Discard **enabled** on the
  very first navigate; switching Flow→Yaml→Flow with no edits made no
  difference (already enabled either way) — this reproduces on
  `create_pipeline_with_nodes()`/`create_pipeline_with_llm_node()` too, since
  they share the identical empty-`pipeline_settings` shape.
- Same pipeline shape, but with ONE extra step — add nodes via the UI's own
  "+" button, then click **Save** once, then hard-reload: Save/Discard
  **disabled** on the next fresh navigate, and switching Flow⇄Yaml repeatedly
  with no edits correctly stayed disabled. Only a REAL content edit flipped
  it to enabled.

**Implication for any case that asserts a Save/Discard baseline** (started
disabled, becomes enabled after edit X): after creating the pipeline via any
API helper, perform ONE explicit `click_save()` / `save_and_wait_for_update()`
BEFORE the test's real steps begin, and assert `is_save_enabled() == False`
right after, as the test's own baseline check — otherwise "becomes enabled
after edit X" passes vacuously (it was already enabled beforehand for an
unrelated reason). **Not filed as a product defect** — the layout diff is a
real, if surprising, uncommitted change, and it only manifests via the
API-creation path, not the normal "create via UI" user flow.

## YAML editor — `pipeline-yaml-lines` testid is DEAD (0 live DOM matches, ELITEA-2028, 2026-07-24)

`PipelineDetailPage.yaml_lines` (testid `pipeline-yaml-lines`, used by
`get_yaml_content()` to preserve line breaks) matches **zero** elements live
— confirmed via `document.querySelectorAll('[data-testid="pipeline-yaml-lines"]').length
=== 0` on a rendered, populated Yaml view, and via `git grep` finding no
source anywhere (neither `main` nor `automation/testids`) that wires this
string onto CodeMirror's `.cm-line` nodes. `YamlCodeEditor.jsx` calls
`Field.CodeMirrorEditor` with no per-line testid prop at all — only
`contentTestId` (a single-node mechanism) exists on that shared component
today. **Not currently a blocker**: `get_yaml_content()` already silently
falls back to `yaml_editor.text_content()` whenever `yaml_lines.count() ==
0` (i.e. every time), so whole-YAML reads still work, just without
preserved line breaks — this is why the existing merged
`test_yaml_content_reflects_pipeline` test has never surfaced this (it only
checks substring presence in the concatenated text).

**For editing a specific line** (e.g. changing one node's `transition:`
value without touching others), do NOT rely on `self.yaml_lines` — use the
declared #579 improvisation instead, mirroring `mcp_form_page.py::
fill_raw_json_line()` exactly: scope `get_by_text(current_line_text,
exact=True)` inside the already-testid'd `yaml_editor` container, click →
`Home` → `Shift+End` → one `keyboard.type(new_line_text)` call. Confirmed
live end-to-end (ELITEA-2028): `Home`+`Shift+End` selects from the first
non-whitespace character to end-of-line (leading indentation is NOT
included in the selection — the replacement text should be just the
line's logical content, e.g. `"transition: LLM 1"`, not
`"    transition: LLM 1"`). **Multiple lines can share identical text**
(e.g. two different nodes both `"transition: END"`) — disambiguate via
`.last`/`.nth(k)` or by locating the node's own `"- id: {node_id}"` line
first and then the next `"transition:"` line after it, never assume
`get_by_text(...)` alone is unique.

## Ordinary nodes (LLM/Printer/Code/…) have NO in-panel "transition/routes" field — only HITL/Router do (ELITEA-2031, 2026-07-24)

**Confirmed by source AND live DOM enumeration: `LLMNode.jsx` and
`PrinterNode.jsx` render zero Transition/Route field anywhere** — the LLM
node's panel is exactly SYSTEM/TASK/CHAT HISTORY/Input/Output/Toolkits/
Interrupt-before/after/Structured-output, nothing else. A visible "Route"/
"Routes" **select** genuinely exists in the product (`RouteSelect.jsx`), but
only on **HITL** (Router mapping, ELITEA-2014) and **Router** node types —
NOT on ordinary flow-through nodes (LLM, Printer, Code, MCP, Toolkit, Agent).
Any case whose text implies "locate the transition/routes field in the
[LLM/Printer/etc.] node panel" is describing a UI element that doesn't exist
for that node type — this is case-text drift, not a defect (filed
`EliteaAI/elitea-testing-public#1031` for ELITEA-2031's instance).

**The real, correct mechanism for an ordinary node's transition is one of
two things, both confirmed live:**
1. **Canvas drag-connect** — drag from the source node's bottom/source
   handle to the target node's top/target handle (existing
   `PipelineDetailPage.connect_nodes(source_id, target_id)`). Client-side
   only, no network call; immediately updates BOTH the canvas edge AND the
   underlying YAML `transition:` value (confirmed via the Yaml-view tab
   re-read right after the drag).
2. **Direct YAML editing** — see the ELITEA-2028 section above (`transition:`
   line edit via the declared #579 CodeMirror-line pattern).

**Edge-testid shape CHANGES between drag-time and post-reload** — a load-
bearing gotcha for any test asserting `edge_exists()` at both points.
Confirmed live end-to-end (LLM 1 → Printer 1):
- **Immediately after the drag** (before Save): `rf__edge-xy-edge__LLM
  1source-Printer 1target` — the user-dragged shape
  (`{source}{handle}-{target}{handle}`, matching `edge_exists()`'s existing
  docstring).
- **After Save + hard reload**: the SAME logical edge now reads
  `rf__edge-xy-edge__LLM 1---Printer 1` — the YAML/transition-derived triple-
  dash shape (per the ELITEA-2018 digest section above), since post-reload
  ALL edges are re-parsed from the YAML `entry_point`/`transition` graph
  regardless of how they were originally created.
- **`edge_exists()`'s existing matching (`testid.startswith(expected_prefix)
  and f"-{target_id}" in testid`) already covers BOTH shapes transparently**
  — confirmed live, no page-object change needed. A test asserting the same
  edge both immediately-after-drag and after-reload can reuse the identical
  `edge_exists(source, target)` call across both points without caring which
  underlying testid shape is currently rendered.

**Deleting/replacing a node's transition correctly removes the OLD edge, not
just adds the new one** — confirmed live (LLM 1's `END` edge disappeared the
instant the drag to Printer 1 landed; `Printer 1`'s own untouched `END` edge
was unaffected) — same "old edge gone, not merely superseded" behavior
ELITEA-2028 already confirmed for the YAML-edit path, now also confirmed for
the canvas-drag path.

Full Concrete Handles + Coverage Map are in
`test-specs/pipelines/l2_pipeline-edge-creation-between-nodes_ELITEA-2031.md`
— read that AFS first if implementing this case; it needs zero new testids
and zero new page-object code (every method it uses is already merged).

## Testid provenance — two view-toggle testids are FALSE NEGATIVES under literal `git grep` (ELITEA-2028, 2026-07-24)

`pipeline-yaml-view` and `pipeline-flow-view` (the Yaml/Flow toggle buttons)
both read as "not found on main" under a literal-string `git grep`, even
though they work live and are used by already-merged tests. Root cause:
`src/components/GroupedButton.jsx:57` builds the testid at RUNTIME via a
template — `` data-testid={item.testid || `pipeline-${item.value}-view`} ``
— so the literal string `"pipeline-yaml-view"` never appears anywhere in
source; it's assembled from `"pipeline-"` + a variable + `"-view"`. When a
provenance grep comes back empty for a testid you've confirmed working
live, check whether the constructing component builds it from a template
before concluding it's missing — this is the same class of gotcha
`workflow.md`'s "two-stage grep pattern" note already covers for prop
indirection, just one layer more indirect (multi-fragment template, not a
single forwarded prop).

## YAML-editor keystroke → Flow-view sync has a real 30ms Redux debounce race (ELITEA-2028 implementer exploration, 2026-07-24)

**Editing pipeline YAML via keyboard and immediately switching to Flow view can
show the PRE-edit edges — a genuine client-side timing race, not a flaky
test.** Confirmed during implementation of the `edit_node_transition_in_yaml()`
method (added for this case): the first automated run failed at the Flow-view
edge assertion (`edge_exists("Code 1", "LLM 1")` → `False`) even though the
immediately-preceding `get_yaml_content()` re-read already showed the edited
`transition: LLM 1` line.

**Root cause (traced in `../EliteaUI/src`):**
- `src/[fsd]/shared/lib/hooks/useCodeMirror.hooks.js::onInputHandler` debounces
  `notifyChange` (→ `setYamlCode` → Redux `state.pipeline.yamlCode`) by
  **30ms** after the last keystroke via `setTimeout`.
- `src/pages/Pipelines/Components/EditorPanel.jsx::onSelectChatMode` (the
  Flow/Yaml toggle's own handler) reads `yamlCode` from a `useCallback`
  closure current only as of the LAST RENDER before the click, and only calls
  `onParseCodeToJson(yamlCode)` (which recomputes the Flow-view node/edge
  layout) when switching TO Flow mode.
- If the toggle click fires before the 30ms debounce flushes AND before React
  re-renders with the updated closure, the Flow view re-parses the STALE
  (pre-edit) YAML string. A raw DOM read of the editor's text
  (`get_yaml_content()`) is unaffected — it reads the CodeMirror DOM directly,
  which updates every keystroke, independent of the debounced Redux dispatch.
  That's why the YAML-content assertion passed while the Flow-view assertion
  failed on the identical run.

**Fix — a condition-based wait, not a network wait (this surface's edits are
100% client-side; see the ELITEA-2028 AFS's Network Behavior section for the
full "no network call, but a client-side race exists" distinction):**
`PipelineDetailPage.edit_node_transition_in_yaml()` polls the Save button's own
`disabled` attribute (`page.wait_for_function("(el) => el && !el.disabled",
arg=self.save_button.element_handle())`) after the `keyboard.type(...)` call,
before returning. The Save button's enabled state is driven by the SAME Redux
`yamlCode`-vs-initial diff (`useIsPipelineYamlCodeDirty.js`), so polling it is a
real app-visible signal that the edit has landed — not a blind sleep, and
robust to the debounce window being longer/shorter than any fixed guess.

**Takeaway for any future case that edits pipeline YAML then immediately reads
view-derived state (Flow-view canvas, or anything else keyed off parsed
`yamlCode`):** never switch views / read derived state in the same "breath" as
a keyboard edit to this CodeMirror instance — wait on an app-visible signal
driven by the same Redux slice first (Save-button state is the cheapest one
already exposed via an existing page-object method). Full root-cause writeup:
`.agents/memory/test-automation-engineer/pipeline_yaml_editor_onchange_debounce_races_flow_view_toggle.md`.

## Router node — Condition/Routes/Input/Default-output, and ReactFlow edge-testid format (ELITEA-2033, 2026-07-24)

**Config is always inline/expanded, same as every other node type.** Fresh
`Router` node (`RouterNode.jsx`) shows Condition (Jinja textarea), Routes
(multi-select combobox), Input (single-select combobox), Default output
(single-select dropdown) immediately — zero click-to-open. Zero
`data-testid` anywhere in the node today; full wiring points (all four
fields have a trivial existing extension point, no shared-component
internals changes needed) are in
`test-specs/pipelines/l2_router-node-configuration-persistence_ELITEA-2033.md`'s
Concrete Handles table — read that AFS first before adding testids here.

**Routes/Default-output options are OTHER EXISTING NODE IDS, not free
text.** `useNodeOptions(nodeFilter, addEndNode)` (shared hook, also used by
HITL's route selects) maps `(yamlJsonObject.nodes || []).filter(nodeFilter)`
to `{label: node.id, value: node.id}` and optionally appends
`{label:'END', value:'END'}`. A case whose test data reads "Routes: approve,
reject" needs those as REAL node ids already present in the pipeline (e.g.
via `PipelineAPI.create_pipeline_with_nodes()` with literal `id: "approve"`/
`id: "reject"` — confirmed live that arbitrary non-type-prefixed ids are
accepted with no validation error), not typed strings in a text field.

**Default output's visual default ("END") is a DISPLAY-ONLY fallback,
distinct from the persisted value — same family as HITL's REJECT default
(ELITEA-2014), but with a sharper consequence here.** `default_output_node =
yamlNode?.default_output || 'END'` makes the field SHOW "END" the instant a
Router node is added, with zero interaction. But a freshly-added,
never-touched node's YAML has **no `default_output` key at all**, and **no
canvas edge** renders to END until the field is explicitly (re-)selected —
confirmed via a before/after YAML diff. Any case asserting "Default output
is END" must perform the explicit select-interaction and assert BOTH the
YAML key and the edge, not just the visual display (which would pass
vacuously even if persistence were broken).

**Edge-testid format has a genuine per-edge-kind quirk that breaks a naive
`edge_exists(..., handle_suffix=...)` call.** ReactFlow's rendered edge
testid is `rf__edge-xy-edge__{edge.id}` where `edge.id` is app-constructed
(`EDGE_PREFIX = 'xy-edge__'`, `flowEditor.constants.js`):
- **Routes edges** (from the shared Routes multi-select): `edge.id =
  ${id}---${value}` — e.g. `rf__edge-xy-edge__Router 1---Printer 1`.
  **Triple-dash, NO handle suffix embedded** even though the underlying
  `sourceHandle` state value IS the shared `routerNode_routes` string for
  every route.
- **Default-output edge**: `edge.id = ${id}default_output---${value}` — e.g.
  `rf__edge-xy-edge__Router 1default_output---END`. Handle name embedded
  directly before the triple-dash.

`PipelineDetailPage.edge_exists(source_id, target_id, handle_suffix=None)`
builds its handle-aware prefix as `f"...{source_id}{handle_suffix}-
{target_id}"` (SINGLE dash before target) when `handle_suffix` is given —
this does NOT match either Router edge kind's actual triple-dash format.
**Call `edge_exists(router_id, target_id)` WITHOUT `handle_suffix` for
BOTH Router edge kinds** — the fallback branch (`expected_prefix =
f"...{source_id}"` + `f"-{target_id}" in testid` substring check) correctly
matches both, confirmed live. This is a usage gotcha specific to Router's
edge-id shape (the helper was originally designed against HITL's
single-dash format), not a bug in the helper itemself.

**Synthetic-vs-real-click hygiene (transient anomaly, did NOT survive the
pristine-repro gate — not filed as a defect).** One interaction sequence
that probed with a synthetic `page.evaluate("el => el.click()")`
immediately followed by a real click on the SAME Default-output combobox
produced `default_output: ''` (empty string) instead of `'END'`, with no
edge created. Re-tested with a single clean real-click-only sequence
(open → click "END") and it worked correctly, twice. Do not mix synthetic
JS-click probes with real Playwright clicks on the same MUI `Select`
trigger within one interaction — use one clean path per select.

**Native id gotchas — same root-cause family as `#1006`/`#1009`, not
re-filed.** Router's Input select shares the literal native id
`simple-select-Input` with the LLM/MCP node's own Input select (cross-node-
type collision); Default output's native id is `simple-select-undefined`
(worse variant: `RouterNode.jsx` passes `labelNode={<Chip.HeadingChip
label="Default output" />}` instead of a plain `label` string, so
`SingleSelect.jsx`'s `id={id || 'simple-select-' + label}` default coerces
the missing `label` to the literal string `"undefined"`). Never locate by
either — testid-only once added.

**Existing suite coverage check:** `tests/api/export_import/
test_export_import_pipelines.py` has its own `_router_node()` helper, but
it only exercises API-level export/import YAML round-tripping of an
already-constructed Router node — it never touches the Flow-editor UI
panel fields this case configures. `tests/ui/pipelines/
test_pipeline_advanced.py`'s docstring claims Router-node-addition coverage
was "consolidated into `test_pipeline_nodes.py`" — confirmed this is STALE
documentation: `test_pipeline_nodes.py` contains exactly one test (HITL→END
connect-via-drag) and zero mentions of Router at all. **No existing merged
spec covers the Router node's panel-driven Condition/Routes/Input/Default-
output configuration** — `ready-for-automation`, not `already-covered`/
`extend-existing`.

**Renaming a UI-added node is a fragile detour for pre-seeding named route
targets — use the API instead.** `edit_node_name()`'s double-click-to-rename
flow works (confirmed on other cases), but nodes added via the "+" menu get
TYPE-prefixed default names (`Printer 1`, `Printer 2`, …), and a
transient/HMR-session artifact was observed where a node added just before
this session's dev-server picked up an unrelated concurrent `add-data-testid`
commit (`pipeline-node-title-label`, ELITEA-2018) rendered its name-label
WITHOUT that testid (stale Fast-Refresh instance) while a later-added
sibling node had it correctly — not a reproducible product defect (would
need a fresh page load to isolate cleanly, out of scope here), but a good
reason to prefer `PipelineAPI.create_pipeline_with_nodes()` with literal
target ids over a UI rename dance when a case's test data names specific
route targets.

## STATE drawer — full CRUD confirmed live, comprehensive testid gap (ELITEA-2042, 2026-07-24)

Supersedes the GAP-007 stub above (which only confirmed the drawer's zero-
testid status at a glance). This session drove the drawer's own add/type-
select/save/persist/combobox-availability flow end-to-end, plus a delete, and
read every component's source (`src/[fsd]/features/pipelines/flow-editor/ui/
state/*.jsx`) for exact wiring points.

**Toolbar toggle → drawer, structure.** The "State" toolbar button (plain
text "State", sibling to the already-testid'd `pipeline-flow-view`/
`pipeline-yaml-view`/`pipeline-add-node-button`) has **no `data-testid`, no
`aria-label`**. It opens a `position: absolute; right: 0` drawer
(`StateDrawer.jsx`) with a "STATE" heading, a close (X) `IconButton` (no
testid, no aria-label), and a `StateVariableList`. **Zero testids anywhere in
this entire feature** — confirmed via source read of all 9 component files
(`StateDrawer`, `StateVariableList`, `StateVariableItem`,
`StateVariableItemActions`, `StateTypeSelector`, `StateVariableIconButton`,
`StateVariableDefaultValue`, `StateVariableTextField`; `StateVariableTable`/
`RunStateDialog` are a different, unrelated feature — the Run-history state
viewer, not this drawer).

**Default vars (`input`/`messages`) are structurally un-renameable/
undeletable, not just policy-blocked.** They render as static `<p>` text
(never an `<input>` — `StateVariableItem.jsx`'s `handleStartEdit` is gated
`!isDefault`) with only a `MuiSwitch` toggle; `StateVariableItemActions.jsx`'s
`showToggle` branch returns EARLY for default rows, skipping the type-
selector/default-value/delete controls entirely — there is no click target
that could rename or delete them. Custom rows are the mirror image: type-
selector + default-value + delete controls, but NO toggle (`showToggle =
!isCreateMode && isDefault`).

**Add-variable flow, confirmed live end-to-end:** click "+ Context"
(`StateVariableList.jsx:205-217`, plain `Button`, no testid) → a NEW
`StateVariableItem` mounts in `Create` mode: autofocused `TextField
placeholder="name"` + a **disabled** type-selector icon + an "Add default
value (optional)" icon + a delete/cancel icon. Type a name, then **commit via
`Enter`** (confirmed reliable, twice) — this fires the `TextField`'s
`onBlur`, which calls `onAddState(name, 'str')`; on success the row becomes a
committed list entry and the type-selector button's `disabled` state clears.
**Sequencing gotcha**: the type-selector is `disabled` (confirmed via
`element.disabled === true` AND `aria-label=""` vs. the enabled state's real
`aria-label="Select data type"`) until the name is committed —
`StateVariableItemActions.jsx`'s `disableTypeSelector={isCreateMode ||
!editable}`. Clicking it before committing the name is a silent no-op; always
commit first.

**Type selector — real accessible name today, but not disambiguating across
multiple custom vars.** `button[aria-label="Select data type"]`
(`StateVariableIconButton.jsx`'s `Tooltip title`) opens a plain MUI `Menu`
with exactly 4 `role="menuitem"` entries in order: **String** (Abc icon,
`Mui-selected` by default), **Number** (`#`), **List**, **Json** (`{}`) —
confirmed live, screenshot evidence this session. The aria-label is shared
across every row (not unique once >1 custom var exists) — fine for a
single-custom-var case, needs a testid for disambiguation otherwise.

**Delete confirmed working correctly, scoped to the row.** Added a throwaway
`tabtest_var`, then clicked its own delete `IconButton`
(`StateVariableItemActions.jsx:64-77`, no testid) — it alone disappeared from
the list; `input`/`messages`/the other custom var were unaffected. Confirms
the per-row scoping is correct at the DOM level, not just in source.

**Persistence — exact YAML shape confirmed, survives a fresh-profile hard
reload.** Saving a pipeline with one custom var `custom_output` (String,
default value) produces:
```yaml
state:
  custom_output:
    type: str
    value: ''
  input:
    type: str
  messages:
    type: list
```
Re-confirmed after killing the browser entirely and re-navigating in a
brand-new, isolated Chrome profile (not just a same-session reload) — this
rules out "looks persisted because the client never forgot it" as a false
positive. Zero `error`-level console messages at every checkpoint
(`get-console --level error` → 0 hits, checked 3 times across the whole
flow).

**Custom vars join the Input/Output combobox option set immediately.**
Confirmed live on a freshly-added LLM node: opening its Input select
(`#simple-select-Input`, native id, exploration-only — the testid gap for
this trigger is already fully specced in ELITEA-2004's AFS, don't re-derive)
listed `select-option-input`, `select-option-messages`,
`select-option-custom_output` — same for Output. Zero new work needed for
the option items themselves (existing `select-option-{value}` shared
mechanism); only the select TRIGGER testid gap (LLM/MCP/Toolkit node-level,
already tracked elsewhere) is outstanding.

**Tooling-only observation, explicitly NOT filed as a defect (pristine-repro
gate).** One exploration attempt — in a browser session already carrying
several prior interactions — saw a `Tab` keypress (instead of `Enter`) appear
to discard an uncommitted new-variable row AND close the entire drawer. A
clean immediate retry (fresh profile, straight open→+Context→type→`Tab`, no
prior interactions) did NOT reproduce this: `Tab` committed the row exactly
like `Enter`, source-consistent (both only trigger the same `onBlur`). Ruled
out as self-inflicted session state per the `playwright-testing`/
`browser-verify` skills' Synthetic Input Hygiene guidance — not filed.
Recommendation: automate via `Enter` to commit (matches the case's own
"Enter variable name" wording, confirmed reliable every time); don't build a
test around `Tab`-commit until/unless it's independently reproduced.

**Comprehensive testid wiring points** (all trivial, feature-local, except
one 2-caller shared-component change) are in
`test-specs/pipelines/l2_state-panel-default-and-custom-variables_ELITEA-2042.md`'s
Concrete Handles table — read that AFS first before adding testids to this
feature; it has exact file:line references for every control (drawer
container, close button, add-context button, name field, type-selector +
menu items, delete button, default-value button, and the one shared
`StateVariableIconButton` component that needs a new `testId` prop threaded
through its 2 call sites).

## Decision node — Input/Description/DECISION OUTPUTS, chip-based output mechanism (ELITEA-2034, 2026-07-24)

**Config is always inline/expanded, same as every other node type.** Fresh
`Decision` node (`NormalDecisionNode.jsx`, the NEW-style `type: decision` —
"Add node" → "Decision" always creates this, never the legacy
`decision:`-nested shape `LegacyDecisionNode.jsx` handles) shows, top to
bottom: **Input** (multi-select combobox), **Description** (plain
`<textarea>`, no AI-Assistant modal complexity needed for classification-
prompt text), **Decision outputs** (heading + chip container, empty on a
fresh node), **Interrupt before/after** switches. Zero click-to-open. **Zero
`data-testid` anywhere on Input/Description/the outputs container/the chips
today** — full wiring points (all four are trivial one-line additions at
existing call sites, `NormalDecisionNode.jsx:107/112`,
`DecisionNodeShared.jsx:19/36` — zero shared-component internals need
touching) are in
`test-specs/pipelines/l2_decision-node-config-input-description-outputs_ELITEA-2034.md`'s
Concrete Handles table — read that AFS first before adding testids here.

**DECISION OUTPUTS chips are populated by canvas drag-connect, NOT free
text — there is no "add chip" input anywhere on the panel.** Confirmed by
full source read: `DecisionOutputs`/`DecisionNodeShared.jsx` only ever
`.map()`s over the existing `decisionOutput` array rendering a delete-only
chip per entry — no add affordance exists in that component at all. The
REAL mechanism is dragging from the Decision node's own **`nodes`** source
handle (bottom-left of its two bottom handles, generic-fallback label
"Output" — see next paragraph) to an ALREADY-EXISTING target node;
`connectionOperations.helpers.js`'s `handleFromDecisionNodeConnection`
appends `connection.target` to the node's `nodes[]` array on a successful
drop, confirmed live for 3 sequential connects to 3 pre-named target nodes.
The three case-cited output names (e.g. `bug_responder`) must exist as REAL
canvas node `id`s *before* attempting the connects — same "seed via API
with literal target ids" pattern this digest's Router-node section (above)
already recommends for Routes/Default-output targets.

**The two bottom handles' labels are ordinary `CustomHandle` behavior, not
Decision-specific strings.** `id="nodes"` renders **"Output"** purely because
`NormalDecisionNode.jsx` passes no explicit `label` prop for it — falls
through to `CustomHandle.jsx`'s generic `finalLabel = label || (type ===
'source' ? 'Output' : 'Input')` fallback (the SAME fallback every other
unlabeled source handle on this canvas would hit). `id="default_output"`
renders **"Default output"** via an explicit `label="Default output"` prop.
Don't assert "Output" as if it were bespoke to Decision — key any assertion
off the stable `data-handleid`, not the rendered word.

**Input select lists custom state vars immediately, same as every other
node type** (confirmed live, no surprises): opening the Decision node's
Input combobox (`#simple-select-Input`, native id — same cross-node-type
duplicate-id family as `#1006`/`#1009`, not re-filed) listed
`select-option-input`, `select-option-messages`, plus whatever custom
`state:` vars the pipeline defines (`select-option-normalized_issue`,
`select-option-metadata_json` this session) — same shared
`select-option-{value}` mechanism the ELITEA-2042 section above already
documents joining Input/Output selects immediately after a custom var is
added.

**Persistence — exact YAML shape confirmed, survives a real Save + hard
reload.** A Decision node with 2 Input vars + a Description string + 3
DECISION OUTPUTS produces:
```yaml
- id: Decision 1
  type: decision
  nodes:
    - bug_responder
    - feature_responder
    - question_responder
  default_output: ''
  description: 'Classify this input into one category: ...'
  input:
    - normalized_issue
    - metadata_json
```
Re-confirmed byte-for-byte via both the Flow-view canvas fields and the YAML
tab, before and after a hard page reload. Zero `error`-level console
messages across the entire session (add node → configure → connect ×3 →
Save → reload → re-verify).

**Edge-testid shape drift is the SAME pattern already documented for
ELITEA-2018/2031 (ordinary nodes) — re-confirmed here for Decision's `nodes`
handle specifically.** Immediately after each drag:
`rf__edge-xy-edge__Decision {n}nodes-{target_id}target`. After Save + hard
reload: `rf__edge-xy-edge__Decision {n}---{target_id}` (triple-dash,
YAML-derived). The EXISTING `edge_exists(source, target,
handle_suffix="nodes")` call — unmodified — transparently matches BOTH
shapes (its `testid.startswith(expected_prefix) and f"-{target_id}" in
testid` check), confirmed live for all 3 connections. `connect_nodes(decision_id,
target_id, source_handle="nodes")` also needs zero changes — its existing
`data-handleid$="_{suffix}"` / `data-handleid="{suffix}"` lookup (originally
proven for HITL's approve/reject/edit handles, ELITEA-2014) finds the
Decision node's `data-handleid="nodes"` handle correctly as-is.

**Analyst-tooling-only note (not a product issue):** this session's headless
CDP/`playwright-cli` exploration needed a wide viewport (≥1900px) and a
rightward canvas pan to keep newly-added nodes clear of the LEFT
General-config panel and the RIGHT embedded-chat panel — both sit in normal
(non-overlay, `position: static`) document flow and will intercept clicks on
a node positioned underneath them (confirmed via `elementFromPoint`
mismatches landing on `agent-tags-input-field`/`chat-messages-scroll-
container`/a left-sidebar icon depending on exactly where the node happened
to render). A typical desktop-viewport Playwright test run shouldn't hit
this, but if a node-field click ever reports landing on one of those
elements instead of the intended target, pan/zoom first
(`fit_view()`/`zoom_in()`, already implemented) before retrying.

Full Concrete Handles table (exact line numbers, all four new-testid
wiring points, provenance-checked against a fresh `git fetch origin`) is in
`test-specs/pipelines/l2_decision-node-config-input-description-outputs_ELITEA-2034.md`
— read that AFS first if implementing this case.

## `get_node_count()` counts the implicit END node too (ELITEA-2031, 2026-07-24)

**`PipelineDetailPage.get_node_count()` counts every `.react-flow__node` in the
DOM, including the always-present `END` node** — confirmed live via
`get_node_ids()` returning `['END', 'LLM 1', 'Printer 1']` on a fresh 2-custom-
node fixture, and consistent with the already-merged `test_save_multi_node_pipeline`
precedent (1 custom node + `END` == 2 counted nodes). A case asserting "N nodes
on canvas" for N custom nodes must expect `get_node_count() == N + 1`, not `N` —
don't assume the helper excludes the implicit END node just because it isn't
one of the case's own named nodes. (Caught during ELITEA-2031's implementer pass
as an in-flight AFS correction; recorded here so the next case touching node
counts doesn't have to rediscover it.)
