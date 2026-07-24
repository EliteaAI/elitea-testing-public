# Test Case: Configure LLM Node — System, Task, Chat History (fields persist across Save + reload)

## Metadata
- **TMS ID**: ELITEA-2004
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths, no explicit login step
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

**Redispatch note (read first):** board `case.md` showed a single earlier analyst
dispatch (`2026-07-23T23:08:15Z`) that never completed — no AFS existed anywhere,
`Branch: —`, `PR: —`. That interrupted session had, however, already reached the
Pipelines list and left behind a manually-built throwaway pipeline
(`autotest_ELITEA_2004_llm_node`, id `5664`) whose LLM node was ALREADY configured
with exactly the case's Test Data values (System=Fixed/"You are a helpful
assistant", Task=F-String/"User Input: {input}", Chat History=Fixed/"[]",
Input=`input`, Output=`messages`) and already saved server-side. This session
reused that residue as a live starting point (fast-reach, not blind trust): a
fresh navigation into it in a brand-new isolated browser profile, plus an
explicit hard reload, both independently confirmed the values were genuinely
persisted server-side (not a client cache artifact) before any of my own edits.
I then additionally drove a full live change→Save→reload→verify→revert→Save→
reload round trip on the System value myself (see Test Steps 9–10) to prove the
save mechanism itself, not just inherited state — and deleted the throwaway
pipeline via the UI's own "Delete pipeline" flow once done (§ Cleanup). No
product defect found; this case's core observable (full LLM-node input-mapping
configuration + persistence) already works correctly end-to-end.

## Preconditions
- User is logged in to the Elitea platform (localhost: automatic via `VITE_DEV_TOKEN`).
- A project exists with access to the Pipelines feature (used: `Private` project).

## Test Data

### reuse-existing
- Existing `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py:160`,
  via `PipelineAPI.create_pipeline_with_llm_node`) already creates a pipeline with
  one LLM node (id `LLM 1`) connected to `END`, `input_mapping` keys `system` /
  `task` / `chat_history` all pre-seeded `type: fixed` (values empty) — this is the
  correct setup fixture; it saves a full extra "add LLM node from scratch" round
  trip while still letting the test exercise the case's own field-configuration
  steps (2–10) against a real, already-connected node.
  - Alternative if the case's own step 1 ("Add node via Add node → LLM") must be
    exercised literally rather than via fixture: `pipeline_id` fixture (empty
    pipeline) + `PipelineDetailPage.add_node("LLM")` +
    `wait_for_node_on_canvas("llm")` — this exact flow is already proven by
    multiple MERGED specs (`test_pipeline_advanced.py`'s `_add_llm_node_and_connect`,
    used by `test_add_llm_node_...` variants; `test_pipeline_nodes.py`'s HITL
    analogue) — no new handle work needed for step 1 itself.
- Default STATE variables `input` / `messages` are available in the Input/Output
  comboboxes on **any** pipeline with no explicit `state:` YAML block at all —
  confirmed live (the reused pipeline's own YAML had no top-level `state:` key,
  yet the Input/Output dropdowns listed exactly `input` and `messages`, each with
  its own `select-option-{value}` testid). No custom state seeding is required for
  this case (unlike GAP-007's f-string-autocomplete case, which needed two extra
  custom vars) — `input`/`messages` cover the case's own Test Data row exactly.

### Test Data values (from case)
| Field | Value |
|---|---|
| SYSTEM Type | Fixed |
| SYSTEM Value | `You are a helpful assistant` |
| TASK Type | F-String |
| TASK Value | `User Input: {input}` |
| CHAT HISTORY Type | Fixed |
| CHAT HISTORY Value | `[]` |
| Input variable | `input` |
| Output variable | `messages` (any existing state var satisfies the case's "desired output variables" wording; `messages` is the natural choice for an LLM node's response) |

## Test Steps

1. Create a pipeline and add an LLM node via "Add node" → "LLM" (or use
   `pipeline_with_llm_id` fixture — see Test Data).
   - **Verify**: an LLM-type node (`.react-flow__node-llm`, ReactFlow's own
     `[data-testid="rf__node-{id}"]`, e.g. `rf__node-LLM 1`) appears on the canvas.
2. Observe the node's configuration fields.
   - **Verify (CLARIFICATION — see Coverage Map)**: no click is needed to "open" a
     panel — the Flow-view canvas renders every node's config fields (Trigger,
     SYSTEM, TASK, CHAT HISTORY, Input, Output, Toolkits, Interrupt before/after,
     Structured output) **always inline/expanded** on the card itself. This is the
     identical, already-established finding from ELITEA-1954 (MCP nodes) —
     confirmed live again here for the LLM node. The case-text's "click to open"
     framing is stale relative to the live UI, not a defect: the observable
     ("panel/fields are visible") is still true.
3. Confirm all listed sections are present.
   - **Verify**: confirmed live — Trigger ("Chat Message"), SYSTEM (Type + Value),
     TASK (Type + Value), CHAT HISTORY (Type + Value), Input, Output, Toolkits,
     Interrupt before, Interrupt after, Structured output are all rendered on the
     node card (see screenshot evidence, `/tmp/e2004-02-pipeline-detail.png`
     equivalent — implementer captures its own on the fixture-created node).
4. In SYSTEM: set Type to "Fixed" (`select-option-fixed`), enter Value
   `You are a helpful assistant`.
   - **Verify**: the field accepts the value — confirmed live via
     `#system-value` (dev-only raw id, NOT the implementer's locator — see
     Concrete Handles) reading back exactly `You are a helpful assistant`
     immediately after typing.
5. In TASK: set Type to "F-String" (`select-option-fstring`), enter Value
   `User Input: {input}`.
   - **Verify**: confirmed live via `#task-value` reading back
     `User Input: {input}` verbatim (no autocomplete-popper interference for a
     plain type-through — the f-string autocomplete popper for the System/Task
     inline fields is a SEPARATE, already-covered mechanism, see GAP-007's AFS;
     this case's Task value contains a *complete*, already-closed `{input}`
     token typed as ordinary text, not exercising the popper's open/insert flow).
6. In CHAT HISTORY: set Type to "Fixed" (`select-option-fixed`), enter Value `[]`.
   - **Verify**: confirmed live via `#chat_history-value` reading back `[]`.
     Functional note for the implementer: `SimpleLLMInputItem.jsx`'s `onInput`
     handler `JSON.parse`s this field's raw text when `variableName ===
     'chat_history' && type === 'fixed'` — a syntactically-invalid value (e.g.
     a stray unclosed bracket while mid-typing) falls back to storing the raw
     string instead of throwing; only the FINAL, fully-typed `[]` needs to
     round-trip cleanly, which it does (confirmed via both the Flow-view field
     and the YAML view showing `value: []` as a real list, not a string).
7. Set Input combobox to include "input".
   - **Verify**: confirmed live — opening the Input select (native id
     `#simple-select-Input` for exploration; implementer uses the new
     dynamic testid, see Concrete Handles) lists exactly two options, `input`
     and `messages`, each carrying the existing `select-option-{value}` testid
     (`select-option-input`, `select-option-messages` — confirmed via a live
     DOM read of the open listbox). Selecting `input` renders it as a chip
     (`input ⊗`) in the field.
8. Set Output combobox to include a desired output variable (`messages`).
   - **Verify**: confirmed live — same select mechanism as step 7; `messages`
     renders as a chip in the Output field.
9. Save pipeline.
   - **Verify**: confirmed live via a genuine change→Save round trip (not just
     reading the residual state): appended `" (livecheck)"` to the SYSTEM value
     via a real `input` event (not a UI click-typed edit — the implementer's
     real Playwright test types this normally via `fill()`/`press_sequentially()`,
     which is unaffected by the CDP-tooling quirk noted in Automation Hints),
     clicked **Save**, and confirmed the app's own dirty-state indicator (the
     **Discard** button) flipped from enabled → disabled, i.e. the app itself
     reports "no unsaved changes" immediately after Save — no error toast, no
     console error, no failed network request (`get-console`/`get-network
     --status error` both empty across the whole round trip).
10. Reload page — verify SYSTEM, TASK, CHAT HISTORY types and values persisted.
    - **Verify**: confirmed live via a **hard reload** (not a client-side route
      change) immediately after step 9's Save: `#system-value` read back the
      modified `You are a helpful assistant (livecheck)` string exactly. Then
      reverted the SYSTEM value back to the original `You are a helpful
      assistant`, clicked Save again, hard-reloaded again, and confirmed ALL
      THREE fields (`#system-value`, `#task-value`, `#chat_history-value`) plus
      Input (`input`) and Output (`messages`) read back exactly the Test Data
      table's values — a full, genuine two-way persistence proof, not a
      one-directional "it happened to still be there" observation. The YAML
      view (`Yaml` tab, `pipeline-yaml-editor`/`pipeline-yaml-lines` — existing
      testids) independently corroborated the exact same values as a second,
      differently-sourced confirmation:
      ```yaml
      entry_point: LLM 1
      nodes:
        - id: LLM 1
          type: llm
          input:
            - input
          input_mapping:
            chat_history:
              type: fixed
              value: []
            system:
              type: fixed
              value: You are a helpful assistant
            task:
              type: fstring
              value: 'User Input: {input}'
          output:
            - messages
          structured_output: false
          transition: END
      ```

## Expected Results
- The LLM node configuration panel's fields (Trigger, SYSTEM, TASK, CHAT HISTORY,
  Input, Output, Toolkits, Interrupt before/after, Structured output) are always
  rendered inline on the canvas card — no separate open/close action exists.
- SYSTEM (Fixed / "You are a helpful assistant"), TASK (F-String / "User Input:
  {input}"), CHAT HISTORY (Fixed / "[]"), Input (`input`), and Output (`messages`)
  all accept their values immediately in the Flow view.
- Save completes with no error toast and no console/network error; the app's own
  dirty-state indicator (Discard button) clears.
- A hard reload of the pipeline detail page re-shows every configured field and
  value exactly as saved — confirmed via both the Flow-view fields and the
  YAML-view tab independently.
- Zero `error`-level console messages and zero failed (`4xx`/`5xx`) network
  requests across the entire configure→save→reload cycle.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline + add LLM node via Add node → LLM | LLM node appears on canvas | step 1 | step 1: `.react-flow__node-llm` / `rf__node-{id}` visible | asserted — infrastructure already proven by merged specs (`test_pipeline_advanced.py`), reused not re-derived |
| 2 Click LLM node to open configuration panel | Panel opens on the right | step 2 | step 2 | **CLARIFICATION** — live product has no click-to-open action; config is always rendered inline/expanded on the node card itself (identical finding + resolution as ELITEA-1954's AFS Coverage Map). Not a defect: the observable ("panel/fields visible") is still true and asserted. No separate ticket filed — following the ELITEA-1954 precedent of resolving this directly in the Coverage Map rather than filing a repeat ticket for the same, already-documented UI simplification. |
| 3 Panel shows Trigger/SYSTEM/TASK/CHAT HISTORY/Input/Output/Toolkits/Interrupt before/after/Structured output | All sections present | step 3 | step 3: `get_llm_node_type`×3 (SYSTEM/TASK/CHAT HISTORY) + `llm_node_input_select`/`llm_node_output_select` visible + `pipeline_trigger_select`/`toolkits_section`/`node_interrupt_before_switch`/`node_interrupt_after_switch`/`node_structured_output_switch` visible — all 9 named sections now individually asserted (review fix pass R1, ELITEA-2004; previously only 5/9 had real assertions behind the "asserted" claim) | asserted |
| 4 SYSTEM: Type=Fixed, Value="You are a helpful assistant" | Section accepts value | step 4 | step 4: `#system-value` read-back | asserted |
| 5 TASK: Type=F-String, Value="User Input: {input}" | Section accepts f-string value | step 5 | step 5: `#task-value` read-back | asserted |
| 6 CHAT HISTORY: Type=Fixed, Value="[]" | Section accepts value | step 6 | step 6: `get_llm_node_value("chat_history")` read-back; the YAML `value: []` (real list, not string) half of this claim is asserted in the Step 7/8-verification and Step 10 YAML blocks (pre-save AND post-reload — review fix pass R1, ELITEA-2004; previously only the DOM read-back was asserted, never the YAML-view corroboration this row itself claims) | asserted |
| 7 Input combobox includes "input" | "input" variable added | step 7 | step 7/8-verification: `_yaml_node_field()` structural check proves the node's `input:` field round-trips as a real YAML list containing exactly `input` (not the empty pre-seeded `[]`) — review fix pass R2, ELITEA-2004; previously a bare `"input" in yaml_before_save`/`yaml_after_reload` substring check, which this row's OWN "chip rendered + `select-option-input`" claim never matched anyway — chip-rendering and `select-option-input` visibility are still NOT asserted (out of scope per this row's Concrete Handles note; the YAML view suffices) | asserted |
| 8 Output combobox includes desired output variable(s) | Output variables set | step 8 | step 8: `"messages" in yaml_before_save`/`yaml_after_reload` substring check (sound as-is — no other fixture value contains "messages", so no collision risk, unlike row 7's "input" pre-fix) — chip-rendering and `select-option-messages` visibility are likewise NOT asserted, same YAML-view-suffices scope (row wording corrected in review fix pass R2, ELITEA-2004 to match what the code has always actually done) | asserted |
| 9 Save pipeline | Saves without errors | step 9 | step 9: Discard button disables, zero console errors so far, zero failed (4xx/5xx) network requests so far | asserted |
| 10 Reload — verify SYSTEM/TASK/CHAT HISTORY types+values persisted | All values/types restored | step 10 | step 10: all 3 fields + Input + Output read back exactly, corroborated by YAML view | asserted |
| Expected Final State: full config persists after reload | — | steps 4–10 | steps 4–10 | asserted |
| Pass/Fail: all steps complete without errors; all fields persist after reload | — | all steps | all steps | asserted — no product defect found, confirmed via a genuine live change→Save→reload→revert→Save→reload round trip, not just a static read |
| Expected Results: "zero error-level console messages and zero failed (4xx/5xx) network requests across the entire configure→save→reload cycle" | — | whole-cycle check (post-Step 10) | `console_errors`/`network_activity` (`BasePage.capture_console_errors`/`capture_requests_matching("")`) registered before Step 1, asserted at Step 9 AND again in a dedicated whole-cycle step after the Step 10 reload — both listeners survive `page.goto()`/reload since they're attached to the same `Page` object (review fix pass R1, ELITEA-2004; previously console_errors was a manually-registered list asserted only once, BEFORE the Step 10 reload, and no network assertion existed at all) | asserted |

### Axis 2 — Analyst additions

- Steps 9–10 assert via **two independently-sourced reads** (Flow-view field
  values AND the YAML-view tab) rather than only one — *added: a single-source
  read can't distinguish "field shows stale client state" from "field reflects
  the actual saved backend value"; the YAML view is generated from the same
  `yamlJsonObject` the Save button PUTs, so agreement between it and the
  Flow-view fields is meaningful corroboration, not a duplicate check.*
- Step 9 additionally asserts zero console errors and zero failed network
  requests across the whole configure→Save cycle — *added: no console/network
  assertion was in the original case text; this is the project's standard
  side-channel discipline (`.agents/testing.md`) and cost nothing extra given
  the interaction was already being driven live.*
- Noted (not asserted, informational only) a pre-existing, already-filed,
  non-blocking defect (`EliteaAI/elitea-testing-public#1006` — duplicate
  `id="simple-select-Type"` across every Type select on an LLM node) that the
  implementer must route around by using testids, never the native id, for the
  System/Task/Chat History Type selects — *added: directly relevant to this
  case's own locator choices, flagging it here saves the implementer a
  rediscovery cycle.*

## Cleanup

1. If the fixture-based setup (recommended, see Test Data) is used, cleanup is
   automatic via `pipeline_with_llm_id`'s/`pipeline_id`'s existing teardown
   (`PipelineAPI.delete_pipeline`).
2. This analysis session's own manually-built throwaway pipeline
   (`autotest_ELITEA_2004_llm_node`, id `5664`, left behind by the earlier
   interrupted analyst dispatch) was deleted via the UI's own "Delete pipeline"
   flow (three-dot menu → Delete pipeline → type-to-confirm) at the end of this
   session — confirmed gone from the Pipelines list afterward. No orphaned data
   remains from this case's analysis.
3. Observational note (out of this case's cleanup scope, not actioned): two
   OTHER stray pipelines from a different case's exploration
   (`autotest_GAP007_fstring`, `GAP-007 f-string autocomplete`) are still present
   in the same `Private` project — left untouched since they belong to GAP-007,
   not this case; flagging for whoever eventually cleans up that case's debris.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance / Notes |
|---|---|---|
| LLM node container | `[data-testid="rf__node-{id}"]` (ReactFlow's own testid, e.g. `rf__node-LLM 1`) | on-main ✓ — third-party (ReactFlow) widget testid, not app-added; already used by existing page-object methods (`wait_for_node_on_canvas`, `get_node_ids`) |
| SYSTEM/TASK/CHAT HISTORY "Type" select (trigger) | **NO `data-testid` today** — native id `#simple-select-Type`, duplicated 3× on a single LLM node (System/Task/Chat History all share the label "Type") and again per additional node — confirmed live this session (`document.querySelectorAll('#simple-select-Type').length === 3` on a single-LLM-node canvas), same root cause as the already-filed `EliteaAI/elitea-testing-public#1006`. **Flag to `add-data-testid`**: `SingleSelect.jsx` (`src/[fsd]/shared/ui/select/SingleSelect.jsx:657-659`) already accepts a `data-testid` prop and wires `SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}` — the exact mechanism already used for `pipeline-mcp-node-toolkit-select-combobox` (ELITEA-1954/1955). Wiring point: `SimpleLLMInputItem.jsx`'s `<SingleSelect label="Type" ...>` call (line ~190) needs `data-testid={`pipeline-llm-node-${variableName}-type-select`}` added — `variableName` is already a prop on the component (`'system'`/`'task'`/`'chat_history'`, confirmed via source read). Zero shared-component edits needed. | needs-adding — on neither `main` nor `automation/testids` yet |
| Type-select "Fixed" / "F-String" / "Variable" option | `[data-testid="select-option-fixed"]` / `[data-testid="select-option-fstring"]` / `[data-testid="select-option-variable"]` (`SELECT_OPTION` class constant already in `pipeline_detail_page.py`) | on-main ✓ — confirmed live this session for `fixed`; `fstring` independently confirmed by GAP-007's AFS same day; `variable` inferred from unconditional source derivation (`SingleSelectMenuItem.jsx:117`: `data-testid={option.testId ?? \`select-option-${option.value}\`}`, and `agentTaskTypeOptions` has no per-option `testId` override) — same shared, already-proven `SELECT_OPTION` mechanism used across the whole app (MCP toolkit/tool selects, this case's own Input/Output selects) |
| SYSTEM/TASK/CHAT HISTORY "Value" field | **NO `data-testid` today** — dev-only DOM id `#{variable}-value` (e.g. `#system-value`, `#task-value`, `#chat_history-value`), confirmed live this session but NOT policy-compliant (raw id, and not guaranteed unique with >1 LLM node on canvas). **Flag to `add-data-testid`**: wiring point is `SimpleLLMInputItem.jsx`'s `NodeFieldInput.commonProps` (line ~48) — add `inputProps: {'data-testid': `pipeline-llm-node-${variableName}-value-input`}`. This flows through `AIAssistantInput`'s `...leftProps` spread (for System/Task, which route through the AI-Assistant-enabled branch) or directly through `Input.StyledInputEnhancer` (for Chat History, which never enables the AI Assistant) into `InputBase.jsx`'s `slotProps={{ htmlInput: inputProps }}` (confirmed by source read, line ~267) — MUI applies `inputProps` straight onto the native `<textarea>` element. Zero shared-component edits needed; this is a first-class, already-supported `InputBase` prop. | needs-adding |
| Input combobox (trigger) | **NO `data-testid` today** — native id `#simple-select-Input` (unique per node today, single-LLM-node canvas only). **Flag to `add-data-testid`**: `LLMNode.jsx`'s `<FlowEditorSelect.InputSelect id={id} label="Input" ... />` call (line ~85) is missing the `dataTestId` prop that `InputSelect.jsx` (line 9, 67) already destructures and forwards to the shared `Select.SingleSelect`'s `data-testid` — exactly the same wiring `BaseToolNode.jsx` already uses for MCP nodes (`dataTestId={isMcpNode ? 'pipeline-mcp-node-input-select' : undefined}`, confirmed via source read). LLMNode.jsx is LLM-specific already, so no ternary is needed — just `dataTestId="pipeline-llm-node-input-select"`. Same mechanism as `mcp_node_toolkit_select`/`-combobox` yields BOTH the outer testid and a `-combobox` suffix testid (carries `aria-expanded`) for free. | needs-adding |
| Output combobox (trigger) | **NO `data-testid` today** — native id `#simple-select-Output`. **Flag to `add-data-testid`**: identical pattern to Input, one line lower in `LLMNode.jsx` (`<FlowEditorSelect.OutputSelect id={id} label="Output" ... />`) — add `dataTestId="pipeline-llm-node-output-select"`. | needs-adding |
| Input/Output select's open-listbox option (per state var, dynamic) | `[data-testid="select-option-{value}"]` — e.g. `select-option-input`, `select-option-messages` (same `SELECT_OPTION` constant) | on-main ✓ — confirmed live this session, identical shared mechanism |
| Input/Output selected-value chip (e.g. "input ⊗") | **NO `data-testid`** — bare MUI `<Chip>` (`SingleSelect.jsx`'s `renderMultipleValue`, confirmed via source read). NOT required for this case: reading the currently-selected Input/Output values is fully satisfiable via the YAML view (`get_yaml_content()`, already an existing `PipelineDetailPage` method with existing testids `pipeline-yaml-editor`/`pipeline-yaml-lines`) instead of scraping chip text — this is the SAME pattern the existing merged `test_yaml_content_reflects_pipeline` test already uses. Flag to `add-data-testid` only if a future case needs to remove/read an individual chip directly rather than via YAML. | out-of-scope for this case (touches rule — not interacted with directly; YAML view suffices) |
| YAML view content (alternate persistence-verification path) | `pipeline-yaml-editor` / `pipeline-yaml-lines` (`PipelineDetailPage.yaml_editor` / `.yaml_lines`, already `LocatorDescriptor` fields) + `get_yaml_content()` (already an existing method) | on-main ✓ — pre-existing page-object surface, zero new work |
| Discard button (dirty-state indicator, used as a Save-succeeded signal) | **NO `data-testid`** — plain `getByRole('button', {name: 'Discard'})` works today (text-based, matches existing `PipelineDetailPage.configuration_tab`/`history_tab` style raw-fallback precedent, tracked tech debt per `.agents/testing.md`, not to be repeated for NEW code). **Flag to `add-data-testid`** only if the implementer chooses to assert on this button directly rather than solely on the reload-based persistence check (which needs no such handle) — not strictly required by this case's own Pass/Fail criteria. | needs-adding (optional — implementer's call) |

### Review fix pass R1 additions (ELITEA-2004) — new/reused handles

Added to close the reviewer's Step-3 coverage gap (Finding 1) and the fixed-sleep
finding (Finding 4). All follow the same testid-only discipline as the rows above.

| Element | Recommended Locator | Provenance / Notes |
|---|---|---|
| Trigger select (entry-point node only) | `[data-testid="pipeline-trigger-select"]` | on-automation/testids ✓ (not yet on `main`) — added for ELITEA-2005/2006, **reused here, not re-added**; `TriggerTypeSelector.jsx` renders on any node where `isEntrypoint` is true, and `pipeline_with_llm_id`'s LLM node is the pipeline's `entry_point` |
| "Interrupt before" toggle | `[data-testid="pipeline-node-interrupt-before-switch"]` | needs-adding → **added this round**, EliteaAI/EliteaUI@1289e746 on `automation/testids` (not yet on `main`). Deliberately GENERIC (not LLM-scoped): `CommonInterruptSettings.jsx` is a shared component rendered by 8+ node types (LLM/MCP/Code/Agent/Subgraph/Decision/deprecated Loop+Tool) — per `.agents/testing.md` § Locator policy "shared components never hardcode feature-scoped testids", a caller-supplied prop would have meant threading `testId` through every call site for no disambiguation benefit this test needs (only one LLM node on canvas) |
| "Interrupt after" toggle | `[data-testid="pipeline-node-interrupt-after-switch"]` | needs-adding → **added this round**, same commit/rationale as above |
| "Structured output" toggle | `[data-testid="pipeline-node-structured-output-switch"]` | needs-adding → **added this round**, same commit/rationale as above |
| Input select — inner combobox div (carries `aria-expanded`) | `[data-testid="pipeline-llm-node-input-select-combobox"]` | on-automation/testids ✓ — **already existed for free**, not newly added: `SingleSelect.jsx` unconditionally wires `SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}` alongside the outer `data-testid` (confirmed via source read), so this landed in the SAME commit (16efb4cb) that added `pipeline-llm-node-input-select` itself — only the page-object `LocatorDescriptor` + the condition-based wait using it are new this round |
| Output select — inner combobox div | `[data-testid="pipeline-llm-node-output-select-combobox"]` | on-automation/testids ✓ — same as above |

## Network Behavior

No network call is central to this case's own field-level assertions while
configuring the node — Type/Value/Input/Output edits are pure client-side
Formik/React state until Save. The Save action itself is inferred (not freshly
captured this session — the intervening `reload` calls cleared this tool's
network buffer before it could be read back) to hit the same
`PUT /elitea_core/application/prompt_lib/{project_id}/{pipeline_id}` endpoint
already used by the existing `PipelineAPI.update_pipeline()` client method
(`automation/api/client.py:658`, `_application_url()`) — this is the same
entity (`application`) the pipeline detail page's Save button persists, and the
existing `test_yaml_content_reflects_pipeline` merged test already relies on
this same save/reload round trip working. No new network assertion is required
by this case; the implementer's persistence check should assert on UI-visible
state (Flow-view fields and/or YAML view) after a real page reload, matching
Test Steps 9–10 above, not on the raw PUT response body.

## Known Defects Found During Exploration

- None found that block or affect this case's own observable. One
  pre-existing, already-filed, non-blocking defect is relevant to locator
  choice only: `EliteaAI/elitea-testing-public#1006` (duplicate
  `id="simple-select-Type"` across every Type select on an LLM node,
  independently re-confirmed live this session — 3 duplicates on a
  single-LLM-node canvas) — the implementer must use the new testid (once
  added) rather than this native id for the System/Task/Chat History Type
  selects; see Concrete Handles.

## Blocked Steps

None. All 10 case steps were executed to completion against the live local
environment, including a genuine live change→Save→reload→revert→Save→reload
round trip (steps 9–10) rather than only reading pre-existing residual state.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). **This case requires `add-data-testid` work** — every
  element central to configuring the node (Type selects, Value fields, Input/
  Output select triggers) lacks a testid today; all four have a trivial
  existing extension point (`data-testid` prop / `inputProps` /  `dataTestId`
  prop already supported by the underlying shared components) — none require
  editing shared-component internals, only wiring a prop at the LLM-node call
  sites (`SimpleLLMInputItem.jsx`, `LLMNode.jsx`). See Concrete Handles for the
  exact line-level wiring points.
- New page-object surface needed: `automation/pages/pipeline_detail_page.py`
  currently has generic node methods (`add_node`, `wait_for_node_on_canvas`,
  `delete_node`, `make_node_entrypoint`) and MCP-node-specific methods
  (ELITEA-1954/1955), but nothing for an LLM node's System/Task/Chat-History
  Type+Value fields or its Input/Output selects. Suggested shape:
  `set_llm_node_field(variable_name, type_value, value)` (handles Type-select +
  Value-field together, since the case always sets both), `select_llm_node_input
  (value)` / `select_llm_node_output(value)` (wrapping the existing
  `SELECT_OPTION`/`select_open_listbox_option` pattern already used for MCP
  nodes).
- **Tooling-only gotcha, not a product issue** (documented in this session's
  memory, `.agents/memory/qa-engineer/browser_verify_cdp_clear_backspace_does_
  not_clear_mui_textarea.md`): the analyst's own `browser-verify`/`cdp.mjs`
  tool cannot reliably clear+retype these MUI multiline textareas via its
  `--clear` flag or a synthetic Ctrl+A+Backspace — this does NOT affect the
  real Playwright/pytest suite, whose `.clear()` / `fill()` /
  `press_sequentially()` are mature and already proven reliable elsewhere in
  this codebase (e.g. `test_agent_save_as_version.py`). No special handling
  needed in the actual test.
- Recommended setup: `pipeline_with_llm_id` fixture (see Test Data) — already
  provisions a connected LLM node with `input_mapping` keys pre-seeded, saving
  a full node-add round trip while still exercising this case's own
  field-configuration + persistence steps.
- Wait strategy: no network wait needed for the field-edit interactions
  themselves (pure client-side); after clicking Save, wait on the Discard
  button's disabled state (Playwright's built-in auto-waiting
  `expect(discard_button).to_be_disabled()`) as the "save completed" signal,
  then `page.reload()` + re-assert field values — never a fixed `sleep`.
- The System/Task fields route through the AI-Assistant-enabled branch
  (`shouldEnableAIAssistant` is true for `system`/`task`/`code`/`printer`/
  `user_message` when Type is Fixed or F-String) but this case never needs to
  open that modal — typing directly into the visible inline field (confirmed
  live to be a real, directly-editable `<textarea>`, not a button that only
  opens a modal) is sufficient and matches the case's own "enter Value" wording.
  The AI Assistant modal / f-string-autocomplete-popper mechanism is a
  SEPARATE, already-covered concern (GAP-007's AFS) — do not conflate the two
  when implementing.

## Implementer Notes (added during ELITEA-2004 implementation)

- `set_llm_node_value` uses `field.evaluate("el => el.select()")` to clear
  pre-existing text, NOT `press("Control+a")` — confirmed live on this exact
  textarea that `Control+a` does not reliably select-all (it left CHAT
  HISTORY's pre-seeded `"[]"` in place and the new text was appended instead
  of replacing it, producing `"[][]"`). Same rationale already documented on
  `PipelineFormPage.update_text_field`.
- `select_llm_node_input`/`select_llm_node_output` press `Escape` after
  selecting an option — Input/Output are `multiple` MUI selects
  (`InputSelect.jsx`/`OutputSelect.jsx`), which do not auto-close the menu on
  option click (unlike the single-select MCP Toolkit/Tool dropdowns this
  page object already wraps). Without the explicit close, the next select's
  click is intercepted by the still-open popover.
- `ApplicationTabBar.jsx`'s Discard button had a live prop-name bug
  (`data-testid="discard-button"` instead of `dataTestId="discard-button"`)
  that meant the testid never actually rendered on ANY caller (Agents/
  Applications/Pipelines) — confirmed live before the fix (0 DOM matches for
  `[data-testid="discard-button"]`). Fixed as part of this case (declared
  improvisation — same class as the other testid work, an already-declared
  page-object contract silently broken by a one-line wiring bug) since this
  case's own Step 9 relies on the Discard button as the save-completion
  signal. One-line fix, no behavior change; benefits every existing caller of
  `PipelineFormPage.discard_button`/`AgentFormPage.discard_button`.

## Implementer Notes — review fix pass R1 (ELITEA-2004)

Four reviewer findings addressed, all in the test file + page object (no case
re-scoping — the AFS's own Coverage Map/Concrete Handles rows already claimed
this coverage; this round made the code match the claim):

1. **Step 3 under-coverage (Important).** Coverage Map row 3 claimed all 9
   sections ("Trigger, SYSTEM, TASK, CHAT HISTORY, Input, Output, Toolkits,
   Interrupt before/after, Structured output") were asserted, but only 5 had
   real assertions. Added assertions for the remaining 4 handles (Trigger,
   Toolkits — both reused existing testids; Interrupt before/after +
   Structured output — 3 new testids added via `add-data-testid` to the
   shared `CommonInterruptSettings.jsx`, generic-named per the shared-
   component locator rule). See § Concrete Handles → "Review fix pass R1
   additions" above.
2. **CHAT HISTORY YAML-list proof missing (Important).** Coverage Map row 6
   claimed the YAML-view `value: []` (real list, not string) corroboration
   was asserted — it wasn't, anywhere. Added both a positive check
   (`"value: []" in yaml`) and a negative check (rules out the quoted-string
   fallback `SimpleLLMInputItem.jsx`'s `onInput` silently produces on
   `JSON.parse` failure) at both the pre-save and post-reload YAML reads.
3. **Whole-cycle side-channel gaps (Important).** (a) No network-response
   assertion existed anywhere despite the AFS Expected Results explicitly
   claiming "zero failed (4xx/5xx) network requests across the entire
   cycle" — added a whole-page `capture_requests_matching("")` (empty
   substring matches every request) asserted at Step 9 and again after the
   Step 10 reload. (b) `console_errors` was only asserted once, BEFORE the
   Step 10 reload, so errors introduced by the reload itself were captured
   but never checked — switched from a manual `page.on("console", ...)` to
   the existing `BasePage.capture_console_errors()` helper (reuse before
   create) and added a second assertion after the reload, mirroring the
   established multi-checkpoint pattern in
   `test_agent_max_five_skills_limit.py`. Both listeners are stopped in a
   `finally` block per that same precedent.
4. **Fixed sleeps in new page-object code (Nit/Important).**
   `select_llm_node_input`/`select_llm_node_output`'s post-Escape
   `page.wait_for_timeout(300)` replaced with a condition-based wait on the
   Input/Output select's `-combobox` testid's `aria-expanded` attribute
   flipping to `"false"` — mirrors the existing
   `close_mcp_node_toolkit_select` pattern exactly. The `-combobox` testid
   needed no new `add-data-testid` work: `SingleSelect.jsx` always wires it
   alongside the outer testid, so it already existed on `automation/testids`
   from the original ELITEA-2004 commit (16efb4cb) — only the
   `LocatorDescriptor` + the wait itself are new.

Both methods (`select_llm_node_input`/`select_llm_node_output`) have zero
other callers in the suite (`grep -rl` confirmed), so modifying their bodies
directly is not subject to the shared-caller additive-only protocol.

## Implementer Notes — review fix pass R2 (ELITEA-2004)

One reviewer finding addressed, in the test file only (no page-object change):

1. **Step 7 "input" verification vacuous (Important).** The Step 7/8-
   verification and Step 10 checks asserted `"input" in yaml_before_save`/
   `yaml_after_reload` — a bare substring match. This is vacuous: Step 5's
   TASK value (`_TASK_VALUE = "User Input: {input}"`) already guarantees the
   literal substring `input` appears in the SAME YAML dump via the f-string
   placeholder, independently proven by the test's own
   `"User Input: {input}" in yaml_after_reload` assertion. The fixture
   (`PipelineAPI.create_pipeline_with_llm_node`) pre-seeds `input: []`
   (empty), so a silent regression in `select_llm_node_input` that fails to
   actually add "input" to the node's Input list would NOT have been caught
   — the assertion passed regardless.

   Fix: a new `_yaml_node_field(yaml_text, field_name)` helper extracts the
   `input:` node field's own value text (terminated at the next
   lowercase_snake_case YAML key or a newline — the same technique
   `PipelineDetailPage.get_entrypoint_node_id()` already uses for
   `entry_point:`, reused rather than duplicated), and both call sites now
   assert `input_field == "- input"` — a structural check that only passes
   when the Input select genuinely wrote a real one-item YAML list.

   `yaml.safe_load()` was considered first (per the reviewer's suggested
   fix) but does not work here: a live pytest run with the raw
   `get_yaml_content()` output captured to disk (2026-07-24) confirmed it
   falls back to a single concatenated string with NO line breaks at all in
   this environment (`pipeline-yaml-lines` testid selector matches 0
   elements — the exact quirk `get_entrypoint_node_id()`'s own docstring
   already documents), so `yaml.safe_load()` would fail to parse the
   squashed text. The regex approach was verified robust to BOTH the
   squashed form (the live-captured one) and a properly newline-separated
   form (hand-constructed) in isolation before committing it to the test.

   Verified the fix actually catches the regression class the finding
   named: temporarily skipped the `select_llm_node_input()` call (simulating
   the exact regression), re-ran, and confirmed the NEW assertion fails with
   `got field text: '[]'` — proving it is not vacuous. Reverted the
   simulated regression before the real (passing) run.

   Coverage Map rows 7 and 8 also corrected in this pass (same finding
   named this as AFS/implementation drift): both previously claimed
   "chip rendered + `select-option-*`" as the assertion mechanism, which the
   code has never actually done (out of scope per the Concrete Handles
   note — the YAML view suffices) — row text now matches what the code
   asserts.
